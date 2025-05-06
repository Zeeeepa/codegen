#!/usr/bin/env python3
"""
Script to analyze a pull request.

This script provides a command-line interface for analyzing a pull request
using the SWEHarnessAgent.
"""

import argparse
import json
import logging
import os
import sys
import traceback
from typing import Any, Dict, Optional

from codegen_on_oss.analysis.swe_harness_agent import SWEHarnessAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Analyze a pull request")
    parser.add_argument(
        "--repo",
        required=True,
        help="Repository URL or owner/repo string",
    )
    parser.add_argument(
        "--pr",
        type=int,
        required=True,
        help="Pull request number",
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
        "--post-comment",
        action="store_true",
        help="Post a comment to the PR with the analysis results",
    )
    parser.add_argument(
        "--include-file-content",
        action="store_true",
        help="Include file content in the results",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args()


def analyze_pr(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Analyze a pull request.

    Args:
        args: Command-line arguments

    Returns:
        Dictionary with analysis results
    """
    try:
        # Initialize SWE harness agent
        logger.info(f"Initializing SWE harness agent for PR analysis: {args.repo}#{args.pr}")
        agent = SWEHarnessAgent(github_token=args.github_token)

        # Analyze pull request
        logger.info(f"Analyzing pull request: {args.repo}#{args.pr} (detailed: {args.detailed})")
        analysis_results = agent.analyze_pr(
            repo=args.repo,
            pr_number=args.pr,
            detailed=args.detailed,
        )
        logger.info(f"PR analysis completed for {args.repo}#{args.pr}")

        # Post comment if requested
        if args.post_comment:
            logger.info(f"Posting comment to PR: {args.repo}#{args.pr}")
            comment = agent.create_comment_for_pr(args.repo, args.pr, analysis_results)
            comment_posted = agent.post_pr_comment(args.repo, args.pr, comment)
            analysis_results["comment_posted"] = comment_posted
            analysis_results["comment"] = comment
            logger.info(f"Comment posted to PR: {args.repo}#{args.pr}")

        # Get file content if requested
        if args.include_file_content:
            logger.info(f"Retrieving file content for PR: {args.repo}#{args.pr}")
            file_content = agent.get_pr_file_content(args.repo, args.pr)
            analysis_results["file_content"] = file_content
            logger.info(f"Retrieved content for {len(file_content) if file_content else 0} files")

        return analysis_results

    except Exception as e:
        logger.error(f"Error analyzing pull request: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


def format_results(results: Dict[str, Any], format_type: str) -> str:
    """
    Format analysis results.

    Args:
        results: Analysis results
        format_type: Output format (json, markdown, text)

    Returns:
        Formatted results
    """
    if format_type == "json":
        # Remove file content from JSON output to avoid excessive output
        if "file_content" in results:
            results_copy = results.copy()
            results_copy["file_content"] = f"[{len(results['file_content'])} files]"
            return json.dumps(results_copy, indent=2)
        return json.dumps(results, indent=2)
    elif format_type == "markdown":
        return format_markdown(results)
    else:
        return format_text(results)


def format_markdown(results: Dict[str, Any]) -> str:
    """
    Format analysis results as Markdown.

    Args:
        results: Analysis results

    Returns:
        Markdown-formatted string
    """
    if "error" in results:
        return f"# Error Analyzing Pull Request\n\n{results['error']}"

    markdown = f"# Pull Request Analysis: #{results.get('pr_number', '')}\n\n"

    if "is_properly_implemented" in results:
        if results["is_properly_implemented"]:
            markdown += "## ✅ Properly Implemented\n\n"
        else:
            markdown += "## ❌ Issues Detected\n\n"

    if "quality_score" in results:
        markdown += f"**Quality Score:** {results['quality_score']}/10.0"
        if "overall_assessment" in results:
            markdown += f" - {results['overall_assessment']}"
        markdown += "\n\n"

    if "summary" in results:
        markdown += "## Summary\n\n"
        markdown += results["summary"] + "\n\n"

    if "issues" in results and results["issues"]:
        markdown += "## Issues\n\n"
        for issue in results["issues"]:
            markdown += f"- {issue}\n"
        markdown += "\n"

    if "recommendations" in results and results["recommendations"]:
        markdown += "## Recommendations\n\n"
        for recommendation in results["recommendations"]:
            markdown += f"- {recommendation}\n"
        markdown += "\n"

    if "file_content" in results:
        markdown += f"## Files Changed ({len(results['file_content'])})\n\n"
        for filename in results["file_content"]:
            markdown += f"- {filename}\n"

    return markdown


def format_text(results: Dict[str, Any]) -> str:
    """
    Format analysis results as plain text.

    Args:
        results: Analysis results

    Returns:
        Text-formatted string
    """
    if "error" in results:
        return f"Error analyzing pull request: {results['error']}"

    text = f"Pull Request Analysis: #{results.get('pr_number', '')}\n"
    text += f"=======================================\n\n"

    if "is_properly_implemented" in results:
        if results["is_properly_implemented"]:
            text += "✅ Properly Implemented\n\n"
        else:
            text += "❌ Issues Detected\n\n"

    if "quality_score" in results:
        text += f"Quality Score: {results['quality_score']}/10.0"
        if "overall_assessment" in results:
            text += f" - {results['overall_assessment']}"
        text += "\n\n"

    if "summary" in results:
        text += "Summary\n-------\n\n"
        text += results["summary"] + "\n\n"

    if "issues" in results and results["issues"]:
        text += "Issues\n------\n\n"
        for issue in results["issues"]:
            text += f"- {issue}\n"
        text += "\n"

    if "recommendations" in results and results["recommendations"]:
        text += "Recommendations\n---------------\n\n"
        for recommendation in results["recommendations"]:
            text += f"- {recommendation}\n"
        text += "\n"

    if "file_content" in results:
        text += f"Files Changed ({len(results['file_content'])})\n"
        text += f"------------------\n\n"
        for filename in results["file_content"]:
            text += f"- {filename}\n"

    return text


def main() -> None:
    """Main entry point for the script."""
    args = parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Set GitHub token from environment if not provided
    if not args.github_token:
        args.github_token = os.environ.get("GITHUB_TOKEN")

    # Analyze pull request
    results = analyze_pr(args)

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
