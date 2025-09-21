#!/usr/bin/env python3
"""
Graph-Sitter SourceFile compatibility module
"""

try:
    from codegen.sdk.core.file import SourceFile
except ImportError:
    class SourceFile:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
        def __repr__(self):
            return "SourceFile(placeholder)"

__all__ = ['SourceFile']