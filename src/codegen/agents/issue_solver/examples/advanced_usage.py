#!/usr/bin/env python
"""Example script demonstrating advanced usage of the IssueSolverAgent."""

import argparse
import json
import os
from pathlib import Path

from codegen import Codebase, IssueSolverAgent
from codegen.agents.issue_solver import Issue
from codegen.shared.enums.programming_language import ProgrammingLanguage


def main():
    """Run the example script."""
    parser = argparse.ArgumentParser(description="Advanced usage of the IssueSolverAgent")
    parser.add_argument("--repo", required=True, help="Repository name (e.g., 'owner/repo')")
    parser.add_argument("--issue-file", help="Path to a JSON file containing the issue description")
    parser.add_argument("--issue-number", type=int, help="GitHub issue number to solve")
    parser.add_argument("--base-commit", default="HEAD", help="Base commit to use (default: HEAD)")
    parser.add_argument("--output-dir", help="Directory to save results to")
    parser.add_argument("--model", default="claude-3-5-sonnet-latest", help="Model to use")
    parser.add_argument("--language", default="python", help="Programming language of the codebase")
    parser.add_argument("--create-pr", action="store_true", help="Create a pull request with the solution")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate the solution against a reference patch")
    parser.add_argument("--generate-report", action="store_true", help="Generate a report from the results")
    parser.add_argument("--swe-bench", action="store_true", help="Load issues from SWE Bench dataset")
    parser.add_argument("--swe-bench-dataset", default="lite", help="SWE Bench dataset to use (lite, full, verified)")
    parser.add_argument("--swe-bench-subset", help="SWE Bench subset to use (e.g., lite_small, lite_medium, lite_large)")
    parser.add_argument("--max-examples", type=int, default=5, help="Maximum number of examples to load from SWE Bench")
    parser.add_argument("--threads", type=int, default=1, help="Number of issues to process concurrently")
    args = parser.parse_args()

    # Create output directory if specified
    output_dir = None
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)

    # Initialize the agent
    agent = IssueSolverAgent(
        model_name=args.model,
        output_dir=output_dir,
        language=args.language,
        disable_file_parse=True
    )

    # Process SWE Bench dataset
    if args.swe_bench:
        print(f"Loading issues from SWE Bench dataset: {args.swe_bench_dataset}")
        issues = agent.load_swe_bench_examples(
            dataset_name=args.swe_bench_dataset,
            subset=args.swe_bench_subset,
            max_examples=args.max_examples
        )
        
        if not issues:
            print("Error: No issues loaded from SWE Bench dataset")
            return 1
            
        print(f"Loaded {len(issues)} issues from SWE Bench dataset")
        
        # Process the issues
        print(f"Processing {len(issues)} issues with {args.threads} threads...")
        results = agent.run(
            issues,
            threads=args.threads,
            run_id=f"swe-bench-{args.swe_bench_dataset}"
        )
        
        # Evaluate the results
        if args.evaluate:
            print("\nEvaluating results...")
            for result in results:
                evaluation = agent.evaluate_solution(result)
                print(f"Issue {result['issue_id']}: {evaluation.get('success')}")
        
        # Generate a report
        if args.generate_report:
            print("\nGenerating report...")
            report = agent.generate_report()
            print(f"Report saved to {output_dir / 'report.json'}")
            
            # Print summary
            print("\nSummary:")
            print(f"Total issues: {report['overall']['total']}")
            print(f"Issues with patches: {report['overall']['with_patch']} ({report['overall']['with_patch_rate']:.2%})")
            print(f"Successful solutions: {report['overall']['successful']} ({report['overall']['successful_rate']:.2%})")
        
        return 0
    
    # Process a GitHub issue
    elif args.issue_number:
        print(f"Solving GitHub issue #{args.issue_number} in {args.repo}...")
        result = agent.solve_github_issue(
            repo=args.repo,
            issue_number=args.issue_number,
            base_branch=args.base_commit
        )
        
        # Evaluate the solution
        if args.evaluate and result.get("reference_patch"):
            print("\nEvaluating solution...")
            evaluation = agent.evaluate_solution(result)
            print(f"Evaluation: {evaluation}")
        
        # Create a pull request
        if args.create_pr:
            print("\nCreating pull request...")
            pr = agent.create_pull_request(result)
            print(f"Pull request created: {pr['html_url']}")
        
        return 0
    
    # Process a local issue
    elif args.issue_file:
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
        
        print(f"Solving issue {issue.id}...")
        result = agent.run(issue)
        
        # Evaluate the solution
        if args.evaluate and issue.patch:
            print("\nEvaluating solution...")
            evaluation = agent.evaluate_solution(result, reference_patch=issue.patch)
            print(f"Evaluation: {evaluation}")
        
        # Create a pull request
        if args.create_pr:
            print("\nCreating pull request...")
            pr = agent.create_pull_request(result)
            print(f"Pull request created: {pr['html_url']}")
        
        return 0
    
    else:
        print("Error: Must specify either --issue-file, --issue-number, or --swe-bench")
        return 1


if __name__ == "__main__":
    exit(main())
