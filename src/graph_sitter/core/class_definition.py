"""
Class definition module for graph-sitter.
"""

class Class:
    """Represents a class definition."""
    
    def __init__(self, name, *args, **kwargs):
        """Initialize the class definition."""
        self.name = name
        self.methods = []
        self.attributes = []
        self.decorators = []
        self.dependencies = []
        self.parent_class_names = []

