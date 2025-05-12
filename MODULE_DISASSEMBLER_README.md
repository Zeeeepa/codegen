# Module Disassembler for Codegen

This tool analyzes, restructures, and deduplicates code in the Codegen codebase, particularly focusing on analysis modules. It extracts functions, identifies duplicates, and reorganizes code based on functionality.

## Features

- **Function Extraction**: Extracts all functions from Python files in the codebase
- **Duplicate Detection**: Identifies exact duplicates and similar functions
- **Functional Categorization**: Categorizes functions by their purpose (analysis, visualization, utility, etc.)
- **Dependency Analysis**: Builds a dependency graph to understand function relationships
- **Code Restructuring**: Generates a new, more maintainable module structure
- **Detailed Reporting**: Provides comprehensive reports on duplicates and code organization

## Installation

No additional installation is required beyond the standard Codegen dependencies. The tool is designed to work with the existing codebase.

## Usage

```bash
python module_disassembler.py --repo-path /path/to/codegen --output-dir /path/to/output
```

### Arguments

- `--repo-path`: Path to the repository to analyze (required)
- `--output-dir`: Directory to output the restructured modules (required)
- `--report-file`: Path to the output report file (default: `disassembler_report.json`)
- `--similarity-threshold`: Threshold for considering functions similar (0.0-1.0, default: 0.8)

## Output Structure

The tool generates a restructured module hierarchy organized by function category:

```
output_dir/
├── __init__.py
├── README.md
├── analysis/
│   ├── __init__.py
│   ├── analyze_codebase.py
│   ├── extract_functions.py
│   └── ...
├── visualization/
│   ├── __init__.py
│   ├── plot_dependency_graph.py
│   └── ...
├── utility/
│   ├── __init__.py
│   ├── format_output.py
│   └── ...
└── ...
```

Each function is placed in its own file, with proper imports for dependencies. Duplicate functions are eliminated, with references pointing to the primary implementation.

## Function Categories

Functions are categorized based on naming patterns:

- **analysis**: Functions that analyze, extract, parse, or process data
- **visualization**: Functions that visualize, plot, or display information
- **utility**: Helper functions, formatters, converters
- **io**: Functions for reading, writing, loading, or saving data
- **validation**: Functions that validate, check, or verify data
- **metrics**: Functions that calculate, measure, or compute metrics
- **core**: Core functionality like initialization, main execution, etc.
- **other**: Functions that don't fit into the above categories

## Report Format

The tool generates a JSON report with the following structure:

```json
{
  "summary": {
    "total_functions": 150,
    "duplicate_groups": 5,
    "similar_groups": 8,
    "categories": {
      "analysis": 45,
      "visualization": 20,
      "utility": 30,
      "io": 15,
      "validation": 10,
      "metrics": 25,
      "core": 5
    }
  },
  "duplicates": [...],
  "similar": [...],
  "categories": {...}
}
```

## Example

```bash
# Analyze the codegen repository and output restructured modules
python module_disassembler.py --repo-path ./codegen --output-dir ./restructured_modules

# Analyze with a higher similarity threshold
python module_disassembler.py --repo-path ./codegen --output-dir ./restructured_modules --similarity-threshold 0.9
```

## Use Cases

1. **Code Cleanup**: Identify and eliminate duplicate code
2. **Refactoring**: Restructure code into a more maintainable organization
3. **Code Understanding**: Gain insights into the codebase structure and dependencies
4. **Technical Debt Reduction**: Identify areas for improvement and consolidation

## Limitations

- The tool currently only analyzes Python files
- Function similarity detection may produce false positives with very generic functions
- Dependency analysis is based on static analysis and may miss dynamic dependencies

