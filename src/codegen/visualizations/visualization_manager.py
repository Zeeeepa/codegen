import os
from typing import Dict, List, Optional, Union

import plotly.graph_objects as go
from networkx import DiGraph, Graph

from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.interfaces.editable import Editable
from codegen.shared.logging.get_logger import get_logger
from codegen.visualizations.inheritance_viz import (
    add_method_override_info,
    create_inheritance_graph,
    highlight_multiple_inheritance,
)
from codegen.visualizations.viz_utils import graph_to_json

logger = get_logger(__name__)


class VisualizationManager:
    op: RepoOperator

    def __init__(
        self,
        op: RepoOperator,
    ) -> None:
        self.op = op

    @property
    def viz_path(self) -> str:
        return os.path.join(self.op.base_dir, "codegen-graphviz")

    @property
    def viz_file_path(self) -> str:
        return os.path.join(self.viz_path, "graph.json")

    def clear_graphviz_data(self) -> None:
        if self.op.folder_exists(self.viz_path):
            self.op.emptydir(self.viz_path)

    def write_graphviz_data(self, G: Graph | go.Figure, root: Editable | str | int | None = None) -> None:
        """Writes the graph data to a file.

        Args:
        ----
            G (Graph | go.Figure): A NetworkX Graph object representing the graph to be visualized.
            root (str | None): The root node to visualize. Defaults to None.

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
            
    def visualize_inheritance_hierarchy(
        self,
        root_class: Class,
        max_depth: Optional[int] = None,
        include_subclasses: bool = True,
        include_superclasses: bool = True,
        include_interfaces: bool = True,
        include_external: bool = True,
        include_methods: bool = False,
        highlight_multiple: bool = True,
        show_method_overrides: bool = True,
        filter_packages: Optional[List[str]] = None,
    ) -> None:
        """
        Creates and visualizes an inheritance hierarchy for a given class.
        
        Args:
            root_class: The root class to start the inheritance hierarchy from
            max_depth: Maximum depth of inheritance hierarchy to include (None for unlimited)
            include_subclasses: Whether to include subclasses in the graph
            include_superclasses: Whether to include superclasses in the graph
            include_interfaces: Whether to include interfaces in the graph
            include_external: Whether to include external modules in the graph
            include_methods: Whether to include methods in the graph
            highlight_multiple: Whether to highlight multiple inheritance
            show_method_overrides: Whether to show method override information
            filter_packages: List of package prefixes to include (None for all)
        """
        # Create the inheritance graph
        G = create_inheritance_graph(
            root_class=root_class,
            max_depth=max_depth,
            include_subclasses=include_subclasses,
            include_superclasses=include_superclasses,
            include_interfaces=include_interfaces,
            include_external=include_external,
            include_methods=include_methods,
            filter_packages=filter_packages,
        )
        
        # Apply additional enhancements
        if highlight_multiple:
            G = highlight_multiple_inheritance(G)
            
        if show_method_overrides and include_methods:
            G = add_method_override_info(G)
        
        # Write the graph data to a file
        self.write_graphviz_data(G, root=root_class)
