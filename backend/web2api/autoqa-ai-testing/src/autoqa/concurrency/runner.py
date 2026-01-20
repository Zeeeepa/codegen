"""
Async test runner with concurrency control.

Provides parallel test execution with:
- Semaphore-based concurrency limiting
- Browser pool integration
- Resource-aware scaling
- Proper async context management
- Both sync and async entry points
"""

from __future__ import annotations

import asyncio
import time
import traceback
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Callable, Sequence

import structlog

from autoqa.concurrency.browser_pool import BrowserPool
from autoqa.concurrency.config import ConcurrencyConfig, ScalingStrategy, load_concurrency_config
from autoqa.concurrency.resource_monitor import MemoryPressure, ResourceMonitor
from autoqa.dsl.models import TestSpec, TestSuite
from autoqa.runner.self_healing import SelfHealingEngine
from autoqa.runner.test_runner import StepStatus, TestRunResult

if TYPE_CHECKING:
    from owl_browser import Browser
    from owl_browser import BrowserContext as OwlBrowserContext

logger = structlog.get_logger(__name__)


@dataclass
class TestExecutionContext:
    """
    Context for a single test execution.

    Contains all information needed to execute and track a test.
    """

    spec: TestSpec
    """Test specification to execute."""

    variables: dict[str, Any] = field(default_factory=dict)
    """Variables for interpolation."""

    priority: int = 0
    """Execution priority (lower = higher priority)."""

    timeout_seconds: float = 600.0
    """Maximum execution time."""

    retry_count: int = 0
    """Current retry count."""

    max_retries: int = 2
    """Maximum retries for this test."""


@dataclass
class ParallelExecutionResult:
    """
    Result of parallel test execution.

    Aggregates results from multiple concurrent tests.
    """

    suite_name: str | None
    """Name of the test suite, if applicable."""

    started_at: datetime
    """When execution started."""

    finished_at: datetime | None = None
    """When execution completed."""

    duration_ms: int = 0
    """Total execution time in milliseconds."""

    total_tests: int = 0
    """Total number of tests executed."""

    passed_tests: int = 0
    """Number of passed tests."""

    failed_tests: int = 0
    """Number of failed tests."""

    skipped_tests: int = 0
    """Number of skipped tests."""

    results: list[TestRunResult] = field(default_factory=list)
    """Individual test results."""

    max_parallelism_reached: int = 0
    """Maximum concurrent tests reached."""

    resource_scaling_events: int = 0
    """Number of resource-based scaling events."""

    context_failures: int = 0
    """Number of browser context failures."""

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100

    @property
    def is_success(self) -> bool:
        """Check if all executed tests passed."""
        return self.failed_tests == 0


class AsyncTestRunner:
    """
    Async test runner with concurrent execution support.

    Features:
    - Parallel test execution with configurable concurrency
    - Browser context pooling for efficiency
    - Resource-aware dynamic scaling
    - Proper cleanup and error handling
    - Support for both individual tests and suites

    Usage:
        async with AsyncTestRunner(browser, config) as runner:
            results = await runner.run_tests(specs)

    Or with sync entry point:
        runner = AsyncTestRunner(browser, config)
        results = runner.run_tests_sync(specs)
    """

    def __init__(
        self,
        browser: Browser,
        config: ConcurrencyConfig | None = None,
        healing_engine: SelfHealingEngine | None = None,
        artifact_dir: str = "./artifacts",
        record_video: bool = False,
        screenshot_on_failure: bool = True,
        default_timeout_ms: int = 30000,
        wait_for_network_idle: bool = True,
        enable_versioning: bool = False,
        versioning_storage_path: str = ".autoqa/history",
        on_test_complete: Callable[[TestRunResult], None] | None = None,
    ) -> None:
        """
        Initialize async test runner.

        Args:
            browser: The owl-browser instance
            config: Concurrency configuration (loads from env if not provided)
            healing_engine: Self-healing engine for selector recovery
            artifact_dir: Directory for test artifacts
            record_video: Enable video recording
            screenshot_on_failure: Capture screenshots on failure
            default_timeout_ms: Default timeout for operations
            wait_for_network_idle: Wait for network idle after navigation
            enable_versioning: Enable test version tracking
            versioning_storage_path: Path for version history
            on_test_complete: Callback when each test completes
        """
        self._browser = browser
        self._config = config or load_concurrency_config()
        self._healing_engine = healing_engine or SelfHealingEngine()
        self._artifact_dir = artifact_dir
        self._record_video = record_video
        self._screenshot_on_failure = screenshot_on_failure
        self._default_timeout_ms = default_timeout_ms
        self._wait_for_network_idle = wait_for_network_idle
        self._enable_versioning = enable_versioning
        self._versioning_storage_path = versioning_storage_path
        self._on_test_complete = on_test_complete

        self._pool: BrowserPool | None = None
        self._resource_monitor: ResourceMonitor | None = None
        self._semaphore: asyncio.Semaphore | None = None
        self._current_parallelism: int = self._config.max_parallel_tests
        self._running = False

        self._log = logger.bind(component="async_test_runner")

    async def start(self) -> None:
        """
        Start the runner and initialize resources.

        Called automatically when using as async context manager.
        """
        if self._running:
            return

        self._log.info(
            "Starting async test runner",
            max_parallel=self._config.max_parallel_tests,
            strategy=self._config.scaling_strategy,
        )

        # Initialize resource monitor
        if self._config.enable_resource_monitoring:
            self._resource_monitor = ResourceMonitor(
                self._config,
                on_pressure_change=self._on_pressure_change,
            )
            await self._resource_monitor.start_monitoring()

        # Initialize browser pool
        self._pool = BrowserPool(
            self._browser,
            self._config,
            self._resource_monitor,
        )
        await self._pool.start()

        # Initialize semaphore
        self._semaphore = asyncio.Semaphore(self._config.max_parallel_tests)
        self._current_parallelism = self._config.max_parallel_tests

        self._running = True
        self._log.info("Async test runner started")

    async def stop(self) -> None:
        """
        Stop the runner and clean up resources.

        Called automatically when using as async context manager.
        """
        if not self._running:
            return

        self._running = False
        self._log.info("Stopping async test runner")

        # Stop browser pool
        if self._pool is not None:
            await self._pool.stop()

        # Stop resource monitor
        if self._resource_monitor is not None:
            await self._resource_monitor.stop_monitoring()

        self._log.info("Async test runner stopped")

    async def run_tests(
        self,
        specs: Sequence[TestSpec],
        variables: dict[str, Any] | None = None,
        fail_fast: bool = False,
    ) -> ParallelExecutionResult:
        """
        Run multiple tests in parallel.

        Args:
            specs: Test specifications to run
            variables: Shared variables for all tests
            fail_fast: Stop on first failure

        Returns:
            Aggregated results from all tests
        """
        if not self._running:
            await self.start()

        result = ParallelExecutionResult(
            suite_name=None,
            started_at=datetime.now(UTC),
            total_tests=len(specs),
        )

        if not specs:
            result.finished_at = datetime.now(UTC)
            return result

        self._log.info(
            "Starting parallel test execution",
            test_count=len(specs),
            max_parallel=self._current_parallelism,
        )

        # Create execution contexts
        contexts = [
            TestExecutionContext(
                spec=spec,
                variables={**(variables or {}), **spec.variables},
            )
            for spec in specs
        ]

        # Track concurrent tests
        concurrent_count = 0
        max_concurrent = 0
        fail_fast_triggered = False

        async def run_single_test(ctx: TestExecutionContext) -> TestRunResult | None:
            nonlocal concurrent_count, max_concurrent, fail_fast_triggered

            if fail_fast_triggered:
                return None

            if self._semaphore is None:
                raise RuntimeError("Runner not started")

            async with self._semaphore:
                concurrent_count += 1
                max_concurrent = max(max_concurrent, concurrent_count)

                try:
                    test_result = await self._execute_test(ctx)

                    if fail_fast and test_result.status == StepStatus.FAILED:
                        fail_fast_triggered = True

                    if self._on_test_complete is not None:
                        try:
                            self._on_test_complete(test_result)
                        except Exception as e:
                            self._log.warning(
                                "Error in test complete callback",
                                error=str(e),
                            )

                    return test_result

                finally:
                    concurrent_count -= 1

        # Run tests concurrently
        tasks = [
            asyncio.create_task(run_single_test(ctx))
            for ctx in contexts
        ]

        try:
            done_results = await asyncio.gather(*tasks, return_exceptions=True)

            for res in done_results:
                if res is None:
                    result.skipped_tests += 1
                elif isinstance(res, Exception):
                    self._log.error("Test execution raised exception", error=str(res))
                    result.failed_tests += 1
                else:
                    result.results.append(res)
                    if res.status == StepStatus.PASSED:
                        result.passed_tests += 1
                    elif res.status == StepStatus.FAILED:
                        result.failed_tests += 1
                    else:
                        result.skipped_tests += 1

        except asyncio.CancelledError:
            self._log.warning("Test execution cancelled")
            for task in tasks:
                task.cancel()
            raise

        result.max_parallelism_reached = max_concurrent
        result.finished_at = datetime.now(UTC)
        result.duration_ms = int(
            (result.finished_at - result.started_at).total_seconds() * 1000
        )

        self._log.info(
            "Parallel test execution completed",
            total=result.total_tests,
            passed=result.passed_tests,
            failed=result.failed_tests,
            duration_ms=result.duration_ms,
            max_concurrent=result.max_parallelism_reached,
        )

        return result

    async def run_suite(
        self,
        suite: TestSuite,
        variables: dict[str, Any] | None = None,
    ) -> ParallelExecutionResult:
        """
        Run a test suite with parallel or sequential execution.

        Uses suite's parallel_execution setting to determine execution mode.

        Args:
            suite: Test suite to run
            variables: Additional variables

        Returns:
            Aggregated results from all tests
        """
        combined_vars = {**(variables or {}), **suite.variables}

        if suite.parallel_execution:
            result = await self.run_tests(
                suite.tests,
                variables=combined_vars,
                fail_fast=suite.fail_fast,
            )
        else:
            # Sequential execution
            result = ParallelExecutionResult(
                suite_name=suite.name,
                started_at=datetime.now(UTC),
                total_tests=len(suite.tests),
            )

            for spec in suite.tests:
                test_vars = {**combined_vars, **spec.variables}
                ctx = TestExecutionContext(spec=spec, variables=test_vars)

                test_result = await self._execute_test(ctx)
                result.results.append(test_result)

                if test_result.status == StepStatus.PASSED:
                    result.passed_tests += 1
                elif test_result.status == StepStatus.FAILED:
                    result.failed_tests += 1
                    if suite.fail_fast:
                        break
                else:
                    result.skipped_tests += 1

            result.finished_at = datetime.now(UTC)
            result.duration_ms = int(
                (result.finished_at - result.started_at).total_seconds() * 1000
            )

        result.suite_name = suite.name
        return result

    async def run_spec(
        self,
        spec: TestSpec,
        variables: dict[str, Any] | None = None,
    ) -> TestRunResult:
        """
        Run a single test specification.

        Args:
            spec: Test specification
            variables: Additional variables

        Returns:
            Test run result
        """
        if not self._running:
            await self.start()

        ctx = TestExecutionContext(
            spec=spec,
            variables={**(variables or {}), **spec.variables},
        )

        return await self._execute_test(ctx)

    def run_tests_sync(
        self,
        specs: Sequence[TestSpec],
        variables: dict[str, Any] | None = None,
        fail_fast: bool = False,
    ) -> ParallelExecutionResult:
        """
        Synchronous entry point for running tests.

        Runs the async execution in an event loop.

        Args:
            specs: Test specifications to run
            variables: Shared variables for all tests
            fail_fast: Stop on first failure

        Returns:
            Aggregated results from all tests
        """
        return asyncio.run(self._run_with_lifecycle(specs, variables, fail_fast))

    async def _run_with_lifecycle(
        self,
        specs: Sequence[TestSpec],
        variables: dict[str, Any] | None,
        fail_fast: bool,
    ) -> ParallelExecutionResult:
        """Run tests with automatic lifecycle management."""
        async with self:
            return await self.run_tests(specs, variables, fail_fast)

    async def _execute_test(
        self,
        ctx: TestExecutionContext,
    ) -> TestRunResult:
        """Execute a single test with browser context from pool."""
        if self._pool is None:
            raise RuntimeError("Browser pool not initialized")

        start_time = time.monotonic()

        for attempt in range(ctx.max_retries + 1):
            try:
                async with self._pool.acquire(ctx.spec.name, ctx.timeout_seconds) as page:
                    result = await self._run_test_in_context(ctx, page)
                    return result

            except Exception as e:
                if attempt < ctx.max_retries and self._config.retry_on_context_failure:
                    self._log.warning(
                        "Test execution failed, retrying",
                        test=ctx.spec.name,
                        attempt=attempt + 1,
                        max_retries=ctx.max_retries,
                        error=str(e),
                    )
                    ctx.retry_count = attempt + 1
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue

                # Return failure result
                duration_ms = int((time.monotonic() - start_time) * 1000)
                return TestRunResult(
                    test_name=ctx.spec.name,
                    status=StepStatus.FAILED,
                    started_at=datetime.now(UTC),
                    finished_at=datetime.now(UTC),
                    duration_ms=duration_ms,
                    error=str(e),
                    total_steps=len(ctx.spec.steps),
                )

        # Should not reach here, but safety fallback
        return TestRunResult(
            test_name=ctx.spec.name,
            status=StepStatus.FAILED,
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
            error="Max retries exceeded",
            total_steps=len(ctx.spec.steps),
        )

    async def _run_test_in_context(
        self,
        ctx: TestExecutionContext,
        page: OwlBrowserContext,
    ) -> TestRunResult:
        """
        Run test using existing TestRunner in a sync thread.

        Uses run_in_executor to avoid blocking the event loop.
        """
        from autoqa.runner.test_runner import TestRunner

        loop = asyncio.get_event_loop()

        def run_sync() -> TestRunResult:
            runner = TestRunner(
                browser=self._browser,
                healing_engine=self._healing_engine,
                artifact_dir=self._artifact_dir,
                record_video=self._record_video,
                screenshot_on_failure=self._screenshot_on_failure,
                default_timeout_ms=self._default_timeout_ms,
                wait_for_network_idle=self._wait_for_network_idle,
                enable_versioning=self._enable_versioning,
                versioning_storage_path=self._versioning_storage_path,
            )
            return runner.run_spec(ctx.spec, page=page, variables=ctx.variables)

        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(None, run_sync),
                timeout=ctx.timeout_seconds,
            )
            return result

        except asyncio.TimeoutError:
            self._log.error(
                "Test execution timed out",
                test=ctx.spec.name,
                timeout=ctx.timeout_seconds,
            )
            return TestRunResult(
                test_name=ctx.spec.name,
                status=StepStatus.FAILED,
                started_at=datetime.now(UTC),
                finished_at=datetime.now(UTC),
                error=f"Test execution timed out after {ctx.timeout_seconds}s",
                total_steps=len(ctx.spec.steps),
            )

    def _on_pressure_change(
        self,
        old_pressure: MemoryPressure,
        new_pressure: MemoryPressure,
    ) -> None:
        """Handle memory pressure changes for adaptive scaling."""
        if self._config.scaling_strategy != ScalingStrategy.ADAPTIVE:
            return

        # Calculate new parallelism based on pressure
        max_parallel = self._config.max_parallel_tests

        match new_pressure:
            case MemoryPressure.NONE:
                new_parallelism = max_parallel
            case MemoryPressure.LOW:
                new_parallelism = max(1, max_parallel - 1)
            case MemoryPressure.MEDIUM:
                new_parallelism = max(1, max_parallel // 2)
            case MemoryPressure.HIGH:
                new_parallelism = max(1, max_parallel // 3)
            case MemoryPressure.CRITICAL:
                new_parallelism = 1

        if new_parallelism != self._current_parallelism:
            self._log.info(
                "Adjusting parallelism due to resource pressure",
                old_parallelism=self._current_parallelism,
                new_parallelism=new_parallelism,
                pressure=new_pressure.name,
            )

            # Note: Cannot easily adjust semaphore limit after creation
            # This tracks intent; actual limiting happens via pool
            self._current_parallelism = new_parallelism

    async def __aenter__(self) -> AsyncTestRunner:
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


class ParallelCrawler:
    """
    Parallel page crawler for Auto Test Builder.

    Crawls multiple pages concurrently during test generation.
    """

    def __init__(
        self,
        browser: Browser,
        config: ConcurrencyConfig | None = None,
        max_concurrent_pages: int = 5,
    ) -> None:
        """
        Initialize parallel crawler.

        Args:
            browser: The owl-browser instance
            config: Concurrency configuration
            max_concurrent_pages: Maximum pages to crawl concurrently
        """
        self._browser = browser
        self._config = config or load_concurrency_config()
        self._max_concurrent = max_concurrent_pages
        self._pool: BrowserPool | None = None
        self._log = logger.bind(component="parallel_crawler")

    async def crawl_pages(
        self,
        urls: list[str],
        crawler_func: Callable[[OwlBrowserContext, str], dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Crawl multiple pages in parallel.

        Args:
            urls: URLs to crawl
            crawler_func: Function to execute on each page

        Returns:
            List of results from each page
        """
        if not urls:
            return []

        # Initialize pool if needed
        if self._pool is None:
            self._pool = BrowserPool(self._browser, self._config)
            await self._pool.start()

        semaphore = asyncio.Semaphore(self._max_concurrent)
        results: list[dict[str, Any]] = []

        async def crawl_single(url: str) -> dict[str, Any]:
            async with semaphore:
                if self._pool is None:
                    raise RuntimeError("Pool not initialized")

                async with self._pool.acquire(url) as page:
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(
                        None,
                        crawler_func,
                        page,
                        url,
                    )

        tasks = [asyncio.create_task(crawl_single(url)) for url in urls]

        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                results.append(result)
            except Exception as e:
                self._log.warning("Page crawl failed", error=str(e))
                results.append({"error": str(e)})

        return results

    async def close(self) -> None:
        """Close the crawler and release resources."""
        if self._pool is not None:
            await self._pool.stop()
            self._pool = None

    async def __aenter__(self) -> ParallelCrawler:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Async context manager exit."""
        await self.close()
