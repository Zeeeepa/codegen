"""
Codebase analysis module for graph-sitter.
"""

from graph_sitter.core.class_definition import Class
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.file import SourceFile
from graph_sitter.core.symbol import Symbol


def get_codebase_summary(codebase: Codebase) -> str:
    """Get a summary of the codebase."""
    return f"Codebase summary for {codebase}"


def get_file_summary(file: SourceFile) -> str:
    """Get a summary of a file."""
    return f"File summary for {file.name}"


def get_class_summary(cls: Class) -> str:
    """Get a summary of a class."""
    return f"Class summary for {cls.name}"


def get_function_summary(func) -> str:
    """Get a summary of a function."""
    return f"Function summary for {func.name}"


def get_symbol_summary(symbol: Symbol) -> str:
    """Get a summary of a symbol."""
    return f"Symbol summary for {symbol.name}"

