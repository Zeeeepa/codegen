import os
from typing import Any, Dict, List, Optional, Union

import plotly.graph_objects as go
from networkx import DiGraph, Graph

from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.sdk.core.function import Function
from codegen.sdk.core.interfaces.editable import Editable
from codegen.shared.logging.get_logger import get_logger
from codegen.visualizations.enums import CallGraphFilterType, GraphType
from codegen.visualizations.viz_utils import (
    apply_call_graph_filters,
    create_call_graph,
    create_interactive_call_graph,
    graph_to_json,
)

logger = get_logger(__name__)


class VisualizationManager:
    """Manager for code visualization features."""
    
    op: RepoOperator

    def __init__(
        self,
        op: RepoOperator,
    ) -> None:
        self.op = op

    @property
    def viz_path(self) -> str:
        """Get the path for visualization data."""
        return os.path.join(self.op.base_dir, "codegen-graphviz")

    @property
    def viz_file_path(self) -> str:
        """Get the file path for the graph JSON data."""
        return os.path.join(self.viz_path, "graph.json")

    def clear_graphviz_data(self) -> None:
        """Clear existing visualization data."""
        if self.op.folder_exists(self.viz_path):
            self.op.emptydir(self.viz_path)

    def write_graphviz_data(self, G: Graph | go.Figure, root: Editable | str | int | None = None) -> None:
        """Write graph data to a file for visualization.

        Args:
        ----
            G (Graph | go.Figure): A NetworkX Graph object or Plotly Figure to be visualized.
            root (Editable | str | int | None): The root node to visualize. Defaults to None.

        Returns:
        ------
            None
        """
        # Convert the graph to a JSON-serializable format
        if isinstance(G, Graph):
            graph_json = graph_to_json(G, root)
        elif isinstance(G, go.Figure):
            graph_json = G.to_json()

        # Check if the visualization path exists, if so, empty it
        if self.op.folder_exists(self.viz_path):
            self.op.emptydir(self.viz_path)
        else:
            # If the path doesn't exist, create it
            self.op.mkdir(self.viz_path)

        # Write the graph data to a file
        with open(self.viz_file_path, "w") as f:
            f.write(graph_json)
            f.flush()  # Ensure data is written to disk
    
    def create_call_graph_visualization(
        self,
        source_function: Function,
        max_depth: int = 5,
        include_external: bool = False,
        include_recursive: bool = True,
        filters: Optional[Dict[CallGraphFilterType, Any]] = None,
        highlight_node: Optional[str] = None,
        layout: str = "dot",
    ) -> go.Figure:
        """Create an enhanced interactive call graph visualization.
        
        Args:
            source_function: The function to create a call graph for
            max_depth: Maximum depth of the call graph
            include_external: Whether to include external module calls
            include_recursive: Whether to include recursive calls
            filters: Filters to apply to the call graph
            highlight_node: Node to highlight
            layout: Layout algorithm to use
            
        Returns:
            A Plotly figure object for interactive visualization
        """
        # Create the call graph
        G, metadata = create_call_graph(
            source_function=source_function,
            max_depth=max_depth,
            include_external=include_external,
            include_recursive=include_recursive,
            filters=filters,
        )
        
        # Apply additional filters if needed
        if filters:
            G = apply_call_graph_filters(G, filters)
        
        # Create the interactive visualization
        fig = create_interactive_call_graph(
            G=G,
            metadata=metadata,
            highlight_node=highlight_node,
            layout=layout,
        )
        
        return fig
    
    def visualize_call_graph(
        self,
        source_function: Function,
        max_depth: int = 5,
        include_external: bool = False,
        include_recursive: bool = True,
        filters: Optional[Dict[CallGraphFilterType, Any]] = None,
        highlight_node: Optional[str] = None,
        layout: str = "dot",
    ) -> None:
        """Create and save a call graph visualization.
        
        Args:
            source_function: The function to create a call graph for
            max_depth: Maximum depth of the call graph
            include_external: Whether to include external module calls
            include_recursive: Whether to include recursive calls
            filters: Filters to apply to the call graph
            highlight_node: Node to highlight
            layout: Layout algorithm to use
        """
        fig = self.create_call_graph_visualization(
            source_function=source_function,
            max_depth=max_depth,
            include_external=include_external,
            include_recursive=include_recursive,
            filters=filters,
            highlight_node=highlight_node,
            layout=layout,
        )
        
        # Write the visualization data
        self.write_graphviz_data(fig)
        
        logger.info(f"Call graph visualization for {source_function.name} saved to {self.viz_file_path}")
    
    def get_available_modules(self, G: DiGraph) -> List[str]:
        """Get a list of available modules in the call graph.
        
        Args:
            G: The call graph
            
        Returns:
            A list of module names
        """
        modules = set()
        for _, attrs in G.nodes(data=True):
            if "file_path" in attrs and attrs["file_path"]:
                module = attrs["file_path"].split("/")[-2]
                modules.add(module)
        return sorted(list(modules))
    
    def get_call_graph_stats(self, G: DiGraph) -> Dict[str, Any]:
        """Get statistics about the call graph.
        
        Args:
            G: The call graph
            
        Returns:
            A dictionary of statistics
        """
        stats = {
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "modules": self.get_available_modules(G),
            "function_types": {
                "methods": sum(1 for _, attrs in G.nodes(data=True) if attrs.get("is_method", False)),
                "functions": sum(1 for _, attrs in G.nodes(data=True) if not attrs.get("is_method", False)),
            },
            "privacy": {
                "private": sum(1 for _, attrs in G.nodes(data=True) if attrs.get("is_private", False)),
                "public": sum(1 for _, attrs in G.nodes(data=True) if not attrs.get("is_private", False)),
            },
            "async": sum(1 for _, attrs in G.nodes(data=True) if attrs.get("is_async", False)),
        }
        return stats

