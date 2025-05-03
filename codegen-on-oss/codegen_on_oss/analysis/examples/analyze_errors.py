#!/usr/bin/env python3
"""
Example script demonstrating how to use the error context analysis functionality.

This script analyzes a repository for errors and prints detailed error context information.
"""

import argparse
import json
import sys
from typing import Dict, Any

from codegen import Codebase
from codegen_on_oss.analysis.analysis import CodeAnalyzer


def print_error(error: Dict[str, Any]) -> None:
    """Print a formatted error message."""
    print(f"ERROR: {error['error_type']} ({error['severity']})")
    print(f"  Message: {error['message']}")
    
    if error.get('file_path'):
        print(f"  File: {error['file_path']}")
    
    if error.get('line_number'):
        print(f"  Line: {error['line_number']}")
    
    if error.get('context_lines'):
        print("  Context:")
        for line_num, line in error['context_lines'].items():
            prefix = ">" if str(line_num) == str(error.get('line_number')) else " "
            print(f"    {prefix} {line_num}: {line}")
    
    if error.get('suggested_fix'):
        print(f"  Suggested Fix: {error['suggested_fix']}")
    
    print()


def analyze_repo(repo_url: str) -> None:
    """Analyze a repository for errors."""
    print(f"Analyzing repository: {repo_url}")
    
    try:
        # Create a codebase from the repository
        codebase = Codebase.from_repo(repo_url)
        
        # Create an analyzer
        analyzer = CodeAnalyzer(codebase)
        
        # Analyze errors in the codebase
        errors = analyzer.analyze_errors()
        
        # Print summary
        total_errors = sum(len(file_errors) for file_errors in errors.values())
        print(f"\nFound {total_errors} errors in {len(errors)} files\n")
        
        # Print errors by file
        for file_path, file_errors in errors.items():
            print(f"File: {file_path}")
            print(f"  {len(file_errors)} errors found")
            
            # Print the first 3 errors for each file
            for i, error in enumerate(file_errors[:3]):
                print(f"  Error {i+1}:")
                print_error(error)
            
            if len(file_errors) > 3:
                print(f"  ... and {len(file_errors) - 3} more errors\n")
            
            print()
    
    except Exception as e:
        print(f"Error analyzing repository: {e}", file=sys.stderr)
        sys.exit(1)


def analyze_file(repo_url: str, file_path: str) -> None:
    """Analyze a specific file for errors."""
    print(f"Analyzing file: {file_path} in repository: {repo_url}")
    
    try:
        # Create a codebase from the repository
        codebase = Codebase.from_repo(repo_url)
        
        # Create an analyzer
        analyzer = CodeAnalyzer(codebase)
        
        # Get file error context
        file_error_context = analyzer.get_file_error_context(file_path)
        
        # Print errors
        if 'errors' in file_error_context:
            errors = file_error_context['errors']
            print(f"\nFound {len(errors)} errors\n")
            
            for i, error in enumerate(errors):
                print(f"Error {i+1}:")
                print_error(error)
        else:
            print("\nNo errors found or file not found")
    
    except Exception as e:
        print(f"Error analyzing file: {e}", file=sys.stderr)
        sys.exit(1)


def analyze_function(repo_url: str, function_name: str) -> None:
    """Analyze a specific function for errors."""
    print(f"Analyzing function: {function_name} in repository: {repo_url}")
    
    try:
        # Create a codebase from the repository
        codebase = Codebase.from_repo(repo_url)
        
        # Create an analyzer
        analyzer = CodeAnalyzer(codebase)
        
        # Get function error context
        function_error_context = analyzer.get_function_error_context(function_name)
        
        # Print function information
        if 'function_name' in function_error_context:
            print(f"\nFunction: {function_error_context['function_name']}")
            
            if 'file_path' in function_error_context:
                print(f"File: {function_error_context['file_path']}")
            
            # Print parameters
            if 'parameters' in function_error_context:
                params = function_error_context['parameters']
                print(f"\nParameters ({len(params)}):")
                for param in params:
                    param_type = f": {param['type']}" if param.get('type') else ""
                    default = f" = {param['default']}" if param.get('default') else ""
                    print(f"  {param['name']}{param_type}{default}")
            
            # Print return information
            if 'return_info' in function_error_context:
                return_info = function_error_context['return_info']
                print(f"\nReturn Type: {return_info.get('type', 'Unknown')}")
                if return_info.get('statements'):
                    print(f"Return Statements ({len(return_info['statements'])}):")
                    for stmt in return_info['statements']:
                        print(f"  return {stmt}")
            
            # Print callers and callees
            if 'callers' in function_error_context:
                callers = function_error_context['callers']
                print(f"\nCallers ({len(callers)}):")
                for caller in callers:
                    print(f"  {caller['name']}")
            
            if 'callees' in function_error_context:
                callees = function_error_context['callees']
                print(f"\nCallees ({len(callees)}):")
                for callee in callees:
                    print(f"  {callee['name']}")
            
            # Print errors
            if 'errors' in function_error_context:
                errors = function_error_context['errors']
                print(f"\nErrors ({len(errors)}):")
                for i, error in enumerate(errors):
                    print(f"Error {i+1}:")
                    print_error(error)
            else:
                print("\nNo errors found")
        else:
            print("\nFunction not found")
    
    except Exception as e:
        print(f"Error analyzing function: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze code for errors")
    parser.add_argument("repo_url", help="Repository URL (owner/repo)")
    
    subparsers = parser.add_subparsers(dest="command", help="Analysis command")
    
    # Repository analysis command
    repo_parser = subparsers.add_parser("repo", help="Analyze entire repository")
    
    # File analysis command
    file_parser = subparsers.add_parser("file", help="Analyze a specific file")
    file_parser.add_argument("file_path", help="Path to the file to analyze")
    
    # Function analysis command
    function_parser = subparsers.add_parser("function", help="Analyze a specific function")
    function_parser.add_argument("function_name", help="Name of the function to analyze")
    
    args = parser.parse_args()
    
    if args.command == "file":
        analyze_file(args.repo_url, args.file_path)
    elif args.command == "function":
        analyze_function(args.repo_url, args.function_name)
    else:
        analyze_repo(args.repo_url)


if __name__ == "__main__":
    main()

