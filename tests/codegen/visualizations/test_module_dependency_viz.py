"""Tests for the module dependency visualization utilities."""

import os
import unittest
from unittest.mock import MagicMock, patch

import networkx as nx

from codegen.visualizations.module_dependency_viz import (
    ModuleDependencyGraph,
    build_module_dependency_graph,
)


class TestModuleDependencyGraph(unittest.TestCase):
    """Test the ModuleDependencyGraph class."""

    def setUp(self):
        """Set up test fixtures."""
        self.graph = ModuleDependencyGraph()
        
        # Create mock SourceFile objects
        self.file1 = MagicMock()
        self.file1.filepath = "src/app/module1.py"
        self.file1.symbols = ["symbol1", "symbol2"]
        self.file1.__class__.__name__ = "PyFile"
        
        self.file2 = MagicMock()
        self.file2.filepath = "src/app/module2.py"
        self.file2.symbols = ["symbol3"]
        self.file2.__class__.__name__ = "PyFile"
        
        self.file3 = MagicMock()
        self.file3.filepath = "src/utils/module3.py"
        self.file3.symbols = ["symbol4", "symbol5", "symbol6"]
        self.file3.__class__.__name__ = "PyFile"

    def test_add_module(self):
        """Test adding a module to the graph."""
        self.graph.add_module(self.file1)
        
        # Check that the module was added to the graph
        self.assertIn(self.file1, self.graph.graph.nodes())
        self.assertEqual(self.graph.modules[self.file1.filepath]["imports_count"], 0)
        self.assertEqual(self.graph.modules[self.file1.filepath]["imported_by_count"], 0)
        self.assertEqual(self.graph.modules[self.file1.filepath]["is_external"], False)
        
        # Check that node attributes were set correctly
        node_attrs = self.graph.graph.nodes[self.file1]
        self.assertEqual(node_attrs["module_id"], self.file1.filepath)
        self.assertEqual(node_attrs["file"], self.file1)
        self.assertEqual(node_attrs["language"], "py")
        self.assertEqual(node_attrs["symbols_count"], len(self.file1.symbols))

    def test_add_dependency(self):
        """Test adding a dependency between modules."""
        # Add a dependency from file1 to file2
        self.graph.add_dependency(self.file1, self.file2)
        
        # Check that both modules were added to the graph
        self.assertIn(self.file1, self.graph.graph.nodes())
        self.assertIn(self.file2, self.graph.graph.nodes())
        
        # Check that the dependency was added
        self.assertTrue(self.graph.graph.has_edge(self.file1, self.file2))
        
        # Check that module statistics were updated
        self.assertEqual(self.graph.modules[self.file1.filepath]["imports_count"], 1)
        self.assertEqual(self.graph.modules[self.file2.filepath]["imported_by_count"], 1)
        
        # Check that edge attributes were set correctly
        edge_attrs = self.graph.graph.edges[self.file1, self.file2]
        self.assertEqual(edge_attrs["weight"], 1)
        self.assertEqual(edge_attrs["source_id"], self.file1.filepath)
        self.assertEqual(edge_attrs["target_id"], self.file2.filepath)
        
        # Add another dependency from file1 to file2
        self.graph.add_dependency(self.file1, self.file2)
        
        # Check that the weight was incremented
        self.assertEqual(self.graph.graph.edges[self.file1, self.file2]["weight"], 2)
        self.assertEqual(self.graph.modules[self.file1.filepath]["imports_count"], 2)
        self.assertEqual(self.graph.modules[self.file2.filepath]["imported_by_count"], 2)

    def test_detect_circular_dependencies(self):
        """Test detecting circular dependencies."""
        # Create a circular dependency: file1 -> file2 -> file3 -> file1
        self.graph.add_dependency(self.file1, self.file2)
        self.graph.add_dependency(self.file2, self.file3)
        self.graph.add_dependency(self.file3, self.file1)
        
        # Detect circular dependencies
        cycles = self.graph.detect_circular_dependencies()
        
        # Check that the cycle was detected
        self.assertEqual(len(cycles), 1)
        
        # The cycle can start from any node, so we need to check that all nodes are in the cycle
        cycle = cycles[0]
        self.assertEqual(len(cycle), 3)
        self.assertIn(self.file1.filepath, cycle)
        self.assertIn(self.file2.filepath, cycle)
        self.assertIn(self.file3.filepath, cycle)
        
        # Check that nodes and edges in the cycle were marked
        for node in [self.file1, self.file2, self.file3]:
            self.assertTrue(self.graph.graph.nodes[node].get("in_cycle", False))
        
        for edge in [(self.file1, self.file2), (self.file2, self.file3), (self.file3, self.file1)]:
            self.assertTrue(self.graph.graph.edges[edge].get("in_cycle", False))

    def test_filter_by_module_path(self):
        """Test filtering the graph by module path."""
        # Add modules and dependencies
        self.graph.add_dependency(self.file1, self.file2)  # src/app/module1.py -> src/app/module2.py
        self.graph.add_dependency(self.file1, self.file3)  # src/app/module1.py -> src/utils/module3.py
        self.graph.add_dependency(self.file2, self.file3)  # src/app/module2.py -> src/utils/module3.py
        
        # Filter by path "src/app"
        filtered_graph = self.graph.filter_by_module_path("src/app")
        
        # Check that only modules with path starting with "src/app" are included
        self.assertEqual(len(filtered_graph.graph.nodes()), 2)
        self.assertIn(self.file1, filtered_graph.graph.nodes())
        self.assertIn(self.file2, filtered_graph.graph.nodes())
        self.assertNotIn(self.file3, filtered_graph.graph.nodes())
        
        # Check that only edges between included modules are included
        self.assertEqual(len(filtered_graph.graph.edges()), 1)
        self.assertTrue(filtered_graph.graph.has_edge(self.file1, self.file2))
        self.assertFalse(filtered_graph.graph.has_edge(self.file1, self.file3))
        self.assertFalse(filtered_graph.graph.has_edge(self.file2, self.file3))

    def test_filter_by_depth(self):
        """Test filtering the graph by depth."""
        # Create a chain of dependencies: file1 -> file2 -> file3
        self.graph.add_dependency(self.file1, self.file2)
        self.graph.add_dependency(self.file2, self.file3)
        
        # Filter by depth 1 from file1
        filtered_graph = self.graph.filter_by_depth(self.file1, 1)
        
        # Check that only file1 and file2 are included
        self.assertEqual(len(filtered_graph.graph.nodes()), 2)
        self.assertIn(self.file1, filtered_graph.graph.nodes())
        self.assertIn(self.file2, filtered_graph.graph.nodes())
        self.assertNotIn(self.file3, filtered_graph.graph.nodes())
        
        # Check that only the edge from file1 to file2 is included
        self.assertEqual(len(filtered_graph.graph.edges()), 1)
        self.assertTrue(filtered_graph.graph.has_edge(self.file1, self.file2))
        
        # Filter by depth 2 from file1
        filtered_graph = self.graph.filter_by_depth(self.file1, 2)
        
        # Check that all files are included
        self.assertEqual(len(filtered_graph.graph.nodes()), 3)
        self.assertIn(self.file1, filtered_graph.graph.nodes())
        self.assertIn(self.file2, filtered_graph.graph.nodes())
        self.assertIn(self.file3, filtered_graph.graph.nodes())
        
        # Check that all edges are included
        self.assertEqual(len(filtered_graph.graph.edges()), 2)
        self.assertTrue(filtered_graph.graph.has_edge(self.file1, self.file2))
        self.assertTrue(filtered_graph.graph.has_edge(self.file2, self.file3))

    def test_get_module_metrics(self):
        """Test getting module metrics."""
        # Add modules and dependencies
        self.graph.add_dependency(self.file1, self.file2)
        self.graph.add_dependency(self.file1, self.file3)
        self.graph.add_dependency(self.file2, self.file3)
        
        # Get module metrics
        metrics = self.graph.get_module_metrics()
        
        # Check metrics for file1
        self.assertEqual(metrics[self.file1.filepath]["imports_count"], 2)
        self.assertEqual(metrics[self.file1.filepath]["imported_by_count"], 0)
        self.assertEqual(metrics[self.file1.filepath]["in_degree"], 0)
        self.assertEqual(metrics[self.file1.filepath]["out_degree"], 2)
        self.assertEqual(metrics[self.file1.filepath]["total_degree"], 2)
        
        # Check metrics for file2
        self.assertEqual(metrics[self.file2.filepath]["imports_count"], 1)
        self.assertEqual(metrics[self.file2.filepath]["imported_by_count"], 1)
        self.assertEqual(metrics[self.file2.filepath]["in_degree"], 1)
        self.assertEqual(metrics[self.file2.filepath]["out_degree"], 1)
        self.assertEqual(metrics[self.file2.filepath]["total_degree"], 2)
        
        # Check metrics for file3
        self.assertEqual(metrics[self.file3.filepath]["imports_count"], 0)
        self.assertEqual(metrics[self.file3.filepath]["imported_by_count"], 2)
        self.assertEqual(metrics[self.file3.filepath]["in_degree"], 2)
        self.assertEqual(metrics[self.file3.filepath]["out_degree"], 0)
        self.assertEqual(metrics[self.file3.filepath]["total_degree"], 2)

    def test_to_visualization_graph(self):
        """Test converting to a visualization graph."""
        # Add modules and dependencies
        self.graph.add_dependency(self.file1, self.file2)
        self.graph.add_dependency(self.file2, self.file3)
        self.graph.add_dependency(self.file3, self.file1)  # Create a cycle
        
        # Detect circular dependencies
        self.graph.detect_circular_dependencies()
        
        # Convert to visualization graph
        viz_graph = self.graph.to_visualization_graph()
        
        # Check that all nodes and edges are included
        self.assertEqual(len(viz_graph.nodes()), 3)
        self.assertEqual(len(viz_graph.edges()), 3)
        
        # Check that visual attributes were added
        for node in viz_graph.nodes():
            self.assertIn("size", viz_graph.nodes[node])
            self.assertIn("color", viz_graph.nodes[node])
            self.assertIn("tooltip", viz_graph.nodes[node])
            
        for u, v in viz_graph.edges():
            self.assertIn("width", viz_graph.edges[u, v])
            self.assertIn("color", viz_graph.edges[u, v])
            self.assertIn("tooltip", viz_graph.edges[u, v])
            
        # Check that cycle nodes and edges are colored red
        for node in viz_graph.nodes():
            self.assertEqual(viz_graph.nodes[node]["color"], "#ff5555")  # Red
            
        for u, v in viz_graph.edges():
            self.assertEqual(viz_graph.edges[u, v]["color"], "#ff5555")  # Red


class TestBuildModuleDependencyGraph(unittest.TestCase):
    """Test the build_module_dependency_graph function."""

    @patch("codegen.visualizations.module_dependency_viz.ModuleDependencyGraph")
    def test_build_module_dependency_graph(self, mock_graph_class):
        """Test building a module dependency graph."""
        # Create mock files and imports
        file1 = MagicMock()
        file1.filepath = "src/app/module1.py"
        
        file2 = MagicMock()
        file2.filepath = "src/app/module2.py"
        
        # Create mock import statements and imports
        import_statement = MagicMock()
        import1 = MagicMock()
        import1.resolved_symbol = file2
        import_statement.imports = [import1]
        
        file1.import_statements = [import_statement]
        file2.import_statements = []
        
        # Create a mock graph instance
        mock_graph = MagicMock()
        mock_graph_class.return_value = mock_graph
        
        # Call the function
        result = build_module_dependency_graph([file1, file2])
        
        # Check that the graph was created
        mock_graph_class.assert_called_once()
        
        # Check that modules were added
        mock_graph.add_module.assert_any_call(file1)
        mock_graph.add_module.assert_any_call(file2)
        
        # Check that dependencies were added
        mock_graph.add_dependency.assert_called_with(file1, file2, import1)
        
        # Check that circular dependencies were detected
        mock_graph.detect_circular_dependencies.assert_called_once()
        
        # Check that the result is the mock graph
        self.assertEqual(result, mock_graph)


if __name__ == "__main__":
    unittest.main()

