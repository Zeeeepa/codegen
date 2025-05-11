# Example: Analyzing a Codebase

This example demonstrates how to analyze a codebase using the Codebase Analysis Viewer.

## Using the CLI

### Basic Analysis

To perform a basic analysis of a codebase, use the `analyze` command:

```bash
# Analyze a repository by URL
codegen-on-oss analyze --repo-url https://github.com/username/repo

# Analyze a local repository
codegen-on-oss analyze --repo-path /path/to/local/repo
```

### Customizing the Analysis

You can customize the analysis by specifying categories, language, output format, and more:

```bash
# Analyze specific categories
codegen-on-oss analyze --repo-url https://github.com/username/repo --categories codebase_structure code_quality

# Analyze with a specific language filter
codegen-on-oss analyze --repo-url https://github.com/username/repo --language python

# Output to JSON file
codegen-on-oss analyze --repo-url https://github.com/username/repo --output-format json --output-file analysis.json

# Output to HTML file
codegen-on-oss analyze --repo-url https://github.com/username/repo --output-format html --output-file report.html
```

## Using the Python API

### Basic Analysis

To perform a basic analysis of a codebase using the Python API:

```python
from codebase_analyzer import CodebaseAnalyzer

# Analyze a repository from URL
analyzer = CodebaseAnalyzer(repo_url="https://github.com/username/repo")
results = analyzer.analyze()

# Analyze a local repository
analyzer = CodebaseAnalyzer(repo_path="/path/to/local/repo")
results = analyzer.analyze()
```

### Customizing the Analysis

You can customize the analysis by specifying categories, output format, and more:

```python
from codebase_analyzer import CodebaseAnalyzer

# Analyze specific categories
analyzer = CodebaseAnalyzer(repo_url="https://github.com/username/repo")
results = analyzer.analyze(categories=["codebase_structure", "code_quality"])

# Output to HTML file
analyzer = CodebaseAnalyzer(repo_url="https://github.com/username/repo")
results = analyzer.analyze(output_format="html", output_file="report.html")

# Output to JSON file
analyzer = CodebaseAnalyzer(repo_url="https://github.com/username/repo")
results = analyzer.analyze(output_format="json", output_file="analysis.json")
```

### Accessing Specific Metrics

You can access specific metrics directly:

```python
from codebase_analyzer import CodebaseAnalyzer

analyzer = CodebaseAnalyzer(repo_url="https://github.com/username/repo")

# Get file count
file_count = analyzer.get_file_count()
print(f"Total files: {file_count}")

# Get files by language
files_by_language = analyzer.get_files_by_language()
print("Files by language:")
for language, count in files_by_language.items():
    print(f"  {language}: {count}")

# Get cyclomatic complexity
complexity = analyzer.get_cyclomatic_complexity()
print(f"Average cyclomatic complexity: {complexity['avg_complexity']}")
print(f"Max cyclomatic complexity: {complexity['max_complexity']}")
```

## Using the Web Interface

### Basic Analysis

To analyze a codebase using the web interface:

1. Launch the web interface:
   ```bash
   codegen-on-oss web
   ```

2. In your browser, navigate to the URL shown in the terminal (usually http://127.0.0.1:7860)

3. In the Repository Selection panel, enter the URL or path of the repository to analyze

4. Click the "Analyze" button

5. View the results in the Results Dashboard and Visualization Panel

### Customizing the Analysis

You can customize the analysis in the web interface:

1. In the Analysis Options panel, select the categories to analyze

2. Specify the language filter if needed

3. Set the depth of analysis (1-3)

4. Click the "Analyze" button

5. View the customized results in the Results Dashboard and Visualization Panel

## Example Analysis Results

Here's an example of what the analysis results might look like:

```json
{
  "metadata": {
    "repo_name": "username/repo",
    "analysis_time": "2025-05-10T23:59:23",
    "language": "python"
  },
  "categories": {
    "codebase_structure": {
      "file_count": 42,
      "files_by_language": {
        "python": 35,
        "markdown": 5,
        "yaml": 2
      },
      "symbol_count": 156,
      "symbol_type_distribution": {
        "function": 87,
        "class": 23,
        "method": 46
      }
    },
    "code_quality": {
      "unused_functions": [
        {
          "name": "deprecated_function",
          "file": "src/utils.py"
        }
      ],
      "cyclomatic_complexity": {
        "avg_complexity": 3.2,
        "max_complexity": 12,
        "complex_functions": [
          {
            "name": "process_data",
            "file": "src/processor.py",
            "complexity": 12
          }
        ]
      }
    }
  }
}
```

## Interpreting the Results

### Codebase Structure

- **File Count**: The total number of files in the codebase (42 in the example)
- **Files by Language**: The distribution of files by programming language (35 Python, 5 Markdown, 2 YAML in the example)
- **Symbol Count**: The total number of symbols (functions, classes, etc.) in the codebase (156 in the example)
- **Symbol Type Distribution**: The distribution of symbols by type (87 functions, 23 classes, 46 methods in the example)

### Code Quality

- **Unused Functions**: Functions that are defined but never called (1 in the example)
- **Cyclomatic Complexity**: Measure of code complexity based on control flow
  - **Average Complexity**: The average cyclomatic complexity of all functions (3.2 in the example)
  - **Max Complexity**: The maximum cyclomatic complexity of any function (12 in the example)
  - **Complex Functions**: Functions with high cyclomatic complexity (1 in the example)

