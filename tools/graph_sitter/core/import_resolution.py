#!/usr/bin/env python3
"""
Graph-Sitter Import compatibility module
"""

try:
    from codegen.sdk.core.import_resolution import Import
except ImportError:
    class Import:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
        def __repr__(self):
            return "Import(placeholder)"

__all__ = ['Import']