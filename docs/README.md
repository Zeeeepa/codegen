# Codebase Analysis Viewer Documentation

Welcome to the Codebase Analysis Viewer documentation! This documentation provides comprehensive information about the Codebase Analysis Viewer, a powerful tool for analyzing and comparing codebases.

## Overview

The Codebase Analysis Viewer is a comprehensive tool for analyzing and comparing codebases. It provides detailed insights into a codebase's structure, dependencies, code quality, and more. The tool can analyze both local repositories and remote GitHub repositories, and can compare different repositories or different branches of the same repository.

## Features

- **Comprehensive Analysis**: Analyzes multiple aspects of a codebase including structure, dependencies, code quality, and more
- **Comparison Capabilities**: Compares two codebases and identifies differences
- **Multiple Input Sources**: Can analyze repositories from URLs or local paths
- **Flexible Output Formats**: Supports JSON, HTML, and console output formats
- **Customizable Analysis**: Allows selecting specific categories to analyze
- **Language Support**: Works with multiple programming languages
- **Command-Line Interface**: Provides a user-friendly command-line interface
- **Web Interface**: Provides a browser-based graphical interface

## Components

The Codebase Analysis Viewer consists of the following main components:

1. [**Codebase Analyzer**](components/codebase_analyzer.md): Analyzes a single codebase
2. [**Codebase Comparator**](components/codebase_comparator.md): Compares two codebases
3. [**Analysis Viewer CLI**](components/analysis_viewer_cli.md): Command-line interface
4. [**Analysis Viewer Web Interface**](components/analysis_viewer_web.md): Browser-based interface

## Usage Examples

- [**Analyzing a Codebase**](examples/analyzing_a_codebase.md): Examples of analyzing a codebase
- [**Comparing Codebases**](examples/comparing_codebases.md): Examples of comparing codebases

## Tutorials

- [**Analyzing Different Types of Codebases**](tutorials/analyzing_different_codebases.md): Tutorial on analyzing different types of codebases
- [**Comparing Codebases**](tutorials/comparing_codebases.md): Tutorial on comparing codebases

## Reference

- [**Analysis Categories and Metrics**](analysis_categories_and_metrics.md): Detailed information about analysis categories and metrics
- [**Comparison Report Examples**](comparison_report_examples.md): Examples of comparison reports

## Installation

```bash
# Install from PyPI
pip install codegen-on-oss

# Install from source
git clone https://github.com/username/codegen-on-oss.git
cd codegen-on-oss
pip install -e .
```

## Quick Start

### Analyzing a Codebase

```bash
# Analyze a repository by URL
codegen-on-oss analyze --repo-url https://github.com/username/repo

# Analyze a local repository
codegen-on-oss analyze --repo-path /path/to/local/repo
```

### Comparing Codebases

```bash
# Compare two repositories by URL
codegen-on-oss compare --base-repo-url https://github.com/username/repo1 --compare-repo-url https://github.com/username/repo2

# Compare two branches of the same repository
codegen-on-oss compare --base-repo-url https://github.com/username/repo --base-branch main --compare-branch feature-branch
```

### Using the Web Interface

```bash
# Launch the web interface
codegen-on-oss web
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

