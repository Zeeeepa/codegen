#!/usr/bin/env python3
"""
Organize Analyzers Module

This script reorganizes the analyzers module by creating dedicated subdirectories
for issues and dependencies, and moving relevant files to these directories.
It also updates imports in affected files to maintain functionality.
"""

import os
import re
import sys
from pathlib import Path

try:
    from codegen.sdk.core.codebase import Codebase
except ImportError:
    print("Codegen SDK not found. Please install it first.")
    sys.exit(1)


def create_directory(base_path, dir_name):
    """Create a directory if it doesn't exist."""
    dir_path = os.path.join(base_path, dir_name)
    os.makedirs(dir_path, exist_ok=True)
    
    # Create __init__.py if it doesn't exist
    init_file = os.path.join(dir_path, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            f.write(f'"""Analyzers {dir_name} module."""\n\n')
            
            # Add imports for common types if this is the issues directory
            if dir_name == "issues":
                f.write("from codegen_on_oss.analyzers.issues.issues import (\n")
                f.write("    Issue,\n")
                f.write("    IssueCollection,\n")
                f.write("    IssueCategory,\n")
                f.write("    IssueSeverity,\n")
                f.write("    IssueStatus,\n")
                f.write("    CodeLocation,\n")
                f.write("    create_issue,\n")
                f.write(")\n\n")
                f.write("from codegen_on_oss.analyzers.issues.issue_analyzer import IssueAnalyzer\n")
            
            # Add imports for common types if this is the dependencies directory
            if dir_name == "dependencies":
                f.write("from codegen_on_oss.analyzers.dependencies.dependencies import (\n")
                f.write("    DependencyAnalyzer,\n")
                f.write("    ImportDependency,\n")
                f.write("    ModuleDependency,\n")
                f.write("    CircularDependency,\n")
                f.write("    ModuleCoupling,\n")
                f.write("    ExternalDependency,\n")
                f.write(")\n")
    
    return dir_path


def update_imports_in_file(file_path, file_mappings):
    """
    Update imports in a file based on the provided mappings.
    
    Args:
        file_path: Path to the file to update
        file_mappings: Dictionary mapping old module paths to new module paths
    """
    if not os.path.exists(file_path):
        return
    
    with open(file_path, "r") as f:
        content = f.read()
    
    # Update imports
    for old_path, new_path in file_mappings.items():
        # Handle from ... import ... style imports
        pattern = f"from codegen_on_oss.analyzers.{old_path} import"
        replacement = f"from codegen_on_oss.analyzers.{new_path} import"
        content = content.replace(pattern, replacement)
        
        # Handle import ... style imports
        pattern = f"import codegen_on_oss.analyzers.{old_path}"
        replacement = f"import codegen_on_oss.analyzers.{new_path}"
        content = content.replace(pattern, replacement)
    
    with open(file_path, "w") as f:
        f.write(content)


def organize_analyzers(base_path=None):
    """
    Reorganize the analyzers module by creating dedicated subdirectories
    for issues and dependencies, and moving relevant files to these directories.
    
    Args:
        base_path: Base path of the analyzers module. If None, use the current directory.
    """
    # Determine base path
    if base_path is None:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    print(f"Organizing analyzers module at: {base_path}")
    
    # Initialize codebase
    codebase = Codebase(base_path)
    
    # Create directories
    issues_dir = create_directory(base_path, "issues")
    dependencies_dir = create_directory(base_path, "dependencies")
    
    # Define file mappings
    file_mappings = {
        # Issues files
        "issues": "issues/issues",
        "issue_types": "issues/issue_types",
        "issue_analyzer": "issues/issue_analyzer",
        
        # Dependencies files
        "dependencies": "dependencies/dependencies",
        "dependency_analyzer": "dependencies/dependency_analyzer",
    }
    
    # Group files by target directory
    files_by_dir = {
        "issues": ["issues.py", "issue_types.py", "issue_analyzer.py"],
        "dependencies": ["dependencies.py", "dependency_analyzer.py"],
    }
    
    # Process each directory
    for dir_name, files in files_by_dir.items():
        dir_path = os.path.join(base_path, dir_name)
        
        # Move files to the directory
        for filename in files:
            source_path = os.path.join(base_path, filename)
            if os.path.exists(source_path):
                print(f"Moving {filename} to {dir_name} directory")
                
                # Get source file
                source_file = codebase.get_file(filename)
                if not source_file:
                    print(f"Warning: Could not find {filename} in codebase")
                    continue
                
                # Create destination file path
                dest_filename = os.path.join(dir_name, filename)
                
                # Get or create destination file
                dest_file = codebase.get_file(dest_filename)
                if not dest_file:
                    dest_file = codebase.create_file(dest_filename)
                
                # Move all symbols from source to destination
                for symbol in source_file.symbols:
                    try:
                        symbol.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")
                    except Exception as e:
                        print(f"Error moving symbol {symbol.name}: {e}")
    
    # Update imports in all Python files
    for root, _, files in os.walk(base_path):
        for filename in files:
            if filename.endswith(".py"):
                file_path = os.path.join(root, filename)
                update_imports_in_file(file_path, file_mappings)
    
    print("Analyzers module organization complete!")


def extend_structure(base_path=None, new_dirs=None):
    """
    Extend the analyzers module structure by creating new directories.
    
    Args:
        base_path: Base path of the analyzers module. If None, use the current directory.
        new_dirs: List of new directories to create. If None, use default list.
    """
    # Determine base path
    if base_path is None:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Default new directories if not provided
    if new_dirs is None:
        new_dirs = ["issues", "dependencies"]
    
    print(f"Extending analyzers module structure at: {base_path}")
    
    # Create new directories
    for dir_name in new_dirs:
        dir_path = create_directory(base_path, dir_name)
        print(f"Created directory: {dir_path}")
    
    print("Structure extension complete!")


if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="Organize analyzers module")
    parser.add_argument("--path", help="Base path of the analyzers module")
    parser.add_argument("--organize", action="store_true", help="Reorganize existing files")
    parser.add_argument("--extend", action="store_true", help="Extend structure with new directories")
    parser.add_argument("--dirs", nargs="+", help="New directories to create")
    
    args = parser.parse_args()
    
    # Determine base path
    base_path = args.path or os.path.dirname(os.path.abspath(__file__))
    
    # Perform requested operations
    if args.organize:
        organize_analyzers(base_path)
    
    if args.extend:
        extend_structure(base_path, args.dirs)
    
    # If no operation specified, show help
    if not (args.organize or args.extend):
        parser.print_help()
