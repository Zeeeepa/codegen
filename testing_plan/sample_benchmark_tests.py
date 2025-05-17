#!/usr/bin/env python3
"""
Performance benchmark tests for visualization features.

This module contains benchmark tests for measuring the performance of
visualization features with different codebase sizes and configurations.
"""

import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest
import networkx as nx
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing

from codegen_on_oss.analyzers.visualization.codebase_visualizer import (
    CodebaseVisualizer,
    VisualizationConfig,
    VisualizationType,
    OutputFormat,
)


class MockSymbol:
    """Mock Symbol class for testing."""
    
    def __init__(self, name, filepath, symbol_type="Function"):
        self.name = name
        self.filepath = filepath
        self.symbol_type = symbol_type
        self.function_calls = []
        self.dependencies = []
        self.usages = []
        self.methods = []
        self.imports = []
        self.viz = MagicMock()
        self.viz.name = name
        self.viz.color = "#AABBCC"


class MockCodebase:
    """Mock Codebase class for testing."""
    
    def __init__(self, size="small"):
        self.size = size
        self.files = []
        self.symbols = {}
        self._setup_codebase()
    
    def _setup_codebase(self):
        """Set up the mock codebase with appropriate size."""
        if self.size == "small":
            self._setup_small_codebase()
        elif self.size == "medium":
            self._setup_medium_codebase()
        elif self.size == "large":
            self._setup_large_codebase()
    
    def _setup_small_codebase(self):
        """Set up a small codebase with ~10 files and ~50 symbols."""
        # Create files
        for i in range(10):
            file = MagicMock()
            file.filepath = f"src/module{i}.py"
            self.files.append(file)
        
        # Create symbols
        for i in range(50):
            file_idx = i % 10
            symbol = MockSymbol(
                name=f"symbol{i}",
                filepath=f"src/module{file_idx}.py",
                symbol_type="Function" if i % 3 == 0 else "Class" if i % 3 == 1 else "Variable"
            )
            self.symbols[symbol.name] = symbol
        
        # Create relationships
        for i in range(50):
            symbol = self.symbols[f"symbol{i}"]
            
            # Add function calls (each function calls 2-3 others)
            if i % 3 == 0:  # Functions
                for j in range(2, 5):
                    if f"symbol{(i+j) % 50}" in self.symbols:
                        call = MagicMock()
                        call.function_definition = self.symbols[f"symbol{(i+j) % 50}"]
                        symbol.function_calls.append(call)
            
            # Add dependencies (each symbol depends on 1-2 others)
            for j in range(1, 3):
                if f"symbol{(i+j*10) % 50}" in self.symbols:
                    symbol.dependencies.append(self.symbols[f"symbol{(i+j*10) % 50}"])
            
            # Add usages (each symbol is used by 1-2 others)
            for j in range(1, 3):
                if f"symbol{(i+j*7) % 50}" in self.symbols:
                    usage = MagicMock()
                    usage.usage_symbol = self.symbols[f"symbol{(i+j*7) % 50}"]
                    usage.match = MagicMock()
                    usage.match.source = f"Using symbol{i}"
                    usage.match.filepath = f"src/module{(i+j*7) % 10}.py"
                    usage.match.start_point = (1, 1)
                    usage.match.end_point = (1, 10)
                    symbol.usages.append(usage)
    
    def _setup_medium_codebase(self):
        """Set up a medium codebase with ~50 files and ~500 symbols."""
        # Create files
        for i in range(50):
            file = MagicMock()
            file.filepath = f"src/module{i//5}/file{i}.py"
            self.files.append(file)
        
        # Create symbols
        for i in range(500):
            file_idx = i % 50
            symbol = MockSymbol(
                name=f"symbol{i}",
                filepath=f"src/module{file_idx//5}/file{file_idx}.py",
                symbol_type="Function" if i % 3 == 0 else "Class" if i % 3 == 1 else "Variable"
            )
            self.symbols[symbol.name] = symbol
        
        # Create relationships (similar to small codebase but scaled up)
        for i in range(500):
            symbol = self.symbols[f"symbol{i}"]
            
            # Add function calls
            if i % 3 == 0:  # Functions
                for j in range(3, 8):
                    if f"symbol{(i+j) % 500}" in self.symbols:
                        call = MagicMock()
                        call.function_definition = self.symbols[f"symbol{(i+j) % 500}"]
                        symbol.function_calls.append(call)
            
            # Add dependencies
            for j in range(2, 5):
                if f"symbol{(i+j*10) % 500}" in self.symbols:
                    symbol.dependencies.append(self.symbols[f"symbol{(i+j*10) % 500}"])
            
            # Add usages
            for j in range(2, 5):
                if f"symbol{(i+j*7) % 500}" in self.symbols:
                    usage = MagicMock()
                    usage.usage_symbol = self.symbols[f"symbol{(i+j*7) % 500}"]
                    usage.match = MagicMock()
                    usage.match.source = f"Using symbol{i}"
                    usage.match.filepath = f"src/module{((i+j*7) % 50)//5}/file{(i+j*7) % 50}.py"
                    usage.match.start_point = (1, 1)
                    usage.match.end_point = (1, 10)
                    symbol.usages.append(usage)
    
    def _setup_large_codebase(self):
        """Set up a large codebase with ~200 files and ~2000 symbols."""
        # Create files
        for i in range(200):
            file = MagicMock()
            file.filepath = f"src/module{i//10}/submodule{i%10}/file{i}.py"
            self.files.append(file)
        
        # Create symbols
        for i in range(2000):
            file_idx = i % 200
            symbol = MockSymbol(
                name=f"symbol{i}",
                filepath=f"src/module{file_idx//10}/submodule{file_idx%10}/file{file_idx}.py",
                symbol_type="Function" if i % 3 == 0 else "Class" if i % 3 == 1 else "Variable"
            )
            self.symbols[symbol.name] = symbol
        
        # Create relationships (similar to medium codebase but scaled up)
        for i in range(2000):
            symbol = self.symbols[f"symbol{i}"]
            
            # Add function calls
            if i % 3 == 0:  # Functions
                for j in range(5, 15):
                    if f"symbol{(i+j) % 2000}" in self.symbols:
                        call = MagicMock()
                        call.function_definition = self.symbols[f"symbol{(i+j) % 2000}"]
                        symbol.function_calls.append(call)
            
            # Add dependencies
            for j in range(3, 8):
                if f"symbol{(i+j*10) % 2000}" in self.symbols:
                    symbol.dependencies.append(self.symbols[f"symbol{(i+j*10) % 2000}"])
            
            # Add usages
            for j in range(3, 8):
                if f"symbol{(i+j*7) % 2000}" in self.symbols:
                    usage = MagicMock()
                    usage.usage_symbol = self.symbols[f"symbol{(i+j*7) % 2000}"]
                    usage.match = MagicMock()
                    usage.match.source = f"Using symbol{i}"
                    usage.match.filepath = f"src/module{((i+j*7) % 200)//10}/submodule{(i+j*7) % 10}/file{(i+j*7) % 200}.py"
                    usage.match.start_point = (1, 1)
                    usage.match.end_point = (1, 10)
                    symbol.usages.append(usage)
    
    def get_function(self, name):
        """Get a function by name."""
        if name in self.symbols and self.symbols[name].symbol_type == "Function":
            return self.symbols[name]
        return None
    
    def get_class(self, name):
        """Get a class by name."""
        if name in self.symbols and self.symbols[name].symbol_type == "Class":
            return self.symbols[name]
        return None
    
    def get_symbol(self, name):
        """Get a symbol by name."""
        return self.symbols.get(name)


@pytest.fixture
def small_codebase():
    """Fixture for a small codebase."""
    return MockCodebase(size="small")


@pytest.fixture
def medium_codebase():
    """Fixture for a medium codebase."""
    return MockCodebase(size="medium")


@pytest.fixture
def large_codebase():
    """Fixture for a large codebase."""
    return MockCodebase(size="large")


class TestVisualizationPerformance:
    """Performance benchmark tests for visualization features."""

    @pytest.mark.benchmark(group="call_graph")
    def test_call_graph_small(self, small_codebase, benchmark):
        """Benchmark call graph visualization with small codebase."""
        config = VisualizationConfig(
            output_format=OutputFormat.JSON,
            max_depth=3,
        )
        visualizer = CodebaseVisualizer(config=config)
        
        # Benchmark the call graph generation
        result = benchmark(
            visualizer.generate_call_graph,
            "symbol0",
            small_codebase
        )
        
        # Verify the result
        assert result is not None
        assert len(visualizer.graph.nodes) > 0
        assert len(visualizer.graph.edges) > 0

    @pytest.mark.benchmark(group="call_graph")
    def test_call_graph_medium(self, medium_codebase, benchmark):
        """Benchmark call graph visualization with medium codebase."""
        config = VisualizationConfig(
            output_format=OutputFormat.JSON,
            max_depth=3,
        )
        visualizer = CodebaseVisualizer(config=config)
        
        # Benchmark the call graph generation
        result = benchmark(
            visualizer.generate_call_graph,
            "symbol0",
            medium_codebase
        )
        
        # Verify the result
        assert result is not None
        assert len(visualizer.graph.nodes) > 0
        assert len(visualizer.graph.edges) > 0

    @pytest.mark.benchmark(group="call_graph")
    def test_call_graph_large(self, large_codebase, benchmark):
        """Benchmark call graph visualization with large codebase."""
        config = VisualizationConfig(
            output_format=OutputFormat.JSON,
            max_depth=3,
        )
        visualizer = CodebaseVisualizer(config=config)
        
        # Benchmark the call graph generation
        result = benchmark(
            visualizer.generate_call_graph,
            "symbol0",
            large_codebase
        )
        
        # Verify the result
        assert result is not None
        assert len(visualizer.graph.nodes) > 0
        assert len(visualizer.graph.edges) > 0

    @pytest.mark.benchmark(group="dependency_graph")
    def test_dependency_graph_small(self, small_codebase, benchmark):
        """Benchmark dependency graph visualization with small codebase."""
        config = VisualizationConfig(
            output_format=OutputFormat.JSON,
            max_depth=3,
        )
        visualizer = CodebaseVisualizer(config=config)
        
        # Benchmark the dependency graph generation
        result = benchmark(
            visualizer.generate_dependency_graph,
            "symbol0",
            small_codebase
        )
        
        # Verify the result
        assert result is not None
        assert len(visualizer.graph.nodes) > 0
        assert len(visualizer.graph.edges) > 0

    @pytest.mark.benchmark(group="dependency_graph")
    def test_dependency_graph_medium(self, medium_codebase, benchmark):
        """Benchmark dependency graph visualization with medium codebase."""
        config = VisualizationConfig(
            output_format=OutputFormat.JSON,
            max_depth=3,
        )
        visualizer = CodebaseVisualizer(config=config)
        
        # Benchmark the dependency graph generation
        result = benchmark(
            visualizer.generate_dependency_graph,
            "symbol0",
            medium_codebase
        )
        
        # Verify the result
        assert result is not None
        assert len(visualizer.graph.nodes) > 0
        assert len(visualizer.graph.edges) > 0

    @pytest.mark.benchmark(group="dependency_graph")
    def test_dependency_graph_large(self, large_codebase, benchmark):
        """Benchmark dependency graph visualization with large codebase."""
        config = VisualizationConfig(
            output_format=OutputFormat.JSON,
            max_depth=3,
        )
        visualizer = CodebaseVisualizer(config=config)
        
        # Benchmark the dependency graph generation
        result = benchmark(
            visualizer.generate_dependency_graph,
            "symbol0",
            large_codebase
        )
        
        # Verify the result
        assert result is not None
        assert len(visualizer.graph.nodes) > 0
        assert len(visualizer.graph.edges) > 0

    @pytest.mark.benchmark(group="blast_radius")
    def test_blast_radius_small(self, small_codebase, benchmark):
        """Benchmark blast radius visualization with small codebase."""
        config = VisualizationConfig(
            output_format=OutputFormat.JSON,
            max_depth=3,
        )
        visualizer = CodebaseVisualizer(config=config)
        
        # Benchmark the blast radius generation
        result = benchmark(
            visualizer.generate_blast_radius,
            "symbol0",
            small_codebase
        )
        
        # Verify the result
        assert result is not None
        assert len(visualizer.graph.nodes) > 0
        assert len(visualizer.graph.edges) > 0

    @pytest.mark.benchmark(group="blast_radius")
    def test_blast_radius_medium(self, medium_codebase, benchmark):
        """Benchmark blast radius visualization with medium codebase."""
        config = VisualizationConfig(
            output_format=OutputFormat.JSON,
            max_depth=3,
        )
        visualizer = CodebaseVisualizer(config=config)
        
        # Benchmark the blast radius generation
        result = benchmark(
            visualizer.generate_blast_radius,
            "symbol0",
            medium_codebase
        )
        
        # Verify the result
        assert result is not None
        assert len(visualizer.graph.nodes) > 0
        assert len(visualizer.graph.edges) > 0

    @pytest.mark.benchmark(group="blast_radius")
    def test_blast_radius_large(self, large_codebase, benchmark):
        """Benchmark blast radius visualization with large codebase."""
        config = VisualizationConfig(
            output_format=OutputFormat.JSON,
            max_depth=3,
        )
        visualizer = CodebaseVisualizer(config=config)
        
        # Benchmark the blast radius generation
        result = benchmark(
            visualizer.generate_blast_radius,
            "symbol0",
            large_codebase
        )
        
        # Verify the result
        assert result is not None
        assert len(visualizer.graph.nodes) > 0
        assert len(visualizer.graph.edges) > 0

    @pytest.mark.benchmark(group="optimization")
    def test_depth_impact(self, medium_codebase, benchmark):
        """Benchmark the impact of depth parameter on performance."""
        # Test with different depth values
        depths = [1, 3, 5, 10]
        
        for depth in depths:
            config = VisualizationConfig(
                output_format=OutputFormat.JSON,
                max_depth=depth,
            )
            visualizer = CodebaseVisualizer(config=config)
            
            # Benchmark with specific depth
            result = benchmark.pedantic(
                visualizer.generate_call_graph,
                args=("symbol0", medium_codebase),
                rounds=3,
                iterations=1,
                name=f"call_graph_depth_{depth}"
            )
            
            # Verify the result
            assert result is not None

    @pytest.mark.benchmark(group="optimization")
    def test_filtering_impact(self, medium_codebase, benchmark):
        """Benchmark the impact of filtering on performance."""
        # Test with different filtering options
        configs = [
            {"ignore_external": True, "ignore_tests": True, "name": "both_filters"},
            {"ignore_external": True, "ignore_tests": False, "name": "ignore_external_only"},
            {"ignore_external": False, "ignore_tests": True, "name": "ignore_tests_only"},
            {"ignore_external": False, "ignore_tests": False, "name": "no_filters"},
        ]
        
        for config_opts in configs:
            name = config_opts.pop("name")
            config = VisualizationConfig(
                output_format=OutputFormat.JSON,
                max_depth=3,
                **config_opts
            )
            visualizer = CodebaseVisualizer(config=config)
            
            # Benchmark with specific filtering
            result = benchmark.pedantic(
                visualizer.generate_dependency_graph,
                args=("symbol0", medium_codebase),
                rounds=3,
                iterations=1,
                name=f"dependency_graph_{name}"
            )
            
            # Verify the result
            assert result is not None

    @pytest.mark.benchmark(group="output_format")
    def test_output_format_impact(self, small_codebase, benchmark):
        """Benchmark the impact of output format on performance."""
        # Test with different output formats
        formats = [
            OutputFormat.JSON,
            OutputFormat.PNG,
            OutputFormat.SVG,
            OutputFormat.DOT,
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            for output_format in formats:
                config = VisualizationConfig(
                    output_format=output_format,
                    output_directory=temp_dir,
                    max_depth=2,
                )
                visualizer = CodebaseVisualizer(config=config)
                
                # Benchmark with specific output format
                result = benchmark.pedantic(
                    visualizer.generate_call_graph,
                    args=("symbol0", small_codebase),
                    rounds=3,
                    iterations=1,
                    name=f"call_graph_{output_format.value}"
                )
                
                # Verify the result
                assert result is not None


if __name__ == "__main__":
    pytest.main(["-v", "--benchmark-save=visualization_benchmarks", __file__])

