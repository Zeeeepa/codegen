"""
Implementation Rules

Rules for validating implementation correctness in pull requests.
"""

import logging
from typing import Any, Dict, List, Optional

from codegen_on_oss.analysis.commit_analyzer import CommitAnalyzer
from codegen_on_oss.analysis.diff_analyzer import DiffAnalyzer
from codegen_on_oss.analysis.pr_analysis.core.analysis_context import AnalysisContext
from codegen_on_oss.analysis.pr_analysis.rules.base_rule import BaseRule

logger = logging.getLogger(__name__)


class ImplementationValidationRule(BaseRule):
    """
    Rule for validating implementation correctness in pull requests.

    This rule checks for issues such as:
    - Inconsistent implementation with requirements
    - Missing functionality
    - Incorrect error handling
    """

    rule_id: str = "implementation_validation"
    rule_name: str = "Implementation Validation"
    rule_description: str = "Checks for correct implementation of features and requirements."

    def analyze(self, context: AnalysisContext) -> Dict[str, Any]:
        """
        Analyze the PR for implementation correctness issues.

        Args:
            context: The analysis context containing PR and codebase information

        Returns:
            A dictionary containing the analysis results
        """
        logger.info("Running implementation validation analysis")

        # Use DiffAnalyzer to compare base and head codebases
        diff_analyzer = DiffAnalyzer()

        # Use CommitAnalyzer to analyze commit quality
        commit_analyzer = CommitAnalyzer()

        # Analyze implementation
        issues = []

        # Analyze diff between base and head
        try:
            diff_issues = self._analyze_diff(context, diff_analyzer)
            issues.extend(diff_issues)
        except Exception as e:
            logger.exception(f"Error analyzing diff: {e}")
            issues.append(
                self.create_issue(message=f"Error analyzing diff: {str(e)}", severity="error")
            )

        # Analyze commit quality
        try:
            commit_issues = self._analyze_commits(context, commit_analyzer)
            issues.extend(commit_issues)
        except Exception as e:
            logger.exception(f"Error analyzing commits: {e}")
            issues.append(
                self.create_issue(message=f"Error analyzing commits: {str(e)}", severity="error")
            )

        return {
            "issues": issues,
            "summary": {
                "total_issues": len(issues),
                "error_count": sum(1 for issue in issues if issue["severity"] == "error"),
                "warning_count": sum(1 for issue in issues if issue["severity"] == "warning"),
                "info_count": sum(1 for issue in issues if issue["severity"] == "info"),
            },
        }

    def _analyze_diff(
        self, context: AnalysisContext, diff_analyzer: DiffAnalyzer
    ) -> List[Dict[str, Any]]:
        """
        Analyze the diff between base and head codebases.

        Args:
            context: The analysis context
            diff_analyzer: The diff analyzer to use

        Returns:
            A list of issues found in the diff
        """
        issues = []

        # Get changed files
        changed_files = context.get_changed_files()

        # Analyze each changed file
        for file_path, file_info in changed_files.items():
            # Skip deleted files
            if file_info.get("status") == "deleted":
                continue

            # Get file diff
            file_diff = context.get_diff_for_file(file_path)
            if not file_diff:
                continue

            # Check for common implementation issues
            if "TODO" in file_diff or "FIXME" in file_diff:
                issues.append(
                    self.create_issue(
                        file_path=file_path,
                        message="File contains TODO or FIXME comments",
                        severity="warning",
                        suggestion="Resolve all TODOs and FIXMEs before merging.",
                    )
                )

            # Check for error handling
            if "try" in file_diff and "except" not in file_diff:
                issues.append(
                    self.create_issue(
                        file_path=file_path,
                        message="File contains try block without except block",
                        severity="error",
                        suggestion="Add proper exception handling to all try blocks.",
                    )
                )

            # Check for commented-out code
            if "# " in file_diff and len(file_diff.split("# ")) > 5:
                issues.append(
                    self.create_issue(
                        file_path=file_path,
                        message="File contains a large amount of commented-out code",
                        severity="warning",
                        suggestion="Remove commented-out code before merging.",
                    )
                )

        return issues

    def _analyze_commits(
        self, context: AnalysisContext, commit_analyzer: CommitAnalyzer
    ) -> List[Dict[str, Any]]:
        """
        Analyze the commits in the PR.

        Args:
            context: The analysis context
            commit_analyzer: The commit analyzer to use

        Returns:
            A list of issues found in the commits
        """
        issues = []

        # Get PR description
        pr_description = context.pr_context.body or ""

        # Check if PR description mentions specific requirements
        requirements = self._extract_requirements(pr_description)

        # Check if all requirements are implemented
        if requirements:
            # This would be implemented to check if all requirements are implemented
            # For now, we'll just add a placeholder issue
            issues.append(
                self.create_issue(
                    message="PR contains requirements that may not be fully implemented",
                    severity="info",
                    suggestion="Verify that all requirements mentioned in the PR description are implemented.",
                )
            )

        return issues

    def _extract_requirements(self, pr_description: str) -> List[str]:
        """
        Extract requirements from the PR description.

        Args:
            pr_description: The PR description

        Returns:
            A list of requirements extracted from the PR description
        """
        requirements = []

        # Look for common requirement patterns
        if "- [ ]" in pr_description:
            # Extract checklist items
            for line in pr_description.split("\n"):
                if line.strip().startswith("- [ ]"):
                    requirements.append(line.strip()[6:].strip())

        return requirements
