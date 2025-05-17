#!/usr/bin/env python
"""
Test runner for the CLI module.

This script runs all the tests for the CLI module and generates a coverage report.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_tests():
    """Run all tests for the CLI module."""
    # Get the directory of this script
    script_dir = Path(__file__).parent
    
    # Get the root directory of the project
    root_dir = script_dir.parent.parent.parent.parent
    
    # Change to the root directory
    os.chdir(root_dir)
    
    # Run the tests
    cmd = [
        "pytest",
        "tests/unit/codegen/cli",
        "tests/integration/codegen/cli",
        "--cov=codegen.cli",
        "--cov-report=term",
        "--cov-report=html:coverage_html",
        "-v",
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Print the output
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    
    # Return the exit code
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())

