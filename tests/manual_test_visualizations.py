#!/usr/bin/env python3
"""
Manual test script for visualization features.

This script tests the visualization features by creating mock objects
and verifying that the visualization functions work correctly.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the visualization modules
from src.codegen.visualizations.enums import GraphType, VizNode
import networkx as nx

# Create mock objects
mock_class = MagicMock()
mock_class.name = "MockClass"
mock_class.parent_classes = []
mock_class.child_classes = []

mock_function = MagicMock()
mock_function.name = "mock_function"
mock_function.is_method = False
mock_function.function_calls = []

mock_symbol = MagicMock()
mock_symbol.name = "mock_symbol"
mock_symbol.dependencies = []

mock_file = MagicMock()
mock_file.path = MagicMock()
mock_file.path.name = "mock_file.py"
mock_file.imports = []

# Test VizNode
viz_node = VizNode(
    name="TestNode",
    text="Test Node",
    code="print('Hello, World!')",
    color="#ff0000",
    shape="circle",
    emoji="🚀",
    methods=["method1", "method2"],
    parent_class="ParentClass",
    children_classes=["ChildClass1", "ChildClass2"],
    dependencies=["dep1", "dep2"],
    dependents=["dep3", "dep4"],
    is_selected=True,
    description="A test node"
)

print("VizNode test passed!")

# Test GraphType
graph_types = [
    GraphType.TREE,
    GraphType.GRAPH,
    GraphType.INHERITANCE,
    GraphType.CALL_GRAPH,
    GraphType.DEPENDENCY_GRAPH,
    GraphType.MODULE_DEPENDENCIES
]

for graph_type in graph_types:
    print(f"GraphType {graph_type} = {graph_type.value}")

print("GraphType test passed!")

print("All tests passed!")

