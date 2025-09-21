#!/usr/bin/env python3
"""
Graph-Sitter Symbol compatibility module
"""

try:
    from codegen.sdk.core.symbol import Symbol
except ImportError:
    class Symbol:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
        def __repr__(self):
            return "Symbol(placeholder)"

__all__ = ['Symbol']