#!/usr/bin/env python
"""Example script for solving a GitHub issue using the IssueSolverAgent."""

import argparse
import json
import os
from pathlib import Path

from codegen import Codebase
from codegen.agents.issue_solver import IssueSolverAgent, Issue


def main():
    """Run the example script."""
    parser = argparse.ArgumentParser(description="Solve a GitHub issue using the IssueSolverAgent")
    parser.add_argument("repo", help="Repository name (e.g., 'owner/repo')")
    parser.add_argument("issue_number", type=int, help="Issue number to solve")
    parser.add_argument("--base-branch", default="main", help="Base branch to use (default: main)")
    parser.add_argument("--output-dir", help="Directory to save results to")
    parser.add_argument("--model", default="claude-3-5-sonnet-latest", help="Model to use")
    parser.add_argument("--create-pr", action="store_true", help="Create a pull request with the solution")
    args = parser.parse_args()

    # Create output directory if specified
    output_dir = None
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)

    # Initialize the agent
    agent = IssueSolverAgent(
        model_name=args.model,
        output_dir=output_dir
    )

    # Solve the issue
    print(f"Solving issue #{args.issue_number} in {args.repo}...")
    result = agent.solve_github_issue(
        repo=args.repo,
        issue_number=args.issue_number,
        base_branch=args.base_branch
    )

    # Print the result
    print("\nSolution:")
    print(f"Issue ID: {result['issue_id']}")
    print(f"Edited files: {result['edited_files']}")
    
    # Create a pull request if requested
    if args.create_pr:
        print("\nCreating pull request...")
        pr = agent.create_pull_request(result)
        print(f"Pull request created: {pr['html_url']}")

    print("\nDone!")


if __name__ == "__main__":
    main()
