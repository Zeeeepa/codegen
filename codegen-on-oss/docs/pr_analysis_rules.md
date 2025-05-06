# PR Static Analysis Rules

This document describes the analysis rules for the PR static analysis system. These rules are used to detect errors, issues, wrongly implemented features, and parameter problems in pull requests.

## Overview

The PR static analysis system includes three categories of rules:

1. **Code Integrity Rules**: Detect syntax errors, undefined references, unused imports, and circular dependencies.
2. **Parameter Validation Rules**: Detect parameter type mismatches, missing parameters, and incorrect parameter usage.
3. **Implementation Validation Rules**: Detect incomplete feature implementations, insufficient test coverage, performance implications, and security considerations.

## Using the Rules

To use the rules, you need to create a context object that provides access to the PR data and utilities, and then apply the rules to the context.

```python
from codegen_on_oss.analysis.pr_analysis.rules import ALL_RULES

# Create a context object (implementation depends on your PR data source)
context = create_context(pr_data)

# Apply all rules
results = []
for rule in ALL_RULES:
    rule_results = rule.apply(context)
    results.extend(rule_results)

# Process the results
for result in results:
    print(f"{result.severity.upper()}: {result.message}")
    if result.file:
        print(f"  File: {result.file}")
        if result.line:
            print(f"  Line: {result.line}")
            if result.column:
                print(f"  Column: {result.column}")
    print()
```

## Rule Categories

### Code Integrity Rules

These rules detect issues with the code's integrity, such as syntax errors and undefined references.

#### SyntaxErrorRule (CI001)

Checks for syntax errors in Python files.

```python
from codegen_on_oss.analysis.pr_analysis.rules import SyntaxErrorRule

rule = SyntaxErrorRule()
results = rule.apply(context)
```

#### UndefinedReferenceRule (CI002)

Checks for undefined references in Python files.

```python
from codegen_on_oss.analysis.pr_analysis.rules import UndefinedReferenceRule

rule = UndefinedReferenceRule()
results = rule.apply(context)
```

#### UnusedImportRule (CI003)

Checks for unused imports in Python files.

```python
from codegen_on_oss.analysis.pr_analysis.rules import UnusedImportRule

rule = UnusedImportRule()
results = rule.apply(context)
```

#### CircularDependencyRule (CI004)

Checks for circular dependencies between Python modules.

```python
from codegen_on_oss.analysis.pr_analysis.rules import CircularDependencyRule

rule = CircularDependencyRule()
results = rule.apply(context)
```

### Parameter Validation Rules

These rules detect issues with function parameters, such as type mismatches and missing parameters.

#### ParameterTypeMismatchRule (PV001)

Checks for parameter type mismatches in function calls.

```python
from codegen_on_oss.analysis.pr_analysis.rules import ParameterTypeMismatchRule

rule = ParameterTypeMismatchRule()
results = rule.apply(context)
```

#### MissingParameterRule (PV002)

Checks for missing required parameters in function calls.

```python
from codegen_on_oss.analysis.pr_analysis.rules import MissingParameterRule

rule = MissingParameterRule()
results = rule.apply(context)
```

#### IncorrectParameterUsageRule (PV003)

Checks for incorrect parameter usage in function calls.

```python
from codegen_on_oss.analysis.pr_analysis.rules import IncorrectParameterUsageRule

rule = IncorrectParameterUsageRule()
results = rule.apply(context)
```

### Implementation Validation Rules

These rules detect issues with the implementation of features, such as incomplete features and insufficient test coverage.

#### FeatureCompletenessRule (IV001)

Checks if a feature is completely implemented.

```python
from codegen_on_oss.analysis.pr_analysis.rules import FeatureCompletenessRule

rule = FeatureCompletenessRule()
results = rule.apply(context)
```

#### TestCoverageRule (IV002)

Checks if the code has sufficient test coverage.

```python
from codegen_on_oss.analysis.pr_analysis.rules import TestCoverageRule

rule = TestCoverageRule()
results = rule.apply(context)
```

#### PerformanceImplicationRule (IV003)

Checks for performance implications in code changes.

```python
from codegen_on_oss.analysis.pr_analysis.rules import PerformanceImplicationRule

rule = PerformanceImplicationRule()
results = rule.apply(context)
```

#### SecurityConsiderationRule (IV004)

Checks for security considerations in code changes.

```python
from codegen_on_oss.analysis.pr_analysis.rules import SecurityConsiderationRule

rule = SecurityConsiderationRule()
results = rule.apply(context)
```

## Creating Custom Rules

You can create custom rules by subclassing the `BaseRule` class and implementing the `apply` method.

```python
from codegen_on_oss.analysis.pr_analysis.rules import BaseRule, AnalysisResult

class CustomRule(BaseRule):
    """Custom rule for detecting specific issues."""
    
    def __init__(self):
        """Initialize the custom rule."""
        super().__init__(
            rule_id="CUSTOM001",
            name="Custom Rule",
            description="Checks for specific issues."
        )
        
    def apply(self, context):
        """
        Apply the rule to the context and return results.
        
        Args:
            context: Analysis context containing PR data and utilities
            
        Returns:
            List of analysis results
        """
        results = []
        
        # Implement your custom rule logic here
        
        return results
```

## Context Interface

The context object passed to the `apply` method of each rule should provide the following interface:

```python
class AnalysisContext:
    """Context for PR analysis, providing data and utilities for rules."""
    
    def get_file_changes(self):
        """
        Get files changed in the PR.
        
        Returns:
            Dictionary mapping file paths to change types ("added", "modified", "deleted")
        """
        pass
    
    def get_files(self):
        """
        Get all files in the repository.
        
        Returns:
            List of file paths
        """
        pass
    
    def get_file_content(self, file_path):
        """
        Get the content of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Content of the file as a string
        """
        pass
```

The context object should also have `base_context` and `head_context` attributes that provide access to the base and head branches of the PR, respectively. These attributes should also implement the above interface.

## Analysis Result

The `AnalysisResult` class represents a result from an analysis rule. It has the following attributes:

- `rule_id`: Unique identifier for the rule that produced this result
- `severity`: Severity level ("error", "warning", or "info")
- `message`: Human-readable message describing the issue
- `file`: Path to the file where the issue was found (optional)
- `line`: Line number where the issue was found (optional)
- `column`: Column number where the issue was found (optional)
- `details`: Additional details about the issue (optional)

You can create an `AnalysisResult` as follows:

```python
from codegen_on_oss.analysis.pr_analysis.rules import AnalysisResult

result = AnalysisResult(
    rule_id="CUSTOM001",
    severity="warning",
    message="Custom issue detected",
    file="path/to/file.py",
    line=10,
    column=5,
    details={"error_type": "custom_issue"}
)
```

## Integration with Core Analysis Engine

The rules are designed to be used with the core analysis engine, which orchestrates the analysis process, applies rules, and generates results. See the core analysis engine documentation for more information on how to integrate the rules with the engine.

