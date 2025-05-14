# Codebase Visualization

This directory contains tools and utilities for visualizing various aspects of a codebase.

## Directory Structure

- **call_graph/**: Visualizations related to function call relationships and method interactions
  - `call_trace.py`: Traces function call paths through a codebase
  - `graph_viz_call_graph.py`: Creates directed call graphs for functions
  - `method_relationships.py`: Visualizes relationships between methods in a class
  - `viz_cal_graph.py`: Generates call graphs with detailed metadata

- **dependency_graph/**: Visualizations related to code dependencies and impact analysis
  - `blast_radius.py`: Shows the "blast radius" of changes to a function
  - `dependency_trace.py`: Traces symbol dependencies through a codebase
  - `viz_dead_code.py`: Identifies and visualizes dead/unused code

- **structure_graph/**: Visualizations related to code structure and organization
  - `graph_viz_dir_tree.py`: Displays directory structure as a graph
  - `graph_viz_foreign_key.py`: Visualizes database schema relationships

- **docs/**: Documentation and examples for visualization tools
  - `codebase-visualization.mdx`: Comprehensive guide to codebase visualization

## Base Visualization Files

- `analysis_visualizer.py`: Core visualization for analysis results
- `code_visualizer.py`: Visualization tools for code elements
- `codebase_visualizer.py`: Main visualization engine for codebases
- `visualizer.py`: Base visualization framework

## Usage

These visualization tools can be used to:

1. Understand complex codebases
2. Plan refactoring efforts
3. Identify tightly coupled components
4. Analyze critical paths
5. Document system architecture
6. Find dead code
7. Visualize database schemas
8. Understand directory structures

