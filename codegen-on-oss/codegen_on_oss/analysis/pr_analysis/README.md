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

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-org/your-repo.git
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

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

### Configuration

The system can be configured using a configuration file or environment variables:

```python
from codegen_on_oss.analysis.pr_analysis.core.pr_analyzer import PRAnalyzer

# Create PR analyzer with configuration file
analyzer = PRAnalyzer("config.yaml")

# Run analysis
analyzer.initialize("https://github.com/owner/repo", 123)
results = analyzer.analyze()
```

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

## License

This project is licensed under the MIT License - see the LICENSE file for details.

