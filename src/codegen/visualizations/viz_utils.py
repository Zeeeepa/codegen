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
    from codegen.sdk.core.class_definition import Class
    from codegen.sdk.core.function import Function
    from codegen.sdk.core.symbol import Symbol

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


def graph_to_json(G1: Graph, root: Editable | str | int | None = None, graph_type: GraphType = None):
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
    elif graph_type:
        if graph_type == GraphType.INHERITANCE:
            return json.dumps(asdict(GraphJson(type=GraphType.INHERITANCE.value, data=nx.node_link_data(G2))), cls=DeterministicJSONEncoder, indent=2)
        elif graph_type == GraphType.CALL_GRAPH:
            return json.dumps(asdict(GraphJson(type=GraphType.CALL_GRAPH.value, data=nx.node_link_data(G2))), cls=DeterministicJSONEncoder, indent=2)
        elif graph_type == GraphType.DEPENDENCY_GRAPH:
            return json.dumps(asdict(GraphJson(type=GraphType.DEPENDENCY_GRAPH.value, data=nx.node_link_data(G2))), cls=DeterministicJSONEncoder, indent=2)
        elif graph_type == GraphType.MODULE_DEPENDENCIES:
            return json.dumps(asdict(GraphJson(type=GraphType.MODULE_DEPENDENCIES.value, data=nx.node_link_data(G2))), cls=DeterministicJSONEncoder, indent=2)
    else:
        return json.dumps(asdict(GraphJson(type=GraphType.GRAPH.value, data=nx.node_link_data(G2))), cls=DeterministicJSONEncoder, indent=2)


####################################################################################################################
# ENHANCED VISUALIZATION UTILITIES
####################################################################################################################

def create_inheritance_graph(class_obj: "Class", max_depth: int = 3) -> Graph:
    """
    Create an inheritance graph for a class.
    
    Args:
        class_obj: The class to create the inheritance graph for
        max_depth: Maximum depth of the inheritance hierarchy to include
        
    Returns:
        A NetworkX Graph representing the inheritance hierarchy
    """
    G = DiGraph()
    
    def add_class_to_graph(cls: "Class", current_depth: int = 0):
        if current_depth > max_depth:
            return
            
        # Add the class node
        G.add_node(cls, name=cls.name, color="#ffca85", type="Class")
        
        # Add parent classes
        for parent in cls.parent_classes:
            if parent:
                G.add_node(parent, name=parent.name, color="#ffca85", type="Class")
                G.add_edge(cls, parent, type="inherits")
                add_class_to_graph(parent, current_depth + 1)
                
        # Add child classes
        for child in cls.child_classes:
            if child:
                G.add_node(child, name=child.name, color="#ffca85", type="Class")
                G.add_edge(child, cls, type="inherits")
                add_class_to_graph(child, current_depth + 1)
    
    add_class_to_graph(class_obj)
    return G


def create_call_graph(function: "Function", max_depth: int = 3, include_external: bool = False) -> Graph:
    """
    Create a call graph for a function.
    
    Args:
        function: The function to create the call graph for
        max_depth: Maximum depth of the call graph to include
        include_external: Whether to include external module calls
        
    Returns:
        A NetworkX Graph representing the call graph
    """
    G = DiGraph()
    visited = set()
    
    def add_function_to_graph(func: "Function", current_depth: int = 0):
        if current_depth > max_depth or func in visited:
            return
            
        visited.add(func)
        
        # Add the function node
        func_name = f"{func.parent_class.name}.{func.name}" if func.is_method else func.name
        G.add_node(func, name=func_name, color="#a277ff", type="Function")
        
        # Add function calls
        for call in func.function_calls:
            called_func = call.function_definition
            if not called_func:
                continue
                
            # Skip external modules if not included
            if not include_external and hasattr(called_func, "is_external") and called_func.is_external:
                continue
                
            # Add the called function node
            called_func_name = f"{called_func.parent_class.name}.{called_func.name}" if hasattr(called_func, "is_method") and called_func.is_method else called_func.name
            G.add_node(called_func, name=called_func_name, color="#a277ff", type="Function")
            G.add_edge(func, called_func, type="calls", name=call.name)
            
            # Recursively add called functions
            add_function_to_graph(called_func, current_depth + 1)
    
    add_function_to_graph(function)
    return G


def create_dependency_graph(symbol: "Symbol", max_depth: int = 3, include_external: bool = False) -> Graph:
    """
    Create a dependency graph for a symbol.
    
    Args:
        symbol: The symbol to create the dependency graph for
        max_depth: Maximum depth of the dependency graph to include
        include_external: Whether to include external module dependencies
        
    Returns:
        A NetworkX Graph representing the dependency graph
    """
    G = DiGraph()
    visited = set()
    
    def add_symbol_to_graph(sym: "Symbol", current_depth: int = 0):
        if current_depth > max_depth or sym in visited:
            return
            
        visited.add(sym)
        
        # Add the symbol node
        G.add_node(sym, name=sym.name, color="#a277ff", type=sym.__class__.__name__)
        
        # Add dependencies
        for dep in sym.dependencies:
            if not include_external and hasattr(dep, "is_external") and dep.is_external:
                continue
                
            # Add the dependency node
            G.add_node(dep, name=dep.name, color="#a277ff", type=dep.__class__.__name__)
            G.add_edge(sym, dep, type="depends_on")
            
            # Recursively add dependencies
            add_symbol_to_graph(dep, current_depth + 1)
    
    add_symbol_to_graph(symbol)
    return G


def create_module_dependency_graph(file_obj, max_depth: int = 3, include_external: bool = False) -> Graph:
    """
    Create a module dependency graph for a file.
    
    Args:
        file_obj: The file to create the module dependency graph for
        max_depth: Maximum depth of the module dependency graph to include
        include_external: Whether to include external module dependencies
        
    Returns:
        A NetworkX Graph representing the module dependency graph
    """
    G = DiGraph()
    visited = set()
    
    def add_file_to_graph(file, current_depth: int = 0):
        if current_depth > max_depth or file in visited:
            return
            
        visited.add(file)
        
        # Add the file node
        G.add_node(file, name=file.path.name, color="#80CBC4", type="File")
        
        # Add imports
        for imp in file.imports:
            imported_file = imp.resolved_file
            if not imported_file:
                continue
                
            # Skip external modules if not included
            if not include_external and hasattr(imported_file, "is_external") and imported_file.is_external:
                continue
                
            # Add the imported file node
            G.add_node(imported_file, name=imported_file.path.name, color="#80CBC4", type="File")
            G.add_edge(file, imported_file, type="imports")
            
            # Recursively add imported files
            add_file_to_graph(imported_file, current_depth + 1)
    
    add_file_to_graph(file_obj)
    return G
