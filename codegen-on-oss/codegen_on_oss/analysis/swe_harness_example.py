"""
SWE Harness Agent Example

This script demonstrates how to use the SWE harness agent to analyze commits and pull requests.
"""

import argparse
import logging
import os
from typing import Optional

from codegen_on_oss.analysis.swe_harness_agent import SWEHarnessAgent
from codegen_on_oss.snapshot.codebase_snapshot import SnapshotManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def analyze_pr(
    repo_url: str,
    pr_number: int,
    github_token: Optional[str] = None,
    post_comment: bool = False,
):
    """
    Analyze a pull request and print the results.

    Args:
        repo_url: The repository URL or owner/repo string
        pr_number: The pull request number
        github_token: Optional GitHub token for private repositories
        post_comment: Whether to post a comment to the PR with the analysis results
    """
    # Create a SWE harness agent
    swe_agent = SWEHarnessAgent(github_token)

    # Analyze the PR
    logger.info(f"Analyzing PR #{pr_number} in {repo_url}")
    results = swe_agent.analyze_and_comment_on_pr(repo_url, pr_number, post_comment)

    # Print the results
    print("\n" + "=" * 80)
    print(f"PR Analysis Results for {repo_url} #{pr_number}")
    print("=" * 80)
    print(f"Quality Score: {results['quality_score']}/10.0 - {results['overall_assessment']}")
    print(f"Properly Implemented: {'Yes' if results['is_properly_implemented'] else 'No'}")

    if "issues" in results and results["issues"]:
        print("\nIssues:")
        for issue in results["issues"]:
            print(f"- {issue}")

    print("\nDetailed Report:")
    print(results["report"])

    if post_comment:
        print(
            "\nComment posted to PR:",
            "Yes" if results.get("comment_posted", False) else "No",
        )


def analyze_commit(
    repo_url: str,
    base_commit: str,
    head_commit: str,
    github_token: Optional[str] = None,
):
    """
    Analyze a commit and print the results.

    Args:
        repo_url: The repository URL or owner/repo string
        base_commit: The base commit SHA (before the changes)
        head_commit: The head commit SHA (after the changes)
        github_token: Optional GitHub token for private repositories
    """
    # Create a SWE harness agent
    swe_agent = SWEHarnessAgent(github_token)

    # Analyze the commit
    logger.info(f"Analyzing commit {head_commit} in {repo_url}")
    results = swe_agent.analyze_commit(repo_url, base_commit, head_commit)

    # Print the results
    print("\n" + "=" * 80)
    print(f"Commit Analysis Results for {repo_url}")
    print(f"Base: {base_commit}")
    print(f"Head: {head_commit}")
    print("=" * 80)
    print(f"Quality Score: {results['quality_score']}/10.0 - {results['overall_assessment']}")
    print(f"Properly Implemented: {'Yes' if results['is_properly_implemented'] else 'No'}")

    if "issues" in results and results["issues"]:
        print("\nIssues:")
        for issue in results["issues"]:
            print(f"- {issue}")

    print("\nDetailed Report:")
    print(results["report"])


def create_snapshots_example(
    repo_url: str,
    base_commit: str,
    head_commit: str,
    github_token: Optional[str] = None,
):
    """
    Demonstrate how to create and compare snapshots.

    Args:
        repo_url: The repository URL or owner/repo string
        base_commit: The base commit SHA
        head_commit: The head commit SHA
        github_token: Optional GitHub token for private repositories
    """
    # Create a snapshot manager
    snapshot_manager = SnapshotManager()

    # Create snapshots for the base and head commits
    logger.info(f"Creating snapshot for base commit {base_commit}")
    base_codebase = snapshot_manager.create_codebase_from_repo(repo_url, base_commit, github_token)
    base_snapshot = snapshot_manager.create_snapshot(base_codebase, base_commit)

    logger.info(f"Creating snapshot for head commit {head_commit}")
    head_codebase = snapshot_manager.create_codebase_from_repo(repo_url, head_commit, github_token)
    head_snapshot = snapshot_manager.create_snapshot(head_codebase, head_commit)

    # Print snapshot summaries
    print("\n" + "=" * 80)
    print("Base Snapshot Summary:")
    print("=" * 80)
    print(base_snapshot.get_summary())

    print("\n" + "=" * 80)
    print("Head Snapshot Summary:")
    print("=" * 80)
    print(head_snapshot.get_summary())

    # Compare the snapshots using the CodeAnalyzer
    from codegen_on_oss.analysis.analysis import CodeAnalyzer

    analyzer = CodeAnalyzer(head_codebase)

    comparison_results = analyzer.compare_snapshots(base_snapshot, head_snapshot)

    print("\n" + "=" * 80)
    print("Snapshot Comparison Results:")
    print("=" * 80)
    print(comparison_results["formatted_summary"])


def main():
    parser = argparse.ArgumentParser(description="SWE Harness Agent Example")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # PR analysis command
    pr_parser = subparsers.add_parser("pr", help="Analyze a pull request")
    pr_parser.add_argument("--repo", required=True, help="Repository URL or owner/repo string")
    pr_parser.add_argument("--pr", type=int, required=True, help="Pull request number")
    pr_parser.add_argument("--token", help="GitHub token for private repositories")
    pr_parser.add_argument(
        "--comment",
        action="store_true",
        help="Post a comment to the PR with the analysis results",
    )

    # Commit analysis command
    commit_parser = subparsers.add_parser("commit", help="Analyze a commit")
    commit_parser.add_argument("--repo", required=True, help="Repository URL or owner/repo string")
    commit_parser.add_argument("--base", required=True, help="Base commit SHA (before the changes)")
    commit_parser.add_argument("--head", required=True, help="Head commit SHA (after the changes)")
    commit_parser.add_argument("--token", help="GitHub token for private repositories")

    # Snapshot example command
    snapshot_parser = subparsers.add_parser(
        "snapshot", help="Demonstrate snapshot creation and comparison"
    )
    snapshot_parser.add_argument(
        "--repo", required=True, help="Repository URL or owner/repo string"
    )
    snapshot_parser.add_argument("--base", required=True, help="Base commit SHA")
    snapshot_parser.add_argument("--head", required=True, help="Head commit SHA")
    snapshot_parser.add_argument("--token", help="GitHub token for private repositories")

    args = parser.parse_args()

    # Get GitHub token from environment if not provided
    github_token = args.token or os.environ.get("GITHUB_TOKEN")

    if args.command == "pr":
        analyze_pr(args.repo, args.pr, github_token, args.comment)
    elif args.command == "commit":
        analyze_commit(args.repo, args.base, args.head, github_token)
    elif args.command == "snapshot":
        create_snapshots_example(args.repo, args.base, args.head, github_token)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
