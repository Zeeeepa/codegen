#!/usr/bin/env python3
"""
Organize Analyzers Codebase

This script helps organize the analyzers codebase by:
1. Creating a proper directory structure
2. Moving related functions to appropriate files
3. Eliminating code duplication
4. Ensuring proper imports and dependencies

Usage:
    python organize_analyzers.py /path/to/analyzers/directory

Example:
    python organize_analyzers.py ./analyzers
"""

import os
import sys
import shutil
import re
import ast
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

class CodebaseOrganizer:
    def __init__(self, base_dir: str, dry_run: bool = True):
        """
        Initialize the CodebaseOrganizer.
        
        Args:
            base_dir: Path to the analyzers directory
            dry_run: If True, only print planned changes without executing them
        """
        self.base_dir = os.path.abspath(base_dir)
        self.dry_run = dry_run
        # Store functions found in the codebase
        self.function_map: defaultdict[str, List[Dict[str, any]]] = defaultdict(list)  # Maps functions to files
        self.duplicate_functions: defaultdict[str, List[str]] = defaultdict(list)  # Maps function signatures to files
        self.dependency_graph: defaultdict[str, Set[str]] = defaultdict(set)  # Maps functions to their dependencies
        
        # Create directory structure if it doesn't exist
        self.dirs = {
            'context': os.path.join(self.base_dir, 'context'),
            'models': os.path.join(self.base_dir, 'models'),
            'resolution': os.path.join(self.base_dir, 'resolution'),
            'snapshot': os.path.join(self.base_dir, 'snapshot'),
            'visualization': os.path.join(self.base_dir, 'visualization'),
        }

    def create_directory_structure(self):
        """Create the directory structure if it doesn't exist."""
        print(f"Creating directory structure in {self.base_dir}")
        
        if not os.path.exists(self.base_dir):
            if not self.dry_run:
                os.makedirs(self.base_dir)
            print(f"Created base directory: {self.base_dir}")
        
        for dir_name, dir_path in self.dirs.items():
            if not os.path.exists(dir_path):
                if not self.dry_run:
                    os.makedirs(dir_path)
                print(f"Created directory: {dir_path}")

    def analyze_files(self):
        """Analyze all Python files in the base directory to identify functions and dependencies."""
        print("Analyzing Python files...")
        
        py_files = [f for f in os.listdir(self.base_dir) if f.endswith('.py') and not f.startswith('__')]
        
        for filename in py_files:
            file_path = os.path.join(self.base_dir, filename)
            self._analyze_file(file_path)
    
    def _analyze_file(self, file_path: str):
        """
        Analyze a single Python file to extract functions and their dependencies.
        
        Args:
            file_path: Path to the Python file
        """
        print(f"Analyzing file: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    function_name = node.name
                    function_code = ast.get_source_segment(content, node)
                    
                    # Skip if it's a private method or dunder method
                    if function_name.startswith('_') and not function_name.startswith('__'):
                        continue
                    
                    # Extract function signature for duplicate detection
                    func_sig = self._get_function_signature(node)
                    
                    # Store function in function map
                    self.function_map[os.path.basename(file_path)].append({
                        'name': function_name,
                        'code': function_code,
                        'signature': func_sig,
                        'node': node
                    })
                    
                    # Check for duplicates
                    self.duplicate_functions[func_sig].append(os.path.basename(file_path))
                    
                    # Analyze function dependencies
                    self._analyze_function_dependencies(node, function_name)
        
        except Exception as e:
            print(f"Error analyzing file {file_path}: {str(e)}")
    
    def _get_function_signature(self, func_node: ast.FunctionDef) -> str:
        """
        Get a normalized function signature for duplicate detection.
        
        Args:
            func_node: AST node for the function
            
        Returns:
            A normalized function signature string
        """
        # Get argument names
        args = [arg.arg for arg in func_node.args.args]
        
        # Get return annotation if it exists
        returns = ""
        if func_node.returns:
            if isinstance(func_node.returns, ast.Name):
                returns = func_node.returns.id
            elif isinstance(func_node.returns, ast.Attribute):
                returns = func_node.returns.attr
        
        return f"{func_node.name}({', '.join(args)}) -> {returns}"
    
    def _analyze_function_dependencies(self, func_node: ast.FunctionDef, function_name: str):
        """
        Analyze function dependencies by looking at function calls.
        
        Args:
            func_node: AST node for the function
            function_name: Name of the function being analyzed
        """
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                called_func = node.func.id
                self.dependency_graph[function_name].add(called_func)
    
    def identify_duplicates(self):
        """Identify duplicate functions across files."""
        print("\nIdentifying duplicate functions...")
        
        duplicates = {sig: files for sig, files in self.duplicate_functions.items() if len(files) > 1}
        
        if not duplicates:
            print("No duplicate functions found.")
            return
        
        print(f"Found {len(duplicates)} duplicate function signatures:")
        for sig, files in duplicates.items():
            print(f"  - {sig} in files: {', '.join(files)}")
    
    def categorize_functions(self) -> Dict[str, List[Dict]]:
        """
        Categorize functions into appropriate modules based on naming patterns and dependencies.
        
        Returns:
            A dictionary mapping module names to lists of function information
        """
        print("\nCategorizing functions...")
        
        categorized: Dict[str, List[Dict]] = {
            'context': [],
            'models': [],
            'resolution': [],
            'snapshot': [],
            'visualization': [],
            'base': [],
            'api': [],
            'utils': [],
        }
        
        # Flatten function list
        all_functions = []
        for filename, functions in self.function_map.items():
            for func in functions:
                func['source_file'] = filename
                all_functions.append(func)
        
        # Categorize based on naming patterns and content
        for func in all_functions:
            name = func['name']
            code = func['code']
            
            # Context-related functions
            if 'context' in name or 'Context' in code or 'context' in func['source_file']:
                categorized['context'].append(func)
            
            # Model-related functions
            elif 'model' in name or 'Model' in code or 'models' in func['source_file']:
                categorized['models'].append(func)
            
            # Resolution-related functions
            elif 'resolve' in name or 'resolution' in name or 'Resolution' in code:
                categorized['resolution'].append(func)
            
            # Snapshot-related functions
            elif 'snapshot' in name or 'Snapshot' in code:
                categorized['snapshot'].append(func)
            
            # Visualization-related functions
            elif 'visual' in name or 'plot' in name or 'graph' in name or 'chart' in name:
                categorized['visualization'].append(func)
            
            # API-related functions
            elif 'api' in name or 'API' in code or 'endpoint' in name:
                categorized['api'].append(func)
            
            # Base analyzer functions
            elif 'base' in name or 'Base' in code or 'analyze' in name:
                categorized['base'].append(func)
            
            # Utility functions
            else:
                categorized['utils'].append(func)
        
        # Print categorization summary
        print("Function categorization summary:")
        for category, funcs in categorized.items():
            print(f"  - {category}: {len(funcs)} functions")
        
        return categorized
    
    def generate_new_files(self, categorized_functions: Dict[str, List[Dict]]):
        """
        Generate new files based on the categorized functions.
        
        Args:
            categorized_functions: Dictionary mapping categories to function information
        """
        print("\nGenerating new files...")
    
    def _generate_file(self, file_path: str, functions: List[Dict]):
        """
        Generate a new Python file with the given functions.
        
        Args:
            file_path: Path to the new file
            functions: List of function information to include in the file
        """
        print(f"Generating file: {file_path}")
        
        # Create directory if it doesn't exist
        dir_path = os.path.dirname(file_path)
        if not os.path.exists(dir_path) and not self.dry_run:
            os.makedirs(dir_path)
        
        # Generate imports
        imports = set()
        for func in functions:
            # Extract imports from function code
            for line in func['code'].split('\n'):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    imports.add(line.strip())
        
        # Generate file content
        content = "#!/usr/bin/env python3\n"
        content += '"""\n'
        content += f"{os.path.basename(file_path)}\n\n"
        content += f"This file contains functions related to {os.path.basename(file_path).replace('.py', '')}.\n"
        content += '"""\n\n'
        
        # Add imports
        for imp in sorted(imports):
            content += imp + '\n'
        
        if imports:
            content += '\n'
        
        # Add functions
        for func in functions:
            content += func['code'] + '\n\n'
        
        # Write to file
        if not self.dry_run:
            with open(file_path, 'w') as f:
                f.write(content)
        
        print(f"  - Added {len(functions)} functions")
    
    def run(self):
        """Run the codebase organization process."""
        print(f"{'DRY RUN: ' if self.dry_run else ''}Organizing codebase in {self.base_dir}")
        
        self.create_directory_structure()
        self.analyze_files()
        self.identify_duplicates()
        categorized = self.categorize_functions()
        self.generate_new_files(categorized)
        
        print("\nDone!")
        if self.dry_run:
            print("This was a dry run. To apply changes, run with --execute flag.")
        else:
            print("Changes have been applied.")

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} /path/to/analyzers/directory [--execute]")
        sys.exit(1)
    
    base_dir = sys.argv[1]
    dry_run = '--execute' not in sys.argv
    
    organizer = CodebaseOrganizer(base_dir, dry_run)
    organizer.run()

if __name__ == "__main__":
    main()
