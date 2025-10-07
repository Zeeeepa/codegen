"""
LSP Extensions for Graph-Sitter

This package provides Language Server Protocol (LSP) integration and
comprehensive error analysis capabilities for graph-sitter.
"""

# Import from serena_analysis to make functions available at package level
try:
    from .serena_analysis import (
        analyze_github_repository,
        get_repository_error_summary,
        analyze_multiple_repositories,
    )
    
    __all__ = [
        "analyze_github_repository",
        "get_repository_error_summary", 
        "analyze_multiple_repositories",
    ]
except ImportError:
    # Graceful fallback if serena dependencies are not available
    __all__ = []
