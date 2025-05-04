#!/usr/bin/env python3
"""
Example script demonstrating the use of the unified API for codegen-on-oss.

This script shows how to use the UnifiedAPI class to perform various code analysis
tasks, including repository analysis, commit analysis, PR analysis, and code integrity
validation.
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Optional

# Add the parent directory to the path so we can import the codegen_on_oss package
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from codegen_on_oss.api.unified_api import (
    UnifiedAPI,
    analyze_repository,
    analyze_commit,
    analyze_pull_request,
    compare_branches,
    create_snapshot,
    compare_snapshots,
    analyze_code_integrity,
    batch_analyze_repositories,
)


def analyze_repo_example(repo_url: str, output_dir: str, github_token: Optional[str] = None) -> None:
    """
    Example of analyzing a repository.

    Args:
        repo_url: URL of the repository to analyze
        output_dir: Directory to save the analysis results
        github_token: Optional GitHub token for accessing private repositories
    """
    print(f"Analyzing repository: {repo_url}")

    # Method 1: Using the convenience function
    results = analyze_repository(
        repo_url=repo_url,
        output_path=os.path.join(output_dir, "repo_analysis.json"),
        include_integrity=True,
        github_token=github_token,
    )

    # Method 2: Using the UnifiedAPI class
    api = UnifiedAPI(github_token=github_token)
    results = api.analyze_repository(
        repo_url=repo_url,
        output_path=os.path.join(output_dir, "repo_analysis_api.json"),
        include_integrity=True,
    )

    # Print a summary of the results
    print("\nRepository Analysis Summary:")
    print(f"Files: {results['summary']['file_count']}")
    print(f"Functions: {results['summary']['function_count']}")
    print(f"Classes: {results['summary']['class_count']}")
    print(f"Average Complexity: {results['complexity']['average_complexity']}")

    if "integrity" in results:
        print(f"Issues Found: {len(results['integrity']['issues'])}")
        if results['integrity']['issues']:
            print("\nTop Issues:")
            for i, issue in enumerate(results['integrity']['issues'][:5]):
                print(f"{i+1}. {issue['title']} - {issue['file']}:{issue['line']}")


def analyze_commit_example(
    repo_url: str, commit_hash: str, base_commit: Optional[str], output_dir: str, github_token: Optional[str] = None
) -> None:
    """
    Example of analyzing a commit.

    Args:
        repo_url: URL of the repository to analyze
        commit_hash: Hash of the commit to analyze
        base_commit: Optional base commit to compare against
        output_dir: Directory to save the analysis results
        github_token: Optional GitHub token for accessing private repositories
    """
    print(f"Analyzing commit: {commit_hash}")

    # Method 1: Using the convenience function
    results = analyze_commit(
        repo_url=repo_url,
        commit_hash=commit_hash,
        base_commit=base_commit,
        output_path=os.path.join(output_dir, "commit_analysis.json"),
        github_token=github_token,
    )

    # Print a summary of the results
    print("\nCommit Analysis Summary:")
    print(f"Is Properly Implemented: {results['quality_assessment']['is_properly_implemented']}")
    print(f"Score: {results['quality_assessment']['score']}")
    print(f"Overall Assessment: {results['quality_assessment']['overall_assessment']}")
    print(f"Files Added: {len(results['changes']['files_added'])}")
    print(f"Files Modified: {len(results['changes']['files_modified'])}")
    print(f"Files Removed: {len(results['changes']['files_removed'])}")
    print(f"Issues Found: {len(results['issues'])}")

    if results['issues']:
        print("\nTop Issues:")
        for i, issue in enumerate(results['issues'][:5]):
            print(f"{i+1}. {issue['title']} - {issue['file']}:{issue['line']}")


def analyze_pr_example(
    repo_url: str, pr_number: int, output_dir: str, github_token: Optional[str] = None
) -> None:
    """
    Example of analyzing a pull request.

    Args:
        repo_url: URL of the repository to analyze
        pr_number: Number of the pull request to analyze
        output_dir: Directory to save the analysis results
        github_token: GitHub token for accessing private repositories
    """
    if not github_token:
        print("GitHub token is required for PR analysis")
        return

    print(f"Analyzing PR #{pr_number}")

    # Method 1: Using the convenience function
    results = analyze_pull_request(
        repo_url=repo_url,
        pr_number=pr_number,
        output_path=os.path.join(output_dir, "pr_analysis.json"),
        github_token=github_token,
    )

    # Print a summary of the results
    print("\nPR Analysis Summary:")
    print(f"Is Properly Implemented: {results['quality_assessment']['is_properly_implemented']}")
    print(f"Score: {results['quality_assessment']['score']}")
    print(f"Overall Assessment: {results['quality_assessment']['overall_assessment']}")
    print(f"Files Added: {len(results['changes']['files_added'])}")
    print(f"Files Modified: {len(results['changes']['files_modified'])}")
    print(f"Files Removed: {len(results['changes']['files_removed'])}")
    print(f"Issues Found: {len(results['issues'])}")

    if results['issues']:
        print("\nTop Issues:")
        for i, issue in enumerate(results['issues'][:5]):
            print(f"{i+1}. {issue['title']} - {issue['file']}:{issue['line']}")


def compare_branches_example(
    repo_url: str, base_branch: str, head_branch: str, output_dir: str, github_token: Optional[str] = None
) -> None:
    """
    Example of comparing two branches.

    Args:
        repo_url: URL of the repository to analyze
        base_branch: Base branch for comparison
        head_branch: Head branch for comparison
        output_dir: Directory to save the comparison results
        github_token: Optional GitHub token for accessing private repositories
    """
    print(f"Comparing branches: {base_branch} -> {head_branch}")

    # Method 1: Using the convenience function
    results = compare_branches(
        repo_url=repo_url,
        base_branch=base_branch,
        head_branch=head_branch,
        output_path=os.path.join(output_dir, "branch_comparison.json"),
        github_token=github_token,
    )

    # Print a summary of the results
    print("\nBranch Comparison Summary:")
    print(f"Summary: {results['summary']}")
    print(f"Files Added: {len(results['changes']['files_added'])}")
    print(f"Files Modified: {len(results['changes']['files_modified'])}")
    print(f"Files Removed: {len(results['changes']['files_removed'])}")


def snapshot_example(
    repo_url: str, output_dir: str, github_token: Optional[str] = None
) -> None:
    """
    Example of creating and comparing snapshots.

    Args:
        repo_url: URL of the repository to snapshot
        output_dir: Directory to save the snapshots and comparison results
        github_token: Optional GitHub token for accessing private repositories
    """
    print(f"Creating snapshots for repository: {repo_url}")

    # Create snapshots for two branches
    snapshot_id_1 = create_snapshot(
        repo_url=repo_url,
        branch="main",
        snapshot_name="main-snapshot",
        output_path=os.path.join(output_dir, "main_snapshot.json"),
        github_token=github_token,
    )

    snapshot_id_2 = create_snapshot(
        repo_url=repo_url,
        branch="develop",
        snapshot_name="develop-snapshot",
        output_path=os.path.join(output_dir, "develop_snapshot.json"),
        github_token=github_token,
    )

    print(f"Created snapshots: {snapshot_id_1} and {snapshot_id_2}")

    # Compare the snapshots
    results = compare_snapshots(
        snapshot_id_1=os.path.join(output_dir, "main_snapshot.json"),
        snapshot_id_2=os.path.join(output_dir, "develop_snapshot.json"),
        output_path=os.path.join(output_dir, "snapshot_comparison.json"),
        github_token=github_token,
    )

    # Print a summary of the results
    print("\nSnapshot Comparison Summary:")
    print(f"Summary: {results['summary']}")
    print(f"Files Added: {len(results['changes']['files_added'])}")
    print(f"Files Modified: {len(results['changes']['files_modified'])}")
    print(f"Files Removed: {len(results['changes']['files_removed'])}")


def code_integrity_example(
    repo_url: str, output_dir: str, github_token: Optional[str] = None
) -> None:
    """
    Example of analyzing code integrity.

    Args:
        repo_url: URL of the repository to analyze
        output_dir: Directory to save the analysis results
        github_token: Optional GitHub token for accessing private repositories
    """
    print(f"Analyzing code integrity for repository: {repo_url}")

    # Define custom rules
    rules = [
        {"type": "complexity", "max_value": 10},
        {"type": "line_length", "max_value": 100},
        {"type": "function_length", "max_value": 50},
        {"type": "class_length", "max_value": 200},
        {"type": "parameter_count", "max_value": 5},
    ]

    # Method 1: Using the convenience function
    results = analyze_code_integrity(
        repo_url=repo_url,
        rules=rules,
        output_path=os.path.join(output_dir, "code_integrity.json"),
        github_token=github_token,
    )

    # Print a summary of the results
    print("\nCode Integrity Analysis Summary:")
    print(f"Issues Found: {len(results['issues'])}")
    print(f"Summary: {results['summary']}")

    if results['issues']:
        print("\nTop Issues:")
        for i, issue in enumerate(results['issues'][:5]):
            print(f"{i+1}. {issue['title']} - {issue['file']}:{issue['line']}")


def batch_analysis_example(
    repo_urls: List[str], output_dir: str, github_token: Optional[str] = None
) -> None:
    """
    Example of batch analyzing multiple repositories.

    Args:
        repo_urls: List of repository URLs to analyze
        output_dir: Directory to save the analysis results
        github_token: Optional GitHub token for accessing private repositories
    """
    print(f"Batch analyzing {len(repo_urls)} repositories")

    # Method 1: Using the convenience function
    results = batch_analyze_repositories(
        repo_urls=repo_urls,
        output_dir=output_dir,
        include_integrity=True,
        github_token=github_token,
    )

    # Print a summary of the results
    print("\nBatch Analysis Summary:")
    for repo_url, result in results.items():
        if "error" in result:
            print(f"{repo_url}: Error - {result['error']}")
        else:
            print(f"{repo_url}: {result['summary']['file_count']} files, {result['summary']['function_count']} functions")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Unified API Example")
    parser.add_argument("--repo", required=True, help="URL of the repository to analyze")
    parser.add_argument("--output-dir", default="output", help="Directory to save the analysis results")
    parser.add_argument("--github-token", help="GitHub token for accessing private repositories")
    parser.add_argument("--commit", help="Commit hash to analyze")
    parser.add_argument("--base-commit", help="Base commit to compare against")
    parser.add_argument("--pr", type=int, help="PR number to analyze")
    parser.add_argument("--base-branch", default="main", help="Base branch for comparison")
    parser.add_argument("--head-branch", default="develop", help="Head branch for comparison")
    parser.add_argument("--batch", action="store_true", help="Perform batch analysis")
    parser.add_argument("--batch-repos", nargs="+", help="List of repository URLs for batch analysis")
    parser.add_argument("--example", choices=["repo", "commit", "pr", "branches", "snapshot", "integrity", "batch"], default="repo", help="Example to run")

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Run the selected example
    if args.example == "repo":
        analyze_repo_example(args.repo, args.output_dir, args.github_token)
    elif args.example == "commit":
        if not args.commit:
            print("Commit hash is required for commit analysis")
            return
        analyze_commit_example(args.repo, args.commit, args.base_commit, args.output_dir, args.github_token)
    elif args.example == "pr":
        if not args.pr:
            print("PR number is required for PR analysis")
            return
        analyze_pr_example(args.repo, args.pr, args.output_dir, args.github_token)
    elif args.example == "branches":
        compare_branches_example(args.repo, args.base_branch, args.head_branch, args.output_dir, args.github_token)
    elif args.example == "snapshot":
        snapshot_example(args.repo, args.output_dir, args.github_token)
    elif args.example == "integrity":
        code_integrity_example(args.repo, args.output_dir, args.github_token)
    elif args.example == "batch":
        if not args.batch_repos:
            print("List of repository URLs is required for batch analysis")
            return
        batch_analysis_example(args.batch_repos, args.output_dir, args.github_token)


if __name__ == "__main__":
    main()

