"""
Enhanced Analysis Server Example

This script demonstrates how to use the enhanced analysis server for PR validation
and codebase analysis.
"""

import argparse
import codegen
import json
from typing import Any, Dict, List, Optional

import requests


class ProjectManager:
    """Manages projects for the enhanced analysis server."""

    def __init__(self, server_url: str = "http://localhost:8000"):
        """
        Initialize a new ProjectManager.
        
        Args:
            server_url: The URL of the enhanced analysis server
        """
        self.server_url = server_url.rstrip("/")
    
    def create_project(self, name: str, repo_url: str) -> Dict[str, Any]:
        """
        Create a new project.
        
        Args:
            name: The name of the project
            repo_url: The URL of the repository
            
        Returns:
            Dict containing the project information
        """
        endpoint = f"{self.server_url}/projects"
        payload = {
            "name": name,
            "repo_url": repo_url
        }
        
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Get project information.
        
        Args:
            project_id: The ID of the project
            
        Returns:
            Dict containing the project information
        """
        endpoint = f"{self.server_url}/projects/{project_id}"
        
        response = requests.get(endpoint)
        response.raise_for_status()
        
        return response.json()
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """
        List all projects.
        
        Returns:
            List of dicts containing project information
        """
        endpoint = f"{self.server_url}/projects"
        
        response = requests.get(endpoint)
        response.raise_for_status()
        
        return response.json()
    
    def analyze_pr(self, project_id: str, pr_number: int) -> Dict[str, Any]:
        """
        Analyze a pull request.
        
        Args:
            project_id: The ID of the project
            pr_number: The number of the pull request
            
        Returns:
            Dict containing the analysis results
        """
        endpoint = f"{self.server_url}/projects/{project_id}/prs/{pr_number}/analyze"
        
        response = requests.post(endpoint)
        response.raise_for_status()
        
        return response.json()
    
    def get_pr_analysis(self, project_id: str, pr_number: int) -> Dict[str, Any]:
        """
        Get the analysis results for a pull request.
        
        Args:
            project_id: The ID of the project
            pr_number: The number of the pull request
            
        Returns:
            Dict containing the analysis results
        """
        endpoint = f"{self.server_url}/projects/{project_id}/prs/{pr_number}/analysis"
        
        response = requests.get(endpoint)
        response.raise_for_status()
        
        return response.json()


@codegen.function("codegen-on-oss-enhanced-server")
def run(repo_url: str, pr_number: Optional[int] = None, server_url: str = "http://localhost:8000"):
    """
    Run an analysis using the enhanced analysis server.
    
    This function:
    1. Creates a project manager for the enhanced analysis server
    2. Creates a project for the repository
    3. If a PR number is provided, analyzes the PR
    4. Returns the analysis results
    
    Args:
        repo_url: The URL of the repository to analyze
        pr_number: Optional PR number to analyze
        server_url: The URL of the enhanced analysis server
        
    Returns:
        dict: The analysis results
    """
    manager = ProjectManager(server_url)
    
    # Extract project name from repo URL
    project_name = repo_url.split("/")[-1].split(".")[0]
    
    print(f"Creating project '{project_name}' for repository {repo_url}...")
    project = manager.create_project(project_name, repo_url)
    project_id = project["id"]
    
    print(f"Project created with ID: {project_id}")
    
    if pr_number:
        print(f"Analyzing PR #{pr_number}...")
        manager.analyze_pr(project_id, pr_number)
        
        print("Waiting for analysis to complete...")
        # In a real application, you would poll for completion
        
        print("Analysis complete! Retrieving results...")
        results = manager.get_pr_analysis(project_id, pr_number)
    else:
        print("No PR number provided. Project created but no analysis performed.")
        results = {"project_id": project_id, "message": "Project created successfully"}
    
    return results


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Enhanced Analysis Server Example")
    parser.add_argument("--repo", required=True, help="Repository URL")
    parser.add_argument("--pr", type=int, help="Pull request number to analyze")
    parser.add_argument("--server", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--output", help="Output file for analysis results (JSON)")
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    results = run(args.repo, args.pr, args.server)
    
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(results, indent=2))

