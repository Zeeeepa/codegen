# Example: Comparing Codebases

This example demonstrates how to compare two codebases using the Codebase Analysis Viewer.

## Using the CLI

### Basic Comparison

To perform a basic comparison of two codebases, use the `compare` command:

```bash
# Compare two repositories by URL
codegen-on-oss compare --base-repo-url https://github.com/username/repo1 --compare-repo-url https://github.com/username/repo2

# Compare two local repositories
codegen-on-oss compare --base-repo-path /path/to/repo1 --compare-repo-path /path/to/repo2

# Compare two branches of the same repository
codegen-on-oss compare --base-repo-url https://github.com/username/repo --base-branch main --compare-branch feature-branch
```

### Customizing the Comparison

You can customize the comparison by specifying categories, language, output format, and more:

```bash
# Compare specific categories
codegen-on-oss compare --base-repo-url https://github.com/username/repo1 --compare-repo-url https://github.com/username/repo2 --categories codebase_structure code_quality

# Compare with a specific language filter
codegen-on-oss compare --base-repo-url https://github.com/username/repo1 --compare-repo-url https://github.com/username/repo2 --language python

# Output to JSON file
codegen-on-oss compare --base-repo-url https://github.com/username/repo1 --compare-repo-url https://github.com/username/repo2 --output-format json --output-file comparison.json

# Output to HTML file
codegen-on-oss compare --base-repo-url https://github.com/username/repo1 --compare-repo-url https://github.com/username/repo2 --output-format html --output-file comparison.html
```

## Using the Python API

### Basic Comparison

To perform a basic comparison of two codebases using the Python API:

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
```

### Customizing the Comparison

You can customize the comparison by specifying categories, output format, and more:

```python
from codebase_comparator import CodebaseComparator

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

# Output to JSON file
comparator = CodebaseComparator(
    base_repo_url="https://github.com/username/repo1",
    compare_repo_url="https://github.com/username/repo2"
)
results = comparator.compare(output_format="json", output_file="comparison.json")
```

### Accessing Specific Comparison Metrics

You can access specific comparison metrics directly:

```python
from codebase_comparator import CodebaseComparator

comparator = CodebaseComparator(
    base_repo_url="https://github.com/username/repo1",
    compare_repo_url="https://github.com/username/repo2"
)

# Compare file counts
file_count_diff = comparator.compare_file_counts()
print(f"Base file count: {file_count_diff['base_file_count']}")
print(f"Compare file count: {file_count_diff['compare_file_count']}")
print(f"Difference: {file_count_diff['difference']}")

# Compare files by language
files_by_language_diff = comparator.compare_files_by_language()
print("Files by language differences:")
for language, diff in files_by_language_diff.items():
    print(f"  {language}: {diff['base']} -> {diff['compare']} (Diff: {diff['difference']})")

# Compare cyclomatic complexity
complexity_diff = comparator.compare_cyclomatic_complexity()
print(f"Average complexity difference: {complexity_diff['avg_complexity_diff']}")
print(f"Max complexity difference: {complexity_diff['max_complexity_diff']}")
```

## Using the Web Interface

### Basic Comparison

To compare codebases using the web interface:

1. Launch the web interface:
   ```bash
   codegen-on-oss web
   ```

2. In your browser, navigate to the URL shown in the terminal (usually http://127.0.0.1:7860)

3. In the Repository Selection panel, enter the URLs or paths of the repositories to compare

4. Click the "Compare" button

5. View the comparison results in the Results Dashboard and Visualization Panel

### Customizing the Comparison

You can customize the comparison in the web interface:

1. In the Analysis Options panel, select the categories to compare

2. Specify the language filter if needed

3. Set the depth of comparison (1-3)

4. Click the "Compare" button

5. View the customized comparison results in the Results Dashboard and Visualization Panel

## Example Comparison Results

Here's an example of what the comparison results might look like:

```json
{
  "metadata": {
    "base_repo_name": "username/repo1",
    "compare_repo_name": "username/repo2",
    "comparison_time": "2025-05-10T23:59:23",
    "language": "python"
  },
  "categories": {
    "codebase_structure": {
      "file_count": {
        "base": 42,
        "compare": 45,
        "difference": 3,
        "percent_change": 7.14
      },
      "files_by_language": {
        "python": {
          "base": 35,
          "compare": 37,
          "difference": 2,
          "percent_change": 5.71
        },
        "markdown": {
          "base": 5,
          "compare": 6,
          "difference": 1,
          "percent_change": 20.0
        },
        "yaml": {
          "base": 2,
          "compare": 2,
          "difference": 0,
          "percent_change": 0.0
        }
      },
      "symbol_count": {
        "base": 156,
        "compare": 168,
        "difference": 12,
        "percent_change": 7.69
      }
    },
    "code_quality": {
      "cyclomatic_complexity": {
        "avg_complexity": {
          "base": 3.2,
          "compare": 3.0,
          "difference": -0.2,
          "percent_change": -6.25
        },
        "max_complexity": {
          "base": 12,
          "compare": 10,
          "difference": -2,
          "percent_change": -16.67
        }
      },
      "new_unused_functions": [
        {
          "name": "new_unused_function",
          "file": "src/new_module.py"
        }
      ],
      "removed_unused_functions": [
        {
          "name": "deprecated_function",
          "file": "src/utils.py"
        }
      ]
    }
  }
}
```

## Interpreting the Comparison Results

### Codebase Structure Differences

- **File Count**: The difference in the total number of files between the codebases
  - Base: 42 files
  - Compare: 45 files
  - Difference: 3 files (7.14% increase)

- **Files by Language**: The differences in the distribution of files by programming language
  - Python: 35 -> 37 files (2 files, 5.71% increase)
  - Markdown: 5 -> 6 files (1 file, 20% increase)
  - YAML: 2 -> 2 files (no change)

- **Symbol Count**: The difference in the total number of symbols between the codebases
  - Base: 156 symbols
  - Compare: 168 symbols
  - Difference: 12 symbols (7.69% increase)

### Code Quality Differences

- **Cyclomatic Complexity**: The differences in code complexity between the codebases
  - Average Complexity: 3.2 -> 3.0 (0.2 decrease, 6.25% improvement)
  - Max Complexity: 12 -> 10 (2 decrease, 16.67% improvement)

- **Unused Functions**: The changes in unused functions between the codebases
  - New Unused Functions: 1 new unused function
  - Removed Unused Functions: 1 unused function removed

## Common Comparison Scenarios

### Comparing Different Versions of a Project

Comparing different versions of a project can help you understand how the codebase has evolved over time:

```bash
# Compare two versions of a project
codegen-on-oss compare --base-repo-url https://github.com/username/repo --base-branch v1.0 --compare-branch v2.0
```

### Comparing a Fork with the Original Repository

Comparing a fork with the original repository can help you understand how the fork has diverged:

```bash
# Compare a fork with the original repository
codegen-on-oss compare --base-repo-url https://github.com/original/repo --compare-repo-url https://github.com/fork/repo
```

### Comparing Before and After a Major Refactoring

Comparing before and after a major refactoring can help you assess the impact of the refactoring:

```bash
# Compare before and after a major refactoring
codegen-on-oss compare --base-repo-url https://github.com/username/repo --base-branch before-refactor --compare-branch after-refactor
```

