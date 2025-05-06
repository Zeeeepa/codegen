# PR Static Analysis System

This package provides a comprehensive system for analyzing pull requests and providing feedback on code quality, potential issues, and suggested improvements.

## Overview

The PR Static Analysis System is designed to analyze pull requests and provide feedback on various aspects of code quality, including:

- Code style and formatting
- Test coverage
- Security vulnerabilities
- Parameter types and validation
- Performance issues
- Error handling
- Documentation

The system is modular and extensible, allowing for easy addition of new analysis rules and customization of existing ones.

## Architecture

The system is organized into several modules:

- **core**: Core components for PR analysis orchestration
  - `pr_analyzer.py`: Main PR analysis orchestrator
  - `rule_engine.py`: Engine for applying analysis rules
  - `analysis_context.py`: Context for PR analysis

- **git**: Git integration components
  - `repo_operator.py`: Wrapper around GitPython
  - `github_client.py`: Wrapper around PyGithub
  - `models.py`: PR data models

- **rules**: Analysis rules
  - `base_rule.py`: Base class for analysis rules
  - `code_integrity_rules.py`: Rules for code integrity
  - `parameter_rules.py`: Rules for parameter validation
  - `implementation_rules.py`: Rules for implementation validation

- **reporting**: Reporting components
  - `report_generator.py`: Generator for analysis reports
  - `report_formatter.py`: Formatter for analysis reports
  - `visualization.py`: Visualization components

- **utils**: Utility functions
  - `diff_utils.py`: Utilities for diff analysis
  - `config_utils.py`: Utilities for configuration management

## Component Interfaces

### Core and Git Interface

The PR analyzer interacts with Git components through the following interfaces:

```python
# In pr_analyzer.py
self.github_client = GitHubClient(token=token, api_url=api_url)
repository = self.github_client.get_repository(repo_url)
pull_request = self.github_client.get_pull_request(repository, pr_number)
self.repo_operator = RepoOperator(repository, git_config)
self.repo_operator.prepare_repository()
self.repo_operator.checkout_pull_request(pull_request)
```

### Core and Rules Interface

The rule engine loads and applies rules through the following interfaces:

```python
# In pr_analyzer.py
self.rule_engine = RuleEngine(self.context)
self.rule_engine.load_rules_from_config(rules_config)
rule_results = self.rule_engine.run_all_rules()

# In rule_engine.py
def load_rule(self, rule_class: Type[BaseRule]) -> BaseRule:
    rule = rule_class(self.context)
    self.rules[rule.rule_id] = rule
    return rule

def run_all_rules(self) -> Dict[str, Dict[str, Any]]:
    results = {}
    for rule_id, rule in self.rules.items():
        results[rule_id] = rule.run()
    return results
```

### Core and Reporting Interface

Analysis results are passed to reporting components through the following interfaces:

```python
# In pr_analyzer.py
self.report_generator = ReportGenerator(self.context)
report = self.report_generator.generate_report(rule_results)
report_markdown = self.report_generator.format_report_for_github(report)
```

### Git and Reporting Interface

Git data is used in reports through the analysis context:

```python
# In report_generator.py
def generate_report(self, rule_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    # Access repository and PR data from context
    repo_name = self.context.repository.full_name
    pr_number = self.context.pull_request.number
    pr_title = self.context.pull_request.title
    # Generate report using this data
```

## Configuration Management

The system supports multiple configuration sources:

1. **Default Configuration**: Provided by `get_default_config()` in `config_utils.py`
2. **Configuration Files**: JSON or YAML files loaded with `load_config()`
3. **Environment Variables**: Loaded with `get_config_from_env()`
4. **User-defined Overrides**: Merged with `merge_configs()`

Configuration options include:

- **GitHub API Access**: Token and API URL
- **Analysis Rules**: Which rules to apply and their configurations
- **Reporting**: Format and destination for reports
- **Performance Settings**: Timeouts and concurrency

Example configuration file (YAML):

```yaml
github:
  token: your-github-token
  api_url: https://api.github.com

git:
  repo_path: /path/to/repos

rules:
  - rule_path: codegen_on_oss.analysis.pr_analysis.rules.code_integrity_rules.CodeStyleRule
    config:
      severity: medium
      include_patterns:
        - '.*\.(py|js|ts|tsx|jsx)$'
      exclude_patterns:
        - '.*\.(json|md|txt|csv|yml|yaml)$'
      max_line_length: 100
      check_trailing_whitespace: true
      check_final_newline: true
      warning_threshold: 5

reporting:
  format: markdown
  post_to_github: true

performance:
  timeout: 300
  concurrency: 4
```

## Dependency Management

### Internal Dependencies

- **Core** depends on **Git**, **Rules**, and **Reporting**
- **Rules** depend on **Core** (for context) and **Utils**
- **Reporting** depends on **Core** (for context)
- **Utils** has no dependencies on other modules

### External Dependencies

The system depends on the following external libraries:

- **PyGithub**: For GitHub API integration
- **GitPython**: For Git operations
- **PyYAML**: For YAML configuration file support

These dependencies are listed in `requirements.txt`.

## Usage

### Basic Usage

```python
from codegen_on_oss.analysis.pr_analysis.core.pr_analyzer import PRAnalyzer

# Create PR analyzer
analyzer = PRAnalyzer()

# Run analysis
analyzer.initialize("https://github.com/owner/repo", 123)
results = analyzer.analyze()

# Post results to GitHub
analyzer.post_results(results)
```

### With Configuration

```python
from codegen_on_oss.analysis.pr_analysis.core.pr_analyzer import PRAnalyzer

# Create PR analyzer with configuration file
analyzer = PRAnalyzer("config.yaml")

# Run analysis
analyzer.initialize("https://github.com/owner/repo", 123)
results = analyzer.analyze()
```

## Adding New Rules

To add a new analysis rule:

1. Create a new rule class that inherits from `BaseRule`:

```python
from codegen_on_oss.analysis.pr_analysis.rules.base_rule import BaseRule

class MyRule(BaseRule):
    rule_id = 'my_rule'
    name = 'My Rule'
    description = 'My custom analysis rule'
    
    def run(self):
        # Implement rule logic
        return self.success("Rule passed successfully")
```

2. Add the rule to your configuration:

```yaml
rules:
  - rule_path: path.to.your.module.MyRule
    config:
      severity: medium
      # Other rule-specific configuration
```

## End-to-End Testing

The system includes an end-to-end test in `test_e2e.py` that demonstrates how to use the PR analysis system:

```bash
# Set GitHub token
export GITHUB_TOKEN=your-github-token

# Run test
python -m codegen_on_oss.analysis.pr_analysis.test_e2e https://github.com/owner/repo 123
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

