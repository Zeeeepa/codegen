# Codebase Analysis Viewer CLI

The Codebase Analysis Viewer CLI provides a comprehensive command-line interface for analyzing and comparing codebases. This tool allows you to perform static analysis on a single codebase, compare two codebases, and view the results in various formats.

## Installation

The Codebase Analysis Viewer CLI is part of the codegen-on-oss project. To install it, follow these steps:

```bash
# Clone the repository
git clone https://github.com/codegen-sh/codegen-on-oss.git
cd codegen-on-oss

# Install the package
pip install -e .
```

## Usage

The CLI provides several commands for analyzing and comparing codebases:

### Analyze a Single Codebase

```bash
# Basic usage
cgparse analyze https://github.com/username/repo

# Specify language
cgparse analyze https://github.com/username/repo --language python

# Specify categories to analyze
cgparse analyze https://github.com/username/repo --categories codebase_structure,code_quality

# Specify output format and file
cgparse analyze https://github.com/username/repo --output-format json --output-file analysis.json

# Analyze a local repository
cgparse analyze /path/to/local/repo
```

### Compare Two Codebases

```bash
# Basic usage
cgparse compare https://github.com/username/repo1 https://github.com/username/repo2

# Specify languages
cgparse compare https://github.com/username/repo1 https://github.com/username/repo2 --language1 python --language2 javascript

# Specify categories to analyze
cgparse compare https://github.com/username/repo1 https://github.com/username/repo2 --categories codebase_structure,code_quality

# Specify output format and file
cgparse compare https://github.com/username/repo1 https://github.com/username/repo2 --output-format html --output-file comparison.html

# Compare a local repository with a remote repository
cgparse compare /path/to/local/repo https://github.com/username/repo2
```

### Interactive Mode

The interactive mode provides a guided interface for analyzing and comparing codebases:

```bash
cgparse interactive
```

This mode allows you to:
- Analyze a single codebase
- Compare two codebases
- View available analysis categories
- Configure output formats and files

### List Available Categories

To see all available analysis categories:

```bash
cgparse list-categories
```

## Analysis Categories

The Codebase Analysis Viewer supports the following categories:

1. **codebase_structure**: Analyzes the structure of the codebase, including file counts, directory structure, symbol hierarchy, and import dependencies.

2. **symbol_level**: Analyzes symbols in the codebase, including functions, classes, methods, and attributes.

3. **dependency_flow**: Analyzes the flow of dependencies in the codebase, including function call relationships, entry points, and data transformation paths.

4. **code_quality**: Analyzes the quality of the code, including unused code, complexity metrics, and naming conventions.

5. **visualization**: Provides visualizations of the codebase, including dependency graphs, call hierarchies, and complexity heat maps.

6. **language_specific**: Provides language-specific analyses, including decorator usage, type hints, and interface implementations.

7. **code_metrics**: Provides various code metrics, including cyclomatic complexity, Halstead volume, and maintainability index.

## Output Formats

The Codebase Analysis Viewer supports the following output formats:

1. **console**: Displays the results in the console with rich formatting.

2. **json**: Saves the results to a JSON file.

3. **html**: Generates an HTML report with the results.

## Examples

### Analyze a Repository and Generate an HTML Report

```bash
cgparse analyze https://github.com/username/repo --output-format html --output-file report.html
```

### Compare Two Repositories and View the Results in the Console

```bash
cgparse compare https://github.com/username/repo1 https://github.com/username/repo2 --output-format console
```

### Analyze Specific Categories of a Repository

```bash
cgparse analyze https://github.com/username/repo --categories codebase_structure,code_quality --output-format json --output-file analysis.json
```

### Run in Interactive Mode

```bash
cgparse interactive
```

## Advanced Usage

### Progress Indicators

By default, the CLI shows progress indicators for long-running operations. To disable them:

```bash
cgparse analyze https://github.com/username/repo --no-progress
```

### Custom Output Files

You can specify custom output files for JSON and HTML formats:

```bash
cgparse analyze https://github.com/username/repo --output-format json --output-file custom_analysis.json
cgparse compare https://github.com/username/repo1 https://github.com/username/repo2 --output-format html --output-file custom_comparison.html
```

### Analyzing Local Repositories

You can analyze local repositories by providing the path:

```bash
cgparse analyze /path/to/local/repo
cgparse compare /path/to/local/repo1 /path/to/local/repo2
```

## Troubleshooting

### Common Issues

1. **ImportError: Could not import CodebaseAnalyzer**
   
   Make sure the codebase_analyzer.py file is in your path or in the codegen_on_oss package.

2. **Error initializing codebase from URL**
   
   Check that the repository URL is correct and accessible.

3. **Error during analysis**
   
   Check the error message for details. Common issues include:
   - Invalid repository URL or path
   - Invalid language specification
   - Invalid category specification

### Getting Help

For more information on a specific command, use the `--help` option:

```bash
cgparse analyze --help
cgparse compare --help
cgparse interactive --help
cgparse list-categories --help
```

## Contributing

Contributions to the Codebase Analysis Viewer CLI are welcome! Please see the [contributing guidelines](../CONTRIBUTING.md) for more information.

## License

The Codebase Analysis Viewer CLI is part of the codegen-on-oss project and is licensed under the [MIT License](../LICENSE).

