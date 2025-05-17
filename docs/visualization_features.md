# Enhanced Visualization Features

This document describes the enhanced visualization features implemented in the Codegen visualization system.

## Overview

The enhanced visualization system provides an interactive UI with a selection row that shows corresponding methods when selecting Symbols, Files, Functions, or Classes. This allows users to explore the codebase more effectively and understand the relationships between different code elements.

## Features

### Selection Row

The selection row is a UI component that appears at the bottom of the visualization and displays information about the currently selected element. It includes:

- The element type (Symbol, File, Function, or Class)
- The element name
- Tabs for viewing methods and related elements
- Lists of methods and related elements that can be clicked to navigate to them

### Interactive Selection

Users can select elements in the visualization by clicking on them. When an element is selected:

1. The selection row is updated to show information about the selected element
2. The element is highlighted in the visualization
3. The methods and related elements of the selected element are displayed in the selection row

### Relationship Visualization

The enhanced visualization system also shows relationships between selected elements:

- When a method is selected from the selection row, it is highlighted in the visualization
- When a related element is selected from the selection row, it is highlighted in the visualization
- Relationships between elements are shown as edges in the graph

### Navigation

The enhanced visualization system provides several ways to navigate between related elements:

- Clicking on an element in the visualization selects it
- Clicking on a method in the selection row selects that method
- Clicking on a related element in the selection row selects that element

## Implementation

The enhanced visualization system is implemented using the following components:

### Backend

- `VisualizationManager`: Manages the visualization data and selection state
- `viz_utils.py`: Provides utility functions for working with the visualization data
- `enums.py`: Defines enums and data classes for the visualization system
- `visualization_api.py`: Provides API endpoints for the visualization frontend

### Frontend

- `VisualizationUI.tsx`: The main visualization component
- `SelectionRow.tsx`: The selection row component
- `VisualizationUI.css`: Styles for the visualization UI
- `SelectionRow.css`: Styles for the selection row

## Usage

To use the enhanced visualization features:

1. Create a visualization using the `VisualizationManager`:

```python
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.visualizations.visualization_manager import VisualizationManager
import networkx as nx

# Create a repo operator
op = RepoOperator("path/to/repo")

# Create a visualization manager
viz_manager = VisualizationManager(op)

# Create a graph
G = nx.DiGraph()
G.add_node("node1", name="Node 1")
G.add_node("node2", name="Node 2")
G.add_edge("node1", "node2")

# Write the graph data
viz_manager.write_graphviz_data(G)
```

2. Select elements in the visualization:

```python
# Select an element
element = codebase.get_function("my_function")
viz_manager.select_element(element)

# Get the selected elements
selected_elements = viz_manager.get_selected_elements()

# Get the methods of a selected element
methods = viz_manager.get_selected_element_methods("element_id")

# Get the related elements of a selected element
related = viz_manager.get_selected_element_related("element_id")
```

3. View the visualization in the frontend:

The visualization is available at the `/visualization` endpoint of the Codegen web server.

## API Reference

### Backend

#### `VisualizationManager`

- `select_element(element)`: Select an element in the visualization
- `deselect_element(element_id)`: Deselect an element in the visualization
- `clear_selection()`: Clear all selected elements
- `get_selected_elements()`: Get all selected elements
- `get_selected_element(element_id)`: Get a selected element by ID
- `get_selected_element_methods(element_id)`: Get the methods of a selected element
- `get_selected_element_related(element_id)`: Get the related elements of a selected element

#### `viz_utils.py`

- `create_selected_element(element)`: Create a `SelectedElement` object from an element
- `get_element_type(element)`: Get the type of an element
- `get_element_methods(element)`: Get the methods of an element
- `get_related_elements(element)`: Get the related elements of an element

### Frontend

#### `VisualizationUI`

The main visualization component that displays the graph and selection row.

#### `SelectionRow`

The selection row component that displays information about the selected element and allows navigation between related elements.

## API Endpoints

- `GET /api/visualization/graph`: Get the graph visualization data
- `GET /api/visualization/selection`: Get the selection data
- `POST /api/visualization/select`: Select an element in the visualization
- `POST /api/visualization/deselect`: Deselect an element in the visualization
- `POST /api/visualization/clear-selection`: Clear all selected elements

