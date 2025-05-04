#!/usr/bin/env python3
"""
Script to analyze code integrity in a repository.

This script analyzes code integrity in a repository, including:
- Finding all functions and classes
- Identifying errors in functions and classes
- Detecting improper parameter usage
- Finding incorrect function callback points
- Comparing error counts between branches
- Analyzing code complexity and duplication
- Checking for type hint usage
- Detecting unused imports
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, Optional

import yaml
from codegen.sdk.core.codebase import Codebase

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from codegen_on_oss.analysis.code_integrity_analyzer import (
    CodeIntegrityAnalyzer,
    analyze_pr,
    compare_branches,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_codebase(
    repo_path: str, branch: Optional[str] = None, commit: Optional[str] = None
) -> Codebase:
    """
    Load a codebase from a repository.

    Args:
        repo_path: Path to the repository
        branch: Optional branch to load
        commit: Optional commit to load

    Returns:
        Loaded codebase
    """
    logger.info(f"Loading codebase from {repo_path}")

    if branch:
        logger.info(f"Using branch: {branch}")

    if commit:
        logger.info(f"Using commit: {commit}")

    # Load the codebase
    codebase = Codebase.from_repo(repo_path, branch=branch, commit=commit)

    logger.info(f"Loaded codebase with {len(list(codebase.files))} files")

    return codebase


def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a file.

    Args:
        config_file: Path to the configuration file

    Returns:
        Configuration dictionary
    """
    if not config_file:
        return {}

    logger.info(f"Loading configuration from {config_file}")

    config = {}
    try:
        with open(config_file, "r") as f:
            if config_file.endswith(".json"):
                config = json.load(f)
            elif config_file.endswith((".yaml", ".yml")):
                config = yaml.safe_load(f)
            else:
                logger.warning(f"Unknown configuration file format: {config_file}")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")

    return config


def analyze_codebase(
    codebase: Codebase, config: Dict[str, Any] = None, output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze a codebase for integrity issues.

    Args:
        codebase: The codebase to analyze
        config: Configuration options for the analyzer
        output_file: Optional file to write the results to

    Returns:
        Analysis results
    """
    logger.info("Analyzing codebase for integrity issues")

    # Create analyzer
    analyzer = CodeIntegrityAnalyzer(codebase, config or {})

    # Analyze codebase
    results = analyzer.analyze()

    # Print summary
    logger.info(
        f"Found {results['total_errors']} errors in {results['total_functions']} "
        f"functions and {results['total_classes']} classes"
    )
    logger.info(f"Function errors: {results['function_errors']}")
    logger.info(f"Class errors: {results['class_errors']}")
    logger.info(f"Parameter errors: {results['parameter_errors']}")
    logger.info(f"Callback errors: {results['callback_errors']}")
    logger.info(f"Import errors: {results['import_errors']}")
    logger.info(f"Complexity errors: {results['complexity_errors']}")
    logger.info(f"Type hint errors: {results['type_hint_errors']}")
    logger.info(f"Duplication errors: {results['duplication_errors']}")

    # Write results to file if requested
    if output_file:
        logger.info(f"Writing results to {output_file}")
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

    return results


def compare_codebases(
    main_codebase: Codebase,
    branch_codebase: Codebase,
    config: Dict[str, Any] = None,
    output_file: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compare two codebases for integrity issues.

    Args:
        main_codebase: The main branch codebase
        branch_codebase: The feature branch codebase
        config: Configuration options for the analyzer
        output_file: Optional file to write the results to

    Returns:
        Comparison results
    """
    logger.info("Comparing codebases for integrity issues")

    # Create analyzers with the same configuration
    main_analyzer = CodeIntegrityAnalyzer(main_codebase, config or {})
    branch_analyzer = CodeIntegrityAnalyzer(branch_codebase, config or {})

    # Analyze both codebases
    main_analyzer.analyze()
    branch_analyzer.analyze()

    # Compare branches
    comparison = compare_branches(main_codebase, branch_codebase)

    # Print summary
    logger.info(f"Main branch has {comparison['main_error_count']} errors")
    logger.info(f"Feature branch has {comparison['branch_error_count']} errors")
    logger.info(f"Difference: {comparison['error_diff']} errors")
    logger.info(f"New errors: {len(comparison['new_errors'])}")
    logger.info(f"Fixed errors: {len(comparison['fixed_errors'])}")

    # Write results to file if requested
    if output_file:
        logger.info(f"Writing results to {output_file}")
        with open(output_file, "w") as f:
            json.dump(comparison, f, indent=2)

    return comparison


def analyze_pull_request(
    main_codebase: Codebase,
    pr_codebase: Codebase,
    config: Dict[str, Any] = None,
    output_file: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze a pull request for integrity issues.

    Args:
        main_codebase: The main branch codebase
        pr_codebase: The PR branch codebase
        config: Configuration options for the analyzer
        output_file: Optional file to write the results to

    Returns:
        Analysis results
    """
    logger.info("Analyzing pull request for integrity issues")

    # Create analyzers with the same configuration
    main_analyzer = CodeIntegrityAnalyzer(main_codebase, config or {})
    pr_analyzer = CodeIntegrityAnalyzer(pr_codebase, config or {})

    # Analyze both codebases
    main_analyzer.analyze()
    pr_analyzer.analyze()

    # Analyze PR
    pr_analysis = analyze_pr(main_codebase, pr_codebase)

    # Print summary
    logger.info(
        f"PR adds {pr_analysis['new_functions']} new functions and "
        f"{pr_analysis['new_classes']} new classes"
    )
    logger.info(
        f"PR modifies {pr_analysis['modified_functions']} functions and "
        f"{pr_analysis['modified_classes']} classes"
    )
    logger.info(f"PR introduces {pr_analysis['total_new_errors']} new errors")

    # Write results to file if requested
    if output_file:
        logger.info(f"Writing results to {output_file}")
        with open(output_file, "w") as f:
            json.dump(pr_analysis, f, indent=2)

    return pr_analysis


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Analyze code integrity in a repository")

    parser.add_argument("--repo", required=True, help="Path to the repository")
    parser.add_argument(
        "--mode",
        choices=["analyze", "compare", "pr"],
        default="analyze",
        help="Mode of operation: analyze a single codebase, compare branches, or analyze a PR",
    )
    parser.add_argument("--main-branch", help="Main branch name (for compare and pr modes)")
    parser.add_argument("--feature-branch", help="Feature branch name (for compare and pr modes)")
    parser.add_argument("--output", help="Output file for results (JSON)")
    parser.add_argument("--html", help="Output file for HTML report")
    parser.add_argument("--config", help="Configuration file (JSON or YAML)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load configuration
    config = load_config(args.config)

    # Process based on mode
    if args.mode == "analyze":
        # Analyze a single codebase
        codebase = load_codebase(args.repo)
        analyze_codebase(codebase, config, args.output)

    elif args.mode == "compare":
        # Compare branches
        if not args.main_branch or not args.feature_branch:
            logger.error("Both --main-branch and --feature-branch are required for compare mode")
            sys.exit(1)

        # Load codebases
        main_codebase = load_codebase(args.repo, args.main_branch)
        feature_codebase = load_codebase(args.repo, args.feature_branch)

        # Compare codebases
        compare_codebases(main_codebase, feature_codebase, config, args.output)

    elif args.mode == "pr":
        # Analyze a PR
        if not args.main_branch or not args.feature_branch:
            logger.error("Both --main-branch and --feature-branch are required for PR mode")
            sys.exit(1)

        # Load codebases
        main_codebase = load_codebase(args.repo, args.main_branch)
        pr_codebase = load_codebase(args.repo, args.feature_branch)

        # Analyze PR
        analyze_pull_request(main_codebase, pr_codebase, config, args.output)


if __name__ == "__main__":
    main()
