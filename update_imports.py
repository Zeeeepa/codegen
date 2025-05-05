#!/usr/bin/env python3
import os
import re
import subprocess

def find_files_with_pattern(pattern):
    """Find all files containing the given pattern."""
    result = subprocess.run(
        ["grep", "-r", "-l", pattern, "src/"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip().split('\n') if result.stdout else []

def update_file(file_path):
    """Update imports in the given file."""
    if not os.path.exists(file_path):
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Update imports
    updated_content = re.sub(
        r'from codegen\.sdk\.(.*)', 
        r'from graph_sitter.\1', 
        content
    )
    updated_content = re.sub(
        r'import codegen\.sdk(.*)', 
        r'import graph_sitter\1', 
        updated_content
    )
    updated_content = re.sub(
        r'from codegen\.gsbuild\.(.*)', 
        r'from gsbuild.\1', 
        updated_content
    )
    updated_content = re.sub(
        r'import codegen\.gsbuild(.*)', 
        r'import gsbuild\1', 
        updated_content
    )
    updated_content = re.sub(
        r'from codegen\.gscli\.(.*)', 
        r'from graph_sitter.gscli.\1', 
        updated_content
    )
    updated_content = re.sub(
        r'import codegen\.gscli(.*)', 
        r'import graph_sitter.gscli\1', 
        updated_content
    )
    
    # Special case for 'import codegen.sdk as sdk'
    updated_content = re.sub(
        r'import codegen\.sdk as sdk', 
        r'import graph_sitter as sdk', 
        updated_content
    )
    
    if content != updated_content:
        with open(file_path, 'w') as f:
            f.write(updated_content)
        return True
    
    return False

def main():
    # Find files with imports to update
    sdk_files = find_files_with_pattern('codegen.sdk')
    gsbuild_files = find_files_with_pattern('codegen.gsbuild')
    gscli_files = find_files_with_pattern('codegen.gscli')
    
    # Combine and deduplicate files
    all_files = list(set(sdk_files + gsbuild_files + gscli_files))
    all_files = [f for f in all_files if f and os.path.exists(f)]
    
    # Update each file
    updated_count = 0
    for file_path in all_files:
        if update_file(file_path):
            print(f"Updated: {file_path}")
            updated_count += 1
    
    print(f"Total files updated: {updated_count}")

if __name__ == "__main__":
    main()

