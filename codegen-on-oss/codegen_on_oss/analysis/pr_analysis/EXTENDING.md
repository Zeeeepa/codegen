# Extending the PR Static Analysis System

This document provides guidance on extending the PR static analysis system with new rules, report formats, Git providers, and visualizations.

## Adding New Rules

Rules are the core of the analysis system. They analyze code changes and provide feedback. To add a new rule:

1. Create a new Python file in the `rules` directory or a subdirectory.
1. Define a class that extends `BaseRule`.
1. Implement the `run` method to perform the analysis.
1. Return a result dictionary with status, message, and optional details.

Here's an example of a simple rule that checks for trailing whitespace:

```python
from typing import Dict, Any
from codegen_on_oss.analysis.pr_analysis.rules.base_rule import BaseRule


class TrailingWhitespaceRule(BaseRule):
    rule_id = "trailing_whitespace"
    name = "Trailing Whitespace Check"
    description = "Checks for trailing whitespace in code changes"

    def run(self) -> Dict[str, Any]:
        # Get the files changed in the PR
        files = self.context.pull_request.files or []

        # Check for trailing whitespace in each file
        files_with_trailing_whitespace = []
        for file_info in files:
            filename = file_info["filename"]
            patch = file_info.get("patch", "")

            # Check for trailing whitespace in added lines
            for line in patch.splitlines():
                if line.startswith("+") and line.rstrip() != line and not line.strip() == "+":
                    files_with_trailing_whitespace.append(filename)
                    break

        # Return the result
        if files_with_trailing_whitespace:
            return self.warning(
                f"Found trailing whitespace in {len(files_with_trailing_whitespace)} files",
                {"files": files_with_trailing_whitespace, "recommendations": ["Remove trailing whitespace from all files", "Consider using a pre-commit hook to prevent trailing whitespace"]},
            )
        else:
            return self.success("No trailing whitespace found")
```

To use the new rule, you need to add it to the configuration:

```yaml
rules:
  - rule_path: 
      codegen_on_oss.analysis.pr_analysis.rules.trailing_whitespace.TrailingWhitespaceRule
    config:
      severity: warning
```

## Adding New Report Formats

The system currently supports Markdown and JSON report formats. To add a new format:

1. Extend the `ReportFormatter` class in `reporting/report_formatter.py`.
1. Add a new method for the format.
1. Update the `ReportGenerator` class to use the new format.

Here's an example of adding an HTML report format:

```python
def format_report_as_html(self, report: Dict[str, Any]) -> str:
    """
    Format a report as HTML.

    Args:
        report: Report to format

    Returns:
        HTML string
    """
    html = f"<html><head><title>PR Analysis Report</title></head><body>"

    # Add repository and PR information
    html += f"<h1>PR Analysis Report</h1>"
    html += f"<h2>Repository: {self.context.repository.full_name}</h2>"
    html += f"<h2>Pull Request: #{self.context.pull_request.number} - {self.context.pull_request.title}</h2>"

    # Add summary
    html += f"<h2>Summary</h2>"
    if "summary" in report:
        html += f"<p>{report['summary']}</p>"
    else:
        html += f"<p>No summary available.</p>"

    # Add rule results
    html += f"<h2>Rule Results</h2>"
    if "rule_results" in report:
        html += f"<ul>"
        for rule_id, result in report["rule_results"].items():
            status = result.get("status", "unknown")
            message = result.get("message", "No message")
            details = result.get("details", {})

            if status == "success":
                html += f"<li style='color: green;'><strong>{rule_id}:</strong> {message}</li>"
            elif status == "warning":
                html += f"<li style='color: orange;'><strong>{rule_id}:</strong> {message}</li>"
            elif status == "error":
                html += f"<li style='color: red;'><strong>{rule_id}:</strong> {message}</li>"
            else:
                html += f"<li><strong>{rule_id}:</strong> {message}</li>"

            if details:
                html += f"<ul>"
                for key, value in details.items():
                    html += f"<li><strong>{key}:</strong> {value}</li>"
                html += f"</ul>"
        html += f"</ul>"
    else:
        html += f"<p>No rule results available.</p>"

    # Add recommendations
    html += f"<h2>Recommendations</h2>"
    if "recommendations" in report:
        html += f"<ul>"
        for recommendation in report["recommendations"]:
            html += f"<li>{recommendation}</li>"
        html += f"</ul>"
    else:
        html += f"<p>No recommendations available.</p>"

    html += f"</body></html>"
    return html
```

Then update the `ReportGenerator` class to use the new format:

```python
def format_report_as_html(self, report: Dict[str, Any]) -> str:
    """
    Format a report as HTML.

    Args:
        report: Report to format

    Returns:
        HTML string
    """
    return self.formatter.format_report_as_html(report)
```

## Adding New Git Providers

The system currently supports GitHub. To add a new Git provider:

1. Create a new client class similar to `GitHubClient`.
1. Implement methods for retrieving repository and PR information.
1. Implement methods for posting comments.
1. Update the `PRAnalyzer` class to use the new client.

Here's an example of adding a GitLab client:

```python
class GitLabClient:
    """
    Client for interacting with GitLab API.

    This class provides methods for retrieving repository and PR data from GitLab.

    Attributes:
        gitlab: python-gitlab client
        api_url: GitLab API URL
    """

    def __init__(self, token: Optional[str] = None, api_url: Optional[str] = None):
        """
        Initialize the GitLab client.

        Args:
            token: GitLab API token
            api_url: GitLab API URL
        """
        import gitlab

        self.api_url = api_url or "https://gitlab.com"
        if token:
            self.gitlab = gitlab.Gitlab(self.api_url, private_token=token)
        else:
            self.gitlab = gitlab.Gitlab(self.api_url)

    def get_repository(self, repo_url: str) -> Repository:
        """
        Get repository information.

        Args:
            repo_url: Repository URL or owner/repo string

        Returns:
            Repository object

        Raises:
            ValueError: If the repository cannot be found
        """
        # Parse the repo URL to get owner and repo name
        if "/" in repo_url and "gitlab.com" not in repo_url:
            owner, repo_name = repo_url.split("/")
        else:
            # Extract owner/repo from a full GitLab URL
            parts = repo_url.rstrip("/").split("/")
            owner = parts[-2]
            repo_name = parts[-1]
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]

        try:
            # Get the repository from GitLab
            gitlab_repo = self.gitlab.projects.get(f"{owner}/{repo_name}")
            return self._convert_gitlab_repo(gitlab_repo)
        except Exception as e:
            logger.error(f"Failed to get repository {repo_url}: {e}")
            raise ValueError(f"Failed to get repository {repo_url}: {e}")

    # ... implement other methods ...
```

## Adding New Visualizations

The system currently provides text-based reports. To add visualizations:

1. Extend the `ReportFormatter` class to generate visualization data.
1. Add methods to generate visualization files (e.g., HTML, SVG, PNG).
1. Update the `ReportGenerator` class to use the new visualizations.

Here's an example of adding a simple chart visualization:

```python
def generate_chart_data(self, report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate data for a chart visualization.

    Args:
        report: Report to visualize

    Returns:
        Chart data
    """
    # Count rule results by status
    status_counts = {"success": 0, "warning": 0, "error": 0, "unknown": 0}

    if "rule_results" in report:
        for result in report["rule_results"].values():
            status = result.get("status", "unknown")
            status_counts[status] += 1

    return {
        "labels": list(status_counts.keys()),
        "data": list(status_counts.values()),
        "colors": ["green", "orange", "red", "gray"],
    }


def generate_chart_html(self, report: Dict[str, Any]) -> str:
    """
    Generate an HTML chart visualization.

    Args:
        report: Report to visualize

    Returns:
        HTML string with chart
    """
    chart_data = self.generate_chart_data(report)

    html = f"""
    <html>
    <head>
        <title>PR Analysis Chart</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <h1>PR Analysis Chart</h1>
        <canvas id="chart" width="400" height="400"></canvas>
        <script>
            const ctx = document.getElementById('chart').getContext('2d');
            const chart = new Chart(ctx, {{
                type: 'pie',
                data: {{
                    labels: {chart_data["labels"]},
                    datasets: [{{
                        data: {chart_data["data"]},
                        backgroundColor: {chart_data["colors"]},
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{
                            position: 'top',
                        }},
                        title: {{
                            display: true,
                            text: 'PR Analysis Results'
                        }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """

    return html
```

## Contributing Guidelines

When extending the system, please follow these guidelines:

1. **Code Style**: Follow the project's code style and linting rules.
1. **Documentation**: Document your code with docstrings and comments.
1. **Testing**: Write tests for your code.
1. **Error Handling**: Handle errors gracefully and provide helpful error messages.
1. **Performance**: Consider the performance implications of your code.
1. **Compatibility**: Ensure your code is compatible with the rest of the system.
1. **Dependencies**: Minimize external dependencies.

## Getting Help

If you need help extending the system, you can:

1. Read the documentation in the code and in the `docs` directory.
1. Look at existing implementations for examples.
1. Ask for help from the project maintainers.

Happy extending!
