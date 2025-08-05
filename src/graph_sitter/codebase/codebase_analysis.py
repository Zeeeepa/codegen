"""
Graph-Sitter Codebase Analysis Functions

Analysis functions for graph-sitter codebases.
"""

from typing import Dict, Any, Optional

def get_codebase_summary(codebase) -> Dict[str, Any]:
    """Get a summary of the codebase."""
    return {
        "path": getattr(codebase, 'path', 'unknown'),
        "type": "codebase_summary"
    }

def get_file_summary(file_path: str) -> Dict[str, Any]:
    """Get a summary of a specific file."""
    return {
        "file_path": file_path,
        "type": "file_summary"
    }

def get_class_summary(class_name: str) -> Dict[str, Any]:
    """Get a summary of a specific class."""
    return {
        "class_name": class_name,
        "type": "class_summary"
    }

def get_function_summary(function_name: str) -> Dict[str, Any]:
    """Get a summary of a specific function."""
    return {
        "function_name": function_name,
        "type": "function_summary"
    }

def get_symbol_summary(symbol_name: str) -> Dict[str, Any]:
    """Get a summary of a specific symbol."""
    return {
        "symbol_name": symbol_name,
        "type": "symbol_summary"
    }
