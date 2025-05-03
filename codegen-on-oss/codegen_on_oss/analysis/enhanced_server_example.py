"""
Enhanced Server Example

This script demonstrates how to use the enhanced code analysis server
for PR validation and codebase analysis.
"""

import os
import sys
import argparse
import requests
import json
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from codegen_on_oss.analysis.server import run_server

def print_json(data: Dict[str, Any]) -> None:
    """Print JSON data in a formatted way."""
    print(json.dumps(data, indent=2))

def register_project(base_url: str, repo_url: str, name: str, description: Optional[str] = None,
                    default_branch: str = "main", webhook_url: Optional[str] = None,
                    github_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Register a project for analysis.
    
    Args:
        base_url: Base URL of the analysis server
        repo_url: URL of the repository to register
        name: Name of the project
        description: Optional description of the project
        default_branch: Default branch of the repository
        webhook_url: Optional webhook URL to notify when analysis is complete
        github_token: Optional GitHub token for private repositories
        
    Returns:
        Project information or None if an error occurred
    """
    print(f"Registering project {name} for analysis")
    
    try:
        response = requests.post(
            f"{base_url}/register_project",
            json={
                "repo_url": repo_url,
                "name": name,
                "description": description,
                "default_branch": default_branch,
                "webhook_url": webhook_url,
                "github_token": github_token
            }
        )
        response.raise_for_status()
        result = response.json()
        
        print("\nProject registration result:")
        print_json(result)
        
        return result
    except Exception as e:
        print(f"Error registering project: {e}")
        return None

def register_webhook(base_url: str, project_id: str, webhook_url: str,
                    events: List[str] = ["pr", "commit", "branch"],
                    secret: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Register a webhook for a project.
    
    Args:
        base_url: Base URL of the analysis server
        project_id: ID of the project to register the webhook for
        webhook_url: URL to send webhook notifications to
        events: Events to trigger the webhook
        secret: Optional secret to sign webhook payloads with
        
    Returns:
        Webhook information or None if an error occurred
    """
    print(f"Registering webhook for project {project_id}")
    
    try:
        response = requests.post(
            f"{base_url}/register_webhook",
            json={
                "project_id": project_id,
                "webhook_url": webhook_url,
                "events": events,
                "secret": secret
            }
        )
        response.raise_for_status()
        result = response.json()
        
        print("\nWebhook registration result:")
        print_json(result)
        
        return result
    except Exception as e:
        print(f"Error registering webhook: {e}")
        return None

def analyze_function(base_url: str, repo_url: str, function_name: str,
                    branch: Optional[str] = None, commit: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Analyze a specific function.
    
    Args:
        base_url: Base URL of the analysis server
        repo_url: URL of the repository to analyze
        function_name: Fully qualified name of the function to analyze
        branch: Branch to analyze (default: default branch)
        commit: Commit to analyze (default: latest commit)
        
    Returns:
        Analysis result or None if an error occurred
    """
    print(f"Analyzing function {function_name} in repository {repo_url}")
    
    try:
        response = requests.post(
            f"{base_url}/analyze_function",
            json={
                "repo_url": repo_url,
                "function_name": function_name,
                "branch": branch,
                "commit": commit
            }
        )
        response.raise_for_status()
        result = response.json()
        
        print("\nFunction analysis result:")
        print_json(result)
        
        return result
    except Exception as e:
        print(f"Error analyzing function: {e}")
        return None

def analyze_feature(base_url: str, repo_url: str, feature_path: str,
                   branch: Optional[str] = None, commit: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Analyze a specific feature (file or directory).
    
    Args:
        base_url: Base URL of the analysis server
        repo_url: URL of the repository to analyze
        feature_path: Path to the feature to analyze
        branch: Branch to analyze (default: default branch)
        commit: Commit to analyze (default: latest commit)
        
    Returns:
        Analysis result or None if an error occurred
    """
    print(f"Analyzing feature {feature_path} in repository {repo_url}")
    
    try:
        response = requests.post(
            f"{base_url}/analyze_feature",
            json={
                "repo_url": repo_url,
                "feature_path": feature_path,
                "branch": branch,
                "commit": commit
            }
        )
        response.raise_for_status()
        result = response.json()
        
        print("\nFeature analysis result:")
        print_json(result)
        
        return result
    except Exception as e:
        print(f"Error analyzing feature: {e}")
        return None

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

def run_pr_validation_workflow(base_url: str, repo_url: str, pr_number: int) -> None:
    """
    Run a complete PR validation workflow.
    
    Args:
        base_url: Base URL of the analysis server
        repo_url: URL of the repository to analyze
        pr_number: Pull request number to analyze
    """
    print(f"Running PR validation workflow for PR #{pr_number} in repository {repo_url}")
    
    # Step 1: Register the project
    project = register_project(
        base_url=base_url,
        repo_url=repo_url,
        name=f"PR Validation for {repo_url}",
        description=f"Project for validating PR #{pr_number}",
        webhook_url="http://example.com/webhook"
    )
    
    if not project:
        print("Failed to register project. Aborting workflow.")
        return
    
    # Step 2: Analyze the PR
    pr_analysis = analyze_pr(
        base_url=base_url,
        repo_url=repo_url,
        pr_number=pr_number
    )
    
    if not pr_analysis:
        print("Failed to analyze PR. Aborting workflow.")
        return
    
    # Step 3: Analyze specific features in the PR
    if pr_analysis.get("files_modified"):
        # Analyze the first modified file as a feature
        feature_path = pr_analysis["files_modified"][0]
        
        feature_analysis = analyze_feature(
            base_url=base_url,
            repo_url=repo_url,
            feature_path=feature_path
        )
        
        if feature_analysis and feature_analysis.get("functions"):
            # Analyze the first function in the feature
            function_name = feature_analysis["functions"][0]["function_name"]
            
            function_analysis = analyze_function(
                base_url=base_url,
                repo_url=repo_url,
                function_name=function_name
            )
    
    # Step 4: Print the validation summary
    print("\n" + "=" * 80)
    print(f"PR Validation Summary for PR #{pr_number} in {repo_url}")
    print("=" * 80)
    
    if pr_analysis:
        print(f"Is properly implemented: {'Yes' if pr_analysis.get('is_properly_implemented') else 'No'}")
        
        if pr_analysis.get("issues"):
            print("\nIssues:")
            for issue in pr_analysis["issues"]:
                print(f"- {issue.get('message', 'Unknown issue')}")
        
        print("\nFiles:")
        print(f"- Added: {len(pr_analysis.get('files_added', []))}")
        print(f"- Modified: {len(pr_analysis.get('files_modified', []))}")
        print(f"- Removed: {len(pr_analysis.get('files_removed', []))}")
        
        print("\nSummary:")
        print(pr_analysis.get("summary", "No summary available"))
    else:
        print("No PR analysis results available.")

def main():
    """Main function to run the example."""
    parser = argparse.ArgumentParser(description="Enhanced Code Analysis Server Example")
    parser.add_argument("--start-server", action="store_true", help="Start the analysis server")
    parser.add_argument("--host", default="localhost", help="Server host (default: localhost)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    
    # Project management
    parser.add_argument("--register-project", nargs=2, metavar=("REPO_URL", "NAME"), help="Register a project for analysis")
    parser.add_argument("--register-webhook", nargs=2, metavar=("PROJECT_ID", "WEBHOOK_URL"), help="Register a webhook")
    
    # Analysis options
    parser.add_argument("--analyze-repo", help="Analyze a repository")
    parser.add_argument("--analyze-commit", nargs=2, metavar=("REPO_URL", "COMMIT_HASH"), help="Analyze a commit")
    parser.add_argument("--compare-branches", nargs=3, metavar=("REPO_URL", "BASE_BRANCH", "COMPARE_BRANCH"), help="Compare two branches")
    parser.add_argument("--analyze-pr", nargs=2, metavar=("REPO_URL", "PR_NUMBER"), help="Analyze a pull request")
    parser.add_argument("--analyze-function", nargs=2, metavar=("REPO_URL", "FUNCTION_NAME"), help="Analyze a specific function")
    parser.add_argument("--analyze-feature", nargs=2, metavar=("REPO_URL", "FEATURE_PATH"), help="Analyze a specific feature")
    
    # Workflow options
    parser.add_argument("--pr-validation", nargs=2, metavar=("REPO_URL", "PR_NUMBER"), help="Run a PR validation workflow")
    
    # Optional parameters
    parser.add_argument("--branch", help="Branch to analyze (for function and feature analysis)")
    parser.add_argument("--commit", help="Commit to analyze (for function and feature analysis)")
    parser.add_argument("--webhook-url", help="Webhook URL for project registration")
    parser.add_argument("--github-token", help="GitHub token for private repositories")
    
    args = parser.parse_args()
    
    # Base URL for API requests
    base_url = f"http://{args.host}:{args.port}"
    
    # Start the server if requested
    if args.start_server:
        print(f"Starting analysis server on {args.host}:{args.port}")
        run_server(host=args.host, port=args.port)
        return
    
    # Register a project
    if args.register_project:
        repo_url, name = args.register_project
        register_project(
            base_url=base_url,
            repo_url=repo_url,
            name=name,
            webhook_url=args.webhook_url,
            github_token=args.github_token
        )
    
    # Register a webhook
    elif args.register_webhook:
        project_id, webhook_url = args.register_webhook
        register_webhook(
            base_url=base_url,
            project_id=project_id,
            webhook_url=webhook_url
        )
    
    # Analyze a repository
    elif args.analyze_repo:
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
    
    # Analyze a function
    elif args.analyze_function:
        repo_url, function_name = args.analyze_function
        analyze_function(
            base_url=base_url,
            repo_url=repo_url,
            function_name=function_name,
            branch=args.branch,
            commit=args.commit
        )
    
    # Analyze a feature
    elif args.analyze_feature:
        repo_url, feature_path = args.analyze_feature
        analyze_feature(
            base_url=base_url,
            repo_url=repo_url,
            feature_path=feature_path,
            branch=args.branch,
            commit=args.commit
        )
    
    # Run a PR validation workflow
    elif args.pr_validation:
        repo_url, pr_number = args.pr_validation
        run_pr_validation_workflow(
            base_url=base_url,
            repo_url=repo_url,
            pr_number=int(pr_number)
        )
    
    # If no action specified, print help
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
