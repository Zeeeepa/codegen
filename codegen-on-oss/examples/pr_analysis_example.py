#!/usr/bin/env python3
"""
PR Analysis Example

This script demonstrates how to use the PR analysis system.
"""

import os
import sys
import argparse
import logging

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codegen_on_oss.analysis.pr_analysis.core import (
    create_rule_engine,
    create_pr_analyzer,
    create_report_generator,
)
from codegen_on_oss.analysis.pr_analysis.rules import (
    ComplexityRule,
    StyleRule,
    DocstringRule,
)
from codegen_on_oss.analysis.pr_analysis.utils.integration import create_github_client


def main():
    """Main function."""
    # Parse arguments
    parser = argparse.ArgumentParser(description='Analyze a GitHub PR')
    parser.add_argument('--repo', required=True, help='Repository name (e.g., "owner/repo")')
    parser.add_argument('--pr', type=int, required=True, help='PR number')
    parser.add_argument('--token', help='GitHub token (or set GITHUB_TOKEN env var)')
    parser.add_argument('--format', choices=['markdown', 'html', 'json'], default='markdown',
                        help='Report format (default: markdown)')
    parser.add_argument('--output', help='Output file (default: stdout)')
    parser.add_argument('--comment', action='store_true', help='Comment on the PR with the results')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get GitHub token
    token = args.token or os.environ.get('GITHUB_TOKEN')
    if not token:
        print('Error: GitHub token is required. Provide it with --token or set GITHUB_TOKEN env var.')
        sys.exit(1)
    
    # Create GitHub client
    github_client = create_github_client(token)
    
    # Create rules
    rules = [
        ComplexityRule(max_complexity=10),
        StyleRule(max_line_length=100),
        DocstringRule(),
    ]
    
    # Create rule engine
    rule_engine = create_rule_engine(rules)
    
    # Create report generator
    report_generator = create_report_generator(args.format)
    
    # Create PR analyzer
    pr_analyzer = create_pr_analyzer(github_client, rule_engine, report_generator)
    
    try:
        # Analyze PR
        print(f'Analyzing PR #{args.pr} in {args.repo}...')
        report = pr_analyzer.analyze_pr(args.pr, args.repo)
        
        # Format report
        if args.format == 'markdown':
            formatted_report = report_generator.format_report_as_markdown(report)
        elif args.format == 'html':
            formatted_report = report_generator.format_report_as_html(report)
        else:  # json
            import json
            formatted_report = json.dumps(report, default=lambda o: o.__dict__, indent=2)
        
        # Output report
        if args.output:
            with open(args.output, 'w') as f:
                f.write(formatted_report)
            print(f'Report saved to {args.output}')
        else:
            print(formatted_report)
        
        # Comment on PR if requested
        if args.comment:
            print(f'Commenting on PR #{args.pr}...')
            pr_analyzer.comment_on_pr(args.pr, args.repo, report)
            print('Comment added to PR')
        
        # Print summary
        summary = report['summary']
        print(f'Analysis complete: {summary["total_results"]} results '
              f'({summary["error_count"]} errors, {summary["warning_count"]} warnings, '
              f'{summary["info_count"]} info)')
        
    except Exception as e:
        print(f'Error analyzing PR: {e}')
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

