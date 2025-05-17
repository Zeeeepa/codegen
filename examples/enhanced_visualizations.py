#!/usr/bin/env python3
"""
Enhanced Visualization Examples

This script demonstrates the enhanced visualization features in Codegen.
It shows how to use the different visualization types and options.
"""

import argparse
import sys

from codegen import Codebase
from codegen.visualizations.enums import GraphType


def visualize_inheritance_hierarchy(codebase, class_name, max_depth=3):
    """
    Visualize the inheritance hierarchy of a class.
    
    Args:
        codebase: The codebase to visualize
        class_name: The name of the class to visualize
        max_depth: Maximum depth of the inheritance hierarchy to include
    """
    print(f"Visualizing inheritance hierarchy for class '{class_name}'...")
    
    # Get the class
    class_obj = codebase.get_class(class_name)
    if not class_obj:
        print(f"Class '{class_name}' not found in the codebase.")
        return
    
    # Visualize the inheritance hierarchy
    codebase.viz_manager.visualize_inheritance_hierarchy(class_obj, max_depth=max_depth)
    
    print(f"Inheritance hierarchy visualization created for class '{class_name}'.")
    print("Use codegen.sh to view the visualization.")


def visualize_call_graph(codebase, function_name, max_depth=3, include_external=False):
    """
    Visualize the call graph of a function.
    
    Args:
        codebase: The codebase to visualize
        function_name: The name of the function to visualize
        max_depth: Maximum depth of the call graph to include
        include_external: Whether to include external module calls
    """
    print(f"Visualizing call graph for function '{function_name}'...")
    
    # Get the function
    function = codebase.get_function(function_name)
    if not function:
        print(f"Function '{function_name}' not found in the codebase.")
        return
    
    # Visualize the call graph
    codebase.viz_manager.visualize_call_graph(function, max_depth=max_depth, include_external=include_external)
    
    print(f"Call graph visualization created for function '{function_name}'.")
    print("Use codegen.sh to view the visualization.")


def visualize_dependency_graph(codebase, symbol_name, max_depth=3, include_external=False):
    """
    Visualize the dependency graph of a symbol.
    
    Args:
        codebase: The codebase to visualize
        symbol_name: The name of the symbol to visualize
        max_depth: Maximum depth of the dependency graph to include
        include_external: Whether to include external module dependencies
    """
    print(f"Visualizing dependency graph for symbol '{symbol_name}'...")
    
    # Get the symbol
    symbol = codebase.get_symbol(symbol_name)
    if not symbol:
        print(f"Symbol '{symbol_name}' not found in the codebase.")
        return
    
    # Visualize the dependency graph
    codebase.viz_manager.visualize_dependency_graph(symbol, max_depth=max_depth, include_external=include_external)
    
    print(f"Dependency graph visualization created for symbol '{symbol_name}'.")
    print("Use codegen.sh to view the visualization.")


def visualize_module_dependencies(codebase, file_path, max_depth=3, include_external=False):
    """
    Visualize the module dependencies of a file.
    
    Args:
        codebase: The codebase to visualize
        file_path: The path of the file to visualize
        max_depth: Maximum depth of the module dependency graph to include
        include_external: Whether to include external module dependencies
    """
    print(f"Visualizing module dependencies for file '{file_path}'...")
    
    # Get the file
    file_obj = codebase.get_file(file_path)
    if not file_obj:
        print(f"File '{file_path}' not found in the codebase.")
        return
    
    # Visualize the module dependencies
    codebase.viz_manager.visualize_module_dependencies(file_obj, max_depth=max_depth, include_external=include_external)
    
    print(f"Module dependency visualization created for file '{file_path}'.")
    print("Use codegen.sh to view the visualization.")


def main():
    """
    Main function to parse arguments and run the appropriate visualization.
    """
    parser = argparse.ArgumentParser(description="Enhanced Visualization Examples")
    
    # Repository options
    parser.add_argument("--repo", required=True, help="Repository to visualize (e.g., 'owner/repo')")
    parser.add_argument("--commit", help="Commit hash to visualize (default: latest)")
    parser.add_argument("--language", default="python", help="Programming language of the codebase (default: python)")
    
    # Visualization type
    parser.add_argument("--type", choices=["inheritance", "call", "dependency", "module"], required=True,
                        help="Type of visualization to generate")
    
    # Entity to visualize
    parser.add_argument("--entity", required=True, help="Entity to visualize (class, function, symbol, or file)")
    
    # Visualization options
    parser.add_argument("--max-depth", type=int, default=3, help="Maximum depth for recursive visualizations (default: 3)")
    parser.add_argument("--include-external", action="store_true", help="Include external dependencies in the visualization")
    
    args = parser.parse_args()
    
    # Initialize codebase
    print(f"Initializing codebase from repository '{args.repo}'...")
    if args.commit:
        codebase = Codebase.from_repo(args.repo, commit=args.commit, language=args.language)
    else:
        codebase = Codebase.from_repo(args.repo, language=args.language)
    
    # Generate visualization based on type
    if args.type == "inheritance":
        visualize_inheritance_hierarchy(codebase, args.entity, max_depth=args.max_depth)
    elif args.type == "call":
        visualize_call_graph(codebase, args.entity, max_depth=args.max_depth, include_external=args.include_external)
    elif args.type == "dependency":
        visualize_dependency_graph(codebase, args.entity, max_depth=args.max_depth, include_external=args.include_external)
    elif args.type == "module":
        visualize_module_dependencies(codebase, args.entity, max_depth=args.max_depth, include_external=args.include_external)


if __name__ == "__main__":
    main()

