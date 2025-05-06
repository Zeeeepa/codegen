"""
End-to-end test for PR analysis.

This module provides a simple end-to-end test for the PR analysis system.
"""

import argparse
import logging
import os
import sys
from typing import Dict, Any

from codegen_on_oss.analysis.pr_analysis.core.pr_analyzer import PRAnalyzer

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """
    Set up logging.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def run_analysis(repo_url: str, pr_number: int) -> Dict[str, Any]:
    """
    Run PR analysis.

    Args:
        repo_url: Repository URL
        pr_number: Pull request number

    Returns:
        Analysis results
    """
    # Create PR analyzer
    analyzer = PRAnalyzer()

    # Run analysis
    return analyzer.run(repo_url, pr_number)


def main() -> None:
    """
    Main function.
    """
    # Set up logging
    setup_logging()

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run PR analysis")
    parser.add_argument("repo_url", help="Repository URL or owner/repo string")
    parser.add_argument("pr_number", type=int, help="Pull request number")
    args = parser.parse_args()

    # Check if GitHub token is set
    if "GITHUB_TOKEN" not in os.environ:
        logger.warning("GITHUB_TOKEN environment variable is not set")
        logger.warning("Some features may not work without a GitHub token")

    # Run analysis
    try:
        results = run_analysis(args.repo_url, args.pr_number)
        print(f"Analysis completed successfully")
        print(f"Report: {results['report']}")
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

