"""
PR static analysis system.

This package provides a flexible rule system for analyzing PRs.
"""

from pr_static_analysis.analyzer import PRStaticAnalyzer
from pr_static_analysis.rules.base import (
    BaseRule,
    RuleCategory,
    RuleResult,
    RuleSeverity,
    rule_config,
    rule_registry,
)

__all__ = [
    "PRStaticAnalyzer",
    "BaseRule",
    "RuleCategory",
    "RuleResult",
    "RuleSeverity",
    "rule_config",
    "rule_registry",
]

