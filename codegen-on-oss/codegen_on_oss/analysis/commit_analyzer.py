"""
Commit Analyzer Module

This module provides functionality for analyzing commits by comparing
the codebase before and after the commit.
"""

import logging
import os
from typing import Any

from codegen_on_oss.analysis.diff_analyzer import DiffAnalyzer
from codegen_on_oss.snapshot.codebase_snapshot import SnapshotManager

logger = logging.getLogger(__name__)


class CommitAnalyzer:
    """
    A class for analyzing commits by comparing snapshots of the codebase
    before and after the commit.
    """

    def __init__(
        self,
        snapshot_manager: SnapshotManager | None = None,
        github_token: str | None = None,
    ):
        """
        Initialize a new CommitAnalyzer.

        Args:
            snapshot_manager: Optional SnapshotManager to use for creating and retrieving snapshots
            github_token: Optional GitHub token for accessing private repositories
        """
        self.snapshot_manager = snapshot_manager or SnapshotManager()
        self.github_token = github_token

    def analyze_commit(
        self, repo_url: str, base_commit: str, head_commit: str
    ) -> dict[str, Any]:
        """
        Analyze a commit by comparing the codebase before and after the commit.

        Args:
            repo_url: The repository URL or owner/repo string
            base_commit: The base commit SHA (before the changes)
            head_commit: The head commit SHA (after the changes)

        Returns:
            A dictionary with analysis results
        """
        # Check if we already have snapshots for these commits
        base_snapshot = self.snapshot_manager.get_snapshot_by_commit(base_commit)
        head_snapshot = self.snapshot_manager.get_snapshot_by_commit(head_commit)

        # Create snapshots if they don't exist
        if not base_snapshot:
            logger.info(f"Creating snapshot for base commit {base_commit}")
            base_codebase = self.snapshot_manager.create_codebase_from_repo(
                repo_url, base_commit, self.github_token
            )
            base_snapshot = self.snapshot_manager.create_snapshot(
                base_codebase, base_commit
            )

        if not head_snapshot:
            logger.info(f"Creating snapshot for head commit {head_commit}")
            head_codebase = self.snapshot_manager.create_codebase_from_repo(
                repo_url, head_commit, self.github_token
            )
            head_snapshot = self.snapshot_manager.create_snapshot(
                head_codebase, head_commit
            )

        # Analyze the differences between the snapshots
        diff_analyzer = DiffAnalyzer(base_snapshot, head_snapshot)

        # Get the analysis results
        summary = diff_analyzer.get_summary()
        high_risk_changes = diff_analyzer.get_high_risk_changes()

        # Evaluate the commit quality
        quality_assessment = self._assess_commit_quality(diff_analyzer)

        return {
            "summary": summary,
            "high_risk_changes": high_risk_changes,
            "quality_assessment": quality_assessment,
            "base_snapshot_id": base_snapshot.snapshot_id,
            "head_snapshot_id": head_snapshot.snapshot_id
        }

    def _assess_commit_quality(self, diff_analyzer: DiffAnalyzer) -> dict[str, Any]:
        """
        Assess the quality of a commit based on the diff analysis.

        Args:
            diff_analyzer: The DiffAnalyzer instance with the analysis results

        Returns:
            A dictionary with quality assessment metrics
        """
        # Get analysis results with fallbacks for None values
        summary = diff_analyzer.get_summary() or {}
        high_risk = diff_analyzer.get_high_risk_changes() or {}

        # Initialize quality metrics
        issues: list[str] = []
        warnings: list[str] = []
        positive_aspects: list[str] = []

        quality: dict[str, Any] = {
            "score": 0.0,  # 0.0 to 10.0
            "issues": issues,
            "warnings": warnings,
            "positive_aspects": positive_aspects,
            "overall_assessment": "",
            "is_properly_implemented": False,
        }

        # Start with a perfect score and deduct points for issues
        score = 10.0

        # Check for high-risk changes
        complexity_increases = high_risk.get("complexity_increases", [])
        if complexity_increases:
            num_increases = len(complexity_increases)
            if num_increases > 5:
                score -= 2.0
                quality["issues"].append(
                    f"Significant complexity increases in {num_increases} functions"
                )
            elif num_increases > 0:
                score -= 0.5
                quality["warnings"].append(
                    f"Complexity increases in {num_increases} functions"
                )

        core_file_changes = high_risk.get("core_file_changes", [])
        if core_file_changes:
            num_core_changes = len(core_file_changes)
            if num_core_changes > 3:
                score -= 1.5
                quality["issues"].append(
                    f"Changes to {num_core_changes} core files with many dependencies"
                )
            elif num_core_changes > 0:
                score -= 0.5
                quality["warnings"].append(f"Changes to {num_core_changes} core files")

        interface_changes = high_risk.get("interface_changes", [])
        if interface_changes:
            num_interface_changes = len(interface_changes)
            if num_interface_changes > 3:
                score -= 1.5
                quality["issues"].append(
                    f"Interface changes to {num_interface_changes} functions"
                )
            elif num_interface_changes > 0:
                score -= 0.5
                quality["warnings"].append(
                    f"Interface changes to {num_interface_changes} functions"
                )

        # Check for positive aspects
        complexity_changes = summary.get("complexity_changes", {})
        decreased = complexity_changes.get("decreased", 0)
        increased = complexity_changes.get("increased", 0)
        if decreased > increased:
            score += 0.5
            quality["positive_aspects"].append("Overall complexity decreased")

        function_changes = summary.get("function_changes", {})
        added = function_changes.get("added", 0)
        deleted = function_changes.get("deleted", 0)
        if added > 0 and deleted == 0:
            score += 0.5
            quality["positive_aspects"].append(
                "Added new functionality without removing existing functions"
            )

        # Adjust score based on the size of the commit
        file_changes = summary.get("file_changes", {})
        total_changes = (
            file_changes.get("added", 0)
            + file_changes.get("deleted", 0)
            + file_changes.get("modified", 0)
        )

        # Very large commits are often problematic
        if total_changes > 50:
            score -= 1.0
            quality["warnings"].append(
                f"Very large commit with {total_changes} file changes"
            )
        # Small, focused commits are good
        elif total_changes < 5:
            score += 0.5
            quality["positive_aspects"].append("Small, focused commit")

        # Ensure score is within bounds
        score = max(0.0, min(10.0, score))
        quality["score"] = round(score, 1)

        # Determine overall assessment
        if score >= 9.0:
            quality["overall_assessment"] = "Excellent"
            quality["is_properly_implemented"] = True
        elif score >= 7.5:
            quality["overall_assessment"] = "Good"
            quality["is_properly_implemented"] = True
        elif score >= 6.0:
            quality["overall_assessment"] = "Satisfactory"
            quality["is_properly_implemented"] = True
        elif score >= 4.0:
            quality["overall_assessment"] = "Needs Improvement"
            quality["is_properly_implemented"] = False
        else:
            quality["overall_assessment"] = "Poor"
            quality["is_properly_implemented"] = False

        return quality

    def format_analysis_report(self, analysis_results: dict[str, Any]) -> str:
        """
        Format the analysis results as a human-readable report.

        Args:
            analysis_results: The analysis results from analyze_commit

        Returns:
            A formatted string with the analysis report
        """
        # Safely access nested dictionaries with .get() method
        summary = analysis_results.get("summary", {})
        quality = analysis_results.get("quality_assessment", {})
        high_risk = analysis_results.get("high_risk_changes", {})

        # Get values with fallbacks
        score = quality.get("score", 0.0)
        assessment = quality.get("overall_assessment", "Unknown")
        is_properly_implemented = quality.get("is_properly_implemented", False)

        # File changes
        file_changes = summary.get("file_changes", {})
        files_added = file_changes.get("added", 0)
        files_deleted = file_changes.get("deleted", 0)
        files_modified = file_changes.get("modified", 0)

        # Function changes
        function_changes = summary.get("function_changes", {})
        funcs_added = function_changes.get("added", 0)
        funcs_deleted = function_changes.get("deleted", 0)
        funcs_modified = function_changes.get("modified", 0)

        # Class changes
        class_changes = summary.get("class_changes", {})
        classes_added = class_changes.get("added", 0)
        classes_deleted = class_changes.get("deleted", 0)
        classes_modified = class_changes.get("modified", 0)

        # Complexity changes
        complexity_changes = summary.get("complexity_changes", {})
        complexity_increased = complexity_changes.get("increased", 0)
        complexity_decreased = complexity_changes.get("decreased", 0)

        report = f"""
Commit Analysis Report
=====================

Quality Score: {score}/10.0 - {assessment}
Properly Implemented: {"Yes" if is_properly_implemented else "No"}

Summary:
- Files: {files_added} added, {files_deleted} deleted, {files_modified} modified
- Functions: {funcs_added} added, {funcs_deleted} deleted, {funcs_modified} modified
- Classes: {classes_added} added, {classes_deleted} deleted, {classes_modified} modified
- Complexity: {complexity_increased} functions increased, {complexity_decreased} decreased
"""

        # Add issues if there are any
        issues = quality.get("issues", [])
        if issues:
            report += "\nIssues:\n"
            for issue in issues:
                report += f"- {issue}\n"

        # Add warnings if there are any
        warnings = quality.get("warnings", [])
        if warnings:
            report += "\nWarnings:\n"
            for warning in warnings:
                report += f"- {warning}\n"

        # Add positive aspects if there are any
        positive_aspects = quality.get("positive_aspects", [])
        if positive_aspects:
            report += "\nPositive Aspects:\n"
            for aspect in positive_aspects:
                report += f"- {aspect}\n"

        # Add high risk changes
        complexity_increases = high_risk.get("complexity_increases", [])
        if complexity_increases:
            report += "\nSignificant Complexity Increases:\n"
            for item in complexity_increases[:5]:  # Limit to top 5
                function_name = item.get("function", "Unknown")
                original = item.get("original", 0)
                modified = item.get("modified", 0)
                delta = item.get("delta", 0)
                percent_change = item.get("percent_change", 0.0)
                report += f"- {function_name}: {original} → {modified} ({delta:+d}, {percent_change:.1f}%)\n"
            if len(complexity_increases) > 5:
                report += f"  ... and {len(complexity_increases) - 5} more\n"

        interface_changes = high_risk.get("interface_changes", [])
        if interface_changes:
            report += "\nInterface Changes:\n"
            for item in interface_changes[:5]:  # Limit to top 5
                function_name = item.get("function", "Unknown")
                original_params = item.get("original_params", "Unknown")
                modified_params = item.get("modified_params", "Unknown")
                report += f"- {function_name}: Parameters changed from {original_params} to {modified_params}\n"
            if len(interface_changes) > 5:
                report += f"  ... and {len(interface_changes) - 5} more\n"

        # Add conclusion
        if is_properly_implemented:
            report += "\nConclusion: This commit is properly implemented and has no significant issues.\n"
        else:
            report += "\nConclusion: This commit has issues that should be addressed before merging.\n"

        return report

    def analyze_pull_request(
        self, repo_url: str, pr_number: int, github_token: str | None = None
    ) -> dict[str, Any]:
        """
        Analyze a pull request by comparing the base and head commits.

        Args:
            repo_url: The repository URL or owner/repo string
            pr_number: The pull request number
            github_token: Optional GitHub token for accessing private repositories.
                          It's recommended to use environment variables instead.

        Returns:
            A dictionary with analysis results

        Raises:
            ValueError: If no GitHub token is available
        """
        from github import Github

        # Use token from environment variable if available, otherwise use provided token or instance token
        token = os.environ.get("GITHUB_TOKEN") or github_token or self.github_token

        if not token:
            logger.error("No GitHub token available for PR analysis")
            raise ValueError(
                "GitHub token is required to analyze pull requests. "
                "Set it via the GITHUB_TOKEN environment variable or provide it as a parameter."
            )

        try:
            # Parse the repo URL to get owner and repo name
            if "/" in repo_url and "github.com" not in repo_url:
                owner, repo_name = repo_url.split("/")
            else:
                # Extract owner/repo from a full GitHub URL
                parts = repo_url.rstrip("/").split("/")
                owner = parts[-2]
                repo_name = parts[-1]
                if repo_name.endswith(".git"):
                    repo_name = repo_name[:-4]

            # Get the PR details from GitHub
            g = Github(token)
            repo = g.get_repo(f"{owner}/{repo_name}")
            pr = repo.get_pull(pr_number)

            # Get the base and head commits
            base_commit = pr.base.sha
            head_commit = pr.head.sha

            logger.info(
                f"Analyzing PR #{pr_number} in {repo_url} (base: {base_commit}, head: {head_commit})"
            )

            # Analyze the commits
            return self.analyze_commit(repo_url, base_commit, head_commit)
        except Exception as e:
            logger.exception(f"Error analyzing PR #{pr_number} in {repo_url}: {e!s}")
            raise
