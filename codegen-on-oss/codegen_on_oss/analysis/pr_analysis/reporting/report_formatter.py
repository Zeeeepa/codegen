"""
Report formatter for PR analysis.

This module provides the ReportFormatter class, which is responsible for
formatting analysis reports in different formats.
"""

import logging
from typing import Dict, Any

from codegen_on_oss.analysis.pr_analysis.core.analysis_context import AnalysisContext

logger = logging.getLogger(__name__)


class ReportFormatter:
    """
    Formatter for analysis reports.

    This class is responsible for formatting analysis reports in different formats.

    Attributes:
        context: Analysis context
    """

    def __init__(self, context: AnalysisContext):
        """
        Initialize the report formatter.

        Args:
            context: Analysis context
        """
        self.context = context

    def format_report_as_markdown(self, report: Dict[str, Any]) -> str:
        """
        Format a report as Markdown.

        Args:
            report: Report to format

        Returns:
            Markdown string
        """
        markdown = f"# PR Analysis Report\n\n"

        # Add repository and PR information
        markdown += f"## Repository: {self.context.repository.full_name}\n\n"
        markdown += f"## Pull Request: #{self.context.pull_request.number} - {self.context.pull_request.title}\n\n"

        # Add summary
        markdown += f"## Summary\n\n"
        if "summary" in report:
            markdown += f"{report['summary']}\n\n"
        else:
            markdown += f"No summary available.\n\n"

        # Add rule results
        markdown += f"## Rule Results\n\n"
        if "rule_results" in report:
            for rule_id, result in report["rule_results"].items():
                status = result.get("status", "unknown")
                message = result.get("message", "No message")
                details = result.get("details", {})

                if status == "success":
                    markdown += f"### ✅ {rule_id}: {message}\n\n"
                elif status == "warning":
                    markdown += f"### ⚠️ {rule_id}: {message}\n\n"
                elif status == "error":
                    markdown += f"### ❌ {rule_id}: {message}\n\n"
                else:
                    markdown += f"### ❓ {rule_id}: {message}\n\n"

                if details:
                    markdown += f"**Details:**\n\n"
                    for key, value in details.items():
                        markdown += f"- {key}: {value}\n"
                    markdown += f"\n"
        else:
            markdown += f"No rule results available.\n\n"

        # Add recommendations
        markdown += f"## Recommendations\n\n"
        if "recommendations" in report:
            for recommendation in report["recommendations"]:
                markdown += f"- {recommendation}\n"
        else:
            markdown += f"No recommendations available.\n\n"

        return markdown

    def format_report_as_json(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a report as JSON.

        Args:
            report: Report to format

        Returns:
            JSON-serializable dictionary
        """
        return {
            "repository": {
                "full_name": self.context.repository.full_name,
                "url": self.context.repository.url,
            },
            "pull_request": {
                "number": self.context.pull_request.number,
                "title": self.context.pull_request.title,
                "url": self.context.pull_request.url,
            },
            "report": report,
        }

    def format_report_for_github(self, report: Dict[str, Any]) -> str:
        """
        Format a report for GitHub comment.

        Args:
            report: Report to format

        Returns:
            Markdown string suitable for GitHub comment
        """
        # Start with a summary
        markdown = f"## PR Analysis Report\n\n"

        # Add overall status
        success_count = 0
        warning_count = 0
        error_count = 0

        if "rule_results" in report:
            for result in report["rule_results"].values():
                status = result.get("status", "unknown")
                if status == "success":
                    success_count += 1
                elif status == "warning":
                    warning_count += 1
                elif status == "error":
                    error_count += 1

        if error_count > 0:
            markdown += f"### ❌ Analysis found {error_count} errors, {warning_count} warnings, and {success_count} successful checks.\n\n"
        elif warning_count > 0:
            markdown += f"### ⚠️ Analysis found {warning_count} warnings and {success_count} successful checks.\n\n"
        else:
            markdown += f"### ✅ Analysis found {success_count} successful checks.\n\n"

        # Add rule results
        if "rule_results" in report:
            markdown += f"### Rule Results\n\n"
            for rule_id, result in report["rule_results"].items():
                status = result.get("status", "unknown")
                message = result.get("message", "No message")

                if status == "success":
                    markdown += f"- ✅ **{rule_id}**: {message}\n"
                elif status == "warning":
                    markdown += f"- ⚠️ **{rule_id}**: {message}\n"
                elif status == "error":
                    markdown += f"- ❌ **{rule_id}**: {message}\n"
                else:
                    markdown += f"- ❓ **{rule_id}**: {message}\n"
            markdown += f"\n"

        # Add recommendations
        if "recommendations" in report and report["recommendations"]:
            markdown += f"### Recommendations\n\n"
            for recommendation in report["recommendations"]:
                markdown += f"- {recommendation}\n"
            markdown += f"\n"

        return markdown

