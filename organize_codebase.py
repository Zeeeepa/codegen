#!/usr/bin/env python3
"""
Codebase Organizer Script

This script helps organize a codebase by analyzing file contents and moving
related files into appropriate directories based on their functionality.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Define categories and their related patterns
CATEGORIES = {
    "analyzers": [
        r"analyzer", r"analysis", r"analyze"
    ],
    "code_quality": [
        r"code_quality", r"quality", r"lint"
    ],
    "context": [
        r"context", r"codebase_context"
    ],
    "dependencies": [
        r"dependenc", r"import"
    ],
    "issues": [
        r"issue", r"error"
    ],
    "visualization": [
        r"visual", r"display", r"render"
    ],
}

def read_file_content(file_path: str) -> str:
    """Read the content of a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""

def categorize_file(file_path: str, categories: Dict[str, List[str]]) -> List[str]:
    """Categorize a file based on its content and name."""
    file_categories = []
    content = read_file_content(file_path)
    filename = os.path.basename(file_path)
    
    # Check filename and content against category patterns
    for category, patterns in categories.items():
        for pattern in patterns:
            if re.search(pattern, filename, re.IGNORECASE) or re.search(pattern, content, re.IGNORECASE):
                file_categories.append(category)
                break
    
    return file_categories

def analyze_imports(file_path: str) -> Set[str]:
    """Analyze imports in a Python file."""
    imports = set()
    content = read_file_content(file_path)
    
    # Find import statements
    import_patterns = [
        r'import\s+([a-zA-Z0-9_\.]+)',
        r'from\s+([a-zA-Z0-9_\.]+)\s+import'
    ]
    
    for pattern in import_patterns:
        for match in re.finditer(pattern, content):
            imports.add(match.group(1))
    
    return imports

def build_dependency_graph(files: List[str]) -> Dict[str, Set[str]]:
    """Build a dependency graph for the files."""
    graph = {}
    module_to_file = {}
    
    # Map module names to files
    for file_path in files:
        if not file_path.endswith('.py'):
            continue
        
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        module_to_file[module_name] = file_path
    
    # Build the graph
    for file_path in files:
        if not file_path.endswith('.py'):
            continue
        
        imports = analyze_imports(file_path)
        graph[file_path] = set()
        
        for imp in imports:
            # Check if this is a local import
            parts = imp.split('.')
            if parts[0] in module_to_file:
                graph[file_path].add(module_to_file[parts[0]])
    
    return graph

def find_related_files(graph: Dict[str, Set[str]], file_path: str) -> Set[str]:
    """Find files related to the given file based on the dependency graph."""
    related = set()
    
    # Files that this file imports
    if file_path in graph:
        related.update(graph[file_path])
    
    # Files that import this file
    for other_file, deps in graph.items():
        if file_path in deps:
            related.add(other_file)
    
    return related

def organize_files(directory: str, dry_run: bool = True) -> Dict[str, List[str]]:
    """
    Organize files in the directory into categories.
    
    Args:
        directory: The directory containing the files to organize
        dry_run: If True, only print the planned changes without making them
        
    Returns:
        A dictionary mapping categories to lists of files
    """
    # Get all Python files
    py_files = [os.path.join(directory, f) for f in os.listdir(directory) 
               if f.endswith('.py') and os.path.isfile(os.path.join(directory, f))]
    
    # Build dependency graph
    graph = build_dependency_graph(py_files)
    
    # Categorize files
    categorized_files = {}
    for category in CATEGORIES:
        categorized_files[category] = []
    
    # Special case for README and init files
    categorized_files["root"] = []
    
    for file_path in py_files:
        filename = os.path.basename(file_path)
        
        # Keep some files in the root directory
        if filename in ['__init__.py', 'README.md']:
            categorized_files["root"].append(file_path)
            continue
            
        # Categorize the file
        categories = categorize_file(file_path, CATEGORIES)
        
        if not categories:
            # If no category found, use related files to determine category
            related = find_related_files(graph, file_path)
            for related_file in related:
                related_categories = categorize_file(related_file, CATEGORIES)
                categories.extend(related_categories)
        
        # Remove duplicates
        categories = list(set(categories))
        
        if not categories:
            # If still no category, put in a default category based on filename
            if "analyzer" in filename:
                categories = ["analyzers"]
            elif "context" in filename:
                categories = ["context"]
            elif "issue" in filename or "error" in filename:
                categories = ["issues"]
            elif "visual" in filename:
                categories = ["visualization"]
            elif "depend" in filename:
                categories = ["dependencies"]
            elif "quality" in filename:
                categories = ["code_quality"]
            else:
                # Default to analyzers if nothing else matches
                categories = ["analyzers"]
        
        # Use the first category (most relevant)
        primary_category = categories[0]
        categorized_files[primary_category].append(file_path)
    
    # Print and execute the organization plan
    for category, files in categorized_files.items():
        if not files:
            continue
            
        print(f"\nCategory: {category}")
        for file_path in files:
            print(f"  - {os.path.basename(file_path)}")
            
        if not dry_run and category != "root":
            # Create the category directory if it doesn't exist
            category_dir = os.path.join(directory, category)
            os.makedirs(category_dir, exist_ok=True)
            
            # Move files to the category directory
            for file_path in files:
                if category != "root":
                    dest_path = os.path.join(category_dir, os.path.basename(file_path))
                    shutil.move(file_path, dest_path)
                    print(f"    Moved to {dest_path}")
    
    return categorized_files

def main():
    """Main function to organize the codebase."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Organize a codebase by categorizing files.')
    parser.add_argument('directory', help='The directory containing the files to organize')
    parser.add_argument('--execute', action='store_true', help='Execute the organization plan (default is dry run)')
    
    args = parser.parse_args()
    
    print(f"Analyzing files in {args.directory}...")
    organize_files(args.directory, dry_run=not args.execute)
    
    if not args.execute:
        print("\nThis was a dry run. Use --execute to actually move the files.")
    else:
        print("\nFiles have been organized.")

if __name__ == "__main__":
    main()

