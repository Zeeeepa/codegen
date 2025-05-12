#!/usr/bin/env python3
"""
Issue Analyzer Module

This module provides common functionality for detecting and tracking issues
across different types of code analyzers. It provides standardized issue
handling and categorization to ensure consistent issue reporting.
"""

import logging
from collections.abc import Callable
from typing import Any

from codegen_on_oss.analyzers.base_analyzer import BaseCodeAnalyzer
from codegen_on_oss.analyzers.issue_types import (
    Issue,
    IssueCategory,
    IssueSeverity,
)

# Configure logging
logger = logging.getLogger(__name__)


class IssueAnalyzer(BaseCodeAnalyzer):
    """
    Base class for analyzers that detect and report issues.

    This class builds on the BaseCodeAnalyzer to add standardized issue tracking,
    categorization, and reporting capabilities.
    """

    def __init__(self, **kwargs):
        """
        Initialize the issue analyzer.

        Args:
            **kwargs: Arguments to pass to the BaseCodeAnalyzer
        """
        super().__init__(**kwargs)
        self.issue_filters = []
        self.issue_handlers = {}
        self.issue_categories = set()
        self.register_default_filters()

    def register_default_filters(self):
        """Register default issue filters."""
        # Filter out issues in test files by default
        self.add_issue_filter(
            lambda issue: "test" in issue.file.lower(), "Skip issues in test files"
        )

        # Filter out issues in generated files by default
        self.add_issue_filter(
            lambda issue: "generated" in issue.file.lower(),
            "Skip issues in generated files",
        )

    def add_issue_filter(self, filter_func: Callable[[Issue], bool], description: str):
        """
        Add a filter function that determines if an issue should be skipped.

        Args:
            filter_func: Function that returns True if issue should be skipped
            description: Description of the filter
        """
        self.issue_filters.append((filter_func, description))

    def register_issue_handler(self, category: IssueCategory, handler: Callable):
        """
        Register a handler function for a specific issue category.

        Args:
            category: Issue category to handle
            handler: Function that will detect issues of this category
        """
        self.issue_handlers[category] = handler
        self.issue_categories.add(category)

    def should_skip_issue(self, issue: Issue) -> bool:
        """
        Check if an issue should be skipped based on registered filters.

        Args:
            issue: Issue to check

        Returns:
            True if the issue should be skipped, False otherwise
        """
        for filter_func, _ in self.issue_filters:
            try:
                if filter_func(issue):
                    return True
            except Exception as e:
                logger.debug(f"Error applying issue filter: {e}")

        return False

    def add_issue(self, issue: Issue):
        """
        Add an issue to the list if it passes all filters.

        Args:
            issue: Issue to add
        """
        if self.should_skip_issue(issue):
            return

        super().add_issue(issue)

    def detect_issues(
        self, categories: list[IssueCategory] | None = None
    ) -> dict[IssueCategory, list[Issue]]:
        """
        Detect issues across specified categories.

        Args:
            categories: Categories of issues to detect (defaults to all registered categories)

        Returns:
            Dictionary mapping categories to lists of issues
        """
        result = {}

        # Use all registered categories if none specified
        if not categories:
            categories = list(self.issue_categories)

        # Process each requested category
        for category in categories:
            if category in self.issue_handlers:
                # Clear existing issues of this category
                self.issues = [i for i in self.issues if i.category != category]

                # Run the handler to detect issues
                try:
                    handler = self.issue_handlers[category]
                    handler_result = handler()
                    result[category] = handler_result
                except Exception as e:
                    logger.exception(
                        f"Error detecting issues for category {category}: {e}"
                    )
                    result[category] = []
            else:
                logger.warning(f"No handler registered for issue category: {category}")
                result[category] = []

        return result

    def get_issues_by_category(self) -> dict[IssueCategory, list[Issue]]:
        """
        Group issues by category.

        Returns:
            Dictionary mapping categories to lists of issues
        """
        result = {}

        for issue in self.issues:
            if issue.category:
                if issue.category not in result:
                    result[issue.category] = []
                result[issue.category].append(issue)

        return result

    def get_issue_statistics(self) -> dict[str, Any]:
        """
        Get statistics about detected issues.

        Returns:
            Dictionary with issue statistics
        """
        issues_by_category = self.get_issues_by_category()

        return {
            "total": len(self.issues),
            "by_severity": {
                "critical": sum(
                    1
                    for issue in self.issues
                    if issue.severity == IssueSeverity.CRITICAL
                ),
                "error": sum(
                    1 for issue in self.issues if issue.severity == IssueSeverity.ERROR
                ),
                "warning": sum(
                    1
                    for issue in self.issues
                    if issue.severity == IssueSeverity.WARNING
                ),
                "info": sum(
                    1 for issue in self.issues if issue.severity == IssueSeverity.INFO
                ),
            },
            "by_category": {
                category.value: len(issues)
                for category, issues in issues_by_category.items()
            },
        }

    def format_issues_report(self) -> str:
        """
        Format issues as a readable report.

        Returns:
            Formatted string with issue report
        """
        report_lines = [
            "==== Issues Report ====",
            f"Total issues: {len(self.issues)}",
            "",
        ]

        # Group by severity
        issues_by_severity = {}
        for issue in self.issues:
            if issue.severity not in issues_by_severity:
                issues_by_severity[issue.severity] = []
            issues_by_severity[issue.severity].append(issue)

        # Add severity sections
        for severity in [
            IssueSeverity.CRITICAL,
            IssueSeverity.ERROR,
            IssueSeverity.WARNING,
            IssueSeverity.INFO,
        ]:
            if severity in issues_by_severity:
                report_lines.append(
                    f"==== {severity.value.upper()} ({len(issues_by_severity[severity])}) ===="
                )

                for issue in issues_by_severity[severity]:
                    location = (
                        f"{issue.file}:{issue.line}" if issue.line else issue.file
                    )
                    category = f"[{issue.category.value}]" if issue.category else ""
                    report_lines.append(f"{location} {category} {issue.message}")
                    if issue.suggestion:
                        report_lines.append(f"  Suggestion: {issue.suggestion}")

                report_lines.append("")

        return "\n".join(report_lines)
