# Codegen Enhanced Visualization Features

This document provides comprehensive documentation for the enhanced visualization features in the Codegen repository.

## Overview

Codegen provides powerful visualization capabilities to help developers understand code structure, relationships, and dependencies. The enhanced visualization features include:

1. **Inheritance Hierarchy Visualization**: Visualize class inheritance hierarchies
2. **Call Graph Visualization**: Visualize function call relationships
3. **Dependency Graph Visualization**: Visualize symbol dependencies
4. **Module Dependency Visualization**: Visualize module/file dependencies
5. **Interactive Selection UI**: Select and view related code elements

## Visualization Types

### Inheritance Hierarchy Visualization

The inheritance hierarchy visualization shows the inheritance relationships between classes. It displays parent and child classes in a hierarchical structure, making it easy to understand class inheritance patterns.

```python
from codegen import Codebase
from codegen.visualizations.visualization_manager import VisualizationManager

# Initialize codebase
codebase = Codebase.from_repo("owner/repo")

# Get the visualization manager
viz_manager = codebase.viz_manager

# Get a class
my_class = codebase.get_class("MyClass")

# Visualize the inheritance hierarchy
viz_manager.visualize_inheritance_hierarchy(my_class, max_depth=3)
```

### Call Graph Visualization

The call graph visualization shows the relationships between functions and methods based on function calls. It displays which functions call which other functions, making it easy to understand the flow of execution in the codebase.

```python
from codegen import Codebase
from codegen.visualizations.visualization_manager import VisualizationManager

# Initialize codebase
codebase = Codebase.from_repo("owner/repo")

# Get the visualization manager
viz_manager = codebase.viz_manager

# Get a function
my_function = codebase.get_function("my_function")

# Visualize the call graph
viz_manager.visualize_call_graph(my_function, max_depth=3, include_external=False)
```

### Dependency Graph Visualization

The dependency graph visualization shows the dependencies between symbols (functions, classes, variables). It displays which symbols depend on which other symbols, making it easy to understand the impact of changes to a symbol.

```python
from codegen import Codebase
from codegen.visualizations.visualization_manager import VisualizationManager

# Initialize codebase
codebase = Codebase.from_repo("owner/repo")

# Get the visualization manager
viz_manager = codebase.viz_manager

# Get a symbol
my_symbol = codebase.get_symbol("my_symbol")

# Visualize the dependency graph
viz_manager.visualize_dependency_graph(my_symbol, max_depth=3, include_external=False)
```

### Module Dependency Visualization

The module dependency visualization shows the dependencies between modules/files based on imports. It displays which files import which other files, making it easy to understand the structure of the codebase.

```python
from codegen import Codebase
from codegen.visualizations.visualization_manager import VisualizationManager

# Initialize codebase
codebase = Codebase.from_repo("owner/repo")

# Get the visualization manager
viz_manager = codebase.viz_manager

# Get a file
my_file = codebase.get_file("path/to/file.py")

# Visualize the module dependencies
viz_manager.visualize_module_dependencies(my_file, max_depth=3, include_external=False)
```

## Interactive Selection UI

The interactive selection UI allows users to select and view related code elements. When a code element is selected, the UI displays a second row with related elements, such as methods for a class, or dependencies for a symbol.

The selection UI is available in the web interface when viewing visualizations. To use it:

1. Click on a node in the visualization to select it
2. The second row will display related elements
3. Click on a related element to navigate to it

## Customization Options

### Visualization Depth

All visualization methods accept a `max_depth` parameter that controls how deep the visualization should go. For example, a `max_depth` of 3 for a call graph will show function calls up to 3 levels deep.

### External Dependencies

All visualization methods accept an `include_external` parameter that controls whether external dependencies (from imported modules) should be included in the visualization.

### Node Styling

Nodes in the visualization can be styled using the `VizNode` class. This allows customizing the appearance of nodes, such as color, shape, and text.

```python
from codegen.visualizations.enums import VizNode

# Create a custom VizNode
viz_node = VizNode(
    name="MyNode",
    color="#ff0000",
    shape="circle",
    text="My custom node",
    emoji="🚀"
)

# Use the VizNode in a visualization
# (Implementation depends on the specific visualization)
```

## Advanced Usage

### Custom Visualizations

You can create custom visualizations by using the `write_graphviz_data` method directly:

```python
import networkx as nx
from codegen import Codebase
from codegen.visualizations.visualization_manager import VisualizationManager
from codegen.visualizations.enums import GraphType

# Initialize codebase
codebase = Codebase.from_repo("owner/repo")

# Get the visualization manager
viz_manager = codebase.viz_manager

# Create a custom graph
G = nx.DiGraph()
G.add_node("A", name="Node A", color="#ff0000")
G.add_node("B", name="Node B", color="#00ff00")
G.add_edge("A", "B", type="custom_edge")

# Write the graph data
viz_manager.write_graphviz_data(G, graph_type=GraphType.GRAPH)
```

### Combining Visualizations

You can combine multiple visualizations by creating a custom graph and adding nodes and edges from different visualization types:

```python
import networkx as nx
from codegen import Codebase
from codegen.visualizations.visualization_manager import VisualizationManager
from codegen.visualizations.viz_utils import create_call_graph, create_dependency_graph
from codegen.visualizations.enums import GraphType

# Initialize codebase
codebase = Codebase.from_repo("owner/repo")

# Get the visualization manager
viz_manager = codebase.viz_manager

# Get a function and a symbol
my_function = codebase.get_function("my_function")
my_symbol = codebase.get_symbol("my_symbol")

# Create individual graphs
call_graph = create_call_graph(my_function)
dependency_graph = create_dependency_graph(my_symbol)

# Combine the graphs
combined_graph = nx.compose(call_graph, dependency_graph)

# Write the combined graph data
viz_manager.write_graphviz_data(combined_graph, graph_type=GraphType.GRAPH)
```

## Performance Considerations

Visualizing large codebases can be resource-intensive. Here are some tips for improving performance:

1. **Limit Visualization Depth**: Use a smaller `max_depth` value to limit the size of the visualization.
2. **Exclude External Dependencies**: Set `include_external=False` to exclude external dependencies from the visualization.
3. **Filter Nodes**: Use filtering options to focus on specific parts of the codebase.
4. **Use Pagination**: For large visualizations, consider paginating the results.

## Troubleshooting

### Common Issues

1. **Visualization is too large**: Reduce the `max_depth` parameter or filter the visualization.
2. **Missing nodes or edges**: Check that the code elements exist in the codebase and are properly linked.
3. **Performance issues**: Follow the performance considerations above.

### Error Messages

- **"Node not found"**: The specified node does not exist in the codebase.
- **"Graph too large"**: The visualization is too large to render. Try reducing the `max_depth` parameter.
- **"Invalid graph type"**: The specified graph type is not supported. Use one of the predefined `GraphType` values.

## API Reference

### VisualizationManager

The `VisualizationManager` class provides methods for creating and managing visualizations.

#### Methods

- `write_graphviz_data(G, root=None, graph_type=None)`: Write graph data to a file.
- `visualize_inheritance_hierarchy(class_obj, max_depth=3)`: Visualize the inheritance hierarchy of a class.
- `visualize_call_graph(function, max_depth=3, include_external=False)`: Visualize the call graph of a function.
- `visualize_dependency_graph(symbol, max_depth=3, include_external=False)`: Visualize the dependency graph of a symbol.
- `visualize_module_dependencies(file_obj, max_depth=3, include_external=False)`: Visualize the module dependencies of a file.

### Visualization Utilities

The `viz_utils` module provides utility functions for creating visualizations.

#### Functions

- `create_inheritance_graph(class_obj, max_depth=3)`: Create an inheritance graph for a class.
- `create_call_graph(function, max_depth=3, include_external=False)`: Create a call graph for a function.
- `create_dependency_graph(symbol, max_depth=3, include_external=False)`: Create a dependency graph for a symbol.
- `create_module_dependency_graph(file_obj, max_depth=3, include_external=False)`: Create a module dependency graph for a file.
- `graph_to_json(G, root=None, graph_type=None)`: Convert a graph to JSON format.

### Enums

The `enums` module provides enums and data classes for visualizations.

#### Classes

- `VizNode`: Data class for node visualization properties.
- `GraphJson`: Data class for graph JSON data.
- `GraphType`: Enum for graph types.

## Examples

### Visualizing Class Inheritance

```python
from codegen import Codebase

# Initialize codebase
codebase = Codebase.from_repo("owner/repo")

# Get a class
my_class = codebase.get_class("MyClass")

# Visualize the inheritance hierarchy
codebase.viz_manager.visualize_inheritance_hierarchy(my_class)
```

### Visualizing Function Calls

```python
from codegen import Codebase

# Initialize codebase
codebase = Codebase.from_repo("owner/repo")

# Get a function
my_function = codebase.get_function("my_function")

# Visualize the call graph
codebase.viz_manager.visualize_call_graph(my_function)
```

### Visualizing Symbol Dependencies

```python
from codegen import Codebase

# Initialize codebase
codebase = Codebase.from_repo("owner/repo")

# Get a symbol
my_symbol = codebase.get_symbol("my_symbol")

# Visualize the dependency graph
codebase.viz_manager.visualize_dependency_graph(my_symbol)
```

### Visualizing Module Dependencies

```python
from codegen import Codebase

# Initialize codebase
codebase = Codebase.from_repo("owner/repo")

# Get a file
my_file = codebase.get_file("path/to/file.py")

# Visualize the module dependencies
codebase.viz_manager.visualize_module_dependencies(my_file)
```

## Conclusion

The enhanced visualization features in Codegen provide powerful tools for understanding code structure, relationships, and dependencies. By visualizing these aspects of the codebase, developers can more easily navigate and understand complex codebases, identify potential issues, and make informed decisions about code changes.

