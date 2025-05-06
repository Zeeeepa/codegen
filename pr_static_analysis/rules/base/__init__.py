"""
Base classes and utilities for PR static analysis rules.

This module provides the base classes and utilities for defining and managing rules.
"""

from pr_static_analysis.rules.base.base_rule import (
    BaseRule,
    RuleCategory,
    RuleResult,
    RuleSeverity,
)
from pr_static_analysis.rules.base.rule_config import rule_config
from pr_static_analysis.rules.base.rule_registry import rule_registry

__all__ = [
    "BaseRule",
    "RuleCategory",
    "RuleResult",
    "RuleSeverity",
    "rule_config",
    "rule_registry",
]

