# Module Disassembler for Codegen

This tool analyzes, restructures, and deduplicates code in the Codegen codebase, particularly focusing on analysis modules. It leverages the **Codegen SDK** to extract functions, identify duplicates, and reorganize code based on functionality.

## Features

- **SDK-Powered Analysis**: Uses Codegen's SDK for deep code analysis
- **Function Extraction**: Extracts all functions from Python files in the codebase
- **Duplicate Detection**: Identifies exact duplicates and similar functions
- **Function Categorization**: Categorizes functions by purpose (analysis, visualization, utility, etc.)
- **Dependency Analysis**: Builds a dependency graph to understand function relationships
- **Module Restructuring**: Generates a new, more maintainable module structure
- **Detailed Reporting**: Provides reports on duplicates and code organization

## Installation

The module disassembler is included in the Codegen repository. To use it, you need to have Codegen installed:

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/Zeeeepa/codegen.git
cd codegen

# Install Codegen in development mode
pip install -e .
```

## Usage

### Basic Usage

```bash
python module_disassembler.py --repo-path "/path/to/repo" --output-dir "/path/to/output"
```

### Example Script

For more flexibility, use the example script:

```bash
python example_usage.py --repo-path "/path/to/repo" --focus-dir "codegen-on-oss" --output-dir "./restructured_modules"
```

### Command Line Arguments

- `--repo-path`: Path to the repository to analyze
- `--output-dir`: Directory to output the restructured modules
- `--report-file`: Path to the output report file (default: disassembler_report.json)
- `--similarity-threshold`: Threshold for considering functions similar (0.0-1.0) (default: 0.8)
- `--focus-dir`: Focus on a specific directory (e.g., 'codegen-on-oss')

## How It Works

1. **Codebase Loading**: Uses Codegen SDK to load and parse the codebase
2. **Function Extraction**: Extracts all functions with their source code and metadata
3. **Duplicate Detection**: 
   - Identifies exact duplicates using normalized code hashing
   - Finds similar functions using difflib sequence matching
4. **Dependency Analysis**: Builds a graph of function dependencies using SDK's symbol resolution
5. **Function Categorization**: Categorizes functions based on naming patterns
6. **Module Generation**: Creates a new module structure organized by function category
7. **Report Generation**: Produces a detailed JSON report of the analysis

## Output Structure

The tool generates:

1. **Restructured Modules**: A directory structure organized by function category
   ```
   output_dir/
   ├── __init__.py
   ├── README.md
   ├── analysis/
   │   ├── __init__.py
   │   ├── analyze_code.py
   │   └── ...
   ├── utility/
   │   ├── __init__.py
   │   └── ...
   └── ...
   ```

2. **Analysis Report**: A JSON file with detailed information about:
   - Function counts by category
   - Duplicate function groups
   - Similar function groups
   - Function dependencies

## Function Categories

Functions are categorized based on naming patterns:

- **analysis**: Functions that analyze, extract, parse, process data
- **visualization**: Functions that visualize, plot, render, display information
- **utility**: Helper functions, formatters, converters
- **io**: Functions for reading, writing, loading, saving data
- **validation**: Functions that validate, check, verify data
- **metrics**: Functions that measure, calculate, compute values
- **core**: Core functionality like initialization, main execution
- **other**: Functions that don't fit into the above categories

## Example: Analyzing Codegen-on-OSS

To analyze and restructure the codegen-on-oss module:

```bash
./run_disassembler.sh
```

Or manually:

```bash
python example_usage.py --repo-path "." --focus-dir "codegen-on-oss" --output-dir "./restructured_modules"
```

## Benefits

- **Code Deduplication**: Identify and eliminate duplicate code
- **Better Organization**: Restructure code based on functionality
- **Dependency Insights**: Understand function relationships
- **Refactoring Guidance**: Use the analysis as a guide for refactoring
- **Maintainability**: Improve code maintainability through better organization

