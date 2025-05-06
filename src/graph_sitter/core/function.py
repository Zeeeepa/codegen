"""
Function module for graph-sitter.
"""

class Function:
    """Represents a function."""
    
    def __init__(self, name, *args, **kwargs):
        """Initialize the function."""
        self.name = name
        self.return_statements = []
        self.parameters = []
        self.function_calls = []
        self.call_sites = []
        self.decorators = []
        self.dependencies = []

