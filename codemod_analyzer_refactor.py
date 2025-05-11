#!/usr/bin/env python3
"""
Codemod for Refactoring Analyzer Functions

This script analyzes the functions in the codegen analyzers directory and
separates them into different modules based on their functionality and dependencies.

Usage:
    python codemod_analyzer_refactor.py [--dry-run] [--output-dir OUTPUT_DIR]

Options:
    --dry-run       Only analyze and print what would be done, without making changes
    --output-dir    Directory to output the refactored modules (default: ./refactored_analyzers)
"""

import os
import sys
import ast
import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional, Union
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict

# Configuration
ANALYZERS_DIR = "codegen-on-oss/codegen_on_oss/analyzers"
DEFAULT_OUTPUT_DIR = "refactored_analyzers"
IGNORED_FILES = {"__init__.py", "__pycache__"}
IGNORED_DIRS = {"__pycache__"}

# Function to extract class and function definitions from a file
def extract_definitions(file_path: str) -> Dict[str, Any]:
    """
    Extract class and function definitions from a Python file.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Dictionary containing extracted information
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return {
            'imports': [],
            'functions': [],
            'classes': [],
            'file_docstring': None,
            'content': content
        }
    
    imports = []
    functions = []
    classes = []
    file_docstring = None
    
    # Extract file docstring if present
    if (len(tree.body) > 0 and 
        isinstance(tree.body[0], ast.Expr) and 
        isinstance(tree.body[0].value, ast.Str)):
        file_docstring = tree.body[0].value.s
    
    # Extract imports
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(ast.unparse(node))
    
    # Extract functions
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            func_info = {
                'name': node.name,
                'code': ast.unparse(node),
                'docstring': ast.get_docstring(node),
                'lineno': node.lineno,
                'end_lineno': node.end_lineno,
                'dependencies': extract_dependencies(node),
                'is_method': False
            }
            functions.append(func_info)
    
    # Extract classes and their methods
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    method_info = {
                        'name': item.name,
                        'code': ast.unparse(item),
                        'docstring': ast.get_docstring(item),
                        'lineno': item.lineno,
                        'end_lineno': item.end_lineno,
                        'dependencies': extract_dependencies(item),
                        'is_method': True
                    }
                    class_methods.append(method_info)
            
            class_info = {
                'name': node.name,
                'code': ast.unparse(node),
                'docstring': ast.get_docstring(node),
                'methods': class_methods,
                'lineno': node.lineno,
                'end_lineno': node.end_lineno,
                'dependencies': extract_class_dependencies(node)
            }
            classes.append(class_info)
    
    return {
        'imports': imports,
        'functions': functions,
        'classes': classes,
        'file_docstring': file_docstring,
        'content': content
    }

def extract_dependencies(node: ast.AST) -> Set[str]:
    """
    Extract dependencies (names used) from a function or method.
    
    Args:
        node: AST node representing a function or method
        
    Returns:
        Set of names used in the function/method
    """
    dependencies = set()
    
    class NameVisitor(ast.NodeVisitor):
        def visit_Name(self, node):
            dependencies.add(node.id)
            self.generic_visit(node)
    
    visitor = NameVisitor()
    visitor.visit(node)
    return dependencies

def extract_class_dependencies(node: ast.ClassDef) -> Set[str]:
    """
    Extract dependencies from a class definition.
    
    Args:
        node: AST node representing a class
        
    Returns:
        Set of names used in the class
    """
    dependencies = set()
    
    # Add base classes
    for base in node.bases:
        if isinstance(base, ast.Name):
            dependencies.add(base.id)
        elif isinstance(base, ast.Attribute):
            # Handle cases like module.Class
            dependencies.add(ast.unparse(base))
    
    # Add dependencies from class body
    for item in node.body:
        if not isinstance(item, ast.FunctionDef):  # Skip methods, they're handled separately
            class NameVisitor(ast.NodeVisitor):
                def visit_Name(self, node):
                    dependencies.add(node.id)
                    self.generic_visit(node)
            
            visitor = NameVisitor()
            visitor.visit(item)
    
    return dependencies

def analyze_codebase(analyzers_dir: str) -> Dict[str, Any]:
    """
    Analyze the codebase to extract all definitions and their relationships.
    
    Args:
        analyzers_dir: Path to the analyzers directory
        
    Returns:
        Dictionary containing all extracted information
    """
    result = {
        'files': {},
        'all_functions': [],
        'all_classes': [],
        'dependency_graph': nx.DiGraph()
    }
    
    # Process all Python files in the directory
    for root, dirs, files in os.walk(analyzers_dir):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        
        for file in files:
            if file.endswith('.py') and file not in IGNORED_FILES:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, analyzers_dir)
                
                print(f"Analyzing {rel_path}...")
                
                # Extract definitions from the file
                definitions = extract_definitions(file_path)
                result['files'][rel_path] = definitions
                
                # Add functions to the global list
                for func in definitions['functions']:
                    func['file'] = rel_path
                    result['all_functions'].append(func)
                
                # Add classes to the global list
                for cls in definitions['classes']:
                    cls['file'] = rel_path
                    result['all_classes'].append(cls)
                    
                    # Add methods to the global function list
                    for method in cls['methods']:
                        method['file'] = rel_path
                        method['class'] = cls['name']
                        result['all_functions'].append(method)
    
    # Build dependency graph
    graph = nx.DiGraph()
    
    # Add all functions and classes as nodes
    for func in result['all_functions']:
        node_id = f"{func['file']}:{func['name']}"
        if 'class' in func:
            node_id = f"{func['file']}:{func['class']}.{func['name']}"
        graph.add_node(node_id, type='function', data=func)
    
    for cls in result['all_classes']:
        node_id = f"{cls['file']}:{cls['name']}"
        graph.add_node(node_id, type='class', data=cls)
    
    # Add edges for dependencies
    # This is a simplified approach - a more sophisticated analysis would trace
    # actual symbol references across files
    for func in result['all_functions']:
        source_id = f"{func['file']}:{func['name']}"
        if 'class' in func:
            source_id = f"{func['file']}:{func['class']}.{func['name']}"
            
            # Add edge from method to its class
            class_id = f"{func['file']}:{func['class']}"
            graph.add_edge(source_id, class_id, type='member_of')
        
        # Add edges for dependencies
        for dep in func['dependencies']:
            # This is a simplified approach - we're just looking for matching names
            for target_func in result['all_functions']:
                if target_func['name'] == dep:
                    target_id = f"{target_func['file']}:{target_func['name']}"
                    if 'class' in target_func:
                        target_id = f"{target_func['file']}:{target_func['class']}.{target_func['name']}"
                    graph.add_edge(source_id, target_id, type='calls')
            
            for target_class in result['all_classes']:
                if target_class['name'] == dep:
                    target_id = f"{target_class['file']}:{target_class['name']}"
                    graph.add_edge(source_id, target_id, type='uses')
    
    result['dependency_graph'] = graph
    return result

def identify_modules(analysis_result: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Identify new modules based on function and class relationships.
    
    Args:
        analysis_result: Result from analyze_codebase
        
    Returns:
        Dictionary mapping new module names to lists of function/class IDs
    """
    graph = analysis_result['dependency_graph']
    
    # Use community detection to identify related functions/classes
    try:
        from community import best_partition
        partition = best_partition(nx.Graph(graph))
    except ImportError:
        print("python-louvain package not available, using connected components instead")
        # Fallback to connected components
        components = list(nx.weakly_connected_components(graph))
        partition = {}
        for i, component in enumerate(components):
            for node in component:
                partition[node] = i
    
    # Group nodes by partition
    modules = defaultdict(list)
    for node, module_id in partition.items():
        modules[f"module_{module_id}"].append(node)
    
    # Refine module names based on content
    refined_modules = {}
    for module_id, nodes in modules.items():
        # Get the most common file for this module
        file_counts = defaultdict(int)
        for node in nodes:
            file = node.split(':')[0]
            file_counts[file] += 1
        
        if file_counts:
            most_common_file = max(file_counts.items(), key=lambda x: x[1])[0]
            base_name = os.path.splitext(os.path.basename(most_common_file))[0]
            
            # Get function types in this module
            func_types = set()
            for node in nodes:
                node_data = graph.nodes[node].get('data', {})
                if 'name' in node_data:
                    name = node_data['name']
                    if name.startswith('_'):
                        name = name[1:]  # Remove leading underscore
                    
                    # Extract function type from name (e.g., analyze_dependencies -> dependencies)
                    parts = name.split('_')
                    if len(parts) > 1 and parts[0] in ('analyze', 'get', 'find', 'extract', 'process'):
                        func_types.update(parts[1:])
            
            # Create module name
            if func_types:
                module_name = f"{base_name}_{'_'.join(sorted(func_types))}"
            else:
                module_name = base_name
            
            refined_modules[module_name] = nodes
        else:
            refined_modules[module_id] = nodes
    
    return refined_modules

def generate_module_code(module_name: str, nodes: List[str], analysis_result: Dict[str, Any]) -> str:
    """
    Generate code for a new module.
    
    Args:
        module_name: Name of the new module
        nodes: List of node IDs to include in this module
        analysis_result: Result from analyze_codebase
        
    Returns:
        Generated code for the module
    """
    graph = analysis_result['dependency_graph']
    
    # Collect all imports from original files
    all_imports = set()
    file_docstrings = {}
    
    for node in nodes:
        file, _ = node.split(':', 1)
        if file in analysis_result['files']:
            file_data = analysis_result['files'][file]
            all_imports.update(file_data['imports'])
            if file_data['file_docstring'] and file not in file_docstrings:
                file_docstrings[file] = file_data['file_docstring']
    
    # Create module docstring
    docstring = f'"""\n{module_name.replace("_", " ").title()} Module\n\n'
    docstring += f'This module contains functions and classes extracted from the original analyzers.\n'
    
    if file_docstrings:
        docstring += '\nOriginal file docstrings:\n\n'
        for file, ds in file_docstrings.items():
            docstring += f'From {file}:\n{ds}\n\n'
    
    docstring += '"""\n\n'
    
    # Add imports
    code = [docstring]
    code.extend(sorted(all_imports))
    code.append('')  # Empty line after imports
    
    # Add classes first (since functions might depend on them)
    for node in nodes:
        node_data = graph.nodes[node].get('data', {})
        if graph.nodes[node].get('type') == 'class':
            code.append(node_data['code'])
            code.append('')  # Empty line after class
    
    # Add standalone functions
    for node in nodes:
        node_data = graph.nodes[node].get('data', {})
        if graph.nodes[node].get('type') == 'function' and not node_data.get('is_method', False):
            code.append(node_data['code'])
            code.append('')  # Empty line after function
    
    return '\n'.join(code)

def create_init_file(modules: Dict[str, List[str]], analysis_result: Dict[str, Any], output_dir: str) -> str:
    """
    Create an __init__.py file that re-exports all the public symbols.
    
    Args:
        modules: Dictionary mapping module names to lists of node IDs
        analysis_result: Result from analyze_codebase
        output_dir: Output directory
        
    Returns:
        Generated code for __init__.py
    """
    graph = analysis_result['dependency_graph']
    
    # Collect all public classes and functions
    public_symbols = []
    module_imports = []
    
    for module_name, nodes in modules.items():
        module_symbols = []
        
        for node in nodes:
            node_data = graph.nodes[node].get('data', {})
            if node_data and 'name' in node_data:
                name = node_data['name']
                if not name.startswith('_'):  # Only include public symbols
                    module_symbols.append(name)
        
        if module_symbols:
            symbols_str = ', '.join(module_symbols)
            module_imports.append(f"from .{module_name} import {symbols_str}")
            public_symbols.extend(module_symbols)
    
    # Create the __init__.py content
    init_content = ['"""', 'Analyzers Package', '', 'This package contains modules for analyzing code.', '"""', '']
    init_content.extend(module_imports)
    init_content.append('')
    init_content.append(f"__all__ = {sorted(public_symbols)}")
    init_content.append('')
    
    return '\n'.join(init_content)

def visualize_dependency_graph(graph: nx.DiGraph, output_file: str = 'dependency_graph.png'):
    """
    Visualize the dependency graph.
    
    Args:
        graph: NetworkX DiGraph object
        output_file: Path to save the visualization
    """
    plt.figure(figsize=(12, 10))
    
    # Use different colors for different node types
    node_colors = []
    for node in graph.nodes():
        if graph.nodes[node].get('type') == 'class':
            node_colors.append('lightblue')
        else:
            node_colors.append('lightgreen')
    
    # Use different edge colors for different relationship types
    edge_colors = []
    for u, v in graph.edges():
        edge_type = graph.edges[u, v].get('type')
        if edge_type == 'calls':
            edge_colors.append('red')
        elif edge_type == 'uses':
            edge_colors.append('blue')
        elif edge_type == 'member_of':
            edge_colors.append('green')
        else:
            edge_colors.append('gray')
    
    # Draw the graph
    pos = nx.spring_layout(graph, seed=42)
    nx.draw_networkx_nodes(graph, pos, node_color=node_colors, alpha=0.8)
    nx.draw_networkx_edges(graph, pos, edge_color=edge_colors, alpha=0.5, arrows=True)
    
    # Add labels
    labels = {}
    for node in graph.nodes():
        file, name = node.split(':', 1)
        labels[node] = name
    
    nx.draw_networkx_labels(graph, pos, labels=labels, font_size=8)
    
    plt.title('Function and Class Dependencies')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    print(f"Dependency graph visualization saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Refactor analyzer functions into separate modules')
    parser.add_argument('--dry-run', action='store_true', help='Only analyze and print what would be done')
    parser.add_argument('--output-dir', default=DEFAULT_OUTPUT_DIR, help='Directory to output the refactored modules')
    args = parser.parse_args()
    
    # Analyze the codebase
    print(f"Analyzing codebase in {ANALYZERS_DIR}...")
    analysis_result = analyze_codebase(ANALYZERS_DIR)
    
    print(f"Found {len(analysis_result['all_functions'])} functions and {len(analysis_result['all_classes'])} classes")
    
    # Identify new modules
    print("Identifying modules based on function relationships...")
    modules = identify_modules(analysis_result)
    
    print(f"Identified {len(modules)} modules:")
    for module_name, nodes in modules.items():
        print(f"  - {module_name}: {len(nodes)} functions/classes")
    
    # Visualize the dependency graph
    print("Generating dependency graph visualization...")
    visualize_dependency_graph(analysis_result['dependency_graph'])
    
    if args.dry_run:
        print("Dry run completed. No files were modified.")
        return
    
    # Create output directory
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate and write module files
    print(f"Generating module files in {output_dir}...")
    for module_name, nodes in modules.items():
        module_code = generate_module_code(module_name, nodes, analysis_result)
        module_file = os.path.join(output_dir, f"{module_name}.py")
        
        with open(module_file, 'w', encoding='utf-8') as f:
            f.write(module_code)
        
        print(f"  - Created {module_file}")
    
    # Create __init__.py
    init_code = create_init_file(modules, analysis_result, output_dir)
    init_file = os.path.join(output_dir, "__init__.py")
    
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write(init_code)
    
    print(f"  - Created {init_file}")
    
    print("Refactoring completed successfully!")

if __name__ == "__main__":
    main()

