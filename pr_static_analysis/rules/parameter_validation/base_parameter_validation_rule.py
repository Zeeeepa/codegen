"""
Base class for parameter validation rules.

This module provides the base class for rules that check parameter validation issues.
"""

import abc
from typing import Any, Dict, List

from pr_static_analysis.rules.base import BaseRule, RuleCategory, RuleResult


class BaseParameterValidationRule(BaseRule):
    """
    Base class for parameter validation rules.
    
    These rules check for issues related to parameter validation, such as:
    - Unused parameters
    - Parameter type checking
    - Parameter usage
    - Parameter naming
    """
    
    @property
    def category(self) -> RuleCategory:
        """Get the category of the rule."""
        return RuleCategory.PARAMETER_VALIDATION
    
    @abc.abstractmethod
    def analyze(self, context: Dict[str, Any]) -> List[RuleResult]:
        """
        Analyze the PR for parameter validation issues.
        
        Args:
            context: Context information for the analysis
        
        Returns:
            A list of RuleResult objects representing issues found
        """
        pass

