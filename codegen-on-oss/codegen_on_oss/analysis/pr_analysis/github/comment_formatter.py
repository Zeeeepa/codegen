"""
Comment Formatter

Formatter for GitHub comments with analysis results.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class CommentFormatter:
    """
    Formatter for GitHub comments with analysis results.

    This class formats analysis results into readable GitHub comments.
    """

    def format_summary_comment(self, results: Dict[str, Any]) -> str:
        """
        Format a summary comment for the PR.

        Args:
            results: The analysis results to format

        Returns:
            A formatted comment string
        """
        # Extract summary information
        total_issues = 0
        error_count = 0
        warning_count = 0
        info_count = 0

        for rule_id, rule_result in results.items():
            summary = rule_result.get("summary", {})
            total_issues += summary.get("total_issues", 0)
            error_count += summary.get("error_count", 0)
            warning_count += summary.get("warning_count", 0)
            info_count += summary.get("info_count", 0)

        # Create comment header
        if total_issues == 0:
            header = "## 🎉 PR Analysis: No Issues Found\n\n"
            header += "Great job! No issues were found in this pull request.\n\n"
        else:
            header = f"## 🔍 PR Analysis: {total_issues} Issues Found\n\n"
            header += "The following issues were found in this pull request:\n\n"
            header += f"- 🚨 **Errors:** {error_count}\n"
            header += f"- ⚠️ **Warnings:** {warning_count}\n"
            header += f"- ℹ️ **Info:** {info_count}\n\n"

        # Add rule summaries
        comment = header
        comment += "### Analysis Results\n\n"

        for rule_id, rule_result in results.items():
            rule_issues = rule_result.get("issues", [])
            if not rule_issues:
                continue

            # Get the rule name from the first issue
            rule_name = rule_issues[0].get("rule_name", rule_id) if rule_issues else rule_id

            comment += f"#### {rule_name}\n\n"
            comment += f"Found {len(rule_issues)} issues:\n\n"

            # Add up to 5 issues as examples
            for i, issue in enumerate(rule_issues[:5]):
                severity = issue.get("severity", "info")
                severity_icon = (
                    "🚨" if severity == "error" else "⚠️" if severity == "warning" else "ℹ️"
                )

                file_path = issue.get("file_path")
                line_number = issue.get("line_number")
                location = (
                    f"{file_path}:{line_number}"
                    if file_path and line_number
                    else file_path if file_path else "N/A"
                )

                comment += (
                    f"{severity_icon} **{location}**: {issue.get('message', 'No message')}\n\n"
                )

            # Add a note if there are more issues
            if len(rule_issues) > 5:
                comment += f"... and {len(rule_issues) - 5} more issues.\n\n"

        # Add footer
        comment += "### Next Steps\n\n"

        if error_count > 0:
            comment += "🚨 **Please fix the errors before merging this PR.**\n\n"

        if warning_count > 0:
            comment += "⚠️ Consider addressing the warnings to improve code quality.\n\n"

        comment += "For more details, see the inline comments on specific files.\n"

        return comment

    def format_inline_comment(self, issue: Dict[str, Any]) -> str:
        """
        Format an inline comment for a specific issue.

        Args:
            issue: The issue to format

        Returns:
            A formatted comment string
        """
        severity = issue.get("severity", "info")
        severity_icon = "🚨" if severity == "error" else "⚠️" if severity == "warning" else "ℹ️"

        rule_name = issue.get("rule_name", issue.get("rule_id", "Unknown Rule"))

        comment = f"{severity_icon} **{rule_name}**\n\n"
        comment += f"{issue.get('message', 'No message')}\n\n"

        if issue.get("code"):
            comment += "```\n"
            comment += issue["code"]
            comment += "\n```\n\n"

        if issue.get("suggestion"):
            comment += f"**Suggestion:** {issue['suggestion']}\n"

        return comment
