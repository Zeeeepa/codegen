#!/usr/bin/env python3
"""
Code Integrity Analyzer Script

This script provides a command-line interface for analyzing code integrity
in a repository. It can analyze a single branch, compare two branches,
or analyze a pull request.

Example usage:
    # Basic analysis
    python -m codegen_on_oss.scripts.analyze_code_integrity_example --repo /path/to/repo --output results.json --html report.html

    # Analysis with custom configuration
    python -m codegen_on_oss.scripts.analyze_code_integrity_example --repo /path/to/repo --config config.json --output results.json --html report.html

    # Branch comparison
    python -m codegen_on_oss.scripts.analyze_code_integrity_example --repo /path/to/repo --mode compare --main-branch main --feature-branch feature --output comparison.json --html report.html

    # PR analysis
    python -m codegen_on_oss.scripts.analyze_code_integrity_example --repo /path/to/repo --mode pr --main-branch main --feature-branch pr-branch --output pr_analysis.json --html report.html
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

from codegen import Codebase
from codegen_on_oss.analysis.code_integrity_analyzer import (
    CodeIntegrityAnalyzer,
    compare_branches,
    analyze_pr,
)
from codegen_on_oss.outputs.html_report_generator import generate_html_report


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        A dictionary with configuration options
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return {}


def save_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save analysis results to a JSON file.
    
    Args:
        results: Analysis results
        output_path: Path to save the results
    """
    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {output_path}")
    except Exception as e:
        print(f"Error saving results: {e}")


def analyze_single_branch(repo_path: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Analyze a single branch for code integrity issues.
    
    Args:
        repo_path: Path to the repository
        config: Optional configuration options
        
    Returns:
        A dictionary with analysis results
    """
    print(f"Analyzing repository: {repo_path}")
    start_time = time.time()
    
    # Create a codebase from the repository
    codebase = Codebase.from_repo(repo_path)
    
    # Create an analyzer with the provided configuration
    analyzer = CodeIntegrityAnalyzer(codebase, config)
    
    # Analyze code integrity
    results = analyzer.analyze()
    
    # Add execution time
    execution_time = time.time() - start_time
    results["execution_time"] = execution_time
    
    print(f"Analysis completed in {execution_time:.2f} seconds")
    print(f"Total Functions: {results['total_functions']}")
    print(f"Total Classes: {results['total_classes']}")
    print(f"Total Files: {results['total_files']}")
    print(f"Total Errors: {results['total_errors']}")
    
    return results


def analyze_branch_comparison(
    repo_path: str,
    main_branch: str,
    feature_branch: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Compare two branches for code integrity issues.
    
    Args:
        repo_path: Path to the repository
        main_branch: Name of the main branch
        feature_branch: Name of the feature branch
        config: Optional configuration options
        
    Returns:
        A dictionary with comparison results
    """
    print(f"Comparing branches: {main_branch} vs {feature_branch}")
    start_time = time.time()
    
    # Create codebases for both branches
    main_codebase = Codebase.from_repo(repo_path, branch=main_branch)
    feature_codebase = Codebase.from_repo(repo_path, branch=feature_branch)
    
    # Compare branches
    comparison = compare_branches(main_codebase, feature_codebase)
    
    # Add execution time
    execution_time = time.time() - start_time
    comparison["execution_time"] = execution_time
    
    print(f"Comparison completed in {execution_time:.2f} seconds")
    print(f"Main Branch Error Count: {comparison['main_error_count']}")
    print(f"Feature Branch Error Count: {comparison['branch_error_count']}")
    print(f"Error Difference: {comparison['error_diff']}")
    print(f"New Errors: {len(comparison['new_errors'])}")
    print(f"Fixed Errors: {len(comparison['fixed_errors'])}")
    
    return comparison


def analyze_pull_request(
    repo_path: str,
    main_branch: str,
    pr_branch: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze a pull request for code integrity issues.
    
    Args:
        repo_path: Path to the repository
        main_branch: Name of the main branch
        pr_branch: Name of the PR branch
        config: Optional configuration options
        
    Returns:
        A dictionary with PR analysis results
    """
    print(f"Analyzing PR: {pr_branch} -> {main_branch}")
    start_time = time.time()
    
    # Create codebases for both branches
    main_codebase = Codebase.from_repo(repo_path, branch=main_branch)
    pr_codebase = Codebase.from_repo(repo_path, branch=pr_branch)
    
    # Analyze PR
    pr_analysis = analyze_pr(main_codebase, pr_codebase)
    
    # Add execution time
    execution_time = time.time() - start_time
    pr_analysis["execution_time"] = execution_time
    
    print(f"PR analysis completed in {execution_time:.2f} seconds")
    print(f"New Functions: {pr_analysis['new_functions']}")
    print(f"New Classes: {pr_analysis['new_classes']}")
    print(f"Modified Functions: {pr_analysis['modified_functions']}")
    print(f"Modified Classes: {pr_analysis['modified_classes']}")
    print(f"Total New Errors: {pr_analysis['total_new_errors']}")
    
    return pr_analysis


def main():
    """
    Main entry point for the script.
    """
    parser = argparse.ArgumentParser(description="Analyze code integrity in a repository")
    
    parser.add_argument("--repo", required=True, help="Path to the repository")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--output", help="Path to save analysis results")
    parser.add_argument("--html", help="Path to save HTML report")
    parser.add_argument(
        "--mode",
        choices=["single", "compare", "pr"],
        default="single",
        help="Analysis mode: single branch, branch comparison, or PR analysis",
    )
    parser.add_argument("--main-branch", default="main", help="Main branch name (for compare and pr modes)")
    parser.add_argument("--feature-branch", help="Feature branch name (for compare and pr modes)")
    
    args = parser.parse_args()
    
    # Load configuration if provided
    config = None
    if args.config:
        config = load_config(args.config)
    
    # Perform analysis based on the selected mode
    if args.mode == "single":
        results = analyze_single_branch(args.repo, config)
    elif args.mode == "compare":
        if not args.feature_branch:
            parser.error("--feature-branch is required for compare mode")
        results = analyze_branch_comparison(args.repo, args.main_branch, args.feature_branch, config)
    elif args.mode == "pr":
        if not args.feature_branch:
            parser.error("--feature-branch is required for pr mode")
        results = analyze_pull_request(args.repo, args.main_branch, args.feature_branch, config)
    
    # Save results if output path is provided
    if args.output:
        save_results(results, args.output)
    
    # Generate HTML report if path is provided
    if args.html:
        generate_html_report(results, args.html, args.mode)
        print(f"HTML report saved to {args.html}")


if __name__ == "__main__":
    main()

