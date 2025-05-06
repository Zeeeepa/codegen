# Extending the PR Static Analysis System

This document provides guidance on how to extend the PR static analysis system with new rules, report formats, and other components.

## Adding New Rules

The rule system is designed to be easily extensible. To add a new rule:

### 1. Create a New Rule Class

Create a new Python file in the appropriate rules directory (e.g., `rules/my_rules.py`) and define a class that inherits from `BaseRule`:

```python
from codegen_on_oss.analysis.pr_analysis.rules.base_rule import BaseRule

class MyCustomRule(BaseRule):
    rule_id = 'my_custom_rule'  # Unique identifier for the rule
    name = 'My Custom Rule'     # Human-readable name
    description = 'This rule checks for custom conditions in the code'  # Description
    
    def run(self):
        """
        Implement the rule logic here.
        
        Returns:
            Rule result dictionary
        """
        # Access the analysis context
        repo = self.context.repository
        pr = self.context.pull_request
        
        # Access rule configuration
        severity = self.get_config('severity', 'medium')
        threshold = self.get_config('threshold', 5)
        
        # Implement rule logic
        # ...
        
        # Return success, warning, or error
        if everything_is_good:
            return self.success("All checks passed")
        elif minor_issues:
            return self.warning("Some minor issues found", {
                'issues': issues_list,
                'count': len(issues_list)
            })
        else:
            return self.error("Serious issues found", {
                'issues': issues_list,
                'count': len(issues_list)
            })
```

### 2. Add the Rule to Configuration

Add your rule to the configuration:

```yaml
rules:
  - rule_path: codegen_on_oss.analysis.pr_analysis.rules.my_rules.MyCustomRule
    config:
      severity: medium
      threshold: 5
      # Other rule-specific configuration
```

### 3. Test Your Rule

Create a test for your rule:

```python
import unittest
from unittest.mock import MagicMock

from codegen_on_oss.analysis.pr_analysis.rules.my_rules import MyCustomRule
from codegen_on_oss.analysis.pr_analysis.core.analysis_context import AnalysisContext

class TestMyCustomRule(unittest.TestCase):
    def setUp(self):
        # Create mock context
        self.context = MagicMock(spec=AnalysisContext)
        self.context.repository = MagicMock()
        self.context.pull_request = MagicMock()
        
        # Create rule instance
        self.rule = MyCustomRule(self.context)
        self.rule.configure({
            'severity': 'medium',
            'threshold': 5
        })
    
    def test_rule_success(self):
        # Set up mock data for success case
        # ...
        
        # Run rule
        result = self.rule.run()
        
        # Assert result
        self.assertEqual(result['status'], 'success')
    
    def test_rule_warning(self):
        # Set up mock data for warning case
        # ...
        
        # Run rule
        result = self.rule.run()
        
        # Assert result
        self.assertEqual(result['status'], 'warning')
    
    def test_rule_error(self):
        # Set up mock data for error case
        # ...
        
        # Run rule
        result = self.rule.run()
        
        # Assert result
        self.assertEqual(result['status'], 'error')
```

## Rule Categories and Best Practices

When creating new rules, consider which category they belong to:

### Code Integrity Rules

These rules focus on code quality and style:

- Code style and formatting
- Test coverage
- Security vulnerabilities
- Code complexity
- Dead code detection

Example: `CodeStyleRule`, `TestCoverageRule`, `SecurityVulnerabilityRule`

### Parameter Rules

These rules focus on function/method parameters:

- Parameter types
- Parameter validation
- Parameter documentation
- Default values
- Required vs. optional parameters

Example: `ParameterTypeRule`, `ParameterValidationRule`

### Implementation Rules

These rules focus on implementation details:

- Performance issues
- Error handling
- Documentation
- Design patterns
- API consistency

Example: `PerformanceRule`, `ErrorHandlingRule`, `DocumentationRule`

### Best Practices for Rule Implementation

1. **Keep rules focused**: Each rule should check one specific aspect of code quality.
2. **Make rules configurable**: Use `self.get_config()` to get configuration values.
3. **Provide detailed results**: Include specific details about issues found.
4. **Handle exceptions gracefully**: Catch and log exceptions in your rule logic.
5. **Document your rule**: Add docstrings and comments to explain what the rule does.
6. **Write tests**: Create unit tests for your rule to ensure it works correctly.

## Adding New Report Formats

To add a new report format:

1. Add a new method to `ReportFormatter` in `reporting/report_formatter.py`:

```python
def format_report_as_html(self, report):
    """
    Format report as HTML.
    
    Args:
        report: Report to format
        
    Returns:
        HTML string
    """
    # Implement HTML formatting logic
    # ...
    return html_string
```

2. Update `ReportGenerator` in `reporting/report_generator.py` to use the new format:

```python
def generate_report(self, rule_results):
    # ...
    
    # Format report based on configuration
    format_type = self.context.config.get('reporting', {}).get('format', 'markdown')
    if format_type == 'markdown':
        formatted_report = self.formatter.format_report_as_markdown(report)
    elif format_type == 'html':
        formatted_report = self.formatter.format_report_as_html(report)
    elif format_type == 'json':
        formatted_report = report  # Already in JSON format
    else:
        raise ValueError(f"Unsupported report format: {format_type}")
    
    return formatted_report
```

## Adding New Git Providers

To add support for a new Git provider (e.g., GitLab, Bitbucket):

1. Create a new client class in `git/` (e.g., `gitlab_client.py`):

```python
class GitLabClient:
    """
    GitLab client for PR analysis.
    """
    
    def __init__(self, token=None, api_url=None):
        """
        Initialize the GitLab client.
        
        Args:
            token: GitLab API token
            api_url: GitLab API URL
        """
        self.token = token
        self.api_url = api_url or 'https://gitlab.com/api/v4'
        # Initialize GitLab API client
        # ...
    
    def get_repository(self, repo_url):
        """
        Get repository information.
        
        Args:
            repo_url: Repository URL
            
        Returns:
            Repository object
        """
        # Implement repository retrieval logic
        # ...
        return repository
    
    def get_pull_request(self, repository, pr_number):
        """
        Get pull request information.
        
        Args:
            repository: Repository object
            pr_number: Pull request number
            
        Returns:
            Pull request object
        """
        # Implement pull request retrieval logic
        # ...
        return pull_request
    
    def post_pr_comment(self, repository, pull_request, comment):
        """
        Post a comment to a pull request.
        
        Args:
            repository: Repository object
            pull_request: Pull request object
            comment: Comment text
        """
        # Implement comment posting logic
        # ...
```

2. Update `PRAnalyzer` in `core/pr_analyzer.py` to support the new provider:

```python
def initialize(self, repo_url, pr_number):
    # ...
    
    # Determine Git provider from URL
    if 'github.com' in repo_url:
        self.git_client = GitHubClient(
            token=self.config.get('github', {}).get('token'),
            api_url=self.config.get('github', {}).get('api_url')
        )
    elif 'gitlab.com' in repo_url:
        self.git_client = GitLabClient(
            token=self.config.get('gitlab', {}).get('token'),
            api_url=self.config.get('gitlab', {}).get('api_url')
        )
    else:
        raise ValueError(f"Unsupported Git provider for URL: {repo_url}")
    
    # Get repository and PR data
    repository = self.git_client.get_repository(repo_url)
    pull_request = self.git_client.get_pull_request(repository, pr_number)
    
    # ...
```

## Adding New Visualizations

To add new visualizations:

1. Add a new method to `Visualization` in `reporting/visualization.py`:

```python
def generate_issue_heatmap(self, rule_results):
    """
    Generate a heatmap of issues by file.
    
    Args:
        rule_results: Rule results
        
    Returns:
        Heatmap data
    """
    # Implement heatmap generation logic
    # ...
    return heatmap_data
```

2. Update `ReportGenerator` in `reporting/report_generator.py` to include the new visualization:

```python
def generate_report(self, rule_results):
    # ...
    
    # Generate visualizations
    visualizations = {}
    if self.context.config.get('reporting', {}).get('include_visualizations', False):
        visualizations['summary_chart'] = self.visualization.generate_summary_chart(rule_results)
        visualizations['issue_heatmap'] = self.visualization.generate_issue_heatmap(rule_results)
    
    # Include visualizations in report
    report['visualizations'] = visualizations
    
    # ...
    return report
```

## Contributing Guidelines

When contributing to the PR static analysis system, please follow these guidelines:

1. **Follow the coding style**: Use consistent indentation, naming conventions, and code organization.
2. **Add docstrings**: Document all classes, methods, and functions with docstrings.
3. **Add type hints**: Use type hints for function parameters and return values.
4. **Write tests**: Add unit tests for new functionality.
5. **Update documentation**: Update README.md and other documentation to reflect your changes.
6. **Keep it modular**: Maintain the modular architecture of the system.
7. **Respect interfaces**: Follow the established interfaces between components.
8. **Handle errors gracefully**: Catch and log exceptions appropriately.
9. **Be configurable**: Make new components configurable through the configuration system.
10. **Consider performance**: Be mindful of performance implications, especially for large repositories.

