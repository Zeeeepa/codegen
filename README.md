# Comprehensive Codebase Analyzer

A powerful static code analysis system that provides extensive information about your codebase using the Codegen SDK.

## Features

This analyzer provides comprehensive analysis of your codebase, including:

### 1. Codebase Structure Analysis

- File Statistics (count, language, size)
- Symbol Tree Analysis
- Import/Export Analysis
- Module Organization

### 2. Symbol-Level Analysis

- Function Analysis (parameters, return types, complexity)
- Class Analysis (methods, attributes, inheritance)
- Variable Analysis
- Type Analysis

### 3. Dependency and Flow Analysis

- Call Graph Generation
- Data Flow Analysis
- Control Flow Analysis
- Symbol Usage Analysis

### 4. Code Quality Analysis

- Unused Code Detection
- Code Duplication Analysis
- Complexity Metrics
- Style and Convention Analysis
- Untyped Code Detection (return statements, parameters, attributes)
- Unnamed Keyword Arguments Detection

### 5. Visualization Capabilities

- Dependency Graphs
- Call Graphs
- Symbol Trees
- Heat Maps
- Directory Tree Visualization
- Import Cycle Visualization

### 6. Language-Specific Analysis

- Python-Specific Analysis
- TypeScript-Specific Analysis

### 7. Code Metrics

- Monthly Commits
- Cyclomatic Complexity
- Halstead Volume
- Maintainability Index

### 8. PR and Commit Comparison

- Compare codebases between commits
- Analyze PR changes
- Get PR quality metrics

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/codebase-analyzer.git
cd codebase-analyzer
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Analyzing a Repository

```bash
# Analyze from URL
python codebase_analyzer.py --repo-url https://github.com/username/repo

# Analyze local repository
python codebase_analyzer.py --repo-path /path/to/repo

# Specify language
python codebase_analyzer.py --repo-url https://github.com/username/repo --language python

# Analyze specific categories
python codebase_analyzer.py --repo-url https://github.com/username/repo --categories codebase_structure code_quality
```

### Output Formats

```bash
# Output as JSON
python codebase_analyzer.py --repo-url https://github.com/username/repo --output-format json --output-file analysis.json

# Generate HTML report
python codebase_analyzer.py --repo-url https://github.com/username/repo --output-format html --output-file report.html

# Print to console (default)
python codebase_analyzer.py --repo-url https://github.com/username/repo --output-format console
```

### Visualization

```bash
# Generate call graph visualization
python codebase_analyzer.py --repo-url https://github.com/username/repo --visualize call-graph --function-name main

# Generate dependency map visualization
python codebase_analyzer.py --repo-url https://github.com/username/repo --visualize dependency-map

# Generate directory tree visualization
python codebase_analyzer.py --repo-url https://github.com/username/repo --visualize directory-tree

# Generate import cycles visualization
python codebase_analyzer.py --repo-url https://github.com/username/repo --visualize import-cycles
```

### Type Analysis

```bash
# Analyze untyped code in the codebase
python codebase_analyzer.py --repo-url https://github.com/username/repo --analyze-types
```

### Codebase Summary

```bash
# Get a summary of the codebase
python codebase_analyzer.py --repo-url https://github.com/username/repo --summary
```

### PR and Commit Comparison

```bash
# Compare with a specific commit
python codebase_analyzer.py --repo-url https://github.com/username/repo --compare-commit abc123

# Analyze a PR
python codebase_analyzer.py --repo-url https://github.com/username/repo --pr-number 123
```

## Available Analysis Categories

- `codebase_structure`: File statistics, symbol tree, import/export analysis, module organization
- `symbol_level`: Function, class, variable, and type analysis
- `dependency_flow`: Call graphs, data flow, control flow, symbol usage
- `code_quality`: Unused code, duplication, complexity, style
- `visualization`: Dependency graphs, call graphs, symbol trees, heat maps
- `language_specific`: Language-specific analysis features
- `code_metrics`: Commits, complexity, volume, maintainability
- `import_analysis`: Import cycle detection and visualization
- `pr_comparison`: PR diff analysis and quality metrics

## Requirements

- Python 3.8+
- Codegen SDK
- NetworkX
- Matplotlib
- Rich
- Plotly

## License

MIT
