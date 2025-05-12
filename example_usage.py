#!/usr/bin/env python3
"""
Example usage of the Module Disassembler for Codegen.

This script demonstrates how to use the module disassembler to analyze
and restructure the Codegen codebase.
"""

import os
import sys
import argparse
from pathlib import Path
from module_disassembler import ModuleDisassembler

def main():
    """Example usage of the module disassembler."""
    parser = argparse.ArgumentParser(description="Example usage of the Module Disassembler")
    
    parser.add_argument("--repo-path", default=".", help="Path to the repository to analyze (default: current directory)")
    parser.add_argument("--output-dir", default="./restructured_modules", help="Directory to output the restructured modules")
    parser.add_argument("--report-file", default="./disassembler_report.json", help="Path to the output report file")
    parser.add_argument("--similarity-threshold", type=float, default=0.8, help="Threshold for considering functions similar (0.0-1.0)")
    parser.add_argument("--focus-dir", default=None, help="Focus on a specific directory (e.g., 'codegen-on-oss')")
    
    args = parser.parse_args()
    
    # Resolve paths
    repo_path = Path(args.repo_path).resolve()
    output_dir = Path(args.output_dir).resolve()
    report_file = Path(args.report_file).resolve()
    
    # If focus directory is specified, adjust the repo path
    if args.focus_dir:
        focus_path = repo_path / args.focus_dir
        if not focus_path.exists():
            print(f"Error: Focus directory '{args.focus_dir}' does not exist in '{repo_path}'")
            sys.exit(1)
        repo_path = focus_path
    
    print(f"Analyzing repository: {repo_path}")
    print(f"Output directory: {output_dir}")
    print(f"Report file: {report_file}")
    print(f"Similarity threshold: {args.similarity_threshold}")
    
    try:
        # Initialize the disassembler
        disassembler = ModuleDisassembler(repo_path=repo_path)
        
        # Perform the analysis
        print("Analyzing codebase...")
        disassembler.analyze(similarity_threshold=args.similarity_threshold)
        
        # Print summary statistics
        print("\nAnalysis Summary:")
        print(f"Total functions: {len(disassembler.functions)}")
        print(f"Duplicate groups: {len(disassembler.duplicate_groups)}")
        print(f"Similar groups: {len(disassembler.similar_groups)}")
        print("\nFunctions by category:")
        for category, funcs in disassembler.categorized_functions.items():
            print(f"  - {category}: {len(funcs)} functions")
        
        # Generate restructured modules
        print("\nGenerating restructured modules...")
        disassembler.generate_restructured_modules(output_dir=output_dir)
        
        # Generate report
        print("Generating report...")
        disassembler.generate_report(output_file=report_file)
        
        print(f"\nAnalysis complete!")
        print(f"Restructured modules saved to: {output_dir}")
        print(f"Report saved to: {report_file}")
        
        # Provide next steps
        print("\nNext steps:")
        print("1. Review the generated report to understand the codebase structure")
        print("2. Examine the restructured modules to see the new organization")
        print("3. Use the restructured modules as a reference for refactoring")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

