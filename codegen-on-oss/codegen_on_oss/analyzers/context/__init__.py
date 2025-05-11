"""
Codebase Context Module

This module provides graph-based context representations of codebases,
files, classes, and functions to support advanced analysis capabilities.
"""

from codegen_on_oss.analyzers.context.codebase import CodebaseContext
from codegen_on_oss.analyzers.context.file import FileContext
from codegen_on_oss.analyzers.context.function import FunctionContext

__all__ = [
    'CodebaseContext',
    'FileContext',
    'FunctionContext',
]