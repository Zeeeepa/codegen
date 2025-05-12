#!/usr/bin/env python3
"""
Core Visualization Module

This module provides the base visualization capabilities for codebases and PR analyses.
It defines the core classes and interfaces for generating visual representations
of code structure, dependencies, and issues.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

try:
    import matplotlib.pyplot as plt
    import networkx as nx
    from matplotlib.colors import LinearSegmentedColormap
except ImportError:
    logging.warning(
        "Visualization dependencies not found. Please install them with: pip install networkx matplotlib"
    )


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


class BaseVisualizer:
    """
    Base visualizer providing common functionality for different visualization types.

    This class implements the core operations needed for visualization, including
    graph creation, node and edge management, and output generation.
    """

    def __init__(self, config: VisualizationConfig | None = None):
        """
        Initialize the BaseVisualizer.

        Args:
            config: Visualization configuration options
        """
        self.config = config or VisualizationConfig()

        # Create visualization directory if specified
        if self.config.output_directory:
            os.makedirs(self.config.output_directory, exist_ok=True)

        # Initialize graph for visualization
        self.graph = nx.DiGraph()

        # Tracking current visualization
        self.current_visualization_type = None
        self.current_entity_name = None

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
        self.current_visualization_type = visualization_type
        self.current_entity_name = entity_name

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
                logging.exception(
                    "networkx.drawing.nx_agraph not available. Install pygraphviz for DOT format."
                )
                return None

        logging.info(f"Visualization saved to {filepath}")
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
