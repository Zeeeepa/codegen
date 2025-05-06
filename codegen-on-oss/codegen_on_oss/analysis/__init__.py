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
    convert_all_calls_to_kwargs,
    convert_call_to_kwargs,
)

# Commit analysis
from codegen_on_oss.analysis.commit_analysis import (
    CommitAnalysisOptions,
    CommitAnalysisResult,
    CommitComparisonResult,
    FileChange,
)

# Project management
from codegen_on_oss.analysis.project_manager import (
    Project,
    ProjectManager,
)

# Symbol analysis
from codegen_on_oss.analysis.symbolattr import (
    get_file_attribution,
    get_symbol_attribution,
)

# WSL integration
from codegen_on_oss.analysis.wsl_integration import (
    CtrlplaneIntegration,
    WeaveIntegration,
)

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
    "convert_call_to_kwargs",
    "convert_all_calls_to_kwargs",
    
    # Symbol analysis
    "get_symbol_attribution",
    "get_file_attribution",
    
    # Project management
    "Project",
    "ProjectManager",
    
    # Commit analysis
    "CommitAnalysisOptions",
    "FileChange",
    "CommitAnalysisResult",
    "CommitComparisonResult",
    
    # WSL integration
    "CtrlplaneIntegration",
    "WeaveIntegration",
]
