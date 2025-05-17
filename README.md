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

### 5. Visualization Capabilities

- Dependency Graphs
- Call Graphs
- Symbol Trees
- Heat Maps

### 6. Language-Specific Analysis

- Python-Specific Analysis
- TypeScript-Specific Analysis

### 7. Code Metrics

- Monthly Commits
- Cyclomatic Complexity
- Halstead Volume
- Maintainability Index

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/codebase-analyzer.git
cd codebase-analyzer
```

2. Install dependencies:

```bash
pip install -e ".[dev]"
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

## Available Analysis Categories

- `codebase_structure`: File statistics, symbol tree, import/export analysis, module organization
- `symbol_level`: Function, class, variable, and type analysis
- `dependency_flow`: Call graphs, data flow, control flow, symbol usage
- `code_quality`: Unused code, duplication, complexity, style
- `visualization`: Dependency graphs, call graphs, symbol trees, heat maps
- `language_specific`: Language-specific analysis features
- `code_metrics`: Commits, complexity, volume, maintainability

## Testing

The Codegen SDK has a comprehensive testing infrastructure to ensure code quality and reliability.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
./scripts/run_tests_with_coverage.sh

# Run specific tests
pytest tests/unit/codegen/agents/test_agent.py
```

### Test Coverage

The goal is to maintain high test coverage for critical components of the SDK. The coverage report can be generated using:

```bash
./scripts/run_tests_with_coverage.sh --format html
```

This will generate:
- A text report in the console
- An HTML report in `coverage_html_report/`
- An analysis report in `reports/coverage_analysis.md`

### Finding Flaky Tests

To identify flaky tests that pass inconsistently:

```bash
./scripts/find_flaky_tests.py --test-path tests/unit/ --iterations 5
```

For more information about testing, see the [Testing Guide](docs/testing_guide.md).

## Requirements

- Python 3.12+
- Codegen SDK
- NetworkX
- Matplotlib
- Rich

## License

MIT
