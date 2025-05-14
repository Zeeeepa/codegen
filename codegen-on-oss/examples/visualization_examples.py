"""Examples of using the visualization capabilities of codegen-on-oss.

This module demonstrates how to use the various visualization tools
provided by the codegen-on-oss package to analyze and understand code structure.
"""

import networkx as nx
from matplotlib import pyplot as plt

from codegen_on_oss.analyzers.context.codebase import Codebase
from codegen_on_oss.visualizers import (
    CallGraphFilter,
    CallGraphFromNode,
    CallPathsBetweenNodes,
    DeadCodeVisualizer,
)


def visualize_call_graph(codebase_path: str, function_name: str):
    """Visualize the call graph starting from a specific function.
    
    Args:
        codebase_path: Path to the codebase
        function_name: Name of the function to start from
    """
    # Create a codebase object
    codebase = Codebase(codebase_path)
    
    # Create a call graph visualizer
    visualizer = CallGraphFromNode(function_name=function_name, max_depth=3)
    
    # Generate the graph
    G = visualizer.visualize(codebase)
    
    # Visualize the graph
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color="lightblue", node_size=1500, font_size=10)
    plt.title(f"Call Graph from {function_name}")
    plt.show()


def visualize_filtered_call_graph(codebase_path: str, function_name: str, class_name: str):
    """Visualize a filtered call graph showing only specific method types.
    
    Args:
        codebase_path: Path to the codebase
        function_name: Name of the function to start from
        class_name: Name of the class to filter methods from
    """
    # Create a codebase object
    codebase = Codebase(codebase_path)
    
    # Create a filtered call graph visualizer
    visualizer = CallGraphFilter(
        function_name=function_name,
        class_name=class_name,
        method_names=["get", "post", "put", "delete"],
        max_depth=3
    )
    
    # Generate the graph
    G = visualizer.visualize(codebase)
    
    # Visualize the graph
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G)
    
    # Draw nodes with different colors based on attributes
    node_colors = []
    for node in G.nodes():
        if G.nodes[node].get("color") == "red":
            node_colors.append("red")
        elif G.nodes[node].get("color") == "yellow":
            node_colors.append("yellow")
        else:
            node_colors.append("lightblue")
            
    nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=1500, font_size=10)
    plt.title(f"Filtered Call Graph from {function_name}")
    plt.show()


def visualize_call_paths(codebase_path: str, start_function: str, end_function: str):
    """Visualize all call paths between two functions.
    
    Args:
        codebase_path: Path to the codebase
        start_function: Name of the starting function
        end_function: Name of the ending function
    """
    # Create a codebase object
    codebase = Codebase(codebase_path)
    
    # Create a call paths visualizer
    visualizer = CallPathsBetweenNodes(
        start_function_name=start_function,
        end_function_name=end_function,
        max_depth=5
    )
    
    # Generate the graph
    G = visualizer.visualize(codebase)
    
    # Visualize the graph
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G)
    
    # Draw nodes with different colors based on attributes
    node_colors = []
    for node in G.nodes():
        if G.nodes[node].get("color") == "blue":
            node_colors.append("blue")
        elif G.nodes[node].get("color") == "red":
            node_colors.append("red")
        else:
            node_colors.append("lightgreen")
            
    nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=1500, font_size=10)
    plt.title(f"Call Paths from {start_function} to {end_function}")
    plt.show()


def visualize_dead_code(codebase_path: str):
    """Visualize dead code in the codebase.
    
    Args:
        codebase_path: Path to the codebase
    """
    # Create a codebase object
    codebase = Codebase(codebase_path)
    
    # Create a dead code visualizer
    visualizer = DeadCodeVisualizer(exclude_test_files=True, exclude_decorated=True)
    
    # Generate the graph
    G = visualizer.visualize(codebase)
    
    # Visualize the graph
    plt.figure(figsize=(15, 10))
    pos = nx.spring_layout(G)
    
    # Draw nodes with different colors based on attributes
    node_colors = []
    for node in G.nodes():
        if G.nodes[node].get("color") == "red":
            node_colors.append("red")
        else:
            node_colors.append("gray")
            
    # Draw edges with different colors based on attributes
    edge_colors = []
    for u, v in G.edges():
        if G.edges[u, v].get("color") == "red":
            edge_colors.append("red")
        else:
            edge_colors.append("black")
            
    nx.draw(G, pos, with_labels=True, node_color=node_colors, edge_color=edge_colors, 
            node_size=1500, font_size=10, arrows=True)
    plt.title("Dead Code Visualization")
    plt.show()


if __name__ == "__main__":
    # Example usage
    codebase_path = "path/to/your/codebase"
    
    # Uncomment the examples you want to run
    # visualize_call_graph(codebase_path, "main")
    # visualize_filtered_call_graph(codebase_path, "process_request", "ApiHandler")
    # visualize_call_paths(codebase_path, "start_process", "end_process")
    # visualize_dead_code(codebase_path)

