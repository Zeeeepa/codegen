import os
import unittest
from unittest.mock import MagicMock, patch

import networkx as nx
import plotly.graph_objects as go

from codegen.sdk.core.function import Function
from codegen.visualizations.enums import CallGraphFilterType
from codegen.visualizations.viz_utils import (
    apply_call_graph_filters,
    create_call_graph,
    create_interactive_call_graph,
)


class TestEnhancedCallGraph(unittest.TestCase):
    """Test cases for enhanced call graph visualization features."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock function for testing
        self.mock_function = MagicMock(spec=Function)
        self.mock_function.name = "test_function"
        self.mock_function.filepath = "src/test/module/test_file.py"
        self.mock_function.is_async = False
        self.mock_function.is_method = False
        self.mock_function.is_private = False
        self.mock_function.function_calls = []
        
        # Mock function call
        self.mock_call = MagicMock()
        self.mock_call.name = "called_function"
        self.mock_call.filepath = "src/test/module/test_file.py"
        self.mock_call.start_point = (1, 0)
        self.mock_call.end_point = (1, 20)
        self.mock_call.function_definition = MagicMock(spec=Function)
        self.mock_call.function_definition.name = "called_function"
        self.mock_call.function_definition.filepath = "src/test/module/test_file.py"
        self.mock_call.function_definition.is_async = False
        self.mock_call.function_definition.is_method = False
        self.mock_call.function_definition.is_private = False
        self.mock_call.function_definition.function_calls = []
        
        # Add the mock call to the mock function
        self.mock_function.function_calls = [self.mock_call]

    @patch("networkx.nx_agraph.graphviz_layout")
    def test_create_call_graph(self, mock_graphviz_layout):
        """Test creating a call graph."""
        # Set up mock
        mock_graphviz_layout.return_value = {0: (0, 0), 1: (1, 1)}
        
        # Create call graph
        G, metadata = create_call_graph(
            source_function=self.mock_function,
            max_depth=3,
            include_external=True,
            include_recursive=True,
        )
        
        # Verify graph structure
        self.assertIsInstance(G, nx.DiGraph)
        self.assertEqual(metadata["node_count"], 2)
        self.assertEqual(metadata["edge_count"], 1)
        self.assertFalse(metadata["max_depth_reached"])
        
        # Verify nodes
        self.assertEqual(len(G.nodes), 2)
        
        # Verify edges
        self.assertEqual(len(G.edges), 1)

    @patch("networkx.nx_agraph.graphviz_layout")
    def test_create_interactive_call_graph(self, mock_graphviz_layout):
        """Test creating an interactive call graph."""
        # Set up mock
        mock_graphviz_layout.return_value = {0: (0, 0), 1: (1, 1)}
        
        # Create call graph
        G, metadata = create_call_graph(
            source_function=self.mock_function,
            max_depth=3,
        )
        
        # Create interactive call graph
        fig = create_interactive_call_graph(
            G=G,
            metadata=metadata,
            layout="dot",
        )
        
        # Verify figure
        self.assertIsInstance(fig, go.Figure)
        self.assertGreaterEqual(len(fig.data), 2)  # At least one edge trace and one node trace

    def test_apply_call_graph_filters(self):
        """Test applying filters to a call graph."""
        # Create a simple graph for testing
        G = nx.DiGraph()
        G.add_node(0, name="func1", is_method=True, is_private=False, file_path="src/module1/file.py", complexity=10)
        G.add_node(1, name="func2", is_method=False, is_private=True, file_path="src/module2/file.py", complexity=5)
        G.add_node(2, name="func3", is_method=True, is_private=False, file_path="src/module1/file.py", complexity=3)
        G.add_edge(0, 1)
        G.add_edge(0, 2)
        
        # Test filtering by function type
        filters = {CallGraphFilterType.FUNCTION_TYPE: "method"}
        filtered_G = apply_call_graph_filters(G, filters)
        self.assertEqual(len(filtered_G.nodes), 2)
        self.assertIn(0, filtered_G.nodes)
        self.assertIn(2, filtered_G.nodes)
        
        # Test filtering by privacy
        filters = {CallGraphFilterType.PRIVACY: "private"}
        filtered_G = apply_call_graph_filters(G, filters)
        self.assertEqual(len(filtered_G.nodes), 1)
        self.assertIn(1, filtered_G.nodes)
        
        # Test filtering by module
        filters = {CallGraphFilterType.MODULE: "module1"}
        filtered_G = apply_call_graph_filters(G, filters)
        self.assertEqual(len(filtered_G.nodes), 2)
        self.assertIn(0, filtered_G.nodes)
        self.assertIn(2, filtered_G.nodes)
        
        # Test filtering by complexity
        filters = {CallGraphFilterType.COMPLEXITY: 5}
        filtered_G = apply_call_graph_filters(G, filters)
        self.assertEqual(len(filtered_G.nodes), 2)
        self.assertIn(0, filtered_G.nodes)
        self.assertIn(1, filtered_G.nodes)
        
        # Test multiple filters
        filters = {
            CallGraphFilterType.FUNCTION_TYPE: "method",
            CallGraphFilterType.COMPLEXITY: 5,
        }
        filtered_G = apply_call_graph_filters(G, filters)
        self.assertEqual(len(filtered_G.nodes), 1)
        self.assertIn(0, filtered_G.nodes)


if __name__ == "__main__":
    unittest.main()

