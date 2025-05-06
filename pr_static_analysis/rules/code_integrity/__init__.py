"""Code integrity rules for PR static analysis.

This package provides rules for checking code integrity issues.
"""

from pr_static_analysis.rules.code_integrity.base_code_integrity_rule import (
    BaseCodeIntegrityRule,
)
from pr_static_analysis.rules.code_integrity.code_smell_rule import CodeSmellRule
from pr_static_analysis.rules.code_integrity.syntax_error_rule import SyntaxErrorRule

__all__ = ["BaseCodeIntegrityRule", "CodeSmellRule", "SyntaxErrorRule"]
