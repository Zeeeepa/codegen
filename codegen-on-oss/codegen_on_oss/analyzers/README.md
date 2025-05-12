# Codegen Analyzers

This directory contains the code analysis modules for the Codegen project. These analyzers provide comprehensive static code analysis, quality checking, dependency analysis, and PR validation capabilities.

## Modules

### Core Analyzers

- **analyzer.py**: Modern analyzer architecture with plugin system
- **base_analyzer.py**: Base class for all code analyzers
- **codebase_analyzer.py**: Comprehensive codebase analysis
- **code_quality.py**: Code quality analysis
- **dependencies.py**: Dependency analysis
- **error_analyzer.py**: Error detection and analysis
- **parser.py**: Code parsing and AST generation for multiple languages

### Support Modules

- **api.py**: API interface for analyzers
- **analyzer_manager.py**: Manages analyzer plugins
- **codebase_context.py**: Provides context for codebase analysis
- **codebase_visualizer.py**: Visualization tools for codebases
- **issue_analyzer.py**: Issue detection and analysis
- **issue_types.py**: Definitions for issue types
- **issues.py**: Issue tracking system

## Parser Module

The `parser.py` module provides specialized parsing functionality for code analysis, including abstract syntax tree (AST) generation and traversal for multiple programming languages. It serves as a foundation for various code analyzers in the system.

### Key Features

- Abstract syntax tree (AST) generation and traversal
- Support for multiple programming languages (Python, JavaScript, TypeScript)
- Symbol extraction (functions, classes, variables)
- Dependency analysis (imports, requires)
- Error handling and reporting

### Usage Examples

#### Basic Parsing

```python
from codegen_on_oss.analyzers.parser import parse_file, parse_code

# Parse a file
ast = parse_file("path/to/file.py")

# Parse code directly
code = "def hello(): print('Hello, World!')"
ast = parse_code(code, "python")
```

#### Language-Specific Parsing

```python
from codegen_on_oss.analyzers.parser import PythonParser, JavaScriptParser, TypeScriptParser

# Python parsing
python_parser = PythonParser()
python_ast = python_parser.parse_file("script.py")

# JavaScript parsing
js_parser = JavaScriptParser()
js_ast = js_parser.parse_file("app.js")

# TypeScript parsing
ts_parser = TypeScriptParser()
ts_ast = ts_parser.parse_file("component.ts")
```

#### Symbol and Dependency Extraction

```python
from codegen_on_oss.analyzers.parser import parse_file, create_parser

# Parse a file
ast = parse_file("path/to/file.py")

# Create a parser for the language
parser = create_parser("python")

# Extract symbols (functions, classes, variables)
symbols = parser.get_symbols(ast)
for symbol in symbols:
    print(f"{symbol['type']}: {symbol['name']}")

# Extract dependencies (imports, requires)
dependencies = parser.get_dependencies(ast)
for dep in dependencies:
    if dep["type"] == "import":
        print(f"import {dep['module']}")
    elif dep["type"] == "from_import":
        print(f"from {dep['module']} import {dep['name']}")
```

## Integration with Other Analyzers

The analyzers in this directory work together to provide comprehensive code analysis capabilities. The typical workflow is:

1. Parse the code using `parser.py`
2. Analyze the code quality using `code_quality.py`
3. Analyze dependencies using `dependencies.py`
4. Detect errors using `error_analyzer.py`
5. Generate reports and visualizations

## API Usage

The `api.py` module provides a high-level interface for using the analyzers:

```python
from codegen_on_oss.analyzers.api import create_api, api_analyze_codebase

# Create API instance
api = create_api()

# Analyze a codebase
result = api_analyze_codebase(repo_url="https://github.com/user/repo")

# Access analysis results
print(f"Issues found: {len(result.issues)}")
print(f"Code quality score: {result.quality_score}")
```
