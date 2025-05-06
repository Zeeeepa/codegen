# PR Static Analysis System

This package provides a system for analyzing pull requests and detecting potential issues.

## Overview

The PR static analysis system is designed to analyze pull requests and provide feedback on code quality, style, and other aspects. It consists of several components:

- **PR Analyzer**: The main orchestrator for PR analysis
- **Rule Engine**: Engine for applying analysis rules
- **Analysis Context**: Context for PR analysis, providing data and utilities for rules
- **Diff Context**: Context representing differences between base and head branches
- **Rules**: Rules for checking various aspects of code quality
- **GitHub Integration**: Integration with GitHub's API
- **Reporting**: Generation of analysis reports

## Components

### PR Analyzer

The PR analyzer is the main entry point for the analysis process. It:

1. Retrieves PR data from GitHub
2. Creates analysis contexts for the base and head branches
3. Invokes the rule engine to apply rules
4. Collects and aggregates results
5. Generates a final analysis report

### Rule Engine

The rule engine is responsible for applying rules to the analysis context:

1. Manages a collection of rules
2. Applies rules to the analysis context
3. Collects and aggregates results
4. Handles rule execution errors

### Analysis Context

The analysis context provides data and utilities for rules:

1. Provides access to the codebase
2. Tracks file and symbol changes
3. Provides utilities for accessing file content and symbols

### Diff Context

The diff context represents the differences between the base and head branches:

1. Tracks file, function, and class changes
2. Provides utilities for accessing changed files and symbols

### Rules

Rules check various aspects of code quality:

1. **Complexity Rule**: Checks for functions with high cyclomatic complexity
2. **Style Rule**: Checks for code style issues like line length, indentation, etc.
3. **Docstring Rule**: Checks if functions and classes have docstrings

### GitHub Integration

GitHub integration provides access to GitHub's API:

1. Retrieves PR data
2. Gets file content
3. Comments on PRs with analysis results

### Reporting

Reporting generates analysis reports:

1. Aggregates analysis results
2. Formats results for different output formats (Markdown, HTML, JSON)
3. Provides summaries and detailed information

## Usage

Here's a simple example of how to use the PR analysis system:

```python
from codegen_on_oss.analysis.pr_analysis.core import (
    create_rule_engine,
    create_pr_analyzer,
    create_report_generator,
)
from codegen_on_oss.analysis.pr_analysis.rules import (
    ComplexityRule,
    StyleRule,
    DocstringRule,
)
from codegen_on_oss.analysis.pr_analysis.utils.integration import create_github_client

# Create GitHub client
github_client = create_github_client("your-github-token")

# Create rules
rules = [
    ComplexityRule(max_complexity=10),
    StyleRule(max_line_length=100),
    DocstringRule(),
]

# Create rule engine
rule_engine = create_rule_engine(rules)

# Create report generator
report_generator = create_report_generator("markdown")

# Create PR analyzer
pr_analyzer = create_pr_analyzer(github_client, rule_engine, report_generator)

# Analyze PR
report = pr_analyzer.analyze_pr(123, "owner/repo")

# Print report
print(report_generator.format_report_as_markdown(report))

# Comment on PR
pr_analyzer.comment_on_pr(123, "owner/repo", report)
```

## Adding New Rules

To add a new rule, create a new class that inherits from `BaseRule` and implements the `apply` method:

```python
from typing import List
from codegen_on_oss.analysis.pr_analysis.rules.base_rule import BaseRule, AnalysisResult

class MyRule(BaseRule):
    def __init__(self):
        super().__init__(
            rule_id="my_rule",
            name="My Rule",
            description="Description of my rule",
            category="my_category"
        )
    
    def apply(self, context) -> List[AnalysisResult]:
        results = []
        # Analyze the context and add results
        return results
```

Then, add your rule to the rule engine:

```python
rule_engine = create_rule_engine([MyRule()])
```

## Integration with Existing Components

The PR analysis system integrates with several existing components:

1. **graph-sitter**: Used for code representation and analysis
2. **codegen-on-oss**: Used for diff analysis and code integrity checking
3. **GitHub API**: Used for PR data retrieval and commenting

## Dependencies

- graph-sitter
- codegen-on-oss
- PyGithub (for GitHub API access)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

