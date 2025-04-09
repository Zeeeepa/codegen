#!/usr/bin/env python3
"""
Script to fix import statements in the codegen repository.
This script standardizes imports to use absolute imports.
"""

import os
import re
import sys
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix imports in a single file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace relative imports with absolute imports
    # Pattern: from .xxx import yyy -> from codegen.agents.xxx import yyy
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
        content
    )
    
    # Replace single-dot imports
    modified_content = re.sub(
        r'from \. import', 
        f'from {module_path} import', 
        modified_content
    )
    
    # Write back if changes were made
    if content != modified_content:
        with open(file_path, 'w') as f:
            f.write(modified_content)
        return True
    return False

def main():
    """Main function to fix imports in all Python files."""
    agents_dir = Path('src/codegen/agents')
    if not agents_dir.exists():
        print(f"Error: {agents_dir} does not exist")
        sys.exit(1)
    
    fixed_files = []
    for root, _, files in os.walk(agents_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_imports_in_file(file_path):
                    fixed_files.append(file_path)
    
    print(f"Fixed imports in {len(fixed_files)} files:")
    for file in fixed_files:
        print(f"  - {file}")

if __name__ == "__main__":
    main()
