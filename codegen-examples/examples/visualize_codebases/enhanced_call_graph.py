import codegen
from codegen import Codebase
from codegen.sdk.core.function import Function
from codegen.visualizations.enums import CallGraphFilterType

# Configuration options for the call graph visualization
MAX_DEPTH = 5
INCLUDE_EXTERNAL = False
INCLUDE_RECURSIVE = True


@codegen.function("visualize-enhanced-call-graph")
def run(codebase: Codebase):
    """Generate an enhanced interactive visualization of function call relationships.

    This codemod:
    1. Creates a detailed call graph starting from a target function
    2. Includes rich metadata about functions and their relationships
    3. Provides interactive features for exploring the call graph
    4. Supports filtering by various criteria
    5. Generates a visual representation with improved aesthetics

    The enhanced call graph visualization includes:
    - Detailed function information (parameters, return types, etc.)
    - Visual differentiation between function types (methods, async, etc.)
    - Interactive navigation with zoom, pan, and node selection
    - Filtering options to focus on specific aspects of the code
    """
    print("Initializing enhanced call graph visualization...")

    # Find a target function to visualize
    # You can replace this with any function from your codebase
    target_function = None

    # Try to find a function with a reasonable number of calls
    for func in codebase.functions:
        if len(func.function_calls) > 3 and len(func.function_calls) < 20:
            target_function = func
            break

    if not target_function:
        # Fall back to the first function with any calls
        for func in codebase.functions:
            if func.function_calls:
                target_function = func
                break

    if not target_function:
        print("No suitable function found for visualization.")
        return

    print(f"Creating enhanced call graph for function: {target_function.name}")

    # Create basic call graph visualization
    basic_visualization(codebase, target_function)

    # Create filtered call graph visualization
    filtered_visualization(codebase, target_function)

    # Create interactive call graph visualization
    interactive_visualization(codebase, target_function)

    print("Enhanced call graph visualizations created.")
    print("Use codegen.sh to view the visualizations!")


def basic_visualization(codebase: Codebase, target_function: Function):
    """Create a basic call graph visualization."""
    print("Creating basic call graph visualization...")

    # Create the call graph using the enhanced visualization manager
    codebase.op.visualization_manager.visualize_call_graph(
        source_function=target_function,
        max_depth=MAX_DEPTH,
        include_external=INCLUDE_EXTERNAL,
        include_recursive=INCLUDE_RECURSIVE,
    )

    print("Basic call graph visualization created.")


def filtered_visualization(codebase: Codebase, target_function: Function):
    """Create a filtered call graph visualization."""
    print("Creating filtered call graph visualization...")

    # Apply filters to focus on specific aspects
    filters = {
        CallGraphFilterType.DEPTH: 3,  # Limit depth to 3 levels
        CallGraphFilterType.FUNCTION_TYPE: "method",  # Show only methods
        CallGraphFilterType.PRIVACY: "public",  # Show only public methods
    }

    # Create the filtered call graph
    codebase.op.visualization_manager.visualize_call_graph(
        source_function=target_function,
        filters=filters,
    )

    print("Filtered call graph visualization created.")


def interactive_visualization(codebase: Codebase, target_function: Function):
    """Create an interactive call graph visualization."""
    print("Creating interactive call graph visualization...")

    # Create the interactive call graph
    fig = codebase.op.visualization_manager.create_call_graph_visualization(
        source_function=target_function,
        max_depth=MAX_DEPTH,
        include_external=True,  # Include external calls for this visualization
        include_recursive=True,
        layout="dot",  # Use dot layout for hierarchical visualization
    )

    # Write the visualization data
    codebase.op.visualization_manager.write_graphviz_data(fig)

    print("Interactive call graph visualization created.")


def explore_call_graph_features(codebase: Codebase, target_function: Function):
    """Demonstrate advanced call graph exploration features."""
    print("Exploring call graph features...")

    # Create the call graph
    G, metadata = codegen.visualizations.viz_utils.create_call_graph(
        source_function=target_function,
        max_depth=MAX_DEPTH,
    )

    # Get call graph statistics
    stats = codebase.op.visualization_manager.get_call_graph_stats(G)

    print("Call graph statistics:")
    print(f"  Nodes: {stats['node_count']}")
    print(f"  Edges: {stats['edge_count']}")
    print(f"  Methods: {stats['function_types']['methods']}")
    print(f"  Functions: {stats['function_types']['functions']}")
    print(f"  Private: {stats['privacy']['private']}")
    print(f"  Public: {stats['privacy']['public']}")
    print(f"  Async: {stats['async']}")
    print(f"  Modules: {', '.join(stats['modules'])}")

    # Find the most called function
    in_degree = dict(G.in_degree())
    if in_degree:
        most_called_node = max(in_degree, key=in_degree.get)
        most_called_attrs = G.nodes[most_called_node]
        print(f"Most called function: {most_called_attrs.get('name', 'Unknown')} ({in_degree[most_called_node]} calls)")

    # Find the function that makes the most calls
    out_degree = dict(G.out_degree())
    if out_degree:
        most_calling_node = max(out_degree, key=out_degree.get)
        most_calling_attrs = G.nodes[most_calling_node]
        print(f"Function making most calls: {most_calling_attrs.get('name', 'Unknown')} ({out_degree[most_calling_node]} calls)")

    print("Call graph exploration complete.")


if __name__ == "__main__":
    print("Initializing codebase...")
    # You can replace this with your own repository
    codebase = Codebase.from_repo("codegen-oss/posthog", language="python")
    print(f"Codebase with {len(codebase.files)} files and {len(codebase.functions)} functions.")

    run(codebase)
