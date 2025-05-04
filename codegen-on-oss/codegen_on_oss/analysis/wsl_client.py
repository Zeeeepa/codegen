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
from typing import Any, Dict, List, Optional, Union

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


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
    ):
        """
        Initialize a new WSLClient.

        Args:
            base_url: Base URL of the WSL2 server
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.base_url = base_url
        self.api_key = api_key or os.getenv("CODEGEN_API_KEY", "")
        self.timeout = timeout
        self.headers = {}

        if self.api_key:
            self.headers["X-API-Key"] = self.api_key

        # Configure session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Make a request to the WSL2 server.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request arguments

        Returns:
            Response JSON

        Raises:
            RequestException: If the request fails
            ValueError: If JSON decoding fails
        """
        url = f"{self.base_url}{endpoint}"
        headers = {**self.headers, **kwargs.pop("headers", {})}
        
        try:
            start_time = time.time()
            logger.debug(f"Making {method} request to {url}")
            
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                timeout=self.timeout,
                **kwargs,
            )
            
            # Log request duration
            duration = time.time() - start_time
            logger.debug(f"Request to {url} completed in {duration:.2f}s")
            
            # Raise exception for error status codes
            response.raise_for_status()
            
            try:
                return response.json()
            except ValueError as e:
                logger.error(f"Failed to decode JSON response: {str(e)}")
                raise ValueError(f"Failed to decode JSON response: {str(e)}") from e
        
        except RequestException as e:
            logger.error(f"Request to {url} failed: {str(e)}")
            
            # Try to extract error details from response
            error_detail = "Unknown error"
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_detail = error_data.get("detail", str(e))
                except ValueError:
                    error_detail = e.response.text or str(e)
            
            raise RequestException(f"Request failed: {error_detail}") from e

    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the WSL2 server.

        Returns:
            Dict containing the health status
        """
        return self._make_request("GET", "/health")

    def validate_codebase(
        self,
        repo_url: str,
        branch: str = "main",
        categories: Optional[List[str]] = None,
        github_token: Optional[str] = None,
        include_details: bool = True,
    ) -> Dict[str, Any]:
        """
        Validate a codebase.

        Args:
            repo_url: URL of the repository to validate
            branch: Branch to validate
            categories: Categories to validate
            github_token: GitHub token for authentication
            include_details: Whether to include detailed results

        Returns:
            Dict containing validation results
        """
        payload = {
            "repo_url": repo_url,
            "branch": branch,
            "categories": categories or ["code_quality", "security", "maintainability"],
            "github_token": github_token,
            "include_details": include_details,
        }

        return self._make_request(
            "POST",
            "/validate",
            json=payload,
        )

    def compare_repositories(
        self,
        base_repo_url: str,
        head_repo_url: str,
        base_branch: str = "main",
        head_branch: str = "main",
        github_token: Optional[str] = None,
        include_file_diffs: bool = True,
        include_function_details: bool = True,
        include_class_details: bool = True,
    ) -> Dict[str, Any]:
        """
        Compare two repositories or branches.

        Args:
            base_repo_url: URL of the base repository
            head_repo_url: URL of the head repository
            base_branch: Base branch
            head_branch: Head branch
            github_token: GitHub token for authentication
            include_file_diffs: Whether to include file diffs in the response
            include_function_details: Whether to include function details
            include_class_details: Whether to include class details

        Returns:
            Dict containing comparison results
        """
        payload = {
            "base_repo_url": base_repo_url,
            "head_repo_url": head_repo_url,
            "base_branch": base_branch,
            "head_branch": head_branch,
            "github_token": github_token,
            "include_file_diffs": include_file_diffs,
            "include_function_details": include_function_details,
            "include_class_details": include_class_details,
        }

        return self._make_request(
            "POST",
            "/compare",
            json=payload,
        )

    def analyze_pr(
        self,
        repo_url: str,
        pr_number: int,
        github_token: Optional[str] = None,
        detailed: bool = True,
        post_comment: bool = False,
        include_diff: bool = True,
    ) -> Dict[str, Any]:
        """
        Analyze a pull request.

        Args:
            repo_url: URL of the repository
            pr_number: PR number to analyze
            github_token: GitHub token for authentication
            detailed: Whether to perform detailed analysis
            post_comment: Whether to post a comment with the analysis results
            include_diff: Whether to include diff information in the response

        Returns:
            Dict containing PR analysis results
        """
        payload = {
            "repo_url": repo_url,
            "pr_number": pr_number,
            "github_token": github_token,
            "detailed": detailed,
            "post_comment": post_comment,
            "include_diff": include_diff,
        }

        return self._make_request(
            "POST",
            "/analyze-pr",
            json=payload,
        )

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

        # Add execution time if available
        if "execution_time" in results:
            markdown += f"*Analysis completed in {results['execution_time']:.2f} seconds*\n\n"

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
        markdown += f"**Base**: {results['base_repo_url']} ({results['base_branch']})\n"
        markdown += f"**Head**: {results['head_repo_url']} ({results['head_branch']})\n\n"
        markdown += f"**Summary**: {results['summary']}\n\n"

        # Add impact analysis
        if "impact_analysis" in results and results["impact_analysis"]:
            impact = results["impact_analysis"]
            
            if "statistics" in impact:
                stats = impact["statistics"]
                markdown += "## Statistics\n\n"
                markdown += f"- **Files**: {stats.get('files_added', 0)} added, {stats.get('files_removed', 0)} removed, {stats.get('files_modified', 0)} modified\n"
                markdown += f"- **Functions**: {stats.get('functions_added', 0)} added, {stats.get('functions_removed', 0)} removed, {stats.get('functions_modified', 0)} modified\n"
                markdown += f"- **Classes**: {stats.get('classes_added', 0)} added, {stats.get('classes_removed', 0)} removed, {stats.get('classes_modified', 0)} modified\n"
                markdown += f"- **Lines**: {stats.get('total_lines_added', 0)} added, {stats.get('total_lines_removed', 0)} removed (net: {stats.get('net_line_change', 0)})\n\n"
            
            if "risk_assessment" in impact:
                markdown += "## Risk Assessment\n\n"
                for category, risk in impact["risk_assessment"].items():
                    markdown += f"- **{category}**: {risk}\n"
                markdown += "\n"

        # Add file changes
        if "file_changes" in results and results["file_changes"]:
            markdown += "## File Changes\n\n"
            
            # Group files by status
            added_files = []
            removed_files = []
            modified_files = []
            
            for file_path, file_info in results["file_changes"].items():
                status = file_info.get("status", "unknown")
                if status == "added":
                    added_files.append((file_path, file_info))
                elif status == "removed":
                    removed_files.append((file_path, file_info))
                elif status == "modified":
                    modified_files.append((file_path, file_info))
            
            if added_files:
                markdown += "### Added Files\n\n"
                for file_path, file_info in added_files:
                    lines_added = file_info.get("lines_added", 0)
                    markdown += f"- **{file_path}**: {lines_added} lines added\n"
                markdown += "\n"
            
            if removed_files:
                markdown += "### Removed Files\n\n"
                for file_path, file_info in removed_files:
                    lines_removed = file_info.get("lines_removed", 0)
                    markdown += f"- **{file_path}**: {lines_removed} lines removed\n"
                markdown += "\n"
            
            if modified_files:
                markdown += "### Modified Files\n\n"
                for file_path, file_info in modified_files:
                    lines_added = file_info.get("lines_added", 0)
                    lines_removed = file_info.get("lines_removed", 0)
                    markdown += f"- **{file_path}**: {lines_added} lines added, {lines_removed} lines removed\n"
                markdown += "\n"

        # Add execution time if available
        if "execution_time" in results:
            markdown += f"*Comparison completed in {results['execution_time']:.2f} seconds*\n\n"

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

        # Add execution time if available
        if "execution_time" in results:
            markdown += f"*Analysis completed in {results['execution_time']:.2f} seconds*\n\n"

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

        logger.info(f"Results saved to {filepath.absolute()}")
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

        # Check if file exists
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        # Load results from JSON
        try:
            with open(filepath, "r") as f:
                results = json.load(f)
            
            logger.info(f"Results loaded from {filepath.absolute()}")
            return results
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {filepath}: {str(e)}")
            raise ValueError(f"Invalid JSON in file: {filepath}") from e
        
    def export_results_to_html(
        self, results: Dict[str, Any], filename: str, template: Optional[str] = None
    ) -> str:
        """
        Export results to an HTML file.

        Args:
            results: Results to export
            filename: Filename to save to
            template: Optional HTML template to use

        Returns:
            Path to the saved file
        """
        filepath = Path(filename)

        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Determine result type and generate appropriate HTML
        if "validation_results" in results:
            # Code validation results
            html = self._generate_validation_html(results, template)
        elif "file_changes" in results and "impact_analysis" in results:
            # Repository comparison results
            html = self._generate_comparison_html(results, template)
        elif "analysis_results" in results and "pr_number" in results:
            # PR analysis results
            html = self._generate_pr_analysis_html(results, template)
        else:
            # Unknown result type
            html = self._generate_generic_html(results, template)

        # Save HTML to file
        with open(filepath, "w") as f:
            f.write(html)

        logger.info(f"HTML report saved to {filepath.absolute()}")
        return str(filepath.absolute())

    def _generate_validation_html(
        self, results: Dict[str, Any], template: Optional[str] = None
    ) -> str:
        """
        Generate HTML for validation results.

        Args:
            results: Validation results
            template: Optional HTML template

        Returns:
            HTML string
        """
        # Use template if provided, otherwise use default
        if template:
            with open(template, "r") as f:
                html = f.read()
        else:
            # Default template
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Code Validation Results</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                    h1, h2, h3 { color: #333; }
                    .summary { background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
                    .category { margin-bottom: 30px; }
                    .score { font-size: 24px; font-weight: bold; }
                    .issue { background-color: #fff; padding: 10px; margin-bottom: 10px; border-left: 4px solid #e74c3c; }
                    .recommendation { background-color: #fff; padding: 10px; margin-bottom: 10px; border-left: 4px solid #3498db; }
                </style>
            </head>
            <body>
                <h1>Code Validation Results: {{repo_url}} ({{branch}})</h1>
                
                <div class="summary">
                    <h2>Summary</h2>
                    <p><span class="score">{{overall_score}}/10</span></p>
                    <p>{{summary}}</p>
                </div>
                
                {{#validation_results}}
                <div class="category">
                    <h2>{{category}}</h2>
                    <p><span class="score">{{score}}/10</span></p>
                    
                    {{#issues}}
                    <h3>Issues</h3>
                    {{#.}}
                    <div class="issue">
                        <h4>{{title}}</h4>
                        <p>{{description}}</p>
                        {{#file}}<p>Location: {{file}}:{{line}}</p>{{/file}}
                    </div>
                    {{/.}}
                    {{/issues}}
                    
                    {{#recommendations}}
                    <h3>Recommendations</h3>
                    {{#.}}
                    <div class="recommendation">
                        <p>{{.}}</p>
                    </div>
                    {{/.}}
                    {{/recommendations}}
                </div>
                {{/validation_results}}
                
                <p><em>Analysis completed in {{execution_time}} seconds</em></p>
            </body>
            </html>
            """

        # Replace placeholders with actual values
        html = html.replace("{{repo_url}}", results["repo_url"])
        html = html.replace("{{branch}}", results["branch"])
        html = html.replace("{{overall_score}}", f"{results['overall_score']:.2f}")
        html = html.replace("{{summary}}", results["summary"])
        html = html.replace("{{execution_time}}", f"{results.get('execution_time', 0):.2f}")

        # Replace validation results
        validation_results_html = ""
        for result in results["validation_results"]:
            category_html = f"""
            <div class="category">
                <h2>{result['category'].title()}</h2>
                <p><span class="score">{result['score']:.2f}/10</span></p>
            """

            # Add issues
            if result["issues"]:
                category_html += "<h3>Issues</h3>"
                for issue in result["issues"]:
                    issue_html = f"""
                    <div class="issue">
                        <h4>{issue['title']}</h4>
                        <p>{issue['description']}</p>
                    """
                    if "file" in issue and "line" in issue:
                        issue_html += f"<p>Location: {issue['file']}:{issue['line']}</p>"
                    issue_html += "</div>"
                    category_html += issue_html

            # Add recommendations
            if result["recommendations"]:
                category_html += "<h3>Recommendations</h3>"
                for recommendation in result["recommendations"]:
                    category_html += f"""
                    <div class="recommendation">
                        <p>{recommendation}</p>
                    </div>
                    """

            category_html += "</div>"
            validation_results_html += category_html

        html = html.replace("{{#validation_results}}", "")
        html = html.replace("{{/validation_results}}", "")
        html = html.replace("{{#issues}}", "")
        html = html.replace("{{/issues}}", "")
        html = html.replace("{{#recommendations}}", "")
        html = html.replace("{{/recommendations}}", "")
        html = html.replace("{{#.}}", "")
        html = html.replace("{{/.}}", "")
        html = html.replace("{{#file}}", "")
        html = html.replace("{{/file}}", "")
        
        # Insert validation results
        html = html.replace("{{category}}", validation_results_html)

        return html

    def _generate_comparison_html(
        self, results: Dict[str, Any], template: Optional[str] = None
    ) -> str:
        """
        Generate HTML for comparison results.

        Args:
            results: Comparison results
            template: Optional HTML template

        Returns:
            HTML string
        """
        # This is a simplified implementation
        # In a real implementation, you would generate a more detailed HTML report
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Repository Comparison Results</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                .summary {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <h1>Repository Comparison Results</h1>
            
            <div class="summary">
                <h2>Summary</h2>
                <p><strong>Base:</strong> {results['base_repo_url']} ({results['base_branch']})</p>
                <p><strong>Head:</strong> {results['head_repo_url']} ({results['head_branch']})</p>
                <p>{results['summary']}</p>
            </div>
            
            <p><em>Comparison completed in {results.get('execution_time', 0):.2f} seconds</em></p>
        </body>
        </html>
        """

    def _generate_pr_analysis_html(
        self, results: Dict[str, Any], template: Optional[str] = None
    ) -> str:
        """
        Generate HTML for PR analysis results.

        Args:
            results: PR analysis results
            template: Optional HTML template

        Returns:
            HTML string
        """
        # This is a simplified implementation
        # In a real implementation, you would generate a more detailed HTML report
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pull Request Analysis Results</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                .summary {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .score {{ font-size: 24px; font-weight: bold; }}
                .issue {{ background-color: #fff; padding: 10px; margin-bottom: 10px; border-left: 4px solid #e74c3c; }}
                .recommendation {{ background-color: #fff; padding: 10px; margin-bottom: 10px; border-left: 4px solid #3498db; }}
            </style>
        </head>
        <body>
            <h1>Pull Request Analysis: #{results['pr_number']}</h1>
            
            <div class="summary">
                <h2>Summary</h2>
                <p><strong>Repository:</strong> {results['repo_url']}</p>
                <p><span class="score">{results['code_quality_score']:.2f}/10</span></p>
                <p>{results['summary']}</p>
            </div>
            
            <p><em>Analysis completed in {results.get('execution_time', 0):.2f} seconds</em></p>
        </body>
        </html>
        """

    def _generate_generic_html(
        self, results: Dict[str, Any], template: Optional[str] = None
    ) -> str:
        """
        Generate HTML for generic results.

        Args:
            results: Generic results
            template: Optional HTML template

        Returns:
            HTML string
        """
        # This is a simplified implementation
        # In a real implementation, you would generate a more detailed HTML report
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Analysis Results</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                pre {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <h1>Analysis Results</h1>
            
            <pre>{json.dumps(results, indent=2)}</pre>
        </body>
        </html>
        """
