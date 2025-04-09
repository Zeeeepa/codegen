#!/usr/bin/env python3
"""
Advanced script to fix import statements in the codegen repository.
This script standardizes imports to use absolute imports and checks for circular imports.
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict

def fix_imports_in_file(file_path):
    """Fix imports in a single file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    modified_content = content
    
    # If the file is in the agents directory, fix relative imports
    if 'src/codegen/agents' in str(file_path):
        # Get the relative path from src/codegen/agents
        rel_path = os.path.relpath(os.path.dirname(file_path), 'src/codegen/agents')
        if rel_path == '.':
            module_path = 'codegen.agents'
        else:
            module_path = f'codegen.agents.{rel_path.replace("/", ".")}'
        
        # Replace relative imports
        modified_content = re.sub(
            r'from \.([\w\.]+) import', 
            lambda m: f'from {module_path}.{m.group(1)} import', 
            modified_content
        )
        
        # Replace single-dot imports
        modified_content = re.sub(
            r'from \. import', 
            f'from {module_path} import', 
            modified_content
        )
        
        # Replace parent directory imports
        modified_content = re.sub(
            r'from \.\.([\w\.]+) import',
            lambda m: f'from codegen.{m.group(1)} import',
            modified_content
        )
    
    # Write back if changes were made
    if content != modified_content:
        with open(file_path, 'w') as f:
            f.write(modified_content)
        return True
    return False

def build_import_graph(directory):
    """Build a graph of imports to detect circular dependencies."""
    import_graph = defaultdict(set)
    file_to_module = {}
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                # Convert file path to module path
                rel_path = os.path.relpath(file_path, 'src')
                module_path = rel_path.replace('/', '.').replace('.py', '')
                file_to_module[file_path] = module_path
                
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Find all imports
                imports = re.findall(r'from\s+([\w\.]+)\s+import', content)
                imports += re.findall(r'import\s+([\w\.]+)', content)
                
                for imp in imports:
                    if imp.startswith('codegen.agents'):
                        import_graph[module_path].add(imp)
    
    return import_graph, file_to_module

def detect_circular_imports(import_graph):
    """Detect circular imports in the import graph."""
    visited = set()
    path = []
    circular_deps = []
    
    def dfs(node):
        visited.add(node)
        path.append(node)
        
        for neighbor in list(import_graph.get(node, [])):
            if neighbor in path:
                circular_deps.append(path[path.index(neighbor):] + [neighbor])
            elif neighbor not in visited:
                dfs(neighbor)
        
        path.pop()
    
    for node in list(import_graph.keys()):
        if node not in visited:
            dfs(node)
    
    return circular_deps

def main():
    """Main function to fix imports in all Python files."""
    # Fix imports in the agents directory
    agents_dir = Path('src/codegen/agents')
    if not agents_dir.exists():
        print(f"Error: {agents_dir} does not exist")
        sys.exit(1)
    
    fixed_files = []
    
    # First, fix imports in the agents directory
    for root, _, files in os.walk(agents_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_imports_in_file(file_path):
                    fixed_files.append(file_path)
    
    # Then, check for imports in dependent directories
    codegen_dir = Path('src/codegen')
    for root, _, files in os.walk(codegen_dir):
        # Skip the agents directory as we've already processed it
        if 'src/codegen/agents' in root:
            continue
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_imports_in_file(file_path):
                    fixed_files.append(file_path)
    
    print(f"Fixed imports in {len(fixed_files)} files:")
    for file in fixed_files:
        print(f"  - {file}")
    
    # Check for circular imports
    print("\nChecking for circular imports...")
    import_graph, file_to_module = build_import_graph(codegen_dir)
    circular_deps = detect_circular_imports(import_graph)
    
    if circular_deps:
        print(f"Found {len(circular_deps)} circular dependencies:")
        for i, dep in enumerate(circular_deps):
            print(f"  {i+1}. {' -> '.join(dep)}")
    else:
        print("No circular dependencies found.")

if __name__ == "__main__":
    main()
