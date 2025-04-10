#!/usr/bin/env python
"""Example script for solving a batch of issues using the IssueSolverAgent."""

import argparse
import json
import os
import uuid
from pathlib import Path

from codegen import Codebase
from codegen.agents.issue_solver import IssueSolverAgent, Issue


def main():
    """Run the example script."""
    parser = argparse.ArgumentParser(description="Solve a batch of issues using the IssueSolverAgent")
    parser.add_argument("issues_dir", help="Directory containing JSON files with issue descriptions")
    parser.add_argument("--repo", help="Repository name (e.g., 'owner/repo')")
    parser.add_argument("--base-commit", default="HEAD", help="Base commit to use (default: HEAD)")
    parser.add_argument("--output-dir", help="Directory to save results to")
    parser.add_argument("--model", default="claude-3-5-sonnet-latest", help="Model to use")
    parser.add_argument("--threads", type=int, default=1, help="Number of issues to process concurrently")
    parser.add_argument("--run-id", help="Run ID for tracking (default: auto-generated)")
    args = parser.parse_args()

    # Load issues from the directory
    issues_dir = Path(args.issues_dir)
    if not issues_dir.exists() or not issues_dir.is_dir():
        print(f"Error: Issues directory {issues_dir} does not exist or is not a directory")
        return 1
        
    # Find all JSON files in the directory
    issue_files = list(issues_dir.glob("*.json"))
    if not issue_files:
        print(f"Error: No JSON files found in {issues_dir}")
        return 1
        
    print(f"Found {len(issue_files)} issue files")
    
    # Load issues from JSON files
    issues = {}
    for issue_file in issue_files:
        try:
            with open(issue_file, "r") as f:
                issue_data = json.load(f)
                
            # Get or generate issue ID
            issue_id = issue_data.get("id", f"local-{issue_file.stem}")
            
            # Get or use default repo
            repo = issue_data.get("repo", args.repo)
            if not repo:
                print(f"Error: No repository specified for issue {issue_id}")
                continue
                
            # Create Issue object
            issue = Issue(
                id=issue_id,
                repo=repo,
                base_commit=issue_data.get("base_commit", args.base_commit),
                problem_statement=issue_data.get("problem_statement", ""),
                patch=issue_data.get("patch"),
                difficulty=issue_data.get("difficulty"),
                metadata=issue_data.get("metadata", {})
            )
            
            issues[issue_id] = issue
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading issue from {issue_file}: {e}")
            continue
    
    if not issues:
        print("Error: No valid issues found")
        return 1
        
    print(f"Loaded {len(issues)} valid issues")
    
    # Create output directory if specified
    output_dir = None
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)

    # Generate run ID if not provided
    run_id = args.run_id or str(uuid.uuid4())

    # Initialize the agent
    agent = IssueSolverAgent(
        model_name=args.model,
        output_dir=output_dir
    )

    # Process the issues
    print(f"Processing {len(issues)} issues with {args.threads} threads...")
    results = agent.run(
        issues,
        threads=args.threads,
        run_id=run_id
    )

    # Print summary
    print("\nProcessing complete!")
    print(f"Processed {len(results)} issues")
    
    # Count successful patches
    successful = sum(1 for result in results if result.get("model_patch"))
    print(f"Successful patches: {successful}/{len(results)}")

    print("\nDone!")
    return 0


if __name__ == "__main__":
    exit(main())
