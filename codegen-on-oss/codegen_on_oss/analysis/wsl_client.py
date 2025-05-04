"""
WSL2 Client for Code Validation

This module provides a client for interacting with the WSL2 server
for code validation, repository comparison, and PR analysis.
"""

import json
import logging
import os
import requests
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

logger = logging.getLogger(__name__)


class WSLClient:
    """
    Client for interacting with the WSL2 server for code validation.
    """

    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        """
        Initialize a new WSLClient.

        Args:
            base_url: Base URL of the WSL2 server
            api_key: Optional API key for authentication
        """
        self.base_url = base_url
        self.api_key = api_key or os.getenv("CODEGEN_API_KEY", "")
        self.headers = {}
        
        if self.api_key:
            self.headers["X-API-Key"] = self.api_key

    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the WSL2 server.

        Returns:
            Dict containing the health status
        """
        response = requests.get(f"{self.base_url}/health", headers=self.headers)
        response.raise_for_status()
        return response.json()

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
        
        response = requests.post(
            f"{self.base_url}/validate",
            headers=self.headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()

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
        
        response = requests.post(
            f"{self.base_url}/compare",
            headers=self.headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()

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
        
        response = requests.post(
            f"{self.base_url}/analyze-pr",
            headers=self.headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()

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
        markdown = f"# Repository Comparison Results\n\n"
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

