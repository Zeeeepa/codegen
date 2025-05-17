"""
Inheritance Hierarchy Visualization Utilities

This module provides utilities for creating and customizing inheritance hierarchy visualizations.
It includes functions for building inheritance graphs with detailed relationship information,
filtering options, and interactive features.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

import networkx as nx
from networkx import DiGraph

from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.core.interface import Interface
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.enums import SymbolType
from codegen.shared.logging.get_logger import get_logger
from codegen.visualizations.enums import InheritanceRelationType, VizNode

logger = get_logger(__name__)


def create_inheritance_graph(
    root_class: Class,
    max_depth: Optional[int] = None,
    include_subclasses: bool = True,
    include_superclasses: bool = True,
    include_interfaces: bool = True,
    include_external: bool = True,
    include_methods: bool = False,
    filter_packages: Optional[List[str]] = None,
) -> DiGraph:
    """
    Creates a detailed inheritance hierarchy graph for a given class.

    Args:
        root_class: The root class to start the inheritance hierarchy from
        max_depth: Maximum depth of inheritance hierarchy to include (None for unlimited)
        include_subclasses: Whether to include subclasses in the graph
        include_superclasses: Whether to include superclasses in the graph
        include_interfaces: Whether to include interfaces in the graph
        include_external: Whether to include external modules in the graph
        include_methods: Whether to include methods in the graph
        filter_packages: List of package prefixes to include (None for all)

    Returns:
        A NetworkX DiGraph representing the inheritance hierarchy
    """
    G = nx.DiGraph()
    visited: Set[str] = set()

    # Add the root class to the graph
    add_class_to_graph(G, root_class, include_methods=include_methods)
    visited.add(root_class.node_id)

    # Add superclasses if requested
    if include_superclasses:
        add_superclasses_to_graph(
            G, 
            root_class, 
            max_depth=max_depth, 
            visited=visited,
            include_interfaces=include_interfaces,
            include_external=include_external,
            include_methods=include_methods,
            filter_packages=filter_packages
        )

    # Add subclasses if requested
    if include_subclasses:
        add_subclasses_to_graph(
            G, 
            root_class, 
            max_depth=max_depth, 
            visited=visited,
            include_interfaces=include_interfaces,
            include_methods=include_methods,
            filter_packages=filter_packages
        )

    return G


def add_class_to_graph(
    G: DiGraph, 
    cls: Class, 
    include_methods: bool = False
) -> None:
    """
    Adds a class to the graph with detailed information.

    Args:
        G: The graph to add the class to
        cls: The class to add
        include_methods: Whether to include methods in the node data
    """
    # Get class metadata
    is_abstract = hasattr(cls, "is_abstract") and cls.is_abstract
    
    # Determine node shape and color based on class type
    shape = "box"
    color = "#4287f5"  # Default blue
    
    if is_abstract:
        color = "#f54242"  # Red for abstract classes
    
    # Add class node with metadata
    node_data = {
        "label": cls.name,
        "shape": shape,
        "color": color,
        "type": cls.symbol_type.name,
        "filepath": cls.filepath,
        "is_abstract": is_abstract,
    }
    
    # Add methods information if requested
    if include_methods:
        methods_info = []
        for method in cls.methods(max_depth=0):
            method_info = {
                "name": method.name,
                "is_private": method.is_private,
                "is_static": hasattr(method, "is_static") and method.is_static,
                "is_abstract": hasattr(method, "is_abstract") and method.is_abstract,
            }
            methods_info.append(method_info)
        node_data["methods"] = methods_info
    
    G.add_node(cls, **node_data)


def add_superclasses_to_graph(
    G: DiGraph,
    cls: Class,
    max_depth: Optional[int] = None,
    visited: Optional[Set[str]] = None,
    depth: int = 0,
    include_interfaces: bool = True,
    include_external: bool = True,
    include_methods: bool = False,
    filter_packages: Optional[List[str]] = None,
) -> None:
    """
    Recursively adds superclasses of a class to the graph.

    Args:
        G: The graph to add the superclasses to
        cls: The class whose superclasses to add
        max_depth: Maximum depth of superclasses to include (None for unlimited)
        visited: Set of already visited node IDs
        depth: Current depth in the recursion
        include_interfaces: Whether to include interfaces
        include_external: Whether to include external modules
        include_methods: Whether to include methods in the node data
        filter_packages: List of package prefixes to include (None for all)
    """
    if visited is None:
        visited = set()
    
    if max_depth is not None and depth >= max_depth:
        return
    
    for superclass in cls.superclasses(max_depth=1):
        # Skip if already visited
        if superclass.node_id in visited:
            continue
        
        # Skip if not matching filter
        if filter_packages and not any(superclass.filepath.startswith(pkg) for pkg in filter_packages):
            continue
            
        # Skip interfaces if not including them
        if isinstance(superclass, Interface) and not include_interfaces:
            continue
            
        # Skip external modules if not including them
        if isinstance(superclass, ExternalModule) and not include_external:
            continue
        
        # Add the superclass to the graph
        if isinstance(superclass, Class):
            add_class_to_graph(G, superclass, include_methods=include_methods)
        else:
            # Add basic node for interfaces and external modules
            node_type = "Interface" if isinstance(superclass, Interface) else "ExternalModule"
            color = "#42f59e" if isinstance(superclass, Interface) else "#f5d442"  # Green for interfaces, yellow for external
            G.add_node(
                superclass,
                label=superclass.name,
                shape="ellipse",
                color=color,
                type=node_type,
                filepath=getattr(superclass, "filepath", ""),
            )
        
        # Add edge from subclass to superclass
        relation_type = InheritanceRelationType.IMPLEMENTS if isinstance(superclass, Interface) else InheritanceRelationType.EXTENDS
        G.add_edge(
            cls, 
            superclass, 
            relation=relation_type.value,
            style="dashed" if relation_type == InheritanceRelationType.IMPLEMENTS else "solid",
        )
        
        visited.add(superclass.node_id)
        
        # Recursively add superclasses
        if isinstance(superclass, Class):
            add_superclasses_to_graph(
                G, 
                superclass, 
                max_depth=max_depth, 
                visited=visited, 
                depth=depth+1,
                include_interfaces=include_interfaces,
                include_external=include_external,
                include_methods=include_methods,
                filter_packages=filter_packages
            )


def add_subclasses_to_graph(
    G: DiGraph,
    cls: Class,
    max_depth: Optional[int] = None,
    visited: Optional[Set[str]] = None,
    depth: int = 0,
    include_interfaces: bool = True,
    include_methods: bool = False,
    filter_packages: Optional[List[str]] = None,
) -> None:
    """
    Recursively adds subclasses of a class to the graph.

    Args:
        G: The graph to add the subclasses to
        cls: The class whose subclasses to add
        max_depth: Maximum depth of subclasses to include (None for unlimited)
        visited: Set of already visited node IDs
        depth: Current depth in the recursion
        include_interfaces: Whether to include interfaces
        include_methods: Whether to include methods in the node data
        filter_packages: List of package prefixes to include (None for all)
    """
    if visited is None:
        visited = set()
    
    if max_depth is not None and depth >= max_depth:
        return
    
    for subclass in cls.subclasses(max_depth=1):
        # Skip if already visited
        if subclass.node_id in visited:
            continue
        
        # Skip if not matching filter
        if filter_packages and not any(subclass.filepath.startswith(pkg) for pkg in filter_packages):
            continue
            
        # Skip interfaces if not including them
        if isinstance(subclass, Interface) and not include_interfaces:
            continue
        
        # Add the subclass to the graph
        add_class_to_graph(G, subclass, include_methods=include_methods)
        
        # Add edge from subclass to superclass
        G.add_edge(
            subclass, 
            cls, 
            relation=InheritanceRelationType.EXTENDS.value,
            style="solid",
        )
        
        visited.add(subclass.node_id)
        
        # Recursively add subclasses
        add_subclasses_to_graph(
            G, 
            subclass, 
            max_depth=max_depth, 
            visited=visited, 
            depth=depth+1,
            include_interfaces=include_interfaces,
            include_methods=include_methods,
            filter_packages=filter_packages
        )


def detect_multiple_inheritance(cls: Class) -> List[Tuple[Class, List[Class]]]:
    """
    Detects multiple inheritance in a class hierarchy.
    
    Args:
        cls: The class to check for multiple inheritance
        
    Returns:
        A list of tuples containing classes with multiple inheritance and their parent classes
    """
    result = []
    
    # Check if the class has multiple direct parents
    if cls.parent_classes and len(cls.parent_class_names) > 1:
        parent_classes = [p for p in cls.superclasses(max_depth=1) if isinstance(p, Class)]
        if len(parent_classes) > 1:
            result.append((cls, parent_classes))
    
    # Recursively check subclasses
    for subclass in cls.subclasses(max_depth=1):
        if isinstance(subclass, Class):
            result.extend(detect_multiple_inheritance(subclass))
    
    return result


def highlight_multiple_inheritance(G: DiGraph) -> DiGraph:
    """
    Highlights multiple inheritance relationships in the graph.
    
    Args:
        G: The inheritance graph
        
    Returns:
        The updated graph with highlighted multiple inheritance
    """
    # Find nodes with multiple parents
    for node in G.nodes():
        if isinstance(node, Class):
            parents = list(G.successors(node))
            if len(parents) > 1:
                # Highlight the node with multiple inheritance
                G.nodes[node]["color"] = "#f542f5"  # Purple for multiple inheritance
                G.nodes[node]["multiple_inheritance"] = True
                
                # Highlight the edges to parent classes
                for parent in parents:
                    G[node][parent]["color"] = "#f542f5"  # Purple for multiple inheritance edges
                    G[node][parent]["width"] = 2.0  # Thicker edges
    
    return G


def find_common_ancestors(G: DiGraph, classes: List[Class]) -> List[Class]:
    """
    Finds common ancestors of multiple classes in the inheritance hierarchy.
    
    Args:
        G: The inheritance graph
        classes: List of classes to find common ancestors for
        
    Returns:
        List of common ancestor classes
    """
    if not classes:
        return []
    
    # Get all ancestors for each class
    ancestors_sets = []
    for cls in classes:
        ancestors = set()
        for path in nx.all_simple_paths(G, cls, None):
            ancestors.update(path[1:])  # Exclude the class itself
        ancestors_sets.append(ancestors)
    
    # Find intersection of all ancestor sets
    common_ancestors = set.intersection(*ancestors_sets) if ancestors_sets else set()
    
    return [a for a in common_ancestors if isinstance(a, Class)]


def add_method_override_info(G: DiGraph) -> DiGraph:
    """
    Adds information about method overrides to the graph.
    
    Args:
        G: The inheritance graph
        
    Returns:
        The updated graph with method override information
    """
    for node in G.nodes():
        if not isinstance(node, Class):
            continue
            
        # Skip if methods are not included
        if "methods" not in G.nodes[node]:
            continue
            
        # Get all superclasses
        superclasses = list(G.successors(node))
        
        # Check each method to see if it overrides a method in a superclass
        for i, method_info in enumerate(G.nodes[node]["methods"]):
            method_name = method_info["name"]
            
            for superclass in superclasses:
                if not isinstance(superclass, Class) or "methods" not in G.nodes[superclass]:
                    continue
                    
                # Check if the superclass has a method with the same name
                for super_method in G.nodes[superclass]["methods"]:
                    if super_method["name"] == method_name:
                        # Mark the method as overriding
                        G.nodes[node]["methods"][i]["overrides"] = superclass.name
                        break
    
    return G

