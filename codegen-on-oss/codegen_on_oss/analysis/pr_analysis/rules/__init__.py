"""
Analysis rules for PR static analysis.

This package contains rules for detecting errors, issues, wrongly implemented features,
and parameter problems in pull requests.
"""

from .base_rule import BaseRule, AnalysisResult
from .code_integrity_rules import (
    SyntaxErrorRule,
    UndefinedReferenceRule,
    UnusedImportRule,
    CircularDependencyRule,
)
from .parameter_rules import (
    ParameterTypeMismatchRule,
    MissingParameterRule,
    IncorrectParameterUsageRule,
)
from .implementation_rules import (
    FeatureCompletenessRule,
    TestCoverageRule,
    PerformanceImplicationRule,
    SecurityConsiderationRule,
)

# List of all available rules
ALL_RULES = [
    # Code integrity rules
    SyntaxErrorRule(),
    UndefinedReferenceRule(),
    UnusedImportRule(),
    CircularDependencyRule(),
    
    # Parameter validation rules
    ParameterTypeMismatchRule(),
    MissingParameterRule(),
    IncorrectParameterUsageRule(),
    
    # Implementation validation rules
    FeatureCompletenessRule(),
    TestCoverageRule(),
    PerformanceImplicationRule(),
    SecurityConsiderationRule(),
]

__all__ = [
    'BaseRule',
    'AnalysisResult',
    'SyntaxErrorRule',
    'UndefinedReferenceRule',
    'UnusedImportRule',
    'CircularDependencyRule',
    'ParameterTypeMismatchRule',
    'MissingParameterRule',
    'IncorrectParameterUsageRule',
    'FeatureCompletenessRule',
    'TestCoverageRule',
    'PerformanceImplicationRule',
    'SecurityConsiderationRule',
    'ALL_RULES',
]

