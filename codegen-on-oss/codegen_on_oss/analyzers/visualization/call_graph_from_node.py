#!/usr/bin/env python3
"""
Call Graph From Node Visualization

This module provides visualization capabilities for generating a call graph
starting from a specific function or method.
"""

import logging
from typing import Any

import networkx as nx

from ..context.class_definition import Class
from ..context.codebase import CodebaseType
from ..context.detached_symbols.function_call import FunctionCall
from ..context.external_module import ExternalModule
from ..context.function import Function
from ..context.interfaces.callable import Callable
from .visualizer import BaseVisualizer, OutputFormat, VisualizationType

logger = logging.getLogger(__name__)


class CallGraphFromNode(BaseVisualizer):
    """
    Visualizer for generating a call graph starting from a specific function.

    This class creates a directed call graph for a given function. Starting from the
    specified function, it recursively iterates through its function calls and the
    functions called by them, building a graph of the call paths to a maximum depth.
    """

    def __init__(self, codebase: CodebaseType | None = None, **kwargs):
        """
        Initialize the CallGraphFromNode visualizer.

        Args:
            codebase: Codebase instance to visualize
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.codebase = codebase

    def visualize(  # noqa: C901
        self,
        function_name: str,
        max_depth: int = 5,
        graph_external_modules: bool = False,
    ):
        """
        Generate a call graph visualization starting from a specific function.

        Args:
            function_name: Name of the function to start the call graph from
            max_depth: Maximum depth of the call graph
            graph_external_modules: Whether to include external module calls in the graph

        Returns:
            Visualization data or path to saved file
        """
        # Create a directed graph
        G = nx.DiGraph()

        # Find the function in the codebase
        function_to_trace = None
        for func in self.codebase.functions:
            if func.name == function_name:
                function_to_trace = func
                break

        if not function_to_trace:
            logger.error(f"Function {function_name} not found in codebase")
            return None

        # Add the starting node
        G.add_node(function_to_trace, color="yellow")

        # Recursive function to create the call graph
        def create_downstream_call_trace(
            parent: FunctionCall | Function | None = None, depth: int = 0
        ):
            """
            Creates call graph for parent function.

            This function recurses through the call graph of a function and creates a visualization.

            Args:
                parent: The function for which a call graph will be created
                depth: The current depth of the recursive stack
            """
            # If the maximum recursive depth has been exceeded, return
            if max_depth <= depth:
                return

            if isinstance(parent, FunctionCall):
                src_call, src_func = parent, parent.function_definition
            else:
                src_call, src_func = parent, parent

            # Iterate over all call paths of the symbol
            for call in src_func.function_calls:
                # The symbol being called
                func = call.function_definition

                # Ignore direct recursive calls
                if func.name == src_func.name:
                    continue

                # If the function being called is not from an external module
                if not isinstance(func, ExternalModule):
                    # Add `call` to the graph and an edge from `src_call` to `call`
                    G.add_node(call)
                    G.add_edge(src_call, call)

                    # Recursive call to function call
                    create_downstream_call_trace(call, depth + 1)
                elif graph_external_modules:
                    # Add `call` to the graph and an edge from `src_call` to `call`
                    G.add_node(call)
                    G.add_edge(src_call, call)

        # Start the recursive traversal
        create_downstream_call_trace(function_to_trace)

        # Set the graph for visualization
        self.graph = G

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


class CallGraphFilter(BaseVisualizer):
    """
    Visualizer for generating a filtered call graph.

    This class creates a call graph that filters nodes based on specific criteria,
    such as method names or file paths.
    """

    def __init__(self, codebase: CodebaseType | None = None, **kwargs):
        """
        Initialize the CallGraphFilter visualizer.

        Args:
            codebase: Codebase instance to visualize
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.codebase = codebase

    def visualize(  # noqa: C901
        self,
        class_name: str,
        method_filters: list[str] | None = None,
        skip_test_files: bool = True,
        max_depth: int = 5,
    ):
        """
        Generate a filtered call graph visualization.

        Args:
            class_name: Name of the class to visualize methods from
            method_filters: List of method names to include (e.g., ['get', 'post', 'patch', 'delete'])
            skip_test_files: Whether to skip test files
            max_depth: Maximum depth of the call graph

        Returns:
            Visualization data or path to saved file
        """
        # Create a directed graph
        G = nx.DiGraph()

        # Find the class in the codebase
        cls = None
        for c in self.codebase.classes:
            if c.name == class_name:
                cls = c
                break

        if not cls:
            logger.error(f"Class {class_name} not found in codebase")
            return None

        # Find a function that uses the class to start tracing from
        func_to_trace = None
        for func in self.codebase.functions:
            if skip_test_files and "test" in func.file.filepath:
                continue

            for call in func.function_calls:
                if (
                    hasattr(call.function_definition, "parent_class")
                    and call.function_definition.parent_class == cls
                ):
                    func_to_trace = func
                    break

            if func_to_trace:
                break

        if not func_to_trace:
            logger.error(f"No function found that uses class {class_name}")
            return None

        # Add the main function as a node
        G.add_node(func_to_trace, color="red")

        # Define a recursive function to traverse function calls
        def create_filtered_downstream_call_trace(
            parent: FunctionCall | Function, current_depth, max_depth
        ):
            if current_depth > max_depth:
                return

            # If parent is of type Function
            if isinstance(parent, Function):
                # Set both src_call, src_func to parent
                src_call, src_func = parent, parent
            else:
                # Get the function definition of parent
                src_call, src_func = parent, parent.function_definition

            # Iterate over all call paths of the symbol
            for call in src_func.function_calls:
                # The symbol being called
                func = call.function_definition

                # Skip class declarations if configured
                if isinstance(func, Class):
                    continue

                # If the function being called is not from an external module and is not defined in a test file
                if not isinstance(func, ExternalModule) and not (
                    skip_test_files and func.file.filepath.startswith("test")
                ):
                    # Add `call` to the graph and an edge from `src_call` to `call`
                    metadata: dict[str, Any] = {}
                    if (
                        isinstance(func, Function)
                        and func.is_method
                        and func.parent_class == cls
                    ):
                        # Only include methods that match the filter
                        if method_filters and func.name not in method_filters:
                            continue

                        name = f"{func.parent_class.name}.{func.name}"
                        metadata = {"color": "yellow", "name": name}

                    G.add_node(call, **metadata)
                    G.add_edge(
                        src_call, call, symbol=cls
                    )  # Add edge from current to successor

                    # Recursively add successors of the current symbol
                    create_filtered_downstream_call_trace(
                        call, current_depth + 1, max_depth
                    )

        # Start the recursive traversal
        create_filtered_downstream_call_trace(func_to_trace, 1, max_depth)

        # Set the graph for visualization
        self.graph = G

        # Generate visualization data
        if self.config.output_format == OutputFormat.JSON:
            data = self._convert_graph_to_json()
            return self._save_visualization(
                VisualizationType.CALL_GRAPH, f"{class_name}_filtered", data
            )
        else:
            fig = self._plot_graph()
            return self._save_visualization(
                VisualizationType.CALL_GRAPH, f"{class_name}_filtered", fig
            )


class CallPathsBetweenNodes(BaseVisualizer):
    """
    Visualizer for generating paths between two functions in the call graph.

    This class creates a visualization of all simple paths between a start function
    and an end function in the call graph.
    """

    def __init__(self, codebase: CodebaseType | None = None, **kwargs):
        """
        Initialize the CallPathsBetweenNodes visualizer.

        Args:
            codebase: Codebase instance to visualize
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.codebase = codebase

    def visualize(self, start_func_name: str, end_func_name: str, max_depth: int = 5):  # noqa: C901
        """
        Generate a visualization of call paths between two functions.

        Args:
            start_func_name: Name of the starting function
            end_func_name: Name of the ending function
            max_depth: Maximum depth for path exploration

        Returns:
            Visualization data or path to saved file
        """
        # Create a directed graph
        G = nx.DiGraph()

        # Find the start and end functions in the codebase
        start_func = None
        end_func = None

        for func in self.codebase.functions:
            if func.name == start_func_name:
                start_func = func
            elif func.name == end_func_name:
                end_func = func

            if start_func and end_func:
                break

        if not start_func:
            logger.error(f"Start function {start_func_name} not found in codebase")
            return None

        if not end_func:
            logger.error(f"End function {end_func_name} not found in codebase")
            return None

        # Set starting node as blue
        G.add_node(start_func, color="blue")
        # Set ending node as red
        G.add_node(end_func, color="red")

        # Define a recursive function to traverse function calls
        def create_downstream_call_trace(
            parent: FunctionCall | Function, end: Callable, current_depth, max_depth
        ):
            if current_depth > max_depth:
                return

            # If parent is of type Function
            if isinstance(parent, Function):
                # Set both src_call, src_func to parent
                src_call, src_func = parent, parent
            else:
                # Get the function definition of parent
                src_call, src_func = parent, parent.function_definition

            # Iterate over all call paths of the symbol
            for call in src_func.function_calls:
                # The symbol being called
                func = call.function_definition

                # Ignore direct recursive calls
                if func.name == src_func.name:
                    continue

                # If the function being called is not from an external module
                if not isinstance(func, ExternalModule):
                    # Add `call` to the graph and an edge from `src_call` to `call`
                    G.add_node(call)
                    G.add_edge(src_call, call)

                    if func == end:
                        G.add_edge(call, end)
                        return

                    # Recursive call to function call
                    create_downstream_call_trace(
                        call, end, current_depth + 1, max_depth
                    )

        # Start the recursive traversal
        create_downstream_call_trace(start_func, end_func, 1, max_depth)

        # Find all the simple paths between start and end
        try:
            all_paths = list(nx.all_simple_paths(G, source=start_func, target=end_func))

            # Collect all nodes that are part of these paths
            nodes_in_paths = set()
            for path in all_paths:
                nodes_in_paths.update(path)

            # Create a new subgraph with only the nodes in the paths
            G = G.subgraph(nodes_in_paths)
        except nx.NetworkXNoPath:
            logger.warning(
                f"No path found between {start_func_name} and {end_func_name}"
            )

        # Set the graph for visualization
        self.graph = G

        # Generate visualization data
        if self.config.output_format == OutputFormat.JSON:
            data = self._convert_graph_to_json()
            return self._save_visualization(
                VisualizationType.CALL_GRAPH,
                f"{start_func_name}_to_{end_func_name}",
                data,
            )
        else:
            fig = self._plot_graph()
            return self._save_visualization(
                VisualizationType.CALL_GRAPH,
                f"{start_func_name}_to_{end_func_name}",
                fig,
            )
