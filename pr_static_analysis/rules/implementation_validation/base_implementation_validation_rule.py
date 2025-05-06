"""
Base class for implementation validation rules.

This module provides the base class for rules that check implementation validation issues.
"""

import abc
from typing import Any, Dict, List

from pr_static_analysis.rules.base import BaseRule, RuleCategory, RuleResult


class BaseImplementationValidationRule(BaseRule):
    """
    Base class for implementation validation rules.
    
    These rules check for issues related to implementation validation, such as:
    - Missing edge cases
    - Incomplete implementation
    - Validation against requirements
    - Performance issues
    """
    
    @property
    def category(self) -> RuleCategory:
        """Get the category of the rule."""
        return RuleCategory.IMPLEMENTATION_VALIDATION
    
    @abc.abstractmethod
    def analyze(self, context: Dict[str, Any]) -> List[RuleResult]:
        """
        Analyze the PR for implementation validation issues.
        
        Args:
            context: Context information for the analysis
        
        Returns:
            A list of RuleResult objects representing issues found
        """
        pass

