# Codegen-on-OSS Repository Analysis Example

This example demonstrates how to use the `codegen-on-oss` component to analyze a repository and generate insights about its structure, dependencies, and code quality.

## Overview

The example shows how to:

1. Parse a repository using the `codegen-on-oss` API
2. Analyze the codebase structure and dependencies
3. Perform code integrity checks
4. Generate a comprehensive report

## Usage

```python
# Basic usage
python run.py --repo https://github.com/organization/repo-name

# With code integrity analysis
python run.py --repo https://github.com/organization/repo-name --integrity

# Save results to a specific file
python run.py --repo https://github.com/organization/repo-name --output results.json
```

## Example Output

The analysis generates a JSON report with the following structure:

```json
{
  "repository": {
    "url": "https://github.com/organization/repo-name",
    "commit": "abc123...",
    "branch": "main"
  },
  "structure": {
    "file_count": 120,
    "directory_count": 25,
    "language_breakdown": {
      "Python": 65,
      "JavaScript": 40,
      "TypeScript": 10,
      "Other": 5
    }
  },
  "dependencies": {
    "internal": [
      {"from": "module_a", "to": "module_b", "type": "import"},
      {"from": "module_b", "to": "module_c", "type": "import"}
    ],
    "external": [
      {"name": "requests", "version": "2.28.1"},
      {"name": "numpy", "version": "1.23.0"}
    ]
  },
  "integrity": {
    "issues": [
      {
        "file": "src/module.py",
        "line": 42,
        "severity": "warning",
        "message": "Function lacks proper error handling"
      }
    ],
    "summary": {
      "error_count": 0,
      "warning_count": 5,
      "info_count": 12
    }
  }
}
```

## How It Works

The example uses the `CodegenOnOSS` class from the `codegen-on-oss` component to:

1. Clone and parse the repository
2. Extract structural information
3. Analyze dependencies between modules
4. Check for code quality issues
5. Generate a comprehensive report

The analysis is performed using a combination of static analysis techniques and pattern matching to identify potential issues and extract meaningful insights from the codebase.

## Integration with Other Tools

The output from this example can be used with other tools in the Codegen ecosystem:

- Use with code transformation examples to target specific issues
- Feed into documentation generators
- Use as input for visualization tools

## Requirements

- Python 3.8+
- Git
- `codegen-on-oss` package

