import json
import os
from typing import Dict, List, Optional, Union

import plotly.graph_objects as go
from networkx import Graph

from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.sdk.core.interfaces.editable import Editable
from codegen.shared.logging.get_logger import get_logger
from codegen.visualizations.enums import ElementType, SelectedElement
from codegen.visualizations.viz_utils import (
    create_selected_element,
    graph_to_json,
    selected_element_to_json,
)

logger = get_logger(__name__)


class VisualizationManager:
    op: RepoOperator
    selected_elements: Dict[str, SelectedElement]

    def __init__(
        self,
        op: RepoOperator,
    ) -> None:
        self.op = op
        self.selected_elements = {}

    @property
    def viz_path(self) -> str:
        return os.path.join(self.op.base_dir, "codegen-graphviz")

    @property
    def viz_file_path(self) -> str:
        return os.path.join(self.viz_path, "graph.json")

    @property
    def selection_file_path(self) -> str:
        return os.path.join(self.viz_path, "selection.json")

    def clear_graphviz_data(self) -> None:
        if self.op.folder_exists(self.viz_path):
            self.op.emptydir(self.viz_path)
        self.selected_elements = {}

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

    def select_element(self, element: Editable) -> SelectedElement:
        """Select an element in the visualization.

        Args:
        ----
            element (Editable): The element to select.

        Returns:
        ------
            SelectedElement: The selected element.
        """
        selected = create_selected_element(element)
        self.selected_elements[selected.id] = selected
        self._write_selection_data()
        return selected

    def deselect_element(self, element_id: str) -> None:
        """Deselect an element in the visualization.

        Args:
        ----
            element_id (str): The ID of the element to deselect.

        Returns:
        ------
            None
        """
        if element_id in self.selected_elements:
            del self.selected_elements[element_id]
            self._write_selection_data()

    def clear_selection(self) -> None:
        """Clear all selected elements.

        Returns:
        ------
            None
        """
        self.selected_elements = {}
        self._write_selection_data()

    def get_selected_elements(self) -> Dict[str, SelectedElement]:
        """Get all selected elements.

        Returns:
        ------
            Dict[str, SelectedElement]: A dictionary of selected elements.
        """
        return self.selected_elements

    def get_selected_element(self, element_id: str) -> Optional[SelectedElement]:
        """Get a selected element by ID.

        Args:
        ----
            element_id (str): The ID of the element to get.

        Returns:
        ------
            Optional[SelectedElement]: The selected element, or None if not found.
        """
        return self.selected_elements.get(element_id)

    def get_selected_element_methods(self, element_id: str) -> List[str]:
        """Get the methods of a selected element.

        Args:
        ----
            element_id (str): The ID of the element to get methods for.

        Returns:
        ------
            List[str]: A list of method names.
        """
        element = self.get_selected_element(element_id)
        if element and element.methods:
            return element.methods
        return []

    def get_selected_element_related(self, element_id: str) -> List[str]:
        """Get the related elements of a selected element.

        Args:
        ----
            element_id (str): The ID of the element to get related elements for.

        Returns:
        ------
            List[str]: A list of related element names.
        """
        element = self.get_selected_element(element_id)
        if element and element.related_elements:
            return element.related_elements
        return []

    def _write_selection_data(self) -> None:
        """Write the selection data to a file.

        Returns:
        ------
            None
        """
        # Ensure the visualization path exists
        if not self.op.folder_exists(self.viz_path):
            self.op.mkdir(self.viz_path)

        # Convert the selection data to JSON
        selection_json = json.dumps(
            {element_id: selected_element_to_json(element) for element_id, element in self.selected_elements.items()},
            indent=2,
        )

        # Write the selection data to a file
        with open(self.selection_file_path, "w") as f:
            f.write(selection_json)
            f.flush()  # Ensure data is written to disk
