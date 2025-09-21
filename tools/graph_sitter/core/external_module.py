#!/usr/bin/env python3
"""
Graph-Sitter ExternalModule compatibility module
"""

try:
    from codegen.sdk.core.external_module import ExternalModule
except ImportError:
    class ExternalModule:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
        def __repr__(self):
            return "ExternalModule(placeholder)"

__all__ = ['ExternalModule']