"""
Rules for PR static analysis.

This package provides rules for checking various aspects of PRs.
"""

from pr_static_analysis.rules.base import rule_config, rule_registry
from pr_static_analysis.rules.code_integrity import (
    BaseCodeIntegrityRule,
    CodeSmellRule,
    SyntaxErrorRule,
)
from pr_static_analysis.rules.implementation_validation import (
    BaseImplementationValidationRule,
    MissingEdgeCaseRule,
)
from pr_static_analysis.rules.parameter_validation import (
    BaseParameterValidationRule,
    UnusedParameterRule,
)

__all__ = [
    "rule_config",
    "rule_registry",
    "BaseCodeIntegrityRule",
    "CodeSmellRule",
    "SyntaxErrorRule",
    "BaseImplementationValidationRule",
    "MissingEdgeCaseRule",
    "BaseParameterValidationRule",
    "UnusedParameterRule",
]

