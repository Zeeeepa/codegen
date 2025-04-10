#!/usr/bin/env python
"""Example script for solving a local issue using the IssueSolverAgent."""

import argparse
import json
import os
from pathlib import Path

from codegen import Codebase
from codegen.agents.issue_solver import IssueSolverAgent, Issue


def main():
    """Run the example script."""
    parser = argparse.ArgumentParser(description="Solve a local issue using the IssueSolverAgent")
    parser.add_argument("repo", help="Repository name (e.g., 'owner/repo')")
    parser.add_argument("issue_file", help="Path to a JSON file containing the issue description")
    parser.add_argument("--base-commit", default="HEAD", help="Base commit to use (default: HEAD)")
    parser.add_argument("--output-dir", help="Directory to save results to")
    parser.add_argument("--model", default="claude-3-5-sonnet-latest", help="Model to use")
    args = parser.parse_args()

    # Load the issue from the JSON file
    issue_path = Path(args.issue_file)
    if not issue_path.exists():
        print(f"Error: Issue file {issue_path} does not exist")
        return 1
        
    try:
        with open(issue_path, "r") as f:
            issue_data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Issue file {issue_path} is not valid JSON")
        return 1
        
    # Create an Issue object
    issue = Issue(
        id=issue_data.get("id", f"local-{issue_path.stem}"),
        repo=args.repo,
        base_commit=args.base_commit,
        problem_statement=issue_data.get("problem_statement", ""),
        patch=issue_data.get("patch"),
        difficulty=issue_data.get("difficulty"),
        metadata=issue_data.get("metadata", {})
    )
    
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
    print(f"Solving issue {issue.id}...")
    result = agent.run(issue)

    # Print the result
    print("\nSolution:")
    print(f"Issue ID: {result['issue_id']}")
    print(f"Edited files: {result['edited_files']}")

    print("\nDone!")
    return 0


if __name__ == "__main__":
    exit(main())
