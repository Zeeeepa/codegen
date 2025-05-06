# PR Static Analysis System

A flexible rule-based system for analyzing pull requests and identifying potential issues.

## Overview

The PR Static Analysis System is designed to analyze pull requests for various issues, including:

- **Code Integrity Issues**: Syntax errors, logical issues, code smells, potential bugs
- **Parameter Validation Issues**: Parameter type checking, parameter usage, unused parameters, parameter naming
- **Implementation Validation Issues**: Implementation completeness, validation against requirements, missing edge cases, performance issues

The system is built around a flexible rule-based architecture that allows for easy customization and extension.

## Features

- **Flexible Rule System**: Rules are organized into categories and can be enabled/disabled individually.
- **Rule Configuration**: Rules can be configured with custom options to adjust their behavior.
- **Rule Dependencies**: Rules can depend on other rules, ensuring they are executed in the correct order.
- **Severity Levels**: Issues can be reported with different severity levels (error, warning, info, hint).
- **Fix Suggestions**: Rules can provide suggestions for fixing issues.
- **Extensible**: The system can be easily extended with custom rules.

## Installation

```bash
pip install -e .
```

## Usage

### Basic Usage

```python
from pr_static_analysis import PRStaticAnalyzer
from pr_static_analysis.rules import rule_config

# Load configuration
rule_config.load_config_file("pr_static_analysis/config.yaml")

# Create analyzer
analyzer = PRStaticAnalyzer()

# Create context
context = {
    "files": [
        {
            "filepath": "example.py",
            "content": "def foo(x, y):\n    return x / y  # Potential division by zero",
        },
    ],
    "pr": {
        "title": "Example PR",
        "description": "This is an example PR.",
        "author": "example-user",
        "branch": "feature/example",
    },
    "config": rule_config.global_config,
}

# Analyze PR
results = analyzer.analyze(context)

# Generate report
report = analyzer.generate_report(results)
```

### Command Line Usage

```bash
python -m pr_static_analysis.example --pr /path/to/pr --config pr_static_analysis/config.yaml --output report.json
```

## Documentation

For more detailed documentation, see the [PR Static Analysis README](pr_static_analysis/README.md).

## License

This project is licensed under the MIT License - see the LICENSE file for details.

