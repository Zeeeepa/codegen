"""
Parameter validation rules for PR static analysis.

This package provides rules for checking parameter validation issues.
"""

from pr_static_analysis.rules.parameter_validation.base_parameter_validation_rule import (
    BaseParameterValidationRule,
)
from pr_static_analysis.rules.parameter_validation.unused_parameter_rule import (
    UnusedParameterRule,
)

__all__ = ["BaseParameterValidationRule", "UnusedParameterRule"]

