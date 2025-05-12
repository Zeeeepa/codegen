# Code Visualization Tools

This directory contains tools for visualizing various aspects of codebases, including:

- Code structure (call graphs, dependency graphs, etc.)
- Code quality (dead code, complexity, etc.)
- Analysis results (issues, PR comparisons, etc.)

## Visualization Types

### Call Graph Visualizations

1. **Basic Call Graph**: Visualize function calls starting from a specific function
   ```python
   visualizer.visualize_call_graph(function_name="main", max_depth=3)
   ```

2. **Call Graph From Node**: Enhanced call graph visualization with more detailed tracing
   ```python
   visualizer.visualize_call_graph_from_node(
       function_name="main", 
       max_depth=3,
       graph_external_modules=False
   )
   ```

3. **Filtered Call Graph**: Visualize call graph with filtering by method names
   ```python
   visualizer.visualize_call_graph_filter(
       class_name="MyClass",
       method_filters=["get", "post", "patch", "delete"],
       skip_test_files=True
   )
   ```

4. **Call Paths Between Nodes**: Visualize all paths between two functions
   ```python
   visualizer.visualize_call_paths_between_nodes(
       start_func_name="start_func",
       end_func_name="end_func"
   )
   ```

### Code Quality Visualizations

1. **Dead Code**: Visualize unused code in the codebase
   ```python
   visualizer.visualize_dead_code(path_filter="src/")
   ```

2. **Dead Code Graph**: Enhanced dead code visualization with dependency tracking
   ```python
   visualizer.visualize_dead_code_graph(
       skip_test_files=True,
       skip_decorated=True
   )
   ```

3. **Cyclomatic Complexity**: Visualize code complexity
   ```python
   visualizer.visualize_cyclomatic_complexity(path_filter="src/")
   ```

### Other Visualizations

1. **Dependency Graph**: Visualize dependencies between symbols
   ```python
   visualizer.visualize_dependency_graph(symbol_name="MyClass")
   ```

2. **Blast Radius**: Visualize the impact of changing a symbol
   ```python
   visualizer.visualize_blast_radius(symbol_name="important_function")
   ```

3. **Class Methods**: Visualize methods in a class and their relationships
   ```python
   visualizer.visualize_class_methods(class_name="MyClass")
   ```

4. **Module Dependencies**: Visualize dependencies between modules
   ```python
   visualizer.visualize_module_dependencies(module_path="src/module/")
   ```

5. **Issues Heatmap**: Visualize issues in the codebase
   ```python
   visualizer.visualize_issues_heatmap(severity="error")
   ```

6. **PR Comparison**: Visualize changes in a pull request
   ```python
   visualizer.visualize_pr_comparison()
   ```

## Configuration

You can configure the visualization output format, colors, and other options:

```python
from codegen_on_oss.analyzers.visualization.visualizer import VisualizationConfig, OutputFormat

config = VisualizationConfig(
    output_format=OutputFormat.PNG,  # Options: JSON, PNG, SVG, HTML, DOT
    output_directory="visualization_output",
    max_depth=5,
    ignore_external=True,
    ignore_tests=True,
    layout_algorithm="spring",  # Options: spring, kamada_kawai, spectral
)

visualizer = CodebaseVisualizer(config=config)
```

## Examples

See the `examples/visualization_examples.py` file for complete examples of using these visualization tools.

