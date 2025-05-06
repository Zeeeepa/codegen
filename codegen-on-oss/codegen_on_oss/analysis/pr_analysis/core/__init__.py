"""
Core Package

This package provides the core components for PR analysis.
"""

from .pr_analyzer import PRAnalyzer
from .rule_engine import RuleEngine
from .analysis_context import AnalysisContext, DiffContext
from .factory import (
    create_rule_engine,
    create_pr_analyzer,
    create_report_formatter,
    create_report_generator,
)

# Export all core components
__all__ = [
    'PRAnalyzer',
    'RuleEngine',
    'AnalysisContext',
    'DiffContext',
    'create_rule_engine',
    'create_pr_analyzer',
    'create_report_formatter',
    'create_report_generator',
]

