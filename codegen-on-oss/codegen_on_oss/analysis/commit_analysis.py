"""
Commit Analysis Module for Codegen-on-OSS

This module provides functionality for analyzing commits and pull requests
to determine if they are properly implemented.
"""

import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import requests
from codegen import Codebase
from github import Github, GithubException, PullRequest, Repository
from github.Commit import Commit as GithubCommit

from codegen_on_oss.analysis.complexity_analyzer import analyze_codebase_complexity
from codegen_on_oss.snapshot.codebase_snapshot import SnapshotManager


@dataclass
class CommitAnalysisIssue:
    """Represents an issue found during commit analysis."""
    severity: str  # "error", "warning", or "info"
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the issue to a dictionary."""
        return {
            "severity": self.severity,
            "message": self.message,
            "file": self.file,
            "line": self.line,
        }


@dataclass
class CommitAnalysisResult:
    """Represents the result of a commit analysis."""
    is_properly_implemented: bool
    issues: List[CommitAnalysisIssue]
    metrics_diff: Dict[str, Any]
    files_added: List[str]
    files_modified: List[str]
    files_removed: List[str]
    summary: Optional[str] = None
    
    def get_summary(self) -> str:
        """Get a summary of the analysis result."""
        if self.summary:
            return self.summary
            
        # Generate a summary if one wasn't provided
        summary = []
        
        # Overall assessment
        if self.is_properly_implemented:
            summary.append("✅ The commit is properly implemented.")
        else:
            summary.append("❌ The commit has implementation issues that should be addressed.")
        
        # Files changed
        summary.append(f"\nSummary:")
        summary.append(f"- {len(self.files_added)} files added")
        summary.append(f"- {len(self.files_modified)} files modified")
        summary.append(f"- {len(self.files_removed)} files removed")
        
        # Issues
        if self.issues:
            summary.append(f"\nIssues:")
            for issue in self.issues:
                location = ""
                if issue.file:
                    location = f" in {issue.file}"
                    if issue.line:
                        location += f" at line {issue.line}"
                summary.append(f"- [{issue.severity.upper()}]{location}: {issue.message}")
        else:
            summary.append("\nNo issues were found.")
            
        # Metrics changes
        if self.metrics_diff:
            summary.append("\nMetrics changes:")
            if "complexity_change" in self.metrics_diff:
                change = self.metrics_diff["complexity_change"]
                if change > 0:
                    summary.append(f"- Complexity increased by {change}")
                elif change < 0:
                    summary.append(f"- Complexity decreased by {abs(change)}")
                else:
                    summary.append(f"- No change in complexity")
                    
            if "lines_added" in self.metrics_diff and "lines_removed" in self.metrics_diff:
                summary.append(f"- {self.metrics_diff['lines_added']} lines added, {self.metrics_diff['lines_removed']} lines removed")
        
        return "\n".join(summary)


class CommitAnalyzer:
    """
    Analyzes commits and pull requests to determine if they are properly implemented.
    """
    
    def __init__(self, snapshot_manager: SnapshotManager, github_token: Optional[str] = None):
        """
        Initialize a new CommitAnalyzer.
        
        Args:
            snapshot_manager: The SnapshotManager to use for creating snapshots
            github_token: Optional GitHub token for accessing private repositories
        """
        self.snapshot_manager = snapshot_manager
        self.github_token = github_token
        
    def analyze_commit(
        self, repo_url: str, base_commit: str, head_commit: str
    ) -> Dict[str, Any]:
        """
        Analyze a commit to determine if it's properly implemented.
        
        Args:
            repo_url: The repository URL or owner/repo string
            base_commit: The base commit SHA (before the changes)
            head_commit: The head commit SHA (after the changes)
            
        Returns:
            A dictionary with analysis results
        """
        # Clone the repository and create snapshots
        base_snapshot = self.snapshot_manager.create_snapshot_from_commit(repo_url, base_commit)
        head_snapshot = self.snapshot_manager.create_snapshot_from_commit(repo_url, head_commit)
        
        # Analyze the snapshots
        return self._analyze_snapshots(base_snapshot, head_snapshot)
    
    def analyze_pull_request(
        self, repo_url: str, pr_number: int, github_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a pull request to determine if it's properly implemented.
        
        Args:
            repo_url: The repository URL or owner/repo string
            pr_number: The pull request number
            github_token: Optional GitHub token for accessing private repositories
            
        Returns:
            A dictionary with analysis results
        """
        token = github_token or self.github_token
        if not token:
            raise ValueError("GitHub token is required to analyze pull requests")
        
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
        
        # Get the PR from GitHub
        g = Github(token)
        repo = g.get_repo(f"{owner}/{repo_name}")
        pr = repo.get_pull(pr_number)
        
        # Get the base and head commits
        base_commit = pr.base.sha
        head_commit = pr.head.sha
        
        # Analyze the commits
        return self.analyze_commit(repo_url, base_commit, head_commit)
    
    def _analyze_snapshots(self, base_snapshot: str, head_snapshot: str) -> Dict[str, Any]:
        """
        Analyze two snapshots to determine if the changes are properly implemented.
        
        Args:
            base_snapshot: Path to the base snapshot
            head_snapshot: Path to the head snapshot
            
        Returns:
            A dictionary with analysis results
        """
        # Create Codebase objects for the snapshots
        base_codebase = Codebase.from_directory(base_snapshot)
        head_codebase = Codebase.from_directory(head_snapshot)
        
        # Get the list of files added, modified, and removed
        base_files = {str(file.path): file for file in base_codebase.files}
        head_files = {str(file.path): file for file in head_codebase.files}
        
        files_added = [path for path in head_files if path not in base_files]
        files_removed = [path for path in base_files if path not in head_files]
        files_modified = [
            path for path in head_files 
            if path in base_files and head_files[path].content != base_files[path].content
        ]
        
        # Analyze complexity for both snapshots
        base_complexity = analyze_codebase_complexity(base_codebase)
        head_complexity = analyze_codebase_complexity(head_codebase)
        
        # Calculate metrics diff
        metrics_diff = {
            "complexity_change": head_complexity["overall_complexity"] - base_complexity["overall_complexity"],
            "function_count_change": head_complexity["function_count"] - base_complexity["function_count"],
            "class_count_change": head_complexity["class_count"] - base_complexity["class_count"],
            "lines_added": sum(len(head_files[path].content.splitlines()) for path in files_added),
            "lines_removed": sum(len(base_files[path].content.splitlines()) for path in files_removed),
        }
        
        # Check for issues
        issues = self._check_for_issues(
            base_codebase, head_codebase, 
            files_added, files_modified, files_removed,
            base_complexity, head_complexity
        )
        
        # Determine if the commit is properly implemented
        is_properly_implemented = not any(issue.severity == "error" for issue in issues)
        
        # Create the quality assessment
        quality_assessment = {
            "is_properly_implemented": is_properly_implemented,
            "score": self._calculate_quality_score(issues, metrics_diff),
            "issues": [issue.to_dict() for issue in issues],
            "overall_assessment": self._get_overall_assessment(is_properly_implemented, issues),
        }
        
        # Return the analysis results
        return {
            "files_added": files_added,
            "files_modified": files_modified,
            "files_removed": files_removed,
            "base_complexity": base_complexity,
            "head_complexity": head_complexity,
            "metrics_diff": metrics_diff,
            "quality_assessment": quality_assessment,
        }
    
    def _check_for_issues(
        self,
        base_codebase: Codebase,
        head_codebase: Codebase,
        files_added: List[str],
        files_modified: List[str],
        files_removed: List[str],
        base_complexity: Dict[str, Any],
        head_complexity: Dict[str, Any],
    ) -> List[CommitAnalysisIssue]:
        """
        Check for issues in the changes between two codebases.
        
        Args:
            base_codebase: The base codebase
            head_codebase: The head codebase
            files_added: List of files added
            files_modified: List of files modified
            files_removed: List of files removed
            base_complexity: Complexity metrics for the base codebase
            head_complexity: Complexity metrics for the head codebase
            
        Returns:
            A list of issues found
        """
        issues = []
        
        # Check for large complexity increases
        if head_complexity["overall_complexity"] > base_complexity["overall_complexity"] + 10:
            issues.append(CommitAnalysisIssue(
                severity="warning",
                message=f"Significant increase in cyclomatic complexity from {base_complexity['overall_complexity']} to {head_complexity['overall_complexity']}",
            ))
        
        # Check for very complex new functions
        for file_path in files_added + files_modified:
            if file_path in head_complexity["files"]:
                file_metrics = head_complexity["files"][file_path]
                for func_name, complexity in file_metrics["functions"].items():
                    if complexity > 20:  # Very complex function
                        issues.append(CommitAnalysisIssue(
                            severity="warning",
                            message=f"Function '{func_name}' has high cyclomatic complexity ({complexity})",
                            file=file_path,
                        ))
        
        # Check for missing tests for new files
        for file_path in files_added:
            if file_path.endswith((".py", ".js", ".ts")) and not file_path.endswith(("_test.py", ".test.js", ".test.ts", ".spec.js", ".spec.ts")):
                # Check if a corresponding test file was added
                test_file_patterns = [
                    file_path.replace(".py", "_test.py"),
                    file_path.replace(".js", ".test.js"),
                    file_path.replace(".ts", ".test.ts"),
                    file_path.replace(".js", ".spec.js"),
                    file_path.replace(".ts", ".spec.ts"),
                ]
                if not any(test_pattern in files_added for test_pattern in test_file_patterns):
                    issues.append(CommitAnalysisIssue(
                        severity="info",
                        message=f"No test file found for new file '{file_path}'",
                        file=file_path,
                    ))
        
        # Check for TODOs in new or modified files
        for file_path in files_added + files_modified:
            if file_path in head_complexity["files"]:
                file = head_codebase.get_file(file_path)
                if file and file.content:
                    todo_matches = re.finditer(r"#\s*TODO|//\s*TODO|/\*\s*TODO", file.content)
                    for match in todo_matches:
                        line_number = file.content[:match.start()].count("\n") + 1
                        issues.append(CommitAnalysisIssue(
                            severity="info",
                            message="TODO comment found",
                            file=file_path,
                            line=line_number,
                        ))
        
        return issues
    
    def _calculate_quality_score(
        self, issues: List[CommitAnalysisIssue], metrics_diff: Dict[str, Any]
    ) -> float:
        """
        Calculate a quality score for the commit based on issues and metrics.
        
        Args:
            issues: List of issues found
            metrics_diff: Metrics differences between base and head
            
        Returns:
            A quality score from 0 to 10
        """
        # Start with a perfect score
        score = 10.0
        
        # Deduct points for issues
        for issue in issues:
            if issue.severity == "error":
                score -= 2.0
            elif issue.severity == "warning":
                score -= 1.0
            elif issue.severity == "info":
                score -= 0.2
        
        # Deduct points for large complexity increases
        if metrics_diff["complexity_change"] > 20:
            score -= 2.0
        elif metrics_diff["complexity_change"] > 10:
            score -= 1.0
        elif metrics_diff["complexity_change"] > 5:
            score -= 0.5
        
        # Ensure the score is between 0 and 10
        return max(0.0, min(10.0, score))
    
    def _get_overall_assessment(
        self, is_properly_implemented: bool, issues: List[CommitAnalysisIssue]
    ) -> str:
        """
        Get an overall assessment of the commit quality.
        
        Args:
            is_properly_implemented: Whether the commit is properly implemented
            issues: List of issues found
            
        Returns:
            A string describing the overall assessment
        """
        if not is_properly_implemented:
            return "Poor - Critical issues need to be addressed"
        
        warning_count = sum(1 for issue in issues if issue.severity == "warning")
        info_count = sum(1 for issue in issues if issue.severity == "info")
        
        if warning_count == 0 and info_count == 0:
            return "Excellent - No issues found"
        elif warning_count == 0 and info_count <= 2:
            return "Very Good - Minor improvements possible"
        elif warning_count <= 2:
            return "Good - Some improvements recommended"
        else:
            return "Fair - Several improvements recommended"
    
    def format_analysis_report(self, analysis_results: Dict[str, Any]) -> str:
        """
        Format the analysis results into a human-readable report.
        
        Args:
            analysis_results: The analysis results from analyze_commit or analyze_pull_request
            
        Returns:
            A formatted report string
        """
        quality = analysis_results["quality_assessment"]
        metrics_diff = analysis_results["metrics_diff"]
        
        report = []
        
        # Header
        if quality["is_properly_implemented"]:
            report.append("# ✅ Commit Analysis: Properly Implemented")
        else:
            report.append("# ❌ Commit Analysis: Issues Detected")
        
        report.append(f"\nQuality Score: {quality['score']:.1f}/10.0 - {quality['overall_assessment']}")
        
        # Summary
        report.append("\n## Summary:")
        report.append(f"- Files Added: {len(analysis_results['files_added'])}")
        report.append(f"- Files Modified: {len(analysis_results['files_modified'])}")
        report.append(f"- Files Removed: {len(analysis_results['files_removed'])}")
        report.append(f"- Complexity Change: {metrics_diff['complexity_change']:+d}")
        report.append(f"- Function Count Change: {metrics_diff['function_count_change']:+d}")
        report.append(f"- Lines Added: {metrics_diff['lines_added']}")
        report.append(f"- Lines Removed: {metrics_diff['lines_removed']}")
        
        # Issues
        if quality["issues"]:
            report.append("\n## Issues:")
            for issue in quality["issues"]:
                location = ""
                if issue["file"]:
                    location = f" in {issue['file']}"
                    if issue["line"]:
                        location += f" at line {issue['line']}"
                report.append(f"- [{issue['severity'].upper()}]{location}: {issue['message']}")
        else:
            report.append("\n## Issues:\nNo issues were found.")
        
        # Files changed
        if analysis_results["files_added"]:
            report.append("\n## Files Added:")
            for file in sorted(analysis_results["files_added"]):
                report.append(f"- {file}")
        
        if analysis_results["files_modified"]:
            report.append("\n## Files Modified:")
            for file in sorted(analysis_results["files_modified"]):
                report.append(f"- {file}")
        
        if analysis_results["files_removed"]:
            report.append("\n## Files Removed:")
            for file in sorted(analysis_results["files_removed"]):
                report.append(f"- {file}")
        
        # Complexity details
        report.append("\n## Complexity Analysis:")
        report.append(f"- Base Complexity: {analysis_results['base_complexity']['overall_complexity']}")
        report.append(f"- Head Complexity: {analysis_results['head_complexity']['overall_complexity']}")
        
        # Conclusion
        report.append("\n## Conclusion:")
        if quality["is_properly_implemented"]:
            report.append("This commit is properly implemented and has no significant issues.")
        else:
            report.append("This commit has issues that should be addressed before merging.")
        
        return "\n".join(report)


def analyze_commit_from_repo_and_commit(
    repo_url: str, commit_hash: str, base_commit: Optional[str] = None
) -> CommitAnalysisResult:
    """
    Analyze a commit from a repository and commit hash.
    
    Args:
        repo_url: The repository URL or owner/repo string
        commit_hash: The commit hash to analyze
        base_commit: Optional base commit hash (if not provided, uses the parent commit)
        
    Returns:
        A CommitAnalysisResult object
    """
    # Create a temporary snapshot manager
    with tempfile.TemporaryDirectory() as temp_dir:
        snapshot_manager = SnapshotManager(temp_dir)
        analyzer = CommitAnalyzer(snapshot_manager)
        
        # If base_commit is not provided, get the parent commit
        if not base_commit:
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
            
            # Get the commit from GitHub
            g = Github()
            repo = g.get_repo(f"{owner}/{repo_name}")
            commit = repo.get_commit(commit_hash)
            
            # Get the parent commit
            if commit.parents:
                base_commit = commit.parents[0].sha
            else:
                raise ValueError(f"Commit {commit_hash} has no parent commits")
        
        # Analyze the commit
        results = analyzer.analyze_commit(repo_url, base_commit, commit_hash)
        
        # Convert to CommitAnalysisResult
        return CommitAnalysisResult(
            is_properly_implemented=results["quality_assessment"]["is_properly_implemented"],
            issues=[
                CommitAnalysisIssue(
                    severity=issue["severity"],
                    message=issue["message"],
                    file=issue["file"],
                    line=issue["line"],
                )
                for issue in results["quality_assessment"]["issues"]
            ],
            metrics_diff=results["metrics_diff"],
            files_added=results["files_added"],
            files_modified=results["files_modified"],
            files_removed=results["files_removed"],
            summary=None,  # Will be generated when get_summary is called
        )


def analyze_commit_from_paths(
    original_path: str, commit_path: str
) -> CommitAnalysisResult:
    """
    Analyze a commit by comparing two local repository paths.
    
    Args:
        original_path: Path to the original repository
        commit_path: Path to the repository with the commit applied
        
    Returns:
        A CommitAnalysisResult object
    """
    # Create Codebase objects for the paths
    base_codebase = Codebase.from_directory(original_path)
    head_codebase = Codebase.from_directory(commit_path)
    
    # Get the list of files added, modified, and removed
    base_files = {str(file.path): file for file in base_codebase.files}
    head_files = {str(file.path): file for file in head_codebase.files}
    
    files_added = [path for path in head_files if path not in base_files]
    files_removed = [path for path in base_files if path not in head_files]
    files_modified = [
        path for path in head_files 
        if path in base_files and head_files[path].content != base_files[path].content
    ]
    
    # Analyze complexity for both snapshots
    base_complexity = analyze_codebase_complexity(base_codebase)
    head_complexity = analyze_codebase_complexity(head_codebase)
    
    # Calculate metrics diff
    metrics_diff = {
        "complexity_change": head_complexity["overall_complexity"] - base_complexity["overall_complexity"],
        "function_count_change": head_complexity["function_count"] - base_complexity["function_count"],
        "class_count_change": head_complexity["class_count"] - base_complexity["class_count"],
        "lines_added": sum(len(head_files[path].content.splitlines()) for path in files_added),
        "lines_removed": sum(len(base_files[path].content.splitlines()) for path in files_removed),
    }
    
    # Create a temporary snapshot manager and analyzer
    with tempfile.TemporaryDirectory() as temp_dir:
        snapshot_manager = SnapshotManager(temp_dir)
        analyzer = CommitAnalyzer(snapshot_manager)
        
        # Check for issues
        issues = analyzer._check_for_issues(
            base_codebase, head_codebase, 
            files_added, files_modified, files_removed,
            base_complexity, head_complexity
        )
        
        # Determine if the commit is properly implemented
        is_properly_implemented = not any(issue.severity == "error" for issue in issues)
        
        # Return the analysis results
        return CommitAnalysisResult(
            is_properly_implemented=is_properly_implemented,
            issues=issues,
            metrics_diff=metrics_diff,
            files_added=files_added,
            files_modified=files_modified,
            files_removed=files_removed,
            summary=None,  # Will be generated when get_summary is called
        )
"""

"""
Diff Analyzer Module

This module provides functionality for comparing two codebase snapshots
and analyzing the differences between them.
"""

import difflib
import logging
from typing import Any, Dict, List, Optional

# Import the CodebaseSnapshot class
from codegen_on_oss.snapshot.codebase_snapshot import CodebaseSnapshot

logger = logging.getLogger(__name__)


class DiffAnalyzer:
    """
    A class for analyzing differences between two codebase snapshots.
    """

    def __init__(self, original_snapshot: CodebaseSnapshot, modified_snapshot: CodebaseSnapshot):
        """
        Initialize a new DiffAnalyzer.

        Args:
            original_snapshot: The original/base codebase snapshot
            modified_snapshot: The modified/new codebase snapshot
        """
        self.original = original_snapshot
        self.modified = modified_snapshot

        # Cache for diff results
        self._file_diffs = None
        self._function_diffs = None
        self._class_diffs = None
        self._import_diffs = None
        self._complexity_changes = None

    def analyze_file_changes(self) -> Dict[str, str]:
        """
        Analyze changes to files between the two snapshots.

        Returns:
            A dictionary mapping file paths to change types:
            - 'added': File exists in modified but not in original
            - 'deleted': File exists in original but not in modified
            - 'modified': File exists in both but has changed
            - 'unchanged': File exists in both and has not changed
        """
        if self._file_diffs is not None:
            return self._file_diffs

        original_files = set(self.original.file_metrics.keys())
        modified_files = set(self.modified.file_metrics.keys())

        added_files = modified_files - original_files
        deleted_files = original_files - modified_files
        common_files = original_files.intersection(modified_files)

        self._file_diffs = {}

        # Mark added files
        for filepath in added_files:
            self._file_diffs[filepath] = "added"

        # Mark deleted files
        for filepath in deleted_files:
            self._file_diffs[filepath] = "deleted"

        # Check common files for modifications
        for filepath in common_files:
            original_hash = self.original.file_metrics[filepath]["content_hash"]
            modified_hash = self.modified.file_metrics[filepath]["content_hash"]

            if original_hash != modified_hash:
                self._file_diffs[filepath] = "modified"
            else:
                self._file_diffs[filepath] = "unchanged"

        return self._file_diffs

    def analyze_function_changes(self) -> Dict[str, str]:
        """
        Analyze changes to functions between the two snapshots.

        Returns:
            A dictionary mapping function qualified names to change types:
            - 'added': Function exists in modified but not in original
            - 'deleted': Function exists in original but not in modified
            - 'modified': Function exists in both but has changed
            - 'unchanged': Function exists in both and has not changed
            - 'moved': Function exists in both but has moved to a different file
        """
        if self._function_diffs is not None:
            return self._function_diffs

        original_functions = set(self.original.function_metrics.keys())
        modified_functions = set(self.modified.function_metrics.keys())

        added_functions = modified_functions - original_functions
        deleted_functions = original_functions - modified_functions
        common_functions = original_functions.intersection(modified_functions)

        self._function_diffs = {}

        # Mark added functions
        for func_name in added_functions:
            self._function_diffs[func_name] = "added"

        # Mark deleted functions
        for func_name in deleted_functions:
            self._function_diffs[func_name] = "deleted"

        # Check common functions for modifications or moves
        for func_name in common_functions:
            original_func = self.original.function_metrics[func_name]
            modified_func = self.modified.function_metrics[func_name]

            # Check if the function has moved to a different file
            if original_func["filepath"] != modified_func["filepath"]:
                self._function_diffs[func_name] = "moved"
            # Check if the function has changed (parameters, complexity, etc.)
            elif (
                original_func["parameter_count"] != modified_func["parameter_count"]
                or original_func["line_count"] != modified_func["line_count"]
                or original_func["cyclomatic_complexity"] != modified_func["cyclomatic_complexity"]
            ):
                self._function_diffs[func_name] = "modified"
            else:
                self._function_diffs[func_name] = "unchanged"

        return self._function_diffs

    def analyze_class_changes(self) -> Dict[str, str]:
        """
        Analyze changes to classes between the two snapshots.

        Returns:
            A dictionary mapping class qualified names to change types:
            - 'added': Class exists in modified but not in original
            - 'deleted': Class exists in original but not in modified
            - 'modified': Class exists in both but has changed
            - 'unchanged': Class exists in both and has not changed
            - 'moved': Class exists in both but has moved to a different file
        """
        if self._class_diffs is not None:
            return self._class_diffs

        original_classes = set(self.original.class_metrics.keys())
        modified_classes = set(self.modified.class_metrics.keys())

        added_classes = modified_classes - original_classes
        deleted_classes = original_classes - modified_classes
        common_classes = original_classes.intersection(modified_classes)

        self._class_diffs = {}

        # Mark added classes
        for class_name in added_classes:
            self._class_diffs[class_name] = "added"

        # Mark deleted classes
        for class_name in deleted_classes:
            self._class_diffs[class_name] = "deleted"

        # Check common classes for modifications or moves
        for class_name in common_classes:
            original_class = self.original.class_metrics[class_name]
            modified_class = self.modified.class_metrics[class_name]

            # Check if the class has moved to a different file
            if original_class["filepath"] != modified_class["filepath"]:
                self._class_diffs[class_name] = "moved"
            # Check if the class has changed (methods, attributes, etc.)
            elif (
                original_class["method_count"] != modified_class["method_count"]
                or original_class["attribute_count"] != modified_class["attribute_count"]
                or original_class["parent_class_count"] != modified_class["parent_class_count"]
            ):
                self._class_diffs[class_name] = "modified"
            else:
                self._class_diffs[class_name] = "unchanged"

        return self._class_diffs

    def analyze_import_changes(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Analyze changes to imports between the two snapshots.

        Returns:
            A dictionary with file paths as keys and dictionaries as values.
            Each inner dictionary has keys 'added', 'deleted', and 'unchanged',
            with lists of import names as values.
        """
        if self._import_diffs is not None:
            return self._import_diffs

        self._import_diffs = {}

        # Get all files from both snapshots
        all_files = set(self.original.import_metrics.keys()).union(
            set(self.modified.import_metrics.keys())
        )

        for filepath in all_files:
            original_imports = set(self.original.import_metrics.get(filepath, []))
            modified_imports = set(self.modified.import_metrics.get(filepath, []))

            added_imports = modified_imports - original_imports
            deleted_imports = original_imports - modified_imports
            unchanged_imports = original_imports.intersection(modified_imports)

            self._import_diffs[filepath] = {
                "added": list(added_imports),
                "deleted": list(deleted_imports),
                "unchanged": list(unchanged_imports),
            }

        return self._import_diffs

    def analyze_complexity_changes(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze changes in cyclomatic complexity between the two snapshots.

        Returns:
            A dictionary mapping function qualified names to dictionaries with:
            - 'original': Original complexity
            - 'modified': Modified complexity
            - 'delta': Change in complexity (modified - original)
            - 'percent_change': Percentage change in complexity
        """
        if self._complexity_changes is not None:
            return self._complexity_changes

        self._complexity_changes = {}

        # Get functions that exist in both snapshots
        function_diffs = self.analyze_function_changes()
        common_functions = [
            func_name
            for func_name, change_type in function_diffs.items()
            if change_type in ["modified", "unchanged", "moved"]
        ]

        for func_name in common_functions:
            original_complexity = self.original.function_metrics[func_name]["cyclomatic_complexity"]
            modified_complexity = self.modified.function_metrics[func_name]["cyclomatic_complexity"]

            delta = modified_complexity - original_complexity

            # Calculate percent change, avoiding division by zero
            if original_complexity == 0:
                percent_change = float("inf") if delta > 0 else 0
            else:
                percent_change = (delta / original_complexity) * 100

            self._complexity_changes[func_name] = {
                "original": original_complexity,
                "modified": modified_complexity,
                "delta": delta,
                "percent_change": percent_change,
            }

        return self._complexity_changes

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all changes between the two snapshots.

        Returns:
            A dictionary with summary statistics for different types of changes.
        """
        file_changes = self.analyze_file_changes()
        function_changes = self.analyze_function_changes()
        class_changes = self.analyze_class_changes()
        complexity_changes = self.analyze_complexity_changes()

        # Count file changes by type
        file_counts = {
            "added": sum(1 for change_type in file_changes.values() if change_type == "added"),
            "deleted": sum(1 for change_type in file_changes.values() if change_type == "deleted"),
            "modified": sum(
                1 for change_type in file_changes.values() if change_type == "modified"
            ),
            "unchanged": sum(
                1 for change_type in file_changes.values() if change_type == "unchanged"
            ),
            "total": len(file_changes),
        }

        # Count function changes by type
        function_counts = {
            "added": sum(1 for change_type in function_changes.values() if change_type == "added"),
            "deleted": sum(
                1 for change_type in function_changes.values() if change_type == "deleted"
            ),
            "modified": sum(
                1 for change_type in function_changes.values() if change_type == "modified"
            ),
            "moved": sum(1 for change_type in function_changes.values() if change_type == "moved"),
            "unchanged": sum(
                1 for change_type in function_changes.values() if change_type == "unchanged"
            ),
            "total": len(function_changes),
        }

        # Count class changes by type
        class_counts = {
            "added": sum(1 for change_type in class_changes.values() if change_type == "added"),
            "deleted": sum(1 for change_type in class_changes.values() if change_type == "deleted"),
            "modified": sum(
                1 for change_type in class_changes.values() if change_type == "modified"
            ),
            "moved": sum(1 for change_type in class_changes.values() if change_type == "moved"),
            "unchanged": sum(
                1 for change_type in class_changes.values() if change_type == "unchanged"
            ),
            "total": len(class_changes),
        }

        # Calculate complexity change statistics
        complexity_stats = {
            "increased": sum(1 for change in complexity_changes.values() if change["delta"] > 0),
            "decreased": sum(1 for change in complexity_changes.values() if change["delta"] < 0),
            "unchanged": sum(1 for change in complexity_changes.values() if change["delta"] == 0),
            "total": len(complexity_changes),
        }

        if complexity_stats["total"] > 0:
            complexity_stats["avg_delta"] = (
                sum(change["delta"] for change in complexity_changes.values())
                / complexity_stats["total"]
            )
            complexity_stats["max_increase"] = max(
                (change["delta"] for change in complexity_changes.values()), default=0
            )
            complexity_stats["max_decrease"] = min(
                (change["delta"] for change in complexity_changes.values()), default=0
            )
        else:
            complexity_stats["avg_delta"] = 0
            complexity_stats["max_increase"] = 0
            complexity_stats["max_decrease"] = 0

        return {
            "file_changes": file_counts,
            "function_changes": function_counts,
            "class_changes": class_counts,
            "complexity_changes": complexity_stats,
            "original_snapshot_id": self.original.snapshot_id,
            "modified_snapshot_id": self.modified.snapshot_id,
            "original_commit": self.original.commit_sha,
            "modified_commit": self.modified.commit_sha,
        }

    def get_detailed_file_diff(self, filepath: str) -> Optional[List[str]]:
        """
        Get a detailed line-by-line diff for a specific file.

        Args:
            filepath: The path of the file to diff

        Returns:
            A list of diff lines, or None if the file doesn't exist in both snapshots
        """
        # Check if the file exists in both snapshots
        if filepath not in self.original.file_metrics or filepath not in self.modified.file_metrics:
            return None

        # Get the file content from the codebases
        original_file = None
        for file in self.original.codebase.files:
            if file.filepath == filepath:
                original_file = file
                break

        modified_file = None
        for file in self.modified.codebase.files:
            if file.filepath == filepath:
                modified_file = file
                break

        if not original_file or not modified_file:
            return None

        # Generate the diff
        original_lines = original_file.content.splitlines()
        modified_lines = modified_file.content.splitlines()

        diff = list(
            difflib.unified_diff(
                original_lines,
                modified_lines,
                fromfile=f"a/{filepath}",
                tofile=f"b/{filepath}",
                lineterm="",
            )
        )

        return diff

    def get_high_risk_changes(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Identify high-risk changes that might need special attention.

        Returns:
            A dictionary with categories of high-risk changes and lists of affected items.
        """
        high_risk = {
            "complexity_increases": [],
            "core_file_changes": [],
            "interface_changes": [],
            "dependency_changes": [],
        }

        # Identify functions with significant complexity increases
        complexity_changes = self.analyze_complexity_changes()
        for func_name, change in complexity_changes.items():
            # Consider a 30% increase or an absolute increase of 5 as high risk
            if change["percent_change"] > 30 or change["delta"] > 5:
                high_risk["complexity_increases"].append(
                    {
                        "function": func_name,
                        "original": change["original"],
                        "modified": change["modified"],
                        "delta": change["delta"],
                        "percent_change": change["percent_change"],
                    }
                )

        # Identify changes to core files (files with many dependencies)
        file_changes = self.analyze_file_changes()
        for filepath, change_type in file_changes.items():
            if change_type in ["modified", "deleted"] and filepath in self.original.file_metrics:
                # Consider files with many symbols as core files
                if self.original.file_metrics[filepath]["symbol_count"] > 10:
                    high_risk["core_file_changes"].append(
                        {
                            "filepath": filepath,
                            "change_type": change_type,
                            "symbol_count": self.original.file_metrics[filepath]["symbol_count"],
                        }
                    )

        # Identify interface changes (changes to function parameters)
        function_changes = self.analyze_function_changes()
        for func_name, change_type in function_changes.items():
            if change_type == "modified" and func_name in self.original.function_metrics:
                original_params = self.original.function_metrics[func_name]["parameter_count"]
                modified_params = self.modified.function_metrics[func_name]["parameter_count"]

                if original_params != modified_params:
                    high_risk["interface_changes"].append(
                        {
                            "function": func_name,
                            "original_params": original_params,
                            "modified_params": modified_params,
                        }
                    )

        # Identify dependency changes (changes to imports)
        import_changes = self.analyze_import_changes()
        for filepath, changes in import_changes.items():
            if changes["added"] or changes["deleted"]:
                high_risk["dependency_changes"].append(
                    {
                        "filepath": filepath,
                        "added_imports": changes["added"],
                        "deleted_imports": changes["deleted"],
                    }
                )

        return high_risk

    def format_summary_text(self) -> str:
        """
        Format a summary text of the comparison.

        Returns:
            Formatted summary text
        """
        summary = self.get_summary()

        text = f"""
Diff Analysis Summary
=====================

Original Snapshot: {summary["original_snapshot_id"]} (Commit: {summary["original_commit"] or "N/A"})
Modified Snapshot: {summary["modified_snapshot_id"]} (Commit: {summary["modified_commit"] or "N/A"})

File Changes:
- Added: {summary["file_changes"]["added"]}
- Deleted: {summary["file_changes"]["deleted"]}
- Modified: {summary["file_changes"]["modified"]}
- Unchanged: {summary["file_changes"]["unchanged"]}
- Total Files: {summary["file_changes"]["total"]}

Function Changes:
- Added: {summary["function_changes"]["added"]}
- Deleted: {summary["function_changes"]["deleted"]}
- Modified: {summary["function_changes"]["modified"]}
- Moved: {summary["function_changes"]["moved"]}
- Unchanged: {summary["function_changes"]["unchanged"]}
- Total Functions: {summary["function_changes"]["total"]}

Class Changes:
- Added: {summary["class_changes"]["added"]}
- Deleted: {summary["class_changes"]["deleted"]}
- Modified: {summary["class_changes"]["modified"]}
- Moved: {summary["class_changes"]["moved"]}
- Unchanged: {summary["class_changes"]["unchanged"]}
- Total Classes: {summary["class_changes"]["total"]}

Complexity Changes:
- Functions with increased complexity: {summary["complexity_changes"]["increased"]}
- Functions with decreased complexity: {summary["complexity_changes"]["decreased"]}
- Functions with unchanged complexity: {summary["complexity_changes"]["unchanged"]}
- Average complexity change: {summary["complexity_changes"]["avg_delta"]:.2f}
- Maximum complexity increase: {summary["complexity_changes"]["max_increase"]}
- Maximum complexity decrease: {summary["complexity_changes"]["max_decrease"]}
"""

        # Add high risk changes
        high_risk = self.get_high_risk_changes()

        if high_risk["complexity_increases"]:
            text += "\nHigh Risk - Significant Complexity Increases:\n"
            for item in high_risk["complexity_increases"]:
                text += f"- {item['function']}: {item['original']} → {item['modified']} ({item['delta']:+d}, {item['percent_change']:.1f}%)\n"

        if high_risk["core_file_changes"]:
            text += "\nHigh Risk - Core File Changes:\n"
            for item in high_risk["core_file_changes"]:
                text += f"- {item['filepath']} ({item['change_type']}, {item['symbol_count']} symbols)\n"

        if high_risk["interface_changes"]:
            text += "\nHigh Risk - Interface Changes:\n"
            for item in high_risk["interface_changes"]:
                text += f"- {item['function']}: Parameters changed from {item['original_params']} to {item['modified_params']}\n"

        if high_risk["dependency_changes"]:
            text += "\nHigh Risk - Dependency Changes:\n"
            for item in high_risk["dependency_changes"]:
                text += f"- {item['filepath']}:\n"
                if item["added_imports"]:
                    text += f"  - Added: {', '.join(item['added_imports'][:3])}"
                    if len(item["added_imports"]) > 3:
                        text += f" and {len(item['added_imports']) - 3} more"
                    text += "\n"
                if item["deleted_imports"]:
                    text += f"  - Deleted: {', '.join(item['deleted_imports'][:3])}"
                    if len(item["deleted_imports"]) > 3:
                        text += f" and {len(item['deleted_imports']) - 3} more"
                    text += "\n"

        return text

def perform_detailed_analysis(self) -> Dict[str, Any]:
    """Perform a detailed analysis of the differences between the two snapshots."""
    results = self._initialize_analysis_results()
    results.update(self._analyze_files_and_functions())
    results.update(self._analyze_complexity())
    results.update(self._analyze_risks())
    results['recommendations'] = self._generate_recommendations(results)
    return results
            "removed_files": [],
            "modified_files": [],
            "added_functions": [],
            "removed_functions": [],
            "modified_functions": [],
            "complexity_increases": [],
            "complexity_decreases": [],
            "potential_issues": [],
            "recommendations": [],
        }

        # Analyze file changes
        file_changes = self.analyze_file_changes()
        for file_path, change_type in file_changes.items():
            if change_type == "added":
                results["added_files"].append(file_path)
            elif change_type == "removed":
                results["removed_files"].append(file_path)
            elif change_type == "modified":
                results["modified_files"].append(file_path)

        # Analyze function changes
        function_changes = self.analyze_function_changes()
        for function_name, change_type in function_changes.items():
            if change_type == "added":
                results["added_functions"].append(function_name)
            elif change_type == "removed":
                results["removed_functions"].append(function_name)
            elif change_type == "modified":
                results["modified_functions"].append(function_name)

        # Analyze complexity changes
        complexity_changes = self.analyze_complexity_changes()
        for file_path, change in complexity_changes.items():
            if change > 0:
                results["complexity_increases"].append({
                    "file": file_path,
                    "increase": change,
                })
            elif change < 0:
                results["complexity_decreases"].append({
                    "file": file_path,
                    "decrease": abs(change),
                })

        # Identify potential issues
        risk_assessment = self.assess_risk()
        for category, risk_level in risk_assessment.items():
            if risk_level in ["high", "medium"]:
                results["potential_issues"].append({
                    "category": category,
                    "risk_level": risk_level,
                    "description": self._get_risk_description(category, risk_level),
                })

        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(results)

        return results

    def _get_risk_description(self, category: str, risk_level: str) -> str:
        """
        Get a description for a risk category and level.

        Args:
            category: Risk category
            risk_level: Risk level

        Returns:
            Description of the risk
        """
        descriptions = {
            "code_quality": {
                "high": "Significant code quality issues detected that may affect maintainability.",
                "medium": "Some code quality issues detected that should be addressed.",
                "low": "Minor code quality issues detected.",
            },
            "security": {
                "high": "Critical security vulnerabilities detected that must be addressed immediately.",
                "medium": "Security vulnerabilities detected that should be addressed.",
                "low": "Minor security concerns detected.",
            },
            "performance": {
                "high": "Significant performance issues detected that may affect system responsiveness.",
                "medium": "Some performance issues detected that should be addressed.",
                "low": "Minor performance concerns detected.",
            },
            "complexity": {
                "high": "Significant increase in code complexity that may affect maintainability.",
                "medium": "Moderate increase in code complexity.",
                "low": "Minor increase in code complexity.",
            },
            "test_coverage": {
                "high": "Significant decrease in test coverage that may affect code reliability.",
                "medium": "Moderate decrease in test coverage.",
                "low": "Minor decrease in test coverage.",
            },
        }

        return descriptions.get(category, {}).get(risk_level, f"Unknown risk for {category} at {risk_level} level")

    def _generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on analysis results.

        Args:
            analysis_results: Analysis results

        Returns:
            List of recommendations
        """
        recommendations = []

        # Check for complexity increases
        if len(analysis_results["complexity_increases"]) > 3:
            recommendations.append(
                "Consider refactoring complex files to improve maintainability."
            )

        # Check for potential issues
        for issue in analysis_results["potential_issues"]:
            if issue["category"] == "code_quality" and issue["risk_level"] == "high":
                recommendations.append(
                    "Address code quality issues to improve maintainability."
                )
            elif issue["category"] == "security" and issue["risk_level"] in ["high", "medium"]:
                recommendations.append(
                    "Address security vulnerabilities to prevent potential exploits."
                )
            elif issue["category"] == "performance" and issue["risk_level"] == "high":
                recommendations.append(
                    "Optimize performance-critical code to improve system responsiveness."
                )
            elif issue["category"] == "test_coverage" and issue["risk_level"] in ["high", "medium"]:
                recommendations.append(
                    "Increase test coverage to ensure code reliability."
                )

        # Check for large changes
        if len(analysis_results["added_files"]) + len(analysis_results["modified_files"]) > 10:
            recommendations.append(
                "Consider breaking large changes into smaller, more manageable pull requests."
            )

        # Add general recommendations
        if not recommendations:
            recommendations.append(
                "No specific recommendations. The changes appear to be well-structured."
            )

        return recommendations
"""
Commit Analysis Module

This module provides functionality for analyzing Git commits.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CommitAnalysisOptions:
    """Options for commit analysis."""

    include_diff: bool = False
    include_file_content: bool = False
    include_function_changes: bool = False


@dataclass
class FileChange:
    """Represents a change in a file."""

    filepath: str
    status: str
    content: Optional[str] = None
    diff: Optional[str] = None
    functions_added: List[str] = field(default_factory=list)
    functions_modified: List[str] = field(default_factory=list)
    functions_removed: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the file change to a dictionary."""
        return {
            "filepath": self.filepath,
            "status": self.status,
            "content": self.content,
            "diff": self.diff,
            "functions_added": self.functions_added,
            "functions_modified": self.functions_modified,
            "functions_removed": self.functions_removed,
        }


@dataclass
class CommitAnalysisResult:
    """Result of a commit analysis."""

    commit_hash: str
    author: str
    date: str
    message: str
    files_changed: List[FileChange]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "commit_hash": self.commit_hash,
            "author": self.author,
            "date": self.date,
            "message": self.message,
            "files_changed": [file.to_dict() for file in self.files_changed],
        }


@dataclass
class CommitComparisonResult:
    """Result of a commit comparison."""

    base_commit_hash: str
    compare_commit_hash: str
    files_changed: List[FileChange]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "base_commit_hash": self.base_commit_hash,
            "compare_commit_hash": self.compare_commit_hash,
            "files_changed": [file.to_dict() for file in self.files_changed],
        }
