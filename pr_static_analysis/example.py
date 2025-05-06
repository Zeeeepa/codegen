#!/usr/bin/env python
"""
Example script for using the PR static analysis system.
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Optional

import yaml

from pr_static_analysis import PRStaticAnalyzer
from pr_static_analysis.rules import rule_config


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="PR static analysis example")
    parser.add_argument(
        "--pr",
        type=str,
        required=True,
        help="Path to the PR directory",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to the configuration file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="report.json",
        help="Path to the output file",
    )
    return parser.parse_args()


def load_pr(pr_path: str) -> Dict:
    """Load PR information from a directory."""
    # In a real implementation, this would load PR information from a VCS API
    pr_info = {
        "title": os.path.basename(pr_path),
        "description": f"PR in {pr_path}",
        "author": "example-user",
        "branch": "feature/example",
    }

    # Load files
    files = []
    for root, _, filenames in os.walk(pr_path):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            files.append({
                "filepath": os.path.relpath(filepath, pr_path),
                "content": content,
            })

    return {
        "pr": pr_info,
        "files": files,
    }


def main() -> int:
    """Run the example."""
    args = parse_args()

    # Load configuration
    if not os.path.exists(args.config):
        print(f"Configuration file '{args.config}' does not exist")
        return 1

    rule_config.load_config_file(args.config)

    # Load PR information
    if not os.path.exists(args.pr):
        print(f"PR directory '{args.pr}' does not exist")
        return 1

    pr_info = load_pr(args.pr)

    # Create analyzer
    analyzer = PRStaticAnalyzer()

    # Create context
    context = {
        "files": pr_info["files"],
        "pr": pr_info["pr"],
        "config": rule_config.global_config,
    }

    # Analyze PR
    results = analyzer.analyze(context)

    # Generate report
    report = analyzer.generate_report(results)

    # Write report to file
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Report written to {args.output}")
    print(f"Found {len(results)} issues")

    return 0


if __name__ == "__main__":
    sys.exit(main())

