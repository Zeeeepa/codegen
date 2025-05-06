"""
Report generator for PR analysis.

This module provides the ReportGenerator class, which is responsible for
generating analysis reports.
"""

import logging
from typing import Dict, List, Any

from codegen_on_oss.analysis.pr_analysis.core.analysis_context import AnalysisContext
from codegen_on_oss.analysis.pr_analysis.reporting.report_formatter import ReportFormatter

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generator for analysis reports.

    This class is responsible for generating analysis reports from rule results.

    Attributes:
        context: Analysis context
        formatter: Report formatter
    """

    def __init__(self, context: AnalysisContext):
        """
        Initialize the report generator.

        Args:
            context: Analysis context
        """
        self.context = context
        self.formatter = ReportFormatter(context)

    def generate_report(self, rule_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a report from rule results.

        Args:
            rule_results: Rule results

        Returns:
            Report dictionary
        """
        # Generate summary
        summary = self._generate_summary(rule_results)

        # Generate recommendations
        recommendations = self._generate_recommendations(rule_results)

        # Create the report
        report = {
            "summary": summary,
            "rule_results": rule_results,
            "recommendations": recommendations,
        }

        return report

    def format_report_as_markdown(self, report: Dict[str, Any]) -> str:
        """
        Format a report as Markdown.

        Args:
            report: Report to format

        Returns:
            Markdown string
        """
        return self.formatter.format_report_as_markdown(report)

    def format_report_as_json(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a report as JSON.

        Args:
            report: Report to format

        Returns:
            JSON-serializable dictionary
        """
        return self.formatter.format_report_as_json(report)

    def format_report_for_github(self, report: Dict[str, Any]) -> str:
        """
        Format a report for GitHub comment.

        Args:
            report: Report to format

        Returns:
            Markdown string suitable for GitHub comment
        """
        return self.formatter.format_report_for_github(report)

    def _generate_summary(self, rule_results: Dict[str, Dict[str, Any]]) -> str:
        """
        Generate a summary from rule results.

        Args:
            rule_results: Rule results

        Returns:
            Summary string
        """
        # Count rule results by status
        success_count = 0
        warning_count = 0
        error_count = 0

        for result in rule_results.values():
            status = result.get("status", "unknown")
            if status == "success":
                success_count += 1
            elif status == "warning":
                warning_count += 1
            elif status == "error":
                error_count += 1

        # Generate summary
        summary = f"Analysis found {success_count} successful checks, {warning_count} warnings, and {error_count} errors."

        return summary

    def _generate_recommendations(self, rule_results: Dict[str, Dict[str, Any]]) -> List[str]:
        """
        Generate recommendations from rule results.

        Args:
            rule_results: Rule results

        Returns:
            List of recommendations
        """
        recommendations = []

        # Add recommendations from rule results
        for result in rule_results.values():
            if "recommendations" in result:
                recommendations.extend(result["recommendations"])

        # Add general recommendations based on rule results
        if any(result.get("status") == "error" for result in rule_results.values()):
            recommendations.append("Fix all errors before merging the pull request.")
        elif any(result.get("status") == "warning" for result in rule_results.values()):
            recommendations.append("Consider addressing warnings before merging the pull request.")

        return recommendations

