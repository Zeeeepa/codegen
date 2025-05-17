import os
from typing import TYPE_CHECKING, Optional, Union

import plotly.graph_objects as go
from networkx import Graph

from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.sdk.core.interfaces.editable import Editable
from codegen.shared.logging.get_logger import get_logger
from codegen.visualizations.viz_utils import graph_to_json

if TYPE_CHECKING:
    from codegen.visualizations.module_dependency_viz import ModuleDependencyGraph

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

    def write_graphviz_data(self, G: Union[Graph, go.Figure, "ModuleDependencyGraph"], root: Optional[Union[Editable, str, int]] = None) -> None:
        """Writes the graph data to a file.

        Args:
        ----
            G (Graph | go.Figure | ModuleDependencyGraph): A graph object representing the graph to be visualized.
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
        else:
            # This is a ModuleDependencyGraph
            from codegen.visualizations.module_dependency_viz import ModuleDependencyGraph
            if isinstance(G, ModuleDependencyGraph):
                graph_json = G.to_json(root)
            else:
                raise TypeError(f"Unsupported graph type: {type(G)}")

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
