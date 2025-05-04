"""
WSL2 Client for Code Validation

This module provides a client for interacting with the WSL2 server
for code validation, repository comparison, and PR analysis.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout

logger = logging.getLogger(__name__)


class WSLClientError(Exception):
    """Exception raised for errors in the WSL client."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a new WSLClientError.

        Args:
            message: Error message
            status_code: HTTP status code
            response: Response data
        """
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class WSLClient:
    """
    Client for interacting with the WSL2 server for code validation.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
        retry_delay: int = 2,
    ):
        """
        Initialize a new WSLClient.

        Args:
            base_url: Base URL of the WSL2 server
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.base_url = base_url
        self.api_key = api_key or os.getenv("CODEGEN_API_KEY", "")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.headers = {}

        if self.api_key:
            self.headers["X-API-Key"] = self.api_key

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Make a request to the WSL2 server with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Optional request data
            params: Optional query parameters
            timeout: Optional request timeout override

        Returns:
            Response data as a dictionary

        Raises:
            WSLClientError: If the request fails after all retries
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        timeout = timeout or self.timeout
        retries = 0

        while retries <= self.max_retries:
            try:
                if method.upper() == "GET":
                    response = requests.get(
                        url, headers=self.headers, params=params, timeout=timeout
                    )
                elif method.upper() == "POST":
                    response = requests.post(
                        url, headers=self.headers, json=data, params=params, timeout=timeout
                    )
                else:
                    raise WSLClientError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response.json()

            except ConnectionError as e:
                retries += 1
                if retries > self.max_retries:
                    raise WSLClientError(f"Connection error: {str(e)}") from e
                logger.warning(
                    f"Connection error, retrying ({retries}/{self.max_retries}): {str(e)}"
                )
                time.sleep(self.retry_delay)

            except Timeout as e:
                retries += 1
                if retries > self.max_retries:
                    raise WSLClientError(f"Request timed out: {str(e)}") from e
                logger.warning(
                    f"Request timed out, retrying ({retries}/{self.max_retries}): {str(e)}"
                )
                time.sleep(self.retry_delay)

            except HTTPError as e:
                # Try to parse error response
                error_detail = str(e)
                status_code = e.response.status_code if hasattr(e, "response") else None

                try:
                    error_data = e.response.json() if hasattr(e, "response") else {}
                except Exception:
                    error_data = {}

                raise WSLClientError(
                    f"HTTP error: {error_detail}", status_code=status_code, response=error_data
                ) from e

            except Exception as e:
                raise WSLClientError(f"Unexpected error: {str(e)}") from e

    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the WSL2 server.

        Returns:
            Dict containing the health status

        Raises:
            WSLClientError: If the health check fails
        """
        try:
            return self._make_request("GET", "health")
        except WSLClientError as e:
            logger.error(f"Health check failed: {e.message}")
            raise

    def validate_codebase(
        self,
        repo_url: str,
        branch: str = "main",
        categories: Optional[List[str]] = None,
        github_token: Optional[str] = None,
        include_metrics: bool = False,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Validate a codebase.

        Args:
            repo_url: URL of the repository to validate
            branch: Branch to validate
            categories: Categories to validate
            github_token: GitHub token for authentication
            include_metrics: Whether to include detailed metrics in the response
            timeout: Optional request timeout override

        Returns:
            Dict containing validation results

        Raises:
            WSLClientError: If the validation fails
        """
        payload = {
            "repo_url": repo_url,
            "branch": branch,
            "categories": categories or ["code_quality", "security", "maintainability"],
            "github_token": github_token,
            "include_metrics": include_metrics,
        }

        try:
            logger.info(f"Validating codebase: {repo_url} ({branch})")
            return self._make_request("POST", "validate", data=payload, timeout=timeout)
        except WSLClientError as e:
            logger.error(f"Codebase validation failed: {e.message}")
            raise

    def compare_repositories(
        self,
        base_repo_url: str,
        head_repo_url: str,
        base_branch: str = "main",
        head_branch: str = "main",
        github_token: Optional[str] = None,
        include_detailed_diff: bool = False,
        diff_file_paths: Optional[List[str]] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Compare two repositories or branches.

        Args:
            base_repo_url: URL of the base repository
            head_repo_url: URL of the head repository
            base_branch: Base branch
            head_branch: Head branch
            github_token: GitHub token for authentication
            include_detailed_diff: Whether to include detailed diffs in the response
            diff_file_paths: Optional list of file paths to include in the detailed diff
            timeout: Optional request timeout override

        Returns:
            Dict containing comparison results

        Raises:
            WSLClientError: If the comparison fails
        """
        payload = {
            "base_repo_url": base_repo_url,
            "head_repo_url": head_repo_url,
            "base_branch": base_branch,
            "head_branch": head_branch,
            "github_token": github_token,
            "include_detailed_diff": include_detailed_diff,
            "diff_file_paths": diff_file_paths or [],
        }

        try:
            logger.info(
                f"Comparing repositories: {base_repo_url} ({base_branch}) "
                f"vs {head_repo_url} ({head_branch})"
            )
            return self._make_request("POST", "compare", data=payload, timeout=timeout)
        except WSLClientError as e:
            logger.error(f"Repository comparison failed: {e.message}")
            raise

    def analyze_pr(
        self,
        repo_url: str,
        pr_number: int,
        github_token: Optional[str] = None,
        detailed: bool = True,
        post_comment: bool = False,
        include_diff_analysis: bool = False,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a pull request.

        Args:
            repo_url: URL of the repository
            pr_number: PR number to analyze
            github_token: GitHub token for authentication
            detailed: Whether to perform detailed analysis
            post_comment: Whether to post a comment with the analysis results
            include_diff_analysis: Whether to include diff analysis in the response
            timeout: Optional request timeout override

        Returns:
            Dict containing PR analysis results

        Raises:
            WSLClientError: If the analysis fails
        """
        payload = {
            "repo_url": repo_url,
            "pr_number": pr_number,
            "github_token": github_token,
            "detailed": detailed,
            "post_comment": post_comment,
            "include_diff_analysis": include_diff_analysis,
        }

        try:
            logger.info(f"Analyzing PR: {repo_url}#{pr_number}")
            return self._make_request("POST", "analyze-pr", data=payload, timeout=timeout)
        except WSLClientError as e:
            logger.error(f"PR analysis failed: {e.message}")
            raise

    def format_validation_results_markdown(self, results: Dict[str, Any]) -> str:
        """
        Format validation results as Markdown.

        Args:
            results: Validation results from validate_codebase

        Returns:
            Markdown-formatted string
        """
        markdown = f"# Code Validation Results: {results['repo_url']} ({results['branch']})\n\n"
        markdown += f"**Overall Score**: {results['overall_score']:.2f}/10\n\n"
        markdown += f"**Summary**: {results['summary']}\n\n"

        for result in results["validation_results"]:
            markdown += f"## {result['category'].title()}\n\n"
            markdown += f"**Score**: {result['score']:.2f}/10\n\n"

            if result["issues"]:
                markdown += "### Issues\n\n"
                for issue in result["issues"]:
                    markdown += f"- **{issue['title']}**: {issue['description']}\n"
                    if "file" in issue and "line" in issue:
                        markdown += f"  - Location: {issue['file']}:{issue['line']}\n"
                markdown += "\n"

            if result["recommendations"]:
                markdown += "### Recommendations\n\n"
                for recommendation in result["recommendations"]:
                    markdown += f"- {recommendation}\n"
                markdown += "\n"

        # Add metrics if available
        if "metrics" in results and results["metrics"]:
            metrics = results["metrics"]
            markdown += "## Codebase Metrics\n\n"
            markdown += f"- **Files**: {metrics.get('file_count', 'N/A')}\n"
            markdown += f"- **Functions**: {metrics.get('function_count', 'N/A')}\n"
            markdown += f"- **Classes**: {metrics.get('class_count', 'N/A')}\n"
            markdown += f"- **Total Lines**: {metrics.get('total_lines', 'N/A')}\n"
            markdown += f"- **Average Complexity**: {metrics.get('avg_complexity', 'N/A'):.2f}\n\n"

        return markdown

    def format_comparison_results_markdown(self, results: Dict[str, Any]) -> str:
        """
        Format comparison results as Markdown.

        Args:
            results: Comparison results from compare_repositories

        Returns:
            Markdown-formatted string
        """
        markdown = "# Repository Comparison Results\n\n"
        markdown += f"**Base**: {results['base_repo_url']}\n"
        markdown += f"**Head**: {results['head_repo_url']}\n\n"
        markdown += f"**Summary**: {results['summary']}\n\n"

        # File changes summary
        file_changes = results["file_changes"]
        added = sum(1 for change in file_changes.values() if change == "added")
        modified = sum(1 for change in file_changes.values() if change == "modified")
        deleted = sum(1 for change in file_changes.values() if change == "deleted")
        unchanged = sum(1 for change in file_changes.values() if change == "unchanged")

        markdown += "## File Changes Summary\n\n"
        markdown += f"- **Added**: {added}\n"
        markdown += f"- **Modified**: {modified}\n"
        markdown += f"- **Deleted**: {deleted}\n"
        markdown += f"- **Unchanged**: {unchanged}\n"
        markdown += f"- **Total**: {len(file_changes)}\n\n"

        # Function changes summary
        function_changes = results["function_changes"]
        added = sum(1 for change in function_changes.values() if change == "added")
        modified = sum(1 for change in function_changes.values() if change == "modified")
        deleted = sum(1 for change in function_changes.values() if change == "deleted")
        moved = sum(1 for change in function_changes.values() if change == "moved")
        unchanged = sum(1 for change in function_changes.values() if change == "unchanged")

        markdown += "## Function Changes Summary\n\n"
        markdown += f"- **Added**: {added}\n"
        markdown += f"- **Modified**: {modified}\n"
        markdown += f"- **Deleted**: {deleted}\n"
        markdown += f"- **Moved**: {moved}\n"
        markdown += f"- **Unchanged**: {unchanged}\n"
        markdown += f"- **Total**: {len(function_changes)}\n\n"

        # Risk assessment
        if results["risk_assessment"]:
            markdown += "## Risk Assessment\n\n"
            for category, risk in results["risk_assessment"].items():
                markdown += f"- **{category}**: {risk}\n"
            markdown += "\n"

        # Detailed file changes (limited to top 10 for brevity)
        if file_changes:
            markdown += "## Detailed File Changes\n\n"
            count = 0
            for file, change in sorted(file_changes.items()):
                if change != "unchanged" and count < 10:
                    markdown += f"- **{file}**: {change}\n"
                    count += 1

            if count < len([c for c in file_changes.values() if c != "unchanged"]):
                remaining = len([c for c in file_changes.values() if c != "unchanged"]) - count
                markdown += f"- ... and {remaining} more\n"
            markdown += "\n"

        # Complexity changes (top 5 increases and decreases)
        if results["complexity_changes"]:
            markdown += "## Complexity Changes\n\n"

            # Sort by complexity change (descending)
            sorted_complexity = sorted(
                results["complexity_changes"].items(), key=lambda x: x[1], reverse=True
            )

            # Top 5 increases
            increases = [item for item in sorted_complexity if item[1] > 0][:5]
            if increases:
                markdown += "### Top Complexity Increases\n\n"
                for file, change in increases:
                    markdown += f"- **{file}**: +{change:.2f}\n"
                markdown += "\n"

            # Top 5 decreases
            decreases = [item for item in sorted_complexity if item[1] < 0][-5:]
            if decreases:
                markdown += "### Top Complexity Decreases\n\n"
                for file, change in decreases:
                    markdown += f"- **{file}**: {change:.2f}\n"
                markdown += "\n"

        # Include detailed diffs if available
        if "detailed_diffs" in results and results["detailed_diffs"]:
            markdown += "## Detailed Diffs\n\n"
            for filepath, diff in results["detailed_diffs"].items():
                markdown += f"### {filepath}\n\n"
                markdown += "```diff\n"
                markdown += "\n".join(diff)
                markdown += "\n```\n\n"

        return markdown

    def format_pr_analysis_markdown(self, results: Dict[str, Any]) -> str:
        """
        Format PR analysis results as Markdown.

        Args:
            results: PR analysis results from analyze_pr

        Returns:
            Markdown-formatted string
        """
        markdown = f"# Pull Request Analysis: #{results['pr_number']}\n\n"
        markdown += f"**Repository**: {results['repo_url']}\n"
        markdown += f"**Code Quality Score**: {results['code_quality_score']:.2f}/10\n\n"
        markdown += f"**Summary**: {results['summary']}\n\n"

        if results["issues_found"]:
            markdown += "## Issues Found\n\n"
            for issue in results["issues_found"]:
                markdown += f"- **{issue['title']}**: {issue['description']}\n"
                if "file" in issue and "line" in issue:
                    markdown += f"  - Location: {issue['file']}:{issue['line']}\n"
            markdown += "\n"

        if results["recommendations"]:
            markdown += "## Recommendations\n\n"
            for recommendation in results["recommendations"]:
                markdown += f"- {recommendation}\n"
            markdown += "\n"

        # Include diff analysis if available
        if "diff_analysis" in results and results["diff_analysis"]:
            diff_analysis = results["diff_analysis"]

            if "error" in diff_analysis:
                markdown += "## Diff Analysis Error\n\n"
                markdown += f"Error: {diff_analysis['error']}\n\n"
            else:
                markdown += "## Diff Analysis\n\n"

                # File changes summary
                if "file_changes" in diff_analysis:
                    file_changes = diff_analysis["file_changes"]
                    added = sum(1 for change in file_changes.values() if change == "added")
                    modified = sum(1 for change in file_changes.values() if change == "modified")
                    deleted = sum(1 for change in file_changes.values() if change == "deleted")

                    markdown += "### File Changes\n\n"
                    markdown += f"- **Added**: {added}\n"
                    markdown += f"- **Modified**: {modified}\n"
                    markdown += f"- **Deleted**: {deleted}\n"
                    markdown += f"- **Total**: {len(file_changes)}\n\n"

                # Risk assessment
                if "risk_assessment" in diff_analysis and diff_analysis["risk_assessment"]:
                    markdown += "### Risk Assessment\n\n"
                    for category, risk in diff_analysis["risk_assessment"].items():
                        markdown += f"- **{category}**: {risk}\n"
                    markdown += "\n"

                # Summary
                if "summary" in diff_analysis:
                    markdown += "### Diff Summary\n\n"
                    markdown += "```\n"
                    markdown += diff_analysis["summary"]
                    markdown += "\n```\n\n"

        return markdown

    def save_results_to_file(self, results: Dict[str, Any], filename: str) -> str:
        """
        Save results to a file.

        Args:
            results: Results to save
            filename: Filename to save to

        Returns:
            Path to the saved file
        """
        filepath = Path(filename)

        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Save results as JSON
        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)

        return str(filepath.absolute())

    def load_results_from_file(self, filename: str) -> Dict[str, Any]:
        """
        Load results from a file.

        Args:
            filename: Filename to load from

        Returns:
            Loaded results
        """
        filepath = Path(filename)

        # Load results from JSON
        with open(filepath, "r") as f:
            results = json.load(f)

        return results

    def save_markdown_to_file(self, markdown: str, filename: str) -> str:
        """
        Save markdown to a file.

        Args:
            markdown: Markdown content to save
            filename: Filename to save to

        Returns:
            Path to the saved file
        """
        filepath = Path(filename)

        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Save markdown
        with open(filepath, "w") as f:
            f.write(markdown)

        return str(filepath.absolute())
