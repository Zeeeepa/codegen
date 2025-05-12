#!/usr/bin/env python3
"""
Dead Code Visualization

This module provides visualization capabilities for identifying and visualizing
dead code in a codebase, including unused functions, classes, and second-order
dead code (code that is only used by other dead code).
"""

import logging

import networkx as nx

from ..context.codebase import CodebaseType
from ..context.function import Function
from ..context.import_resolution import Import
from ..context.symbol import Symbol
from .visualizer import BaseVisualizer, OutputFormat, VisualizationType

logger = logging.getLogger(__name__)


class DeadCodeVisualizer(BaseVisualizer):
    """
    Visualizer for identifying and visualizing dead code in a codebase.

    This class identifies functions and classes that have no usages and are not in test
    files or decorated. These are considered 'dead code' and are added to a directed graph.
    The visualizer then explores the dependencies of these dead code functions, adding them
    to the graph as well. This process helps to identify not only directly unused code
    but also code that might only be used by other dead code (second-order dead code).
    """

    def __init__(self, codebase: CodebaseType | None = None, **kwargs):
        """
        Initialize the DeadCodeVisualizer.

        Args:
            codebase: Codebase instance to visualize
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.codebase = codebase

    def visualize(self, skip_test_files: bool = True, skip_decorated: bool = True):  # noqa: C901
        """
        Generate a visualization of dead code in the codebase.

        Args:
            skip_test_files: Whether to skip functions in test files
            skip_decorated: Whether to skip decorated functions

        Returns:
            Visualization data or path to saved file
        """
        # Create a directed graph to visualize dead and second-order dead code
        G = nx.DiGraph()

        # First, identify all dead code
        dead_code: list[Function] = []

        # Iterate through all functions in the codebase
        for function in self.codebase.functions:
            # Filter down functions
            if skip_test_files and "test" in function.file.filepath:
                continue

            if skip_decorated and function.decorators:
                continue

            # Check if the function has no usages
            if not function.symbol_usages:
                # Add the function to the dead code list
                dead_code.append(function)
                # Add the function to the graph as dead code
                G.add_node(function, color="red")

        # Now, find second-order dead code
        for symbol in dead_code:
            # Get all usages of the dead code symbol
            for dep in symbol.dependencies:
                if isinstance(dep, Import):
                    dep = dep.imported_symbol
                if isinstance(dep, Symbol) and not (
                    skip_test_files and "test" in dep.name
                ):
                    G.add_node(dep)
                    G.add_edge(symbol, dep, color="red")
                    for usage_symbol in dep.symbol_usages:
                        if isinstance(usage_symbol, Function) and not (
                            skip_test_files and "test" in usage_symbol.name
                        ):
                            G.add_edge(usage_symbol, dep)

        # Set the graph for visualization
        self.graph = G

        # Generate visualization data
        if self.config.output_format == OutputFormat.JSON:
            data = self._convert_graph_to_json()
            return self._save_visualization(
                VisualizationType.DEAD_CODE, "codebase_dead_code", data
            )
        else:
            fig = self._plot_graph()
            return self._save_visualization(
                VisualizationType.DEAD_CODE, "codebase_dead_code", fig
            )
