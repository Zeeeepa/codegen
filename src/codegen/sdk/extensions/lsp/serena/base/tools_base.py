"""
Filtered Serena Tools Base Classes

Contains base Tool class and markers for non-agentic functionality.
Removes dependencies on SerenaAgent and other agentic components.
"""

import inspect
import os
from abc import ABC
from collections.abc import Iterable
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Protocol, Self, TypeVar

from mcp.server.fastmcp.utilities.func_metadata import FuncMetadata, func_metadata

T = TypeVar("T")
SUCCESS_RESULT = "OK"


class ToolMarker:
    """
    Base class for tool markers.
    """


class ToolMarkerCanEdit(ToolMarker):
    """
    Marker class for all tools that can perform editing operations on files.
    """


class ToolMarkerDoesNotRequireActiveProject(ToolMarker):
    pass


class ToolMarkerOptional(ToolMarker):
    """
    Marker class for optional tools that are disabled by default.
    """


class ToolMarkerSymbolicRead(ToolMarker):
    """
    Marker class for tools that perform symbol read operations.
    """


class ToolMarkerSymbolicEdit(ToolMarkerCanEdit):
    """
    Marker class for tools that perform symbolic edit operations.
    """


class ApplyMethodProtocol(Protocol):
    """Callable protocol for the apply method of a tool."""

    def __call__(self, *args: Any, **kwargs: Any) -> str:
        pass


class Tool(ABC):
    """
    Base Tool class for non-agentic functionality.
    
    Simplified version that doesn't depend on SerenaAgent or other agentic components.
    Tools should implement the apply method with proper docstring and type hints.
    """
    
    def __init__(self, project_root: str = None, **kwargs):
        """Initialize tool with optional project root."""
        self.project_root = project_root or os.getcwd()

    @classmethod
    def get_name_from_cls(cls) -> str:
        name = cls.__name__
        if name.endswith("Tool"):
            name = name[:-4]
        # convert to snake_case
        name = "".join(["_" + c.lower() if c.isupper() else c for c in name]).lstrip("_")
        return name

    def get_name(self) -> str:
        return self.get_name_from_cls()

    def get_apply_fn(self) -> ApplyMethodProtocol:
        apply_fn = getattr(self, "apply")
        if apply_fn is None:
            raise RuntimeError(f"apply not defined in {self}. Did you forget to implement it?")
        return apply_fn

    @classmethod
    def can_edit(cls) -> bool:
        """
        Returns whether this tool can perform editing operations on code.

        :return: True if the tool can edit code, False otherwise
        """
        return issubclass(cls, ToolMarkerCanEdit)

    @classmethod
    def get_tool_description(cls) -> str:
        docstring = cls.__doc__
        if docstring is None:
            return ""
        return docstring.strip()

    @classmethod
    def get_apply_docstring_from_cls(cls) -> str:
        """Get the docstring for the apply method from the class (static metadata).
        Needed for creating MCP tools in a separate process without running into serialization issues.
        """
        # First try to get from __dict__ to handle dynamic docstring changes
        if "apply" in cls.__dict__:
            apply_fn = cls.__dict__["apply"]
        else:
            # Fall back to getattr for inherited methods
            apply_fn = getattr(cls, "apply", None)
            if apply_fn is None:
                raise AttributeError(f"apply method not defined in {cls}. Did you forget to implement it?")

        docstring = apply_fn.__doc__
        if not docstring:
            raise AttributeError(f"apply method has no (or empty) docstring in {cls}. Did you forget to implement it?")
        return docstring.strip()

    def get_apply_docstring(self) -> str:
        """Gets the docstring for the tool application, used by the MCP server."""
        return self.get_apply_docstring_from_cls()

    def get_apply_fn_metadata(self) -> FuncMetadata:
        """Gets the metadata for the tool application function, used by the MCP server."""
        return self.get_apply_fn_metadata_from_cls()

    @classmethod
    def get_apply_fn_metadata_from_cls(cls) -> FuncMetadata:
        """Get the metadata for the apply method from the class (static metadata).
        Needed for creating MCP tools in a separate process without running into serialization issues.
        """
        # First try to get from __dict__ to handle dynamic docstring changes
        if "apply" in cls.__dict__:
            apply_fn = cls.__dict__["apply"]
        else:
            # Fall back to getattr for inherited methods
            apply_fn = getattr(cls, "apply", None)
            if apply_fn is None:
                raise AttributeError(f"apply method not defined in {cls}. Did you forget to implement it?")

        return func_metadata(apply_fn, skip_names=["self", "cls"])


class ToolRegistry:
    """
    Simple registry for managing tools without agentic dependencies.
    """
    
    def __init__(self):
        self._tools = {}
    
    def register(self, tool_class: type[Tool]):
        """Register a tool class."""
        name = tool_class.get_name_from_cls()
        self._tools[name] = tool_class
    
    def get_tool(self, name: str) -> type[Tool]:
        """Get a tool class by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
    
    def create_tool(self, name: str, **kwargs) -> Tool:
        """Create a tool instance by name."""
        tool_class = self.get_tool(name)
        if tool_class is None:
            raise ValueError(f"Tool '{name}' not found")
        return tool_class(**kwargs)
