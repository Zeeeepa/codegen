#!/usr/bin/env python3
"""
Organize Codebase with Codegen SDK

This script uses the Codegen SDK to organize a codebase by:
1. Moving functions between files
2. Creating a proper directory structure
3. Updating imports automatically
4. Eliminating code duplication

Usage:
    python organize_with_codegen_sdk.py /path/to/analyzers/directory

Example:
    python organize_with_codegen_sdk.py ./analyzers
"""

import os
import sys
import re
import ast
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

try:
    from codegen.sdk import Codebase
    from codegen.sdk.codebase import Symbol, File
except ImportError:
    print("Error: Codegen SDK not found. Please install it with:")
    print("pip install codegen-sdk")
    sys.exit(1)

class CodegenOrganizer:
    def __init__(self, base_dir: str, dry_run: bool = True):
        """
        Initialize the CodegenOrganizer.
        
        Args:
            base_dir: Path to the analyzers directory
            dry_run: If True, only print planned changes without executing them
        """
        self.base_dir = os.path.abspath(base_dir)
        self.dry_run = dry_run
        
        # Initialize Codegen SDK
        self.codebase = Codebase(self.base_dir)
        
        # Create directory structure if it doesn't exist
        self.dirs = {
            'context': os.path.join(self.base_dir, 'context'),
            'models': os.path.join(self.base_dir, 'models'),
            'resolution': os.path.join(self.base_dir, 'resolution'),
            'snapshot': os.path.join(self.base_dir, 'snapshot'),
            'visualization': os.path.join(self.base_dir, 'visualization'),
        }
        
        # Define file mapping for functions
        self.file_mapping = {
            'context': {
                'context/context.py': ['context', 'get_context', 'create_context', 'update_context'],
                'context/context_manager.py': ['manage_context', 'load_context', 'save_context'],
                'context_codebase.py': ['codebase_context']
            },
            'models': {
                'models/model.py': ['model', 'create_model', 'train_model', 'evaluate_model'],
                'models/model_manager.py': ['manage_model', 'load_model', 'save_model']
            },
            'resolution': {
                'resolution/resolver.py': ['resolve', 'fix', 'repair'],
                'resolution/resolution_manager.py': ['manage_resolution', 'track_resolution', 'apply_resolution']
            },
            'snapshot': {
                'snapshot/snapshot.py': ['snapshot', 'create_snapshot', 'compare_snapshot'],
                'snapshot/snapshot_manager.py': ['manage_snapshot', 'load_snapshot', 'save_snapshot']
            },
            'visualization': {
                'visualization/visualizer.py': ['visualize', 'plot', 'graph', 'chart'],
                'visualization/visualization_manager.py': ['manage_visualization', 'generate_visualization', 'export_visualization'],
                'codebase_visualizer.py': ['visualize_codebase']
            },
            'analyzer': {
                'analyzer.py': ['analyze', 'run_analysis', 'execute_analysis'],
                'analyzer_manager.py': ['manage_analyzer', 'coordinate_analyzer', 'orchestrate_analyzer'],
                'base_analyzer.py': ['BaseAnalyzer', 'base_analyze'],
                'code_quality.py': ['quality', 'lint', 'style'],
                'code_quality_analyzer.py': ['analyze_quality', 'check_quality'],
                'codebase_analyzer.py': ['analyze_codebase'],
                'dependency_analyzer.py': ['analyze_dependencies', 'check_dependencies'],
                'error_analyzer.py': ['analyze_errors', 'check_errors'],
                'issue_analyzer.py': ['analyze_issues', 'check_issues']
            },
            'api': {
                'api.py': ['api', 'endpoint', 'route', 'request', 'response']
            },
            'utils': {
                'dependencies.py': ['dependency', 'dependencies'],
                'issue_types.py': ['issue_type', 'issue_types'],
                'issues.py': ['issue', 'issues']
            }
        }

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
        """Analyze the codebase using Codegen SDK."""
        print("Analyzing codebase...")
        
        # Get all Python files in the base directory
        py_files = [f for f in os.listdir(self.base_dir) if f.endswith('.py') and not f.startswith('__')]
        
        # Collect all functions and their source files
        self.functions = {}  # Maps function name to (file, symbol) tuple
        self.duplicate_functions = defaultdict(list)  # Maps function name to list of files
        
        for filename in py_files:
            file_path = os.path.join(self.base_dir, filename)
            file = self.codebase.get_file(file_path)
            
            if not file:
                print(f"Warning: Could not load file {file_path}")
                continue
            
            # Get all functions in the file
            for symbol in file.get_symbols():
                if symbol.kind == 'function':
                    function_name = symbol.name
                    
                    # Skip private methods
                    if function_name.startswith('_') and not function_name.startswith('__'):
                        continue
                    
                    # Store function
                    self.functions[function_name] = (file, symbol)
                    
                    # Check for duplicates
                    self.duplicate_functions[function_name].append(file_path)
        
        # Print summary
        print(f"Found {len(self.functions)} functions in {len(py_files)} files")
        
        # Identify duplicates
        duplicates = {name: files for name, files in self.duplicate_functions.items() if len(files) > 1}
        if duplicates:
            print(f"Found {len(duplicates)} duplicate functions:")
            for name, files in duplicates.items():
                print(f"  - {name} in files: {', '.join(os.path.basename(f) for f in files)}")

    def categorize_functions(self):
        """
        Categorize functions into appropriate files based on naming patterns.
        
        Returns:
            A dictionary mapping destination file paths to lists of (source_file, symbol) tuples
        """
        print("Categorizing functions...")
        
        categorized = defaultdict(list)
        
        for function_name, (file, symbol) in self.functions.items():
            assigned = False
            
            # Try to assign to specific files based on function name patterns
            for category, file_patterns in self.file_mapping.items():
                for file_path, patterns in file_patterns.items():
                    if any(pattern in function_name.lower() for pattern in patterns):
                        dest_path = os.path.join(self.base_dir, file_path)
                        categorized[dest_path].append((file, symbol))
                        assigned = True
                        break
                
                if assigned:
                    break
            
            # If not assigned, put in a default file based on the first word of the function name
            if not assigned:
                first_word = function_name.split('_')[0].lower()
                
                # Try to find a matching category
                matched_category = None
                for category in self.file_mapping.keys():
                    if first_word in category.lower() or category.lower() in first_word:
                        matched_category = category
                        break
                
                if matched_category:
                    # Use the first file in that category
                    first_file = list(self.file_mapping[matched_category].keys())[0]
                    dest_path = os.path.join(self.base_dir, first_file)
                else:
                    # Default to utils.py
                    dest_path = os.path.join(self.base_dir, 'utils.py')
                
                categorized[dest_path].append((file, symbol))
        
        # Print categorization summary
        print("Function categorization summary:")
        for dest_file, symbols in categorized.items():
            print(f"  - {os.path.basename(dest_file)}: {len(symbols)} functions")
        
        return categorized

    def move_functions(self, categorized_functions):
        """
        Move functions to their new files using Codegen SDK.
        
        Args:
            categorized_functions: Dictionary mapping destination file paths to lists of (source_file, symbol) tuples
        """
        print("Moving functions...")
        
        # Create necessary directories and files
        self.create_directory_structure()
        
        # Create destination files if they don't exist
        for dest_path in categorized_functions.keys():
            if not os.path.exists(dest_path) and not self.dry_run:
                dir_path = os.path.dirname(dest_path)
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)
                
                # Create the file with a basic header
                with open(dest_path, 'w') as f:
                    f.write(f"#!/usr/bin/env python3\n")
                    f.write(f'"""\n')
                    f.write(f"{os.path.basename(dest_path)}\n\n")
                    f.write(f"This file contains functions related to {os.path.basename(dest_path).replace('.py', '')}.\n")
                    f.write(f'"""\n\n')
        
        # Move functions to their new files
        for dest_path, symbols in categorized_functions.items():
            print(f"Moving {len(symbols)} functions to {dest_path}")
            
            if self.dry_run:
                for source_file, symbol in symbols:
                    print(f"  - Would move {symbol.name} from {source_file.path}")
                continue
            
            # Get or create the destination file
            dest_file = self.codebase.get_file(dest_path)
            if not dest_file:
                print(f"Creating file: {dest_path}")
                dest_file = self.codebase.create_file(dest_path)
            
            # Move each function to the destination file
            for source_file, symbol in symbols:
                try:
                    print(f"  - Moving {symbol.name} from {source_file.path}")
                    
                    # Move the symbol to the destination file
                    symbol.move_to_file(
                        dest_file,
                        include_dependencies=True,
                        strategy="update_all_imports"
                    )
                    
                    # Commit after each move to avoid conflicts
                    self.codebase.commit()
                    
                except Exception as e:
                    print(f"    Error moving {symbol.name}: {str(e)}")
        
        print("Done moving functions!")

    def run(self):
        """Run the codebase organization process."""
        print(f"{'DRY RUN: ' if self.dry_run else ''}Organizing codebase with Codegen SDK in {self.base_dir}")
        
        self.analyze_codebase()
        categorized = self.categorize_functions()
        self.move_functions(categorized)
        
        # Commit all changes
        if not self.dry_run:
            self.codebase.commit()
        
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
    
    organizer = CodegenOrganizer(base_dir, dry_run)
    organizer.run()

if __name__ == "__main__":
    main()

