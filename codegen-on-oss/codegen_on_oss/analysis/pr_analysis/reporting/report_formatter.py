"""
Report Formatter

Formatter for analysis reports in various formats.
"""

import logging
from typing import Any, Dict, List

from codegen_on_oss.analysis.pr_analysis.core.analysis_context import AnalysisContext

logger = logging.getLogger(__name__)


class ReportFormatter:
    """
    Formatter for analysis reports in various formats.

    This class formats analysis results into various report formats.
    """

    def format_html_report(self, context: AnalysisContext, results: Dict[str, Any]) -> str:
        """
        Format analysis results as an HTML report.

        Args:
            context: The analysis context
            results: The analysis results

        Returns:
            The formatted HTML report
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

        # Create HTML report
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>PR Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #555; }}
                h3 {{ color: #777; }}
                .summary {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; }}
                .error {{ color: #d9534f; }}
                .warning {{ color: #f0ad4e; }}
                .info {{ color: #5bc0de; }}
                .issue {{ margin-bottom: 10px; padding: 10px; border-left: 4px solid #ddd; }}
                .issue.error {{ border-left-color: #d9534f; }}
                .issue.warning {{ border-left-color: #f0ad4e; }}
                .issue.info {{ border-left-color: #5bc0de; }}
                .code {{ background-color: #f8f8f8; padding: 10px; border-radius: 5px; font-family: monospace; }}
            </style>
        </head>
        <body>
            <h1>PR Analysis Report</h1>
            <div class="summary">
                <h2>Summary</h2>
                <p>PR #{context.pr_context.number}: {context.pr_context.title}</p>
                <p>Total Issues: {total_issues}</p>
                <p class="error">Errors: {error_count}</p>
                <p class="warning">Warnings: {warning_count}</p>
                <p class="info">Info: {info_count}</p>
            </div>
        """

        # Add rule results
        for rule_id, rule_result in results.items():
            rule_issues = rule_result.get("issues", [])
            if not rule_issues:
                continue

            # Get the rule name from the first issue
            rule_name = rule_issues[0].get("rule_name", rule_id) if rule_issues else rule_id

            html += f"""
            <h2>{rule_name}</h2>
            <p>Found {len(rule_issues)} issues</p>
            """

            for issue in rule_issues:
                severity = issue.get("severity", "info")
                severity_class = severity

                file_path = issue.get("file_path", "N/A")
                line_number = issue.get("line_number", "N/A")
                location = (
                    f"{file_path}:{line_number}"
                    if file_path != "N/A" and line_number != "N/A"
                    else file_path
                )

                html += f"""
                <div class="issue {severity_class}">
                    <h3>{location}</h3>
                    <p>{issue.get('message', 'No message')}</p>
                """

                if issue.get("code"):
                    html += f"""
                    <div class="code">
                        <pre>{issue['code']}</pre>
                    </div>
                    """

                if issue.get("suggestion"):
                    html += f"""
                    <p><strong>Suggestion:</strong> {issue['suggestion']}</p>
                    """

                html += """
                </div>
                """

        html += """
        </body>
        </html>
        """

        return html

    def format_text_report(self, context: AnalysisContext, results: Dict[str, Any]) -> str:
        """
        Format analysis results as a plain text report.

        Args:
            context: The analysis context
            results: The analysis results

        Returns:
            The formatted text report
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

        # Create text report
        text = f"PR Analysis Report\n"
        text += f"=================\n\n"
        text += f"PR #{context.pr_context.number}: {context.pr_context.title}\n\n"
        text += f"Summary:\n"
        text += f"- Total Issues: {total_issues}\n"
        text += f"- Errors: {error_count}\n"
        text += f"- Warnings: {warning_count}\n"
        text += f"- Info: {info_count}\n\n"

        # Add rule results
        for rule_id, rule_result in results.items():
            rule_issues = rule_result.get("issues", [])
            if not rule_issues:
                continue

            # Get the rule name from the first issue
            rule_name = rule_issues[0].get("rule_name", rule_id) if rule_issues else rule_id

            text += f"{rule_name}\n"
            text += f"{'-' * len(rule_name)}\n\n"
            text += f"Found {len(rule_issues)} issues:\n\n"

            for issue in rule_issues:
                severity = issue.get("severity", "info").upper()

                file_path = issue.get("file_path", "N/A")
                line_number = issue.get("line_number", "N/A")
                location = (
                    f"{file_path}:{line_number}"
                    if file_path != "N/A" and line_number != "N/A"
                    else file_path
                )

                text += f"[{severity}] {location}\n"
                text += f"{issue.get('message', 'No message')}\n"

                if issue.get("code"):
                    text += f"\n{issue['code']}\n\n"

                if issue.get("suggestion"):
                    text += f"Suggestion: {issue['suggestion']}\n"

                text += f"\n"

        return text
