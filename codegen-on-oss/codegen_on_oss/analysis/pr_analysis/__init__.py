"""
PR Static Analysis System

This system analyzes pull requests to detect errors, issues, wrongly implemented features, and parameter problems.
It provides clear feedback on whether a PR provides a valid and error-free implementation.
"""

from .core.pr_analyzer import PRAnalyzer
from .core.rule_engine import RuleEngine, BaseRule
from .core.analysis_context import AnalysisContext, AnalysisResult

__all__ = [
    'PRAnalyzer',
    'RuleEngine',
    'BaseRule',
    'AnalysisContext',
    'AnalysisResult',
]

