"""
Rules for PR static analysis.

This package provides rules for analyzing PRs.
"""

from pr_static_analysis.rules.base import (
    BaseRule,
    RuleCategory,
    RuleResult,
    RuleSeverity,
    rule_config,
    rule_registry,
)
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

# Register all rules
rule_registry.register(SyntaxErrorRule)
rule_registry.register(CodeSmellRule)
rule_registry.register(UnusedParameterRule)
rule_registry.register(MissingEdgeCaseRule)

__all__ = [
    "BaseRule",
    "RuleCategory",
    "RuleResult",
    "RuleSeverity",
    "rule_config",
    "rule_registry",
    "BaseCodeIntegrityRule",
    "SyntaxErrorRule",
    "CodeSmellRule",
    "BaseParameterValidationRule",
    "UnusedParameterRule",
    "BaseImplementationValidationRule",
    "MissingEdgeCaseRule",
]

