#!/usr/bin/env python3
"""
Example usage of the Module Disassembler

This script demonstrates how to use the Module Disassembler to analyze
a codebase and restructure it based on functionality.
"""

import os
import sys
from pathlib import Path
from module_disassembler import ModuleDisassembler

def main():
    """Run the Module Disassembler on the Codegen SDK."""
    # Get the current directory
    current_dir = Path(__file__).parent.resolve()
    
    # Path to the Codegen SDK (assuming this script is in the root of the repo)
    repo_path = current_dir / "src" / "codegen"
    
    # Output directory for restructured modules
    output_dir = current_dir / "restructured_modules"
    
    print(f"Analyzing Codegen SDK at: {repo_path}")
    print(f"Output directory: {output_dir}")
    
    # Initialize the disassembler
    disassembler = ModuleDisassembler(
        repo_path=str(repo_path),
        output_dir=str(output_dir)
    )
    
    # Run the analysis
    results = disassembler.analyze()
    
    # Generate a report
    disassembler.generate_report(output_format="console")
    
    # Also generate a JSON report
    disassembler.generate_report(
        output_format="json",
        output_file=str(output_dir / "analysis_report.json")
    )
    
    print("\nAnalysis complete!")
    print(f"Total functions analyzed: {results['total_functions']}")
    print(f"Duplicate functions found: {results['duplicate_functions']}")
    print(f"Restructured modules generated: {results['restructured_modules']}")
    print(f"Check {output_dir} for the restructured modules")

if __name__ == "__main__":
    main()

