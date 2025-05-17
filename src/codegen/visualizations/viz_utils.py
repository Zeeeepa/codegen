import json
import os
from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import networkx as nx
from networkx import DiGraph, Graph

from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.interfaces.importable import Importable
from codegen.sdk.output.utils import DeterministicJSONEncoder
from codegen.visualizations.enums import GraphJson, GraphType

if TYPE_CHECKING:
    from codegen.git.repo_operator.repo_operator import RepoOperator

####################################################################################################################
# READING GRAPH VISUALIZATION DATA
####################################################################################################################


def get_graph_json(op: "RepoOperator"):
    if os.path.exists(op.viz_file_path):
        with open(op.viz_file_path) as f:
            graph_json = json.load(f)
        return graph_json
    else:
        return None


####################################################################################################################
# NETWORKX GRAPH TO JSON
####################################################################################################################


def get_node_options(node: Editable | str | int):
    if isinstance(node, Editable):
        return asdict(node.viz)
    return {}


def get_node_id(node: Editable | str | int):
    if isinstance(node, Importable):
        return node.node_id
    elif isinstance(node, Editable):
        return str(node.span)
    elif isinstance(node, str) or isinstance(node, int):
        return node


def graph_to_json(G1: Graph, root: Editable | str | int | None = None):
    G2 = DiGraph()
    for node_tuple in G1.nodes(data=True):
        options = get_node_options(node_tuple[0])
        options.update(node_tuple[1])
        G2.add_node(get_node_id(node_tuple[0]), **options)

    for edge_tuple in G1.edges(data=True):
        options = edge_tuple[2]
        if "symbol" in options:
            print(get_node_options(options["symbol"]))
            options.update(get_node_options(options["symbol"]))
            del options["symbol"]
        G2.add_edge(get_node_id(edge_tuple[0]), get_node_id(edge_tuple[1]), **options)

    if root:
        root = get_node_id(root)
        return json.dumps(asdict(GraphJson(type=GraphType.TREE.value, data=nx.tree_data(G2, root))), cls=DeterministicJSONEncoder, indent=2)
    else:
        return json.dumps(asdict(GraphJson(type=GraphType.GRAPH.value, data=nx.node_link_data(G2))), cls=DeterministicJSONEncoder, indent=2)


####################################################################################################################
# GRAPH FILTERING AND CUSTOMIZATION
####################################################################################################################


def filter_graph_by_depth(G: Graph, root: Editable | str | int, max_depth: int) -> Graph:
    """
    Filters a graph to include only nodes within a certain depth from the root.
    
    Args:
        G: The graph to filter
        root: The root node
        max_depth: Maximum depth to include
        
    Returns:
        A new graph containing only nodes within the specified depth
    """
    filtered_graph = G.__class__()  # Create a new graph of the same type
    
    # Get all nodes within max_depth of root
    nodes_within_depth = {root}
    current_level = {root}
    
    for _ in range(max_depth):
        next_level = set()
        for node in current_level:
            for neighbor in G.neighbors(node):
                next_level.add(neighbor)
        nodes_within_depth.update(next_level)
        current_level = next_level
        
        if not current_level:
            break
    
    # Create the subgraph with the nodes within depth
    filtered_graph = G.subgraph(nodes_within_depth).copy()
    
    return filtered_graph


def apply_layout_to_graph(G: Graph, layout_type: str = "hierarchical") -> Dict[Any, List[float]]:
    """
    Applies a layout algorithm to a graph and returns the node positions.
    
    Args:
        G: The graph to apply layout to
        layout_type: The type of layout to apply (hierarchical, spring, circular, etc.)
        
    Returns:
        A dictionary mapping nodes to positions
    """
    if layout_type == "hierarchical":
        return nx.multipartite_layout(G, subset_key="depth")
    elif layout_type == "spring":
        return nx.spring_layout(G)
    elif layout_type == "circular":
        return nx.circular_layout(G)
    elif layout_type == "shell":
        return nx.shell_layout(G)
    elif layout_type == "spectral":
        return nx.spectral_layout(G)
    else:
        return nx.spring_layout(G)  # Default to spring layout


def add_depth_information(G: Graph, root: Editable | str | int) -> Graph:
    """
    Adds depth information to each node in the graph relative to the root.
    
    Args:
        G: The graph to add depth information to
        root: The root node
        
    Returns:
        The graph with depth information added to each node
    """
    # Calculate shortest path lengths from root
    path_lengths = nx.shortest_path_length(G, source=root)
    
    # Add depth information to each node
    for node, depth in path_lengths.items():
        G.nodes[node]["depth"] = depth
    
    return G


def add_cluster_information(G: Graph) -> Graph:
    """
    Adds cluster information to nodes based on their package/namespace.
    
    Args:
        G: The graph to add cluster information to
        
    Returns:
        The graph with cluster information added
    """
    for node in G.nodes():
        if hasattr(node, "filepath") and node.filepath:
            # Extract package/namespace from filepath
            parts = node.filepath.split("/")
            if len(parts) > 2:
                package = "/".join(parts[:-1])  # Use directory as cluster
            else:
                package = parts[0] if parts else ""
                
            G.nodes[node]["cluster"] = package
    
    return G
