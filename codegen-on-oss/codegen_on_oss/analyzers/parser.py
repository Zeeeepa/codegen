#!/usr/bin/env python3
"""
Code Parser Module for Analyzers

This module provides specialized parsing functionality for code analysis,
including abstract syntax tree (AST) generation and traversal for multiple
programming languages. It serves as a foundation for various code analyzers
in the system.
"""

import importlib.util
import logging
import sys
from enum import Enum
from typing import Any, Optional, TypeVar

# Check if required modules are available
if importlib.util.find_spec("codegen.sdk") is None:
    print("Codegen SDK not found.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Type variable for generic parser implementations
T = TypeVar("T")


class ParserType(Enum):
    """Enum defining the types of parsers available."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GENERIC = "generic"


class ParseError(Exception):
    """Exception raised for errors during parsing."""

    pass


class ASTNode:
    """
    Base class representing a node in an Abstract Syntax Tree.

    This provides a common interface for working with AST nodes
    regardless of the underlying parser implementation.
    """

    def __init__(
        self,
        node_type: str,
        value: str | None = None,
        children: list["ASTNode"] | None = None,
        parent: Optional["ASTNode"] = None,
        start_position: tuple[int, int] | None = None,
        end_position: tuple[int, int] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Initialize an AST node.

        Args:
            node_type: Type of the node (e.g., 'function', 'class', 'variable')
            value: Optional value associated with the node
            children: List of child nodes
            parent: Parent node
            start_position: Tuple of (line, column) for the start position
            end_position: Tuple of (line, column) for the end position
            metadata: Additional metadata for the node
        """
        self.node_type = node_type
        self.value = value
        self.children = children or []
        self.parent = parent
        self.start_position = start_position
        self.end_position = end_position
        self.metadata = metadata or {}

    def add_child(self, child: "ASTNode") -> None:
        """
        Add a child node to this node.

        Args:
            child: Child node to add
        """
        self.children.append(child)
        child.parent = self

    def find_nodes_by_type(self, node_type: str) -> list["ASTNode"]:
        """
        Find all descendant nodes of a specific type.

        Args:
            node_type: Type of nodes to find

        Returns:
            List of matching nodes
        """
        result = []
        if self.node_type == node_type:
            result.append(self)

        for child in self.children:
            result.extend(child.find_nodes_by_type(node_type))

        return result

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the node to a dictionary representation.

        Returns:
            Dictionary representation of the node
        """
        return {
            "type": self.node_type,
            "value": self.value,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "metadata": self.metadata,
            "children": [child.to_dict() for child in self.children],
        }

    def __repr__(self) -> str:
        """String representation of the node."""
        return f"ASTNode({self.node_type}, value={self.value}, children={len(self.children)})"
