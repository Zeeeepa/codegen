"""
Test runner module with self-healing capabilities.

Executes tests using owl-browser with:
- Deterministic self-healing (no AI/LLM dependency)
- Smart waits (network idle, selector visibility)
- Exponential backoff retry
- Screenshot/network log capture on failure
"""

from autoqa.runner.self_healing import (
    HealingResult,
    HealingStrategy,
    SelectorCandidate,
    SelectorHistory,
    SelfHealingEngine,
)
from autoqa.runner.test_runner import (
    ElementNotFoundError,
    ElementNotInteractableError,
    NetworkTimeoutError,
    StepResult,
    StepStatus,
    TestRunner,
    TestRunResult,
)

__all__ = [
    # Test Runner
    "TestRunner",
    "TestRunResult",
    "StepResult",
    "StepStatus",
    # Custom Exceptions
    "ElementNotFoundError",
    "ElementNotInteractableError",
    "NetworkTimeoutError",
    # Self-Healing
    "SelfHealingEngine",
    "HealingStrategy",
    "HealingResult",
    "SelectorCandidate",
    "SelectorHistory",
]
