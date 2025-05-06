"""
File module for graph-sitter.
"""

class File:
    """Represents a file."""
    
    def __init__(self, path, content=""):
        """Initialize the file."""
        self.path = path
        self.content = content


class SourceFile(File):
    """Represents a source file."""
    
    def __init__(self, path, content=""):
        """Initialize the source file."""
        super().__init__(path, content)
        self.name = path
        self.imports = []
        self.symbols = []
        self.classes = []
        self.functions = []
        self.global_vars = []
        self.interfaces = []

