#!/usr/bin/env python3
"""
Test module for the BaseVisualizer class.

This module contains comprehensive tests for the BaseVisualizer class,
which provides the foundation for all visualization capabilities in the Codegen repository.
"""

import os
import tempfile
import json
from unittest.mock import patch, MagicMock

import pytest
import networkx as nx
import matplotlib.pyplot as plt

from codegen_on_oss.analyzers.visualization.visualizer import (
    BaseVisualizer,
    VisualizationConfig,
    VisualizationType,
    OutputFormat,
)


class TestBaseVisualizerInitialization:
    """Tests for BaseVisualizer initialization."""

    def test_default_initialization(self):
        """Test initializing visualizer with default configuration."""
        visualizer = BaseVisualizer()
        assert visualizer.config is not None
        assert visualizer.config.max_depth == 5
        assert visualizer.config.ignore_external is True
        assert visualizer.config.ignore_tests is True
        assert visualizer.config.output_format == OutputFormat.JSON
        assert visualizer.config.output_directory is None
        assert isinstance(visualizer.graph, nx.DiGraph)
        assert visualizer.current_visualization_type is None
        assert visualizer.current_entity_name is None

    def test_custom_initialization(self):
        """Test initializing visualizer with custom configuration."""
        config = VisualizationConfig(
            max_depth=10,
            ignore_external=False,
            ignore_tests=False,
            output_format=OutputFormat.PNG,
            output_directory="/tmp/viz",
            layout_algorithm="kamada_kawai",
        )
        visualizer = BaseVisualizer(config=config)
        assert visualizer.config.max_depth == 10
        assert visualizer.config.ignore_external is False
        assert visualizer.config.ignore_tests is False
        assert visualizer.config.output_format == OutputFormat.PNG
        assert visualizer.config.output_directory == "/tmp/viz"
        assert visualizer.config.layout_algorithm == "kamada_kawai"

    def test_initialization_creates_output_directory(self):
        """Test that initialization creates the output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = os.path.join(temp_dir, "viz_output")
            config = VisualizationConfig(output_directory=output_dir)
            
            # Directory shouldn't exist yet
            assert not os.path.exists(output_dir)
            
            # Initialize visualizer
            visualizer = BaseVisualizer(config=config)
            
            # Directory should now exist
            assert os.path.exists(output_dir)
            assert os.path.isdir(output_dir)


class TestBaseVisualizerGraphManipulation:
    """Tests for BaseVisualizer graph manipulation methods."""

    def test_initialize_graph(self):
        """Test graph initialization."""
        visualizer = BaseVisualizer()
        
        # Add a node to the graph
        visualizer.graph.add_node(1, name="test")
        assert visualizer.graph.has_node(1)
        
        # Initialize graph should clear it
        visualizer._initialize_graph()
        assert not visualizer.graph.has_node(1)
        assert isinstance(visualizer.graph, nx.DiGraph)

    def test_add_node_basic(self):
        """Test adding a basic node to the graph."""
        visualizer = BaseVisualizer()
        
        # Create a mock node
        mock_node = MagicMock()
        mock_node.name = "test_node"
        mock_node.__class__.__name__ = "Function"
        
        # Add the node
        node_id = visualizer._add_node(mock_node)
        
        # Verify the node was added correctly
        assert visualizer.graph.has_node(node_id)
        node_attrs = visualizer.graph.nodes[node_id]
        assert node_attrs["name"] == "test_node"
        assert node_attrs["type"] == "Function"
        assert node_attrs["color"] == visualizer.config.color_palette["Function"]
        assert node_attrs["original_node"] == mock_node

    def test_add_node_with_attributes(self):
        """Test adding a node with custom attributes."""
        visualizer = BaseVisualizer()
        
        # Create a mock node
        mock_node = MagicMock()
        mock_node.name = "test_node"
        
        # Add the node with custom attributes
        node_id = visualizer._add_node(
            mock_node,
            color="#FF0000",
            weight=5,
            custom_attr="custom_value"
        )
        
        # Verify the node was added with custom attributes
        node_attrs = visualizer.graph.nodes[node_id]
        assert node_attrs["color"] == "#FF0000"
        assert node_attrs["weight"] == 5
        assert node_attrs["custom_attr"] == "custom_value"

    def test_add_node_with_path(self):
        """Test adding a node with path instead of name."""
        visualizer = BaseVisualizer()
        
        # Create a mock node without name but with path
        mock_node = MagicMock()
        delattr(mock_node, "name")
        mock_node.path = "/path/to/file.py"
        
        # Add the node
        node_id = visualizer._add_node(mock_node)
        
        # Verify the node name is derived from path
        node_attrs = visualizer.graph.nodes[node_id]
        assert node_attrs["name"] == "file.py"

    def test_add_node_duplicate(self):
        """Test adding the same node twice."""
        visualizer = BaseVisualizer()
        
        # Create a mock node
        mock_node = MagicMock()
        mock_node.name = "test_node"
        
        # Add the node twice
        node_id1 = visualizer._add_node(mock_node)
        node_id2 = visualizer._add_node(mock_node)
        
        # Verify only one node was added
        assert node_id1 == node_id2
        assert len(visualizer.graph.nodes) == 1

    def test_add_edge_basic(self):
        """Test adding a basic edge to the graph."""
        visualizer = BaseVisualizer()
        
        # Create mock nodes
        source_node = MagicMock()
        source_node.name = "source"
        target_node = MagicMock()
        target_node.name = "target"
        
        # Add nodes and edge
        source_id = visualizer._add_node(source_node)
        target_id = visualizer._add_node(target_node)
        visualizer._add_edge(source_node, target_node)
        
        # Verify the edge was added correctly
        assert visualizer.graph.has_edge(source_id, target_id)

    def test_add_edge_with_attributes(self):
        """Test adding an edge with custom attributes."""
        visualizer = BaseVisualizer()
        
        # Create mock nodes
        source_node = MagicMock()
        source_node.name = "source"
        target_node = MagicMock()
        target_node.name = "target"
        
        # Add nodes and edge with attributes
        source_id = visualizer._add_node(source_node)
        target_id = visualizer._add_node(target_node)
        visualizer._add_edge(
            source_node,
            target_node,
            weight=2,
            type="calls",
            color="#00FF00"
        )
        
        # Verify the edge attributes
        edge_attrs = visualizer.graph.edges[source_id, target_id]
        assert edge_attrs["weight"] == 2
        assert edge_attrs["type"] == "calls"
        assert edge_attrs["color"] == "#00FF00"


class TestBaseVisualizerFileOperations:
    """Tests for BaseVisualizer file operations."""

    def test_generate_filename(self):
        """Test filename generation for visualization."""
        visualizer = BaseVisualizer()
        filename = visualizer._generate_filename(
            VisualizationType.CALL_GRAPH, "test/function"
        )
        
        # Verify filename format
        assert filename.startswith("call_graph_test_function_")
        assert filename.endswith(".json")

    def test_generate_filename_sanitization(self):
        """Test filename sanitization for special characters."""
        visualizer = BaseVisualizer()
        filename = visualizer._generate_filename(
            VisualizationType.DEPENDENCY_GRAPH, "path/to/file.py"
        )
        
        # Verify special characters are sanitized
        assert "path/to/file.py" not in filename
        assert "path_to_file_py" in filename

    @patch("builtins.open", new_callable=MagicMock)
    @patch("json.dump")
    def test_save_visualization_json(self, mock_json_dump, mock_open):
        """Test saving visualization as JSON."""
        visualizer = BaseVisualizer()
        
        # Mock data to save
        data = {"nodes": [], "edges": []}
        
        # Save visualization
        result = visualizer._save_visualization(
            VisualizationType.CALL_GRAPH, "test_func", data
        )
        
        # Verify file operations
        mock_open.assert_called_once()
        mock_json_dump.assert_called_once_with(data, mock_open().__enter__(), indent=2)
        
        # Verify visualization tracking
        assert visualizer.current_visualization_type == VisualizationType.CALL_GRAPH
        assert visualizer.current_entity_name == "test_func"

    @patch("matplotlib.pyplot.savefig")
    @patch("matplotlib.pyplot.close")
    def test_save_visualization_png(self, mock_close, mock_savefig):
        """Test saving visualization as PNG."""
        # Create temp directory for output
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VisualizationConfig(
                output_format=OutputFormat.PNG,
                output_directory=temp_dir,
            )
            visualizer = BaseVisualizer(config=config)
            
            # Mock figure for saving
            mock_fig = MagicMock()
            
            # Save visualization
            filepath = visualizer._save_visualization(
                VisualizationType.CALL_GRAPH, "test_func", mock_fig
            )
            
            # Verify savefig was called
            mock_savefig.assert_called_once()
            mock_close.assert_called_once()
            assert os.path.dirname(filepath) == temp_dir
            assert filepath.endswith(".png")

    @patch("networkx.drawing.nx_agraph.write_dot")
    def test_save_visualization_dot(self, mock_write_dot):
        """Test saving visualization as DOT."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VisualizationConfig(
                output_format=OutputFormat.DOT,
                output_directory=temp_dir,
            )
            visualizer = BaseVisualizer(config=config)
            
            # Add some nodes to the graph
            visualizer.graph.add_node(1, name="node1")
            visualizer.graph.add_node(2, name="node2")
            visualizer.graph.add_edge(1, 2)
            
            # Save visualization
            filepath = visualizer._save_visualization(
                VisualizationType.DEPENDENCY_GRAPH, "test_module", visualizer.graph
            )
            
            # Verify write_dot was called
            mock_write_dot.assert_called_once_with(visualizer.graph, filepath)


class TestBaseVisualizerDataConversion:
    """Tests for BaseVisualizer data conversion methods."""

    def test_convert_graph_to_json_empty(self):
        """Test converting an empty graph to JSON."""
        visualizer = BaseVisualizer()
        visualizer.current_visualization_type = VisualizationType.CALL_GRAPH
        visualizer.current_entity_name = "test_func"
        
        # Convert empty graph
        result = visualizer._convert_graph_to_json()
        
        # Verify structure
        assert "nodes" in result
        assert "edges" in result
        assert "metadata" in result
        assert len(result["nodes"]) == 0
        assert len(result["edges"]) == 0
        assert result["metadata"]["visualization_type"] == VisualizationType.CALL_GRAPH
        assert result["metadata"]["entity_name"] == "test_func"
        assert result["metadata"]["node_count"] == 0
        assert result["metadata"]["edge_count"] == 0

    def test_convert_graph_to_json_with_data(self):
        """Test converting a graph with data to JSON."""
        visualizer = BaseVisualizer()
        visualizer.current_visualization_type = VisualizationType.DEPENDENCY_GRAPH
        visualizer.current_entity_name = "test_module"
        
        # Add nodes and edges
        visualizer.graph.add_node(1, name="node1", type="Function", color="#FF0000")
        visualizer.graph.add_node(2, name="node2", type="Class", color="#00FF00")
        visualizer.graph.add_edge(1, 2, weight=2, type="calls")
        
        # Convert graph
        result = visualizer._convert_graph_to_json()
        
        # Verify nodes
        assert len(result["nodes"]) == 2
        node1 = next(n for n in result["nodes"] if n["name"] == "node1")
        assert node1["type"] == "Function"
        assert node1["color"] == "#FF0000"
        
        # Verify edges
        assert len(result["edges"]) == 1
        edge = result["edges"][0]
        assert edge["source"] == 1
        assert edge["target"] == 2
        assert edge["weight"] == 2
        assert edge["type"] == "calls"

    def test_convert_graph_to_json_with_complex_attributes(self):
        """Test converting a graph with complex attributes to JSON."""
        visualizer = BaseVisualizer()
        
        # Add node with complex attributes
        visualizer.graph.add_node(
            1,
            name="node1",
            original_node=MagicMock(),  # Should be excluded
            complex_object=MagicMock(),  # Should be excluded
            file_path="/path/to/file.py",  # Should be included
            simple_list=[1, 2, 3],  # Should be included
            simple_dict={"key": "value"},  # Should be included
        )
        
        # Convert graph
        result = visualizer._convert_graph_to_json()
        
        # Verify node attributes
        node = result["nodes"][0]
        assert "original_node" not in node
        assert "complex_object" not in node
        assert node["file_path"] == "/path/to/file.py"
        assert node["simple_list"] == [1, 2, 3]
        assert node["simple_dict"] == {"key": "value"}


class TestBaseVisualizerPlotting:
    """Tests for BaseVisualizer plotting methods."""

    @patch("networkx.draw_networkx_nodes")
    @patch("networkx.draw_networkx_edges")
    @patch("networkx.draw_networkx_labels")
    @patch("matplotlib.pyplot.figure")
    @patch("matplotlib.pyplot.title")
    @patch("matplotlib.pyplot.axis")
    @patch("matplotlib.pyplot.gcf")
    @patch("networkx.spring_layout")
    def test_plot_graph_spring_layout(
        self, mock_spring_layout, mock_gcf, mock_axis, mock_title,
        mock_figure, mock_draw_labels, mock_draw_edges, mock_draw_nodes
    ):
        """Test plotting graph with spring layout."""
        visualizer = BaseVisualizer()
        visualizer.current_visualization_type = VisualizationType.CALL_GRAPH
        visualizer.current_entity_name = "test_func"
        
        # Add nodes and edges
        visualizer.graph.add_node(1, name="node1", color="#FF0000")
        visualizer.graph.add_node(2, name="node2", color="#00FF00")
        visualizer.graph.add_edge(1, 2)
        
        # Mock layout
        mock_spring_layout.return_value = {1: (0, 0), 2: (1, 1)}
        
        # Plot graph
        result = visualizer._plot_graph()
        
        # Verify layout was used
        mock_spring_layout.assert_called_once_with(visualizer.graph, seed=42)
        
        # Verify drawing functions were called
        mock_draw_nodes.assert_called_once()
        mock_draw_edges.assert_called_once()
        mock_draw_labels.assert_called_once()
        
        # Verify title and axis
        mock_title.assert_called_once_with("call_graph - test_func")
        mock_axis.assert_called_once_with("off")

    @patch("networkx.kamada_kawai_layout")
    @patch("matplotlib.pyplot.gcf")
    def test_plot_graph_kamada_kawai_layout(self, mock_gcf, mock_kamada_kawai_layout):
        """Test plotting graph with Kamada-Kawai layout."""
        config = VisualizationConfig(layout_algorithm="kamada_kawai")
        visualizer = BaseVisualizer(config=config)
        
        # Add nodes
        visualizer.graph.add_node(1, name="node1")
        visualizer.graph.add_node(2, name="node2")
        
        # Mock layout
        mock_kamada_kawai_layout.return_value = {1: (0, 0), 2: (1, 1)}
        
        # Plot graph
        visualizer._plot_graph()
        
        # Verify layout was used
        mock_kamada_kawai_layout.assert_called_once_with(visualizer.graph)

    @patch("networkx.spectral_layout")
    @patch("matplotlib.pyplot.gcf")
    def test_plot_graph_spectral_layout(self, mock_gcf, mock_spectral_layout):
        """Test plotting graph with spectral layout."""
        config = VisualizationConfig(layout_algorithm="spectral")
        visualizer = BaseVisualizer(config=config)
        
        # Add nodes
        visualizer.graph.add_node(1, name="node1")
        visualizer.graph.add_node(2, name="node2")
        
        # Mock layout
        mock_spectral_layout.return_value = {1: (0, 0), 2: (1, 1)}
        
        # Plot graph
        visualizer._plot_graph()
        
        # Verify layout was used
        mock_spectral_layout.assert_called_once_with(visualizer.graph)


if __name__ == "__main__":
    pytest.main(["-v", __file__])

