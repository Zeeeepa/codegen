import json
import os
from dataclasses import asdict
from typing import TYPE_CHECKING, Dict, Any, Optional, Union

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
# ENHANCED VISUALIZATION UTILITIES
####################################################################################################################

def apply_visual_attributes(G: Graph, 
                           node_size_attr: Optional[str] = None,
                           node_color_attr: Optional[str] = None,
                           edge_width_attr: Optional[str] = None,
                           edge_color_attr: Optional[str] = None,
                           default_node_size: int = 10,
                           default_node_color: str = "#5555ff",
                           default_edge_width: int = 1,
                           default_edge_color: str = "#999999") -> Graph:
    """Apply visual attributes to a graph based on node and edge attributes.
    
    Args:
        G: The graph to apply visual attributes to
        node_size_attr: Node attribute to use for sizing nodes
        node_color_attr: Node attribute to use for coloring nodes
        edge_width_attr: Edge attribute to use for edge width
        edge_color_attr: Edge attribute to use for edge color
        default_node_size: Default node size
        default_node_color: Default node color
        default_edge_width: Default edge width
        default_edge_color: Default edge color
        
    Returns:
        The graph with visual attributes applied
    """
    # Create a copy of the graph to avoid modifying the original
    G_viz = G.copy()
    
    # Apply node visual attributes
    for node, data in G_viz.nodes(data=True):
        # Set node size
        if node_size_attr and node_size_attr in data:
            G_viz.nodes[node]["size"] = data[node_size_attr]
        elif "size" not in data:
            G_viz.nodes[node]["size"] = default_node_size
            
        # Set node color
        if node_color_attr and node_color_attr in data:
            G_viz.nodes[node]["color"] = data[node_color_attr]
        elif "color" not in data:
            G_viz.nodes[node]["color"] = default_node_color
            
    # Apply edge visual attributes
    for u, v, data in G_viz.edges(data=True):
        # Set edge width
        if edge_width_attr and edge_width_attr in data:
            G_viz.edges[u, v]["width"] = data[edge_width_attr]
        elif "width" not in data:
            G_viz.edges[u, v]["width"] = default_edge_width
            
        # Set edge color
        if edge_color_attr and edge_color_attr in data:
            G_viz.edges[u, v]["color"] = data[edge_color_attr]
        elif "color" not in data:
            G_viz.edges[u, v]["color"] = default_edge_color
            
    return G_viz


def add_tooltips(G: Graph, 
                node_tooltip_template: Optional[str] = None,
                edge_tooltip_template: Optional[str] = None) -> Graph:
    """Add tooltips to nodes and edges based on their attributes.
    
    Args:
        G: The graph to add tooltips to
        node_tooltip_template: Template string for node tooltips with {attr} placeholders
        edge_tooltip_template: Template string for edge tooltips with {attr} placeholders
        
    Returns:
        The graph with tooltips added
    """
    # Create a copy of the graph to avoid modifying the original
    G_tooltip = G.copy()
    
    # Add node tooltips
    for node, data in G_tooltip.nodes(data=True):
        if "tooltip" not in data:
            if node_tooltip_template:
                try:
                    G_tooltip.nodes[node]["tooltip"] = node_tooltip_template.format(**data)
                except KeyError:
                    # If template has placeholders for missing attributes, use a default
                    G_tooltip.nodes[node]["tooltip"] = str(node)
            else:
                # Create a default tooltip from all attributes
                tooltip = []
                for key, value in data.items():
                    if key not in ["tooltip", "color", "size"]:
                        tooltip.append(f"{key}: {value}")
                G_tooltip.nodes[node]["tooltip"] = "<br>".join(tooltip) if tooltip else str(node)
    
    # Add edge tooltips
    for u, v, data in G_tooltip.edges(data=True):
        if "tooltip" not in data:
            if edge_tooltip_template:
                try:
                    G_tooltip.edges[u, v]["tooltip"] = edge_tooltip_template.format(**data)
                except KeyError:
                    # If template has placeholders for missing attributes, use a default
                    G_tooltip.edges[u, v]["tooltip"] = f"{u} → {v}"
            else:
                # Create a default tooltip from all attributes
                tooltip = []
                for key, value in data.items():
                    if key not in ["tooltip", "color", "width"]:
                        tooltip.append(f"{key}: {value}")
                G_tooltip.edges[u, v]["tooltip"] = "<br>".join(tooltip) if tooltip else f"{u} → {v}"
    
    return G_tooltip


def filter_graph_by_node_attribute(G: Graph, 
                                  attribute: str, 
                                  value: Any,
                                  include_neighbors: bool = False) -> Graph:
    """Filter a graph to only include nodes with a specific attribute value.
    
    Args:
        G: The graph to filter
        attribute: The node attribute to filter by
        value: The attribute value to match
        include_neighbors: Whether to include neighbors of matching nodes
        
    Returns:
        A new graph containing only the filtered nodes and their edges
    """
    # Create a new graph of the same type as G
    H = G.__class__()
    
    # Find nodes matching the attribute value
    matching_nodes = [n for n, d in G.nodes(data=True) if attribute in d and d[attribute] == value]
    
    # Add matching nodes to the new graph
    for node in matching_nodes:
        H.add_node(node, **G.nodes[node])
    
    # If including neighbors, add them too
    if include_neighbors:
        for node in matching_nodes:
            for neighbor in G.neighbors(node):
                if neighbor not in H:
                    H.add_node(neighbor, **G.nodes[neighbor])
                H.add_edge(node, neighbor, **G.edges[node, neighbor])
    
    # Add edges between nodes in the new graph
    for u in H.nodes():
        for v in H.nodes():
            if G.has_edge(u, v):
                H.add_edge(u, v, **G.edges[u, v])
    
    return H
