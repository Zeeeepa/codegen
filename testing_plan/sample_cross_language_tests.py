#!/usr/bin/env python3
"""
Cross-language compatibility tests for visualization features.

This module contains tests to validate that visualization features work correctly
across different programming languages (Python, TypeScript, etc.).
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


class MockPythonSymbol:
    """Mock Python Symbol class for testing."""
    
    def __init__(self, name, filepath, symbol_type="Function"):
        self.name = name
        self.filepath = filepath
        self.symbol_type = symbol_type
        self.language = "python"
        self.function_calls = []
        self.dependencies = []
        self.usages = []
        self.methods = []
        self.imports = []
        self.viz = MagicMock()
        self.viz.name = name
        self.viz.color = "#3572A5"  # Python blue


class MockTypeScriptSymbol:
    """Mock TypeScript Symbol class for testing."""
    
    def __init__(self, name, filepath, symbol_type="Function"):
        self.name = name
        self.filepath = filepath
        self.symbol_type = symbol_type
        self.language = "typescript"
        self.function_calls = []
        self.dependencies = []
        self.usages = []
        self.methods = []
        self.imports = []
        self.viz = MagicMock()
        self.viz.name = name
        self.viz.color = "#2b7489"  # TypeScript blue


class MockMixedLanguageCodebase:
    """Mock Codebase with mixed language symbols for testing."""
    
    def __init__(self):
        self.files = []
        self.symbols = {}
        self._setup_codebase()
    
    def _setup_codebase(self):
        """Set up a mixed language codebase with Python and TypeScript files."""
        # Create Python files
        for i in range(5):
            file = MagicMock()
            file.filepath = f"src/python/module{i}.py"
            file.language = "python"
            self.files.append(file)
        
        # Create TypeScript files
        for i in range(5):
            file = MagicMock()
            file.filepath = f"src/typescript/module{i}.ts"
            file.language = "typescript"
            self.files.append(file)
        
        # Create Python symbols
        for i in range(25):
            file_idx = i % 5
            symbol = MockPythonSymbol(
                name=f"py_symbol{i}",
                filepath=f"src/python/module{file_idx}.py",
                symbol_type="Function" if i % 3 == 0 else "Class" if i % 3 == 1 else "Variable"
            )
            self.symbols[symbol.name] = symbol
        
        # Create TypeScript symbols
        for i in range(25):
            file_idx = i % 5
            symbol = MockTypeScriptSymbol(
                name=f"ts_symbol{i}",
                filepath=f"src/typescript/module{file_idx}.ts",
                symbol_type="Function" if i % 3 == 0 else "Class" if i % 3 == 1 else "Interface" if i % 3 == 2 else "Variable"
            )
            self.symbols[symbol.name] = symbol
        
        # Create Python-to-Python relationships
        for i in range(25):
            symbol = self.symbols[f"py_symbol{i}"]
            
            # Add function calls
            if i % 3 == 0:  # Functions
                for j in range(1, 4):
                    if f"py_symbol{(i+j) % 25}" in self.symbols:
                        call = MagicMock()
                        call.function_definition = self.symbols[f"py_symbol{(i+j) % 25}"]
                        symbol.function_calls.append(call)
            
            # Add dependencies
            for j in range(1, 3):
                if f"py_symbol{(i+j*5) % 25}" in self.symbols:
                    symbol.dependencies.append(self.symbols[f"py_symbol{(i+j*5) % 25}"])
        
        # Create TypeScript-to-TypeScript relationships
        for i in range(25):
            symbol = self.symbols[f"ts_symbol{i}"]
            
            # Add function calls
            if i % 3 == 0:  # Functions
                for j in range(1, 4):
                    if f"ts_symbol{(i+j) % 25}" in self.symbols:
                        call = MagicMock()
                        call.function_definition = self.symbols[f"ts_symbol{(i+j) % 25}"]
                        symbol.function_calls.append(call)
            
            # Add dependencies
            for j in range(1, 3):
                if f"ts_symbol{(i+j*5) % 25}" in self.symbols:
                    symbol.dependencies.append(self.symbols[f"ts_symbol{(i+j*5) % 25}"])
        
        # Create cross-language relationships (Python -> TypeScript)
        for i in range(0, 25, 5):  # Every 5th Python symbol
            symbol = self.symbols[f"py_symbol{i}"]
            
            # Add TypeScript dependencies
            for j in range(0, 25, 5):  # Every 5th TypeScript symbol
                if f"ts_symbol{j}" in self.symbols:
                    symbol.dependencies.append(self.symbols[f"ts_symbol{j}"])
                    
                    # Add usage relationship (TypeScript -> Python)
                    ts_symbol = self.symbols[f"ts_symbol{j}"]
                    usage = MagicMock()
                    usage.usage_symbol = symbol
                    usage.match = MagicMock()
                    usage.match.source = f"Using py_symbol{i}"
                    usage.match.filepath = f"src/typescript/module{j % 5}.ts"
                    usage.match.start_point = (1, 1)
                    usage.match.end_point = (1, 10)
                    ts_symbol.usages.append(usage)
    
    def get_function(self, name):
        """Get a function by name."""
        if name in self.symbols and self.symbols[name].symbol_type == "Function":
            return self.symbols[name]
        return None
    
    def get_class(self, name):
        """Get a class by name."""
        if name in self.symbols and self.symbols[name].symbol_type in ["Class", "Interface"]:
            return self.symbols[name]
        return None
    
    def get_symbol(self, name):
        """Get a symbol by name."""
        return self.symbols.get(name)


@pytest.fixture
def mixed_language_codebase():
    """Fixture for a mixed language codebase."""
    return MockMixedLanguageCodebase()


class TestCrossLanguageCompatibility:
    """Cross-language compatibility tests for visualization features."""

    def test_call_graph_python(self, mixed_language_codebase):
        """Test call graph visualization with Python symbols."""
        config = VisualizationConfig(
            output_format=OutputFormat.JSON,
            max_depth=3,
        )
        visualizer = CodebaseVisualizer(config=config)
        
        # Generate call graph for Python function
        result = visualizer.generate_call_graph(
            "py_symbol0",
            mixed_language_codebase
        )
        
        # Verify the result
        assert result is not None
        
        # Convert graph to JSON for analysis
        graph_json = visualizer._convert_graph_to_json()
        
        # Verify Python nodes are present
        python_nodes = [
            node for node in graph_json["nodes"]
            if "py_symbol" in node["name"]
        ]
        assert len(python_nodes) > 0
        
        # Verify Python function calls are represented
        assert len(graph_json["edges"]) > 0

    def test_call_graph_typescript(self, mixed_language_codebase):
        """Test call graph visualization with TypeScript symbols."""
        config = VisualizationConfig(
            output_format=OutputFormat.JSON,
            max_depth=3,
        )
        visualizer = CodebaseVisualizer(config=config)
        
        # Generate call graph for TypeScript function
        result = visualizer.generate_call_graph(
            "ts_symbol0",
            mixed_language_codebase
        )
        
        # Verify the result
        assert result is not None
        
        # Convert graph to JSON for analysis
        graph_json = visualizer._convert_graph_to_json()
        
        # Verify TypeScript nodes are present
        typescript_nodes = [
            node for node in graph_json["nodes"]
            if "ts_symbol" in node["name"]
        ]
        assert len(typescript_nodes) > 0
        
        # Verify TypeScript function calls are represented
        assert len(graph_json["edges"]) > 0

    def test_dependency_graph_cross_language(self, mixed_language_codebase):
        """Test dependency graph visualization with cross-language dependencies."""
        config = VisualizationConfig(
            output_format=OutputFormat.JSON,
            max_depth=3,
        )
        visualizer = CodebaseVisualizer(config=config)
        
        # Generate dependency graph for Python function with TypeScript dependencies
        result = visualizer.generate_dependency_graph(
            "py_symbol0",
            mixed_language_codebase
        )
        
        # Verify the result
        assert result is not None
        
        # Convert graph to JSON for analysis
        graph_json = visualizer._convert_graph_to_json()
        
        # Verify both Python and TypeScript nodes are present
        python_nodes = [
            node for node in graph_json["nodes"]
            if "py_symbol" in node["name"]
        ]
        typescript_nodes = [
            node for node in graph_json["nodes"]
            if "ts_symbol" in node["name"]
        ]
        
        assert len(python_nodes) > 0
        assert len(typescript_nodes) > 0
        
        # Verify cross-language edges exist
        cross_language_edges = []
        for edge in graph_json["edges"]:
            source_node = next(
                (node for node in graph_json["nodes"] if node["id"] == edge["source"]),
                None
            )
            target_node = next(
                (node for node in graph_json["nodes"] if node["id"] == edge["target"]),
                None
            )
            
            if (source_node and target_node and
                ("py_symbol" in source_node["name"] and "ts_symbol" in target_node["name"]) or
                ("ts_symbol" in source_node["name"] and "py_symbol" in target_node["name"])):
                cross_language_edges.append(edge)
        
        assert len(cross_language_edges) > 0

    def test_blast_radius_cross_language(self, mixed_language_codebase):
        """Test blast radius visualization with cross-language usages."""
        config = VisualizationConfig(
            output_format=OutputFormat.JSON,
            max_depth=3,
        )
        visualizer = CodebaseVisualizer(config=config)
        
        # Generate blast radius for TypeScript symbol that uses Python symbols
        result = visualizer.generate_blast_radius(
            "ts_symbol0",
            mixed_language_codebase
        )
        
        # Verify the result
        assert result is not None
        
        # Convert graph to JSON for analysis
        graph_json = visualizer._convert_graph_to_json()
        
        # Verify both TypeScript and Python nodes are present
        typescript_nodes = [
            node for node in graph_json["nodes"]
            if "ts_symbol" in node["name"]
        ]
        python_nodes = [
            node for node in graph_json["nodes"]
            if "py_symbol" in node["name"]
        ]
        
        assert len(typescript_nodes) > 0
        assert len(python_nodes) > 0
        
        # Verify cross-language usage edges exist
        cross_language_edges = []
        for edge in graph_json["edges"]:
            source_node = next(
                (node for node in graph_json["nodes"] if node["id"] == edge["source"]),
                None
            )
            target_node = next(
                (node for node in graph_json["nodes"] if node["id"] == edge["target"]),
                None
            )
            
            if (source_node and target_node and
                ("ts_symbol" in source_node["name"] and "py_symbol" in target_node["name"])):
                cross_language_edges.append(edge)
        
        assert len(cross_language_edges) > 0

    def test_typescript_specific_features(self, mixed_language_codebase):
        """Test visualization of TypeScript-specific features."""
        # Add TypeScript-specific features to the codebase
        
        # Add an interface
        interface = MockTypeScriptSymbol(
            name="IUserService",
            filepath="src/typescript/interfaces.ts",
            symbol_type="Interface"
        )
        mixed_language_codebase.symbols[interface.name] = interface
        
        # Add a class implementing the interface
        impl_class = MockTypeScriptSymbol(
            name="UserService",
            filepath="src/typescript/services.ts",
            symbol_type="Class"
        )
        mixed_language_codebase.symbols[impl_class.name] = impl_class
        
        # Add implementation relationship
        impl_class.dependencies.append(interface)
        
        # Add a type definition
        type_def = MockTypeScriptSymbol(
            name="UserType",
            filepath="src/typescript/types.ts",
            symbol_type="TypeAlias"
        )
        mixed_language_codebase.symbols[type_def.name] = type_def
        
        # Add usage of type definition
        impl_class.dependencies.append(type_def)
        
        # Configure visualizer
        config = VisualizationConfig(
            output_format=OutputFormat.JSON,
            max_depth=3,
        )
        visualizer = CodebaseVisualizer(config=config)
        
        # Generate dependency graph for the implementation class
        result = visualizer.generate_dependency_graph(
            "UserService",
            mixed_language_codebase
        )
        
        # Verify the result
        assert result is not None
        
        # Convert graph to JSON for analysis
        graph_json = visualizer._convert_graph_to_json()
        
        # Verify TypeScript-specific nodes are present
        interface_nodes = [
            node for node in graph_json["nodes"]
            if node["name"] == "IUserService"
        ]
        type_nodes = [
            node for node in graph_json["nodes"]
            if node["name"] == "UserType"
        ]
        
        assert len(interface_nodes) > 0
        assert len(type_nodes) > 0
        
        # Verify implementation relationship is represented
        impl_edges = []
        for edge in graph_json["edges"]:
            source_node = next(
                (node for node in graph_json["nodes"] if node["id"] == edge["source"]),
                None
            )
            target_node = next(
                (node for node in graph_json["nodes"] if node["id"] == edge["target"]),
                None
            )
            
            if (source_node and target_node and
                source_node["name"] == "UserService" and target_node["name"] == "IUserService"):
                impl_edges.append(edge)
        
        assert len(impl_edges) > 0

    def test_python_specific_features(self, mixed_language_codebase):
        """Test visualization of Python-specific features."""
        # Add Python-specific features to the codebase
        
        # Add a decorated function
        decorated_func = MockPythonSymbol(
            name="decorated_function",
            filepath="src/python/decorators.py",
            symbol_type="Function"
        )
        mixed_language_codebase.symbols[decorated_func.name] = decorated_func
        
        # Add a decorator
        decorator = MockPythonSymbol(
            name="route_decorator",
            filepath="src/python/decorators.py",
            symbol_type="Function"
        )
        mixed_language_codebase.symbols[decorator.name] = decorator
        
        # Add decorator relationship
        decorated_func.dependencies.append(decorator)
        
        # Add a dynamic import
        dynamic_import = MockPythonSymbol(
            name="dynamic_import",
            filepath="src/python/dynamic.py",
            symbol_type="Import"
        )
        mixed_language_codebase.symbols[dynamic_import.name] = dynamic_import
        
        # Add usage of dynamic import
        decorated_func.dependencies.append(dynamic_import)
        
        # Configure visualizer
        config = VisualizationConfig(
            output_format=OutputFormat.JSON,
            max_depth=3,
        )
        visualizer = CodebaseVisualizer(config=config)
        
        # Generate dependency graph for the decorated function
        result = visualizer.generate_dependency_graph(
            "decorated_function",
            mixed_language_codebase
        )
        
        # Verify the result
        assert result is not None
        
        # Convert graph to JSON for analysis
        graph_json = visualizer._convert_graph_to_json()
        
        # Verify Python-specific nodes are present
        decorator_nodes = [
            node for node in graph_json["nodes"]
            if node["name"] == "route_decorator"
        ]
        import_nodes = [
            node for node in graph_json["nodes"]
            if node["name"] == "dynamic_import"
        ]
        
        assert len(decorator_nodes) > 0
        assert len(import_nodes) > 0
        
        # Verify decorator relationship is represented
        decorator_edges = []
        for edge in graph_json["edges"]:
            source_node = next(
                (node for node in graph_json["nodes"] if node["id"] == edge["source"]),
                None
            )
            target_node = next(
                (node for node in graph_json["nodes"] if node["id"] == edge["target"]),
                None
            )
            
            if (source_node and target_node and
                source_node["name"] == "decorated_function" and target_node["name"] == "route_decorator"):
                decorator_edges.append(edge)
        
        assert len(decorator_edges) > 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])

