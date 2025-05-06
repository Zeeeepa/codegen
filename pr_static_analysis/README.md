# PR Static Analysis System

A flexible rule-based system for analyzing pull requests and identifying potential issues.

## Overview

The PR Static Analysis System is designed to analyze pull requests for various issues, including:

- Code integrity issues (syntax errors, logical issues, code smells, potential bugs)
- Parameter validation issues (parameter type checking, parameter usage, unused parameters, parameter naming)
- Implementation validation issues (implementation completeness, validation against requirements, missing edge cases, performance issues)

The system is built around a flexible rule-based architecture that allows for easy customization and extension.

## Features

- **Flexible Rule System**: Rules are organized into categories and can be enabled/disabled individually.
- **Rule Configuration**: Rules can be configured with custom options to adjust their behavior.
- **Rule Dependencies**: Rules can depend on other rules, ensuring they are executed in the correct order.
- **Severity Levels**: Issues can be reported with different severity levels (error, warning, info, hint).
- **Fix Suggestions**: Rules can provide suggestions for fixing issues.
- **Extensible**: The system can be easily extended with custom rules.

## Architecture

The system is built around the following components:

- **BaseRule**: Abstract base class that all rules inherit from.
- **RuleRegistry**: Registry for managing available rules.
- **RuleConfig**: Configuration manager for rules.
- **PRStaticAnalyzer**: Main engine for analyzing PRs using the rule system.

Rules are organized into categories:

- **Code Integrity Rules**: Rules for checking code integrity issues.
- **Parameter Validation Rules**: Rules for checking parameter validation issues.
- **Implementation Validation Rules**: Rules for checking implementation validation issues.

## Usage

### Basic Usage

```python
from pr_static_analysis import PRStaticAnalyzer
from pr_static_analysis.rules import rule_config

# Load configuration
rule_config.load_config_file("config.yaml")

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
python -m pr_static_analysis.example --pr /path/to/pr --config config.yaml --output report.json
```

## Configuration

The system can be configured using a YAML or JSON configuration file. Here's an example:

```yaml
# Global configuration options
global:
  max_issues_per_file: 10
  max_issues_per_rule: 20
  include_code_snippets: true
  include_fix_suggestions: true

# Rule-specific configuration options
rules:
  syntax-error:
    enabled: true
    severity: error

  code-smell:
    enabled: true
    severity: warning
    max_function_length: 50
    max_nesting_depth: 3

# List of explicitly enabled rules
enabled_rules:
  - syntax-error
  - code-smell

# List of explicitly disabled rules
disabled_rules: []
```

## Creating Custom Rules

To create a custom rule, follow these steps:

1. Create a new rule class that inherits from `BaseRule` or one of the category-specific base classes.
1. Implement the required properties and methods.
1. Register the rule with the rule registry.

Example:

```python
from pr_static_analysis.rules.base import BaseRule, RuleCategory, RuleResult, RuleSeverity

class MyCustomRule(BaseRule):
    @property
    def id(self) -> str:
        return "my-custom-rule"
    
    @property
    def name(self) -> str:
        return "My Custom Rule"
    
    @property
    def description(self) -> str:
        return "This is a custom rule that does something."
    
    @property
    def category(self) -> RuleCategory:
        return RuleCategory.CUSTOM
    
    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.WARNING
    
    def analyze(self, context: Dict[str, Any]) -> List[RuleResult]:
        results = []
        # Analyze the PR and add results
        return results

# Register the rule
from pr_static_analysis.rules import rule_registry
rule_registry.register(MyCustomRule)
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
