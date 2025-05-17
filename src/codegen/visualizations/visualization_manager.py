import os
from typing import Any, Dict, List, Optional, Union

import plotly.graph_objects as go
from networkx import Graph

from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.sdk.core.interfaces.editable import Editable
from codegen.shared.logging.get_logger import get_logger
from codegen.visualizations.enums import GraphType
from codegen.visualizations.viz_utils import (
    create_call_graph,
    create_dependency_graph,
    create_inheritance_graph,
    create_module_dependency_graph,
    graph_to_json,
)

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

    def write_graphviz_data(self, G: Graph | go.Figure, root: Editable | str | int | None = None, graph_type: GraphType = None) -> None:
        """Writes the graph data to a file.

        Args:
        ----
            G (Graph | go.Figure): A NetworkX Graph object representing the graph to be visualized.
            root (str | None): The root node to visualize. Defaults to None.
            graph_type (GraphType | None): The type of graph to visualize. Defaults to None.

        Returns:
        ------
            None
        """
        # Convert the graph to a JSON-serializable format
        if isinstance(G, Graph):
            graph_json = graph_to_json(G, root, graph_type)
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
            
    def visualize_inheritance_hierarchy(self, class_obj, max_depth: int = 3) -> None:
        """
        Visualize the inheritance hierarchy of a class.
        
        Args:
            class_obj: The class to visualize the inheritance hierarchy for
            max_depth: Maximum depth of the inheritance hierarchy to include
        """
        G = create_inheritance_graph(class_obj, max_depth)
        self.write_graphviz_data(G, graph_type=GraphType.INHERITANCE)
        
    def visualize_call_graph(self, function, max_depth: int = 3, include_external: bool = False) -> None:
        """
        Visualize the call graph of a function.
        
        Args:
            function: The function to visualize the call graph for
            max_depth: Maximum depth of the call graph to include
            include_external: Whether to include external module calls
        """
        G = create_call_graph(function, max_depth, include_external)
        self.write_graphviz_data(G, graph_type=GraphType.CALL_GRAPH)
        
    def visualize_dependency_graph(self, symbol, max_depth: int = 3, include_external: bool = False) -> None:
        """
        Visualize the dependency graph of a symbol.
        
        Args:
            symbol: The symbol to visualize the dependency graph for
            max_depth: Maximum depth of the dependency graph to include
            include_external: Whether to include external module dependencies
        """
        G = create_dependency_graph(symbol, max_depth, include_external)
        self.write_graphviz_data(G, graph_type=GraphType.DEPENDENCY_GRAPH)
        
    def visualize_module_dependencies(self, file_obj, max_depth: int = 3, include_external: bool = False) -> None:
        """
        Visualize the module dependencies of a file.
        
        Args:
            file_obj: The file to visualize the module dependencies for
            max_depth: Maximum depth of the module dependency graph to include
            include_external: Whether to include external module dependencies
        """
        G = create_module_dependency_graph(file_obj, max_depth, include_external)
        self.write_graphviz_data(G, graph_type=GraphType.MODULE_DEPENDENCIES)
