#!/usr/bin/env python3
"""
Codebase Context Module

This module provides a graph-based context representation of a codebase
for advanced analysis capabilities, including dependency analysis,
code structure visualization, and PR comparison.
"""

import logging
import sys
from enum import Enum
from typing import Any

import networkx as nx

try:
    from codegen.sdk.codebase.codebase_context import (
        CodebaseContext as SDKCodebaseContext,
    )
    from codegen.sdk.core.class_definition import Class
    from codegen.sdk.core.codebase import Codebase
    from codegen.sdk.core.directory import Directory
    from codegen.sdk.core.file import SourceFile
    from codegen.sdk.core.function import Function
    from codegen.sdk.core.symbol import Symbol
    from codegen.sdk.enums import EdgeType, SymbolType
except ImportError:
    print("Codegen SDK not found. Please install it first.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Global file ignore patterns
GLOBAL_FILE_IGNORE_LIST = [
    "__pycache__",
    ".git",
    "node_modules",
    "dist",
    "build",
    ".DS_Store",
    ".pytest_cache",
    ".venv",
    "venv",
    "env",
    ".env",
    ".idea",
    ".vscode",
]


class NodeType(str, Enum):
    """Types of nodes in the graph."""

    FILE = "file"
    DIRECTORY = "directory"
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    VARIABLE = "variable"
    UNKNOWN = "unknown"


def get_node_type(node: Any) -> NodeType:
    """Determine the type of a node."""
    if isinstance(node, SourceFile):
        return NodeType.FILE
    elif isinstance(node, Directory):
        return NodeType.DIRECTORY
    elif isinstance(node, Function):
        return NodeType.FUNCTION
    elif isinstance(node, Class):
        return NodeType.CLASS
    else:
        return NodeType.UNKNOWN


def get_node_classes():
    """Get a dictionary mapping node types to their classes."""
    return {
        NodeType.FILE: SourceFile,
        NodeType.DIRECTORY: Directory,
        NodeType.FUNCTION: Function,
        NodeType.CLASS: Class,
    }


class CodebaseContext:
    """
    Graph-based representation of a codebase for advanced analysis.

    This class provides a graph representation of a codebase, including
    files, directories, functions, classes, and their relationships.
    It supports advanced analysis capabilities such as dependency analysis,
    code structure visualization, and PR comparison.
    """

    def __init__(
        self,
        codebase: Codebase,
        base_path: str | None = None,
        pr_branch: str | None = None,
        base_branch: str = "main",
        file_ignore_list: list[str] | None = None,
    ):
        """
        Initialize the CodebaseContext.

        Args:
            codebase: The codebase to analyze
            base_path: Base path of the codebase
            pr_branch: PR branch name (for PR analysis)
            base_branch: Base branch name (for PR analysis)
            file_ignore_list: List of file patterns to ignore
        """
        self.codebase = codebase
        self.base_path = base_path
        self.pr_branch = pr_branch
        self.base_branch = base_branch
        self.file_ignore_list = file_ignore_list or GLOBAL_FILE_IGNORE_LIST

        # Initialize graph
        self._graph = nx.DiGraph()

        # Build the graph
        self._build_graph()

    def _build_graph(self):
        """Build the codebase graph."""
        logger.info("Building codebase graph...")

        # Add nodes for files
        for file in self.codebase.files:
            # Skip ignored files
            if self._should_ignore_file(file):
                continue

            # Add file node
            self._graph.add_node(
                file,
                type=NodeType.FILE,
                path=file.file_path if hasattr(file, "file_path") else str(file),
            )

            # Add nodes for functions in the file
            if hasattr(file, "functions"):
                for func in file.functions:
                    self._graph.add_node(
                        func,
                        type=NodeType.FUNCTION,
                        name=func.name if hasattr(func, "name") else str(func),
                        file=file,
                    )

                    # Add edge from file to function
                    self._graph.add_edge(file, func, type=EdgeType.CONTAINS)

            # Add nodes for classes in the file
            if hasattr(file, "classes"):
                for cls in file.classes:
                    self._graph.add_node(
                        cls,
                        type=NodeType.CLASS,
                        name=cls.name if hasattr(cls, "name") else str(cls),
                        file=file,
                    )

                    # Add edge from file to class
                    self._graph.add_edge(file, cls, type=EdgeType.CONTAINS)

                    # Add nodes for methods in the class
                    if hasattr(cls, "methods"):
                        for method in cls.methods:
                            self._graph.add_node(
                                method,
                                type=NodeType.FUNCTION,
                                name=method.name
                                if hasattr(method, "name")
                                else str(method),
                                file=file,
                                class_name=cls.name
                                if hasattr(cls, "name")
                                else str(cls),
                            )

                            # Add edge from class to method
                            self._graph.add_edge(cls, method, type=EdgeType.CONTAINS)

        # Add edges for imports
        for file in self.codebase.files:
            # Skip ignored files
            if self._should_ignore_file(file):
                continue

            # Add import edges
            if hasattr(file, "imports"):
                for imp in file.imports:
                    # Get imported file
                    imported_file = None

                    if hasattr(imp, "resolved_file"):
                        imported_file = imp.resolved_file
                    elif hasattr(imp, "resolved_symbol") and hasattr(
                        imp.resolved_symbol, "file"
                    ):
                        imported_file = imp.resolved_symbol.file

                    if imported_file and imported_file in self._graph:
                        # Add edge from file to imported file
                        self._graph.add_edge(file, imported_file, type=EdgeType.IMPORTS)

        # Add edges for function calls
        for func in [
            n for n in self._graph.nodes if get_node_type(n) == NodeType.FUNCTION
        ]:
            if hasattr(func, "call_sites"):
                for call_site in func.call_sites:
                    if (
                        hasattr(call_site, "called_function")
                        and call_site.called_function in self._graph
                    ):
                        # Add edge from function to called function
                        self._graph.add_edge(
                            func, call_site.called_function, type=EdgeType.CALLS
                        )

        # Add edges for class inheritance
        for cls in [n for n in self._graph.nodes if get_node_type(n) == NodeType.CLASS]:
            if hasattr(cls, "superclasses"):
                for superclass in cls.superclasses:
                    if superclass in self._graph:
                        # Add edge from class to superclass
                        self._graph.add_edge(
                            cls, superclass, type=EdgeType.INHERITS_FROM
                        )

        logger.info(
            f"Graph built with {len(self._graph.nodes)} nodes and {len(self._graph.edges)} edges"
        )

    def _should_ignore_file(self, file) -> bool:
        """Check if a file should be ignored."""
        if hasattr(file, "is_binary") and file.is_binary:
            return True

        file_path = file.file_path if hasattr(file, "file_path") else str(file)

        # Check against ignore list
        return any(pattern in file_path for pattern in self.file_ignore_list)

    @property
    def graph(self) -> nx.DiGraph:
        """Get the codebase graph."""
        return self._graph

    @property
    def nodes(self) -> list[Any]:
        """Get all nodes in the graph."""
        return list(self._graph.nodes)

    def get_node(self, name: str) -> Any | None:
        """
        Get a node by name.

        Args:
            name: Name of the node to get

        Returns:
            The node, or None if not found
        """
        for node in self._graph.nodes:
            if (hasattr(node, "name") and node.name == name) or str(node) == name:
                return node
        return None

    def predecessors(self, node: Any) -> list[Any]:
        """
        Get predecessors of a node.

        Args:
            node: Node to get predecessors for

        Returns:
            List of predecessor nodes
        """
        return list(self._graph.predecessors(node))

    def successors(self, node: Any) -> list[Any]:
        """
        Get successors of a node.

        Args:
            node: Node to get successors for

        Returns:
            List of successor nodes
        """
        return list(self._graph.successors(node))

    def in_edges(self, node: Any, data: bool = False) -> list[Any]:
        """
        Get incoming edges of a node.

        Args:
            node: Node to get edges for
            data: Whether to include edge data

        Returns:
            List of incoming edges
        """
        return list(self._graph.in_edges(node, data=data))

    def out_edges(self, node: Any, data: bool = False) -> list[Any]:
        """
        Get outgoing edges of a node.

        Args:
            node: Node to get edges for
            data: Whether to include edge data

        Returns:
            List of outgoing edges
        """
        return list(self._graph.out_edges(node, data=data))

    def edges(self, data: bool = False) -> list[Any]:
        """
        Get all edges in the graph.

        Args:
            data: Whether to include edge data

        Returns:
            List of edges
        """
        return list(self._graph.edges(data=data))

    def get_nodes_by_type(self, node_type: NodeType) -> list[Any]:
        """
        Get nodes by type.

        Args:
            node_type: Type of nodes to get

        Returns:
            List of nodes of the specified type
        """
        return [n for n in self._graph.nodes if get_node_type(n) == node_type]

    def build_subgraph(self, nodes: list[Any]) -> nx.DiGraph:
        """
        Build a subgraph from a list of nodes.

        Args:
            nodes: List of nodes to include in the subgraph

        Returns:
            Subgraph containing the specified nodes
        """
        return self._graph.subgraph(nodes)

    def find_paths(
        self, source: Any, target: Any, cutoff: int | None = None
    ) -> list[list[Any]]:
        """
        Find all paths between two nodes.

        Args:
            source: Source node
            target: Target node
            cutoff: Maximum path length

        Returns:
            List of paths from source to target
        """
        if source not in self._graph or target not in self._graph:
            return []

        try:
            return list(nx.all_simple_paths(self._graph, source, target, cutoff=cutoff))
        except nx.NetworkXError:
            return []

    def find_shortest_path(self, source: Any, target: Any) -> list[Any] | None:
        """
        Find the shortest path between two nodes.

        Args:
            source: Source node
            target: Target node

        Returns:
            Shortest path from source to target, or None if no path exists
        """
        if source not in self._graph or target not in self._graph:
            return None

        try:
            return nx.shortest_path(self._graph, source, target)
        except nx.NetworkXNoPath:
            return None

    def find_cycles(self) -> list[list[Any]]:
        """
        Find cycles in the graph.

        Returns:
            List of cycles in the graph
        """
        try:
            return list(nx.simple_cycles(self._graph))
        except nx.NetworkXNoCycle:
            return []

    def get_files(self) -> list[SourceFile]:
        """
        Get all files in the codebase.

        Returns:
            List of files
        """
        return self.get_nodes_by_type(NodeType.FILE)

    def get_functions(self) -> list[Function]:
        """
        Get all functions in the codebase.

        Returns:
            List of functions
        """
        return self.get_nodes_by_type(NodeType.FUNCTION)

    def get_classes(self) -> list[Class]:
        """
        Get all classes in the codebase.

        Returns:
            List of classes
        """
        return self.get_nodes_by_type(NodeType.CLASS)

    def export_to_networkx(self) -> nx.DiGraph:
        """
        Export the graph to a NetworkX graph.

        Returns:
            NetworkX graph representation of the codebase
        """
        return self._graph.copy()

    def export_to_dict(self) -> dict[str, Any]:
        """
        Export the graph to a dictionary.

        Returns:
            Dictionary representation of the codebase graph
        """
        nodes = []
        for node in self._graph.nodes:
            node_data = {
                "id": str(id(node)),
                "type": get_node_type(node).value,
            }

            if hasattr(node, "name"):
                node_data["name"] = node.name

            if hasattr(node, "file") and hasattr(node.file, "file_path"):
                node_data["file"] = node.file.file_path

            nodes.append(node_data)

        edges = []
        for source, target, data in self._graph.edges(data=True):
            edge_data = {
                "source": str(id(source)),
                "target": str(id(target)),
            }

            if "type" in data:
                edge_data["type"] = (
                    data["type"].value
                    if isinstance(data["type"], Enum)
                    else str(data["type"])
                )

            edges.append(edge_data)

        return {"nodes": nodes, "edges": edges}
