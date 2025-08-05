"""
Graph-Sitter Codebase Core

Core codebase functionality for graph-sitter.
"""

class Codebase:
    """Core codebase class for graph-sitter analysis."""
    
    def __init__(self, path: str):
        self.path = path
        
    def __repr__(self):
        return f"Codebase(path='{self.path}')"
