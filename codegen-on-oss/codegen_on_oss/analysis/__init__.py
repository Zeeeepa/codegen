"""
Code Analysis Module

This module provides tools and utilities for analyzing codebases,
validating code integrity, and performing various code transformations.
"""

# Core analysis functionality
from codegen_on_oss.analysis.analysis import (
    analyze_codebase,
    analyze_commit,
    analyze_pr,
    compare_branches,
    get_codebase_summary,
)

# Code integrity and validation
from codegen_on_oss.analysis.code_integrity import (
    CodeIntegrityAnalyzer,
    check_code_quality,
    validate_code_integrity,
    validate_dependencies,
)

# Code transformations
from codegen_on_oss.analysis.code_transformations import (
    apply_transformation,
    optimize_imports,
    refactor_code,
)

# Commit analysis
from codegen_on_oss.analysis.commit_analysis import (
    analyze_commit_history,
    get_commit_stats,
)

# Project management
from codegen_on_oss.analysis.project_manager import (
    analyze_project_structure,
    get_project_metrics,
)

# Symbol analysis
from codegen_on_oss.analysis.symbolattr import (
    analyze_symbol_usage,
    get_symbol_attributes,
)

# WSL integration
from codegen_on_oss.analysis.wsl_integration import run_in_wsl, setup_wsl_environment

__all__ = [
    # Core analysis
    "analyze_codebase",
    "analyze_commit",
    "analyze_pr",
    "compare_branches",
    "get_codebase_summary",
    # Code integrity
    "validate_code_integrity",
    "check_code_quality",
    "validate_dependencies",
    "CodeIntegrityAnalyzer",
    # Code transformations
    "apply_transformation",
    "refactor_code",
    "optimize_imports",
    # Symbol analysis
    "get_symbol_attributes",
    "analyze_symbol_usage",
    # Project management
    "analyze_project_structure",
    "get_project_metrics",
    # Commit analysis
    "analyze_commit_history",
    "get_commit_stats",
    # WSL integration
    "setup_wsl_environment",
    "run_in_wsl",
]
