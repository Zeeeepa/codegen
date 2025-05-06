"""
Symbol module for graph-sitter.
"""

class Symbol:
    """Represents a symbol."""
    
    def __init__(self, name, symbol_type=None):
        """Initialize the symbol."""
        self.name = name
        self.symbol_type = symbol_type
        self.symbol_usages = []

