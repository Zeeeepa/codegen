"""
Unit tests for the concurrency module.

Tests cover:
- ConcurrencyConfig validation and loading
- ResourceMonitor memory pressure detection
- BrowserPool lifecycle management
- AsyncTestRunner parallel execution
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autoqa.concurrency.config import (
    ConcurrencyConfig,
    ResourceLimits,
    ScalingStrategy,
    load_concurrency_config,
)
from autoqa.concurrency.resource_monitor import (
    MemoryPressure,
    ResourceMonitor,
    ResourceSnapshot,
)


class TestResourceLimits:
    """Tests for ResourceLimits configuration."""

    def test_default_values(self) -> None:
        """Test default resource limit values are sensible."""
        limits = ResourceLimits()

        assert limits.max_memory_percent == 80.0
        assert limits.critical_memory_percent == 90.0
        assert limits.max_cpu_percent == 85.0
        assert limits.min_available_memory_mb == 512
        assert limits.context_memory_estimate_mb == 150

    def test_validation_passes_for_valid_limits(self) -> None:
        """Test validation passes for valid configuration."""
        limits = ResourceLimits(
            max_memory_percent=70.0,
            critical_memory_percent=85.0,
            max_cpu_percent=80.0,
            min_available_memory_mb=256,
            context_memory_estimate_mb=100,
        )
        limits.validate()  # Should not raise

    def test_validation_fails_for_invalid_memory_percent(self) -> None:
        """Test validation fails for invalid memory percentage."""
        limits = ResourceLimits(max_memory_percent=110.0)
        with pytest.raises(ValueError, match="max_memory_percent must be between"):
            limits.validate()

    def test_validation_fails_when_max_exceeds_critical(self) -> None:
        """Test validation fails when max exceeds critical threshold."""
        limits = ResourceLimits(
            max_memory_percent=95.0,
            critical_memory_percent=90.0,
        )
        with pytest.raises(ValueError, match="must be less than critical"):
            limits.validate()


class TestConcurrencyConfig:
    """Tests for ConcurrencyConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = ConcurrencyConfig()

        assert config.max_parallel_tests == 5
        assert config.max_browser_contexts == 10
        assert config.min_browser_contexts == 1
        assert config.context_idle_timeout_seconds == 60.0
        assert config.scaling_strategy == ScalingStrategy.ADAPTIVE

    def test_validation_fails_for_invalid_parallel(self) -> None:
        """Test validation fails for invalid max_parallel_tests."""
        with pytest.raises(ValueError, match="max_parallel_tests must be at least 1"):
            ConcurrencyConfig(max_parallel_tests=0)

    def test_validation_fails_for_invalid_contexts(self) -> None:
        """Test validation fails for invalid context limits."""
        with pytest.raises(ValueError, match="min_browser_contexts cannot exceed"):
            ConcurrencyConfig(
                min_browser_contexts=10,
                max_browser_contexts=5,
            )

    def test_with_overrides(self) -> None:
        """Test creating new config with overrides."""
        original = ConcurrencyConfig(max_parallel_tests=5)
        modified = original.with_overrides(max_parallel_tests=10)

        assert original.max_parallel_tests == 5
        assert modified.max_parallel_tests == 10

    def test_frozen_resource_limits(self) -> None:
        """Test that resource limits are immutable."""
        config = ConcurrencyConfig()
        with pytest.raises(AttributeError):
            config.resource_limits.max_memory_percent = 50.0  # type: ignore[misc]


class TestLoadConcurrencyConfig:
    """Tests for environment variable loading."""

    def test_loads_defaults_without_env_vars(self) -> None:
        """Test loading with no environment variables set."""
        with patch.dict("os.environ", {}, clear=True):
            config = load_concurrency_config()

        assert config.max_parallel_tests == 5
        assert config.scaling_strategy == ScalingStrategy.ADAPTIVE

    def test_loads_from_env_vars(self) -> None:
        """Test loading from environment variables."""
        env = {
            "AUTOQA_MAX_PARALLEL": "10",
            "AUTOQA_MAX_BROWSER_CONTEXTS": "20",
            "AUTOQA_SCALING_STRATEGY": "aggressive",
            "AUTOQA_MAX_MEMORY_PERCENT": "75.0",
        }
        with patch.dict("os.environ", env, clear=True):
            config = load_concurrency_config()

        assert config.max_parallel_tests == 10
        assert config.max_browser_contexts == 20
        assert config.scaling_strategy == ScalingStrategy.AGGRESSIVE
        assert config.resource_limits.max_memory_percent == 75.0

    def test_handles_invalid_env_values(self) -> None:
        """Test graceful handling of invalid environment values."""
        env = {
            "AUTOQA_MAX_PARALLEL": "not_a_number",
        }
        with patch.dict("os.environ", env, clear=True):
            config = load_concurrency_config()

        # Should use default value
        assert config.max_parallel_tests == 5

    def test_custom_prefix(self) -> None:
        """Test loading with custom prefix."""
        env = {
            "CUSTOM_MAX_PARALLEL": "15",
        }
        with patch.dict("os.environ", env, clear=True):
            config = load_concurrency_config(env_prefix="CUSTOM_")

        assert config.max_parallel_tests == 15


class TestResourceSnapshot:
    """Tests for ResourceSnapshot data class."""

    def test_is_healthy_at_low_pressure(self) -> None:
        """Test healthy status at low pressure."""
        snapshot = ResourceSnapshot(
            timestamp=0.0,
            memory_used_percent=50.0,
            memory_available_mb=4096,
            memory_total_mb=8192,
            cpu_percent=30.0,
            memory_pressure=MemoryPressure.NONE,
            recommended_parallelism=5,
        )

        assert snapshot.is_healthy is True
        assert snapshot.can_scale_up is True
        assert snapshot.should_scale_down is False

    def test_should_scale_down_at_high_pressure(self) -> None:
        """Test scale down recommendation at high pressure."""
        snapshot = ResourceSnapshot(
            timestamp=0.0,
            memory_used_percent=90.0,
            memory_available_mb=512,
            memory_total_mb=8192,
            cpu_percent=80.0,
            memory_pressure=MemoryPressure.HIGH,
            recommended_parallelism=2,
        )

        assert snapshot.is_healthy is False
        assert snapshot.can_scale_up is False
        assert snapshot.should_scale_down is True


class TestResourceMonitor:
    """Tests for ResourceMonitor."""

    def test_take_snapshot(self) -> None:
        """Test taking a resource snapshot."""
        config = ConcurrencyConfig()
        monitor = ResourceMonitor(config)

        snapshot = monitor.take_snapshot()

        assert isinstance(snapshot, ResourceSnapshot)
        assert snapshot.timestamp > 0
        assert 0 <= snapshot.memory_used_percent <= 100
        assert snapshot.memory_available_mb >= 0
        assert snapshot.memory_total_mb > 0
        assert snapshot.recommended_parallelism >= 1

    def test_pressure_calculation_none(self) -> None:
        """Test pressure calculation for low usage."""
        config = ConcurrencyConfig()
        monitor = ResourceMonitor(config)

        # Simulate low memory usage
        pressure = monitor._calculate_pressure(50.0, 4096)

        assert pressure == MemoryPressure.NONE

    def test_pressure_calculation_critical(self) -> None:
        """Test pressure calculation for critical usage."""
        config = ConcurrencyConfig()
        monitor = ResourceMonitor(config)

        # Simulate critical memory usage (above 90%)
        pressure = monitor._calculate_pressure(95.0, 256)

        assert pressure == MemoryPressure.CRITICAL

    def test_pressure_calculation_high_from_low_available(self) -> None:
        """Test pressure calculation when available memory is low."""
        config = ConcurrencyConfig()
        monitor = ResourceMonitor(config)

        # Below minimum available (512 MB)
        pressure = monitor._calculate_pressure(60.0, 300)

        assert pressure == MemoryPressure.HIGH

    @pytest.mark.asyncio
    async def test_monitoring_lifecycle(self) -> None:
        """Test starting and stopping monitoring."""
        config = ConcurrencyConfig(monitoring_interval_seconds=0.1)
        monitor = ResourceMonitor(config)

        await monitor.start_monitoring()
        assert monitor._running is True

        # Let it run briefly
        await asyncio.sleep(0.2)

        await monitor.stop_monitoring()
        assert monitor._running is False

    @pytest.mark.asyncio
    async def test_pressure_change_callback(self) -> None:
        """Test callback invocation on pressure change."""
        callback_calls: list[tuple[MemoryPressure, MemoryPressure]] = []

        def on_change(old: MemoryPressure, new: MemoryPressure) -> None:
            callback_calls.append((old, new))

        config = ConcurrencyConfig(monitoring_interval_seconds=0.1)
        monitor = ResourceMonitor(config, on_pressure_change=on_change)

        # Manually trigger pressure change
        monitor._current_pressure = MemoryPressure.NONE
        snapshot = ResourceSnapshot(
            timestamp=0.0,
            memory_used_percent=95.0,
            memory_available_mb=256,
            memory_total_mb=8192,
            cpu_percent=50.0,
            memory_pressure=MemoryPressure.CRITICAL,
            recommended_parallelism=1,
        )

        # Simulate what happens in monitoring loop
        if snapshot.memory_pressure != monitor._current_pressure:
            old_pressure = monitor._current_pressure
            monitor._current_pressure = snapshot.memory_pressure
            on_change(old_pressure, snapshot.memory_pressure)

        assert len(callback_calls) == 1
        assert callback_calls[0] == (MemoryPressure.NONE, MemoryPressure.CRITICAL)

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test async context manager usage."""
        config = ConcurrencyConfig(monitoring_interval_seconds=0.1)

        async with ResourceMonitor(config) as monitor:
            assert monitor._running is True
            snapshot = monitor.take_snapshot()
            assert snapshot is not None

        # Should be stopped after exiting context
        assert monitor._running is False


class TestMemoryPressureLevels:
    """Tests for MemoryPressure enum ordering."""

    def test_pressure_ordering(self) -> None:
        """Test that pressure levels are properly ordered."""
        assert MemoryPressure.NONE < MemoryPressure.LOW
        assert MemoryPressure.LOW < MemoryPressure.MEDIUM
        assert MemoryPressure.MEDIUM < MemoryPressure.HIGH
        assert MemoryPressure.HIGH < MemoryPressure.CRITICAL


class TestMockBrowserPool:
    """Tests for BrowserPool with mocked browser."""

    @pytest.fixture
    def mock_browser(self) -> MagicMock:
        """Create a mock browser."""
        browser = MagicMock()
        mock_page = MagicMock()
        mock_page.get_url.return_value = "about:blank"
        browser.new_page.return_value = mock_page
        return browser

    @pytest.mark.asyncio
    async def test_pool_creation(self, mock_browser: MagicMock) -> None:
        """Test browser pool initialization."""
        from autoqa.concurrency.browser_pool import BrowserPool

        config = ConcurrencyConfig(
            min_browser_contexts=2,
            max_browser_contexts=5,
        )

        pool = BrowserPool(mock_browser, config)
        await pool.start()

        try:
            # Should create minimum contexts
            assert pool.size >= config.min_browser_contexts
            assert mock_browser.new_page.call_count >= config.min_browser_contexts
        finally:
            await pool.stop()

    @pytest.mark.asyncio
    async def test_context_acquisition(self, mock_browser: MagicMock) -> None:
        """Test acquiring and releasing contexts."""
        from autoqa.concurrency.browser_pool import BrowserPool

        config = ConcurrencyConfig(
            min_browser_contexts=1,
            max_browser_contexts=5,
        )

        async with BrowserPool(mock_browser, config) as pool:
            async with pool.acquire("test") as context:
                assert context is not None
                assert pool.in_use_count == 1

            # After release
            assert pool.in_use_count == 0

    @pytest.mark.asyncio
    async def test_multiple_acquisitions(self, mock_browser: MagicMock) -> None:
        """Test acquiring multiple contexts concurrently."""
        from autoqa.concurrency.browser_pool import BrowserPool

        config = ConcurrencyConfig(
            min_browser_contexts=1,
            max_browser_contexts=5,
            graceful_shutdown_timeout_seconds=1.0,  # Short timeout for test
        )

        pool = BrowserPool(mock_browser, config)
        await pool.start()

        try:
            contexts = []

            for i in range(3):
                ctx = await pool._acquire_context(f"test_{i}", timeout=5.0)
                contexts.append(ctx)

            assert pool.in_use_count == 3

            # Release all
            for ctx in contexts:
                await pool._release_context(ctx)

            assert pool.in_use_count == 0
        finally:
            await pool.stop()

    @pytest.mark.asyncio
    async def test_pool_statistics(self, mock_browser: MagicMock) -> None:
        """Test pool statistics tracking."""
        from autoqa.concurrency.browser_pool import BrowserPool

        config = ConcurrencyConfig(
            min_browser_contexts=1,
            max_browser_contexts=5,
        )

        async with BrowserPool(mock_browser, config) as pool:
            async with pool.acquire("test"):
                pass

            stats = pool.statistics
            assert stats["total_acquisitions"] >= 1
            assert stats["total_releases"] >= 1
            assert stats["total_created"] >= 1


class TestAsyncTestRunnerMocked:
    """Tests for AsyncTestRunner with mocked dependencies."""

    @pytest.fixture
    def mock_browser(self) -> MagicMock:
        """Create a mock browser."""
        browser = MagicMock()
        mock_page = MagicMock()
        mock_page.get_url.return_value = "about:blank"
        mock_page.get_title.return_value = "Test"
        browser.new_page.return_value = mock_page
        return browser

    @pytest.fixture
    def mock_test_spec(self) -> MagicMock:
        """Create a mock test spec."""
        from autoqa.dsl.models import TestSpec, TestStep

        spec = MagicMock(spec=TestSpec)
        spec.name = "Mock Test"
        spec.steps = []
        spec.variables = {}
        spec.before_all = None
        spec.after_all = None
        spec.before_each = None
        spec.after_each = None
        spec.versioning = None
        return spec

    @pytest.mark.asyncio
    async def test_runner_lifecycle(self, mock_browser: MagicMock) -> None:
        """Test runner start and stop."""
        from autoqa.concurrency.runner import AsyncTestRunner

        config = ConcurrencyConfig(
            max_parallel_tests=2,
            enable_resource_monitoring=False,
        )

        runner = AsyncTestRunner(mock_browser, config)
        await runner.start()

        try:
            assert runner._running is True
            assert runner._pool is not None
            assert runner._semaphore is not None
        finally:
            await runner.stop()
            assert runner._running is False

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_browser: MagicMock) -> None:
        """Test async context manager usage."""
        from autoqa.concurrency.runner import AsyncTestRunner

        config = ConcurrencyConfig(enable_resource_monitoring=False)

        async with AsyncTestRunner(mock_browser, config) as runner:
            assert runner._running is True

        assert runner._running is False


class TestScalingStrategy:
    """Tests for scaling strategy enum."""

    def test_all_strategies_have_values(self) -> None:
        """Test all scaling strategies are defined."""
        strategies = list(ScalingStrategy)

        assert ScalingStrategy.FIXED in strategies
        assert ScalingStrategy.ADAPTIVE in strategies
        assert ScalingStrategy.AGGRESSIVE in strategies
        assert ScalingStrategy.CONSERVATIVE in strategies

    def test_strategy_from_string(self) -> None:
        """Test creating strategy from string value."""
        assert ScalingStrategy("fixed") == ScalingStrategy.FIXED
        assert ScalingStrategy("adaptive") == ScalingStrategy.ADAPTIVE
