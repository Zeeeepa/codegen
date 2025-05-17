import json
import os
from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Optional, Union

import networkx as nx
import plotly.graph_objects as go
from networkx import DiGraph, Graph

from codegen.sdk.core.function import Function
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.interfaces.importable import Importable
from codegen.sdk.output.utils import DeterministicJSONEncoder
from codegen.visualizations.enums import (
    CallGraphEdgeType,
    CallGraphFilterType,
    GraphJson,
    GraphType,
    VizEdge,
)

if TYPE_CHECKING:
    from codegen.git.repo_operator.repo_operator import RepoOperator
    from codegen.sdk.core.class_definition import Class
    from codegen.sdk.core.detached_symbols.function_call import FunctionCall
    from codegen.sdk.core.external_module import ExternalModule

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


def get_node_options(node: Editable | str | int) -> dict[str, Any]:
    """Get visualization options for a node.

    Args:
        node: The node to get options for

    Returns:
        A dictionary of visualization options
    """
    if isinstance(node, Editable):
        return asdict(node.viz)
    return {}


def get_node_id(node: Editable | str | int) -> str:
    """Get a unique identifier for a node.

    Args:
        node: The node to get an ID for

    Returns:
        A string identifier for the node
    """
    if isinstance(node, Importable):
        return node.node_id
    elif isinstance(node, Editable):
        return str(node.span)
    elif isinstance(node, str) or isinstance(node, int):
        return str(node)


def graph_to_json(G1: Graph, root: Editable | str | int | None = None) -> str:
    """Convert a NetworkX graph to JSON for visualization.

    Args:
        G1: The NetworkX graph to convert
        root: The root node for tree visualization

    Returns:
        A JSON string representation of the graph
    """
    G2 = DiGraph()
    for node_tuple in G1.nodes(data=True):
        options = get_node_options(node_tuple[0])
        options.update(node_tuple[1])
        G2.add_node(get_node_id(node_tuple[0]), **options)

    for edge_tuple in G1.edges(data=True):
        options = edge_tuple[2]
        if "symbol" in options:
            options.update(get_node_options(options["symbol"]))
            del options["symbol"]
        G2.add_edge(get_node_id(edge_tuple[0]), get_node_id(edge_tuple[1]), **options)

    if root:
        root = get_node_id(root)
        return json.dumps(asdict(GraphJson(type=GraphType.TREE.value, data=nx.tree_data(G2, root))), cls=DeterministicJSONEncoder, indent=2)
    else:
        return json.dumps(asdict(GraphJson(type=GraphType.GRAPH.value, data=nx.node_link_data(G2))), cls=DeterministicJSONEncoder, indent=2)


####################################################################################################################
# ENHANCED CALL GRAPH VISUALIZATION
####################################################################################################################


def create_call_graph(
    source_function: Function,
    max_depth: int = 5,
    include_external: bool = False,
    include_recursive: bool = True,
    filters: Optional[dict[CallGraphFilterType, Any]] = None,
) -> tuple[DiGraph, dict[str, Any]]:
    """Create an enhanced call graph for visualization.

    Args:
        source_function: The function to create a call graph for
        max_depth: Maximum depth of the call graph
        include_external: Whether to include external module calls
        include_recursive: Whether to include recursive calls
        filters: Filters to apply to the call graph

    Returns:
        A tuple containing the call graph and metadata
    """
    G = DiGraph()
    visited_nodes: set[str] = set()
    edge_counts: dict[str, int] = {}
    metadata = {
        "node_count": 0,
        "edge_count": 0,
        "max_depth_reached": False,
        "filters_applied": filters or {},
    }

    # Apply default filters if none provided
    if filters is None:
        filters = {
            CallGraphFilterType.DEPTH: max_depth,
            CallGraphFilterType.FUNCTION_TYPE: "all",
            CallGraphFilterType.PRIVACY: "all",
        }

    def add_node_with_metadata(func: Union[Function, "Class", "ExternalModule"]) -> str:
        """Add a node to the graph with enhanced metadata."""
        node_id = get_node_id(func)

        if node_id in visited_nodes:
            return node_id

        visited_nodes.add(node_id)
        metadata["node_count"] += 1

        # Basic node attributes
        node_attrs = {
            "name": func.name,
            "file_path": getattr(func, "filepath", None),
            "symbol_name": func.__class__.__name__,
        }

        # Enhanced attributes for Function objects
        if isinstance(func, Function):
            node_attrs.update(
                {
                    "is_async": func.is_async,
                    "is_method": func.is_method,
                    "is_private": func.is_private,
                    "module": func.filepath.split("/")[-2] if func.filepath else None,
                    "parent_class": func.parent_class.name if func.is_method else None,
                    "return_type": str(func.return_type) if func.return_type else None,
                    "parameters": [p.name for p in func.parameters] if hasattr(func, "parameters") else [],
                    "complexity": len(func.code_block.statements) if hasattr(func, "code_block") else 0,
                }
            )

        G.add_node(node_id, **node_attrs)
        return node_id

    def add_edge_with_metadata(source_id: str, target_id: str, call: "FunctionCall", call_type: CallGraphEdgeType = CallGraphEdgeType.DIRECT) -> None:
        """Add an edge to the graph with enhanced metadata."""
        edge_key = f"{source_id}-{target_id}"

        # Track call counts for each edge
        if edge_key in edge_counts:
            edge_counts[edge_key] += 1
        else:
            edge_counts[edge_key] = 1
            metadata["edge_count"] += 1

        edge_attrs = asdict(
            VizEdge(
                name=call.name,
                source=source_id,
                target=target_id,
                call_type=call_type.value,
                file_path=call.filepath,
                start_point=call.start_point,
                end_point=call.end_point,
                weight=edge_counts[edge_key],
                label=f"{call.name}()" if hasattr(call, "name") else "call",
            )
        )

        # Set edge style based on call type
        if call_type == CallGraphEdgeType.RECURSIVE:
            edge_attrs["style"] = "dashed"
            edge_attrs["color"] = "#FF5733"  # Orange-red
        elif call_type == CallGraphEdgeType.ASYNC:
            edge_attrs["style"] = "dotted"
            edge_attrs["color"] = "#33A1FF"  # Light blue
        elif call_type == CallGraphEdgeType.EXTERNAL:
            edge_attrs["style"] = "dashdot"
            edge_attrs["color"] = "#AAAAAA"  # Gray
        else:
            edge_attrs["style"] = "solid"
            edge_attrs["color"] = "#333333"  # Dark gray

        G.add_edge(source_id, target_id, **edge_attrs)

    def should_include_node(func: Union[Function, "Class", "ExternalModule"]) -> bool:
        """Determine if a node should be included based on filters."""
        # Filter by function type
        func_type_filter = filters.get(CallGraphFilterType.FUNCTION_TYPE, "all")
        if func_type_filter != "all":
            if func_type_filter == "method" and not getattr(func, "is_method", False):
                return False
            if func_type_filter == "function" and getattr(func, "is_method", True):
                return False

        # Filter by privacy
        privacy_filter = filters.get(CallGraphFilterType.PRIVACY, "all")
        if privacy_filter != "all":
            is_private = getattr(func, "is_private", False)
            if privacy_filter == "private" and not is_private:
                return False
            if privacy_filter == "public" and is_private:
                return False

        # Filter by module
        module_filter = filters.get(CallGraphFilterType.MODULE, None)
        if module_filter:
            module = func.filepath.split("/")[-2] if getattr(func, "filepath", None) else None
            if module != module_filter:
                return False

        return True

    def traverse_calls(func: Function, depth: int = 0) -> None:
        """Recursively traverse function calls to build the graph."""
        if depth >= filters.get(CallGraphFilterType.DEPTH, max_depth):
            metadata["max_depth_reached"] = True
            return

        source_id = add_node_with_metadata(func)

        for call in func.function_calls:
            target_func = call.function_definition

            # Skip if no function definition found
            if not target_func:
                continue

            # Determine call type
            call_type = CallGraphEdgeType.DIRECT
            if target_func.name == func.name:
                if not include_recursive:
                    continue
                call_type = CallGraphEdgeType.RECURSIVE
            elif getattr(target_func, "is_async", False):
                call_type = CallGraphEdgeType.ASYNC
            elif not hasattr(target_func, "function_calls"):
                call_type = CallGraphEdgeType.EXTERNAL
                if not include_external:
                    continue

            # Apply filters
            if not should_include_node(target_func):
                continue

            # Add target node and edge
            target_id = add_node_with_metadata(target_func)
            add_edge_with_metadata(source_id, target_id, call, call_type)

            # Continue traversal if target is a Function
            if hasattr(target_func, "function_calls"):
                traverse_calls(target_func, depth + 1)

    # Start traversal from source function
    if should_include_node(source_function):
        traverse_calls(source_function)

    return G, metadata


def create_interactive_call_graph(
    G: DiGraph,
    metadata: dict[str, Any],
    highlight_node: Optional[str] = None,
    layout: str = "dot",
) -> go.Figure:
    """Create an interactive Plotly figure for call graph visualization.

    Args:
        G: The call graph
        metadata: Metadata about the graph
        highlight_node: Node to highlight
        layout: Layout algorithm to use

    Returns:
        A Plotly figure object
    """
    # Use networkx to calculate positions
    if layout == "dot":
        pos = nx.nx_agraph.graphviz_layout(G, prog="dot")
    elif layout == "circular":
        pos = nx.circular_layout(G)
    elif layout == "spring":
        pos = nx.spring_layout(G)
    else:
        pos = nx.kamada_kawai_layout(G)

    # Extract node positions
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []

    for node in G.nodes():
        node_attrs = G.nodes[node]
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        # Create detailed hover text
        hover_text = f"<b>{node_attrs.get('name', 'Unknown')}</b><br>"
        if node_attrs.get("is_method", False):
            hover_text += f"Method of: {node_attrs.get('parent_class', 'Unknown')}<br>"
        if node_attrs.get("is_async", False):
            hover_text += "Async: Yes<br>"
        if node_attrs.get("is_private", False):
            hover_text += "Private: Yes<br>"
        if node_attrs.get("file_path"):
            hover_text += f"File: {node_attrs.get('file_path')}<br>"
        if node_attrs.get("parameters"):
            params = ", ".join(node_attrs.get("parameters", []))
            hover_text += f"Parameters: {params}<br>"
        if node_attrs.get("return_type"):
            hover_text += f"Returns: {node_attrs.get('return_type')}<br>"

        node_text.append(hover_text)

        # Set node color based on type
        if node == highlight_node:
            node_color.append("#FF0000")  # Red for highlighted node
        elif node_attrs.get("is_async", False):
            node_color.append("#33A1FF")  # Light blue for async functions
        elif node_attrs.get("is_method", False):
            node_color.append("#A277FF")  # Purple for methods
        elif node_attrs.get("symbol_name") == "ExternalModule":
            node_color.append("#AAAAAA")  # Gray for external modules
        else:
            node_color.append("#9CDCFE")  # Default blue for functions

        # Set node size based on complexity
        complexity = node_attrs.get("complexity", 5)
        node_size.append(10 + min(complexity, 20))

    # Create node trace
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hoverinfo="text",
        text=node_text,
        marker=dict(
            color=node_color,
            size=node_size,
            line=dict(width=2, color="#FFFFFF"),
        ),
    )

    # Extract edge positions and attributes
    edge_x = []
    edge_y = []
    edge_color = []
    edge_width = []
    edge_dash = []

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_attrs = G.edges[edge]

        # Add line trace for each edge
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

        # Set edge color and style
        edge_color.append(edge_attrs.get("color", "#333333"))
        edge_width.append(1 + min(edge_attrs.get("weight", 1), 5))

        # Set dash style based on edge type
        if edge_attrs.get("style") == "dashed":
            edge_dash.append("dash")
        elif edge_attrs.get("style") == "dotted":
            edge_dash.append("dot")
        elif edge_attrs.get("style") == "dashdot":
            edge_dash.append("dashdot")
        else:
            edge_dash.append("solid")

    # Create edge traces (one for each dash style)
    edge_traces = []
    dash_styles = set(edge_dash)

    for dash_style in dash_styles:
        indices = [i for i, d in enumerate(edge_dash) if d == dash_style]
        if not indices:
            continue

        # Extract data for this dash style
        style_x = [edge_x[i] for i in indices]
        style_y = [edge_y[i] for i in indices]
        style_color = [edge_color[i] for i in indices]
        style_width = [edge_width[i] for i in indices]

        edge_traces.append(
            go.Scatter(
                x=style_x,
                y=style_y,
                mode="lines",
                line=dict(
                    color=style_color,
                    width=style_width,
                    dash=dash_style,
                ),
                hoverinfo="none",
            )
        )

    # Create figure
    fig = go.Figure(
        data=[*edge_traces, node_trace],
        layout=go.Layout(
            title=f"Call Graph ({metadata['node_count']} nodes, {metadata['edge_count']} edges)",
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="#FFFFFF",
        ),
    )

    # Add buttons for different layouts
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                buttons=[
                    dict(
                        args=[{"visible": [True] * len(fig.data)}],
                        label="All",
                        method="update",
                    ),
                    dict(
                        args=[
                            {"visible": [t.name.startswith("lines") for t in fig.data]},
                        ],
                        label="Edges Only",
                        method="update",
                    ),
                    dict(
                        args=[
                            {"visible": [not t.name.startswith("lines") for t in fig.data]},
                        ],
                        label="Nodes Only",
                        method="update",
                    ),
                ],
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.1,
                xanchor="left",
                y=1.1,
                yanchor="top",
            ),
        ]
    )

    return fig


def apply_call_graph_filters(
    G: DiGraph,
    filters: dict[CallGraphFilterType, Any],
) -> DiGraph:
    """Apply filters to a call graph.

    Args:
        G: The call graph to filter
        filters: Filters to apply

    Returns:
        A filtered call graph
    """
    filtered_G = G.copy()
    nodes_to_remove = []

    for node, attrs in filtered_G.nodes(data=True):
        # Filter by function type
        func_type_filter = filters.get(CallGraphFilterType.FUNCTION_TYPE, "all")
        if func_type_filter != "all":
            if func_type_filter == "method" and not attrs.get("is_method", False):
                nodes_to_remove.append(node)
                continue
            if func_type_filter == "function" and attrs.get("is_method", True):
                nodes_to_remove.append(node)
                continue

        # Filter by privacy
        privacy_filter = filters.get(CallGraphFilterType.PRIVACY, "all")
        if privacy_filter != "all":
            is_private = attrs.get("is_private", False)
            if privacy_filter == "private" and not is_private:
                nodes_to_remove.append(node)
                continue
            if privacy_filter == "public" and is_private:
                nodes_to_remove.append(node)
                continue

        # Filter by module
        module_filter = filters.get(CallGraphFilterType.MODULE, None)
        if module_filter:
            module = attrs.get("file_path", "").split("/")[-2] if attrs.get("file_path") else None
            if module != module_filter:
                nodes_to_remove.append(node)
                continue

        # Filter by complexity
        complexity_filter = filters.get(CallGraphFilterType.COMPLEXITY, None)
        if complexity_filter is not None:
            complexity = attrs.get("complexity", 0)
            if complexity < complexity_filter:
                nodes_to_remove.append(node)
                continue

        # Filter by call count
        call_count_filter = filters.get(CallGraphFilterType.CALL_COUNT, None)
        if call_count_filter is not None:
            # Count incoming edges
            in_edges = filtered_G.in_edges(node)
            if len(in_edges) < call_count_filter:
                nodes_to_remove.append(node)
                continue

    # Remove filtered nodes
    for node in nodes_to_remove:
        filtered_G.remove_node(node)

    return filtered_G
