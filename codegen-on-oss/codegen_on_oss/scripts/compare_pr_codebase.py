#!/usr/bin/env python3
"""
Script to compare a PR version of a codebase with the base branch.

This script provides a comprehensive comparison between a PR version of a codebase
and its base branch, including:
- File changes analysis
- Function changes analysis
- Complexity changes analysis
- Risk assessment
- Code quality comparison
- Error detection and reporting
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from codegen_on_oss.analysis.wsl_client import WSLClient


def compare_pr_codebase(
    repo_url: str,
    pr_number: int,
    github_token: Optional[str] = None,
    server_url: str = "http://localhost:8000",
    api_key: Optional[str] = None,
    output_file: Optional[str] = None,
    output_format: str = "json",
    detailed: bool = True,
) -> Dict[str, Any]:
    """
    Compare a PR version of a codebase with its base branch.

    Args:
        repo_url: URL of the repository
        pr_number: PR number to analyze
        github_token: GitHub token for authentication
        server_url: URL of the WSL2 server
        api_key: API key for authentication
        output_file: Optional file to write the results to
        output_format: Output format (json or markdown)
        detailed: Whether to perform detailed analysis

    Returns:
        Comparison results
    """
    # Initialize WSL client
    client = WSLClient(base_url=server_url, api_key=api_key)

    # Check server health
    health = client.health_check()
    if health.get("status") != "healthy":
        logger.error(f"Server is not healthy: {health.get('error', 'Unknown error')}")
        sys.exit(1)

    # Analyze PR
    logger.info(f"Analyzing PR {repo_url}#{pr_number}")
    pr_analysis = client.analyze_pr(
        repo_url=repo_url,
        pr_number=pr_number,
        github_token=github_token,
        detailed=detailed,
        post_comment=False,
    )

    # Check for error in PR analysis
    if pr_analysis.get("error"):
        logger.error(f"PR analysis error: {pr_analysis['error']}")
        if output_file:
            client.save_results_to_file(pr_analysis, output_file, format=output_format)
        return pr_analysis

    # Extract PR details for comparison
    base_repo_url = repo_url
    head_repo_url = repo_url
    base_branch = pr_analysis.get("analysis_results", {}).get("base_branch", "main")
    head_branch = pr_analysis.get("analysis_results", {}).get("head_branch", "")

    if not head_branch:
        logger.error("Could not determine head branch from PR analysis")
        return {
            "error": "Could not determine head branch from PR analysis",
            "pr_analysis": pr_analysis,
        }

    # Compare repositories
    logger.info(f"Comparing {base_repo_url}:{base_branch} with {head_repo_url}:{head_branch}")
    comparison = client.compare_repositories(
        base_repo_url=base_repo_url,
        head_repo_url=head_repo_url,
        base_branch=base_branch,
        head_branch=head_branch,
        github_token=github_token,
    )

    # Check for error in comparison
    if comparison.get("error"):
        logger.error(f"Comparison error: {comparison['error']}")
        if output_file:
            client.save_results_to_file(comparison, output_file, format=output_format)
        return comparison

    # Combine results
    results = {
        "repo_url": repo_url,
        "pr_number": pr_number,
        "base_branch": base_branch,
        "head_branch": head_branch,
        "pr_analysis": pr_analysis,
        "comparison": comparison,
        "summary": f"Comparison of PR #{pr_number} ({head_branch}) against {base_branch} completed.",
    }

    # Save results to file if requested
    if output_file:
        client.save_results_to_file(results, output_file, format=output_format)
        logger.info(f"Results saved to {output_file}")

    return results


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Compare a PR version of a codebase with its base branch"
    )

    parser.add_argument("repo_url", help="URL of the repository")
    parser.add_argument("pr_number", type=int, help="PR number to analyze")
    parser.add_argument("--github-token", help="GitHub token for authentication")
    parser.add_argument(
        "--server-url",
        default="http://localhost:8000",
        help="URL of the WSL2 server",
    )
    parser.add_argument("--api-key", help="API key for authentication")
    parser.add_argument("--output", help="Output file to save results to")
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="Output format",
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        default=True,
        help="Perform detailed analysis",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Compare PR codebase
    results = compare_pr_codebase(
        repo_url=args.repo_url,
        pr_number=args.pr_number,
        github_token=args.github_token,
        server_url=args.server_url,
        api_key=args.api_key,
        output_file=args.output,
        output_format=args.format,
        detailed=args.detailed,
    )

    # Print summary
    if args.format == "markdown":
        if results.get("error"):
            print(f"# Error\n\n{results['error']}\n")
        else:
            print(f"# PR Comparison Summary\n\n{results['summary']}\n")
            print(f"## PR Analysis\n\n{results['pr_analysis']['summary']}\n")
            print(f"## Codebase Comparison\n\n{results['comparison']['summary']}\n")
    else:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

