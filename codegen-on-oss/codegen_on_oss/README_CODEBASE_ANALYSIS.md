# Codebase Analysis Tools

This directory contains a set of tools for analyzing codebases using the Codegen SDK. These tools provide comprehensive analysis capabilities, including code quality assessment, dependency analysis, and context retrieval.

## Overview

The codebase analysis tools consist of three main components:

1. **Codebase Analyzer** (`codebase_analyzer.py`): A comprehensive analyzer that identifies code quality issues, dependency problems, and structural concerns.

2. **Context Retriever** (`context_retriever.py`): A utility for retrieving and organizing context from a codebase, focusing on code structure, dependencies, and relationships.

3. **Analysis CLI** (`analyze.py`): A command-line interface for running analyses and retrieving context from codebases.

## Installation

These tools are part of the `codegen-on-oss` package. To use them, you need to have the Codegen SDK installed:

```bash
pip install codegen-sdk
```

## Usage

### Command-Line Interface

The `analyze.py` script provides a command-line interface for running analyses and retrieving context:

#### Analyze a Codebase

```bash
python -m codegen_on_oss.analyze analyze --repo-path /path/to/repo [--language python] [--output-format text|json|html] [--output-file results.json]
```

This command performs a comprehensive analysis of the codebase, identifying issues related to code quality, dependencies, and structure.

#### Get Context from a Codebase

```bash
python -m codegen_on_oss.analyze context --repo-path /path/to/repo [--file path/to/file.py] [--function function_name] [--class class_name] [--output-file context.json]
```

This command retrieves context information about a specific file, function, or class in the codebase.

#### Get a Summary of a Codebase

```bash
python -m codegen_on_oss.analyze summary --repo-path /path/to/repo [--output-file summary.json]
```

This command generates a summary of the codebase, including statistics and high-level issue counts.

### Programmatic Usage

You can also use the tools programmatically in your Python code:

#### Using the Codebase Analyzer

```python
from codegen_on_oss.codebase_analyzer import CodebaseAnalyzer

# Initialize the analyzer
analyzer = CodebaseAnalyzer(repo_path="/path/to/repo", language="python")

# Perform the analysis
results = analyzer.analyze(output_format="json", output_file="results.json")
```

#### Using the Context Retriever

```python
from codegen.sdk.core.codebase import Codebase
from codegen_on_oss.context_retriever import get_codebase_context

# Initialize the codebase
codebase = Codebase(repo_path="/path/to/repo")

# Get context
context = get_codebase_context(codebase)

# Get file context
file_context = context.get_file_context("path/to/file.py")

# Get function context
function_context = context.get_function_context("function_name")

# Get class context
class_context = context.get_class_context("ClassName")
```

## Features

### Codebase Analyzer

The Codebase Analyzer identifies the following types of issues:

- **Code Quality Issues**:
  - Unused functions
  - Unused imports
  - Functions with unused parameters
  - Overly complex functions

- **Dependency Issues**:
  - Parameter mismatches in function calls
  - Circular imports

- **Structure Issues**:
  - Excessively large files
  - Deeply nested functions

### Context Retriever

The Context Retriever provides the following types of context:

- **Codebase Summary**:
  - File count
  - Function count
  - Class count
  - Import count
  - File extensions
  - Top-level directories

- **File Context**:
  - Functions in the file
  - Classes in the file
  - Imports in the file
  - Files that import this file

- **Function Context**:
  - Parameters
  - Function calls
  - Call sites
  - Recursion status

- **Class Context**:
  - Methods
  - Attributes
  - Parent classes
  - Child classes

## Output Formats

The Codebase Analyzer supports the following output formats:

- **Text**: Plain text output suitable for console display
- **JSON**: Structured JSON output suitable for programmatic processing
- **HTML**: Rich HTML report with formatting and styling

## Examples

### Example 1: Analyze a Python Codebase

```bash
python -m codegen_on_oss.analyze analyze --repo-path /path/to/repo --language python --output-format html --output-file analysis_report.html
```

### Example 2: Get Context for a Specific Function

```bash
python -m codegen_on_oss.analyze context --repo-path /path/to/repo --function process_data --output-file function_context.json
```

### Example 3: Get a Summary of a Codebase

```bash
python -m codegen_on_oss.analyze summary --repo-path /path/to/repo --output-file codebase_summary.json
```

## Contributing

Contributions to the codebase analysis tools are welcome! Please feel free to submit issues or pull requests to improve the functionality or fix bugs.

## License

These tools are released under the same license as the Codegen SDK.

