import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import networkx as nx

from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.sdk.core.interfaces.editable import Editable
from codegen.visualizations.enums import ElementType, SelectedElement
from codegen.visualizations.visualization_manager import VisualizationManager


class TestVisualizationManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Mock the RepoOperator
        self.mock_op = MagicMock(spec=RepoOperator)
        self.mock_op.base_dir = self.temp_dir.name
        self.mock_op.folder_exists.return_value = False
        
        # Create the visualization manager
        self.viz_manager = VisualizationManager(self.mock_op)
        
        # Create a mock element
        self.mock_element = MagicMock(spec=Editable)
        self.mock_element.name = "test_element"
        self.mock_element.node_id = "test_id"
        self.mock_element.viz = MagicMock()
        
        # Set up paths
        self.viz_path = os.path.join(self.temp_dir.name, "codegen-graphviz")
        self.viz_file_path = os.path.join(self.viz_path, "graph.json")
        self.selection_file_path = os.path.join(self.viz_path, "selection.json")
        
        # Create the visualization directory
        os.makedirs(self.viz_path, exist_ok=True)
    
    def tearDown(self):
        # Clean up the temporary directory
        self.temp_dir.cleanup()
    
    def test_select_element(self):
        # Mock the create_selected_element function
        mock_selected = SelectedElement(
            type=ElementType.SYMBOL,
            id="test_id",
            name="test_element",
            methods=["method1", "method2"],
            related_elements=["related1", "related2"]
        )
        
        with patch("codegen.visualizations.visualization_manager.create_selected_element", return_value=mock_selected):
            # Select the element
            selected = self.viz_manager.select_element(self.mock_element)
            
            # Check that the element was selected
            self.assertEqual(selected, mock_selected)
            self.assertEqual(self.viz_manager.selected_elements["test_id"], mock_selected)
            
            # Check that the selection file was created
            self.assertTrue(os.path.exists(self.selection_file_path))
    
    def test_deselect_element(self):
        # First select an element
        mock_selected = SelectedElement(
            type=ElementType.SYMBOL,
            id="test_id",
            name="test_element",
            methods=["method1", "method2"],
            related_elements=["related1", "related2"]
        )
        
        with patch("codegen.visualizations.visualization_manager.create_selected_element", return_value=mock_selected):
            self.viz_manager.select_element(self.mock_element)
            
            # Now deselect it
            self.viz_manager.deselect_element("test_id")
            
            # Check that the element was deselected
            self.assertNotIn("test_id", self.viz_manager.selected_elements)
    
    def test_clear_selection(self):
        # First select an element
        mock_selected = SelectedElement(
            type=ElementType.SYMBOL,
            id="test_id",
            name="test_element",
            methods=["method1", "method2"],
            related_elements=["related1", "related2"]
        )
        
        with patch("codegen.visualizations.visualization_manager.create_selected_element", return_value=mock_selected):
            self.viz_manager.select_element(self.mock_element)
            
            # Now clear the selection
            self.viz_manager.clear_selection()
            
            # Check that the selection was cleared
            self.assertEqual(self.viz_manager.selected_elements, {})
    
    def test_get_selected_elements(self):
        # First select an element
        mock_selected = SelectedElement(
            type=ElementType.SYMBOL,
            id="test_id",
            name="test_element",
            methods=["method1", "method2"],
            related_elements=["related1", "related2"]
        )
        
        with patch("codegen.visualizations.visualization_manager.create_selected_element", return_value=mock_selected):
            self.viz_manager.select_element(self.mock_element)
            
            # Get the selected elements
            selected_elements = self.viz_manager.get_selected_elements()
            
            # Check that the selected elements are correct
            self.assertEqual(selected_elements, {"test_id": mock_selected})
    
    def test_get_selected_element(self):
        # First select an element
        mock_selected = SelectedElement(
            type=ElementType.SYMBOL,
            id="test_id",
            name="test_element",
            methods=["method1", "method2"],
            related_elements=["related1", "related2"]
        )
        
        with patch("codegen.visualizations.visualization_manager.create_selected_element", return_value=mock_selected):
            self.viz_manager.select_element(self.mock_element)
            
            # Get the selected element
            selected_element = self.viz_manager.get_selected_element("test_id")
            
            # Check that the selected element is correct
            self.assertEqual(selected_element, mock_selected)
    
    def test_get_selected_element_methods(self):
        # First select an element
        mock_selected = SelectedElement(
            type=ElementType.SYMBOL,
            id="test_id",
            name="test_element",
            methods=["method1", "method2"],
            related_elements=["related1", "related2"]
        )
        
        with patch("codegen.visualizations.visualization_manager.create_selected_element", return_value=mock_selected):
            self.viz_manager.select_element(self.mock_element)
            
            # Get the selected element methods
            methods = self.viz_manager.get_selected_element_methods("test_id")
            
            # Check that the methods are correct
            self.assertEqual(methods, ["method1", "method2"])
    
    def test_get_selected_element_related(self):
        # First select an element
        mock_selected = SelectedElement(
            type=ElementType.SYMBOL,
            id="test_id",
            name="test_element",
            methods=["method1", "method2"],
            related_elements=["related1", "related2"]
        )
        
        with patch("codegen.visualizations.visualization_manager.create_selected_element", return_value=mock_selected):
            self.viz_manager.select_element(self.mock_element)
            
            # Get the selected element related elements
            related = self.viz_manager.get_selected_element_related("test_id")
            
            # Check that the related elements are correct
            self.assertEqual(related, ["related1", "related2"])
    
    def test_write_graphviz_data(self):
        # Create a mock graph
        G = nx.DiGraph()
        G.add_node("node1", name="Node 1")
        G.add_node("node2", name="Node 2")
        G.add_edge("node1", "node2")
        
        # Write the graph data
        with patch("codegen.visualizations.visualization_manager.graph_to_json", return_value='{"test": "data"}'):
            self.viz_manager.write_graphviz_data(G)
            
            # Check that the graph file was created
            self.assertTrue(os.path.exists(self.viz_file_path))
            
            # Check that the file contains the expected data
            with open(self.viz_file_path, "r") as f:
                data = f.read()
                self.assertEqual(data, '{"test": "data"}')


if __name__ == "__main__":
    unittest.main()

