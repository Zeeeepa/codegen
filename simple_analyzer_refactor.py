#!/usr/bin/env python3
"""
Simple Analyzer Refactoring Script

This script analyzes Python files in the analyzers directory and separates functions
into different modules based on their names and functionality.

Usage:
    python simple_analyzer_refactor.py [--dry-run] [--output-dir OUTPUT_DIR]

Options:
    --dry-run       Only analyze and print what would be done, without making changes
    --output-dir    Directory to output the refactored modules (default: ./refactored_analyzers)
"""

import os
import sys
import ast
import re
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional, Union
from collections import defaultdict

# Configuration
ANALYZERS_DIR = "codegen-on-oss/codegen_on_oss/analyzers"
DEFAULT_OUTPUT_DIR = "refactored_analyzers"
IGNORED_FILES = {"__init__.py", "__pycache__"}
IGNORED_DIRS = {"__pycache__"}

class FunctionExtractor(ast.NodeVisitor):
    """AST visitor to extract functions and classes from Python files."""
    
    def __init__(self):
        self.functions = []
        self.classes = []
        self.imports = []
        self.file_docstring = None
    
    def visit_Module(self, node):
        # Extract module docstring if present
        if (len(node.body) > 0 and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant)):
            self.file_docstring = node.body[0].value.value
        elif (len(node.body) > 0 and 
              isinstance(node.body[0], ast.Expr) and 
              hasattr(node.body[0].value, 's')):  # For Python < 3.8
            self.file_docstring = node.body[0].value.s
            
        self.generic_visit(node)
    
    def visit_Import(self, node):
        self.imports.append(ast.unparse(node))
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        self.imports.append(ast.unparse(node))
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        # Skip if this is a method (parent is a class)
        if not any(isinstance(parent, ast.ClassDef) for parent in self.get_parents(node)):
            func_info = {
                'name': node.name,
                'code': ast.unparse(node),
                'docstring': ast.get_docstring(node),
                'lineno': node.lineno,
                'end_lineno': getattr(node, 'end_lineno', None),  # For Python < 3.8 compatibility
                'is_method': False,
                'category': self.categorize_function(node)
            }
            self.functions.append(func_info)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = {
                    'name': item.name,
                    'code': ast.unparse(item),
                    'docstring': ast.get_docstring(item),
                    'lineno': item.lineno,
                    'end_lineno': getattr(item, 'end_lineno', None),
                    'is_method': True,
                    'category': self.categorize_function(item)
                }
                methods.append(method_info)
        
        class_info = {
            'name': node.name,
            'code': ast.unparse(node),
            'docstring': ast.get_docstring(node),
            'methods': methods,
            'lineno': node.lineno,
            'end_lineno': getattr(node, 'end_lineno', None),
            'category': self.categorize_class(node)
        }
        self.classes.append(class_info)
        
        # Don't visit children, we've already processed the methods
        # self.generic_visit(node)
    
    def get_parents(self, node):
        """Get parent nodes for a given node (not used in this implementation)."""
        # This is a placeholder - in a real implementation, we would track parent nodes
        return []
    
    def categorize_function(self, node):
        """Categorize a function based on its name and content."""
        name = node.name.lower()
        
        # Extract category from function name
        if name.startswith('analyze_') or name.startswith('_analyze_'):
            return name.split('_')[1]
        elif name.startswith('get_') or name.startswith('_get_'):
            return name.split('_')[1]
        elif name.startswith('find_') or name.startswith('_find_'):
            return name.split('_')[1]
        elif name.startswith('extract_') or name.startswith('_extract_'):
            return name.split('_')[1]
        elif name.startswith('process_') or name.startswith('_process_'):
            return name.split('_')[1]
        elif 'dependency' in name or 'dependencies' in name:
            return 'dependency'
        elif 'quality' in name:
            return 'quality'
        elif 'issue' in name:
            return 'issue'
        elif 'error' in name:
            return 'error'
        elif 'visualize' in name or 'visualization' in name:
            return 'visualization'
        elif 'context' in name:
            return 'context'
        else:
            return 'general'
    
    def categorize_class(self, node):
        """Categorize a class based on its name and content."""
        name = node.name.lower()
        
        if 'analyzer' in name:
            if 'quality' in name:
                return 'quality_analyzer'
            elif 'dependency' in name:
                return 'dependency_analyzer'
            elif 'error' in name:
                return 'error_analyzer'
            elif 'issue' in name:
                return 'issue_analyzer'
            elif 'codebase' in name:
                return 'codebase_analyzer'
            else:
                return 'analyzer'
        elif 'manager' in name:
            return 'manager'
        elif 'visualizer' in name:
            return 'visualizer'
        elif 'context' in name:
            return 'context'
        else:
            return 'general'

def extract_file_info(file_path):
    """Extract information from a Python file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
        extractor = FunctionExtractor()
        extractor.visit(tree)
        
        return {
            'imports': extractor.imports,
            'functions': extractor.functions,
            'classes': extractor.classes,
            'file_docstring': extractor.file_docstring,
            'content': content
        }
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return {
            'imports': [],
            'functions': [],
            'classes': [],
            'file_docstring': None,
            'content': content
        }

def analyze_codebase(analyzers_dir):
    """Analyze all Python files in the analyzers directory."""
    result = {
        'files': {},
        'functions_by_category': defaultdict(list),
        'classes_by_category': defaultdict(list)
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
                
                # Extract information from the file
                file_info = extract_file_info(file_path)
                result['files'][rel_path] = file_info
                
                # Group functions by category
                for func in file_info['functions']:
                    func['file'] = rel_path
                    result['functions_by_category'][func['category']].append(func)
                
                # Group classes by category
                for cls in file_info['classes']:
                    cls['file'] = rel_path
                    result['classes_by_category'][cls['category']].append(cls)
                    
                    # Add methods to their categories
                    for method in cls['methods']:
                        method['file'] = rel_path
                        method['class'] = cls['name']
                        result['functions_by_category'][method['category']].append(method)
    
    return result

def generate_module_code(module_name, functions, classes, analysis_result):
    """Generate code for a new module."""
    # Collect all imports from original files
    all_imports = set()
    file_docstrings = {}
    
    # Get files that contain these functions and classes
    files = set()
    for func in functions:
        files.add(func['file'])
    for cls in classes:
        files.add(cls['file'])
    
    # Collect imports and docstrings
    for file in files:
        if file in analysis_result['files']:
            file_data = analysis_result['files'][file]
            all_imports.update(file_data['imports'])
            if file_data['file_docstring'] and file not in file_docstrings:
                file_docstrings[file] = file_data['file_docstring']
    
    # Create module docstring
    docstring = f'"""\n{module_name.replace("_", " ").title()} Module\n\n'
    docstring += f'This module contains functions and classes related to {module_name.replace("_", " ")}.\n'
    
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
    for cls in classes:
        code.append(cls['code'])
        code.append('')  # Empty line after class
    
    # Add standalone functions
    for func in functions:
        if not func.get('is_method', False):
            code.append(func['code'])
            code.append('')  # Empty line after function
    
    return '\n'.join(code)

def create_init_file(modules, analysis_result, output_dir):
    """Create an __init__.py file that re-exports all the public symbols."""
    # Collect all public classes and functions
    public_symbols = []
    module_imports = []
    
    for module_name, module_info in modules.items():
        module_symbols = []
        
        # Add class names
        for cls in module_info['classes']:
            name = cls['name']
            if not name.startswith('_'):  # Only include public symbols
                module_symbols.append(name)
        
        # Add function names
        for func in module_info['functions']:
            if not func.get('is_method', False):  # Skip methods
                name = func['name']
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

def main():
    parser = argparse.ArgumentParser(description='Refactor analyzer functions into separate modules')
    parser.add_argument('--dry-run', action='store_true', help='Only analyze and print what would be done')
    parser.add_argument('--output-dir', default=DEFAULT_OUTPUT_DIR, help='Directory to output the refactored modules')
    args = parser.parse_args()
    
    # Analyze the codebase
    print(f"Analyzing codebase in {ANALYZERS_DIR}...")
    analysis_result = analyze_codebase(ANALYZERS_DIR)
    
    # Group functions and classes into modules
    modules = {}
    
    # Create modules based on function categories
    for category, functions in analysis_result['functions_by_category'].items():
        if category not in modules:
            modules[category] = {'functions': [], 'classes': []}
        modules[category]['functions'].extend(functions)
    
    # Add classes to appropriate modules
    for category, classes in analysis_result['classes_by_category'].items():
        if category not in modules:
            modules[category] = {'functions': [], 'classes': []}
        modules[category]['classes'].extend(classes)
    
    # Print summary
    print(f"Identified {len(modules)} modules:")
    for module_name, module_info in modules.items():
        print(f"  - {module_name}: {len(module_info['functions'])} functions, {len(module_info['classes'])} classes")
    
    if args.dry_run:
        print("Dry run completed. No files were modified.")
        return
    
    # Create output directory
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate and write module files
    print(f"Generating module files in {output_dir}...")
    for module_name, module_info in modules.items():
        module_code = generate_module_code(
            module_name, 
            module_info['functions'], 
            module_info['classes'], 
            analysis_result
        )
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

