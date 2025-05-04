#!/usr/bin/env python
"""
SWE Harness CLI Module

This module provides a command-line interface for the SWE Harness Agent,
allowing users to analyze commits and pull requests from the command line.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

from codegen_on_oss.analysis.swe_harness_agent import SWEHarnessAgent
from codegen_on_oss.snapshot.codebase_snapshot import CodebaseSnapshot, SnapshotManager
from codegen_on_oss.analysis.diff_analyzer import DiffAnalyzer

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """
    Set up logging configuration.

    Args:
        verbose: Whether to enable verbose logging
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def analyze_pr(args: argparse.Namespace) -> None:
    """
    Analyze a pull request.

    Args:
        args: Command-line arguments
    """
    agent = SWEHarnessAgent(
        github_token=args.token,
        snapshot_dir=args.snapshot_dir,
        use_agent=not args.no_agent,
    )

    results = agent.analyze_and_comment_on_pr(
        args.repo, args.pr, args.comment, args.detailed
    )

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
    else:
        print(json.dumps(results, indent=2))


def analyze_commit(args: argparse.Namespace) -> None:
    """
    Analyze a commit.

    Args:
        args: Command-line arguments
    """
    agent = SWEHarnessAgent(
        github_token=args.token,
        snapshot_dir=args.snapshot_dir,
        use_agent=not args.no_agent,
    )

    results = agent.analyze_commit(args.repo, args.base, args.head, args.detailed)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
    else:
        print(json.dumps(results, indent=2))


def compare_branches(args: argparse.Namespace) -> None:
    """
    Compare two branches.

    Args:
        args: Command-line arguments
    """
    snapshot_manager = SnapshotManager(args.snapshot_dir)

    # Create snapshots for the base and head branches
    base_snapshot = CodebaseSnapshot.create_from_repo(
        args.repo, args.base, args.token
    )
    head_snapshot = CodebaseSnapshot.create_from_repo(
        args.repo, args.head, args.token
    )

    # Verify snapshots were created successfully
    if not base_snapshot or not head_snapshot:
        logger.error("Failed to create one or both snapshots")
        return

    # Compare the snapshots
    diff_analyzer = DiffAnalyzer(base_snapshot, head_snapshot)

    # Get the summary
    summary = diff_analyzer.get_summary()

    # Get high-risk changes if requested
    if args.high_risk:
        high_risk_changes = diff_analyzer.get_high_risk_changes()
        summary["high_risk_changes"] = high_risk_changes

    # Format the summary as text if requested
    if args.text:
        summary_text = diff_analyzer.format_summary_text()
        print(summary_text)
    else:
        if args.output:
            with open(args.output, "w") as f:
                json.dump(summary, f, indent=2)
        else:
            print(json.dumps(summary, indent=2))


def create_snapshot(args: argparse.Namespace) -> None:
    """
    Create a snapshot of a repository.

    Args:
        args: Command-line arguments
    """
    snapshot_manager = SnapshotManager(args.snapshot_dir)

    # Create a snapshot
    snapshot = CodebaseSnapshot.create_from_repo(
        args.repo, args.commit, args.token
    )

    # Verify snapshot was created successfully
    if not snapshot:
        logger.error(f"Failed to create snapshot for {args.repo}")
        return

    # Save the snapshot
    if args.output:
        snapshot.save_to_file(args.output)
        print(f"Snapshot saved to {args.output}")
    else:
        # Print the snapshot summary
        print(snapshot.get_summary())


def main() -> None:
    """
    Main entry point for the CLI.
    """
    parser = argparse.ArgumentParser(
        description="SWE Harness CLI for analyzing commits and pull requests"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--token",
        help="GitHub token for private repositories",
        default=os.environ.get("GITHUB_TOKEN"),
    )
    parser.add_argument(
        "--snapshot-dir", help="Directory to store snapshots", default=None
    )
    parser.add_argument(
        "--output", "-o", help="Output file for results (default: stdout)", default=None
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # PR analysis command
    pr_parser = subparsers.add_parser("analyze-pr", help="Analyze a pull request")
    pr_parser.add_argument("repo", help="Repository URL or owner/repo string")
    pr_parser.add_argument("pr", type=int, help="Pull request number to analyze")
    pr_parser.add_argument(
        "--detailed", action="store_true", help="Include detailed analysis in results"
    )
    pr_parser.add_argument(
        "--no-agent", action="store_true", help="Disable LLM-based agent analysis"
    )
    pr_parser.add_argument(
        "--comment",
        action="store_true",
        help="Post a comment to the PR with analysis results",
    )
    pr_parser.set_defaults(func=analyze_pr)

    # Commit analysis command
    commit_parser = subparsers.add_parser("analyze-commit", help="Analyze a commit")
    commit_parser.add_argument("repo", help="Repository URL or owner/repo string")
    commit_parser.add_argument("base", help="Base commit SHA")
    commit_parser.add_argument("head", help="Head commit SHA")
    commit_parser.add_argument(
        "--detailed", action="store_true", help="Include detailed analysis in results"
    )
    commit_parser.add_argument(
        "--no-agent", action="store_true", help="Disable LLM-based agent analysis"
    )
    commit_parser.set_defaults(func=analyze_commit)

    # Branch comparison command
    branch_parser = subparsers.add_parser(
        "compare-branches", help="Compare two branches"
    )
    branch_parser.add_argument("repo", help="Repository URL or owner/repo string")
    branch_parser.add_argument("base", help="Base branch or commit SHA")
    branch_parser.add_argument("head", help="Head branch or commit SHA")
    branch_parser.add_argument(
        "--high-risk",
        action="store_true",
        help="Include high-risk changes in the output",
    )
    branch_parser.add_argument(
        "--text", action="store_true", help="Output as formatted text instead of JSON"
    )
    branch_parser.set_defaults(func=compare_branches)

    # Snapshot command
    snapshot_parser = subparsers.add_parser(
        "create-snapshot", help="Create a snapshot of a repository"
    )
    snapshot_parser.add_argument("repo", help="Repository URL or owner/repo string")
    snapshot_parser.add_argument(
        "--commit", help="Commit SHA to snapshot", default=None
    )
    snapshot_parser.set_defaults(func=create_snapshot)

    args = parser.parse_args()

    # Set up logging
    setup_logging(args.verbose)

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Run the selected command
    args.func(args)


if __name__ == "__main__":
    main()
