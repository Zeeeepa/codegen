#!/usr/bin/env python3
"""
Specific Codebase Organizer

This script organizes the specific codebase structure shown in the screenshot,
with 5 folders and 21 Python files in the root directory.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Set

# Define the organization structure based on the files in the screenshot
ORGANIZATION_PLAN = {
    "analyzers": [
        "analyzer.py",
        "analyzer_manager.py",
        "base_analyzer.py",
        "code_quality_analyzer.py",
        "codebase_analyzer.py",
        "dependency_analyzer.py",
        "error_analyzer.py",
        "unified_analyzer.py"
    ],
    "code_quality": [
        "code_quality.py"
    ],
    "context": [
        "codebase_context.py",
        "context_codebase.py",
        "current_code_codebase.py"
    ],
    "issues": [
        "issue_analyzer.py",
        "issue_types.py",
        "issues.py"
    ],
    "dependencies": [
        "dependencies.py"
    ],
    # Files to keep in root
    "root": [
        "__init__.py",
        "api.py",
        "README.md"
    ]
}

def organize_specific_codebase(directory: str, dry_run: bool = True) -> None:
    """
    Organize the specific codebase structure.
    
    Args:
        directory: The directory containing the files to organize
        dry_run: If True, only print the planned changes without making them
    """
    print(f"Organizing codebase in {directory}...")
    
    # Create directories if they don't exist (unless dry run)
    if not dry_run:
        for category in ORGANIZATION_PLAN:
            if category != "root":
                os.makedirs(os.path.join(directory, category), exist_ok=True)
    
    # Process each file according to the plan
    for category, files in ORGANIZATION_PLAN.items():
        print(f"\nCategory: {category}")
        
        for filename in files:
            source_path = os.path.join(directory, filename)
            
            # Skip if file doesn't exist
            if not os.path.exists(source_path):
                print(f"  - {filename} (not found, skipping)")
                continue
                
            print(f"  - {filename}")
            
            # Move the file if not a dry run and not in root category
            if not dry_run and category != "root":
                dest_path = os.path.join(directory, category, filename)
                shutil.move(source_path, dest_path)
                print(f"    Moved to {dest_path}")
    
    # Handle any remaining Python files not explicitly categorized
    all_planned_files = [f for files in ORGANIZATION_PLAN.values() for f in files]
    remaining_files = [f for f in os.listdir(directory) 
                      if f.endswith('.py') and os.path.isfile(os.path.join(directory, f))
                      and f not in all_planned_files]
    
    if remaining_files:
        print("\nRemaining Python files (not categorized):")
        for filename in remaining_files:
            print(f"  - {filename}")
            
            # Try to categorize based on filename
            if "analyzer" in filename.lower():
                category = "analyzers"
            elif "context" in filename.lower() or "codebase" in filename.lower():
                category = "context"
            elif "visual" in filename.lower():
                category = "visualization"
            elif "issue" in filename.lower() or "error" in filename.lower():
                category = "issues"
            elif "depend" in filename.lower():
                category = "dependencies"
            elif "quality" in filename.lower():
                category = "code_quality"
            else:
                # Default to analyzers
                category = "analyzers"
                
            print(f"    Suggested category: {category}")
            
            # Move the file if not a dry run
            if not dry_run:
                os.makedirs(os.path.join(directory, category), exist_ok=True)
                dest_path = os.path.join(directory, category, filename)
                shutil.move(os.path.join(directory, filename), dest_path)
                print(f"    Moved to {dest_path}")

def main():
    """Main function to organize the specific codebase."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Organize the specific codebase structure.')
    parser.add_argument('directory', help='The directory containing the files to organize')
    parser.add_argument('--execute', action='store_true', help='Execute the organization plan (default is dry run)')
    
    args = parser.parse_args()
    
    organize_specific_codebase(args.directory, dry_run=not args.execute)
    
    if not args.execute:
        print("\nThis was a dry run. Use --execute to actually move the files.")
    else:
        print("\nFiles have been organized according to the plan.")
        
    print("\nAfter organizing, you may need to update imports in your code.")
    print("You can use the Codegen SDK to automatically update imports:")
    print("""
    # Example code to update imports after moving files
    from codegen.sdk import Codebase
    
    # Initialize the codebase
    codebase = Codebase("path/to/your/codebase")
    
    # Commit the changes to ensure the codebase is up-to-date
    codebase.commit()
    """)

if __name__ == "__main__":
    main()

