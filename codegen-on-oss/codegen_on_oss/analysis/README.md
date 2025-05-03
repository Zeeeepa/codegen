# Code Analysis Module with Error Context

This module provides robust and dynamic code analysis capabilities with a focus on error detection and contextual error information.

## Overview

The code analysis module consists of several components:

1. **CodeAnalyzer**: The main class that integrates all analysis components and provides a unified interface.
2. **ErrorContextAnalyzer**: A specialized class for detecting and analyzing errors in code.
3. **CodeError**: A class representing an error in code with detailed context information.
4. **API Endpoints**: FastAPI endpoints for accessing the analysis functionality.

## Features

### Code Structure Analysis

- Analyze codebase structure and dependencies
- Generate dependency graphs for files and symbols
- Analyze import relationships and detect circular imports
- Get detailed information about files, functions, classes, and symbols

### Error Detection and Analysis

- Detect syntax errors, type errors, parameter errors, and more
- Analyze function parameters and return statements for errors
- Detect undefined variables and unused imports
- Find circular dependencies between symbols
- Provide detailed context information for errors

### API Endpoints

- `/analyze_repo`: Analyze a repository and return various metrics
- `/analyze_symbol`: Analyze a symbol and return detailed information
- `/analyze_file`: Analyze a file and return detailed information
- `/analyze_function`: Analyze a function and return detailed information
- `/analyze_errors`: Analyze errors in a repository, file, or function

## Error Types

The module can detect the following types of errors:

- **Syntax Errors**: Invalid syntax in code
- **Type Errors**: Type mismatches in expressions
- **Parameter Errors**: Incorrect function parameters
- **Call Errors**: Incorrect function calls
- **Undefined Variables**: Variables used without being defined
- **Unused Imports**: Imports that are not used in the code
- **Circular Imports**: Circular dependencies between files
- **Circular Dependencies**: Circular dependencies between symbols
- **Name Errors**: References to undefined names
- **Import Errors**: Problems with import statements
- **Attribute Errors**: References to undefined attributes

## Error Severity Levels

The module assigns severity levels to each error:

- **Critical**: Errors that will definitely cause the code to crash or fail
- **High**: Errors that are likely to cause problems in most execution paths
- **Medium**: Errors that may cause problems in some execution paths
- **Low**: Minor issues that are unlikely to cause problems but should be fixed
- **Info**: Informational messages about potential improvements

## Usage

### Using the CodeAnalyzer

```python
from codegen import Codebase
from codegen_on_oss.analysis.analysis import CodeAnalyzer

# Create a codebase from a repository
codebase = Codebase.from_repo("owner/repo")

# Create an analyzer
analyzer = CodeAnalyzer(codebase)

# Analyze errors in the codebase
errors = analyzer.analyze_errors()

# Get detailed error context for a function
function_errors = analyzer.get_function_error_context("function_name")

# Get detailed error context for a file
file_errors = analyzer.get_file_error_context("path/to/file.py")
```

### Using the API

```bash
# Analyze a repository
curl -X POST "http://localhost:8000/analyze_repo" \
     -H "Content-Type: application/json" \
     -d '{"repo_url": "owner/repo"}'

# Analyze errors in a function
curl -X POST "http://localhost:8000/analyze_function" \
     -H "Content-Type: application/json" \
     -d '{"repo_url": "owner/repo", "function_name": "function_name"}'

# Analyze errors in a file
curl -X POST "http://localhost:8000/analyze_file" \
     -H "Content-Type: application/json" \
     -d '{"repo_url": "owner/repo", "file_path": "path/to/file.py"}'
```

## Error Context Example

Here's an example of the error context information provided for a function:

```json
{
  "function_name": "calculate_total",
  "file_path": "app/utils.py",
  "errors": [
    {
      "error_type": "parameter_error",
      "message": "Function 'calculate_discount' called with 1 arguments but expects 2",
      "line_number": 15,
      "severity": "high",
      "context_lines": {
        "13": "def calculate_total(items):",
        "14": "    total = sum(item.price for item in items)",
        "15": "    discount = calculate_discount(total)",
        "16": "    return total - discount",
        "17": ""
      },
      "suggested_fix": "Update call to provide 2 arguments: calculate_discount(total, discount_percent)"
    }
  ],
  "callers": [
    {"name": "process_order"}
  ],
  "callees": [
    {"name": "calculate_discount"}
  ],
  "parameters": [
    {
      "name": "items",
      "type": "List[Item]",
      "default": null
    }
  ],
  "return_info": {
    "type": "float",
    "statements": ["total - discount"]
  }
}
```

## Implementation Details

### ErrorContextAnalyzer

The `ErrorContextAnalyzer` class is responsible for detecting and analyzing errors in code. It uses various techniques to detect errors, including:

- **AST Analysis**: Parsing the code into an abstract syntax tree to detect syntax errors and undefined variables
- **Graph Analysis**: Building dependency graphs to detect circular imports and dependencies
- **Pattern Matching**: Using regular expressions to detect potential type errors and other issues
- **Static Analysis**: Analyzing function parameters, return statements, and variable usage

### CodeError

The `CodeError` class represents an error in code with detailed context information. It includes:

- **Error Type**: The type of error (syntax, type, parameter, etc.)
- **Message**: A descriptive message explaining the error
- **Location**: The file path and line number where the error occurs
- **Severity**: The severity of the error (critical, high, medium, low, info)
- **Context Lines**: The lines of code surrounding the error
- **Suggested Fix**: A suggested fix for the error

## Running the API Server

To run the API server locally:

```bash
cd codegen-on-oss
python -m codegen_on_oss.analysis.analysis
```

The server will be available at `http://localhost:8000`.
