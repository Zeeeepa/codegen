#!/usr/bin/env python3
"""
Test script for the organize.py module.

This script demonstrates how to use the organize.py module to extend
the structure of the analyzers module with new directories.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to allow importing organize
sys.path.insert(0, str(Path(__file__).parent))

try:
    from organize import extend_structure
except ImportError:
    print("Could not import organize module. Make sure it exists in the same directory.")
    sys.exit(1)


def main():
    """Run the test script."""
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("Testing organize.py module...")
    
    # Example 1: Extend structure with default directories
    print("\nExample 1: Extend structure with default directories (issues, dependencies)")
    extend_structure(current_dir)
    
    # Example 2: Extend structure with custom directories
    print("\nExample 2: Extend structure with custom directories")
    custom_dirs = ["metrics", "reports", "optimizations"]
    extend_structure(current_dir, custom_dirs)
    
    print("\nTest complete!")


if __name__ == "__main__":
    main()

