# Enhanced Code Analysis Module

This module provides comprehensive code analysis capabilities for Python codebases, focusing on detailed error detection, function call analysis, and type validation.

## Features

### Error Detection

The error detection system identifies various issues in your code:

- **Parameter Validation**: Detects unused parameters, parameter count mismatches, and missing required parameters
- **Call Validation**: Validates function call-in and call-out points, detects circular dependencies
- **Return Validation**: Checks for inconsistent return types and values
- **Code Quality**: Identifies unreachable code, overly complex functions, and potential exceptions

### Function Call Analysis

The function call analysis provides insights into how functions interact:

- **Call Graph**: Builds a graph of function calls to visualize dependencies
- **Parameter Usage**: Analyzes how parameters are used within functions
- **Call Statistics**: Identifies most called functions, entry points, and leaf functions
- **Call Chains**: Finds paths between functions and calculates call depths

### Type Validation

The type validation system checks for type-related issues:

- **Type Annotations**: Validates type annotations and identifies missing annotations
- **Type Compatibility**: Checks for type mismatches and inconsistencies
- **Type Inference**: Infers types for variables and expressions where possible

## Usage

### Using the CodeAnalyzer

```python
from codegen import Codebase
from codegen_on_oss.analysis.analysis import CodeAnalyzer

# Create a codebase from a repository
codebase = Codebase.from_repo("owner/repo")

# Create an analyzer
analyzer = CodeAnalyzer(codebase)

# Get comprehensive analysis
results = analyzer.analyze_all()

# Access specific analysis components
error_analysis = analyzer.analyze_errors()
function_call_analysis = analyzer.analyze_function_calls()
type_analysis = analyzer.analyze_types()
complexity_analysis = analyzer.analyze_complexity()
import_analysis = analyzer.analyze_imports()

# Get detailed information about specific elements
function = analyzer.find_function_by_name("my_function")
call_graph = analyzer.get_function_call_graph()
callers = call_graph.get_callers("my_function")
callees = call_graph.get_callees("my_function")
```

### Using the API

The module provides a FastAPI-based API for analyzing codebases:

- `POST /analyze_repo`: Analyze an entire repository
- `POST /analyze_file`: Analyze a specific file
- `POST /analyze_function`: Analyze a specific function
- `POST /analyze_errors`: Get detailed error analysis with optional filtering

Example request to analyze a repository:

```json
{
  "repo_url": "owner/repo"
}
```

Example request to analyze a specific function:

```json
{
  "repo_url": "owner/repo",
  "function_name": "my_function"
}
```

## Error Categories

The error detection system identifies the following categories of errors:

- `PARAMETER_TYPE_MISMATCH`: Parameter type doesn't match expected type
- `PARAMETER_COUNT_MISMATCH`: Wrong number of parameters in function call
- `UNUSED_PARAMETER`: Parameter is declared but never used
- `UNDEFINED_PARAMETER`: Parameter is used but not declared
- `MISSING_REQUIRED_PARAMETER`: Required parameter is missing in function call
- `RETURN_TYPE_MISMATCH`: Return value type doesn't match declared return type
- `UNDEFINED_VARIABLE`: Variable is used but not defined
- `UNUSED_IMPORT`: Import is never used
- `UNUSED_VARIABLE`: Variable is defined but never used
- `POTENTIAL_EXCEPTION`: Function might throw an exception without proper handling
- `CALL_POINT_ERROR`: Error in function call-in or call-out point
- `CIRCULAR_DEPENDENCY`: Circular dependency between functions
- `INCONSISTENT_RETURN`: Inconsistent return statements in function
- `UNREACHABLE_CODE`: Code that will never be executed
- `COMPLEX_FUNCTION`: Function with high cyclomatic complexity

## Extending the Analysis

You can extend the analysis capabilities by:

1. Creating new detector classes that inherit from `ErrorDetector`
2. Implementing custom analysis logic in the `detect_errors` method
3. Adding the new detector to the `CodeAnalysisError` class

Example:

```python
from codegen_on_oss.analysis.error_detection import ErrorDetector, ErrorCategory, ErrorSeverity, CodeError

class MyCustomDetector(ErrorDetector):
    def detect_errors(self) -> List[CodeError]:
        self.clear_errors()
        
        # Implement custom detection logic
        for function in self.codebase.functions:
            # Check for issues
            if some_condition:
                self.errors.append(CodeError(
                    category=ErrorCategory.COMPLEX_FUNCTION,
                    severity=ErrorSeverity.WARNING,
                    message="Custom error message",
                    file_path=function.filepath,
                    function_name=function.name
                ))
        
        return self.errors
```

## Future Enhancements

Planned enhancements for the analysis module:

- Integration with external linters and type checkers
- Machine learning-based error detection
- Interactive visualization of analysis results
- Performance optimization for large codebases
- Support for more programming languages

