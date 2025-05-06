"""
PR Static Analysis System

This package provides a comprehensive system for analyzing pull requests
and providing feedback on code quality, potential issues, and suggested improvements.

The system is organized into several modules:
- core: Core components for PR analysis orchestration
- git: Git integration components for repository and PR data access
- rules: Analysis rules that can be applied to PRs
- reporting: Components for generating and formatting analysis reports
- utils: Utility functions for diff analysis and configuration management
"""

from codegen_on_oss.analysis.pr_analysis.core.pr_analyzer import PRAnalyzer
from codegen_on_oss.analysis.pr_analysis.core.analysis_context import AnalysisContext
from codegen_on_oss.analysis.pr_analysis.core.rule_engine import RuleEngine

__all__ = [
    'PRAnalyzer',
    'AnalysisContext',
    'RuleEngine',
]

__version__ = '0.1.0'

