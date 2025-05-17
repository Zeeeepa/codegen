"""Enhanced module dependency visualization example.

This example demonstrates the enhanced module dependency visualization features,
including detailed relationship visualization, interactive navigation, filtering options,
and handling of complex dependency graphs.
"""

import codegen
from codegen import Codebase
from codegen.visualizations.module_dependency_viz import build_module_dependency_graph


@codegen.function("visualize-enhanced-modules-dependencies")
def run(codebase: Codebase, path_filter: str = None, max_depth: int = None, include_external: bool = False):
    """Visualize module dependencies with enhanced features.
    
    Args:
        codebase: The codebase to analyze
        path_filter: Optional path prefix to filter modules by
        max_depth: Optional maximum dependency depth to include
        include_external: Whether to include external module dependencies
    """
    # Build the module dependency graph
    module_graph = build_module_dependency_graph(
        codebase.files,
        include_external=include_external,
        path_filter=path_filter
    )
    
    # Detect circular dependencies
    circular_deps = module_graph.detect_circular_dependencies()
    if circular_deps:
        print(f"Found {len(circular_deps)} circular dependencies:")
        for i, cycle in enumerate(circular_deps[:5]):  # Show first 5 cycles
            print(f"  Cycle {i+1}: {' -> '.join(cycle)} -> {cycle[0]}")
        if len(circular_deps) > 5:
            print(f"  ... and {len(circular_deps) - 5} more")
    else:
        print("No circular dependencies found.")
    
    # Calculate module metrics
    metrics = module_graph.get_module_metrics()
    
    # Find most imported modules
    most_imported = sorted(
        [(module_id, data["imported_by_count"]) for module_id, data in metrics.items()],
        key=lambda x: x[1],
        reverse=True
    )
    
    print("\nMost imported modules:")
    for module_id, count in most_imported[:5]:  # Show top 5
        print(f"  {module_id}: imported by {count} modules")
    
    # Find modules with most imports
    most_imports = sorted(
        [(module_id, data["imports_count"]) for module_id, data in metrics.items()],
        key=lambda x: x[1],
        reverse=True
    )
    
    print("\nModules with most imports:")
    for module_id, count in most_imports[:5]:  # Show top 5
        print(f"  {module_id}: imports {count} modules")
    
    # Apply depth filtering if specified
    if max_depth is not None and most_imported:
        # Use the most imported module as the root for depth filtering
        root_module = most_imported[0][0]
        print(f"\nFiltering to depth {max_depth} from {root_module}")
        module_graph = module_graph.filter_by_depth(root_module, max_depth)
    
    # Visualize the graph
    print("\nVisualizing module dependencies...")
    codebase.visualize(module_graph)
    print("Use codegen.sh to view the visualization!")


@codegen.function("visualize-module-dependencies-by-path")
def visualize_by_path(codebase: Codebase, path_prefix: str):
    """Visualize module dependencies for a specific path prefix.
    
    Args:
        codebase: The codebase to analyze
        path_prefix: The path prefix to filter by
    """
    # Build the module dependency graph
    module_graph = build_module_dependency_graph(codebase.files)
    
    # Filter by path
    filtered_graph = module_graph.filter_by_module_path(path_prefix)
    
    # Visualize the filtered graph
    print(f"Visualizing module dependencies for path: {path_prefix}")
    codebase.visualize(filtered_graph)
    print("Use codegen.sh to view the visualization!")


@codegen.function("analyze-circular-dependencies")
def analyze_circular_dependencies(codebase: Codebase):
    """Analyze and visualize circular dependencies in the codebase.
    
    Args:
        codebase: The codebase to analyze
    """
    # Build the module dependency graph
    module_graph = build_module_dependency_graph(codebase.files)
    
    # Detect circular dependencies
    circular_deps = module_graph.detect_circular_dependencies()
    
    if not circular_deps:
        print("No circular dependencies found.")
        return
    
    print(f"Found {len(circular_deps)} circular dependencies:")
    for i, cycle in enumerate(circular_deps):
        print(f"  Cycle {i+1}: {' -> '.join(cycle)} -> {cycle[0]}")
    
    # Visualize the graph with circular dependencies highlighted
    print("\nVisualizing circular dependencies...")
    codebase.visualize(module_graph)
    print("Use codegen.sh to view the visualization! Circular dependencies are highlighted in red.")


if __name__ == "__main__":
    # Example usage with the Sentry codebase
    codebase = Codebase.from_repo(
        "getsentry/sentry", 
        commit="fb0d53b2210cc896fc3e2cf32dae149ea8a8a45a", 
        language="python"
    )
    
    # Run the enhanced module dependency visualization
    run(codebase, path_filter="src/sentry/api", include_external=False)
    
    # Alternatively, visualize by path
    # visualize_by_path(codebase, "src/sentry/api")
    
    # Or analyze circular dependencies
    # analyze_circular_dependencies(codebase)

