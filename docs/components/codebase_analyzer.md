# Codebase Analyzer

The Codebase Analyzer is a comprehensive static code analysis tool that provides detailed insights into a codebase's structure, dependencies, code quality, and more.

## Overview

The `CodebaseAnalyzer` class uses the Codegen SDK to analyze a codebase and extract detailed information about its structure, dependencies, code quality, and other metrics. It can analyze both local repositories and remote GitHub repositories.

## Features

- **Comprehensive Analysis**: Analyzes multiple aspects of a codebase including structure, dependencies, code quality, and more
- **Multiple Input Sources**: Can analyze repositories from a URL or local path
- **Flexible Output Formats**: Supports JSON, HTML, and console output formats
- **Customizable Analysis**: Allows selecting specific categories to analyze
- **Language Support**: Works with multiple programming languages

## Analysis Categories

The Codebase Analyzer supports the following analysis categories:

1. **Codebase Structure**
   - File counts and distribution
   - Directory structure
   - Symbol counts and distribution
   - Import dependencies
   - Module coupling and cohesion
   - Package structure

2. **Symbol Level Analysis**
   - Function parameter analysis
   - Return type analysis
   - Function complexity metrics
   - Inheritance hierarchy
   - Method and attribute analysis
   - Type inference and usage

3. **Dependency Flow**
   - Function call relationships
   - Call hierarchy visualization
   - Entry point analysis
   - Dead code detection
   - Variable usage tracking
   - Data transformation paths

4. **Code Quality**
   - Unused functions, classes, and variables
   - Similar function detection
   - Repeated code patterns
   - Refactoring opportunities
   - Cyclomatic and cognitive complexity
   - Naming convention consistency

5. **Visualization**
   - Module dependency visualization
   - Symbol dependency visualization
   - Import relationship graphs
   - Function call visualization
   - Class hierarchy visualization
   - Code complexity heat maps

6. **Language Specific Analysis**
   - Decorator usage analysis
   - Dynamic attribute access detection
   - Type hint coverage
   - Magic method usage
   - Interface implementation verification
   - Type definition completeness

7. **Code Metrics**
   - Monthly commits
   - Cyclomatic complexity
   - Halstead volume
   - Maintainability index
   - Line counts

## API Reference

### Constructor

```python
CodebaseAnalyzer(repo_url=None, repo_path=None, language=None)
```

- `repo_url` (str, optional): URL of the repository to analyze
- `repo_path` (str, optional): Local path to the repository to analyze
- `language` (str, optional): Programming language of the codebase (auto-detected if not provided)

### Methods

#### analyze

```python
analyze(categories=None, output_format="json", output_file=None)
```

Perform a comprehensive analysis of the codebase.

- `categories` (List[str], optional): List of categories to analyze. If None, all categories are analyzed.
- `output_format` (str, optional): Format of the output (json, html, console)
- `output_file` (str, optional): Path to the output file

Returns:
- Dict containing the analysis results

#### Category-specific Methods

The `CodebaseAnalyzer` class provides numerous methods for specific analysis tasks, including:

- `get_file_count()`: Get the total number of files in the codebase
- `get_files_by_language()`: Get the distribution of files by programming language
- `get_symbol_count()`: Get the total number of symbols in the codebase
- `get_unused_functions()`: Identify unused functions in the codebase
- `get_cyclomatic_complexity()`: Calculate cyclomatic complexity for functions
- `get_function_call_relationships()`: Analyze function call relationships
- ... and many more

## Usage Examples

### Basic Usage

```python
from codebase_analyzer import CodebaseAnalyzer

# Analyze a repository from URL
analyzer = CodebaseAnalyzer(repo_url="https://github.com/username/repo")
results = analyzer.analyze()

# Analyze a local repository
analyzer = CodebaseAnalyzer(repo_path="/path/to/local/repo")
results = analyzer.analyze()

# Analyze specific categories
analyzer = CodebaseAnalyzer(repo_url="https://github.com/username/repo")
results = analyzer.analyze(categories=["codebase_structure", "code_quality"])

# Output to HTML file
analyzer = CodebaseAnalyzer(repo_url="https://github.com/username/repo")
results = analyzer.analyze(output_format="html", output_file="report.html")
```

### Command-line Usage

```bash
# Analyze a repository from URL
python codebase_analyzer.py --repo-url https://github.com/username/repo

# Analyze a local repository
python codebase_analyzer.py --repo-path /path/to/repo

# Analyze with specific language
python codebase_analyzer.py --repo-url https://github.com/username/repo --language python

# Analyze specific categories
python codebase_analyzer.py --repo-url https://github.com/username/repo --categories codebase_structure code_quality

# Output to JSON file
python codebase_analyzer.py --repo-url https://github.com/username/repo --output-format json --output-file analysis.json

# Output to HTML file
python codebase_analyzer.py --repo-url https://github.com/username/repo --output-format html --output-file report.html

# Output to console
python codebase_analyzer.py --repo-url https://github.com/username/repo --output-format console
```

## Interpreting Results

The analysis results are organized by category, with each category containing multiple metrics. Here's how to interpret some of the key metrics:

### Codebase Structure

- **File Count**: Total number of files in the codebase
- **Files by Language**: Distribution of files by programming language
- **Symbol Count**: Total number of symbols (functions, classes, etc.) in the codebase
- **Import Dependency Map**: Map of import dependencies between modules

### Code Quality

- **Unused Functions**: Functions that are defined but never called
- **Cyclomatic Complexity**: Measure of code complexity based on control flow
- **Cognitive Complexity**: Measure of code complexity based on readability
- **Nesting Depth**: Maximum nesting depth of control structures

### Dependency Flow

- **Function Call Relationships**: Map of function calls between functions
- **Entry Point Analysis**: Identification of entry points to the codebase
- **Dead Code Detection**: Code that can never be executed

## Troubleshooting

### Common Issues

1. **Repository Not Found**
   - Ensure the repository URL is correct
   - Check that you have access to the repository

2. **Language Detection Issues**
   - Specify the language explicitly using the `--language` parameter

3. **Memory Issues**
   - For large codebases, increase available memory
   - Analyze specific categories instead of all categories

4. **Slow Analysis**
   - For large codebases, analysis can take time
   - Consider analyzing specific categories instead of all categories

### Error Messages

- **"Error initializing codebase from URL"**: Check the repository URL and your internet connection
- **"Error initializing codebase from path"**: Ensure the local path exists and is a valid repository
- **"Codebase not initialized"**: Initialize the codebase before calling analyze()

