"""
Example script demonstrating how to use the code analysis server.

This script shows how to start the server and make requests to analyze
repositories, commits, branches, and pull requests.
"""

import os
import sys
import argparse
import requests
import json
from typing import Dict, Any, Optional

from codegen_on_oss.analysis.server import run_server

def print_json(data: Dict[str, Any]) -> None:
    """Print JSON data in a formatted way."""
    print(json.dumps(data, indent=2))

def analyze_repo(base_url: str, repo_url: str) -> Optional[Dict[str, Any]]:
    """
    Analyze a repository.
    
    Args:
        base_url: Base URL of the analysis server
        repo_url: URL of the repository to analyze
        
    Returns:
        Analysis result or None if an error occurred
    """
    print(f"Analyzing repository: {repo_url}")
    
    try:
        response = requests.post(
            f"{base_url}/analyze_repo",
            json={"repo_url": repo_url}
        )
        response.raise_for_status()
        result = response.json()
        
        print("\nAnalysis result:")
        print_json(result)
        
        return result
    except Exception as e:
        print(f"Error analyzing repository: {e}")
        return None

def analyze_commit(base_url: str, repo_url: str, commit_hash: str) -> Optional[Dict[str, Any]]:
    """
    Analyze a commit in a repository.
    
    Args:
        base_url: Base URL of the analysis server
        repo_url: URL of the repository to analyze
        commit_hash: Hash of the commit to analyze
        
    Returns:
        Analysis result or None if an error occurred
    """
    print(f"Analyzing commit {commit_hash} in repository {repo_url}")
    
    try:
        response = requests.post(
            f"{base_url}/analyze_commit",
            json={
                "repo_url": repo_url,
                "commit_hash": commit_hash
            }
        )
        response.raise_for_status()
        result = response.json()
        
        print("\nAnalysis result:")
        print_json(result)
        
        return result
    except Exception as e:
        print(f"Error analyzing commit: {e}")
        return None

def compare_branches(base_url: str, repo_url: str, base_branch: str, compare_branch: str) -> Optional[Dict[str, Any]]:
    """
    Compare two branches in a repository.
    
    Args:
        base_url: Base URL of the analysis server
        repo_url: URL of the repository to analyze
        base_branch: Base branch name
        compare_branch: Branch to compare against the base branch
        
    Returns:
        Comparison result or None if an error occurred
    """
    print(f"Comparing branches {base_branch} and {compare_branch} in repository {repo_url}")
    
    try:
        response = requests.post(
            f"{base_url}/compare_branches",
            json={
                "repo_url": repo_url,
                "base_branch": base_branch,
                "compare_branch": compare_branch
            }
        )
        response.raise_for_status()
        result = response.json()
        
        print("\nComparison result:")
        print_json(result)
        
        return result
    except Exception as e:
        print(f"Error comparing branches: {e}")
        return None

def analyze_pr(base_url: str, repo_url: str, pr_number: int) -> Optional[Dict[str, Any]]:
    """
    Analyze a pull request in a repository.
    
    Args:
        base_url: Base URL of the analysis server
        repo_url: URL of the repository to analyze
        pr_number: Pull request number to analyze
        
    Returns:
        Analysis result or None if an error occurred
    """
    print(f"Analyzing PR #{pr_number} in repository {repo_url}")
    
    try:
        response = requests.post(
            f"{base_url}/analyze_pr",
            json={
                "repo_url": repo_url,
                "pr_number": pr_number
            }
        )
        response.raise_for_status()
        result = response.json()
        
        print("\nAnalysis result:")
        print_json(result)
        
        return result
    except Exception as e:
        print(f"Error analyzing PR: {e}")
        return None

def main():
    """Main function to run the example."""
    parser = argparse.ArgumentParser(description="Code Analysis Server Example")
    parser.add_argument("--start-server", action="store_true", help="Start the analysis server")
    parser.add_argument("--host", default="localhost", help="Server host (default: localhost)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--analyze-repo", help="Analyze a repository")
    parser.add_argument("--analyze-commit", nargs=2, metavar=("REPO_URL", "COMMIT_HASH"), help="Analyze a commit")
    parser.add_argument("--compare-branches", nargs=3, metavar=("REPO_URL", "BASE_BRANCH", "COMPARE_BRANCH"), help="Compare two branches")
    parser.add_argument("--analyze-pr", nargs=2, metavar=("REPO_URL", "PR_NUMBER"), help="Analyze a pull request")
    
    args = parser.parse_args()
    
    # Start the server if requested
    if args.start_server:
        print(f"Starting analysis server on {args.host}:{args.port}")
        run_server(host=args.host, port=args.port)
        return
    
    # Base URL for API requests
    base_url = f"http://{args.host}:{args.port}"
    
    # Analyze a repository
    if args.analyze_repo:
        analyze_repo(base_url, args.analyze_repo)
    
    # Analyze a commit
    elif args.analyze_commit:
        repo_url, commit_hash = args.analyze_commit
        analyze_commit(base_url, repo_url, commit_hash)
    
    # Compare branches
    elif args.compare_branches:
        repo_url, base_branch, compare_branch = args.compare_branches
        compare_branches(base_url, repo_url, base_branch, compare_branch)
    
    # Analyze a pull request
    elif args.analyze_pr:
        repo_url, pr_number = args.analyze_pr
        analyze_pr(base_url, repo_url, int(pr_number))
    
    # If no action specified, print help
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
"""

