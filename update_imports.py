#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path

def update_imports_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace imports
    updated_content = re.sub(
        r'from codegen\.sdk(\..*)', 
        r'from graph_sitter\1', 
        content
    )
    
    updated_content = re.sub(
        r'import codegen\.sdk(\..*)', 
        r'import graph_sitter\1', 
        updated_content
    )
    
    # Write back if changes were made
    if content != updated_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        return True
    return False

def main():
    src_dir = Path('src')
    py_files = list(src_dir.glob('**/*.py'))
    
    updated_files = 0
    for file_path in py_files:
        if update_imports_in_file(file_path):
            updated_files += 1
            print(f"Updated imports in {file_path}")
    
    print(f"\nTotal files updated: {updated_files}")

if __name__ == "__main__":
    main()

