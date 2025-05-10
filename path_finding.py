"""
Path Finding Module

This module provides functions for finding paths between functions in a call graph.
"""

import logging
import networkx as nx
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

def get_path_finding_in_call_graphs(codebase, source_function: str = None, target_function: str = None, max_depth: int = 10) -> Dict[str, Any]:
    """
    Find paths between functions in the call graph.
    
    This function identifies all possible paths between a source function and a target function
    in the call graph, with options to limit the search depth.
    
    Args:
        codebase: The codebase object to analyze
        source_function: Name of the source function (if None, all entry points are considered)
        target_function: Name of the target function (if None, all functions are considered)
        max_depth: Maximum depth of the search
        
    Returns:
        Dict containing path finding results
    """
    path_finding_results = {
        "paths": [],
        "total_paths": 0,
        "average_path_length": 0,
        "shortest_path": None,
        "source_function": source_function,
        "target_function": target_function
    }
    
    try:
        # Create a directed graph of function calls
        G = nx.DiGraph()
        
        # Map to store function objects by their qualified name
        function_map = {}
        name_to_qualified = {}  # Maps simple names to qualified names
        
        # Add nodes and edges to the graph
        for function in codebase.functions:
            qualified_name = f"{function.file.file_path}::{function.name}" if hasattr(function, "file") else f"unknown::{function.name}"
            G.add_node(qualified_name)
            function_map[qualified_name] = function
            
            # Map simple name to qualified name (might have duplicates)
            if function.name in name_to_qualified:
                name_to_qualified[function.name].append(qualified_name)
            else:
                name_to_qualified[function.name] = [qualified_name]
            
            # Add edges for each function call
            for call in function.function_calls:
                if hasattr(call, "function_definition") and call.function_definition:
                    called_func = call.function_definition
                    called_name = f"{called_func.file.file_path if hasattr(called_func, 'file') else 'unknown'}::{called_func.name}"
                    G.add_node(called_name)
                    G.add_edge(qualified_name, called_name)
        
        # Determine source and target nodes
        source_nodes = []
        target_nodes = []
        
        if source_function:
            # Find all qualified names matching the source function name
            if source_function in name_to_qualified:
                source_nodes = name_to_qualified[source_function]
            else:
                # Try partial matching
                for name, qualified_names in name_to_qualified.items():
                    if source_function in name:
                        source_nodes.extend(qualified_names)
        else:
            # Use all entry points (functions not called by any other function)
            source_nodes = [node for node in G.nodes() if G.in_degree(node) == 0]
        
        if target_function:
            # Find all qualified names matching the target function name
            if target_function in name_to_qualified:
                target_nodes = name_to_qualified[target_function]
            else:
                # Try partial matching
                for name, qualified_names in name_to_qualified.items():
                    if target_function in name:
                        target_nodes.extend(qualified_names)
        else:
            # Use all functions as targets
            target_nodes = list(G.nodes())
        
        # Find all paths between source and target nodes
        all_paths = []
        for source in source_nodes:
            for target in target_nodes:
                if source != target and source in G and target in G:
                    try:
                        paths = list(nx.all_simple_paths(G, source, target, cutoff=max_depth))
                        all_paths.extend(paths)
                    except (nx.NetworkXNoPath, nx.NodeNotFound):
                        continue
        
        # Process the paths
        if all_paths:
            path_lengths = [len(path) for path in all_paths]
            path_finding_results["average_path_length"] = sum(path_lengths) / len(path_lengths)
            path_finding_results["total_paths"] = len(all_paths)
            
            # Format the paths for output
            path_finding_results["paths"] = [
                {
                    "path": [node.split("::")[-1] for node in path],  # Just function names for readability
                    "length": len(path),
                    "files": [node.split("::")[0] for node in path]
                }
                for path in all_paths[:20]  # Limit to 20 paths to avoid overwhelming output
            ]
            
            # Find the shortest path
            shortest_path = min(all_paths, key=len)
            path_finding_results["shortest_path"] = {
                "path": [node.split("::")[-1] for node in shortest_path],
                "length": len(shortest_path),
                "files": [node.split("::")[0] for node in shortest_path]
            }
        
        return path_finding_results
    except Exception as e:
        logger.error(f"Error in path finding: {e}")
        return {"error": str(e)}

