"""
Code Analysis Module

This module provides tools and utilities for analyzing codebases,
validating code integrity, and performing various code transformations.
"""

# Core analysis functionality
from codegen_on_oss.analysis.analysis import (
    CodeAnalyzer,
    calculate_cyclomatic_complexity,
    cc_rank,
    calculate_doi,
    get_operators_and_operands,
    calculate_halstead_volume,
    count_lines,
    calculate_maintainability_index,
    get_maintainability_rank,
    get_github_repo_description,
)

# Code integrity and validation
from codegen_on_oss.analysis.code_integrity import (
    CodeIntegrityAnalyzer,
    analyze_code_integrity,
    compare_branches,
)

# Code transformations
from codegen_on_oss.analysis.code_transformations import (
    apply_transformation,
    refactor_code,
    optimize_imports,
    convert_all_calls_to_kwargs,
)

# Symbol analysis
from codegen_on_oss.analysis.symbolattr import (
    get_symbol_attributes,
    analyze_symbol_usage,
)

# Project management
from codegen_on_oss.analysis.project_manager import (
    analyze_project_structure,
    get_project_metrics,
)

# Commit analysis
from codegen_on_oss.analysis.commit_analysis import (
    CommitAnalysisResult,
    analyze_commit_history,
    get_commit_stats,
)

from codegen_on_oss.analysis.commit_analyzer import CommitAnalyzer

# Import analysis
from codegen_on_oss.analysis.analysis_import import (
    create_graph_from_codebase,
    find_import_cycles,
    find_problematic_import_loops,
)

# Module dependencies
from graph_sitter.codebase.module_dependencies import (
    visualize_module_dependencies,
)

# Document functions
from graph_sitter.code_generation.doc_utils.utils import document_function

# Codebase analysis from graph-sitter
from graph_sitter.codebase.codebase_analysis import (
    get_class_summary,
    get_codebase_summary,
    get_file_summary,
    get_function_summary,
    get_symbol_summary,
)

# Codebase context from graph-sitter
from graph_sitter.codebase.codebase_context import CodebaseContext

# Core classes from graph-sitter
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.class_definition import Class
from graph_sitter.core.function import Function
from graph_sitter.core.file import SourceFile
from graph_sitter.enums import SymbolType, EdgeType
from graph_sitter.shared.enums.programming_language import ProgrammingLanguage

__all__ = [
    # Core analysis
    "CodeAnalyzer",
    "calculate_cyclomatic_complexity",
    "cc_rank",
    "calculate_doi",
    "get_operators_and_operands",
    "calculate_halstead_volume",
    "count_lines",
    "calculate_maintainability_index",
    "get_maintainability_rank",
    "get_github_repo_description",
    
    # Code integrity
    "CodeIntegrityAnalyzer",
    "analyze_code_integrity",
    "compare_branches",
    
    # Code transformations
    "apply_transformation",
    "refactor_code",
    "optimize_imports",
    "convert_all_calls_to_kwargs",
    
    # Symbol analysis
    "get_symbol_attributes",
    "analyze_symbol_usage",
    
    # Project management
    "analyze_project_structure",
    "get_project_metrics",
    
    # Commit analysis
    "CommitAnalysisResult",
    "CommitAnalyzer",
    "analyze_commit_history",
    "get_commit_stats",
    
    # Import analysis
    "create_graph_from_codebase",
    "find_import_cycles",
    "find_problematic_import_loops",
    
    # Module dependencies
    "visualize_module_dependencies",
    
    # Document functions
    "document_function",
    
    # Codebase analysis from graph-sitter
    "get_class_summary",
    "get_codebase_summary",
    "get_file_summary",
    "get_function_summary",
    "get_symbol_summary",
    
    # Codebase context from graph-sitter
    "CodebaseContext",
    
    # Core classes from graph-sitter
    "Codebase",
    "Class",
    "Function",
    "SourceFile",
    "SymbolType",
    "EdgeType",
    "ProgrammingLanguage",
]

