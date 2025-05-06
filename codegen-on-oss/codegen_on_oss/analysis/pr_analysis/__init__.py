"""
PR static analysis system.

This package provides a system for static analysis of pull requests.
It includes components for analyzing code changes, applying rules,
and generating reports.

The system is designed to be extensible, allowing for the addition of
new rules, report formats, and Git providers.

Main components:
- Core: Main orchestration components
- Git: Git integration components
- Reporting: Report generation and formatting components
- Rules: Analysis rules
- Utils: Utility functions
"""

from codegen_on_oss.analysis.pr_analysis.core import PRAnalyzer

__all__ = [
    'PRAnalyzer',
]

