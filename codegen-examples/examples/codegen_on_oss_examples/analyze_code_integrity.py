#!/usr/bin/env python3
"""
Code Integrity Analyzer Script

This script provides a command-line interface for analyzing code integrity
in a repository. It can analyze a single branch, compare two branches,
or analyze a pull request.

Example usage:
    # Basic analysis
    python -m codegen-examples.examples.codegen_on_oss_examples.analyze_code_integrity \
        --repo /path/to/repo --output results.json --html report.html

    # Analysis with custom configuration
    python -m codegen-examples.examples.codegen_on_oss_examples.analyze_code_integrity \
        --repo /path/to/repo --config config.json \
        --output results.json --html report.html

    # Branch comparison
    python -m codegen-examples.examples.codegen_on_oss_examples.analyze_code_integrity \
        --repo /path/to/repo --base main --head feature-branch \
        --output results.json --html report.html

    # PR analysis
    python -m codegen-examples.examples.codegen_on_oss_examples.analyze_code_integrity \
        --repo /path/to/repo --pr 123 \
        --output results.json --html report.html
"""

import argparse
import codegen
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from codegen import Codebase
from codegen_on_oss.analysis import CodeAnalyzer


def generate_html_report(results: Dict[str, Any], output_path: str) -> None:
    """
    Generate an HTML report from the analysis results.
    
    Args:
        results: The analysis results
        output_path: Path to save the HTML report
    """
    # This is a simplified version of the HTML report generation
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Code Integrity Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333; }}
            .summary {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; }}
            .issues {{ margin-top: 20px; }}
            .issue {{ margin-bottom: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
            .high {{ background-color: #ffdddd; }}
            .medium {{ background-color: #ffffdd; }}
            .low {{ background-color: #ddffdd; }}
        </style>
    </head>
    <body>
        <h1>Code Integrity Analysis Report</h1>
        <div class="summary">
            <h2>Summary</h2>
            <p>Total Issues: {len(results.get('issues', []))}</p>
            <p>Analysis Date: {results.get('timestamp', 'N/A')}</p>
        </div>
        <div class="issues">
            <h2>Issues</h2>
    """
    
    for issue in results.get('issues', []):
        severity = issue.get('severity', 'medium')
        html += f"""
            <div class="issue {severity}">
                <h3>{issue.get('title', 'Unnamed Issue')}</h3>
                <p><strong>Severity:</strong> {severity}</p>
                <p><strong>Location:</strong> {issue.get('file', 'N/A')}:{issue.get('line', 'N/A')}</p>
                <p><strong>Description:</strong> {issue.get('description', 'No description')}</p>
            </div>
        """
    
    html += """
        </div>
    </body>
    </html>
    """
    
    with open(output_path, 'w') as f:
        f.write(html)


@codegen.function("codegen-on-oss-code-integrity")
def run(
    repo_path: str,
    base_branch: Optional[str] = None,
    head_branch: Optional[str] = None,
    pr_number: Optional[int] = None,
    config_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze code integrity in a repository.
    
    This function:
    1. Initializes a CodeAnalyzer with the provided codebase
    2. Loads configuration if provided
    3. Performs code integrity analysis based on the parameters
    4. Returns the analysis results
    
    Args:
        repo_path: Path to the repository
        base_branch: Optional base branch for comparison
        head_branch: Optional head branch for comparison
        pr_number: Optional PR number to analyze
        config_path: Optional path to a configuration file
        
    Returns:
        dict: The analysis results
    """
    # Create a codebase from the repository
    codebase = Codebase(repo_path)
    
    # Initialize the analyzer
    analyzer = CodeAnalyzer(codebase)
    
    # Load configuration if provided
    config = None
    if config_path:
        with open(config_path, 'r') as f:
            config = json.load(f)
    
    # Determine the analysis type
    if pr_number:
        print(f"Analyzing PR #{pr_number}...")
        results = analyzer.analyze_pr(pr_number, config=config)
    elif base_branch and head_branch:
        print(f"Comparing branches: {base_branch} -> {head_branch}...")
        results = analyzer.compare_branches(base_branch, head_branch, config=config)
    else:
        print("Analyzing the current codebase...")
        results = analyzer.analyze_code_integrity(config=config)
    
    print("Analysis complete!")
    return results


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Code Integrity Analyzer")
    parser.add_argument("--repo", required=True, help="Path to the repository")
    parser.add_argument("--base", help="Base branch for comparison")
    parser.add_argument("--head", help="Head branch for comparison")
    parser.add_argument("--pr", type=int, help="PR number to analyze")
    parser.add_argument("--config", help="Path to a configuration file (JSON)")
    parser.add_argument("--output", help="Output file for analysis results (JSON)")
    parser.add_argument("--html", help="Output file for HTML report")
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    # Validate arguments
    if args.base and not args.head:
        print("Error: If --base is specified, --head must also be specified")
        sys.exit(1)
    if args.head and not args.base:
        print("Error: If --head is specified, --base must also be specified")
        sys.exit(1)
    if args.pr and (args.base or args.head):
        print("Error: Cannot specify both --pr and --base/--head")
        sys.exit(1)
    
    # Run the analysis
    results = run(args.repo, args.base, args.head, args.pr, args.config)
    
    # Save the results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")
    
    # Generate HTML report
    if args.html:
        generate_html_report(results, args.html)
        print(f"HTML report saved to {args.html}")
    
    # Print a summary if no output file is specified
    if not args.output and not args.html:
        print("\nAnalysis Summary:")
        print(f"Total Issues: {len(results.get('issues', []))}")
        
        # Print the top 5 issues
        if results.get('issues'):
            print("\nTop Issues:")
            for i, issue in enumerate(results.get('issues', [])[:5]):
                print(f"{i+1}. {issue.get('title', 'Unnamed Issue')} - {issue.get('file', 'N/A')}:{issue.get('line', 'N/A')}")
        
        print("\nUse --output to save the full results to a file")

