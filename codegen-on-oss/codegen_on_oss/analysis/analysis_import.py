"""
Analysis import module for code analysis.

This module provides functions for analyzing import relationships in code,
including finding import cycles and problematic import loops.
"""

from typing import Dict, List, Union

import networkx as nx
from codegen import Codebase
from codegen.sdk.core.function import Function


def create_graph_from_codebase(repo_name: str) -> nx.DiGraph:
    """
    Create a directed graph from a codebase.

    Args:
        repo_name: Name of the repository

    Returns:
        A directed graph representing the import relationships
    """
    # Create a directed graph
    graph = nx.DiGraph()

    # Add nodes and edges based on import relationships
    # This is a placeholder implementation
    graph.add_node(f"{repo_name}/module1")
    graph.add_node(f"{repo_name}/module2")
    graph.add_node(f"{repo_name}/module3")
    graph.add_edge(f"{repo_name}/module1", f"{repo_name}/module2")
    graph.add_edge(f"{repo_name}/module2", f"{repo_name}/module3")
    graph.add_edge(f"{repo_name}/module3", f"{repo_name}/module1")

    return graph


def find_import_cycles(graph: nx.DiGraph) -> List[List[str]]:
    """
    Find cycles in the import graph.

    Args:
        graph: A directed graph representing import relationships

    Returns:
        A list of cycles, where each cycle is a list of module names
    """
    # Find simple cycles in the graph
    cycles = list(nx.simple_cycles(graph))
    return cycles


def find_problematic_import_loops(
    graph: nx.DiGraph, cycles: List[List[str]]
) -> List[List[str]]:
    """
    Find problematic import loops that might cause issues.

    Args:
        graph: A directed graph representing import relationships
        cycles: A list of cycles in the graph

    Returns:
        A list of problematic import loops
    """
    # Filter cycles based on certain criteria
    # This is a placeholder implementation
    problematic_loops = []
    for cycle in cycles:
        # Consider cycles with more than 2 nodes problematic
        if len(cycle) > 2:
            problematic_loops.append(cycle)
    return problematic_loops


def convert_all_calls_to_kwargs(codebase: Codebase) -> None:
    """
    Convert all function calls to use keyword arguments.

    Args:
        codebase: The codebase to modify
    """
    for function in codebase.functions:
        convert_function_calls_to_kwargs(function)


def convert_function_calls_to_kwargs(function: Function) -> None:
    """
    Convert all function calls within a function to use keyword arguments.

    Args:
        function: The function to modify
    """
    if not hasattr(function, "code_block"):
        return

    for call in function.code_block.function_calls:
        if not hasattr(call, "arguments"):
            continue

        # Find the called function
        called_function = None
        for func in function.codebase.functions:
            if func.name == call.name:
                called_function = func
                break

        if not called_function or not hasattr(called_function, "parameters"):
            continue

        # Convert positional arguments to keyword arguments
        for i, arg in enumerate(call.arguments):
            if not hasattr(arg, "name") or not arg.name:
                if i < len(called_function.parameters):
                    param = called_function.parameters[i]
                    arg.name = param.name


def analyze_imports(codebase: Codebase) -> Dict[str, Union[List, Dict]]:
    """
    Analyze import relationships in a codebase.

    Args:
        codebase: The codebase to analyze

    Returns:
        A dictionary containing import analysis results
    """
    # Create a graph from the codebase
    graph = create_graph_from_codebase(codebase.repo_name)

    # Find import cycles
    cycles = find_import_cycles(graph)

    # Find problematic import loops
    problematic_loops = find_problematic_import_loops(graph, cycles)

    # Count imports per file
    imports_per_file = {}
    for file in codebase.files:
        if hasattr(file, "imports"):
            imports_per_file[file.name] = len(file.imports)

    # Find files with the most imports
    files_with_most_imports = sorted(
        imports_per_file.items(), key=lambda x: x[1], reverse=True
    )[:10]

    return {
        "import_cycles": cycles,
        "problematic_loops": problematic_loops,
        "imports_per_file": imports_per_file,
        "files_with_most_imports": files_with_most_imports
    }
