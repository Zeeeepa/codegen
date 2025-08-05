"""
LSP Extensions for Graph-Sitter

This package provides Language Server Protocol (LSP) integration and
comprehensive error analysis capabilities for graph-sitter.
"""

# Import comprehensive error analysis from serena_analysis
from .serena_analysis import *

__all__ = [
    # Core enums and data structures from bridge
    "ErrorType",
    "ErrorCategory", 
    "ErrorLocation",
    "RuntimeContext",
    "ErrorInfo",
    
    # Transaction-aware LSP manager
    "TransactionAwareLSPManager",
    "get_lsp_manager",
    "shutdown_all_lsp_managers",
    
    # Main Serena LSP bridge
    "SerenaLSPBridge",
    "create_serena_lsp_bridge",
    "get_all_errors_with_context",
    "analyze_file_errors",
    
    # Enhanced integration
    "EnhancedSerenaIntegration",
    "create_enhanced_serena_integration",
    
    # Comprehensive analysis classes
    "ErrorSeverity",
    "CodeError",
    "ComprehensiveErrorList",
    "RepositoryInfo",
    "AnalysisResult",
    "GitHubRepositoryAnalyzer",
    
    # Convenience functions
    "analyze_github_repository",
    
    # Core graph-sitter functions
    "Codebase",
    "get_codebase_summary",
    "get_file_summary",
    "get_class_summary", 
    "get_function_summary",
    "get_symbol_summary",
    
    # Serena availability
    "SERENA_AVAILABLE",
]
