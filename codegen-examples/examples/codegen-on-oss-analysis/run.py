#!/usr/bin/env python3
"""
Repository Analysis Example using codegen-on-oss.

This example demonstrates how to use the codegen-on-oss component to analyze
a repository and generate insights about its structure, dependencies, and code quality.
"""

import argparse
import json
import os
import sys
from typing import Dict, Any, Optional

# Import the codegen-on-oss API
from codegen_on_oss.api import CodegenOnOSS
from codegen_on_oss.helpers import save_results, setup_logging


def format_dependency_graph(dependencies: Dict[str, Any]) -> Dict[str, Any]:
    """Format the dependency graph for better readability.
    
    Args:
        dependencies: Raw dependency data from the analysis.
        
    Returns:
        Formatted dependency graph.
    """
    formatted = {
        "internal": [],
        "external": []
    }
    
    # Process internal dependencies
    for module, deps in dependencies.get("internal", {}).items():
        for dep in deps:
            formatted["internal"].append({
                "from": module,
                "to": dep["module"],
                "type": dep["type"]
            })
    
    # Process external dependencies
    for pkg, version in dependencies.get("external", {}).items():
        formatted["external"].append({
            "name": pkg,
            "version": version
        })
    
    return formatted


def format_integrity_results(integrity_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format code integrity results for better readability.
    
    Args:
        integrity_data: Raw integrity data from the analysis.
        
    Returns:
        Formatted integrity results.
    """
    issues = []
    error_count = 0
    warning_count = 0
    info_count = 0
    
    for file_path, file_issues in integrity_data.get("issues", {}).items():
        for issue in file_issues:
            severity = issue.get("severity", "info")
            
            if severity == "error":
                error_count += 1
            elif severity == "warning":
                warning_count += 1
            else:
                info_count += 1
            
            issues.append({
                "file": file_path,
                "line": issue.get("line", 0),
                "severity": severity,
                "message": issue.get("message", "")
            })
    
    return {
        "issues": issues,
        "summary": {
            "error_count": error_count,
            "warning_count": warning_count,
            "info_count": info_count
        }
    }


def analyze_repository(
    repo_url: str,
    include_integrity: bool = False,
    branch: Optional[str] = None
) -> Dict[str, Any]:
    """Analyze a repository and return formatted results.
    
    Args:
        repo_url: URL of the repository to analyze.
        include_integrity: Whether to include code integrity analysis.
        branch: Optional branch to analyze.
        
    Returns:
        Dictionary containing formatted analysis results.
    """
    # Initialize the API
    api = CodegenOnOSS()
    logger = setup_logging(level="INFO")
    
    # Parse the repository
    logger.info(f"Parsing repository: {repo_url}")
    repo_data = api.parse_repository(repo_url, branch=branch)
    
    # Get repository metadata
    commit = repo_data.get("commit", "unknown")
    branch_name = repo_data.get("branch", "unknown")
    
    # Analyze the codebase
    logger.info("Analyzing codebase structure and dependencies")
    analysis = api.analyze_codebase(repo_data, analysis_type="full")
    
    # Format the results
    file_count = len(repo_data.get("files", []))
    directory_count = len(repo_data.get("directories", []))
    
    # Calculate language breakdown
    language_breakdown = {}
    for file_path, file_info in repo_data.get("files", {}).items():
        lang = file_info.get("language", "Other")
        language_breakdown[lang] = language_breakdown.get(lang, 0) + 1
    
    # Format dependencies
    dependencies = format_dependency_graph(analysis.get("dependencies", {}))
    
    # Build the result dictionary
    result = {
        "repository": {
            "url": repo_url,
            "commit": commit,
            "branch": branch_name
        },
        "structure": {
            "file_count": file_count,
            "directory_count": directory_count,
            "language_breakdown": language_breakdown
        },
        "dependencies": dependencies
    }
    
    # Add integrity analysis if requested
    if include_integrity:
        logger.info("Performing code integrity analysis")
        integrity_data = api.analyze_code_integrity(repo_data)
        result["integrity"] = format_integrity_results(integrity_data)
    
    return result


def run(repo_url: str, output_path: Optional[str] = None, include_integrity: bool = False, branch: Optional[str] = None):
    """Run the repository analysis example.
    
    This function demonstrates how to use the codegen-on-oss component to analyze
    a repository and generate insights about its structure, dependencies, and code quality.
    
    Args:
        repo_url: URL of the repository to analyze.
        output_path: Optional path to save the results to.
        include_integrity: Whether to include code integrity analysis.
        branch: Optional branch to analyze.
        
    Returns:
        Dictionary containing analysis results.
    """
    # Analyze the repository
    results = analyze_repository(repo_url, include_integrity, branch)
    
    # Save results if output path is provided
    if output_path:
        save_results(results, output_path)
        print(f"Results saved to {output_path}")
    else:
        # Print a summary to the console
        print(f"\nRepository Analysis Summary for {repo_url}")
        print(f"Commit: {results['repository']['commit']}")
        print(f"Branch: {results['repository']['branch']}")
        print(f"Files: {results['structure']['file_count']}")
        print(f"Directories: {results['structure']['directory_count']}")
        
        print("\nLanguage Breakdown:")
        for lang, count in results['structure']['language_breakdown'].items():
            print(f"  {lang}: {count} files")
        
        if include_integrity:
            print("\nCode Integrity:")
            summary = results['integrity']['summary']
            print(f"  Errors: {summary['error_count']}")
            print(f"  Warnings: {summary['warning_count']}")
            print(f"  Info: {summary['info_count']}")
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze a repository using codegen-on-oss")
    parser.add_argument("--repo", required=True, help="Repository URL to analyze")
    parser.add_argument("--output", help="Path to save the results to")
    parser.add_argument("--integrity", action="store_true", help="Include code integrity analysis")
    parser.add_argument("--branch", help="Branch to analyze")
    
    args = parser.parse_args()
    
    try:
        run(args.repo, args.output, args.integrity, args.branch)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
