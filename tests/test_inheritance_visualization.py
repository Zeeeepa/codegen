"""
Tests for inheritance hierarchy visualization features.
"""

import unittest
from unittest.mock import MagicMock, patch

import networkx as nx

from codegen.sdk.core.class_definition import Class
from codegen.visualizations.inheritance_viz import (
    add_class_to_graph,
    add_method_override_info,
    add_subclasses_to_graph,
    add_superclasses_to_graph,
    create_inheritance_graph,
    detect_multiple_inheritance,
    find_common_ancestors,
    highlight_multiple_inheritance,
)


class TestInheritanceVisualization(unittest.TestCase):
    """Test cases for inheritance hierarchy visualization features."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock classes for testing
        self.base_class = MagicMock(spec=Class)
        self.base_class.name = "BaseClass"
        self.base_class.node_id = "base_class_id"
        self.base_class.filepath = "src/models/base.py"
        self.base_class.parent_class_names = []
        self.base_class.has_multiple_inheritance.return_value = False
        
        self.child_class1 = MagicMock(spec=Class)
        self.child_class1.name = "ChildClass1"
        self.child_class1.node_id = "child_class1_id"
        self.child_class1.filepath = "src/models/child1.py"
        self.child_class1.parent_class_names = ["BaseClass"]
        self.child_class1.has_multiple_inheritance.return_value = False
        
        self.child_class2 = MagicMock(spec=Class)
        self.child_class2.name = "ChildClass2"
        self.child_class2.node_id = "child_class2_id"
        self.child_class2.filepath = "src/models/child2.py"
        self.child_class2.parent_class_names = ["BaseClass"]
        self.child_class2.has_multiple_inheritance.return_value = False
        
        self.multi_inherit_class = MagicMock(spec=Class)
        self.multi_inherit_class.name = "MultiInheritClass"
        self.multi_inherit_class.node_id = "multi_inherit_class_id"
        self.multi_inherit_class.filepath = "src/models/multi.py"
        self.multi_inherit_class.parent_class_names = ["ChildClass1", "ChildClass2"]
        self.multi_inherit_class.has_multiple_inheritance.return_value = True
        
        # Set up inheritance relationships
        self.base_class.superclasses.return_value = []
        self.base_class.subclasses.return_value = [self.child_class1, self.child_class2]
        
        self.child_class1.superclasses.return_value = [self.base_class]
        self.child_class1.subclasses.return_value = [self.multi_inherit_class]
        
        self.child_class2.superclasses.return_value = [self.base_class]
        self.child_class2.subclasses.return_value = [self.multi_inherit_class]
        
        self.multi_inherit_class.superclasses.return_value = [self.child_class1, self.child_class2]
        self.multi_inherit_class.subclasses.return_value = []
        
        # Set up methods
        method1 = MagicMock()
        method1.name = "method1"
        method1.is_private = False
        method1.is_static = False
        
        method2 = MagicMock()
        method2.name = "method2"
        method2.is_private = False
        method2.is_static = True
        
        self.base_class.methods.return_value = [method1, method2]
        self.child_class1.methods.return_value = [method1]  # Override method1
        self.child_class2.methods.return_value = []
        self.multi_inherit_class.methods.return_value = [method1, method2]  # Override both methods

    def test_add_class_to_graph(self):
        """Test adding a class to a graph."""
        G = nx.DiGraph()
        add_class_to_graph(G, self.base_class, include_methods=True)
        
        # Check that the class was added to the graph
        self.assertIn(self.base_class, G.nodes())
        
        # Check that the node has the correct attributes
        node_data = G.nodes[self.base_class]
        self.assertEqual(node_data["label"], "BaseClass")
        self.assertEqual(node_data["filepath"], "src/models/base.py")
        self.assertIn("methods", node_data)
        self.assertEqual(len(node_data["methods"]), 2)

    def test_create_inheritance_graph(self):
        """Test creating an inheritance graph."""
        with patch("codegen.visualizations.inheritance_viz.add_superclasses_to_graph") as mock_add_super, \
             patch("codegen.visualizations.inheritance_viz.add_subclasses_to_graph") as mock_add_sub, \
             patch("codegen.visualizations.inheritance_viz.add_class_to_graph") as mock_add_class:
            
            G = create_inheritance_graph(
                root_class=self.base_class,
                include_subclasses=True,
                include_superclasses=True,
                include_methods=True
            )
            
            # Check that the appropriate methods were called
            mock_add_class.assert_called_once_with(G, self.base_class, include_methods=True)
            mock_add_super.assert_called_once()
            mock_add_sub.assert_called_once()

    def test_detect_multiple_inheritance(self):
        """Test detecting multiple inheritance."""
        with patch("codegen.visualizations.inheritance_viz.detect_multiple_inheritance", return_value=[(self.multi_inherit_class, [self.child_class1, self.child_class2])]):
            G = nx.DiGraph()
            
            # Add nodes and edges to the graph
            G.add_node(self.base_class)
            G.add_node(self.child_class1)
            G.add_node(self.child_class2)
            G.add_node(self.multi_inherit_class)
            
            G.add_edge(self.child_class1, self.base_class)
            G.add_edge(self.child_class2, self.base_class)
            G.add_edge(self.multi_inherit_class, self.child_class1)
            G.add_edge(self.multi_inherit_class, self.child_class2)
            
            # Highlight multiple inheritance
            G = highlight_multiple_inheritance(G)
            
            # Check that the multi-inherit class is highlighted
            self.assertIn("multiple_inheritance", G.nodes[self.multi_inherit_class])
            self.assertTrue(G.nodes[self.multi_inherit_class]["multiple_inheritance"])

    def test_find_common_ancestors(self):
        """Test finding common ancestors."""
        G = nx.DiGraph()
        
        # Add nodes and edges to the graph
        G.add_node(self.base_class)
        G.add_node(self.child_class1)
        G.add_node(self.child_class2)
        G.add_node(self.multi_inherit_class)
        
        G.add_edge(self.child_class1, self.base_class)
        G.add_edge(self.child_class2, self.base_class)
        G.add_edge(self.multi_inherit_class, self.child_class1)
        G.add_edge(self.multi_inherit_class, self.child_class2)
        
        # Find common ancestors
        common = find_common_ancestors(G, [self.child_class1, self.child_class2])
        
        # Check that the base class is a common ancestor
        self.assertIn(self.base_class, common)

    def test_add_method_override_info(self):
        """Test adding method override information."""
        G = nx.DiGraph()
        
        # Add nodes to the graph with method information
        G.add_node(
            self.base_class,
            methods=[
                {"name": "method1", "is_private": False, "is_static": False},
                {"name": "method2", "is_private": False, "is_static": True}
            ]
        )
        G.add_node(
            self.child_class1,
            methods=[
                {"name": "method1", "is_private": False, "is_static": False}
            ]
        )
        
        # Add edges
        G.add_edge(self.child_class1, self.base_class)
        
        # Add method override information
        G = add_method_override_info(G)
        
        # Check that the method in child_class1 is marked as overriding
        self.assertIn("overrides", G.nodes[self.child_class1]["methods"][0])
        self.assertEqual(G.nodes[self.child_class1]["methods"][0]["overrides"], "BaseClass")


if __name__ == "__main__":
    unittest.main()

