# Module Disassembler and Restructurer

A powerful tool for analyzing codebases, identifying duplicate and redundant code, and restructuring modules based on their functionality.

## Overview

The Module Disassembler is designed to help you:

1. **Analyze** your codebase to understand its structure
2. **Identify** duplicate and redundant code
3. **Group** functions by their functionality
4. **Restructure** your codebase into more logical modules

This tool is particularly useful for:
- Refactoring large codebases
- Understanding unfamiliar code
- Improving code organization
- Reducing technical debt
- Preparing for architectural changes

## Features

- **Function Extraction**: Extracts all functions from your codebase
- **Duplicate Detection**: Identifies exact and near-duplicate functions
- **Functionality Grouping**: Groups functions based on their purpose
- **Module Restructuring**: Generates new modules organized by functionality
- **Comprehensive Reporting**: Provides detailed reports in multiple formats

## Installation

The Module Disassembler requires the Codegen SDK to be installed:

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/codegen.git
cd codegen

# Install dependencies
pip install -e .
```

## Usage

```bash
python module_disassembler.py --repo-path /path/to/your/repo --output-dir /path/to/output
```

### Command Line Options

- `--repo-path`: Path to the repository to analyze (required)
- `--output-dir`: Directory to output restructured modules (optional)
- `--output-format`: Output format for the report (`console` or `json`, default: `console`)
- `--output-file`: File to write the report to (for JSON format, optional)

### Example

```bash
# Analyze a repository and generate restructured modules
python module_disassembler.py --repo-path ./src/codegen --output-dir ./restructured

# Generate a JSON report
python module_disassembler.py --repo-path ./src/codegen --output-format json --output-file report.json
```

## How It Works

1. **Function Extraction**: The tool scans your codebase and extracts all functions using regex pattern matching (a more sophisticated implementation would use AST parsing).

2. **Duplicate Detection**: Functions are compared to identify exact duplicates (same hash) and near-duplicates (similarity above a threshold).

3. **Functionality Grouping**: Functions are grouped based on their names and purposes using predefined patterns.

4. **Module Restructuring**: New modules are generated for each function group, with proper imports and documentation.

## Function Groups

Functions are grouped into the following categories:

- **validation**: Functions related to validating data
- **data_processing**: Functions for processing or transforming data
- **io_operations**: Functions for reading/writing data
- **api_calls**: Functions for making API requests
- **authentication**: Functions related to user authentication
- **database**: Functions for database operations
- **utility**: Helper and utility functions
- **configuration**: Functions for handling configuration
- **logging**: Functions for logging
- **testing**: Functions related to testing
- **misc**: Functions that don't fit into other categories

## Output

The tool generates:

1. **Restructured Modules**: Python files organized by functionality
2. **Package Structure**: An `__init__.py` file that imports all modules
3. **Analysis Report**: A detailed report of the analysis results

## Limitations

- The current implementation uses regex for function extraction, which may not handle all edge cases correctly. A more robust implementation would use AST parsing.
- Function grouping is based on name patterns, which may not always accurately reflect the function's purpose.
- The tool currently only supports Python code, but could be extended to support other languages.

## Future Improvements

- Use AST parsing for more accurate function extraction
- Implement more sophisticated code similarity algorithms
- Add support for additional programming languages
- Improve function grouping using NLP techniques
- Add visualization of code dependencies
- Implement interactive mode for manual grouping

## License

This tool is part of the Codegen SDK and is subject to the same license terms.

