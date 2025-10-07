"""
Core Error Analysis Module

This module imports all Serena analysis features and provides unified access
to comprehensive error analysis capabilities for graph-sitter.
"""

# Import all serena analysis features
from ..extensions.lsp.serena_analysis import *

# Import graph-sitter core functions
from graph_sitter.core.codebase import Codebase
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary, 
    get_file_summary, 
    get_class_summary, 
    get_function_summary, 
    get_symbol_summary
)

__all__ = [
    # Re-export all serena analysis features
    "ErrorType",
    "ErrorCategory", 
    "ErrorLocation",
    "RuntimeContext",
    "ErrorInfo",
    "ComprehensiveErrorList",
    "RuntimeErrorCollector",
    "SerenaLSPBridge",
    "TransactionAwareLSPManager",
    "GitHubRepositoryAnalyzer",
    "AnalysisResult",
    "RepositoryInfo",
    "EnhancedSerenaIntegration",
    "analyze_github_repository",
    "get_repository_error_summary",
    "analyze_multiple_repositories",
    
    # Graph-sitter core functions
    "Codebase",
    "get_codebase_summary",
    "get_file_summary", 
    "get_class_summary",
    "get_function_summary",
    "get_symbol_summary",
]
