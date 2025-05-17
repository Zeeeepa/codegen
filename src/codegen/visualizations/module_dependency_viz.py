"""Module dependency visualization utilities.

This module provides enhanced utilities for visualizing module dependencies in a codebase.
It includes features for detailed relationship visualization, interactive navigation,
filtering options, and handling of complex dependency graphs.
"""

from __future__ import annotations

import networkx as nx
from networkx import DiGraph
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.interfaces.editable import Editable
from codegen.shared.logging.get_logger import get_logger
from codegen.visualizations.viz_utils import graph_to_json

logger = get_logger(__name__)


class ModuleDependencyGraph:
    """Class for creating and managing enhanced module dependency graphs."""

    def __init__(self):
        """Initialize a new module dependency graph."""
        self.graph = DiGraph()
        self.modules: Dict[str, Dict[str, Any]] = {}
        self.dependencies: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self.circular_dependencies: List[List[str]] = []

    def add_module(
        self, 
        module: Union[SourceFile, str], 
        attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a module to the dependency graph.
        
        Args:
            module: The module to add, either as a SourceFile object or a string path
            attributes: Optional attributes to associate with the module
        """
        module_id = module.filepath if isinstance(module, SourceFile) else module
        
        # Store module metadata
        if module_id not in self.modules:
            self.modules[module_id] = {
                "imports_count": 0,
                "imported_by_count": 0,
                "is_external": not isinstance(module, SourceFile),
                "attributes": attributes or {},
            }
            
            # Add node to graph with attributes
            node_attrs = {"module_id": module_id}
            if isinstance(module, SourceFile):
                node_attrs["file"] = module
                node_attrs["language"] = module.__class__.__name__.replace("File", "").lower()
                node_attrs["symbols_count"] = len(module.symbols)
                
            # Add any custom attributes
            if attributes:
                node_attrs.update(attributes)
                
            self.graph.add_node(module, **node_attrs)

    def add_dependency(
        self, 
        source_module: Union[SourceFile, str], 
        target_module: Union[SourceFile, str],
        import_obj: Optional[Import] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a dependency between two modules.
        
        Args:
            source_module: The module that depends on the target
            target_module: The module that is depended upon
            import_obj: Optional Import object representing this dependency
            attributes: Optional attributes to associate with this dependency
        """
        # Ensure both modules are in the graph
        self.add_module(source_module)
        self.add_module(target_module)
        
        source_id = source_module.filepath if isinstance(source_module, SourceFile) else source_module
        target_id = target_module.filepath if isinstance(target_module, SourceFile) else target_module
        
        # Create or update dependency metadata
        dep_key = (source_id, target_id)
        if dep_key not in self.dependencies:
            self.dependencies[dep_key] = {
                "imports": [],
                "weight": 0,
                "attributes": attributes or {},
            }
        
        # Add the import if provided
        if import_obj:
            self.dependencies[dep_key]["imports"].append(import_obj)
            
        # Increment weight (number of imports between these modules)
        self.dependencies[dep_key]["weight"] += 1
        
        # Update module statistics
        self.modules[source_id]["imports_count"] += 1
        self.modules[target_id]["imported_by_count"] += 1
        
        # Add edge to graph with attributes
        edge_attrs = {
            "weight": self.dependencies[dep_key]["weight"],
            "source_id": source_id,
            "target_id": target_id,
        }
        
        # Add any custom attributes
        if attributes:
            edge_attrs.update(attributes)
            
        self.graph.add_edge(source_module, target_module, **edge_attrs)

    def detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies in the graph.
        
        Returns:
            A list of cycles, where each cycle is a list of module IDs
        """
        try:
            # Find all simple cycles in the graph
            cycles = list(nx.simple_cycles(self.graph))
            
            # Convert node objects to module IDs for easier handling
            id_cycles = []
            for cycle in cycles:
                id_cycle = []
                for node in cycle:
                    if isinstance(node, SourceFile):
                        id_cycle.append(node.filepath)
                    else:
                        id_cycle.append(str(node))
                id_cycles.append(id_cycle)
                
            # Store the detected cycles
            self.circular_dependencies = id_cycles
            
            # Mark nodes and edges involved in cycles
            for cycle in id_cycles:
                for i in range(len(cycle)):
                    # Mark the node as part of a cycle
                    node = cycle[i]
                    for n in self.graph.nodes():
                        if (isinstance(n, SourceFile) and n.filepath == node) or (isinstance(n, str) and n == node):
                            self.graph.nodes[n]["in_cycle"] = True
                    
                    # Mark the edge as part of a cycle
                    next_i = (i + 1) % len(cycle)
                    source = cycle[i]
                    target = cycle[next_i]
                    
                    for s, t, data in self.graph.edges(data=True):
                        s_id = s.filepath if isinstance(s, SourceFile) else s
                        t_id = t.filepath if isinstance(t, SourceFile) else t
                        
                        if s_id == source and t_id == target:
                            self.graph.edges[s, t]["in_cycle"] = True
            
            return id_cycles
        except Exception as e:
            logger.error(f"Error detecting circular dependencies: {e}")
            return []

    def filter_by_module_path(self, path_prefix: str) -> ModuleDependencyGraph:
        """Filter the graph to only include modules with paths starting with the given prefix.
        
        Args:
            path_prefix: The path prefix to filter by
            
        Returns:
            A new ModuleDependencyGraph containing only the filtered modules
        """
        filtered_graph = ModuleDependencyGraph()
        
        # Add nodes that match the prefix
        for node in self.graph.nodes():
            node_id = node.filepath if isinstance(node, SourceFile) else node
            if node_id.startswith(path_prefix):
                filtered_graph.add_module(node, dict(self.graph.nodes[node]))
        
        # Add edges between nodes that are both in the filtered graph
        for source, target, data in self.graph.edges(data=True):
            source_id = source.filepath if isinstance(source, SourceFile) else source
            target_id = target.filepath if isinstance(target, SourceFile) else target
            
            if source_id.startswith(path_prefix) and target_id.startswith(path_prefix):
                filtered_graph.add_dependency(source, target, None, data)
                
        return filtered_graph

    def filter_by_depth(self, root_module: Union[SourceFile, str], max_depth: int) -> ModuleDependencyGraph:
        """Filter the graph to only include modules within a certain dependency depth from the root.
        
        Args:
            root_module: The module to use as the root
            max_depth: The maximum dependency depth to include
            
        Returns:
            A new ModuleDependencyGraph containing only modules within the specified depth
        """
        filtered_graph = ModuleDependencyGraph()
        
        # Get the root module ID
        root_id = root_module.filepath if isinstance(root_module, SourceFile) else root_module
        
        # Find all nodes within max_depth of the root
        nodes_within_depth = {root_module}
        current_depth = 0
        frontier = {root_module}
        
        while current_depth < max_depth and frontier:
            next_frontier = set()
            for node in frontier:
                for neighbor in self.graph.successors(node):
                    if neighbor not in nodes_within_depth:
                        next_frontier.add(neighbor)
                        nodes_within_depth.add(neighbor)
            
            frontier = next_frontier
            current_depth += 1
        
        # Add all nodes within depth
        for node in nodes_within_depth:
            filtered_graph.add_module(node, dict(self.graph.nodes[node]))
        
        # Add edges between nodes that are both in the filtered graph
        for source in nodes_within_depth:
            for target in self.graph.successors(source):
                if target in nodes_within_depth:
                    filtered_graph.add_dependency(source, target, None, dict(self.graph.edges[source, target]))
                    
        return filtered_graph

    def get_module_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Calculate and return metrics for each module in the graph.
        
        Returns:
            A dictionary mapping module IDs to their metrics
        """
        metrics = {}
        
        for module_id, module_data in self.modules.items():
            # Get the corresponding node from the graph
            node = None
            for n in self.graph.nodes():
                if (isinstance(n, SourceFile) and n.filepath == module_id) or (isinstance(n, str) and n == module_id):
                    node = n
                    break
            
            if node is None:
                continue
                
            # Calculate metrics
            in_degree = self.graph.in_degree(node)
            out_degree = self.graph.out_degree(node)
            
            # Centrality measures
            try:
                betweenness = nx.betweenness_centrality(self.graph, weight="weight").get(node, 0)
                closeness = nx.closeness_centrality(self.graph, distance="weight").get(node, 0)
            except:
                betweenness = 0
                closeness = 0
            
            # Store metrics
            metrics[module_id] = {
                "in_degree": in_degree,
                "out_degree": out_degree,
                "total_degree": in_degree + out_degree,
                "betweenness_centrality": betweenness,
                "closeness_centrality": closeness,
                "is_in_cycle": self.graph.nodes[node].get("in_cycle", False),
                **module_data
            }
            
        return metrics

    def to_visualization_graph(self) -> DiGraph:
        """Convert the module dependency graph to a format suitable for visualization.
        
        This method enhances the graph with additional visual attributes based on
        the module metrics and dependency characteristics.
        
        Returns:
            A NetworkX DiGraph with visualization attributes
        """
        viz_graph = DiGraph()
        
        # Get module metrics for sizing and coloring
        metrics = self.get_module_metrics()
        
        # Add nodes with visual attributes
        for node in self.graph.nodes():
            node_id = node.filepath if isinstance(node, SourceFile) else node
            node_metrics = metrics.get(node_id, {})
            
            # Determine node size based on degree
            total_degree = node_metrics.get("total_degree", 1)
            node_size = 10 + min(total_degree * 2, 40)  # Scale size but cap it
            
            # Determine node color based on whether it's in a cycle
            is_in_cycle = node_metrics.get("is_in_cycle", False)
            node_color = "#ff5555" if is_in_cycle else "#5555ff"
            
            # Add node with visual attributes
            viz_graph.add_node(
                node,
                size=node_size,
                color=node_color,
                tooltip=f"Module: {node_id}<br>"
                        f"Imports: {node_metrics.get('imports_count', 0)}<br>"
                        f"Imported by: {node_metrics.get('imported_by_count', 0)}<br>"
                        f"{'In circular dependency' if is_in_cycle else ''}",
                **self.graph.nodes[node]
            )
        
        # Add edges with visual attributes
        for source, target, data in self.graph.edges(data=True):
            # Determine edge width based on weight
            weight = data.get("weight", 1)
            edge_width = 1 + min(weight * 0.5, 5)  # Scale width but cap it
            
            # Determine edge color based on whether it's in a cycle
            is_in_cycle = data.get("in_cycle", False)
            edge_color = "#ff5555" if is_in_cycle else "#999999"
            
            # Add edge with visual attributes
            viz_graph.add_edge(
                source,
                target,
                width=edge_width,
                color=edge_color,
                tooltip=f"Imports: {weight}",
                **data
            )
            
        return viz_graph

    def to_json(self, root: Optional[Union[SourceFile, str, Editable]] = None) -> str:
        """Convert the module dependency graph to a JSON string for visualization.
        
        Args:
            root: Optional root node for tree-based visualizations
            
        Returns:
            A JSON string representation of the graph
        """
        viz_graph = self.to_visualization_graph()
        return graph_to_json(viz_graph, root)


def build_module_dependency_graph(
    files: List[SourceFile],
    include_external: bool = False,
    path_filter: Optional[str] = None
) -> ModuleDependencyGraph:
    """Build a module dependency graph from a list of files.
    
    Args:
        files: List of SourceFile objects to analyze
        include_external: Whether to include external module dependencies
        path_filter: Optional path prefix to filter files by
        
    Returns:
        A ModuleDependencyGraph object
    """
    graph = ModuleDependencyGraph()
    
    # Filter files by path if specified
    if path_filter:
        files = [f for f in files if f.filepath.startswith(path_filter)]
    
    # Process each file
    for file in files:
        # Add the file as a module
        graph.add_module(file)
        
        # Process import statements
        for import_statement in file.import_statements:
            for imp in import_statement.imports:
                # Get the resolved symbol
                resolved = imp.resolved_symbol
                
                # Skip if no resolution
                if not resolved:
                    continue
                    
                # Handle different types of resolved symbols
                if hasattr(resolved, "file") and resolved.file:
                    # Symbol from another file
                    target_file = resolved.file
                    
                    # Skip external modules if not included
                    if not include_external and not isinstance(target_file, SourceFile):
                        continue
                        
                    graph.add_dependency(file, target_file, imp)
                elif hasattr(resolved, "node_type") and resolved.node_type == "FILE":
                    # Direct file import
                    target_file = resolved
                    
                    # Skip external modules if not included
                    if not include_external and not isinstance(target_file, SourceFile):
                        continue
                        
                    graph.add_dependency(file, target_file, imp)
    
    # Detect circular dependencies
    graph.detect_circular_dependencies()
    
    return graph

