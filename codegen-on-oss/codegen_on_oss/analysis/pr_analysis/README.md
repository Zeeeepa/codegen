# PR Static Analysis System

This system analyzes pull requests to detect errors, issues, wrongly implemented features, and parameter problems. It provides clear feedback on whether a PR provides a valid and error-free implementation.

## Architecture

The PR static analysis system has the following components:

```
pr_analysis/
├── __init__.py
├── core/                  # Core components
│   ├── __init__.py
│   ├── pr_analyzer.py     # Main PR analysis orchestrator
│   ├── rule_engine.py     # Engine for applying analysis rules
│   └── analysis_context.py # Context for PR analysis
├── git/                   # Git integration components
│   ├── __init__.py
│   ├── repo_operator.py   # Wrapper around GitPython
│   ├── github_client.py   # Wrapper around PyGithub
│   └── models.py          # PR data models
├── rules/                 # Analysis rules
│   ├── __init__.py
│   ├── base_rule.py       # Base class for analysis rules
│   ├── code_integrity_rules.py # Rules for code integrity
│   ├── parameter_rules.py # Rules for parameter validation
│   └── implementation_rules.py # Rules for implementation validation
├── reporting/             # Reporting components
│   ├── __init__.py
│   ├── report_generator.py # Generator for analysis reports
│   ├── report_formatter.py # Formatter for analysis reports
│   └── visualization.py    # Visualization components
└── utils/                 # Utility functions
    ├── __init__.py
    ├── diff_utils.py      # Utilities for diff analysis
    └── config_utils.py    # Utilities for configuration
```

## Core Components

### PR Analyzer

The `PRAnalyzer` class orchestrates the analysis process. It provides methods for analyzing PRs, commits, and diffs.

```python
from pr_analysis.core.pr_analyzer import PRAnalyzer

# Create a PR analyzer
analyzer = PRAnalyzer()

# Analyze a PR
context = analyzer.analyze_pr(
    pr_number=123,
    repo="owner/repo"
)

# Get the results
results = analyzer.get_results(context)

# Check if there are any errors or warnings
if analyzer.has_errors(context):
    print(f"Found {analyzer.get_error_count(context)} errors")
if analyzer.has_warnings(context):
    print(f"Found {analyzer.get_warning_count(context)} warnings")
```

### Rule Engine

The `RuleEngine` class manages and applies analysis rules. It supports rule prioritization, dependencies, and customization.

```python
from pr_analysis.core.rule_engine import RuleEngine, BaseRule

# Create a rule engine
engine = RuleEngine()

# Register a rule
engine.register_rule(MyRule())

# Apply rules to a context
results = engine.apply_rules(context)

# Apply rules of a specific category
results = engine.apply_rule_category("code_integrity", context)

# Apply a single rule
results = engine.apply_single_rule("my_rule", context)
```

### Analysis Context

The `AnalysisContext` class holds all the necessary data for PR analysis. It includes references to the base and head branches, changed files, and analysis results.

```python
from pr_analysis.core.analysis_context import AnalysisContext, AnalysisResult

# Create a context
context = AnalysisContext(
    base_ref="main",
    head_ref="feature-branch",
    repo_path="/path/to/repo",
    pr_number=123,
    repo_name="owner/repo"
)

# Add a changed file
context.add_changed_file("path/to/file.py")

# Add file content
context.add_file_content("path/to/file.py", "main", "content at main")
context.add_file_content("path/to/file.py", "feature-branch", "content at feature-branch")

# Add a diff
context.add_file_diff("path/to/file.py", "diff content")

# Add a result
result = AnalysisResult(
    rule_id="my_rule",
    message="This is a result",
    file_path="path/to/file.py",
    line_number=42,
    severity="error",
    category="code_integrity"
)
context.add_result(result)

# Get results
all_results = context.get_results()
error_results = context.get_results_by_severity("error")
code_integrity_results = context.get_results_by_category("code_integrity")
file_results = context.get_results_by_file("path/to/file.py")
```

## Creating Custom Rules

To create a custom rule, extend the `BaseRule` class and implement the `apply` method:

```python
from typing import List
from pr_analysis.core.rule_engine import BaseRule
from pr_analysis.core.analysis_context import AnalysisContext, AnalysisResult

class MyRule(BaseRule):
    """
    A custom rule.
    """
    
    id = "my_rule"
    name = "My Rule"
    description = "A custom rule"
    category = "code_integrity"
    severity = "error"
    
    def apply(self, context: AnalysisContext) -> List[AnalysisResult]:
        """
        Apply the rule to the analysis context.
        
        Args:
            context: Analysis context
            
        Returns:
            List of analysis results
        """
        results = []
        
        # Analyze changed files
        for file_path in context.get_changed_files():
            # Get file content
            base_content = context.get_file_content(file_path, context.base_ref)
            head_content = context.get_file_content(file_path, context.head_ref)
            
            # Analyze the content
            if head_content and "TODO" in head_content:
                # Create a result
                result = self.create_result(
                    message="Found TODO in the code",
                    file_path=file_path,
                    line_number=head_content.split("TODO")[0].count("\n") + 1
                )
                results.append(result)
        
        return results
```

## Usage

To use the PR static analysis system, create a `PRAnalyzer` instance, register rules, and analyze PRs:

```python
from pr_analysis.core.pr_analyzer import PRAnalyzer
from pr_analysis.rules.code_integrity_rules import SyntaxErrorRule, MissingImportRule

# Create a PR analyzer
analyzer = PRAnalyzer()

# Register rules
analyzer.register_rule(SyntaxErrorRule())
analyzer.register_rule(MissingImportRule())

# Analyze a PR
context = analyzer.analyze_pr(
    pr_number=123,
    repo="owner/repo"
)

# Get the results
results = analyzer.get_results(context)

# Print the results
for result in results:
    print(f"{result.rule_id}: {result.message} ({result.severity})")
    if result.file_path:
        print(f"  File: {result.file_path}")
    if result.line_number:
        print(f"  Line: {result.line_number}")
```

## Dependencies

The PR static analysis system depends on the following:

- graph-sitter: Provides robust Git/GitHub integration and PR data extraction capabilities
- codegen: Offers sophisticated code analysis modules for detecting issues
- PyGithub: For GitHub API interactions
- GitPython: For Git operations

