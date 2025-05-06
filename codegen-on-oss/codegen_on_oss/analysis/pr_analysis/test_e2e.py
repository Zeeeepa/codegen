"""
End-to-end test for PR analysis.

This module provides a simple end-to-end test for the PR analysis system.
"""

import logging
import os
import sys
from typing import Dict, Any

from codegen_on_oss.analysis.pr_analysis.core.pr_analyzer import PRAnalyzer
from codegen_on_oss.analysis.pr_analysis.utils.config_utils import get_default_config


logger = logging.getLogger(__name__)


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )


def run_test(repo_url: str, pr_number: int) -> Dict[str, Any]:
    """
    Run an end-to-end test of the PR analysis system.
    
    Args:
        repo_url: Repository URL
        pr_number: Pull request number
        
    Returns:
        Analysis results
    """
    logger.info(f"Running end-to-end test for {repo_url} PR #{pr_number}")
    
    # Get default configuration
    config = get_default_config()
    
    # Override configuration with environment variables
    if 'GITHUB_TOKEN' in os.environ:
        config['github']['token'] = os.environ['GITHUB_TOKEN']
    
    # Create PR analyzer
    analyzer = PRAnalyzer()
    analyzer.config = config
    
    # Run analysis
    analyzer.initialize(repo_url, pr_number)
    results = analyzer.analyze()
    
    # Print report
    report = results['report']
    print("\n" + "=" * 80)
    print(f"PR Analysis Report for {repo_url} PR #{pr_number}")
    print("=" * 80)
    print(f"Status: {report['summary']['status']}")
    print(f"Message: {report['summary']['message']}")
    print("-" * 80)
    
    # Print details
    for detail in report['details']:
        status_emoji = '✅' if detail['status'] == 'success' else '⚠️' if detail['status'] == 'warning' else '❌'
        print(f"{status_emoji} {detail['name']}: {detail['message']}")
    
    print("=" * 80)
    
    return results


def main():
    """Main function."""
    setup_logging()
    
    # Get repository URL and PR number from command line arguments
    if len(sys.argv) < 3:
        print("Usage: python test_e2e.py <repo_url> <pr_number>")
        sys.exit(1)
    
    repo_url = sys.argv[1]
    pr_number = int(sys.argv[2])
    
    # Run test
    run_test(repo_url, pr_number)


if __name__ == '__main__':
    main()

