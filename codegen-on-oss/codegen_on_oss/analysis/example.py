"""
Example script demonstrating the usage of the enhanced code analysis module.
"""

import json
import sys
from pathlib import Path

from codegen import Codebase
from codegen_on_oss.analysis.analysis import CodeAnalyzer


def print_section(title):
    """Print a section title."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)


def print_json(data):
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=2))


def analyze_repo(repo_url, branch=None):
    """Analyze a repository and print the results."""
    print_section(f"Analyzing repository: {repo_url}")
    
    # Load the codebase
    print(f"Loading codebase from {repo_url}...")
    if branch:
        codebase = Codebase.from_repo(repo_url, branch=branch)
    else:
        codebase = Codebase.from_repo(repo_url)
    
    # Create analyzer
    analyzer = CodeAnalyzer(codebase)
    
    # Get codebase summary
    print_section("Codebase Summary")
    print(analyzer.get_codebase_summary())
    
    # Analyze errors
    print_section("Error Analysis")
    error_analysis = analyzer.analyze_errors()
    print(f"Total errors: {error_analysis['total_errors']}")
    print("\nError summary:")
    print_json(error_analysis['error_summary'])
    print("\nSeverity summary:")
    print_json(error_analysis['severity_summary'])
    
    # Show some errors if there are any
    if error_analysis['errors']:
        print("\nSample errors:")
        for i, error in enumerate(error_analysis['errors'][:5]):  # Show first 5 errors
            print(f"\n{i+1}. {error['category']} ({error['severity']}): {error['message']}")
            if error['function_name']:
                print(f"   Function: {error['function_name']}")
            if error['file_path']:
                print(f"   File: {error['file_path']}")
            if error['fix_suggestion']:
                print(f"   Suggestion: {error['fix_suggestion']}")
    
    # Analyze function calls
    print_section("Function Call Analysis")
    call_analysis = analyzer.analyze_function_calls()
    
    print("Most called functions:")
    for func, count in call_analysis['call_graph']['most_called']:
        print(f"- {func}: {count} calls")
    
    print("\nMost complex functions (by number of calls made):")
    for func, count in call_analysis['call_graph']['most_complex']:
        print(f"- {func}: calls {count} other functions")
    
    print("\nEntry point functions:")
    for func in call_analysis['call_graph']['entry_points'][:10]:  # Show first 10
        print(f"- {func}")
    
    print("\nLeaf functions:")
    for func in call_analysis['call_graph']['leaf_functions'][:10]:  # Show first 10
        print(f"- {func}")
    
    # Analyze circular dependencies
    if call_analysis['call_graph']['circular_dependencies']:
        print("\nCircular dependencies:")
        for i, cycle in enumerate(call_analysis['call_graph']['circular_dependencies'][:5]):  # Show first 5
            print(f"- Cycle {i+1}: {' -> '.join(cycle)}")
    
    # Analyze type annotations
    print_section("Type Analysis")
    type_analysis = analyzer.analyze_types()
    
    print("Type annotation coverage:")
    print_json(type_analysis['annotation_coverage'])
    
    if type_analysis['annotation_errors']:
        print("\nSample type annotation errors:")
        for i, error in enumerate(type_analysis['annotation_errors'][:5]):  # Show first 5
            print(f"\n{i+1}. {error['message']}")
            if error['function_name']:
                print(f"   Function: {error['function_name']}")
            if error['file_path']:
                print(f"   File: {error['file_path']}")
            if error['fix_suggestion']:
                print(f"   Suggestion: {error['fix_suggestion']}")
    
    # Analyze a specific function if there are any
    if codebase.functions:
        func = next(iter(codebase.functions))
        if hasattr(func, 'name'):
            print_section(f"Detailed Analysis of Function: {func.name}")
            func_analysis = analyzer.analyze_function(func.name)
            
            print("Function summary:")
            print(func_analysis['summary'])
            
            print("\nFunction call analysis:")
            print(f"- Calls: {', '.join(func_analysis['call_analysis']['calls'])}" if func_analysis['call_analysis']['calls'] else "- Calls: None")
            print(f"- Called by: {', '.join(func_analysis['call_analysis']['called_by'])}" if func_analysis['call_analysis']['called_by'] else "- Called by: None")
            print(f"- Call depth: {func_analysis['call_analysis']['call_depth']}")
            
            print("\nParameter analysis:")
            if 'parameters' in func_analysis['parameter_analysis']:
                for param in func_analysis['parameter_analysis']['parameters']:
                    print(f"- {param['name']}: {'Used' if param['is_used'] else 'Unused'}, Type: {param['type'] or 'Unknown'}")
            
            print("\nType analysis:")
            if 'inferred_types' in func_analysis['type_analysis']:
                print("Inferred types:")
                for var, type_name in func_analysis['type_analysis']['inferred_types'].items():
                    print(f"- {var}: {type_name}")
    
    # Analyze a specific file if there are any
    if codebase.files:
        file = next(iter(codebase.files))
        if hasattr(file, 'filepath'):
            print_section(f"Detailed Analysis of File: {file.filepath}")
            file_analysis = analyzer.analyze_file(file.filepath)
            
            print("File summary:")
            print(file_analysis['summary'])
            
            print("\nFunctions in file:")
            for func in file_analysis['functions']:
                print(f"- {func['name']}: Parameters: {', '.join(func['parameters'])}, Return type: {func['return_type'] or 'Unknown'}")
            
            print("\nClasses in file:")
            for cls in file_analysis['classes']:
                print(f"- {cls['name']}: Methods: {', '.join(cls['methods'])}")
            
            print("\nImports in file:")
            for imp in file_analysis['imports']:
                print(f"- {imp}")
            
            if file_analysis['errors']:
                print("\nErrors in file:")
                for i, error in enumerate(file_analysis['errors']):
                    print(f"- {error['category']}: {error['message']}")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python example.py <repo_url> [branch]")
        print("Example: python example.py https://github.com/user/repo main")
        return
    
    repo_url = sys.argv[1]
    branch = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        analyze_repo(repo_url, branch)
    except Exception as e:
        print(f"Error analyzing repository: {e}")


if __name__ == "__main__":
    main()

