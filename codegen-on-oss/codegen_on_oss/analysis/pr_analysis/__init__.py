"""
PR static analysis system.

This package contains components for analyzing pull requests to detect errors,
issues, wrongly implemented features, and parameter problems.
"""

from .rules import BaseRule, AnalysisResult, ALL_RULES

__all__ = [
    'BaseRule',
    'AnalysisResult',
    'ALL_RULES',
]

