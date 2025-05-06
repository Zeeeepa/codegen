"""
Code Integrity Rules

Rules for checking code integrity in pull requests.
"""

import logging
from typing import Any, Dict, List, Optional

from codegen_on_oss.analysis.code_integrity_analyzer import CodeIntegrityAnalyzer
from codegen_on_oss.analysis.pr_analysis.core.analysis_context import AnalysisContext
from codegen_on_oss.analysis.pr_analysis.rules.base_rule import BaseRule

logger = logging.getLogger(__name__)


class CodeIntegrityRule(BaseRule):
    """
    Rule for checking code integrity in pull requests.

    This rule uses the CodeIntegrityAnalyzer to detect issues such as:
    - Undefined variables
    - Unused imports
    - Type mismatches
    - Parameter usage errors
    """

    rule_id: str = "code_integrity"
    rule_name: str = "Code Integrity"
    rule_description: str = (
        "Checks for code integrity issues such as undefined variables, unused imports, and type mismatches."
    )

    def analyze(self, context: AnalysisContext) -> Dict[str, Any]:
        """
        Analyze the PR for code integrity issues.

        Args:
            context: The analysis context containing PR and codebase information

        Returns:
            A dictionary containing the analysis results
        """
        logger.info("Running code integrity analysis")

        # Get changed files
        changed_files = context.get_changed_files()

        # Create analyzer
        analyzer = CodeIntegrityAnalyzer()

        # Analyze each changed file
        issues = []
        for file_path, file_info in changed_files.items():
            # Skip deleted files
            if file_info.get("status") == "deleted":
                continue

            # Get file content
            file_content = context.get_file_content(file_path, "head")
            if not file_content:
                continue

            # Analyze file
            try:
                file_issues = analyzer.analyze_file_content(file_content, file_path)
                for issue in file_issues:
                    issues.append(
                        self.create_issue(
                            file_path=file_path,
                            line_number=issue.get("line_number"),
                            message=issue.get("message", ""),
                            severity=issue.get("severity", "warning"),
                            code=issue.get("code"),
                            suggestion=issue.get("suggestion"),
                        )
                    )
            except Exception as e:
                logger.exception(f"Error analyzing file {file_path}: {e}")
                issues.append(
                    self.create_issue(
                        file_path=file_path,
                        message=f"Error analyzing file: {str(e)}",
                        severity="error",
                    )
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
