"""
Codegen-on-OSS: A toolkit for analyzing and processing code repositories

This package provides tools for analyzing code repositories, calculating code metrics,
and generating reports on code quality and complexity.
"""

__version__ = "0.1.0"

# Import and expose key functionality
from codegen_on_oss.analysis.code_metrics import (
    calculate_cyclomatic_complexity,
    calculate_maintainability_index,
    calculate_halstead_metrics,
    analyze_codebase_metrics,
    get_function_metrics,
    calculate_line_metrics
)

from codegen_on_oss.parser import CodegenParser

__all__ = [
    "calculate_cyclomatic_complexity",
    "calculate_maintainability_index",
    "calculate_halstead_metrics",
    "analyze_codebase_metrics",
    "get_function_metrics",
    "calculate_line_metrics",
    "CodegenParser",
]

