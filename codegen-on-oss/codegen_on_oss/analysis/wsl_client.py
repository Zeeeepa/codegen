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
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class WSLClient:
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None,
                 timeout: int = 60, max_retries: int = 3, retry_delay: int = 5,
                 pool_connections: int = 10, pool_maxsize: int = 10):
        self.session = requests.Session()
        retry_strategy = Retry(total=max_retries, backoff_factor=retry_delay,
                             status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=pool_connections,
                            pool_maxsize=pool_maxsize)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)


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
        retry_delay: int = 5
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

        logger.info(f"Initialized WSL client for server at {base_url}")

    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to the WSL2 server with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Optional request data
            params: Optional query parameters

        Returns:
            Response data as dictionary

        Raises:
            RequestException: If the request fails after all retries
        """
        url = f"{self.base_url}{endpoint}"
        retries = 0
        last_error = None

        while retries <= self.max_retries:
            try:
                logger.debug(f"Making {method} request to {url}")
                
                if method.upper() == "GET":
                    response = requests.get(
                        url, 
                        headers=self.headers, 
                        params=params,
                        timeout=self.timeout
                    )
                elif method.upper() == "POST":
                    response = requests.post(
                        url, 
                        headers=self.headers, 
                        json=data,
                        timeout=self.timeout
                    )
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response.json()
            
            except (ConnectionError, Timeout) as e:
                retries += 1
                last_error = e
                if retries <= self.max_retries:
                    logger.warning(
                        f"Request to {url} failed with error: {str(e)}. "
                        f"Retrying ({retries}/{self.max_retries}) in {self.retry_delay} seconds..."
                    )
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Request to {url} failed after {self.max_retries} retries: {str(e)}")
                    raise
            
            except RequestException as e:
                logger.error(f"Request to {url} failed: {str(e)}")
                raise

        if last_error:
            raise last_error
        raise RequestException(f"Request to {url} failed for unknown reasons")

    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the WSL2 server.

        Returns:
            Dict containing the health status
        """
        try:
            return self._make_request("GET", "/health")
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)}

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
        """
        payload = {
            "repo_url": repo_url,
            "branch": branch,
            "categories": categories or ["code_quality", "security", "maintainability"],
            "github_token": github_token,
        }

        logger.info(f"Validating codebase: {repo_url} ({branch})")
        try:
            result = self._make_request("POST", "/validate", data=payload)
            
            # Check for error in response
            if result.get("error"):
                logger.error(f"Validation error: {result['error']}")
            else:
                logger.info(f"Validation completed with overall score: {result.get('overall_score', 0):.2f}/10")
            
            return result
        except Exception as e:
            logger.error(f"Validation request failed: {str(e)}")
            # Return a structured error response
            return {
                "repo_url": repo_url,
                "branch": branch,
                "validation_results": [],
                "overall_score": 0.0,
                "summary": f"Validation failed: {str(e)}",
                "error": str(e),
            }

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
        """
        payload = {
            "base_repo_url": base_repo_url,
            "head_repo_url": head_repo_url,
            "base_branch": base_branch,
            "head_branch": head_branch,
            "github_token": github_token,
        }

        logger.info(f"Comparing repositories: {base_repo_url} ({base_branch}) vs {head_repo_url} ({head_branch})")
        try:
            result = self._make_request("POST", "/compare", data=payload)
            
            # Check for error in response
            if result.get("error"):
                logger.error(f"Comparison error: {result['error']}")
            else:
                logger.info(f"Comparison completed successfully")
                logger.info(f"File changes: {len(result.get('file_changes', {}))}")
                logger.info(f"Function changes: {len(result.get('function_changes', {}))}")
            
            return result
        except Exception as e:
            logger.error(f"Comparison request failed: {str(e)}")
            # Return a structured error response
            return {
                "base_repo_url": base_repo_url,
                "head_repo_url": head_repo_url,
                "file_changes": {},
                "function_changes": {},
                "complexity_changes": {},
                "risk_assessment": {},
                "summary": f"Comparison failed: {str(e)}",
                "error": str(e),
            }

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
        """
        payload = {
            "repo_url": repo_url,
            "pr_number": pr_number,
            "github_token": github_token,
            "detailed": detailed,
            "post_comment": post_comment,
        }

        logger.info(f"Analyzing PR: {repo_url}#{pr_number}")
        try:
            result = self._make_request("POST", "/analyze-pr", data=payload)
            
            # Check for error in response
            if result.get("error"):
                logger.error(f"PR analysis error: {result['error']}")
            else:
                logger.info(f"PR analysis completed with code quality score: {result.get('code_quality_score', 0):.2f}/10")
                logger.info(f"Issues found: {len(result.get('issues_found', []))}")
            
            return result
        except Exception as e:
            logger.error(f"PR analysis request failed: {str(e)}")
            # Return a structured error response
            return {
                "repo_url": repo_url,
                "pr_number": pr_number,
                "analysis_results": {},
                "code_quality_score": 0.0,
                "issues_found": [],
                "recommendations": [],
                "summary": f"Analysis failed: {str(e)}",
                "error": str(e),
            }

    def format_validation_results_markdown(self, results: Dict[str, Any]) -> str:
        """
        Format validation results as Markdown.

        Args:
            results: Validation results from validate_codebase

        Returns:
            Markdown-formatted string
        """
        # Check for error
        if results.get("error"):
            return f"# Validation Error\n\n**Error**: {results['error']}\n\n"

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
        # Check for error
        if results.get("error"):
            return f"# Comparison Error\n\n**Error**: {results['error']}\n\n"

        markdown = "# Repository Comparison Results\n\n"
        markdown += f"**Base**: {results['base_repo_url']}\n"
        markdown += f"**Head**: {results['head_repo_url']}\n\n"
        markdown += f"**Summary**: {results['summary']}\n\n"

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
        # Check for error
        if results.get("error"):
            return f"# PR Analysis Error\n\n**Error**: {results['error']}\n\n"

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

        return markdown

    def save_results_to_file(
        self, 
        results: Dict[str, Any], 
        filename: str,
        format: str = "json"
    ) -> str:
        """
        Save results to a file.

        Args:
            results: Results to save
            filename: Filename to save to
            format: Format to save in (json or markdown)

        Returns:
            Path to the saved file
        """
        filepath = Path(filename)

        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Determine content based on format
        if format.lower() == "markdown":
            # Determine the type of results and format accordingly
            if "validation_results" in results:
                content = self.format_validation_results_markdown(results)
            elif "file_changes" in results:
                content = self.format_comparison_results_markdown(results)
            elif "analysis_results" in results:
                content = self.format_pr_analysis_markdown(results)
            else:
                content = f"# Results\n\n```json\n{json.dumps(results, indent=2)}\n```\n"
            
            # Save as markdown
            with open(filepath, "w") as f:
                f.write(content)
        else:
            # Save as JSON
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

        if not filepath.exists():
            logger.error(f"File not found: {filepath}")
            raise FileNotFoundError(f"File not found: {filepath}")

        # Load results from JSON
        try:
            with open(filepath, "r") as f:
                results = json.load(f)
            
            logger.info(f"Results loaded from {filepath}")
            return results
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from {filepath}: {str(e)}")
            raise
