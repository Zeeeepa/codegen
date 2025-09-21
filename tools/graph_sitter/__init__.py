#!/usr/bin/env python3
"""
Graph-Sitter compatibility package
Provides import aliases for the analysis files to work with the codegen exports
"""

# Import from codegen.exports and make them available
try:
    from codegen.exports import Codebase, Function, ProgrammingLanguage
except ImportError as e:
    print(f"Warning: graph-sitter or related modules not available: {e}")
    print("Install with: pip install graph-sitter")
    
    # Provide fallback placeholder classes
    class Codebase:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
        def __repr__(self):
            return "Codebase(placeholder - dependencies missing)"

    class Function:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
        def __repr__(self):
            return "Function(placeholder - dependencies missing)"
    
    class ProgrammingLanguage:
        PYTHON = "python"
        JAVASCRIPT = "javascript"
        TYPESCRIPT = "typescript"

__all__ = ['Codebase', 'Function', 'ProgrammingLanguage']