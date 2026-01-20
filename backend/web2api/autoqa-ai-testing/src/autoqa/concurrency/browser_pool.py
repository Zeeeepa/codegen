"""
Browser context pool for efficient resource reuse.

Provides a pool of browser contexts with:
- Lifecycle management (creation, recycling, cleanup)
- Usage tracking and limits
- Health checks and automatic recovery
- Async-first design with proper cleanup

SDK v2 Notes:
- Uses OwlBrowser instead of Browser
- Context is identified by context_id string (from create_context)
- All operations are async
- Context lifecycle: create_context -> use -> close_context
"""

from __future__ import annotations

import asyncio
import contextlib
import time
import uuid
from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import TYPE_CHECKING, Any, AsyncIterator

import structlog

if TYPE_CHECKING:
    from owl_browser import OwlBrowser

    from autoqa.concurrency.config import ConcurrencyConfig
    from autoqa.concurrency.resource_monitor import ResourceMonitor

logger = structlog.get_logger(__name__)


class BrowserPoolError(Exception):
    """Base exception for browser pool errors."""


class PoolExhaustedError(BrowserPoolError):
    """Raised when pool is exhausted and cannot create new contexts."""


class ContextAcquisitionError(BrowserPoolError):
    """Raised when context acquisition fails."""


class ContextState(StrEnum):
    """State of a browser context in the pool."""

    AVAILABLE = auto()
    """Context is available for acquisition."""

    IN_USE = auto()
    """Context is currently being used."""

    RECYCLING = auto()
    """Context is being recycled."""

    FAILED = auto()
    """Context has failed and needs cleanup."""


@dataclass
class PooledContext:
    """
    Wrapper for a browser context with metadata.

    Tracks lifecycle information for pool management.

    SDK v2 Notes:
        - context_id is the string ID from browser.create_context()
        - No longer holds a page object, just the ID
    """

    id: str
    """Unique identifier for this context in the pool."""

    context_id: str
    """The browser context_id from SDK v2 create_context."""

    state: ContextState = ContextState.AVAILABLE
    """Current state of the context."""

    created_at: float = field(default_factory=time.time)
    """Unix timestamp when context was created."""

    last_used_at: float = field(default_factory=time.time)
    """Unix timestamp when context was last used."""

    use_count: int = 0
    """Number of times this context has been used."""

    current_test: str | None = None
    """Name of currently running test, if any."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata for the context."""

    @property
    def age_seconds(self) -> float:
        """Get the age of this context in seconds."""
        return time.time() - self.created_at

    @property
    def idle_seconds(self) -> float:
        """Get time since last use in seconds."""
        return time.time() - self.last_used_at

    def mark_used(self, test_name: str | None = None) -> None:
        """Mark context as used and update metadata."""
        self.last_used_at = time.time()
        self.use_count += 1
        self.current_test = test_name
        self.state = ContextState.IN_USE

    def mark_released(self) -> None:
        """Mark context as released and available."""
        self.current_test = None
        self.state = ContextState.AVAILABLE
        self.last_used_at = time.time()


# Alias for backwards compatibility
BrowserContext = PooledContext


class BrowserPool:
    """
    Pool of browser contexts for parallel test execution.

    Features:
    - Efficient context reuse with lifecycle management
    - Automatic cleanup of idle/stale contexts
    - Health checks and recovery
    - Resource-aware scaling
    - Async-first with proper cancellation handling

    SDK v2 Notes:
        - Uses OwlBrowser.create_context() to get context_id
        - acquire() yields context_id string for use with browser methods
        - All browser operations done via browser.method(context_id=...)

    Usage:
        async with BrowserPool(browser, config) as pool:
            async with pool.acquire("my_test") as context_id:
                # Use context_id with browser methods
                await browser.navigate(context_id=context_id, url="https://example.com")
    """

    def __init__(
        self,
        browser: OwlBrowser,
        config: ConcurrencyConfig,
        resource_monitor: ResourceMonitor | None = None,
    ) -> None:
        """
        Initialize browser pool.

        Args:
            browser: The owl-browser SDK v2 instance
            config: Concurrency configuration
            resource_monitor: Optional resource monitor for adaptive scaling
        """
        self._browser = browser
        self._config = config
        self._resource_monitor = resource_monitor

        self._contexts: dict[str, PooledContext] = {}
        self._available: asyncio.Queue[str] = asyncio.Queue()
        self._lock = asyncio.Lock()
        self._cleanup_task: asyncio.Task[None] | None = None
        self._running = False
        self._closed = False

        self._log = logger.bind(component="browser_pool")

        # Statistics
        self._stats = {
            "total_created": 0,
            "total_recycled": 0,
            "total_failed": 0,
            "total_acquisitions": 0,
            "total_releases": 0,
        }

    @property
    def size(self) -> int:
        """Get current pool size."""
        return len(self._contexts)

    @property
    def available_count(self) -> int:
        """Get number of available contexts."""
        return self._available.qsize()

    @property
    def in_use_count(self) -> int:
        """Get number of contexts in use."""
        return sum(
            1 for c in self._contexts.values()
            if c.state == ContextState.IN_USE
        )

    @property
    def statistics(self) -> dict[str, Any]:
        """Get pool statistics."""
        return {
            **self._stats,
            "current_size": self.size,
            "available": self.available_count,
            "in_use": self.in_use_count,
        }

    async def start(self) -> None:
        """
        Start the pool and initialize minimum contexts.

        Called automatically when using as async context manager.
        """
        if self._running:
            return

        self._running = True
        self._log.info(
            "Starting browser pool",
            max_parallel=self._config.max_parallel_tests,
            max_contexts=self._config.max_browser_contexts,
            min_contexts=self._config.min_browser_contexts,
        )

        # Create minimum contexts
        for _ in range(self._config.min_browser_contexts):
            try:
                await self._create_context()
            except Exception as e:
                self._log.warning("Failed to create initial context", error=str(e))

        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        self._log.info("Browser pool started", initial_size=self.size)

    async def stop(self) -> None:
        """
        Stop the pool and clean up all contexts.

        Waits for in-use contexts to be released with timeout.
        """
        if not self._running:
            return

        self._running = False
        self._log.info("Stopping browser pool")

        # Stop cleanup task
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task

        # Wait for in-use contexts with timeout
        timeout = self._config.graceful_shutdown_timeout_seconds
        start = time.monotonic()

        while self.in_use_count > 0 and (time.monotonic() - start) < timeout:
            await asyncio.sleep(0.5)
            self._log.debug(
                "Waiting for contexts to be released",
                in_use=self.in_use_count,
            )

        # Force close all contexts
        async with self._lock:
            for ctx in list(self._contexts.values()):
                await self._close_context(ctx)
            self._contexts.clear()

        self._closed = True
        self._log.info("Browser pool stopped", stats=self._stats)

    @contextlib.asynccontextmanager
    async def acquire(
        self,
        test_name: str | None = None,
        timeout: float | None = None,
    ) -> AsyncIterator[str]:
        """
        Acquire a browser context from the pool.

        SDK v2 Notes:
            - Yields context_id string for use with browser methods
            - Caller uses: await browser.navigate(context_id=context_id, url=...)

        Usage:
            async with pool.acquire("my_test") as context_id:
                await browser.navigate(context_id=context_id, url="https://example.com")

        Args:
            test_name: Optional name of the test for tracking
            timeout: Acquisition timeout (uses config default if not specified)

        Yields:
            The context_id string for browser operations

        Raises:
            PoolExhaustedError: If no context available within timeout
            ContextAcquisitionError: If acquisition fails
        """
        if self._closed:
            raise BrowserPoolError("Pool is closed")

        effective_timeout = timeout or self._config.acquire_timeout_seconds
        pooled_context = await self._acquire_context(test_name, effective_timeout)

        try:
            yield pooled_context.context_id
        finally:
            await self._release_context(pooled_context)

    async def _acquire_context(
        self,
        test_name: str | None,
        timeout: float,
    ) -> PooledContext:
        """Acquire a context from the pool or create new one."""
        self._stats["total_acquisitions"] += 1
        start = time.monotonic()

        while (time.monotonic() - start) < timeout:
            # Try to get available context
            try:
                pool_id = await asyncio.wait_for(
                    self._available.get(),
                    timeout=min(1.0, timeout - (time.monotonic() - start)),
                )

                async with self._lock:
                    pooled_context = self._contexts.get(pool_id)
                    if pooled_context is None:
                        continue

                    # Check if context needs recycling
                    if self._should_recycle(pooled_context):
                        await self._recycle_context(pooled_context)
                        continue

                    # Check context health
                    if not await self._check_context_health(pooled_context):
                        await self._recycle_context(pooled_context)
                        continue

                    pooled_context.mark_used(test_name)
                    self._log.debug(
                        "Context acquired",
                        pool_id=pooled_context.id,
                        context_id=pooled_context.context_id,
                        test=test_name,
                        use_count=pooled_context.use_count,
                    )
                    return pooled_context

            except asyncio.TimeoutError:
                # No available context, try to create new one
                pass

            # Try to create new context if pool not full
            async with self._lock:
                if self.size < self._config.max_browser_contexts:
                    # Check resource constraints
                    if self._resource_monitor is not None:
                        snapshot = self._resource_monitor.take_snapshot()
                        if not snapshot.can_scale_up and self.size > 0:
                            self._log.debug(
                                "Resource constraints prevent new context",
                                pressure=snapshot.memory_pressure.name,
                            )
                            continue

                    # Create context without adding to available queue
                    # since we're immediately acquiring it
                    pooled_context = await self._create_context(make_available=False)
                    if pooled_context is not None:
                        pooled_context.mark_used(test_name)
                        self._log.debug(
                            "New context created and acquired",
                            pool_id=pooled_context.id,
                            context_id=pooled_context.context_id,
                            test=test_name,
                        )
                        return pooled_context

            # Brief wait before retry
            await asyncio.sleep(0.1)

        raise PoolExhaustedError(
            f"Could not acquire browser context within {timeout}s "
            f"(pool size: {self.size}, available: {self.available_count})"
        )

    async def _release_context(self, pooled_context: PooledContext) -> None:
        """Release a context back to the pool."""
        self._stats["total_releases"] += 1

        async with self._lock:
            if pooled_context.id not in self._contexts:
                self._log.warning(
                    "Released context not in pool",
                    pool_id=pooled_context.id,
                )
                return

            # Check if context should be recycled
            if self._should_recycle(pooled_context):
                await self._recycle_context(pooled_context)
                return

            # Mark as available
            pooled_context.mark_released()
            await self._available.put(pooled_context.id)

            self._log.debug(
                "Context released",
                pool_id=pooled_context.id,
                context_id=pooled_context.context_id,
                use_count=pooled_context.use_count,
            )

    async def _create_context(self, make_available: bool = True) -> PooledContext | None:
        """
        Create a new browser context.

        SDK v2 Notes:
            - Uses browser.create_context() to get context_id
            - Stores context_id for later browser operations

        Args:
            make_available: If True, add to available queue. If False, caller
                           is responsible for managing the context state.
        """
        try:
            # SDK v2: create_context returns dict with context_id
            result = await self._browser.create_context()
            browser_context_id = result["context_id"]
            pool_id = str(uuid.uuid4())[:8]

            pooled_context = PooledContext(
                id=pool_id,
                context_id=browser_context_id,
            )

            self._contexts[pool_id] = pooled_context
            if make_available:
                await self._available.put(pool_id)
            self._stats["total_created"] += 1

            self._log.debug(
                "Created browser context",
                pool_id=pool_id,
                context_id=browser_context_id,
            )
            return pooled_context

        except Exception as e:
            self._stats["total_failed"] += 1
            self._log.error("Failed to create browser context", error=str(e))
            return None

    async def _recycle_context(self, pooled_context: PooledContext) -> None:
        """Recycle a context by closing and replacing it."""
        pooled_context.state = ContextState.RECYCLING
        self._stats["total_recycled"] += 1

        self._log.debug(
            "Recycling context",
            pool_id=pooled_context.id,
            context_id=pooled_context.context_id,
            age=pooled_context.age_seconds,
            uses=pooled_context.use_count,
        )

        # Close old context
        await self._close_context(pooled_context)

        # Remove from pool
        self._contexts.pop(pooled_context.id, None)

        # Create replacement if pool below minimum
        if self.size < self._config.min_browser_contexts:
            await self._create_context()

    async def _close_context(self, pooled_context: PooledContext) -> None:
        """Close a browser context safely."""
        try:
            # SDK v2: use close_context with context_id
            await self._browser.close_context(context_id=pooled_context.context_id)
        except Exception as e:
            self._log.debug(
                "Error closing context",
                pool_id=pooled_context.id,
                context_id=pooled_context.context_id,
                error=str(e),
            )

    def _should_recycle(self, pooled_context: PooledContext) -> bool:
        """Check if a context should be recycled."""
        # Check use count
        if pooled_context.use_count >= self._config.context_max_uses:
            return True

        # Check age
        if pooled_context.age_seconds >= self._config.context_max_age_seconds:
            return True

        # Check idle time (only for available contexts)
        if (
            pooled_context.state == ContextState.AVAILABLE
            and pooled_context.idle_seconds >= self._config.context_idle_timeout_seconds
            and self.size > self._config.min_browser_contexts
        ):
            return True

        return False

    async def _check_context_health(self, pooled_context: PooledContext) -> bool:
        """Check if a context is healthy and usable."""
        try:
            # SDK v2: Try get_page_info to verify context is alive
            await self._browser.get_page_info(context_id=pooled_context.context_id)
            return True
        except Exception as e:
            self._log.warning(
                "Context health check failed",
                pool_id=pooled_context.id,
                context_id=pooled_context.context_id,
                error=str(e),
            )
            pooled_context.state = ContextState.FAILED
            return False

    async def _cleanup_loop(self) -> None:
        """Background loop for cleaning up idle/stale contexts."""
        while self._running:
            try:
                await asyncio.sleep(self._config.monitoring_interval_seconds)

                async with self._lock:
                    # Find contexts to recycle
                    to_recycle: list[BrowserContext] = []

                    for context in self._contexts.values():
                        if context.state == ContextState.AVAILABLE and self._should_recycle(context):
                            to_recycle.append(context)

                    # Respect minimum pool size
                    max_recycle = max(
                        0,
                        self.size - self._config.min_browser_contexts,
                    )
                    to_recycle = to_recycle[:max_recycle]

                    # Recycle contexts
                    for context in to_recycle:
                        # Remove from available queue
                        new_queue: asyncio.Queue[str] = asyncio.Queue()
                        while not self._available.empty():
                            ctx_id = self._available.get_nowait()
                            if ctx_id != context.id:
                                await new_queue.put(ctx_id)
                        self._available = new_queue

                        await self._recycle_context(context)

                    if to_recycle:
                        self._log.info(
                            "Cleaned up idle contexts",
                            count=len(to_recycle),
                            pool_size=self.size,
                        )

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._log.error("Error in cleanup loop", error=str(e))

    async def __aenter__(self) -> BrowserPool:
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Async context manager exit."""
        await self.stop()
