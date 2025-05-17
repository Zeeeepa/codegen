import os
import unittest
from unittest.mock import MagicMock, patch

import networkx as nx

from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.function import Function
from codegen.sdk.core.symbol import Symbol
from codegen.visualizations.enums import GraphType
from codegen.visualizations.viz_utils import (
    create_call_graph,
    create_dependency_graph,
    create_inheritance_graph,
    create_module_dependency_graph,
)
from codegen.visualizations.visualization_manager import VisualizationManager


class TestVisualizationUtils(unittest.TestCase):
    def setUp(self):
        # Create mock objects for testing
        self.mock_class = MagicMock(spec=Class)
        self.mock_class.name = "MockClass"
        self.mock_class.parent_classes = []
        self.mock_class.child_classes = []
        
        self.mock_function = MagicMock(spec=Function)
        self.mock_function.name = "mock_function"
        self.mock_function.is_method = False
        self.mock_function.function_calls = []
        
        self.mock_symbol = MagicMock(spec=Symbol)
        self.mock_symbol.name = "mock_symbol"
        self.mock_symbol.dependencies = []
        
        self.mock_file = MagicMock()
        self.mock_file.path.name = "mock_file.py"
        self.mock_file.imports = []

    def test_create_inheritance_graph(self):
        # Test creating an inheritance graph
        G = create_inheritance_graph(self.mock_class)
        self.assertIsInstance(G, nx.DiGraph)
        self.assertEqual(len(G.nodes()), 1)
        
        # Add a parent class and test again
        parent_class = MagicMock(spec=Class)
        parent_class.name = "ParentClass"
        parent_class.parent_classes = []
        parent_class.child_classes = [self.mock_class]
        self.mock_class.parent_classes = [parent_class]
        
        G = create_inheritance_graph(self.mock_class)
        self.assertEqual(len(G.nodes()), 2)
        self.assertEqual(len(G.edges()), 1)

    def test_create_call_graph(self):
        # Test creating a call graph
        G = create_call_graph(self.mock_function)
        self.assertIsInstance(G, nx.DiGraph)
        self.assertEqual(len(G.nodes()), 1)
        
        # Add a function call and test again
        called_function = MagicMock(spec=Function)
        called_function.name = "called_function"
        called_function.is_method = False
        called_function.function_calls = []
        
        function_call = MagicMock()
        function_call.name = "called_function"
        function_call.function_definition = called_function
        
        self.mock_function.function_calls = [function_call]
        
        G = create_call_graph(self.mock_function)
        self.assertEqual(len(G.nodes()), 2)
        self.assertEqual(len(G.edges()), 1)

    def test_create_dependency_graph(self):
        # Test creating a dependency graph
        G = create_dependency_graph(self.mock_symbol)
        self.assertIsInstance(G, nx.DiGraph)
        self.assertEqual(len(G.nodes()), 1)
        
        # Add a dependency and test again
        dependency = MagicMock(spec=Symbol)
        dependency.name = "dependency"
        dependency.dependencies = []
        
        self.mock_symbol.dependencies = [dependency]
        
        G = create_dependency_graph(self.mock_symbol)
        self.assertEqual(len(G.nodes()), 2)
        self.assertEqual(len(G.edges()), 1)

    def test_create_module_dependency_graph(self):
        # Test creating a module dependency graph
        G = create_module_dependency_graph(self.mock_file)
        self.assertIsInstance(G, nx.DiGraph)
        self.assertEqual(len(G.nodes()), 1)
        
        # Add an import and test again
        imported_file = MagicMock()
        imported_file.path.name = "imported_file.py"
        imported_file.imports = []
        
        import_obj = MagicMock()
        import_obj.resolved_file = imported_file
        
        self.mock_file.imports = [import_obj]
        
        G = create_module_dependency_graph(self.mock_file)
        self.assertEqual(len(G.nodes()), 2)
        self.assertEqual(len(G.edges()), 1)


class TestVisualizationManager(unittest.TestCase):
    def setUp(self):
        # Create a mock RepoOperator
        self.mock_op = MagicMock(spec=RepoOperator)
        self.mock_op.base_dir = "/mock/base/dir"
        self.mock_op.folder_exists.return_value = False
        
        # Create a VisualizationManager with the mock RepoOperator
        self.viz_manager = VisualizationManager(self.mock_op)
        
        # Create mock objects for testing
        self.mock_class = MagicMock(spec=Class)
        self.mock_class.name = "MockClass"
        self.mock_class.parent_classes = []
        self.mock_class.child_classes = []
        
        self.mock_function = MagicMock(spec=Function)
        self.mock_function.name = "mock_function"
        self.mock_function.is_method = False
        self.mock_function.function_calls = []
        
        self.mock_symbol = MagicMock(spec=Symbol)
        self.mock_symbol.name = "mock_symbol"
        self.mock_symbol.dependencies = []
        
        self.mock_file = MagicMock()
        self.mock_file.path.name = "mock_file.py"
        self.mock_file.imports = []

    @patch("codegen.visualizations.visualization_manager.create_inheritance_graph")
    def test_visualize_inheritance_hierarchy(self, mock_create_inheritance_graph):
        # Mock the create_inheritance_graph function
        mock_graph = nx.DiGraph()
        mock_create_inheritance_graph.return_value = mock_graph
        
        # Test visualizing an inheritance hierarchy
        with patch.object(self.viz_manager, "write_graphviz_data") as mock_write_graphviz_data:
            self.viz_manager.visualize_inheritance_hierarchy(self.mock_class)
            mock_create_inheritance_graph.assert_called_once_with(self.mock_class, 3)
            mock_write_graphviz_data.assert_called_once_with(mock_graph, graph_type=GraphType.INHERITANCE)

    @patch("codegen.visualizations.visualization_manager.create_call_graph")
    def test_visualize_call_graph(self, mock_create_call_graph):
        # Mock the create_call_graph function
        mock_graph = nx.DiGraph()
        mock_create_call_graph.return_value = mock_graph
        
        # Test visualizing a call graph
        with patch.object(self.viz_manager, "write_graphviz_data") as mock_write_graphviz_data:
            self.viz_manager.visualize_call_graph(self.mock_function)
            mock_create_call_graph.assert_called_once_with(self.mock_function, 3, False)
            mock_write_graphviz_data.assert_called_once_with(mock_graph, graph_type=GraphType.CALL_GRAPH)

    @patch("codegen.visualizations.visualization_manager.create_dependency_graph")
    def test_visualize_dependency_graph(self, mock_create_dependency_graph):
        # Mock the create_dependency_graph function
        mock_graph = nx.DiGraph()
        mock_create_dependency_graph.return_value = mock_graph
        
        # Test visualizing a dependency graph
        with patch.object(self.viz_manager, "write_graphviz_data") as mock_write_graphviz_data:
            self.viz_manager.visualize_dependency_graph(self.mock_symbol)
            mock_create_dependency_graph.assert_called_once_with(self.mock_symbol, 3, False)
            mock_write_graphviz_data.assert_called_once_with(mock_graph, graph_type=GraphType.DEPENDENCY_GRAPH)

    @patch("codegen.visualizations.visualization_manager.create_module_dependency_graph")
    def test_visualize_module_dependencies(self, mock_create_module_dependency_graph):
        # Mock the create_module_dependency_graph function
        mock_graph = nx.DiGraph()
        mock_create_module_dependency_graph.return_value = mock_graph
        
        # Test visualizing module dependencies
        with patch.object(self.viz_manager, "write_graphviz_data") as mock_write_graphviz_data:
            self.viz_manager.visualize_module_dependencies(self.mock_file)
            mock_create_module_dependency_graph.assert_called_once_with(self.mock_file, 3, False)
            mock_write_graphviz_data.assert_called_once_with(mock_graph, graph_type=GraphType.MODULE_DEPENDENCIES)


if __name__ == "__main__":
    unittest.main()

