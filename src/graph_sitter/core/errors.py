"""
Core Error Analysis Module

This module provides comprehensive error analysis capabilities by importing
all Serena analysis features and integrating with graph-sitter's codebase analysis.
"""

# Core graph-sitter imports
from graph_sitter.core.codebase import Codebase
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary, 
    get_file_summary, 
    get_class_summary, 
    get_function_summary, 
    get_symbol_summary
)

# Import all serena analysis features
from ..extensions.lsp.serena_analysis import *

__all__ = [
    # Core codebase functionality
    "Codebase",
    "get_codebase_summary",
    "get_file_summary", 
    "get_class_summary",
    "get_function_summary",
    "get_symbol_summary",
    
    # All serena analysis exports (imported via *)
    # This includes all classes, functions, and constants from serena_analysis
]
