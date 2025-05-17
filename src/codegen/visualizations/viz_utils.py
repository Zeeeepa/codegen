import json
import os
from dataclasses import asdict
from typing import TYPE_CHECKING, Dict, List, Optional, Union

import networkx as nx
from networkx import DiGraph, Graph

from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.interfaces.importable import Importable
from codegen.sdk.output.utils import DeterministicJSONEncoder
from codegen.visualizations.enums import ElementType, GraphJson, GraphType, SelectedElement

if TYPE_CHECKING:
    from codegen.git.repo_operator.repo_operator import RepoOperator
    from codegen.sdk.core.class_definition import Class
    from codegen.sdk.core.file import File
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
# SELECTION ROW FUNCTIONALITY
####################################################################################################################


def get_element_type(element: Union["Symbol", "File", "Function", "Class"]) -> ElementType:
    """Determine the type of the element."""
    from codegen.sdk.core.class_definition import Class
    from codegen.sdk.core.file import File
    from codegen.sdk.core.function import Function
    from codegen.sdk.core.symbol import Symbol

    if isinstance(element, Symbol):
        return ElementType.SYMBOL
    elif isinstance(element, File):
        return ElementType.FILE
    elif isinstance(element, Function):
        return ElementType.FUNCTION
    elif isinstance(element, Class):
        return ElementType.CLASS
    else:
        raise ValueError(f"Unknown element type: {type(element)}")


def get_element_methods(element: Union["Symbol", "File", "Function", "Class"]) -> List[str]:
    """Get methods associated with the element."""
    from codegen.sdk.core.class_definition import Class
    from codegen.sdk.core.file import File
    from codegen.sdk.core.function import Function

    methods = []
    
    if isinstance(element, Class):
        # For a class, return all its methods
        methods = [method.name for method in element.methods]
    elif isinstance(element, File):
        # For a file, return all functions defined in it
        methods = [func.name for func in element.functions]
    elif isinstance(element, Function):
        # For a function, return its name and any nested functions
        methods = [element.name]
        # Add any nested functions if available
        if hasattr(element, 'nested_functions'):
            methods.extend([func.name for func in element.nested_functions])
    
    return methods


def get_related_elements(element: Union["Symbol", "File", "Function", "Class"]) -> List[str]:
    """Get elements related to the selected element."""
    from codegen.sdk.core.class_definition import Class
    from codegen.sdk.core.file import File
    from codegen.sdk.core.function import Function
    from codegen.sdk.core.symbol import Symbol

    related = []
    
    if isinstance(element, Symbol):
        # For a symbol, return its usages
        if hasattr(element, 'usages'):
            related = [usage.name for usage in element.usages]
    elif isinstance(element, File):
        # For a file, return imported files
        if hasattr(element, 'imports'):
            related = [imp.module_name for imp in element.imports]
    elif isinstance(element, Function):
        # For a function, return functions it calls
        if hasattr(element, 'function_calls'):
            related = [call.name for call in element.function_calls]
    elif isinstance(element, Class):
        # For a class, return parent classes
        if hasattr(element, 'bases'):
            related = [base.name for base in element.bases]
    
    return related


def create_selected_element(element: Union["Symbol", "File", "Function", "Class"]) -> SelectedElement:
    """Create a SelectedElement object from the given element."""
    element_type = get_element_type(element)
    element_id = get_node_id(element)
    element_name = element.name if hasattr(element, 'name') else str(element)
    element_methods = get_element_methods(element)
    related_elements = get_related_elements(element)
    
    return SelectedElement(
        type=element_type,
        id=element_id,
        name=element_name,
        methods=element_methods,
        related_elements=related_elements
    )


def selected_element_to_json(element: SelectedElement) -> str:
    """Convert a SelectedElement to JSON."""
    return json.dumps(asdict(element), cls=DeterministicJSONEncoder, indent=2)
