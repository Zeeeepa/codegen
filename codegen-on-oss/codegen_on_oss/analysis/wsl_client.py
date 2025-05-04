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
from requests.packages.urllib3.util.retry import Retry

from codegen_on_oss.errors import (
    AuthenticationError,
    ComparisonError,
    PRAnalysisError,
    RateLimitError,
    TimeoutError,
    ValidationError,
    WSLClientError,
)

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
            
        # Configure session with retries
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
        
    def __del__(self):
        """
        Clean up resources when the client is destroyed.
        """
        try:
            if hasattr(self, 'session'):
                self.session.close()
                logger.debug("WSLClient session closed")
        except Exception as e:
            logger.warning(f"Error closing WSLClient session: {str(e)}")
            
    def __enter__(self):
        """
        Support for context manager protocol.
        """
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Clean up resources when exiting context manager.
        """
        try:
            self.session.close()
            logger.debug("WSLClient session closed")
        except Exception as e:
            logger.warning(f"Error closing WSLClient session: {str(e)}")
            
    def close(self):
        """
        Explicitly close the session.
        """
        try:
            self.session.close()
            logger.debug("WSLClient session closed")
        except Exception as e:
            logger.warning(f"Error closing WSLClient session: {str(e)}")
            raise WSLClientError(f"Error closing session: {str(e)}")
    
    def _handle_response_error(self, response: requests.Response, operation: str) -> None:
        """
        Handle error responses from the server.

        Args:
            response: Response object
            operation: Description of the operation being performed

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit is exceeded
            TimeoutError: If the request times out
            WSLClientError: For other client errors
            ValidationError: For validation errors
            ComparisonError: For comparison errors
            PRAnalysisError: For PR analysis errors
        """
        try:
            error_data = response.json()
            error_message = error_data.get("detail", "Unknown error")
            error_type = error_data.get("error_type", "Unknown")
        except (ValueError, KeyError):
            error_message = response.text or f"HTTP {response.status_code}"
            error_type = "Unknown"

        logger.error(f"Error during {operation}: {error_message} (Type: {error_type})")

        if response.status_code == 401:
            raise AuthenticationError(f"Authentication failed: {error_message}")
        elif response.status_code == 429:
            raise RateLimitError(f"Rate limit exceeded: {error_message}")
        elif response.status_code == 408:
            raise TimeoutError(f"Request timed out: {error_message}")
        elif 400 <= response.status_code < 500:
            if operation == "validation":
                raise ValidationError(f"Validation error: {error_message}")
            elif operation == "comparison":
                raise ComparisonError(f"Comparison error: {error_message}")
            elif operation == "PR analysis":
                raise PRAnalysisError(f"PR analysis error: {error_message}")
            else:
                raise WSLClientError(f"Client error during {operation}: {error_message}")
        else:
            raise WSLClientError(f"Server error during {operation}: {error_message}")

    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the WSL2 server.

        Returns:
            Dict containing the health status

        Raises:
            WSLClientError: If the health check fails
        """
        try:
            response = self.session.get(
                f"{self.base_url}/health", 
                headers=self.headers,
                timeout=self.timeout,
            )
            
            if response.status_code != 200:
                self._handle_response_error(response, "health check")
                
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Health check failed: {str(e)}")
            raise WSLClientError(f"Health check failed: {str(e)}")

    def validate_codebase(
        self,
        repo_url: str,
        branch: str = "main",
        categories: Optional[List[str]] = None,
        github_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate a codebase.

        Args:
            repo_url: URL of the repository to validate
            branch: Branch to validate
            categories: Categories to validate
            github_token: GitHub token for authentication

        Returns:
            Dict containing validation results

        Raises:
            ValidationError: If validation fails
        """
        payload = {
            "repo_url": repo_url,
            "branch": branch,
            "categories": categories or ["code_quality", "security", "maintainability"],
            "github_token": github_token,
        }

        try:
            start_time = time.time()
            logger.info(f"Validating codebase: {repo_url} (branch: {branch})")
            
            response = self.session.post(
                f"{self.base_url}/validate",
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
            )
            
            if response.status_code != 200:
                self._handle_response_error(response, "validation")
                
            result = response.json()
            
            elapsed_time = time.time() - start_time
            logger.info(f"Validation completed in {elapsed_time:.2f} seconds")
            
            return result
        except requests.RequestException as e:
            logger.error(f"Validation request failed: {str(e)}")
            raise ValidationError(f"Validation request failed: {str(e)}")

    def compare_repositories(
        self,
        base_repo_url: str,
        head_repo_url: str,
        base_branch: str = "main",
        head_branch: str = "main",
        github_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compare two repositories or branches.

        Args:
            base_repo_url: URL of the base repository
            head_repo_url: URL of the head repository
            base_branch: Base branch
            head_branch: Head branch
            github_token: GitHub token for authentication

        Returns:
            Dict containing comparison results

        Raises:
            ComparisonError: If comparison fails
        """
        payload = {
            "base_repo_url": base_repo_url,
            "head_repo_url": head_repo_url,
            "base_branch": base_branch,
            "head_branch": head_branch,
            "github_token": github_token,
        }

        try:
            start_time = time.time()
            logger.info(f"Comparing repositories: {base_repo_url} vs {head_repo_url}")
            
            response = self.session.post(
                f"{self.base_url}/compare",
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
            )
            
            if response.status_code != 200:
                self._handle_response_error(response, "comparison")
                
            result = response.json()
            
            elapsed_time = time.time() - start_time
            logger.info(f"Comparison completed in {elapsed_time:.2f} seconds")
            
            return result
        except requests.RequestException as e:
            logger.error(f"Comparison request failed: {str(e)}")
            raise ComparisonError(f"Comparison request failed: {str(e)}")

    def analyze_pr(
        self,
        repo_url: str,
        pr_number: int,
        github_token: Optional[str] = None,
        detailed: bool = True,
        post_comment: bool = False,
    ) -> Dict[str, Any]:
        """
        Analyze a pull request.

        Args:
            repo_url: URL of the repository
            pr_number: PR number to analyze
            github_token: GitHub token for authentication
            detailed: Whether to perform detailed analysis
            post_comment: Whether to post a comment with the analysis results

        Returns:
            Dict containing PR analysis results

        Raises:
            PRAnalysisError: If PR analysis fails
        """
        payload = {
            "repo_url": repo_url,
            "pr_number": pr_number,
            "github_token": github_token,
            "detailed": detailed,
            "post_comment": post_comment,
        }

        try:
            start_time = time.time()
            logger.info(f"Analyzing PR: {repo_url}#{pr_number}")
            
            response = self.session.post(
                f"{self.base_url}/analyze-pr",
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
            )
            
            if response.status_code != 200:
                self._handle_response_error(response, "PR analysis")
                
            result = response.json()
            
            elapsed_time = time.time() - start_time
            logger.info(f"PR analysis completed in {elapsed_time:.2f} seconds")
            
            return result
        except requests.RequestException as e:
            logger.error(f"PR analysis request failed: {str(e)}")
            raise PRAnalysisError(f"PR analysis request failed: {str(e)}")

    def get_server_metrics(self) -> Dict[str, Any]:
        """
        Get server metrics.

        Returns:
            Dict containing server metrics

        Raises:
            WSLClientError: If the request fails
        """
        try:
            response = self.session.get(
                f"{self.base_url}/metrics", 
                headers=self.headers,
                timeout=self.timeout,
            )
            
            if response.status_code != 200:
                self._handle_response_error(response, "get metrics")
                
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Get metrics failed: {str(e)}")
            raise WSLClientError(f"Get metrics failed: {str(e)}")

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
        markdown += f"**Execution Time**: {results.get('execution_time', 0):.2f} seconds\n\n"

        for result in results["validation_results"]:
            markdown += f"## {result['category'].title()}\n\n"
            markdown += f"**Score**: {result['score']:.2f}/10\n\n"

            if result["issues"]:
                markdown += "### Issues\n\n"
                for issue in result["issues"]:
                    markdown += f"- **{issue['title']}**: {issue['description']}\n"
                markdown += "\n"

            if result["recommendations"]:
                markdown += "### Recommendations\n\n"
                for recommendation in result["recommendations"]:
                    markdown += f"- {recommendation}\n"
                markdown += "\n"

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
        markdown += f"**Execution Time**: {results.get('execution_time', 0):.2f} seconds\n\n"

        if results["file_changes"]:
            markdown += "## File Changes\n\n"
            for file, change in results["file_changes"].items():
                markdown += f"- **{file}**: {change}\n"
            markdown += "\n"

        if results["function_changes"]:
            markdown += "## Function Changes\n\n"
            for func, change in results["function_changes"].items():
                markdown += f"- **{func}**: {change}\n"
            markdown += "\n"

        if results["complexity_changes"]:
            markdown += "## Complexity Changes\n\n"
            for file, change in results["complexity_changes"].items():
                markdown += f"- **{file}**: {change:+.2f}\n"
            markdown += "\n"

        if results["risk_assessment"]:
            markdown += "## Risk Assessment\n\n"
            for category, risk in results["risk_assessment"].items():
                markdown += f"- **{category}**: {risk}\n"
            markdown += "\n"

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
        markdown += f"**Execution Time**: {results.get('execution_time', 0):.2f} seconds\n\n"

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
