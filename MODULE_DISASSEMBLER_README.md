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

- **Function Extraction**: Extracts all functions from your codebase using Codegen SDK
- **Duplicate Detection**: Identifies exact and near-duplicate functions
- **Functionality Grouping**: Groups functions based on their purpose
- **Module Restructuring**: Generates new modules organized by functionality
- **Comprehensive Reporting**: Provides detailed reports in multiple formats

## Codegen SDK Integration

This tool leverages the Codegen SDK to provide advanced code analysis capabilities:

- **Symbol Extraction**: Uses the SDK to extract functions, classes, and other symbols
- **Dependency Analysis**: Analyzes function call relationships using the SDK's call graph
- **Type Information**: Leverages the SDK's type inference capabilities
- **Semantic Understanding**: Benefits from the SDK's semantic code understanding

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
- `--output-dir`: Directory to output restructured modules (required)
- `--report-file`: File to write the report to (default: disassembler_report.json)
- `--similarity-threshold`: Threshold for considering functions similar (0.0-1.0, default: 0.8)
- `--language`: Programming language of the codebase (auto-detected if not provided)

### Example Usage

```bash
# Analyze a repository and generate restructured modules
python module_disassembler.py --repo-path ./src/codegen --output-dir ./restructured

# Focus on a specific directory
python example_usage.py --repo-path . --focus-dir codegen-on-oss --output-dir ./restructured

# Specify a language and similarity threshold
python module_disassembler.py --repo-path ./src/codegen --output-dir ./restructured --language python --similarity-threshold 0.7
```

## How It Works

1. **Function Extraction**: The tool uses Codegen SDK to extract all functions from your codebase, with a fallback to AST parsing if needed.

2. **Duplicate Detection**: Functions are compared to identify exact duplicates (same hash) and near-duplicates (similarity above a threshold).

3. **Dependency Analysis**: The tool builds a dependency graph showing which functions call other functions, using the SDK's call graph capabilities.

4. **Functionality Grouping**: Functions are grouped based on their names and purposes using predefined patterns.

5. **Module Restructuring**: New modules are generated for each function group, with proper imports and documentation.

## Function Categories

Functions are grouped into the following categories:

- **analysis**: Functions for analyzing, extracting, parsing, or processing data
- **visualization**: Functions for visualizing, plotting, or displaying data
- **utility**: Helper and utility functions
- **io**: Functions for reading/writing data
- **validation**: Functions for validating or checking data
- **metrics**: Functions for measuring, calculating, or computing metrics
- **core**: Core functionality like initialization, main functions, etc.
- **other**: Functions that don't fit into other categories

## Output

The tool generates:

1. **Restructured Modules**: Python files organized by functionality
2. **Package Structure**: An `__init__.py` file that imports all modules
3. **Analysis Report**: A detailed report of the analysis results

## Fallback Mechanisms

The tool is designed to work even if the Codegen SDK is not fully functional:

- If SDK function extraction fails, it falls back to AST-based extraction
- If SDK dependency analysis fails, it falls back to AST-based dependency analysis
- All core functionality works without the SDK, but with reduced capabilities

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
