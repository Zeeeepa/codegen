"""Graph utilities for analyzing code dependencies."""

import logging
from typing import Any, List, Optional, Set, Tuple

import networkx as nx

logger = logging.getLogger(__name__)


def build_dependency_graph(edges: list[dict[str, Any]]) -> nx.DiGraph:
    """Builds a dependency graph from a list of edges.

    Args:
        edges: List of dictionaries, each containing at least a "source" and "target" key.
            Each edge represents a dependency from source to target.

    Returns:
        NetworkX DiGraph representing the dependencies
    """
    graph: nx.DiGraph = nx.DiGraph()

    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if source and target:
            graph.add_edge(source, target)
        else:
            logger.warning(f"Skipping edge with missing source or target: {edge}")

    return graph


def find_hubs(graph: nx.DiGraph, threshold: int = 5) -> list:
    """Finds hub nodes in the graph.

    A hub is a node with a high number of connections (both incoming and outgoing).

    Args:
        graph: The dependency graph
        threshold: Minimum number of connections for a node to be considered a hub

    Returns:
        List of hub nodes, sorted by connection count in descending order
    """
    hubs = []

    for node in graph.nodes():
        # Count both incoming and outgoing connections
        in_degree = graph.in_degree(node)
        out_degree = graph.out_degree(node)
        connection_count = in_degree + out_degree
        
        if connection_count >= threshold:
            hubs.append(node)

    # Sort by connection count in descending order
    hubs.sort(
        key=lambda node: graph.in_degree(node) + graph.out_degree(node), reverse=True
    )

    return hubs


def find_cycles(graph: nx.DiGraph) -> list:
    """Finds cycles in the dependency graph.

    Args:
        graph: The dependency graph

    Returns:
        List of cycles in the graph
    """
    try:
        return list(nx.simple_cycles(graph))
    except nx.NetworkXNoCycle:
        return []

