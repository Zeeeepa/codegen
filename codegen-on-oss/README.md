# Codegen On OSS

This package provides a set of tools for analyzing and visualizing codebases. It's designed to help developers understand code structure, identify issues, and optimize their codebase.

## Features

- **Code Analysis**: Analyze code structure, dependencies, and relationships
- **Call Graph Visualization**: Visualize function call graphs and paths
- **Dead Code Detection**: Identify unused code in your codebase
- **Diff Analysis**: Analyze code changes and their impact
- **Issue Detection**: Find potential issues in your code

## Installation

```bash
pip install codegen-on-oss
```

## Usage

### Codebase Analysis

```python
from codegen_on_oss.analyzers.context.codebase import Codebase

# Create a codebase object
codebase = Codebase("/path/to/your/codebase")

# Get all functions in the codebase
functions = codebase.functions

# Get all classes in the codebase
classes = codebase.classes

# Get a specific function
main_function = codebase.get_function("main")

# Get a specific class
user_class = codebase.get_class("User")
```

### Call Graph Visualization

```python
from codegen_on_oss.visualizers import CallGraphFromNode
import matplotlib.pyplot as plt
import networkx as nx

# Create a call graph visualizer
visualizer = CallGraphFromNode(function_name="main", max_depth=3)

# Generate the graph
G = visualizer.visualize(codebase)

# Visualize the graph
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_color="lightblue", node_size=1500, font_size=10)
plt.title("Call Graph from main")
plt.show()
```

### Dead Code Detection

```python
from codegen_on_oss.visualizers import DeadCodeVisualizer
import matplotlib.pyplot as plt
import networkx as nx

# Create a dead code visualizer
visualizer = DeadCodeVisualizer(exclude_test_files=True, exclude_decorated=True)

# Generate the graph
G = visualizer.visualize(codebase)

# Visualize the graph
plt.figure(figsize=(15, 10))
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_color="red", node_size=1500, font_size=10)
plt.title("Dead Code Visualization")
plt.show()
```

### Filtered Call Graph

```python
from codegen_on_oss.visualizers import CallGraphFilter
import matplotlib.pyplot as plt
import networkx as nx

# Create a filtered call graph visualizer
visualizer = CallGraphFilter(
    function_name="process_request",
    class_name="ApiHandler",
    method_names=["get", "post", "put", "delete"],
    max_depth=3
)

# Generate the graph
G = visualizer.visualize(codebase)

# Visualize the graph
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_size=1500, font_size=10)
plt.title("API Endpoints Call Graph")
plt.show()
```

### Call Paths Between Functions

```python
from codegen_on_oss.visualizers import CallPathsBetweenNodes
import matplotlib.pyplot as plt
import networkx as nx

# Create a call paths visualizer
visualizer = CallPathsBetweenNodes(
    start_function_name="start_process",
    end_function_name="end_process",
    max_depth=5
)

# Generate the graph
G = visualizer.visualize(codebase)

# Visualize the graph
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_color="lightgreen", node_size=1500, font_size=10)
plt.title("Call Paths Visualization")
plt.show()
```

## Advanced Usage

See the `examples` directory for more detailed examples of how to use the package.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

