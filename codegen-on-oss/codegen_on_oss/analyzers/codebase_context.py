#!/usr/bin/env python3
"""
Codebase Context Module

This module provides a comprehensive graph-based context representation of a codebase
for advanced analysis capabilities, including dependency analysis, code structure
visualization, and PR comparison. It serves as the central data model for analysis.
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

# Import context components
from codegen_on_oss.analyzers.context.file import FileContext
from codegen_on_oss.analyzers.context.function import FunctionContext
from codegen_on_oss.analyzers.context.graph import (
    calculate_centrality,
    find_circular_dependencies,
)

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


class CodebaseContext:
    """
    Graph-based representation of a codebase for advanced analysis.

    This class provides a unified graph representation of a codebase, including
    files, directories, functions, classes, and their relationships. It serves
    as the central data model for all analysis operations.
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

        # File and symbol context caches
        self._file_contexts = {}
        self._function_contexts = {}

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
            file_path = file.file_path if hasattr(file, "file_path") else str(file)
            self._graph.add_node(file, type=NodeType.FILE, path=file_path)

            # Add nodes for functions in the file
            if hasattr(file, "functions"):
                for func in file.functions:
                    # Create function node
                    func_name = func.name if hasattr(func, "name") else str(func)
                    self._graph.add_node(
                        func, type=NodeType.FUNCTION, name=func_name, file=file
                    )

                    # Add edge from file to function
                    self._graph.add_edge(file, func, type=EdgeType.CONTAINS)

            # Add nodes for classes in the file
            if hasattr(file, "classes"):
                for cls in file.classes:
                    # Create class node
                    cls_name = cls.name if hasattr(cls, "name") else str(cls)
                    self._graph.add_node(
                        cls, type=NodeType.CLASS, name=cls_name, file=file
                    )

                    # Add edge from file to class
                    self._graph.add_edge(file, cls, type=EdgeType.CONTAINS)

                    # Add nodes for methods in the class
                    if hasattr(cls, "methods"):
                        for method in cls.methods:
                            # Create method node
                            method_name = (
                                method.name if hasattr(method, "name") else str(method)
                            )
                            self._graph.add_node(
                                method,
                                type=NodeType.FUNCTION,
                                name=method_name,
                                file=file,
                                class_name=cls_name,
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

    def get_file_context(self, file: SourceFile | str) -> FileContext:
        """
        Get context for a specific file.

        Args:
            file: File object or file path

        Returns:
            FileContext for the specified file
        """
        # If file is a string, find the corresponding file object
        if isinstance(file, str):
            for f in self.codebase.files:
                file_path = f.file_path if hasattr(f, "file_path") else str(f)
                if file_path == file:
                    file = f
                    break
            else:
                raise ValueError(f"File not found: {file}")

        # Get file path
        file_path = file.file_path if hasattr(file, "file_path") else str(file)

        # Return cached context if available
        if file_path in self._file_contexts:
            return self._file_contexts[file_path]

        # Create and cache new context
        context = FileContext(file)
        self._file_contexts[file_path] = context

        return context

    def get_function_context(self, function: Function | str) -> FunctionContext:
        """
        Get context for a specific function.

        Args:
            function: Function object or function name

        Returns:
            FunctionContext for the specified function
        """
        # If function is a string, find the corresponding function object
        if isinstance(function, str):
            for f in self.get_functions():
                if hasattr(f, "name") and f.name == function:
                    function = f
                    break
            else:
                raise ValueError(f"Function not found: {function}")

        # Get function name
        func_name = function.name if hasattr(function, "name") else str(function)

        # Return cached context if available
        if func_name in self._function_contexts:
            return self._function_contexts[func_name]

        # Create and cache new context
        context = FunctionContext(function)
        self._function_contexts[func_name] = context

        return context

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

    def get_nodes_by_type(self, node_type: NodeType) -> list[Any]:
        """
        Get nodes by type.

        Args:
            node_type: Type of nodes to get

        Returns:
            List of nodes of the specified type
        """
        return [n for n in self._graph.nodes if get_node_type(n) == node_type]

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

    def get_import_graph(self) -> nx.DiGraph:
        """
        Get the import dependency graph.

        Returns:
            NetworkX DiGraph representing import dependencies
        """
        # Create a subgraph with only file nodes
        files = self.get_files()
        subgraph = self._graph.subgraph(files)

        # Create a new graph with only import edges
        import_graph = nx.DiGraph()

        for source, target, data in subgraph.edges(data=True):
            if "type" in data and data["type"] == EdgeType.IMPORTS:
                # Get file paths
                source_path = (
                    source.file_path if hasattr(source, "file_path") else str(source)
                )
                target_path = (
                    target.file_path if hasattr(target, "file_path") else str(target)
                )

                # Add edge to import graph
                import_graph.add_edge(source_path, target_path)

        return import_graph

    def get_call_graph(self) -> nx.DiGraph:
        """
        Get the function call graph.

        Returns:
            NetworkX DiGraph representing function calls
        """
        # Create a subgraph with only function nodes
        functions = self.get_functions()
        subgraph = self._graph.subgraph(functions)

        # Create a new graph with only call edges
        call_graph = nx.DiGraph()

        for source, target, data in subgraph.edges(data=True):
            if "type" in data and data["type"] == EdgeType.CALLS:
                # Get function names
                source_name = source.name if hasattr(source, "name") else str(source)
                target_name = target.name if hasattr(target, "name") else str(target)

                # Add edge to call graph
                call_graph.add_edge(source_name, target_name)

        return call_graph

    def get_inheritance_graph(self) -> nx.DiGraph:
        """
        Get the class inheritance graph.

        Returns:
            NetworkX DiGraph representing class inheritance
        """
        # Create a subgraph with only class nodes
        classes = self.get_classes()
        subgraph = self._graph.subgraph(classes)

        # Create a new graph with only inheritance edges
        inheritance_graph = nx.DiGraph()

        for source, target, data in subgraph.edges(data=True):
            if "type" in data and data["type"] == EdgeType.INHERITS_FROM:
                # Get class names
                source_name = source.name if hasattr(source, "name") else str(source)
                target_name = target.name if hasattr(target, "name") else str(target)

                # Add edge to inheritance graph
                inheritance_graph.add_edge(source_name, target_name)

        return inheritance_graph

    def analyze_dependencies(self) -> dict[str, Any]:
        """
        Analyze dependencies in the codebase.

        Returns:
            Dictionary containing dependency analysis results
        """
        # Get import graph
        import_graph = self.get_import_graph()

        # Find circular dependencies
        circular_deps = find_circular_dependencies(import_graph)

        # Calculate centrality
        centrality = calculate_centrality(import_graph)

        # Find hub modules (most central)
        hub_modules = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "circular_dependencies": [
                {"cycle": cycle, "length": len(cycle)} for cycle in circular_deps
            ],
            "hub_modules": [
                {"module": module, "centrality": centrality}
                for module, centrality in hub_modules
            ],
            "dependency_count": len(import_graph.edges),
            "module_count": len(import_graph.nodes),
        }

    def analyze_code_structure(self) -> dict[str, Any]:
        """
        Analyze code structure.

        Returns:
            Dictionary containing code structure analysis results
        """
        return {
            "file_count": len(self.get_files()),
            "function_count": len(self.get_functions()),
            "class_count": len(self.get_classes()),
            "average_file_size": self._calculate_average_file_size(),
            "average_function_size": self._calculate_average_function_size(),
            "most_complex_files": self._find_most_complex_files(10),
            "most_complex_functions": self._find_most_complex_functions(10),
        }

    def _calculate_average_file_size(self) -> float:
        """
        Calculate average file size in lines.

        Returns:
            Average file size in lines
        """
        files = self.get_files()

        if not files:
            return 0

        total_lines = 0
        file_count = 0

        for file in files:
            if hasattr(file, "content"):
                lines = len(file.content.split("\n"))
                total_lines += lines
                file_count += 1

        return total_lines / file_count if file_count > 0 else 0

    def _calculate_average_function_size(self) -> float:
        """
        Calculate average function size in lines.

        Returns:
            Average function size in lines
        """
        functions = self.get_functions()

        if not functions:
            return 0

        total_lines = 0
        function_count = 0

        for func in functions:
            if hasattr(func, "source"):
                lines = len(func.source.split("\n"))
                total_lines += lines
                function_count += 1

        return total_lines / function_count if function_count > 0 else 0

    def _find_most_complex_files(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Find the most complex files.

        Args:
            limit: Maximum number of files to return

        Returns:
            List of complex files with complexity metrics
        """
        files = self.get_files()
        file_complexity = []

        for file in files:
            file_context = self.get_file_context(file)
            complexity = file_context.analyze_complexity()

            file_complexity.append({
                "file": file_context.path,
                "complexity": complexity,
            })

        # Sort by complexity
        file_complexity.sort(
            key=lambda x: x["complexity"].get("total_complexity", 0), reverse=True
        )

        return file_complexity[:limit]

    def _find_most_complex_functions(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Find the most complex functions.

        Args:
            limit: Maximum number of functions to return

        Returns:
            List of complex functions with complexity metrics
        """
        functions = self.get_functions()
        function_complexity = []

        for func in functions:
            function_context = self.get_function_context(func)
            complexity = function_context.analyze_complexity()

            function_complexity.append({
                "function": function_context.name,
                "file": function_context.file_path,
                "line": function_context.line,
                "complexity": complexity["cyclomatic_complexity"],
            })

        # Sort by complexity
        function_complexity.sort(key=lambda x: x["complexity"], reverse=True)

        return function_complexity[:limit]

    def export_to_dict(self) -> dict[str, Any]:
        """
        Export the codebase context to a dictionary.

        Returns:
            Dictionary representation of the codebase context
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

        return {
            "nodes": nodes,
            "edges": edges,
            "summary": {
                "file_count": len(self.get_files()),
                "function_count": len(self.get_functions()),
                "class_count": len(self.get_classes()),
                "edge_count": len(self._graph.edges),
            },
        }
