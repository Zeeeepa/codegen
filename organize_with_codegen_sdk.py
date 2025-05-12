#!/usr/bin/env python3
"""Codebase Organizer using Codegen SDK

This script uses the Codegen SDK to programmatically organize a codebase by
moving symbols between files and updating imports automatically.
"""

import os
import sys

try:
    from codegen.sdk import Codebase
except ImportError:
    print("Error: Codegen SDK not found. Please install it with:")
    print("pip install codegen-sdk")
    sys.exit(1)

# Define the organization structure based on the files in the screenshot
ORGANIZATION_PLAN = {
    "analyzers": ["analyzer.py", "analyzer_manager.py", "base_analyzer.py", "code_quality_analyzer.py", "codebase_analyzer.py", "dependency_analyzer.py", "error_analyzer.py", "unified_analyzer.py"],
    "code_quality": ["code_quality.py"],
    "context": ["codebase_context.py", "context_codebase.py", "current_code_codebase.py"],
    "issues": ["issue_analyzer.py", "issue_types.py", "issues.py"],
    "dependencies": ["dependencies.py"],
    # Files to keep in root
    "root": ["__init__.py", "api.py", "README.md"],
}


def organize_with_codegen_sdk(directory: str, dry_run: bool = True) -> None:
    """Organize the codebase using Codegen SDK.

    Args:
        directory: The directory containing the files to organize
        dry_run: If True, only print the planned changes without making them
    """
    print(f"Organizing codebase in {directory} using Codegen SDK...")

    # Initialize the codebase
    codebase = Codebase(directory)

    # Create directories if they don't exist (unless dry run)
    if not dry_run:
        for category in ORGANIZATION_PLAN:
            if category != "root":
                os.makedirs(os.path.join(directory, category), exist_ok=True)

    # Process each file according to the plan
    for category, files in ORGANIZATION_PLAN.items():
        if category == "root":
            continue  # Skip files that should stay in root

        print(f"\nCategory: {category}")

        for filename in files:
            source_path = os.path.join(directory, filename)

            # Skip if file doesn't exist
            if not os.path.exists(source_path):
                print(f"  - {filename} (not found, skipping)")
                continue

            print(f"  - {filename}")

            # Move the file if not a dry run
            if not dry_run:
                try:
                    # Get the source file
                    source_file = codebase.get_file(filename)

                    # Create the destination file path
                    dest_path = os.path.join(category, filename)

                    # Create the destination file if it doesn't exist
                    if not os.path.exists(os.path.join(directory, dest_path)):
                        dest_file = codebase.create_file(dest_path)
                    else:
                        dest_file = codebase.get_file(dest_path)

                    # Move all symbols from source to destination
                    for symbol in source_file.symbols:
                        print(f"    Moving symbol: {symbol.name}")
                        symbol.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

                    # Commit changes to ensure the codebase is up-to-date
                    codebase.commit()

                    print(f"    Moved to {dest_path} with imports updated")
                except Exception as e:
                    print(f"    Error moving {filename}: {e}")

    # Handle any remaining Python files not explicitly categorized
    all_planned_files = [f for files in ORGANIZATION_PLAN.values() for f in files]
    remaining_files = [f for f in os.listdir(directory) if f.endswith(".py") and os.path.isfile(os.path.join(directory, f)) and f not in all_planned_files]

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
                try:
                    # Get the source file
                    source_file = codebase.get_file(filename)

                    # Create the destination file path
                    dest_path = os.path.join(category, filename)

                    # Create the destination file if it doesn't exist
                    if not os.path.exists(os.path.join(directory, dest_path)):
                        dest_file = codebase.create_file(dest_path)
                    else:
                        dest_file = codebase.get_file(dest_path)

                    # Move all symbols from source to destination
                    for symbol in source_file.symbols:
                        print(f"    Moving symbol: {symbol.name}")
                        symbol.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

                    # Commit changes to ensure the codebase is up-to-date
                    codebase.commit()

                    print(f"    Moved to {dest_path} with imports updated")
                except Exception as e:
                    print(f"    Error moving {filename}: {e}")


def main():
    """Main function to organize the codebase using Codegen SDK."""
    import argparse

    parser = argparse.ArgumentParser(description="Organize the codebase using Codegen SDK.")
    parser.add_argument("directory", help="The directory containing the files to organize")
    parser.add_argument("--execute", action="store_true", help="Execute the organization plan (default is dry run)")

    args = parser.parse_args()

    organize_with_codegen_sdk(args.directory, dry_run=not args.execute)

    if not args.execute:
        print("\nThis was a dry run. Use --execute to actually move the files.")
    else:
        print("\nFiles have been organized according to the plan.")


if __name__ == "__main__":
    main()
