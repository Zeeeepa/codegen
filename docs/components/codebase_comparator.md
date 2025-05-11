# Codebase Comparator

The Codebase Comparator is a powerful tool for comparing two codebases and identifying differences between them. It can compare different repositories or different branches of the same repository.

## Overview

The `CodebaseComparator` class uses the Codegen SDK to analyze and compare two codebases, providing detailed insights into their differences in structure, dependencies, code quality, and other metrics.

## Features

- **Comprehensive Comparison**: Compares multiple aspects of codebases including structure, dependencies, code quality, and more
- **Multiple Input Sources**: Can compare repositories from URLs or local paths
- **Flexible Output Formats**: Supports JSON, HTML, and console output formats
- **Customizable Comparison**: Allows selecting specific categories to compare
- **Branch Comparison**: Can compare different branches of the same repository
- **Visual Diff Reports**: Generates visual reports highlighting differences

## Comparison Categories

The Codebase Comparator supports the following comparison categories:

1. **Codebase Structure Differences**
   - File count changes
   - Directory structure changes
   - Symbol count differences
   - Import dependency changes
   - Module coupling and cohesion differences
   - Package structure changes

2. **Symbol Level Differences**
   - Function parameter changes
   - Return type changes
   - Function complexity changes
   - Inheritance hierarchy changes
   - Method and attribute changes
   - Type usage changes

3. **Dependency Flow Changes**
   - Function call relationship differences
   - Call hierarchy changes
   - Entry point changes
   - Dead code changes
   - Variable usage changes
   - Data transformation path changes

4. **Code Quality Differences**
   - Changes in unused code
   - Changes in code patterns
   - Refactoring opportunity changes
   - Complexity metric changes
   - Naming convention changes
   - Documentation coverage changes

5. **Visualization of Differences**
   - Module dependency change visualization
   - Symbol dependency change visualization
   - Import relationship change graphs
   - Function call change visualization
   - Class hierarchy change visualization
   - Code complexity change heat maps

6. **Language Specific Differences**
   - Decorator usage changes
   - Type hint coverage changes
   - Magic method usage changes
   - Interface implementation changes
   - Type definition changes

7. **Code Metric Changes**
   - Commit frequency changes
   - Complexity metric changes
   - Maintainability index changes
   - Line count changes

## API Reference

### Constructor

```python
CodebaseComparator(base_repo_url=None, base_repo_path=None, 
                  compare_repo_url=None, compare_repo_path=None,
                  base_branch=None, compare_branch=None,
                  language=None)
```

- `base_repo_url` (str, optional): URL of the base repository to compare
- `base_repo_path` (str, optional): Local path to the base repository to compare
- `compare_repo_url` (str, optional): URL of the comparison repository
- `compare_repo_path` (str, optional): Local path to the comparison repository
- `base_branch` (str, optional): Branch name for the base repository (if comparing branches)
- `compare_branch` (str, optional): Branch name for the comparison repository (if comparing branches)
- `language` (str, optional): Programming language of the codebases (auto-detected if not provided)

### Methods

#### compare

```python
compare(categories=None, output_format="json", output_file=None)
```

Perform a comprehensive comparison of the codebases.

- `categories` (List[str], optional): List of categories to compare. If None, all categories are compared.
- `output_format` (str, optional): Format of the output (json, html, console)
- `output_file` (str, optional): Path to the output file

Returns:
- Dict containing the comparison results

#### Category-specific Methods

The `CodebaseComparator` class provides numerous methods for specific comparison tasks, including:

- `compare_file_counts()`: Compare the total number of files in the codebases
- `compare_files_by_language()`: Compare the distribution of files by programming language
- `compare_symbol_counts()`: Compare the total number of symbols in the codebases
- `compare_unused_functions()`: Compare unused functions in the codebases
- `compare_cyclomatic_complexity()`: Compare cyclomatic complexity for functions
- `compare_function_call_relationships()`: Compare function call relationships
- ... and many more

## Usage Examples

### Basic Usage

```python
from codebase_comparator import CodebaseComparator

# Compare two repositories from URLs
comparator = CodebaseComparator(
    base_repo_url="https://github.com/username/repo1",
    compare_repo_url="https://github.com/username/repo2"
)
results = comparator.compare()

# Compare two local repositories
comparator = CodebaseComparator(
    base_repo_path="/path/to/repo1",
    compare_repo_path="/path/to/repo2"
)
results = comparator.compare()

# Compare two branches of the same repository
comparator = CodebaseComparator(
    base_repo_url="https://github.com/username/repo",
    base_branch="main",
    compare_branch="feature-branch"
)
results = comparator.compare()

# Compare specific categories
comparator = CodebaseComparator(
    base_repo_url="https://github.com/username/repo1",
    compare_repo_url="https://github.com/username/repo2"
)
results = comparator.compare(categories=["codebase_structure", "code_quality"])

# Output to HTML file
comparator = CodebaseComparator(
    base_repo_url="https://github.com/username/repo1",
    compare_repo_url="https://github.com/username/repo2"
)
results = comparator.compare(output_format="html", output_file="comparison.html")
```

### Command-line Usage

```bash
# Compare two repositories from URLs
python codebase_comparator.py --base-repo-url https://github.com/username/repo1 --compare-repo-url https://github.com/username/repo2

# Compare two local repositories
python codebase_comparator.py --base-repo-path /path/to/repo1 --compare-repo-path /path/to/repo2

# Compare two branches of the same repository
python codebase_comparator.py --base-repo-url https://github.com/username/repo --base-branch main --compare-branch feature-branch

# Compare specific categories
python codebase_comparator.py --base-repo-url https://github.com/username/repo1 --compare-repo-url https://github.com/username/repo2 --categories codebase_structure code_quality

# Output to JSON file
python codebase_comparator.py --base-repo-url https://github.com/username/repo1 --compare-repo-url https://github.com/username/repo2 --output-format json --output-file comparison.json

# Output to HTML file
python codebase_comparator.py --base-repo-url https://github.com/username/repo1 --compare-repo-url https://github.com/username/repo2 --output-format html --output-file comparison.html
```

## Interpreting Comparison Results

The comparison results are organized by category, with each category containing multiple metrics showing differences between the two codebases. Here's how to interpret some of the key comparison metrics:

### Codebase Structure Differences

- **File Count Changes**: Difference in the total number of files
- **Files by Language Changes**: Changes in the distribution of files by programming language
- **Symbol Count Changes**: Difference in the total number of symbols
- **Import Dependency Changes**: Changes in import dependencies between modules

### Code Quality Differences

- **Unused Functions Changes**: Changes in functions that are defined but never called
- **Cyclomatic Complexity Changes**: Changes in code complexity based on control flow
- **Cognitive Complexity Changes**: Changes in code complexity based on readability
- **Nesting Depth Changes**: Changes in maximum nesting depth of control structures

### Dependency Flow Changes

- **Function Call Relationship Changes**: Changes in function calls between functions
- **Entry Point Changes**: Changes in entry points to the codebase
- **Dead Code Changes**: Changes in code that can never be executed

## Troubleshooting

### Common Issues

1. **Repository Not Found**
   - Ensure the repository URLs are correct
   - Check that you have access to the repositories

2. **Branch Not Found**
   - Ensure the branch names are correct
   - Check that the branches exist in the repository

3. **Language Detection Issues**
   - Specify the language explicitly using the `--language` parameter

4. **Memory Issues**
   - For large codebases, increase available memory
   - Compare specific categories instead of all categories

5. **Slow Comparison**
   - For large codebases, comparison can take time
   - Consider comparing specific categories instead of all categories

### Error Messages

- **"Error initializing codebase from URL"**: Check the repository URL and your internet connection
- **"Error initializing codebase from path"**: Ensure the local path exists and is a valid repository
- **"Branch not found"**: Ensure the branch name is correct and exists in the repository
- **"Codebases not initialized"**: Initialize the codebases before calling compare()

