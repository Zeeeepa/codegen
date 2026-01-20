"""
Resource monitoring for adaptive concurrency scaling.

Monitors system resources (memory, CPU) and provides signals
for dynamic adjustment of parallelism levels.
"""

from __future__ import annotations

import asyncio
import platform
import time
from dataclasses import dataclass
from enum import IntEnum, auto
from typing import TYPE_CHECKING, Callable

import structlog

if TYPE_CHECKING:
    from autoqa.concurrency.config import ConcurrencyConfig, ResourceLimits

logger = structlog.get_logger(__name__)


class MemoryPressure(IntEnum):
    """Memory pressure levels for scaling decisions."""

    NONE = auto()
    """Normal memory usage - can scale up."""

    LOW = auto()
    """Approaching threshold - avoid scaling up."""

    MEDIUM = auto()
    """At threshold - should consider scaling down."""

    HIGH = auto()
    """Above threshold - actively scale down."""

    CRITICAL = auto()
    """Critical - force immediate scale down."""


@dataclass(frozen=True, slots=True)
class ResourceSnapshot:
    """
    Point-in-time snapshot of system resources.

    Immutable record of resource state for analysis.
    """

    timestamp: float
    """Unix timestamp of snapshot."""

    memory_used_percent: float
    """Current memory usage percentage (0-100)."""

    memory_available_mb: int
    """Available memory in megabytes."""

    memory_total_mb: int
    """Total system memory in megabytes."""

    cpu_percent: float
    """Current CPU usage percentage (0-100)."""

    memory_pressure: MemoryPressure
    """Calculated memory pressure level."""

    recommended_parallelism: int
    """Recommended parallelism based on resources."""

    @property
    def is_healthy(self) -> bool:
        """Check if resources are healthy for normal operation."""
        return self.memory_pressure <= MemoryPressure.LOW

    @property
    def should_scale_down(self) -> bool:
        """Check if resources indicate need to scale down."""
        return self.memory_pressure >= MemoryPressure.MEDIUM

    @property
    def can_scale_up(self) -> bool:
        """Check if resources allow scaling up."""
        return self.memory_pressure == MemoryPressure.NONE


def _get_memory_info() -> tuple[int, int, float]:
    """
    Get system memory information.

    Returns:
        Tuple of (available_mb, total_mb, used_percent)
    """
    try:
        # Try psutil first (most accurate)
        import psutil
        mem = psutil.virtual_memory()
        return (
            int(mem.available / (1024 * 1024)),
            int(mem.total / (1024 * 1024)),
            mem.percent,
        )
    except ImportError:
        pass

    # Fallback for macOS/Linux without psutil
    system = platform.system()

    if system == "Darwin":
        # macOS fallback using vm_stat
        import subprocess
        try:
            result = subprocess.run(
                ["vm_stat"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            lines = result.stdout.split("\n")
            page_size = 4096
            stats: dict[str, int] = {}

            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().lower()
                    value = value.strip().rstrip(".")
                    try:
                        stats[key] = int(value)
                    except ValueError:
                        continue

            free_pages = stats.get("pages free", 0)
            inactive_pages = stats.get("pages inactive", 0)
            speculative_pages = stats.get("pages speculative", 0)
            available_mb = int(
                (free_pages + inactive_pages + speculative_pages) * page_size
                / (1024 * 1024)
            )

            # Get total memory
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            total_mb = int(int(result.stdout.strip()) / (1024 * 1024))
            used_percent = ((total_mb - available_mb) / total_mb) * 100

            return available_mb, total_mb, used_percent

        except Exception:
            pass

    elif system == "Linux":
        # Linux fallback using /proc/meminfo
        try:
            with open("/proc/meminfo") as f:
                meminfo: dict[str, int] = {}
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        key = parts[0].rstrip(":")
                        value = int(parts[1])  # in kB
                        meminfo[key] = value

                total_mb = meminfo.get("MemTotal", 0) // 1024
                available_mb = meminfo.get(
                    "MemAvailable",
                    meminfo.get("MemFree", 0) + meminfo.get("Buffers", 0) + meminfo.get("Cached", 0),
                ) // 1024
                used_percent = ((total_mb - available_mb) / total_mb) * 100 if total_mb > 0 else 0

                return available_mb, total_mb, used_percent

        except Exception:
            pass

    # Ultimate fallback: assume 8GB total, 50% used
    logger.warning("Could not determine memory info, using defaults")
    return 4096, 8192, 50.0


def _get_cpu_percent() -> float:
    """
    Get current CPU usage percentage.

    Returns:
        CPU usage percentage (0-100)
    """
    try:
        import psutil
        return psutil.cpu_percent(interval=0.1)
    except ImportError:
        pass

    # Fallback: no CPU monitoring
    return 0.0


class ResourceMonitor:
    """
    Monitors system resources for adaptive concurrency control.

    Provides:
    - Periodic resource snapshots
    - Memory pressure calculation
    - Parallelism recommendations
    - Callback notifications for threshold crossings

    Thread-safe and designed for async operation.
    """

    def __init__(
        self,
        config: ConcurrencyConfig,
        on_pressure_change: Callable[[MemoryPressure, MemoryPressure], None] | None = None,
    ) -> None:
        """
        Initialize resource monitor.

        Args:
            config: Concurrency configuration
            on_pressure_change: Callback for pressure level changes
        """
        self._config = config
        self._limits = config.resource_limits
        self._on_pressure_change = on_pressure_change
        self._current_pressure = MemoryPressure.NONE
        self._last_snapshot: ResourceSnapshot | None = None
        self._monitoring_task: asyncio.Task[None] | None = None
        self._running = False
        self._log = logger.bind(component="resource_monitor")

    @property
    def current_pressure(self) -> MemoryPressure:
        """Get current memory pressure level."""
        return self._current_pressure

    @property
    def last_snapshot(self) -> ResourceSnapshot | None:
        """Get most recent resource snapshot."""
        return self._last_snapshot

    def take_snapshot(self) -> ResourceSnapshot:
        """
        Take an immediate resource snapshot.

        Thread-safe and can be called at any time.
        """
        available_mb, total_mb, memory_percent = _get_memory_info()
        cpu_percent = _get_cpu_percent()

        # Calculate memory pressure
        pressure = self._calculate_pressure(memory_percent, available_mb)

        # Calculate recommended parallelism
        recommended = self._calculate_recommended_parallelism(
            available_mb, memory_percent, pressure
        )

        snapshot = ResourceSnapshot(
            timestamp=time.time(),
            memory_used_percent=memory_percent,
            memory_available_mb=available_mb,
            memory_total_mb=total_mb,
            cpu_percent=cpu_percent,
            memory_pressure=pressure,
            recommended_parallelism=recommended,
        )

        self._last_snapshot = snapshot
        return snapshot

    def _calculate_pressure(
        self,
        memory_percent: float,
        available_mb: int,
    ) -> MemoryPressure:
        """Calculate memory pressure level from metrics."""
        # Check critical threshold first
        if memory_percent >= self._limits.critical_memory_percent:
            return MemoryPressure.CRITICAL

        # Check available memory minimum
        if available_mb < self._limits.min_available_memory_mb:
            return MemoryPressure.HIGH

        # Check high threshold
        if memory_percent >= self._limits.max_memory_percent:
            return MemoryPressure.HIGH

        # Check medium threshold (80% of max)
        medium_threshold = self._limits.max_memory_percent * 0.9
        if memory_percent >= medium_threshold:
            return MemoryPressure.MEDIUM

        # Check low threshold (70% of max)
        low_threshold = self._limits.max_memory_percent * 0.8
        if memory_percent >= low_threshold:
            return MemoryPressure.LOW

        return MemoryPressure.NONE

    def _calculate_recommended_parallelism(
        self,
        available_mb: int,
        memory_percent: float,  # noqa: ARG002
        pressure: MemoryPressure,
    ) -> int:
        """Calculate recommended parallelism level."""
        max_parallel = self._config.max_parallel_tests
        context_estimate = self._limits.context_memory_estimate_mb

        # Calculate how many contexts we can support based on memory
        memory_based_max = max(1, available_mb // context_estimate)

        # Adjust based on pressure level
        match pressure:
            case MemoryPressure.NONE:
                # Can use full parallelism
                return min(max_parallel, memory_based_max)

            case MemoryPressure.LOW:
                # Slight reduction
                return min(max_parallel, memory_based_max, max(1, max_parallel - 1))

            case MemoryPressure.MEDIUM:
                # Moderate reduction
                return min(max_parallel // 2, memory_based_max, max(1, max_parallel - 2))

            case MemoryPressure.HIGH:
                # Significant reduction
                return min(2, memory_based_max, max(1, max_parallel // 3))

            case MemoryPressure.CRITICAL:
                # Minimum parallelism
                return 1

    async def start_monitoring(self) -> None:
        """Start background resource monitoring."""
        if self._running:
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self._log.info("Resource monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop background resource monitoring."""
        self._running = False

        if self._monitoring_task is not None:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None

        self._log.info("Resource monitoring stopped")

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while self._running:
            try:
                snapshot = self.take_snapshot()

                # Check for pressure level change
                if snapshot.memory_pressure != self._current_pressure:
                    old_pressure = self._current_pressure
                    self._current_pressure = snapshot.memory_pressure

                    self._log.info(
                        "Memory pressure changed",
                        old=old_pressure.name,
                        new=snapshot.memory_pressure.name,
                        memory_percent=snapshot.memory_used_percent,
                        available_mb=snapshot.memory_available_mb,
                        recommended_parallelism=snapshot.recommended_parallelism,
                    )

                    if self._on_pressure_change is not None:
                        try:
                            self._on_pressure_change(old_pressure, snapshot.memory_pressure)
                        except Exception as e:
                            self._log.error(
                                "Error in pressure change callback",
                                error=str(e),
                            )

                await asyncio.sleep(self._config.monitoring_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._log.error("Error in monitoring loop", error=str(e))
                await asyncio.sleep(self._config.monitoring_interval_seconds)

    async def wait_for_healthy_resources(
        self,
        timeout_seconds: float = 30.0,
    ) -> bool:
        """
        Wait until resources are healthy.

        Args:
            timeout_seconds: Maximum time to wait

        Returns:
            True if resources became healthy, False on timeout
        """
        start = time.monotonic()

        while (time.monotonic() - start) < timeout_seconds:
            snapshot = self.take_snapshot()
            if snapshot.is_healthy:
                return True

            await asyncio.sleep(1.0)

        return False

    async def __aenter__(self) -> ResourceMonitor:
        """Async context manager entry."""
        await self.start_monitoring()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Async context manager exit."""
        await self.stop_monitoring()
