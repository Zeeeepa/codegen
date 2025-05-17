# Visualization Test Implementation Details

This document provides detailed implementation plans for testing each visualization component in the Codegen repository.

## 1. Base Visualizer Tests

### Test File: `tests/unit/visualizations/test_base_visualizer.py`

#### Test Cases:

1. **Initialization Tests**
   - Test initialization with default parameters
   - Test initialization with custom configuration
   - Test initialization with output directory

2. **Graph Manipulation Tests**
   - Test graph initialization
   - Test node addition with various attributes
   - Test edge addition with various attributes
   - Test node and edge retrieval

3. **Output Format Tests**
   - Test JSON output generation
   - Test PNG output generation
   - Test SVG output generation
   - Test HTML output generation
   - Test DOT output generation

4. **Filename Generation Tests**
   - Test filename generation with different visualization types
   - Test filename sanitization for special characters

5. **Error Handling Tests**
   - Test handling of invalid configuration
   - Test handling of missing dependencies

## 2. Codebase Visualizer Tests

### Test File: `tests/unit/visualizations/test_codebase_visualizer.py`

#### Test Cases:

1. **Initialization Tests**
   - Test initialization with different codebase types
   - Test initialization with analyzer integration

2. **Call Graph Tests**
   - Test call graph generation for simple function
   - Test call graph with recursive functions
   - Test call graph with external dependencies
   - Test call graph with depth limitations

3. **Dependency Graph Tests**
   - Test dependency graph for simple module
   - Test dependency graph with circular dependencies
   - Test dependency graph with external imports
   - Test dependency graph with depth limitations

4. **Blast Radius Tests**
   - Test blast radius for function with few usages
   - Test blast radius for widely used function
   - Test blast radius with depth limitations

5. **Class Methods Tests**
   - Test class methods visualization for simple class
   - Test class methods with inheritance
   - Test class methods with complex relationships

6. **Module Dependencies Tests**
   - Test module dependencies for simple project
   - Test module dependencies with circular imports
   - Test module dependencies with external packages

7. **Dead Code Tests**
   - Test dead code visualization with unused functions
   - Test dead code with partially used classes
   - Test dead code detection accuracy

8. **Complexity Tests**
   - Test complexity visualization for simple codebase
   - Test complexity with highly complex functions
   - Test complexity heatmap generation

9. **Issues Heatmap Tests**
   - Test issues heatmap with various issue types
   - Test issues heatmap with severity levels
   - Test issues clustering visualization

10. **PR Comparison Tests**
    - Test PR visualization with simple changes
    - Test PR visualization with complex changes
    - Test PR visualization with conflicts

## 3. Visualization Utilities Tests

### Test File: `tests/unit/visualizations/test_visualization_utils.py`

#### Test Cases:

1. **Graph Conversion Tests**
   - Test NetworkX graph to JSON conversion
   - Test tree data conversion
   - Test node link data conversion

2. **Node Handling Tests**
   - Test node ID generation for different types
   - Test node options extraction
   - Test node attribute handling

3. **Visualization Manager Tests**
   - Test visualization path management
   - Test graph data writing
   - Test graph data clearing

## 4. Cross-Language Compatibility Tests

### Test File: `tests/integration/visualizations/test_cross_language.py`

#### Test Cases:

1. **Python Visualization Tests**
   - Test Python-specific features visualization
   - Test Python decorator visualization
   - Test Python dynamic import visualization

2. **TypeScript Visualization Tests**
   - Test TypeScript-specific features visualization
   - Test TypeScript interface visualization
   - Test TypeScript type definition visualization

3. **Mixed Language Tests**
   - Test Python-TypeScript interaction visualization
   - Test consistent representation across languages

## 5. Performance Benchmark Tests

### Test File: `tests/benchmarks/visualizations/test_visualization_performance.py`

#### Test Cases:

1. **Small Codebase Benchmarks**
   - Benchmark each visualization type with small codebase
   - Measure memory usage during visualization

2. **Medium Codebase Benchmarks**
   - Benchmark each visualization type with medium codebase
   - Identify performance scaling factors

3. **Large Codebase Benchmarks**
   - Benchmark each visualization type with large codebase
   - Test optimization techniques effectiveness

4. **Optimization Tests**
   - Test caching impact on performance
   - Test filtering impact on performance
   - Test lazy loading impact on performance

## 6. UI/UX Tests

### Test File: `tests/integration/visualizations/test_visualization_ui.py`

#### Test Cases:

1. **Interactive Feature Tests**
   - Test node selection functionality
   - Test graph navigation (zoom, pan)
   - Test search and filter features
   - Test information display features

2. **Browser Compatibility Tests**
   - Test visualization in Chrome
   - Test visualization in Firefox
   - Test visualization in Safari
   - Test visualization in Edge

3. **Accessibility Tests**
   - Test keyboard navigation
   - Test screen reader compatibility
   - Test color contrast compliance

## 7. Edge Case Tests

### Test File: `tests/unit/visualizations/test_visualization_edge_cases.py`

#### Test Cases:

1. **Empty Input Tests**
   - Test visualization with empty codebase
   - Test visualization with empty module
   - Test visualization with empty class

2. **Complex Structure Tests**
   - Test with deeply nested code structures
   - Test with circular dependencies
   - Test with unusual naming patterns

3. **Error Handling Tests**
   - Test with malformed inputs
   - Test with missing dependencies
   - Test with invalid configuration

## 8. Sample Test Code

### Example: Base Visualizer Test

```python
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from codegen_on_oss.analyzers.visualization.visualizer import (
    BaseVisualizer,
    VisualizationConfig,
    VisualizationType,
    OutputFormat,
)

class TestBaseVisualizer:
    def test_initialization_default(self):
        """Test initializing visualizer with default configuration."""
        visualizer = BaseVisualizer()
        assert visualizer.config is not None
        assert visualizer.config.max_depth == 5
        assert visualizer.config.output_format == OutputFormat.JSON

    def test_initialization_custom(self):
        """Test initializing visualizer with custom configuration."""
        config = VisualizationConfig(
            max_depth=10,
            output_format=OutputFormat.PNG,
            ignore_tests=False,
        )
        visualizer = BaseVisualizer(config=config)
        assert visualizer.config.max_depth == 10
        assert visualizer.config.output_format == OutputFormat.PNG
        assert visualizer.config.ignore_tests is False

    def test_add_node(self):
        """Test adding a node to the graph."""
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

    def test_add_edge(self):
        """Test adding an edge to the graph."""
        visualizer = BaseVisualizer()
        
        # Create mock nodes
        source_node = MagicMock()
        source_node.name = "source"
        target_node = MagicMock()
        target_node.name = "target"
        
        # Add nodes and edge
        source_id = visualizer._add_node(source_node)
        target_id = visualizer._add_node(target_node)
        visualizer._add_edge(source_node, target_node, weight=2)
        
        # Verify the edge was added correctly
        assert visualizer.graph.has_edge(source_id, target_id)
        edge_attrs = visualizer.graph.edges[source_id, target_id]
        assert edge_attrs["weight"] == 2

    def test_generate_filename(self):
        """Test filename generation for visualization."""
        visualizer = BaseVisualizer()
        filename = visualizer._generate_filename(
            VisualizationType.CALL_GRAPH, "test/function"
        )
        
        # Verify filename format
        assert filename.startswith("call_graph_test_function_")
        assert filename.endswith(".json")

    @patch("matplotlib.pyplot.savefig")
    def test_save_visualization_png(self, mock_savefig):
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
            assert os.path.dirname(filepath) == temp_dir
            assert filepath.endswith(".png")
```

### Example: Call Graph Visualization Test

```python
import pytest
from unittest.mock import patch, MagicMock

from codegen_on_oss.analyzers.visualization.code_visualizer import CodeVisualizer
from codegen_on_oss.analyzers.visualization.visualizer import (
    VisualizationConfig,
    VisualizationType,
    OutputFormat,
)

class TestCallGraphVisualization:
    @pytest.fixture
    def mock_codebase(self):
        """Create a mock codebase with functions for testing."""
        codebase = MagicMock()
        
        # Create mock functions
        main_func = MagicMock()
        main_func.name = "main"
        main_func.filepath = "main.py"
        
        helper_func = MagicMock()
        helper_func.name = "helper"
        helper_func.filepath = "utils.py"
        
        # Set up function calls
        main_func.function_calls = [MagicMock(function_definition=helper_func)]
        helper_func.function_calls = []
        
        # Configure codebase to return our functions
        codebase.get_function.side_effect = lambda name: {
            "main": main_func,
            "helper": helper_func,
        }.get(name)
        
        return codebase, main_func, helper_func

    def test_call_graph_generation(self, mock_codebase):
        """Test generating a call graph visualization."""
        codebase, main_func, helper_func = mock_codebase
        
        # Create visualizer
        config = VisualizationConfig(output_format=OutputFormat.JSON)
        visualizer = CodeVisualizer(config=config)
        
        # Generate call graph
        result = visualizer.generate_call_graph("main", codebase)
        
        # Verify graph structure
        assert len(visualizer.graph.nodes) == 2  # main and helper
        assert len(visualizer.graph.edges) == 1  # main -> helper
        
        # Verify node attributes
        nodes = list(visualizer.graph.nodes(data=True))
        assert any(attr.get("name") == "main" for _, attr in nodes)
        assert any(attr.get("name") == "helper" for _, attr in nodes)
        
        # Verify edge exists
        main_id = id(main_func)
        helper_id = id(helper_func)
        assert visualizer.graph.has_edge(main_id, helper_id)

    def test_call_graph_depth_limit(self, mock_codebase):
        """Test call graph respects depth limit."""
        codebase, main_func, helper_func = mock_codebase
        
        # Create deep call chain
        deep_func = MagicMock()
        deep_func.name = "deep"
        deep_func.filepath = "deep.py"
        deep_func.function_calls = []
        
        # main -> helper -> deep
        helper_func.function_calls = [MagicMock(function_definition=deep_func)]
        
        # Configure codebase to return our functions
        codebase.get_function.side_effect = lambda name: {
            "main": main_func,
            "helper": helper_func,
            "deep": deep_func,
        }.get(name)
        
        # Create visualizer with depth=1
        config = VisualizationConfig(max_depth=1, output_format=OutputFormat.JSON)
        visualizer = CodeVisualizer(config=config)
        
        # Generate call graph
        result = visualizer.generate_call_graph("main", codebase)
        
        # Verify graph structure - should only include main and helper, not deep
        assert len(visualizer.graph.nodes) == 2
        assert len(visualizer.graph.edges) == 1
```

## 9. Test Data Requirements

For effective testing, we need the following test data:

1. **Small Test Codebase**
   - Simple Python project with clear function calls
   - Simple TypeScript project with interfaces and classes
   - Mixed language project with Python-TypeScript interaction

2. **Medium Test Codebase**
   - Open-source project with moderate complexity
   - Project with various dependency patterns
   - Project with multiple modules and packages

3. **Large Test Codebase**
   - Complex open-source project
   - Project with deep call hierarchies
   - Project with extensive cross-module dependencies

4. **Edge Case Test Data**
   - Project with circular dependencies
   - Project with unusual code patterns
   - Project with mixed language features

## 10. Test Execution Strategy

1. **Unit Tests**: Run first to validate basic functionality
2. **Integration Tests**: Run after unit tests pass
3. **Performance Tests**: Run on dedicated hardware for consistent results
4. **UI Tests**: Run in multiple browser environments

## 11. Test Reporting

1. **Test Coverage Report**: Generate coverage report for visualization code
2. **Performance Benchmark Report**: Generate performance comparison charts
3. **Bug Report Template**: Standard format for reporting visualization issues
4. **Test Summary Dashboard**: Overview of all test results

