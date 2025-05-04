#!/usr/bin/env python3
"""
Cleanup script for codegen-on-oss

This script removes unused example files and duplicate documentation
from the codegen-on-oss codebase.
"""

import argparse
import os
import shutil
from pathlib import Path
from typing import List

# Files to be removed
UNUSED_FILES = [
    "codegen_on_oss/analysis/commit_example.py",
    "codegen_on_oss/analysis/enhanced_server_example.py",
    "codegen_on_oss/analysis/example.py",
    "codegen_on_oss/analysis/server_example.py",
    "codegen_on_oss/analysis/swe_harness_example.py",
    "codegen_on_oss/analysis/README_ENHANCED.md",
]


def cleanup_files(dry_run=False) -> List[str]:
    """
    Remove unused files from the codebase

    Args:
        dry_run: If True, only print the files that would be removed without
                actually removing them

    Returns:
        list: List of files that were removed or would be removed in dry run
    """
    base_dir = Path(__file__).parent.parent.parent
    removed_files = []

    for file_path in UNUSED_FILES:
        full_path = base_dir / file_path
        if full_path.exists():
            if dry_run:
                print(f"Would remove: {full_path}")
            else:
                if full_path.is_file():
                    os.remove(full_path)
                elif full_path.is_dir():
                    shutil.rmtree(full_path)
                print(f"Removed: {full_path}")
            removed_files.append(str(full_path))
        else:
            print(f"File not found: {full_path}")

    return removed_files


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean up unused files in codegen-on-oss"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print files to be removed without removing them",
    )
    args = parser.parse_args()

    print("Starting cleanup process...")
    removed = cleanup_files(dry_run=args.dry_run)

    if args.dry_run:
        print(f"\nDry run completed. {len(removed)} files would be removed.")
    else:
        print(f"\nCleanup completed. {len(removed)} files were removed.")


if __name__ == "__main__":
    main()
