# PR Static Analysis System

This directory contains the PR static analysis system, which is designed to analyze pull requests and provide feedback on code quality, implementation, and potential issues.

## System Overview

The PR static analysis system is designed to analyze pull requests and provide feedback on code quality, implementation, and potential issues. It is built with extensibility in mind, allowing for the addition of new rules, report formats, and Git providers.

The system works by:

1. Retrieving pull request information from GitHub
1. Cloning the repository and checking out the PR branch
1. Analyzing the code changes using a set of rules
1. Generating a report with findings and recommendations
1. Posting the report as a comment on the PR

## Directory Structure

The system is organized into the following directories:

- `core/`: Core components for orchestrating the analysis process
- `git/`: Git integration components for interacting with repositories and GitHub
- `reporting/`: Components for generating and formatting reports
- `rules/`: Analysis rules for evaluating code changes
- `utils/`: Utility functions for configuration, diff analysis, etc.

## Core Components

The core components are responsible for orchestrating the analysis process:

- `PRAnalyzer`: Main orchestrator for PR analysis
- `RuleEngine`: Engine for loading and running analysis rules
- `AnalysisContext`: Context object for PR analysis

## Git Components

The Git components are responsible for interacting with repositories and GitHub:

- `GitHubClient`: Client for interacting with GitHub API
- `RepoOperator`: Operator for Git repository operations
- `Models`: Data models for Git entities

## Reporting Components

The reporting components are responsible for generating and formatting reports:

- `ReportGenerator`: Generator for analysis reports
- `ReportFormatter`: Formatter for analysis reports

## Rules

The rules are responsible for evaluating code changes:

- `BaseRule`: Base class for all rules

## Utilities

The utilities provide common functionality:

- `ConfigUtils`: Utilities for configuration management
- `DiffUtils`: Utilities for diff analysis

## Usage

To use the PR static analysis system, you can use the `PRAnalyzer` class:

```python
from codegen_on_oss.analysis.pr_analysis import PRAnalyzer

# Create a PR analyzer
analyzer = PRAnalyzer()

# Run analysis on a PR
results = analyzer.run("owner/repo", 123)

# Print the report
print(results["report"])
```

You can also use the `test_e2e.py` script to run analysis from the command line:

```bash
python -m codegen_on_oss.analysis.pr_analysis.test_e2e owner/repo 123
```

## Configuration

The system can be configured using a configuration file or environment variables. The configuration includes:

- GitHub API token and URL
- Git repository path
- Rules to apply
- Reporting format and options
- Performance settings

See `utils/config_utils.py` for more details on configuration options.

## Extending the System

The system is designed to be extensible. You can:

- Add new rules by subclassing `BaseRule`
- Add new report formats by extending `ReportFormatter`
- Add new Git providers by implementing similar interfaces to `GitHubClient`
- Add new visualizations by extending the reporting components

See `EXTENDING.md` for more details on extending the system.

## Dependencies

The system depends on the following external libraries:

- `PyGithub`: For interacting with the GitHub API
- `GitPython`: For Git operations
- `PyYAML`: For configuration file parsing

## Testing

The system includes a simple end-to-end test in `test_e2e.py` that demonstrates how to use the system.

## License

This code is licensed under the same license as the parent project.
