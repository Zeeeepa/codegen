# PR Static Analysis System Architecture

This document describes the architecture of the PR static analysis system.

## System Architecture

The PR static analysis system is designed with a modular architecture that separates concerns and allows for extensibility. The system is organized into the following components:

```
                                +----------------+
                                |                |
                                |   PRAnalyzer   |
                                |                |
                                +-------+--------+
                                        |
                                        |
                +---------------------+-+-------------------+
                |                     |                     |
        +-------v-------+    +--------v--------+    +------v-------+
        |               |    |                 |    |              |
        | GitHubClient  |    |   RuleEngine    |    |  Report      |
        | RepoOperator  |    |                 |    |  Generator   |
        |               |    |                 |    |              |
        +---------------+    +-----------------+    +--------------+
                                     |
                                     |
                              +------v------+
                              |             |
                              |   Rules     |
                              |             |
                              +-------------+
```

### Component Responsibilities

#### Core Components

- **PRAnalyzer**: The main orchestrator for PR analysis. It coordinates the analysis process, including loading repository data, applying rules, and generating reports.
- **RuleEngine**: Responsible for loading and running analysis rules.
- **AnalysisContext**: Holds the context for PR analysis, including repository and PR information.

#### Git Components

- **GitHubClient**: A wrapper around PyGithub for interacting with the GitHub API.
- **RepoOperator**: A wrapper around GitPython for Git operations.
- **Models**: Data models for Git entities like repositories and pull requests.

#### Reporting Components

- **ReportGenerator**: Responsible for generating analysis reports from rule results.
- **ReportFormatter**: Responsible for formatting analysis reports in different formats.

#### Rules

- **BaseRule**: The base class for all analysis rules.
- **Rule Implementations**: Specific rule implementations that extend BaseRule.

#### Utilities

- **ConfigUtils**: Utilities for loading and managing configuration.
- **DiffUtils**: Utilities for analyzing code diffs.

## Data Flow

The data flow through the system is as follows:

1. The user initiates analysis by calling `PRAnalyzer.run()` with a repository URL and PR number.
1. `PRAnalyzer` initializes the system components and retrieves repository and PR information from GitHub.
1. `RepoOperator` clones or updates the repository and checks out the PR branch.
1. `RuleEngine` loads and runs all configured rules.
1. Each rule analyzes the code changes and produces a result.
1. `ReportGenerator` collects the rule results and generates a report.
1. `PRAnalyzer` posts the report as a comment on the PR.

## Component Interfaces

### PRAnalyzer

```python
class PRAnalyzer:
    def __init__(self, config_path: Optional[str] = None): ...
    def initialize(self, repo_url: str, pr_number: int) -> None: ...
    def analyze(self) -> Dict[str, Any]: ...
    def post_results(self, results: Dict[str, Any]) -> None: ...
    def run(self, repo_url: str, pr_number: int) -> Dict[str, Any]: ...
```

### RuleEngine

```python
class RuleEngine:
    def __init__(self, context: AnalysisContext): ...
    def load_rule(self, rule_class: Type[BaseRule]) -> BaseRule: ...
    def load_rule_from_path(self, rule_path: str) -> BaseRule: ...
    def load_rules_from_config(self, rules_config: List[Dict[str, Any]]) -> None: ...
    def run_rule(self, rule_id: str) -> Dict[str, Any]: ...
    def run_all_rules(self) -> Dict[str, Dict[str, Any]]: ...
```

### AnalysisContext

```python
class AnalysisContext:
    def __init__(self, repository: Repository, pull_request: PullRequest, config: Dict[str, Any]): ...
    def set_data(self, key: str, value: Any) -> None: ...
    def get_data(self, key: str, default: Any = None) -> Any: ...
    def get_config(self, key: str, default: Any = None) -> Any: ...
```

### GitHubClient

```python
class GitHubClient:
    def __init__(self, token: Optional[str] = None, api_url: Optional[str] = None): ...
    def get_repository(self, repo_url: str) -> Repository: ...
    def get_pull_request(self, repository: Repository, pr_number: int) -> PullRequest: ...
    def post_pr_comment(self, repository: Repository, pull_request: PullRequest, comment: str) -> None: ...
```

### RepoOperator

```python
class RepoOperator:
    def __init__(self, repository: Repository, config: Optional[Dict[str, Any]] = None): ...
    def prepare_repository(self) -> None: ...
    def checkout_pull_request(self, pull_request: PullRequest) -> None: ...
    def cleanup(self) -> None: ...
```

### ReportGenerator

```python
class ReportGenerator:
    def __init__(self, context: AnalysisContext): ...
    def generate_report(self, rule_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]: ...
    def format_report_as_markdown(self, report: Dict[str, Any]) -> str: ...
    def format_report_as_json(self, report: Dict[str, Any]) -> Dict[str, Any]: ...
    def format_report_for_github(self, report: Dict[str, Any]) -> str: ...
```

### BaseRule

```python
class BaseRule:
    def __init__(self, context: AnalysisContext): ...
    def configure(self, config: Dict[str, Any]) -> None: ...
    def get_config(self, key: str, default: Any = None) -> Any: ...
    def run(self) -> Dict[str, Any]: ...
    def success(self, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]: ...
    def warning(self, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]: ...
    def error(self, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]: ...
```

## Extension Points

The system is designed to be extensible. The main extension points are:

- **Rules**: You can add new rules by subclassing `BaseRule`.
- **Report Formats**: You can add new report formats by extending `ReportFormatter`.
- **Git Providers**: You can add new Git providers by implementing similar interfaces to `GitHubClient`.
- **Visualizations**: You can add new visualizations by extending the reporting components.

## Configuration Management

The system uses a flexible configuration system that supports:

- Configuration files (JSON or YAML)
- Environment variables
- Default values

The configuration is loaded and managed by the `ConfigUtils` module.

## Dependency Management

The system depends on the following external libraries:

- `PyGithub`: For interacting with the GitHub API
- `GitPython`: For Git operations
- `PyYAML`: For configuration file parsing

These dependencies are managed through the project's dependency management system.
