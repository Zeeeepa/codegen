# Code Integrity Analyzer

The Code Integrity Analyzer is a comprehensive tool for analyzing code quality and detecting potential issues in your codebase. It provides detailed insights into code structure, identifies errors, and helps maintain high code quality standards.

## Features

- **Comprehensive Code Analysis**
  - Analyzes all functions and classes in the codebase
  - Identifies error functions with exact error details
  - Detects implementation points that are not properly used

- **Specific Error Detection**
  - Wrong parameter usage detection
  - Incorrect function callback points
  - Missing docstrings
  - Empty functions/classes
  - Unused parameters
  - Too many parameters/return statements
  - And more...

- **Branch Comparison**
  - Compares error counts between branches
  - Identifies new errors introduced in PR branches
  - Shows fixed errors in PR branches

- **HTML Report Generation**
  - Generates detailed HTML reports with error listings
  - Provides tabbed interface for easy navigation
  - Includes codebase summaries

## Installation

### Prerequisites

- Python 3.8 or higher
- Codegen SDK

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/Zeeeepa/codegen.git
   cd codegen
   ```

2. Install the package:
   ```bash
   pip install -e .
   ```

## Usage

### Python API

#### Basic Usage

```python
from codegen import Codebase
from codegen_on_oss.analysis import CodeAnalyzer

# Create a codebase
codebase = Codebase.from_repo("/path/to/repo")

# Create an analyzer
analyzer = CodeAnalyzer(codebase)

# Analyze code integrity
results = analyzer.analyze_code_integrity()

# Print summary
print(f"Total Functions: {results['total_functions']}")
print(f"Total Classes: {results['total_classes']}")
print(f"Total Errors: {results['total_errors']}")
```

#### Direct Usage of CodeIntegrityAnalyzer

```python
from codegen import Codebase
from codegen_on_oss.analysis import CodeIntegrityAnalyzer

# Create a codebase
codebase = Codebase.from_repo("/path/to/repo")

# Create an analyzer with custom configuration
config = {
    "max_function_parameters": 10,
    "max_function_returns": 8,
    "max_class_methods": 25,
    "max_class_attributes": 20,
    "require_docstrings": True,
    "require_type_hints": True,
    "ignore_patterns": [r"__pycache__", r"\.git", r"\.venv", r"\.env", r"tests/"]
}

analyzer = CodeIntegrityAnalyzer(codebase, config)

# Analyze code integrity
results = analyzer.analyze()

# Process results
for error in results["errors"]:
    print(f"{error['type']}: {error['message']} in {error['filepath']} at line {error['line']}")
```

### Command Line Interface

The package includes a command-line script for analyzing code integrity:

```bash
# Basic analysis
python -m codegen_on_oss.scripts.analyze_code_integrity_example --repo /path/to/repo --output results.json --html report.html

# Analysis with custom configuration
python -m codegen_on_oss.scripts.analyze_code_integrity_example --repo /path/to/repo --config config.json --output results.json --html report.html

# Branch comparison
python -m codegen_on_oss.scripts.analyze_code_integrity_example --repo /path/to/repo --mode compare --main-branch main --feature-branch feature --output comparison.json --html report.html

# PR analysis
python -m codegen_on_oss.scripts.analyze_code_integrity_example --repo /path/to/repo --mode pr --main-branch main --feature-branch pr-branch --output pr_analysis.json --html report.html
```

### Configuration

You can customize the analyzer behavior using a configuration file (JSON or YAML):

```json
{
  "max_function_parameters": 7,
  "max_function_returns": 5,
  "max_class_methods": 20,
  "max_class_attributes": 15,
  "max_function_complexity": 15,
  "max_line_length": 100,
  "require_docstrings": true,
  "require_type_hints": false,
  "ignore_patterns": ["__pycache__", "\\.git", "\\.venv", "\\.env"],
  "severity_levels": {
    "missing_docstring": "warning",
    "empty_function": "error",
    "unused_parameter": "warning",
    "too_many_parameters": "warning",
    "too_many_returns": "warning",
    "empty_class": "error",
    "too_many_methods": "warning",
    "too_many_attributes": "warning",
    "missing_init": "warning",
    "wrong_parameter_type": "error",
    "wrong_callback_signature": "error",
    "high_complexity": "warning",
    "long_line": "warning",
    "missing_type_hints": "warning",
    "inconsistent_return_type": "error",
    "mutable_default_argument": "warning",
    "unused_import": "warning",
    "duplicate_code": "warning"
  }
}
```

## Integration with CI/CD

### GitHub Actions

```yaml
name: Code Integrity Check

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
      with:
        fetch-depth: 0
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .
    
    - name: Analyze code integrity
      run: |
        python -m codegen_on_oss.scripts.analyze_code_integrity_example --repo . --output results.json --html report.html
    
    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: code-integrity-report
        path: |
          results.json
          report.html
```

### GitLab CI

```yaml
code_integrity:
  stage: test
  image: python:3.10
  script:
    - pip install -e .
    - python -m codegen_on_oss.scripts.analyze_code_integrity_example --repo . --output results.json --html report.html
  artifacts:
    paths:
      - results.json
      - report.html
```

## Docker Deployment

You can also run the analyzer in a Docker container:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install git
RUN apt-get update && apt-get install -y git

# Copy the application
COPY . /app/

# Install dependencies
RUN pip install -e .

# Set the entrypoint
ENTRYPOINT ["python", "-m", "codegen_on_oss.scripts.analyze_code_integrity_example"]

# Default command
CMD ["--help"]
```

Build and run the Docker container:

```bash
# Build the image
docker build -t code-integrity-analyzer .

# Run the analyzer
docker run -v /path/to/repo:/repo code-integrity-analyzer --repo /repo --output /repo/results.json --html /repo/report.html
```

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'codegen'**
   - Make sure you have installed the Codegen SDK
   - Check your Python path

2. **FileNotFoundError: Repository not found**
   - Verify the repository path exists
   - Ensure you have read permissions for the repository

3. **MemoryError during analysis**
   - For large codebases, increase available memory
   - Consider analyzing specific directories instead of the entire repository

### Getting Help

If you encounter any issues or have questions, please:
1. Check the documentation
2. Look for similar issues in the issue tracker
3. Open a new issue with detailed information about your problem

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

