"""
Configuration models for concurrency control.

Provides typed configuration for:
- Parallel test execution limits
- Resource constraints (memory, CPU)
- Browser pool sizing
- Environment variable support
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Self

import structlog

logger = structlog.get_logger(__name__)


class ScalingStrategy(StrEnum):
    """Strategy for dynamic scaling of parallel workers."""

    FIXED = "fixed"
    """Fixed number of workers regardless of load."""

    ADAPTIVE = "adaptive"
    """Scale workers based on resource availability."""

    AGGRESSIVE = "aggressive"
    """Maximize parallelism up to hard limits."""

    CONSERVATIVE = "conservative"
    """Prefer lower parallelism for stability."""


@dataclass(frozen=True, slots=True)
class ResourceLimits:
    """
    Resource constraints for concurrency control.

    Defines hard limits that trigger scaling adjustments.
    """

    max_memory_percent: float = 80.0
    """Maximum memory usage percentage before reducing parallelism."""

    critical_memory_percent: float = 90.0
    """Memory threshold that triggers immediate scale-down."""

    max_cpu_percent: float = 85.0
    """Maximum CPU usage percentage before reducing parallelism."""

    min_available_memory_mb: int = 512
    """Minimum available memory in MB to start new contexts."""

    context_memory_estimate_mb: int = 150
    """Estimated memory per browser context in MB."""

    def validate(self) -> None:
        """Validate resource limits are sensible."""
        if not 0 < self.max_memory_percent < 100:
            raise ValueError("max_memory_percent must be between 0 and 100")
        if not 0 < self.critical_memory_percent <= 100:
            raise ValueError("critical_memory_percent must be between 0 and 100")
        if self.max_memory_percent >= self.critical_memory_percent:
            raise ValueError(
                "max_memory_percent must be less than critical_memory_percent"
            )
        if self.min_available_memory_mb < 0:
            raise ValueError("min_available_memory_mb must be non-negative")
        if self.context_memory_estimate_mb <= 0:
            raise ValueError("context_memory_estimate_mb must be positive")


@dataclass(slots=True)
class ConcurrencyConfig:
    """
    Configuration for parallel test execution.

    Supports loading from environment variables with sensible defaults.
    Thread-safe immutable configuration after initialization.
    """

    max_parallel_tests: int = 5
    """Maximum number of tests running concurrently."""

    max_browser_contexts: int = 10
    """Maximum browser contexts in the pool."""

    min_browser_contexts: int = 1
    """Minimum browser contexts to keep warm."""

    context_idle_timeout_seconds: float = 60.0
    """Time before idle contexts are recycled."""

    context_max_age_seconds: float = 300.0
    """Maximum age of a context before forced recycling."""

    context_max_uses: int = 50
    """Maximum test runs per context before recycling."""

    acquire_timeout_seconds: float = 30.0
    """Timeout for acquiring a browser context."""

    scaling_strategy: ScalingStrategy = ScalingStrategy.ADAPTIVE
    """Strategy for dynamic worker scaling."""

    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    """Resource constraints for scaling decisions."""

    enable_resource_monitoring: bool = True
    """Enable dynamic scaling based on system resources."""

    monitoring_interval_seconds: float = 5.0
    """Interval for resource monitoring checks."""

    graceful_shutdown_timeout_seconds: float = 30.0
    """Timeout for graceful shutdown of pool."""

    retry_on_context_failure: bool = True
    """Retry test with new context if context fails."""

    max_context_retries: int = 2
    """Maximum retries for context-related failures."""

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate configuration values."""
        if self.max_parallel_tests < 1:
            raise ValueError("max_parallel_tests must be at least 1")
        if self.max_browser_contexts < 1:
            raise ValueError("max_browser_contexts must be at least 1")
        if self.min_browser_contexts < 0:
            raise ValueError("min_browser_contexts must be non-negative")
        if self.min_browser_contexts > self.max_browser_contexts:
            raise ValueError(
                "min_browser_contexts cannot exceed max_browser_contexts"
            )
        if self.context_idle_timeout_seconds <= 0:
            raise ValueError("context_idle_timeout_seconds must be positive")
        if self.context_max_age_seconds <= 0:
            raise ValueError("context_max_age_seconds must be positive")
        if self.context_max_uses < 1:
            raise ValueError("context_max_uses must be at least 1")
        if self.acquire_timeout_seconds <= 0:
            raise ValueError("acquire_timeout_seconds must be positive")
        if self.monitoring_interval_seconds <= 0:
            raise ValueError("monitoring_interval_seconds must be positive")
        if self.graceful_shutdown_timeout_seconds < 0:
            raise ValueError("graceful_shutdown_timeout_seconds must be non-negative")

        self.resource_limits.validate()

    def with_overrides(
        self,
        max_parallel_tests: int | None = None,
        max_browser_contexts: int | None = None,
        scaling_strategy: ScalingStrategy | None = None,
    ) -> Self:
        """
        Create a new config with specified overrides.

        Returns a new instance - does not mutate the original.
        """
        return ConcurrencyConfig(
            max_parallel_tests=max_parallel_tests or self.max_parallel_tests,
            max_browser_contexts=max_browser_contexts or self.max_browser_contexts,
            min_browser_contexts=self.min_browser_contexts,
            context_idle_timeout_seconds=self.context_idle_timeout_seconds,
            context_max_age_seconds=self.context_max_age_seconds,
            context_max_uses=self.context_max_uses,
            acquire_timeout_seconds=self.acquire_timeout_seconds,
            scaling_strategy=scaling_strategy or self.scaling_strategy,
            resource_limits=self.resource_limits,
            enable_resource_monitoring=self.enable_resource_monitoring,
            monitoring_interval_seconds=self.monitoring_interval_seconds,
            graceful_shutdown_timeout_seconds=self.graceful_shutdown_timeout_seconds,
            retry_on_context_failure=self.retry_on_context_failure,
            max_context_retries=self.max_context_retries,
        )


def load_concurrency_config(
    env_prefix: str = "AUTOQA_",
    defaults: ConcurrencyConfig | None = None,
) -> ConcurrencyConfig:
    """
    Load concurrency configuration from environment variables.

    Environment variables (all optional):
    - AUTOQA_MAX_PARALLEL: Maximum parallel tests
    - AUTOQA_MAX_BROWSER_CONTEXTS: Maximum browser contexts
    - AUTOQA_MIN_BROWSER_CONTEXTS: Minimum warm contexts
    - AUTOQA_SCALING_STRATEGY: fixed/adaptive/aggressive/conservative
    - AUTOQA_CONTEXT_IDLE_TIMEOUT: Idle timeout in seconds
    - AUTOQA_CONTEXT_MAX_AGE: Max context age in seconds
    - AUTOQA_CONTEXT_MAX_USES: Max uses per context
    - AUTOQA_ACQUIRE_TIMEOUT: Context acquisition timeout
    - AUTOQA_ENABLE_RESOURCE_MONITORING: Enable/disable monitoring
    - AUTOQA_MAX_MEMORY_PERCENT: Memory threshold percentage
    - AUTOQA_CRITICAL_MEMORY_PERCENT: Critical memory threshold
    - AUTOQA_MIN_AVAILABLE_MEMORY_MB: Minimum available memory

    Args:
        env_prefix: Prefix for environment variables
        defaults: Default configuration to use as base

    Returns:
        Loaded and validated ConcurrencyConfig
    """
    base = defaults or ConcurrencyConfig()

    def get_int(key: str, default: int) -> int:
        value = os.environ.get(f"{env_prefix}{key}")
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            logger.warning(
                "Invalid integer value for config",
                key=key,
                value=value,
                using_default=default,
            )
            return default

    def get_float(key: str, default: float) -> float:
        value = os.environ.get(f"{env_prefix}{key}")
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            logger.warning(
                "Invalid float value for config",
                key=key,
                value=value,
                using_default=default,
            )
            return default

    def get_bool(key: str, default: bool) -> bool:
        value = os.environ.get(f"{env_prefix}{key}")
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")

    def get_strategy(key: str, default: ScalingStrategy) -> ScalingStrategy:
        value = os.environ.get(f"{env_prefix}{key}")
        if value is None:
            return default
        try:
            return ScalingStrategy(value.lower())
        except ValueError:
            logger.warning(
                "Invalid scaling strategy",
                key=key,
                value=value,
                valid_values=list(ScalingStrategy),
                using_default=default,
            )
            return default

    resource_limits = ResourceLimits(
        max_memory_percent=get_float(
            "MAX_MEMORY_PERCENT", base.resource_limits.max_memory_percent
        ),
        critical_memory_percent=get_float(
            "CRITICAL_MEMORY_PERCENT", base.resource_limits.critical_memory_percent
        ),
        max_cpu_percent=get_float(
            "MAX_CPU_PERCENT", base.resource_limits.max_cpu_percent
        ),
        min_available_memory_mb=get_int(
            "MIN_AVAILABLE_MEMORY_MB", base.resource_limits.min_available_memory_mb
        ),
        context_memory_estimate_mb=get_int(
            "CONTEXT_MEMORY_ESTIMATE_MB", base.resource_limits.context_memory_estimate_mb
        ),
    )

    config = ConcurrencyConfig(
        max_parallel_tests=get_int("MAX_PARALLEL", base.max_parallel_tests),
        max_browser_contexts=get_int(
            "MAX_BROWSER_CONTEXTS", base.max_browser_contexts
        ),
        min_browser_contexts=get_int(
            "MIN_BROWSER_CONTEXTS", base.min_browser_contexts
        ),
        context_idle_timeout_seconds=get_float(
            "CONTEXT_IDLE_TIMEOUT", base.context_idle_timeout_seconds
        ),
        context_max_age_seconds=get_float(
            "CONTEXT_MAX_AGE", base.context_max_age_seconds
        ),
        context_max_uses=get_int("CONTEXT_MAX_USES", base.context_max_uses),
        acquire_timeout_seconds=get_float(
            "ACQUIRE_TIMEOUT", base.acquire_timeout_seconds
        ),
        scaling_strategy=get_strategy("SCALING_STRATEGY", base.scaling_strategy),
        resource_limits=resource_limits,
        enable_resource_monitoring=get_bool(
            "ENABLE_RESOURCE_MONITORING", base.enable_resource_monitoring
        ),
        monitoring_interval_seconds=get_float(
            "MONITORING_INTERVAL", base.monitoring_interval_seconds
        ),
        graceful_shutdown_timeout_seconds=get_float(
            "GRACEFUL_SHUTDOWN_TIMEOUT", base.graceful_shutdown_timeout_seconds
        ),
        retry_on_context_failure=get_bool(
            "RETRY_ON_CONTEXT_FAILURE", base.retry_on_context_failure
        ),
        max_context_retries=get_int("MAX_CONTEXT_RETRIES", base.max_context_retries),
    )

    logger.info(
        "Loaded concurrency config",
        max_parallel=config.max_parallel_tests,
        max_contexts=config.max_browser_contexts,
        strategy=config.scaling_strategy,
        resource_monitoring=config.enable_resource_monitoring,
    )

    return config
