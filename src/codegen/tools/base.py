"""
Base tool implementation for codegen.

This module provides the base class for all tools.
"""

from typing import Any, Callable, Dict, List, Optional, Union


class BaseTool:
    """Base class for all tools."""
    
    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        args_schema: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a tool.
        
        Args:
            name: Name of the tool
            description: Description of the tool
            func: Function to call when the tool is invoked
            args_schema: Schema for the tool's arguments
        """
        self.name = name
        self.description = description
        self.func = func
        self.args_schema = args_schema or {}
    
    def __call__(self, *args, **kwargs) -> Any:
        """Call the tool's function."""
        return self.func(*args, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the tool to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "args_schema": self.args_schema,
        }
