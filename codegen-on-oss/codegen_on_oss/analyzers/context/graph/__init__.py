"""
Graph Context Module

This module provides utilities for working with graph representations
of code, including building, traversing, exporting, and visualizing graphs.
"""

from typing import Any, Dict, List, Optional

import networkx as nx


def build_dependency_graph(edges: list[dict[str, Any]]) -> nx.DiGraph:
    """
    Build a dependency graph from a list of edges.

    Args:
        edges: List of edges, where each edge is a dictionary with
            'source', 'target', and optional 'type' keys

    Returns:
        NetworkX DiGraph representing the dependencies
    """
    graph: nx.DiGraph = nx.DiGraph()

    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        edge_type = edge.get("type", "unknown")

        if source and target:
            graph.add_edge(source, target, type=edge_type)

    return graph


def find_circular_dependencies(graph: nx.DiGraph) -> list[list[str]]:
    """
    Find circular dependencies in a graph.

    Args:
        graph: NetworkX DiGraph to analyze

    Returns:
        List of cycles, where each cycle is a list of node names
    """
    try:
        return list(nx.simple_cycles(graph))
    except nx.NetworkXNoCycle:
        return []


def find_hub_nodes(graph: nx.DiGraph, threshold: int = 5) -> list[str]:
    """
    Find hub nodes in a graph (nodes with many connections).

    Args:
        graph: NetworkX DiGraph to analyze
        threshold: Minimum number of connections to be considered a hub

    Returns:
        List of hub node names
    """
    hubs = []

    for node in graph.nodes():
        # Count both incoming and outgoing connections
        connection_count = graph.in_degree(node) + graph.out_degree(node)

        if connection_count >= threshold:
            hubs.append(node)

    # Sort by connection count in descending order
    hubs.sort(
        key=lambda node: graph.in_degree(node) + graph.out_degree(node), reverse=True
    )

    return hubs


def calculate_centrality(graph: nx.DiGraph) -> dict[str, float]:
    """
    Calculate centrality for each node in the graph.

    Args:
        graph: NetworkX DiGraph to analyze

    Returns:
        Dictionary mapping node names to centrality scores
    """
    try:
        return nx.betweenness_centrality(graph)
    except:
        # Fall back to degree centrality if betweenness fails
        return nx.degree_centrality(graph)


def export_to_dot(graph: nx.DiGraph, filename: str | None = None) -> str:
    """
    Export a graph to DOT format.

    Args:
        graph: NetworkX DiGraph to export
        filename: File to write DOT to, or None to return as string

    Returns:
        DOT representation of the graph if filename is None,
        otherwise returns empty string
    """
    try:
        import pydot
        from networkx.drawing.nx_pydot import write_dot

        if filename:
            write_dot(graph, filename)
            return ""
        else:
            # Convert to pydot
            pydot_graph = nx.nx_pydot.to_pydot(graph)
            return pydot_graph.to_string()

    except ImportError:
        # Fallback to basic DOT export if pydot is not available
        dot = ["digraph G {"]

        # Add nodes
        for node in graph.nodes():
            dot.append(f'    "{node}";')

        # Add edges
        for u, v, data in graph.edges(data=True):
            edge_type = data.get("type", "")
            edge_str = f'    "{u}" -> "{v}"'

            if edge_type:
                edge_str += f' [label="{edge_type}"]'

            edge_str += ";"
            dot.append(edge_str)

        dot.append("}")
        dot_str = "\n".join(dot)

        if filename:
            with open(filename, "w") as f:
                f.write(dot_str)
            return ""
        else:
            return dot_str


def calculate_cohesion(
    graph: nx.DiGraph, module_nodes: dict[str, list[str]]
) -> dict[str, float]:
    """
    Calculate cohesion for modules in the graph.

    Args:
        graph: NetworkX DiGraph to analyze
        module_nodes: Dictionary mapping module names to lists of node names

    Returns:
        Dictionary mapping module names to cohesion scores
    """
    cohesion = {}

    for module, nodes in module_nodes.items():
        if not nodes:
            cohesion[module] = 0.0
            continue

        # Create subgraph for this module
        module_subgraph = graph.subgraph(nodes)

        # Count internal edges
        internal_edges = module_subgraph.number_of_edges()

        # Count external edges
        external_edges = 0
        for node in nodes:
            for _, target in graph.out_edges(node):
                if target not in nodes:
                    external_edges += 1

        # Calculate cohesion as ratio of internal to total edges
        total_edges = internal_edges + external_edges
        cohesion[module] = internal_edges / total_edges if total_edges > 0 else 0.0

    return cohesion
