#!/usr/bin/env python3
"""
Graph-Sitter Function compatibility module
"""

try:
    from codegen.exports import Function
except ImportError:
    class Function:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
        def __repr__(self):
            return "Function(placeholder)"

__all__ = ['Function']