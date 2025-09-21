#!/usr/bin/env python3
"""
Graph-Sitter Class compatibility module
"""

try:
    from codegen.sdk.core.class_definition import Class
except ImportError:
    class Class:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
        def __repr__(self):
            return "Class(placeholder)"

__all__ = ['Class']