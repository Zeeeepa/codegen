#!/usr/bin/env python3
"""
Codebase Visualizer Module

This module provides comprehensive visualization capabilities for codebases and PR analyses.
It integrates with codebase_analyzer.py and context_codebase.py to provide visual representations
of code structure, dependencies, and issues. It supports multiple visualization types to help
developers understand codebase architecture and identify potential problems.
"""

import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

try:
    import matplotlib.pyplot as plt
    import networkx as nx
    from matplotlib.colors import LinearSegmentedColormap
except ImportError:
    print(
        "Visualization dependencies not found. Please install them with: pip install networkx matplotlib"
    )
    sys.exit(1)

try:
    from codegen.sdk.core.class_definition import Class
    from codegen.sdk.core.codebase import Codebase
    from codegen.sdk.core.detached_symbols.function_call import FunctionCall
    from codegen.sdk.core.file import SourceFile
    from codegen.sdk.core.function import Function
    from codegen.sdk.core.import_resolution import Import
    from codegen.sdk.core.symbol import Symbol
    from codegen.sdk.enums import EdgeType, SymbolType

    from codegen_on_oss.codebase_analyzer import (
        AnalysisType,
        CodebaseAnalyzer,
        Issue,
        IssueSeverity,
    )

    # Import custom modules
    from codegen_on_oss.context_codebase import (
        GLOBAL_FILE_IGNORE_LIST,
        CodebaseContext,
        get_node_classes,
    )
    from codegen_on_oss.current_code_codebase import get_selected_codebase
except ImportError:
    print(
        "Codegen SDK or custom modules not found. Please ensure all dependencies are installed."
    )
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class VisualizationType(str, Enum):
    """Types of visualizations supported by this module."""

    CALL_GRAPH = "call_graph"
    DEPENDENCY_GRAPH = "dependency_graph"
    BLAST_RADIUS = "blast_radius"
    CLASS_METHODS = "class_methods"
    MODULE_DEPENDENCIES = "module_dependencies"
    DEAD_CODE = "dead_code"
    CYCLOMATIC_COMPLEXITY = "cyclomatic_complexity"
    ISSUES_HEATMAP = "issues_heatmap"
    PR_COMPARISON = "pr_comparison"


class OutputFormat(str, Enum):
    """Output formats for visualizations."""

    JSON = "json"
    PNG = "png"
    SVG = "svg"
    HTML = "html"
    DOT = "dot"


@dataclass
class VisualizationConfig:
    """Configuration for visualization generation."""

    max_depth: int = 5
    ignore_external: bool = True
    ignore_tests: bool = True
    node_size_base: int = 300
    edge_width_base: float = 1.0
    filename_filter: list[str] | None = None
    symbol_filter: list[str] | None = None
    output_format: OutputFormat = OutputFormat.JSON
    output_directory: str | None = None
    layout_algorithm: str = "spring"
    highlight_nodes: list[str] = field(default_factory=list)
    highlight_color: str = "#ff5555"
    color_palette: dict[str, str] = field(
        default_factory=lambda: {
            "Function": "#a277ff",  # Purple
            "Class": "#ffca85",  # Orange
            "File": "#80CBC4",  # Teal
            "Module": "#81D4FA",  # Light Blue
            "Variable": "#B39DDB",  # Light Purple
            "Root": "#ef5350",  # Red
            "Warning": "#FFCA28",  # Amber
            "Error": "#EF5350",  # Red
            "Dead": "#78909C",  # Gray
            "External": "#B0BEC5",  # Light Gray
        }
    )


class CodebaseVisualizer:
    """
    Visualizer for codebase structures and analytics.

    This class provides methods to generate various visualizations of a codebase,
    including call graphs, dependency graphs, complexity heatmaps, and more.
    It integrates with CodebaseAnalyzer to visualize analysis results.
    """

    def __init__(
        self,
        analyzer: CodebaseAnalyzer | None = None,
        codebase: Codebase | None = None,
        context: CodebaseContext | None = None,
        config: VisualizationConfig | None = None,
    ):
        """
        Initialize the CodebaseVisualizer.

        Args:
            analyzer: Optional CodebaseAnalyzer instance with analysis results
            codebase: Optional Codebase instance to visualize
            context: Optional CodebaseContext providing graph representation
            config: Visualization configuration options
        """
        self.analyzer = analyzer
        self.codebase = codebase or (analyzer.base_codebase if analyzer else None)
        self.context = context or (analyzer.base_context if analyzer else None)
        self.config = config or VisualizationConfig()

        # Create visualization directory if specified
        if self.config.output_directory:
            os.makedirs(self.config.output_directory, exist_ok=True)

        # Initialize graph for visualization
        self.graph = nx.DiGraph()

        # Initialize codebase if needed
        if not self.codebase and not self.context:
            logger.info(
                "No codebase or context provided, initializing from current directory"
            )
            self.codebase = get_selected_codebase()
            self.context = CodebaseContext(
                codebase=self.codebase, base_path=os.getcwd()
            )
        elif self.codebase and not self.context:
            logger.info("Creating context from provided codebase")
            self.context = CodebaseContext(
                codebase=self.codebase,
                base_path=os.getcwd()
                if not hasattr(self.codebase, "base_path")
                else self.codebase.base_path,
            )

    def _initialize_graph(self):
        """Initialize a fresh graph for visualization."""
        self.graph = nx.DiGraph()

    def _add_node(self, node: Any, **attrs):
        """
        Add a node to the visualization graph with attributes.

        Args:
            node: Node object to add
            **attrs: Node attributes
        """
        # Skip if node already exists
        if self.graph.has_node(node):
            return

        # Generate node ID (memory address for unique identification)
        node_id = id(node)

        # Get node name
        if "name" in attrs:
            node_name = attrs["name"]
        elif hasattr(node, "name"):
            node_name = node.name
        elif hasattr(node, "path"):
            node_name = str(node.path).split("/")[-1]
        else:
            node_name = str(node)

        # Determine node type and color
        node_type = node.__class__.__name__
        color = attrs.get("color", self.config.color_palette.get(node_type, "#BBBBBB"))

        # Add node with attributes
        self.graph.add_node(
            node_id,
            original_node=node,
            name=node_name,
            type=node_type,
            color=color,
            **attrs,
        )

        return node_id

    def _add_edge(self, source: Any, target: Any, **attrs):
        """
        Add an edge to the visualization graph with attributes.

        Args:
            source: Source node
            target: Target node
            **attrs: Edge attributes
        """
        # Get node IDs
        source_id = id(source)
        target_id = id(target)

        # Add edge with attributes
        self.graph.add_edge(source_id, target_id, **attrs)

    def _generate_filename(
        self, visualization_type: VisualizationType, entity_name: str
    ):
        """
        Generate a filename for the visualization.

        Args:
            visualization_type: Type of visualization
            entity_name: Name of the entity being visualized

        Returns:
            Generated filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_name = (
            entity_name.replace("/", "_").replace("\\", "_").replace(".", "_")
        )
        return f"{visualization_type.value}_{sanitized_name}_{timestamp}.{self.config.output_format.value}"

    def _save_visualization(
        self, visualization_type: VisualizationType, entity_name: str, data: Any
    ):
        """
        Save a visualization to file or return it.

        Args:
            visualization_type: Type of visualization
            entity_name: Name of the entity being visualized
            data: Visualization data to save

        Returns:
            Path to saved file or visualization data
        """
        filename = self._generate_filename(visualization_type, entity_name)

        if self.config.output_directory:
            filepath = os.path.join(self.config.output_directory, filename)
        else:
            filepath = filename

        if self.config.output_format == OutputFormat.JSON:
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
        elif self.config.output_format in [OutputFormat.PNG, OutputFormat.SVG]:
            # Save matplotlib figure
            plt.savefig(
                filepath, format=self.config.output_format.value, bbox_inches="tight"
            )
            plt.close()
        elif self.config.output_format == OutputFormat.DOT:
            # Save as DOT file for Graphviz
            try:
                from networkx.drawing.nx_agraph import write_dot

                write_dot(self.graph, filepath)
            except ImportError:
                logger.exception(
                    "networkx.drawing.nx_agraph not available. Install pygraphviz for DOT format."
                )
                return None

        logger.info(f"Visualization saved to {filepath}")
        return filepath

    def _convert_graph_to_json(self):
        """
        Convert the networkx graph to a JSON-serializable dictionary.

        Returns:
            Dictionary representation of the graph
        """
        nodes = []
        for node, attrs in self.graph.nodes(data=True):
            # Create a serializable node
            node_data = {
                "id": node,
                "name": attrs.get("name", ""),
                "type": attrs.get("type", ""),
                "color": attrs.get("color", "#BBBBBB"),
            }

            # Add file path if available
            if "file_path" in attrs:
                node_data["file_path"] = attrs["file_path"]

            # Add other attributes
            for key, value in attrs.items():
                if key not in ["name", "type", "color", "file_path", "original_node"]:
                    if (
                        isinstance(value, str | int | float | bool | list | dict)
                        or value is None
                    ):
                        node_data[key] = value

            nodes.append(node_data)

        edges = []
        for source, target, attrs in self.graph.edges(data=True):
            # Create a serializable edge
            edge_data = {
                "source": source,
                "target": target,
            }

            # Add other attributes
            for key, value in attrs.items():
                if (
                    isinstance(value, str | int | float | bool | list | dict)
                    or value is None
                ):
                    edge_data[key] = value

            edges.append(edge_data)

        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "visualization_type": self.current_visualization_type,
                "entity_name": self.current_entity_name,
                "timestamp": datetime.now().isoformat(),
                "node_count": len(nodes),
                "edge_count": len(edges),
            },
        }

    def _plot_graph(self):
        """
        Plot the graph using matplotlib.

        Returns:
            Matplotlib figure
        """
        plt.figure(figsize=(12, 10))

        # Extract node positions using specified layout algorithm
        if self.config.layout_algorithm == "spring":
            pos = nx.spring_layout(self.graph, seed=42)
        elif self.config.layout_algorithm == "kamada_kawai":
            pos = nx.kamada_kawai_layout(self.graph)
        elif self.config.layout_algorithm == "spectral":
            pos = nx.spectral_layout(self.graph)
        else:
            # Default to spring layout
            pos = nx.spring_layout(self.graph, seed=42)

        # Extract node colors
        node_colors = [
            attrs.get("color", "#BBBBBB") for _, attrs in self.graph.nodes(data=True)
        ]

        # Extract node sizes (can be based on some metric)
        node_sizes = [self.config.node_size_base for _ in self.graph.nodes()]

        # Draw nodes
        nx.draw_networkx_nodes(
            self.graph, pos, node_color=node_colors, node_size=node_sizes, alpha=0.8
        )

        # Draw edges
        nx.draw_networkx_edges(
            self.graph,
            pos,
            width=self.config.edge_width_base,
            alpha=0.6,
            arrows=True,
            arrowsize=10,
        )

        # Draw labels
        nx.draw_networkx_labels(
            self.graph,
            pos,
            labels={
                node: attrs.get("name", "")
                for node, attrs in self.graph.nodes(data=True)
            },
            font_size=8,
            font_weight="bold",
        )

        plt.title(f"{self.current_visualization_type} - {self.current_entity_name}")
        plt.axis("off")

        return plt.gcf()

    def visualize_call_graph(self, function_name: str, max_depth: int | None = None):
        """
        Generate a call graph visualization for a function.

        Args:
            function_name: Name of the function to visualize
            max_depth: Maximum depth of the call graph (overrides config)

        Returns:
            Visualization data or path to saved file
        """
        self.current_visualization_type = VisualizationType.CALL_GRAPH
        self.current_entity_name = function_name

        # Set max depth
        current_max_depth = (
            max_depth if max_depth is not None else self.config.max_depth
        )

        # Initialize graph
        self._initialize_graph()

        # Find the function in the codebase
        function = None
        for func in self.codebase.functions:
            if func.name == function_name:
                function = func
                break

        if not function:
            logger.error(f"Function {function_name} not found in codebase")
            return None

        # Add root node
        self._add_node(
            function,
            name=function_name,
            color=self.config.color_palette.get("Root"),
            is_root=True,
        )

        # Recursively add call relationships
        visited = {function}

        def add_calls(func, depth=0):
            if depth >= current_max_depth:
                return

            # Skip if no function calls attribute
            if not hasattr(func, "function_calls"):
                return

            for call in func.function_calls:
                # Skip recursive calls
                if call.name == func.name:
                    continue

                # Get the called function
                called_func = call.function_definition
                if not called_func:
                    continue

                # Skip external modules if configured
                if (
                    self.config.ignore_external
                    and hasattr(called_func, "is_external")
                    and called_func.is_external
                ):
                    continue

                # Generate name for display
                if (
                    hasattr(called_func, "is_method")
                    and called_func.is_method
                    and hasattr(called_func, "parent_class")
                ):
                    called_name = f"{called_func.parent_class.name}.{called_func.name}"
                else:
                    called_name = called_func.name

                # Add node for called function
                self._add_node(
                    called_func,
                    name=called_name,
                    color=self.config.color_palette.get("Function"),
                    file_path=called_func.file.path
                    if hasattr(called_func, "file")
                    and hasattr(called_func.file, "path")
                    else None,
                )

                # Add edge for call relationship
                self._add_edge(
                    function,
                    called_func,
                    type="call",
                    file_path=call.filepath if hasattr(call, "filepath") else None,
                    line=call.line if hasattr(call, "line") else None,
                )

                # Recursively process called function
                if isinstance(called_func, Function) and called_func not in visited:
                    visited.add(called_func)
                    add_calls(called_func, depth + 1)

        # Start from the root function
        add_calls(function)

        # Generate visualization data
        if self.config.output_format == OutputFormat.JSON:
            data = self._convert_graph_to_json()
            return self._save_visualization(
                VisualizationType.CALL_GRAPH, function_name, data
            )
        else:
            fig = self._plot_graph()
            return self._save_visualization(
                VisualizationType.CALL_GRAPH, function_name, fig
            )

    def visualize_dependency_graph(
        self, symbol_name: str, max_depth: int | None = None
    ):
        """
        Generate a dependency graph visualization for a symbol.

        Args:
            symbol_name: Name of the symbol to visualize
            max_depth: Maximum depth of the dependency graph (overrides config)

        Returns:
            Visualization data or path to saved file
        """
        self.current_visualization_type = VisualizationType.DEPENDENCY_GRAPH
        self.current_entity_name = symbol_name

        # Set max depth
        current_max_depth = (
            max_depth if max_depth is not None else self.config.max_depth
        )

        # Initialize graph
        self._initialize_graph()

        # Find the symbol in the codebase
        symbol = None
        for sym in self.codebase.symbols:
            if hasattr(sym, "name") and sym.name == symbol_name:
                symbol = sym
                break

        if not symbol:
            logger.error(f"Symbol {symbol_name} not found in codebase")
            return None

        # Add root node
        self._add_node(
            symbol,
            name=symbol_name,
            color=self.config.color_palette.get("Root"),
            is_root=True,
        )

        # Recursively add dependencies
        visited = {symbol}

        def add_dependencies(sym, depth=0):
            if depth >= current_max_depth:
                return

            # Skip if no dependencies attribute
            if not hasattr(sym, "dependencies"):
                return

            for dep in sym.dependencies:
                dep_symbol = None

                if isinstance(dep, Symbol):
                    dep_symbol = dep
                elif isinstance(dep, Import) and hasattr(dep, "resolved_symbol"):
                    dep_symbol = dep.resolved_symbol

                if not dep_symbol:
                    continue

                # Skip external modules if configured
                if (
                    self.config.ignore_external
                    and hasattr(dep_symbol, "is_external")
                    and dep_symbol.is_external
                ):
                    continue

                # Add node for dependency
                self._add_node(
                    dep_symbol,
                    name=dep_symbol.name
                    if hasattr(dep_symbol, "name")
                    else str(dep_symbol),
                    color=self.config.color_palette.get(
                        dep_symbol.__class__.__name__, "#BBBBBB"
                    ),
                    file_path=dep_symbol.file.path
                    if hasattr(dep_symbol, "file") and hasattr(dep_symbol.file, "path")
                    else None,
                )

                # Add edge for dependency relationship
                self._add_edge(sym, dep_symbol, type="depends_on")

                # Recursively process dependency
                if dep_symbol not in visited:
                    visited.add(dep_symbol)
                    add_dependencies(dep_symbol, depth + 1)

        # Start from the root symbol
        add_dependencies(symbol)

        # Generate visualization data
        if self.config.output_format == OutputFormat.JSON:
            data = self._convert_graph_to_json()
            return self._save_visualization(
                VisualizationType.DEPENDENCY_GRAPH, symbol_name, data
            )
        else:
            fig = self._plot_graph()
            return self._save_visualization(
                VisualizationType.DEPENDENCY_GRAPH, symbol_name, fig
            )

    def visualize_blast_radius(self, symbol_name: str, max_depth: int | None = None):
        """
        Generate a blast radius visualization for a symbol.

        Args:
            symbol_name: Name of the symbol to visualize
            max_depth: Maximum depth of the blast radius (overrides config)

        Returns:
            Visualization data or path to saved file
        """
        self.current_visualization_type = VisualizationType.BLAST_RADIUS
        self.current_entity_name = symbol_name

        # Set max depth
        current_max_depth = (
            max_depth if max_depth is not None else self.config.max_depth
        )

        # Initialize graph
        self._initialize_graph()

        # Find the symbol in the codebase
        symbol = None
        for sym in self.codebase.symbols:
            if hasattr(sym, "name") and sym.name == symbol_name:
                symbol = sym
                break

        if not symbol:
            logger.error(f"Symbol {symbol_name} not found in codebase")
            return None

        # Add root node
        self._add_node(
            symbol,
            name=symbol_name,
            color=self.config.color_palette.get("Root"),
            is_root=True,
        )

        # Recursively add usages (reverse dependencies)
        visited = {symbol}

        def add_usages(sym, depth=0):
            if depth >= current_max_depth:
                return

            # Skip if no usages attribute
            if not hasattr(sym, "usages"):
                return

            for usage in sym.usages:
                # Skip if no usage symbol
                if not hasattr(usage, "usage_symbol"):
                    continue

                usage_symbol = usage.usage_symbol

                # Skip external modules if configured
                if (
                    self.config.ignore_external
                    and hasattr(usage_symbol, "is_external")
                    and usage_symbol.is_external
                ):
                    continue

                # Add node for usage
                self._add_node(
                    usage_symbol,
                    name=usage_symbol.name
                    if hasattr(usage_symbol, "name")
                    else str(usage_symbol),
                    color=self.config.color_palette.get(
                        usage_symbol.__class__.__name__, "#BBBBBB"
                    ),
                    file_path=usage_symbol.file.path
                    if hasattr(usage_symbol, "file")
                    and hasattr(usage_symbol.file, "path")
                    else None,
                )

                # Add edge for usage relationship
                self._add_edge(sym, usage_symbol, type="used_by")

                # Recursively process usage
                if usage_symbol not in visited:
                    visited.add(usage_symbol)
                    add_usages(usage_symbol, depth + 1)

        # Start from the root symbol
        add_usages(symbol)

        # Generate visualization data
        if self.config.output_format == OutputFormat.JSON:
            data = self._convert_graph_to_json()
            return self._save_visualization(
                VisualizationType.BLAST_RADIUS, symbol_name, data
            )
        else:
            fig = self._plot_graph()
            return self._save_visualization(
                VisualizationType.BLAST_RADIUS, symbol_name, fig
            )

    def visualize_class_methods(self, class_name: str):
        """
        Generate a class methods visualization.

        Args:
            class_name: Name of the class to visualize

        Returns:
            Visualization data or path to saved file
        """
        self.current_visualization_type = VisualizationType.CLASS_METHODS
        self.current_entity_name = class_name

        # Initialize graph
        self._initialize_graph()

        # Find the class in the codebase
        class_obj = None
        for cls in self.codebase.classes:
            if cls.name == class_name:
                class_obj = cls
                break

        if not class_obj:
            logger.error(f"Class {class_name} not found in codebase")
            return None

        # Add class node
        self._add_node(
            class_obj,
            name=class_name,
            color=self.config.color_palette.get("Class"),
            is_root=True,
        )

        # Skip if no methods attribute
        if not hasattr(class_obj, "methods"):
            logger.error(f"Class {class_name} has no methods attribute")
            return None

        # Add method nodes and connections
        method_ids = {}
        for method in class_obj.methods:
            method_name = f"{class_name}.{method.name}"

            # Add method node
            method_id = self._add_node(
                method,
                name=method_name,
                color=self.config.color_palette.get("Function"),
                file_path=method.file.path
                if hasattr(method, "file") and hasattr(method.file, "path")
                else None,
            )

            method_ids[method.name] = method_id

            # Add edge from class to method
            self._add_edge(class_obj, method, type="contains")

        # Add call relationships between methods
        for method in class_obj.methods:
            # Skip if no function calls attribute
            if not hasattr(method, "function_calls"):
                continue

            for call in method.function_calls:
                # Get the called function
                called_func = call.function_definition
                if not called_func:
                    continue

                # Only add edges between methods of this class
                if (
                    hasattr(called_func, "is_method")
                    and called_func.is_method
                    and hasattr(called_func, "parent_class")
                    and called_func.parent_class == class_obj
                ):
                    self._add_edge(
                        method,
                        called_func,
                        type="calls",
                        line=call.line if hasattr(call, "line") else None,
                    )

        # Generate visualization data
        if self.config.output_format == OutputFormat.JSON:
            data = self._convert_graph_to_json()
            return self._save_visualization(
                VisualizationType.CLASS_METHODS, class_name, data
            )
        else:
            fig = self._plot_graph()
            return self._save_visualization(
                VisualizationType.CLASS_METHODS, class_name, fig
            )

    def visualize_module_dependencies(self, module_path: str):
        """
        Generate a module dependencies visualization.

        Args:
            module_path: Path to the module to visualize

        Returns:
            Visualization data or path to saved file
        """
        self.current_visualization_type = VisualizationType.MODULE_DEPENDENCIES
        self.current_entity_name = module_path

        # Initialize graph
        self._initialize_graph()

        # Get all files in the module
        module_files = []
        for file in self.codebase.files:
            if hasattr(file, "path") and str(file.path).startswith(module_path):
                module_files.append(file)

        if not module_files:
            logger.error(f"No files found in module {module_path}")
            return None

        # Add file nodes
        module_node_ids = {}
        for file in module_files:
            file_name = str(file.path).split("/")[-1]
            file_module = "/".join(str(file.path).split("/")[:-1])

            # Add file node
            file_id = self._add_node(
                file,
                name=file_name,
                module=file_module,
                color=self.config.color_palette.get("File"),
                file_path=str(file.path),
            )

            module_node_ids[str(file.path)] = file_id

        # Add import relationships
        for file in module_files:
            # Skip if no imports attribute
            if not hasattr(file, "imports"):
                continue

            for imp in file.imports:
                imported_file = None

                # Try to get imported file
                if hasattr(imp, "resolved_file"):
                    imported_file = imp.resolved_file
                elif hasattr(imp, "resolved_symbol") and hasattr(
                    imp.resolved_symbol, "file"
                ):
                    imported_file = imp.resolved_symbol.file

                if not imported_file:
                    continue

                # Skip external modules if configured
                if (
                    self.config.ignore_external
                    and hasattr(imported_file, "is_external")
                    and imported_file.is_external
                ):
                    continue

                # Add node for imported file if not already added
                imported_path = (
                    str(imported_file.path) if hasattr(imported_file, "path") else ""
                )

                if imported_path not in module_node_ids:
                    imported_name = imported_path.split("/")[-1]
                    imported_module = "/".join(imported_path.split("/")[:-1])

                    imported_id = self._add_node(
                        imported_file,
                        name=imported_name,
                        module=imported_module,
                        color=self.config.color_palette.get(
                            "External"
                            if imported_path.startswith(module_path)
                            else "File"
                        ),
                        file_path=imported_path,
                    )

                    module_node_ids[imported_path] = imported_id

                # Add edge for import relationship
                self._add_edge(
                    file,
                    imported_file,
                    type="imports",
                    import_name=imp.name if hasattr(imp, "name") else "",
                )

        # Generate visualization data
        if self.config.output_format == OutputFormat.JSON:
            data = self._convert_graph_to_json()
            return self._save_visualization(
                VisualizationType.MODULE_DEPENDENCIES, module_path, data
            )
        else:
            fig = self._plot_graph()
            return self._save_visualization(
                VisualizationType.MODULE_DEPENDENCIES, module_path, fig
            )

    def visualize_dead_code(self, path_filter: str | None = None):
        """
        Generate a visualization of dead (unused) code in the codebase.

        Args:
            path_filter: Optional path to filter files

        Returns:
            Visualization data or path to saved file
        """
        self.current_visualization_type = VisualizationType.DEAD_CODE
        self.current_entity_name = path_filter or "codebase"

        # Initialize graph
        self._initialize_graph()

        # Initialize analyzer if needed
        if not self.analyzer:
            logger.info("Initializing analyzer for dead code detection")
            self.analyzer = CodebaseAnalyzer(
                codebase=self.codebase,
                repo_path=self.context.base_path
                if hasattr(self.context, "base_path")
                else None,
            )

        # Perform analysis if not already done
        if not hasattr(self.analyzer, "results") or not self.analyzer.results:
            logger.info("Running code analysis")
            self.analyzer.analyze(AnalysisType.CODEBASE)

        # Extract dead code information from analysis results
        if not hasattr(self.analyzer, "results"):
            logger.error("Analysis results not available")
            return None

        dead_code = {}
        if (
            "static_analysis" in self.analyzer.results
            and "dead_code" in self.analyzer.results["static_analysis"]
        ):
            dead_code = self.analyzer.results["static_analysis"]["dead_code"]

        if not dead_code:
            logger.warning("No dead code detected in analysis results")
            return None

        # Create file nodes for containing dead code
        file_nodes = {}

        # Process unused functions
        if "unused_functions" in dead_code:
            for unused_func in dead_code["unused_functions"]:
                file_path = unused_func.get("file", "")

                # Skip if path filter is specified and doesn't match
                if path_filter and not file_path.startswith(path_filter):
                    continue

                # Add file node if not already added
                if file_path not in file_nodes:
                    # Find file in codebase
                    file_obj = None
                    for file in self.codebase.files:
                        if hasattr(file, "path") and str(file.path) == file_path:
                            file_obj = file
                            break

                    if file_obj:
                        file_name = file_path.split("/")[-1]
                        self._add_node(
                            file_obj,
                            name=file_name,
                            color=self.config.color_palette.get("File"),
                            file_path=file_path,
                        )

                        file_nodes[file_path] = file_obj

                # Add unused function node
                func_name = unused_func.get("name", "")
                func_line = unused_func.get("line", None)

                # Create a placeholder for the function (we don't have the actual object)
                func_obj = {
                    "name": func_name,
                    "file_path": file_path,
                    "line": func_line,
                    "type": "Function",
                }

                self._add_node(
                    func_obj,
                    name=func_name,
                    color=self.config.color_palette.get("Dead"),
                    file_path=file_path,
                    line=func_line,
                    is_dead=True,
                )

                # Add edge from file to function
                if file_path in file_nodes:
                    self._add_edge(
                        file_nodes[file_path], func_obj, type="contains_dead"
                    )

        # Process unused variables
        if "unused_variables" in dead_code:
            for unused_var in dead_code["unused_variables"]:
                file_path = unused_var.get("file", "")

                # Skip if path filter is specified and doesn't match
                if path_filter and not file_path.startswith(path_filter):
                    continue

                # Add file node if not already added
                if file_path not in file_nodes:
                    # Find file in codebase
                    file_obj = None
                    for file in self.codebase.files:
                        if hasattr(file, "path") and str(file.path) == file_path:
                            file_obj = file
                            break

                    if file_obj:
                        file_name = file_path.split("/")[-1]
                        self._add_node(
                            file_obj,
                            name=file_name,
                            color=self.config.color_palette.get("File"),
                            file_path=file_path,
                        )

                        file_nodes[file_path] = file_obj

                # Add unused variable node
                var_name = unused_var.get("name", "")
                var_line = unused_var.get("line", None)

                # Create a placeholder for the variable
                var_obj = {
                    "name": var_name,
                    "file_path": file_path,
                    "line": var_line,
                    "type": "Variable",
                }

                self._add_node(
                    var_obj,
                    name=var_name,
                    color=self.config.color_palette.get("Dead"),
                    file_path=file_path,
                    line=var_line,
                    is_dead=True,
                )

                # Add edge from file to variable
                if file_path in file_nodes:
                    self._add_edge(file_nodes[file_path], var_obj, type="contains_dead")

        # Generate visualization data
        if self.config.output_format == OutputFormat.JSON:
            data = self._convert_graph_to_json()
            return self._save_visualization(
                VisualizationType.DEAD_CODE, self.current_entity_name, data
            )
        else:
            fig = self._plot_graph()
            return self._save_visualization(
                VisualizationType.DEAD_CODE, self.current_entity_name, fig
            )

    def visualize_cyclomatic_complexity(self, path_filter: str | None = None):
        """
        Generate a heatmap visualization of cyclomatic complexity.

        Args:
            path_filter: Optional path to filter files

        Returns:
            Visualization data or path to saved file
        """
        self.current_visualization_type = VisualizationType.CYCLOMATIC_COMPLEXITY
        self.current_entity_name = path_filter or "codebase"

        # Initialize analyzer if needed
        if not self.analyzer:
            logger.info("Initializing analyzer for complexity analysis")
            self.analyzer = CodebaseAnalyzer(
                codebase=self.codebase,
                repo_path=self.context.base_path
                if hasattr(self.context, "base_path")
                else None,
            )

        # Perform analysis if not already done
        if not hasattr(self.analyzer, "results") or not self.analyzer.results:
            logger.info("Running code analysis")
            self.analyzer.analyze(AnalysisType.CODEBASE)

        # Extract complexity information from analysis results
        if not hasattr(self.analyzer, "results"):
            logger.error("Analysis results not available")
            return None

        complexity_data = {}
        if (
            "static_analysis" in self.analyzer.results
            and "code_complexity" in self.analyzer.results["static_analysis"]
        ):
            complexity_data = self.analyzer.results["static_analysis"][
                "code_complexity"
            ]

        if not complexity_data:
            logger.warning("No complexity data found in analysis results")
            return None

        # Extract function complexities
        functions = []
        if "function_complexity" in complexity_data:
            for func_data in complexity_data["function_complexity"]:
                # Skip if path filter is specified and doesn't match
                if path_filter and not func_data.get("file", "").startswith(
                    path_filter
                ):
                    continue

                functions.append({
                    "name": func_data.get("name", ""),
                    "file": func_data.get("file", ""),
                    "complexity": func_data.get("complexity", 1),
                    "line": func_data.get("line", None),
                })

        # Sort functions by complexity (descending)
        functions.sort(key=lambda x: x.get("complexity", 0), reverse=True)

        # Generate heatmap visualization
        plt.figure(figsize=(12, 10))

        # Extract data for heatmap
        func_names = [
            f"{func['name']} ({func['file'].split('/')[-1]})" for func in functions[:30]
        ]
        complexities = [func.get("complexity", 0) for func in functions[:30]]

        # Create horizontal bar chart
        bars = plt.barh(func_names, complexities)

        # Color bars by complexity
        norm = plt.Normalize(1, max(10, max(complexities)))
        cmap = plt.cm.get_cmap("YlOrRd")

        for i, bar in enumerate(bars):
            complexity = complexities[i]
            bar.set_color(cmap(norm(complexity)))

        # Add labels and title
        plt.xlabel("Cyclomatic Complexity")
        plt.title("Top Functions by Cyclomatic Complexity")
        plt.grid(axis="x", linestyle="--", alpha=0.6)

        # Add colorbar
        plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), label="Complexity")

        # Save and return visualization
        return self._save_visualization(
            VisualizationType.CYCLOMATIC_COMPLEXITY, self.current_entity_name, plt.gcf()
        )

    def visualize_issues_heatmap(
        self,
        severity: IssueSeverity | None = None,
        path_filter: str | None = None,
    ):
        """
        Generate a heatmap visualization of issues in the codebase.

        Args:
            severity: Optional severity level to filter issues
            path_filter: Optional path to filter files

        Returns:
            Visualization data or path to saved file
        """
        self.current_visualization_type = VisualizationType.ISSUES_HEATMAP
        self.current_entity_name = f"{severity.value if severity else 'all'}_issues"

        # Initialize analyzer if needed
        if not self.analyzer:
            logger.info("Initializing analyzer for issues analysis")
            self.analyzer = CodebaseAnalyzer(
                codebase=self.codebase,
                repo_path=self.context.base_path
                if hasattr(self.context, "base_path")
                else None,
            )

        # Perform analysis if not already done
        if not hasattr(self.analyzer, "results") or not self.analyzer.results:
            logger.info("Running code analysis")
            self.analyzer.analyze(AnalysisType.CODEBASE)

        # Extract issues from analysis results
        if (
            not hasattr(self.analyzer, "results")
            or "issues" not in self.analyzer.results
        ):
            logger.error("Issues not available in analysis results")
            return None

        issues = self.analyzer.results["issues"]

        # Filter issues by severity if specified
        if severity:
            issues = [issue for issue in issues if issue.get("severity") == severity]

        # Filter issues by path if specified
        if path_filter:
            issues = [
                issue
                for issue in issues
                if issue.get("file", "").startswith(path_filter)
            ]

        if not issues:
            logger.warning("No issues found matching the criteria")
            return None

        # Group issues by file
        file_issues = {}
        for issue in issues:
            file_path = issue.get("file", "")
            if file_path not in file_issues:
                file_issues[file_path] = []

            file_issues[file_path].append(issue)

        # Generate heatmap visualization
        plt.figure(figsize=(12, 10))

        # Extract data for heatmap
        files = list(file_issues.keys())
        file_names = [file_path.split("/")[-1] for file_path in files]
        issue_counts = [len(file_issues[file_path]) for file_path in files]

        # Sort by issue count
        sorted_data = sorted(
            zip(file_names, issue_counts, files, strict=False),
            key=lambda x: x[1],
            reverse=True,
        )
        file_names, issue_counts, files = zip(*sorted_data, strict=False)

        # Create horizontal bar chart
        bars = plt.barh(file_names[:20], issue_counts[:20])

        # Color bars by issue count
        norm = plt.Normalize(1, max(5, max(issue_counts[:20])))
        cmap = plt.cm.get_cmap("OrRd")

        for i, bar in enumerate(bars):
            count = issue_counts[i]
            bar.set_color(cmap(norm(count)))

        # Add labels and title
        plt.xlabel("Number of Issues")
        severity_text = f" ({severity.value})" if severity else ""
        plt.title(f"Files with the Most Issues{severity_text}")
        plt.grid(axis="x", linestyle="--", alpha=0.6)

        # Add colorbar
        plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), label="Issue Count")

        # Save and return visualization
        return self._save_visualization(
            VisualizationType.ISSUES_HEATMAP, self.current_entity_name, plt.gcf()
        )

    def visualize_pr_comparison(self):
        """
        Generate a visualization comparing base branch with PR.

        Returns:
            Visualization data or path to saved file
        """
        self.current_visualization_type = VisualizationType.PR_COMPARISON

        # Check if analyzer has PR data
        if (
            not self.analyzer
            or not self.analyzer.pr_codebase
            or not self.analyzer.base_codebase
        ):
            logger.error("PR comparison requires analyzer with PR data")
            return None

        self.current_entity_name = (
            f"pr_{self.analyzer.pr_number}"
            if self.analyzer.pr_number
            else "pr_comparison"
        )

        # Perform comparison analysis if not already done
        if not hasattr(self.analyzer, "results") or not self.analyzer.results:
            logger.info("Running PR comparison analysis")
            self.analyzer.analyze(AnalysisType.COMPARISON)

        # Extract comparison data from analysis results
        if (
            not hasattr(self.analyzer, "results")
            or "comparison" not in self.analyzer.results
        ):
            logger.error("Comparison data not available in analysis results")
            return None

        comparison = self.analyzer.results["comparison"]

        # Initialize graph
        self._initialize_graph()

        # Process symbol comparison data
        if "symbol_comparison" in comparison:
            for symbol_data in comparison["symbol_comparison"]:
                symbol_name = symbol_data.get("name", "")
                in_base = symbol_data.get("in_base", False)
                in_pr = symbol_data.get("in_pr", False)

                # Create a placeholder for the symbol
                symbol_obj = {
                    "name": symbol_name,
                    "in_base": in_base,
                    "in_pr": in_pr,
                    "type": "Symbol",
                }

                # Determine node color based on presence in base and PR
                if in_base and in_pr:
                    color = "#A5D6A7"  # Light green (modified)
                elif in_base:
                    color = "#EF9A9A"  # Light red (removed)
                else:
                    color = "#90CAF9"  # Light blue (added)

                # Add node for symbol
                self._add_node(
                    symbol_obj,
                    name=symbol_name,
                    color=color,
                    in_base=in_base,
                    in_pr=in_pr,
                )

                # Process parameter changes if available
                if "parameter_changes" in symbol_data:
                    param_changes = symbol_data["parameter_changes"]

                    # Process removed parameters
                    for param in param_changes.get("removed", []):
                        param_obj = {
                            "name": param,
                            "change_type": "removed",
                            "type": "Parameter",
                        }

                        self._add_node(
                            param_obj,
                            name=param,
                            color="#EF9A9A",  # Light red (removed)
                            change_type="removed",
                        )

                        self._add_edge(symbol_obj, param_obj, type="removed_parameter")

                    # Process added parameters
                    for param in param_changes.get("added", []):
                        param_obj = {
                            "name": param,
                            "change_type": "added",
                            "type": "Parameter",
                        }

                        self._add_node(
                            param_obj,
                            name=param,
                            color="#90CAF9",  # Light blue (added)
                            change_type="added",
                        )

                        self._add_edge(symbol_obj, param_obj, type="added_parameter")

                # Process return type changes if available
                if "return_type_change" in symbol_data:
                    return_type_change = symbol_data["return_type_change"]
                    old_type = return_type_change.get("old", "None")
                    new_type = return_type_change.get("new", "None")

                    return_obj = {
                        "name": f"{old_type} -> {new_type}",
                        "old_type": old_type,
                        "new_type": new_type,
                        "type": "ReturnType",
                    }

                    self._add_node(
                        return_obj,
                        name=f"{old_type} -> {new_type}",
                        color="#FFD54F",  # Amber (changed)
                        old_type=old_type,
                        new_type=new_type,
                    )

                    self._add_edge(symbol_obj, return_obj, type="return_type_change")

                # Process call site issues if available
                if "call_site_issues" in symbol_data:
                    for issue in symbol_data["call_site_issues"]:
                        issue_file = issue.get("file", "")
                        issue_line = issue.get("line", None)
                        issue_text = issue.get("issue", "")

                        # Create a placeholder for the issue
                        issue_obj = {
                            "name": issue_text,
                            "file": issue_file,
                            "line": issue_line,
                            "type": "Issue",
                        }

                        self._add_node(
                            issue_obj,
                            name=f"{issue_file.split('/')[-1]}:{issue_line}",
                            color="#EF5350",  # Red (error)
                            file_path=issue_file,
                            line=issue_line,
                            issue_text=issue_text,
                        )

                        self._add_edge(symbol_obj, issue_obj, type="call_site_issue")

        # Generate visualization data
        if self.config.output_format == OutputFormat.JSON:
            data = self._convert_graph_to_json()
            return self._save_visualization(
                VisualizationType.PR_COMPARISON, self.current_entity_name, data
            )
        else:
            fig = self._plot_graph()
            return self._save_visualization(
                VisualizationType.PR_COMPARISON, self.current_entity_name, fig
            )


# Command-line interface
def main():
    """
    Command-line interface for the codebase visualizer.

    This function parses command-line arguments and generates visualizations
    based on the specified parameters.
    """
    parser = argparse.ArgumentParser(
        description="Generate visualizations of codebase structure and analysis."
    )

    # Repository options
    repo_group = parser.add_argument_group("Repository Options")
    repo_group.add_argument("--repo-url", help="URL of the repository to analyze")
    repo_group.add_argument(
        "--repo-path", help="Local path to the repository to analyze"
    )
    repo_group.add_argument("--language", help="Programming language of the codebase")

    # Visualization options
    viz_group = parser.add_argument_group("Visualization Options")
    viz_group.add_argument(
        "--type",
        choices=[t.value for t in VisualizationType],
        required=True,
        help="Type of visualization to generate",
    )
    viz_group.add_argument(
        "--entity", help="Name of the entity to visualize (function, class, file, etc.)"
    )
    viz_group.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="Maximum depth for recursive visualizations",
    )
    viz_group.add_argument(
        "--ignore-external", action="store_true", help="Ignore external dependencies"
    )
    viz_group.add_argument(
        "--severity",
        choices=[s.value for s in IssueSeverity],
        help="Filter issues by severity",
    )
    viz_group.add_argument("--path-filter", help="Filter by file path")

    # PR options
    pr_group = parser.add_argument_group("PR Options")
    pr_group.add_argument("--pr-number", type=int, help="PR number to analyze")
    pr_group.add_argument(
        "--base-branch", default="main", help="Base branch for comparison"
    )

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--output-format",
        choices=[f.value for f in OutputFormat],
        default="json",
        help="Output format for the visualization",
    )
    output_group.add_argument(
        "--output-directory", help="Directory to save visualizations"
    )
    output_group.add_argument(
        "--layout",
        choices=["spring", "kamada_kawai", "spectral"],
        default="spring",
        help="Layout algorithm for graph visualization",
    )

    args = parser.parse_args()

    # Create visualizer configuration
    config = VisualizationConfig(
        max_depth=args.max_depth,
        ignore_external=args.ignore_external,
        output_format=OutputFormat(args.output_format),
        output_directory=args.output_directory,
        layout_algorithm=args.layout,
    )

    # Create codebase analyzer if needed for PR comparison
    analyzer = None
    if args.type == VisualizationType.PR_COMPARISON.value or args.pr_number:
        analyzer = CodebaseAnalyzer(
            repo_url=args.repo_url,
            repo_path=args.repo_path,
            base_branch=args.base_branch,
            pr_number=args.pr_number,
            language=args.language,
        )

    # Create visualizer
    visualizer = CodebaseVisualizer(analyzer=analyzer, config=config)

    # Generate visualization based on type
    viz_type = VisualizationType(args.type)
    result = None

    if viz_type == VisualizationType.CALL_GRAPH:
        if not args.entity:
            logger.error("Entity name required for call graph visualization")
            sys.exit(1)

        result = visualizer.visualize_call_graph(args.entity)

    elif viz_type == VisualizationType.DEPENDENCY_GRAPH:
        if not args.entity:
            logger.error("Entity name required for dependency graph visualization")
            sys.exit(1)

        result = visualizer.visualize_dependency_graph(args.entity)

    elif viz_type == VisualizationType.BLAST_RADIUS:
        if not args.entity:
            logger.error("Entity name required for blast radius visualization")
            sys.exit(1)

        result = visualizer.visualize_blast_radius(args.entity)

    elif viz_type == VisualizationType.CLASS_METHODS:
        if not args.entity:
            logger.error("Class name required for class methods visualization")
            sys.exit(1)

        result = visualizer.visualize_class_methods(args.entity)

    elif viz_type == VisualizationType.MODULE_DEPENDENCIES:
        if not args.entity:
            logger.error("Module path required for module dependencies visualization")
            sys.exit(1)

        result = visualizer.visualize_module_dependencies(args.entity)

    elif viz_type == VisualizationType.DEAD_CODE:
        result = visualizer.visualize_dead_code(args.path_filter)

    elif viz_type == VisualizationType.CYCLOMATIC_COMPLEXITY:
        result = visualizer.visualize_cyclomatic_complexity(args.path_filter)

    elif viz_type == VisualizationType.ISSUES_HEATMAP:
        severity = IssueSeverity(args.severity) if args.severity else None
        result = visualizer.visualize_issues_heatmap(severity, args.path_filter)

    elif viz_type == VisualizationType.PR_COMPARISON:
        if not args.pr_number:
            logger.error("PR number required for PR comparison visualization")
            sys.exit(1)

        result = visualizer.visualize_pr_comparison()

    # Output result
    if result:
        logger.info(f"Visualization completed: {result}")
    else:
        logger.error("Failed to generate visualization")
        sys.exit(1)


if __name__ == "__main__":
    main()
