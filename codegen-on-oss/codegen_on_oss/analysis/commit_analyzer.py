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
    
    files_added = set(head_files.keys()) - set(base_files.keys())
    files_modified = set(path for path in set(head_files.keys()) & set(base_files.keys())
                        if head_files[path].content != base_files[path].content)
    files_removed = set(base_files.keys()) - set(head_files.keys())
    
    # Calculate complexity metrics for both codebases
    base_complexity = analyze_codebase_complexity(base_codebase)
    head_complexity = analyze_codebase_complexity(head_codebase)
    
    # Calculate metrics diff
    metrics_diff = {
        "files_added": len(files_added),
        "files_modified": len(files_modified),
        "files_removed": len(files_removed),
        "lines_added": sum(len(head_files[path].content.splitlines()) for path in files_added),
        "lines_modified": sum(len(head_files[path].content.splitlines()) for path in files_modified),
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
