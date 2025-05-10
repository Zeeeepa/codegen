#!/usr/bin/env python3
"""
Script to compare two codebases or branches.

This script provides a command-line interface for comparing two codebases
or branches using the DiffAnalyzer.
"""

import argparse
import json
import logging
import os
import sys
import tempfile
import traceback
from typing import Dict, Any, Optional

from codegen_on_oss.analysis.diff_analyzer import DiffAnalyzer
from codegen_on_oss.snapshot.codebase_snapshot import CodebaseSnapshot, SnapshotManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Compare two codebases or branches")
    parser.add_argument(
        "--base-repo",
        required=True,
        help="Base repository URL or path",
    )
    parser.add_argument(
        "--head-repo",
        required=True,
        help="Head repository URL or path",
    )
    parser.add_argument(
        "--base-branch",
        default="main",
        help="Base branch (default: main)",
    )
    parser.add_argument(
        "--head-branch",
        default="main",
        help="Head branch (default: main)",
    )
    parser.add_argument(
        "--github-token",
        help="GitHub token for private repositories",
    )
    parser.add_argument(
        "--output",
        help="Output file for results (JSON)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "text"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Include detailed analysis in the results",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args()


def compare_codebases(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Compare two codebases or branches.

    Args:
        args: Command-line arguments

    Returns:
        Dictionary with comparison results
    """
    try:
        # Create temporary directory for snapshots
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize snapshot manager
            snapshot_manager = SnapshotManager(temp_dir)
            logger.info(f"Initialized snapshot manager in {temp_dir}")

            # Create snapshots from repositories
            logger.info(f"Creating base snapshot from {args.base_repo} ({args.base_branch})")
            base_snapshot = CodebaseSnapshot.create_from_repo(
                repo_url=args.base_repo,
                branch=args.base_branch,
                github_token=args.github_token,
            )
            logger.info(f"Base snapshot created with {len(base_snapshot.files)} files")

            logger.info(f"Creating head snapshot from {args.head_repo} ({args.head_branch})")
            head_snapshot = CodebaseSnapshot.create_from_repo(
                repo_url=args.head_repo,
                branch=args.head_branch,
                github_token=args.github_token,
            )
            logger.info(f"Head snapshot created with {len(head_snapshot.files)} files")

            # Initialize diff analyzer
            logger.info("Initializing diff analyzer")
            diff_analyzer = DiffAnalyzer(base_snapshot, head_snapshot)

            # Analyze differences
            logger.info("Analyzing file changes")
            file_changes = diff_analyzer.analyze_file_changes()
            logger.info(f"Found {len(file_changes)} file changes")
            
            logger.info("Analyzing function changes")
            function_changes = diff_analyzer.analyze_function_changes()
            logger.info(f"Found {len(function_changes)} function changes")
            
            logger.info("Analyzing complexity changes")
            complexity_changes = diff_analyzer.analyze_complexity_changes()
            logger.info(f"Found {len(complexity_changes)} complexity changes")

            # Assess risk
            logger.info("Assessing risk")
            risk_assessment = diff_analyzer.assess_risk()
            logger.info(f"Risk assessment completed")

            # Generate summary
            logger.info("Generating summary")
            summary = diff_analyzer.format_summary_text()
            logger.info(f"Summary generated")

            # Perform detailed analysis if requested
            detailed_analysis = None
            if args.detailed:
                logger.info("Performing detailed analysis")
                detailed_analysis = diff_analyzer.perform_detailed_analysis()
                logger.info("Detailed analysis completed")

            # Prepare results
            results = {
                "base_repo_url": args.base_repo,
                "head_repo_url": args.head_repo,
                "base_branch": args.base_branch,
                "head_branch": args.head_branch,
                "file_changes": file_changes,
                "function_changes": function_changes,
                "complexity_changes": complexity_changes,
                "risk_assessment": risk_assessment,
                "summary": summary,
            }

            if detailed_analysis:
                results["detailed_analysis"] = detailed_analysis

            return results

    except Exception as e:
        logger.error(f"Error comparing codebases: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


def format_results(results: Dict[str, Any], format_type: str) -> str:
    """
    Format comparison results.

    Args:
        results: Comparison results
        format_type: Output format (json, markdown, text)

    Returns:
        Formatted results
    """
    if format_type == "json":
        return json.dumps(results, indent=2)
    elif format_type == "markdown":
        return format_markdown(results)
    else:
        return format_text(results)


def format_markdown(results: Dict[str, Any]) -> str:
    """
    Format comparison results as Markdown.

    Args:
        results: Comparison results

    Returns:
        Markdown-formatted string
    """
    if "error" in results:
        return f"# Error Comparing Codebases\n\n{results['error']}"

    markdown = f"# Codebase Comparison Results\n\n"
    markdown += f"**Base Repository:** {results['base_repo_url']} ({results['base_branch']})\n"
    markdown += f"**Head Repository:** {results['head_repo_url']} ({results['head_branch']})\n\n"
    
    markdown += "## Summary\n\n"
    markdown += results["summary"].replace("\n", "\n\n")
    
    markdown += "\n\n## File Changes\n\n"
    for file, change_type in results["file_changes"].items():
        markdown += f"- **{file}**: {change_type}\n"
    
    markdown += "\n## Function Changes\n\n"
    for func, change_type in results["function_changes"].items():
        markdown += f"- **{func}**: {change_type}\n"
    
    markdown += "\n## Risk Assessment\n\n"
    for category, risk_level in results["risk_assessment"].items():
        markdown += f"- **{category}**: {risk_level}\n"
    
    if "detailed_analysis" in results:
        markdown += "\n## Detailed Analysis\n\n"
        
        markdown += "### Added Files\n\n"
        for file in results["detailed_analysis"]["added_files"]:
            markdown += f"- {file}\n"
        
        markdown += "\n### Removed Files\n\n"
        for file in results["detailed_analysis"]["removed_files"]:
            markdown += f"- {file}\n"
        
        markdown += "\n### Modified Files\n\n"
        for file in results["detailed_analysis"]["modified_files"]:
            markdown += f"- {file}\n"
        
        markdown += "\n### Potential Issues\n\n"
        for issue in results["detailed_analysis"]["potential_issues"]:
            markdown += f"- **{issue['category']} ({issue['risk_level']})**: {issue['description']}\n"
        
        markdown += "\n### Recommendations\n\n"
        for recommendation in results["detailed_analysis"]["recommendations"]:
            markdown += f"- {recommendation}\n"
    
    return markdown


def format_text(results: Dict[str, Any]) -> str:
    """
    Format comparison results as plain text.

    Args:
        results: Comparison results

    Returns:
        Text-formatted string
    """
    if "error" in results:
        return f"Error comparing codebases: {results['error']}"

    text = f"Codebase Comparison Results\n"
    text += f"=========================\n\n"
    text += f"Base Repository: {results['base_repo_url']} ({results['base_branch']})\n"
    text += f"Head Repository: {results['head_repo_url']} ({results['head_branch']})\n\n"
    
    text += "Summary\n-------\n\n"
    text += results["summary"]
    
    text += "\n\nFile Changes\n-----------\n\n"
    for file, change_type in results["file_changes"].items():
        text += f"{file}: {change_type}\n"
    
    text += "\nFunction Changes\n---------------\n\n"
    for func, change_type in results["function_changes"].items():
        text += f"{func}: {change_type}\n"
    
    text += "\nRisk Assessment\n--------------\n\n"
    for category, risk_level in results["risk_assessment"].items():
        text += f"{category}: {risk_level}\n"
    
    if "detailed_analysis" in results:
        text += "\nDetailed Analysis\n----------------\n\n"
        
        text += "Added Files:\n"
        for file in results["detailed_analysis"]["added_files"]:
            text += f"- {file}\n"
        
        text += "\nRemoved Files:\n"
        for file in results["detailed_analysis"]["removed_files"]:
            text += f"- {file}\n"
        
        text += "\nModified Files:\n"
        for file in results["detailed_analysis"]["modified_files"]:
            text += f"- {file}\n"
        
        text += "\nPotential Issues:\n"
        for issue in results["detailed_analysis"]["potential_issues"]:
            text += f"- {issue['category']} ({issue['risk_level']}): {issue['description']}\n"
        
        text += "\nRecommendations:\n"
        for recommendation in results["detailed_analysis"]["recommendations"]:
            text += f"- {recommendation}\n"
    
    return text


def main() -> None:
    """Main entry point for the script."""
    args = parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Compare codebases
    results = compare_codebases(args)

    # Format results
    formatted_results = format_results(results, args.format)

    # Save results to file if specified
    if args.output:
        logger.info(f"Saving results to {args.output}")
        with open(args.output, "w") as f:
            if args.format == "json":
                json.dump(results, f, indent=2)
            else:
                f.write(formatted_results)

    # Print results
    print(formatted_results)


if __name__ == "__main__":
    main()

