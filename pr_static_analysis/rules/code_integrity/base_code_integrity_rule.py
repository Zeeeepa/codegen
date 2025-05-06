"""Base class for code integrity rules.

This module provides the base class for rules that check code integrity issues.
"""

import abc
from typing import Any

from pr_static_analysis.rules.base import BaseRule, RuleCategory, RuleResult


class BaseCodeIntegrityRule(BaseRule):
    """Base class for code integrity rules.

    These rules check for issues related to code integrity, such as:
    - Syntax errors
    - Logical issues
    - Code smells
    - Potential bugs
    """

    @property
    def category(self) -> RuleCategory:
        """Get the category of the rule."""
        return RuleCategory.CODE_INTEGRITY

    @abc.abstractmethod
    def analyze(self, context: dict[str, Any]) -> list[RuleResult]:
        """Analyze the PR for code integrity issues.

        Args:
            context: Context information for the analysis

        Returns:
            A list of RuleResult objects representing issues found
        """
        pass
