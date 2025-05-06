"""
Example script for using the PR static analysis system.

This script demonstrates how to use the PR static analysis system to analyze a PR.
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, List

from pr_static_analysis import PRStaticAnalyzer
from pr_static_analysis.rules import rule_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="PR static analysis example")
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--pr",
        type=str,
        required=True,
        help="Path to PR directory or URL",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Path to output file (JSON)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args()


def load_pr_files(pr_path: str) -> List[Dict]:
    """
    Load files from a PR directory.
    
    Args:
        pr_path: Path to PR directory
    
    Returns:
        List of file information dictionaries
    """
    files = []
    
    if os.path.isdir(pr_path):
        # Load files from directory
        for root, _, filenames in os.walk(pr_path):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                rel_filepath = os.path.relpath(filepath, pr_path)
                
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    files.append(
                        {
                            "filepath": rel_filepath,
                            "content": content,
                        }
                    )
                except Exception as e:
                    logger.warning(f"Error reading file {filepath}: {e}")
    else:
        # Assume it's a URL or other format
        # In a real implementation, this would fetch the PR from a Git provider
        logger.error(f"Unsupported PR path: {pr_path}")
        sys.exit(1)
    
    return files


def main():
    """Run the example script."""
    args = parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    if args.config:
        rule_config.load_config_file(args.config)
    
    # Create analyzer
    analyzer = PRStaticAnalyzer()
    
    # Load PR files
    files = load_pr_files(args.pr)
    logger.info(f"Loaded {len(files)} files from PR")
    
    # Create context
    context = {
        "files": files,
        "pr": {
            "title": "Example PR",
            "description": "This is an example PR for testing the static analysis system.",
            "author": "example-user",
            "branch": "feature/example",
        },
        "config": rule_config.global_config,
    }
    
    # Analyze PR
    logger.info("Analyzing PR...")
    results = analyzer.analyze(context)
    logger.info(f"Found {len(results)} issues")
    
    # Generate report
    report = analyzer.generate_report(results)
    
    # Output report
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report written to {args.output}")
    else:
        # Print summary to console
        print(f"Total issues: {report['summary']['total_issues']}")
        print("Issues by severity:")
        for severity, count in report["summary"]["issues_by_severity"].items():
            print(f"  {severity}: {count}")
        print("Issues by rule:")
        for rule_id, count in report["summary"]["issues_by_rule"].items():
            print(f"  {rule_id}: {count}")
        print("Issues by file:")
        for filepath, count in report["summary"]["issues_by_file"].items():
            print(f"  {filepath}: {count}")


if __name__ == "__main__":
    main()

