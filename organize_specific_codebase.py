#!/usr/bin/env python3
"""
Organize Specific Codebase Structure

This script is specifically designed to organize the codebase structure shown in the screenshot:
- 5 folders: context, models, resolution, snapshot, visualization
- 21 .py files in the root directory

It will:
1. Create the directory structure
2. Move files to appropriate directories
3. Split functions between files to reduce duplication
4. Update imports automatically

Usage:
    python organize_specific_codebase.py /path/to/analyzers/directory [--execute]

Example:
    python organize_specific_codebase.py ./analyzers --execute
"""

import os
import sys
import shutil
import re
import ast
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

class SpecificCodebaseOrganizer:
    def __init__(self, base_dir: str, dry_run: bool = True):
        """
        Initialize the SpecificCodebaseOrganizer.
        
        Args:
            base_dir: Path to the analyzers directory
            dry_run: If True, only print planned changes without executing them
        """
        self.base_dir = os.path.abspath(base_dir)
        self.dry_run = dry_run
        
        # Define the target directory structure
        self.dirs = {
            'context': os.path.join(self.base_dir, 'context'),
            'models': os.path.join(self.base_dir, 'models'),
            'resolution': os.path.join(self.base_dir, 'resolution'),
            'snapshot': os.path.join(self.base_dir, 'snapshot'),
            'visualization': os.path.join(self.base_dir, 'visualization'),
        }
        
        # Define file mapping based on the screenshot
        self.file_mapping = {
            # Files to keep in root
            'root': [
                '__init__.py',
                'analyzer.py',
                'analyzer_manager.py',
                'api.py',
                'base_analyzer.py',
                'code_quality.py',
                'code_quality_analyzer.py',
                'dependencies.py',
                'dependency_analyzer.py',
                'error_analyzer.py',
                'issue_analyzer.py',
                'issue_types.py',
                'issues.py',
                'README.md',
                'unified_analyzer.py'
            ],
            
            # Files to move to context directory
            'context': [
                'codebase_context.py',
                'context_codebase.py'
            ],
            
            # Files to move to models directory
            'models': [],
            
            # Files to move to resolution directory
            'resolution': [],
            
            # Files to move to snapshot directory
            'snapshot': [],
            
            # Files to move to visualization directory
            'visualization': [
                'codebase_visualizer.py'
            ]
        }
        
        # Define function mapping for splitting functions between files
        self.function_mapping = {
            # Map function patterns to destination files
            'analyzer.py': [
                'analyze', 'run_analysis', 'execute_analysis', 'perform_analysis'
            ],
            'analyzer_manager.py': [
                'manage', 'coordinate', 'orchestrate', 'configure'
            ],
            'base_analyzer.py': [
                'BaseAnalyzer', 'base_analyze', 'AbstractAnalyzer'
            ],
            'code_quality.py': [
                'quality', 'lint', 'style', 'format'
            ],
            'code_quality_analyzer.py': [
                'analyze_quality', 'check_quality', 'quality_check'
            ],
            'codebase_analyzer.py': [
                'analyze_codebase', 'codebase_analysis'
            ],
            'dependency_analyzer.py': [
                'analyze_dependencies', 'check_dependencies', 'dependency_check'
            ],
            'error_analyzer.py': [
                'analyze_errors', 'check_errors', 'error_check'
            ],
            'issue_analyzer.py': [
                'analyze_issues', 'check_issues', 'issue_check'
            ],
            'context/context.py': [
                'context', 'get_context', 'create_context', 'update_context'
            ],
            'visualization/visualizer.py': [
                'visualize', 'plot', 'graph', 'chart'
            ]
        }
        
        # Store functions found in the codebase
        self.functions: Dict[str, Tuple[str, str]] = {}  # Maps function name to (file_path, code) tuple
        self.duplicate_functions: defaultdict[str, List[str]] = defaultdict(list)  # Maps function signature to list of file paths

    def create_directory_structure(self):
        """Create the directory structure if it doesn't exist."""
        print(f"Creating directory structure in {self.base_dir}")
        
        for dir_name, dir_path in self.dirs.items():
            if not os.path.exists(dir_path):
                if not self.dry_run:
                    os.makedirs(dir_path)
                    # Create __init__.py in each directory
                    with open(os.path.join(dir_path, '__init__.py'), 'w') as f:
                        f.write(f"# {dir_name.capitalize()} module\n")
                print(f"Created directory: {dir_path}")

    def analyze_codebase(self):
        """Analyze the codebase to identify files and functions."""
        print("Analyzing codebase...")
        
        # Get all Python files in the base directory
        py_files = [f for f in os.listdir(self.base_dir) if f.endswith('.py')]
        
        print(f"Found {len(py_files)} Python files in {self.base_dir}")
        
        # Analyze each file to extract functions
        for filename in py_files:
            file_path = os.path.join(self.base_dir, filename)
            self._analyze_file(file_path)
        
        # Identify duplicate functions
        duplicates = {sig: files for sig, files in self.duplicate_functions.items() if len(files) > 1}
        if duplicates:
            print(f"Found {len(duplicates)} duplicate function signatures:")
            for sig, files in duplicates.items():
                print(f"  - {sig} in files: {', '.join(os.path.basename(f) for f in files)}")

    def _analyze_file(self, file_path: str):
        """
        Analyze a single Python file to extract functions.
        
        Args:
            file_path: Path to the Python file
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    function_name = node.name
                    
                    # Skip private methods
                    if function_name.startswith('_') and not function_name.startswith('__'):
                        continue
                    
                    # Get function code
                    function_code = ast.get_source_segment(content, node)
                    
                    # Store function
                    self.functions[function_name] = (file_path, function_code)
                    
                    # Create function signature for duplicate detection
                    func_sig = self._get_function_signature(node)
                    self.duplicate_functions[func_sig].append(file_path)
        
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

    def organize_files(self):
        """Organize files according to the file mapping."""
        print("Organizing files...")
        
        # Create directory structure
        self.create_directory_structure()
        
        # Get all files in the base directory
        all_files = os.listdir(self.base_dir)
        
        # Process each file according to the mapping
        for category, files in self.file_mapping.items():
            if category == 'root':
                continue  # Skip files that should stay in root
                
            dest_dir = self.dirs[category]
            
            for filename in files:
                if filename in all_files:
                    source_path = os.path.join(self.base_dir, filename)
                    dest_path = os.path.join(dest_dir, filename)
                    
                    print(f"Moving {filename} to {category}/")
                    
                    if not self.dry_run:
                        shutil.move(source_path, dest_path)
                        
                        # Update imports in the moved file
                        self._update_imports(dest_path, filename)

    def _update_imports(self, file_path: str, filename: str):
        """
        Update imports in a moved file.
        
        Args:
            file_path: Path to the moved file
            filename: Original filename
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Update relative imports
            updated_content = content
            
            # Add import for the module
            module_name = os.path.basename(os.path.dirname(file_path))
            if not re.search(rf"from {module_name} import", content):
                # Add import at the top of the file after existing imports
                import_lines = re.findall(r"^(from .+? import .+|import .+)$", content, re.MULTILINE)
                if import_lines:
                    last_import = import_lines[-1]
                    updated_content = content.replace(last_import, f"{last_import}\n\n# Added by organizer\nfrom {module_name} import *")
                else:
                    # Add after docstring or at the top
                    if '"""' in content:
                        docstring_end = content.find('"""', content.find('"""') + 3) + 3
                        updated_content = content[:docstring_end] + f"\n\n# Added by organizer\nfrom {module_name} import *\n" + content[docstring_end:]
                    else:
                        updated_content = f"# Added by organizer\nfrom {module_name} import *\n\n" + content
            
            with open(file_path, 'w') as f:
                f.write(updated_content)
        
        except Exception as e:
            print(f"Error updating imports in {file_path}: {str(e)}")

    def split_functions(self):
        """Split functions between files according to the function mapping."""
        print("Splitting functions between files...")
        
        # Group functions by destination file
        function_groups = defaultdict(list)
        
        for function_name, (source_path, function_code) in self.functions.items():
            # Find the appropriate destination file
            dest_file = None
            
            for file_path, patterns in self.function_mapping.items():
                if any(pattern in function_name.lower() for pattern in patterns):
                    dest_file = file_path
                    break
            
            # If no match found, keep in the original file
            if not dest_file:
                dest_file = os.path.basename(source_path)
            
            # Convert relative path to absolute
            if '/' in dest_file:
                dest_file = os.path.join(self.base_dir, dest_file)
            else:
                dest_file = os.path.join(self.base_dir, dest_file)
            
            # Add to function groups
            function_groups[dest_file].append((function_name, source_path, function_code))
        
        # Process each destination file
        for dest_file, functions in function_groups.items():
            print(f"Adding {len(functions)} functions to {os.path.basename(dest_file)}")
            
            if self.dry_run:
                for function_name, source_path, _ in functions:
                    if source_path != dest_file:
                        print(f"  - Would move {function_name} from {os.path.basename(source_path)}")
                continue
            
            # Create destination file if it doesn't exist
            if not os.path.exists(dest_file):
                dir_path = os.path.dirname(dest_file)
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)
                
                # Create the file with a basic header
                with open(dest_file, 'w') as f:
                    f.write(f"#!/usr/bin/env python3\n")
                    f.write(f'"""\n')
                    f.write(f"{os.path.basename(dest_file)}\n\n")
                    f.write(f"This file contains functions related to {os.path.basename(dest_file).replace('.py', '')}.\n")
                    f.write(f'"""\n\n')
            
            # Read existing content
            with open(dest_file, 'r') as f:
                content = f.read()
            
            # Add functions that aren't already in the file
            for function_name, source_path, function_code in functions:
                if source_path == dest_file:
                    continue  # Skip if function is already in the right file
                
                if function_name in content:
                    continue  # Skip if function already exists in the destination
                
                # Add function to the end of the file
                with open(dest_file, 'a') as f:
                    f.write(f"\n\n{function_code}")
                
                print(f"  - Moved {function_name} from {os.path.basename(source_path)}")

    def run(self):
        """Run the codebase organization process."""
        print(f"{'DRY RUN: ' if self.dry_run else ''}Organizing specific codebase in {self.base_dir}")
        
        self.analyze_codebase()
        self.organize_files()
        self.split_functions()
        
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
    
    organizer = SpecificCodebaseOrganizer(base_dir, dry_run)
    organizer.run()

if __name__ == "__main__":
    main()
