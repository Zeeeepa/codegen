"""
Base package for PR static analysis rules.

This package provides the base classes and utilities for PR static analysis rules.
"""

from pr_static_analysis.rules.base.base_rule import (
    BaseRule,
    RuleCategory,
    RuleResult,
    RuleSeverity,
)
from pr_static_analysis.rules.base.rule_config import RuleConfig, rule_config
from pr_static_analysis.rules.base.rule_registry import RuleRegistry, rule_registry

__all__ = [
    "BaseRule",
    "RuleCategory",
    "RuleResult",
    "RuleSeverity",
    "RuleRegistry",
    "rule_registry",
    "RuleConfig",
    "rule_config",
]

