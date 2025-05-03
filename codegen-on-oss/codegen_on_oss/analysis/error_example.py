"""
Example script demonstrating the use of the error context analysis functionality.

This script shows how to use the CodeAnalyzer class to detect and analyze errors
in a codebase, providing detailed contextual information about the errors.
"""

from codegen import Codebase
from codegen_on_oss.analysis.analysis import CodeAnalyzer
from codegen_on_oss.analysis.error_context import ErrorType, ErrorSeverity


def main():
    """
    Main function demonstrating the use of the error context analysis functionality.
    """
    print("Analyzing a sample repository for errors...")
    
    # Load a codebase
    repo_name = "fastapi/fastapi"
    codebase = Codebase.from_repo(repo_name)
    
    print(f"Loaded codebase: {repo_name}")
    print(f"Files: {len(codebase.files)}")
    print(f"Functions: {len(codebase.functions)}")
    print(f"Classes: {len(codebase.classes)}")
    
    # Create analyzer instance
    analyzer = CodeAnalyzer(codebase)
    
    # Analyze errors in the entire codebase
    print("\n=== Codebase Error Analysis ===")
    error_analysis = analyzer.analyze_errors()
    
    # Count errors by type
    error_counts = {}
    total_errors = 0
    
    for file_path, errors in error_analysis.items():
        for error in errors:
            error_type = error["error_type"]
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
            total_errors += 1
    
    print(f"Found {total_errors} errors across {len(error_analysis)} files")
    
    if error_counts:
        print("\nError types:")
        for error_type, count in error_counts.items():
            print(f"- {error_type}: {count}")
    
    # Find files with the most errors
    files_with_errors = [(file_path, len(errors)) for file_path, errors in error_analysis.items()]
    files_with_errors.sort(key=lambda x: x[1], reverse=True)
    
    if files_with_errors:
        print("\nTop files with errors:")
        for file_path, count in files_with_errors[:5]:  # Show top 5
            print(f"- {file_path}: {count} errors")
    
    # Analyze a specific file
    if files_with_errors:
        file_to_analyze = files_with_errors[0][0]
        print(f"\n=== Detailed Error Analysis for {file_to_analyze} ===")
        file_error_context = analyzer.get_file_error_context(file_to_analyze)
        
        print(f"File: {file_error_context['file_path']}")
        print(f"Errors: {len(file_error_context['errors'])}")
        
        if file_error_context['errors']:
            print("\nDetailed errors:")
            for i, error in enumerate(file_error_context['errors'][:3], 1):  # Show top 3
                print(f"\nError {i}:")
                print(f"- Type: {error['error_type']}")
                print(f"- Message: {error['message']}")
                print(f"- Severity: {error['severity']}")
                if error['line_number']:
                    print(f"- Line: {error['line_number']}")
                if error['suggested_fix']:
                    print(f"- Suggested fix: {error['suggested_fix']}")
                
                if error['context_lines']:
                    print("- Context:")
                    for line_num, line in error['context_lines'].items():
                        prefix = ">" if line_num == error['line_number'] else " "
                        print(f"  {prefix} {line_num}: {line}")
        
        # Show functions in the file
        if file_error_context['functions']:
            print("\nFunctions in this file:")
            for func in file_error_context['functions']:
                error_count = len(func['errors'])
                error_suffix = f" ({error_count} errors)" if error_count > 0 else ""
                print(f"- {func['name']}{error_suffix}")
    
    # Analyze a specific function with errors
    function_to_analyze = None
    for file_path, errors in error_analysis.items():
        for error in errors:
            if error['symbol_name']:
                function_to_analyze = error['symbol_name']
                break
        if function_to_analyze:
            break
    
    if function_to_analyze:
        print(f"\n=== Detailed Error Analysis for function {function_to_analyze} ===")
        function_error_context = analyzer.get_function_error_context(function_to_analyze)
        
        print(f"Function: {function_error_context['function_name']}")
        print(f"File: {function_error_context['file_path']}")
        print(f"Errors: {len(function_error_context['errors'])}")
        
        if function_error_context['parameters']:
            print("\nParameters:")
            for param in function_error_context['parameters']:
                default = f" = {param['default']}" if param['default'] is not None else ""
                type_annotation = f": {param['type']}" if param['type'] else ""
                print(f"- {param['name']}{type_annotation}{default}")
        
        if function_error_context['return_info']['type']:
            print(f"\nReturn type: {function_error_context['return_info']['type']}")
        
        if function_error_context['callers']:
            print("\nCalled by:")
            for caller in function_error_context['callers']:
                print(f"- {caller['name']}")
        
        if function_error_context['callees']:
            print("\nCalls:")
            for callee in function_error_context['callees']:
                print(f"- {callee['name']}")
        
        if function_error_context['errors']:
            print("\nDetailed errors:")
            for i, error in enumerate(function_error_context['errors'], 1):
                print(f"\nError {i}:")
                print(f"- Type: {error['error_type']}")
                print(f"- Message: {error['message']}")
                print(f"- Severity: {error['severity']}")
                if error['line_number']:
                    print(f"- Line: {error['line_number']}")
                if error['suggested_fix']:
                    print(f"- Suggested fix: {error['suggested_fix']}")
                
                if error['context_lines']:
                    print("- Context:")
                    for line_num, line in error['context_lines'].items():
                        prefix = ">" if line_num == error['line_number'] else " "
                        print(f"  {prefix} {line_num}: {line}")
    
    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()

