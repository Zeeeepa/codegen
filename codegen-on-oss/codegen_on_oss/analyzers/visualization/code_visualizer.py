#!/usr/bin/env python3
"""
Code Structure Visualizer

This module provides visualization capabilities for code structures such as
call graphs, dependency graphs, class methods, and blast radius.
"""

import logging

from .visualizer import BaseVisualizer, OutputFormat, VisualizationType

try:
    import matplotlib.pyplot as plt
    import networkx as nx
except ImportError:
    logging.warning(
        "Visualization dependencies not found. Please install them with: pip install networkx matplotlib"
    )

logger = logging.getLogger(__name__)


class CodeVisualizer(BaseVisualizer):
    """
    Visualizer for code structures such as call graphs and dependencies.

    This class provides methods to visualize relationships between code entities
    including functions, classes, and modules.
    """

    def __init__(self, codebase=None, context=None, **kwargs):
        """
        Initialize the CodeVisualizer.

        Args:
            codebase: Codebase instance to visualize
            context: Context providing graph representation
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.codebase = codebase
        self.context = context

        # Initialize codebase if needed
        if not self.codebase and not self.context and "analyzer" in kwargs:
            self.codebase = kwargs["analyzer"].base_codebase
            self.context = kwargs["analyzer"].base_context

    def visualize_call_graph(self, function_name: str, max_depth: int | None = None):
        """
        Generate a call graph visualization for a function.

        Args:
            function_name: Name of the function to visualize
            max_depth: Maximum depth of the call graph (overrides config)

        Returns:
            Visualization data or path to saved file
        """
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
                if called_func not in visited:
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

                if hasattr(dep, "__class__") and dep.__class__.__name__ == "Symbol":
                    dep_symbol = dep
                elif hasattr(dep, "resolved_symbol"):
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
