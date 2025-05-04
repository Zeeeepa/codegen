# Scripts for Codebase Analysis

This directory contains scripts for analyzing codebases and repositories. These scripts provide comprehensive analysis capabilities for code validation, repository comparison, PR analysis, error detection, and more.

## Scripts

### analyze_code_integrity.py

Analyzes code integrity in a repository, including:
- Finding all functions and classes
- Identifying errors in functions and classes
- Detecting improper parameter usage
- Finding incorrect function callback points
- Comparing error counts between branches
- Analyzing code complexity and duplication
- Checking for type hint usage
- Detecting unused imports

```bash
python -m codegen_on_oss.scripts.analyze_code_integrity --repo /path/to/repo --output results.json
```

### compare_pr_codebase.py

Compares a PR version of a codebase with its base branch, including:
- File changes analysis
- Function changes analysis
- Complexity changes analysis
- Risk assessment
- Code quality comparison
- Error detection and reporting

```bash
python -m codegen_on_oss.scripts.compare_pr_codebase https://github.com/example/repo.git 123 --output pr_comparison.json
```

### error_analyzer.py

Analyzes and reports errors in a codebase, including:
- Syntax errors
- Import errors
- Type errors
- Unused imports
- Undefined variables
- Code style issues
- Security vulnerabilities

```bash
python -m codegen_on_oss.scripts.error_analyzer /path/to/repo --output errors.json
```

### codebase_analyzer.py

Analyzes a codebase for structure, dependencies, complexity, and more, including:
- Code structure analysis
- Dependency analysis
- Complexity analysis
- Code quality metrics
- Error detection
- Documentation coverage

```bash
python -m codegen_on_oss.scripts.codebase_analyzer /path/to/repo --output codebase_analysis.json
```

## Common Features

All scripts share the following features:
- Output in JSON or Markdown format
- Detailed error reporting
- Comprehensive analysis results
- Command-line interface with help documentation

## Getting Started

1. Install the package:

```bash
pip install -e .
```

2. Run the desired script:

```bash
python -m codegen_on_oss.scripts.<script_name> --help
```

## Examples

### Analyzing Code Integrity

```bash
python -m codegen_on_oss.scripts.analyze_code_integrity --repo /path/to/repo --mode analyze --output results.json --html report.html
```

### Comparing PR Codebase

```bash
python -m codegen_on_oss.scripts.compare_pr_codebase https://github.com/example/repo.git 123 --github-token <token> --output pr_comparison.json --format markdown
```

### Analyzing Errors

```bash
python -m codegen_on_oss.scripts.error_analyzer /path/to/repo --output errors.json --format markdown --verbose
```

### Analyzing Codebase

```bash
python -m codegen_on_oss.scripts.codebase_analyzer /path/to/repo --output codebase_analysis.json --format markdown --verbose
```

## Integration with WSL2 Server

These scripts can be used in conjunction with the WSL2 server for more advanced analysis capabilities. See the [WSL2 Server README](../analysis/WSL_README.md) for more details.

