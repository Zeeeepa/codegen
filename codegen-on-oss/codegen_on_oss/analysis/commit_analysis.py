"""
Commit Analysis Module for Codegen-on-OSS

This module provides functionality for analyzing and comparing commits,
determining if a commit is properly implemented, and identifying potential issues.
"""

import os
import tempfile
import subprocess
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
import difflib
import re
from dataclasses import dataclass, field

from codegen import Codebase
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.enums import EdgeType, SymbolType

from codegen_on_oss.analysis.analysis import CodeAnalyzer


@dataclass
class CommitIssue:
    """Represents an issue found in a commit."""
    issue_type: str
    severity: str  # "critical", "warning", "info"
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the issue to a dictionary."""
        return {
            "issue_type": self.issue_type,
            "severity": self.severity,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
        }


@dataclass
class CommitAnalysisResult:
    """Result of a commit analysis."""
    is_properly_implemented: bool
    issues: List["CommitIssue"] = field(default_factory=list)
    metrics_diff: Dict[str, Any] = field(default_factory=dict)
    files_added: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    files_removed: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "is_properly_implemented": self.is_properly_implemented,
            "issues": [issue.to_dict() for issue in self.issues],
            "metrics_diff": self.metrics_diff,
            "files_added": self.files_added,
            "files_modified": self.files_modified,
            "files_removed": self.files_removed,
        }
    
    def get_summary(self) -> str:
        """Get a summary of the analysis result."""
        status = "✅ Properly implemented" if self.is_properly_implemented else "❌ Issues found"
        
        summary = f"Commit Analysis Summary: {status}\n\n"
        
        if self.files_added:
            summary += f"Files Added ({len(self.files_added)}):\n"
            for file in self.files_added[:5]:  # Limit to 5 files for brevity
                summary += f"  - {file}\n"
            if len(self.files_added) > 5:
                summary += f"  - ... and {len(self.files_added) - 5} more\n"
            summary += "\n"
            
        if self.files_modified:
            summary += f"Files Modified ({len(self.files_modified)}):\n"
            for file in self.files_modified[:5]:
                summary += f"  - {file}\n"
            if len(self.files_modified) > 5:
                summary += f"  - ... and {len(self.files_modified) - 5} more\n"
            summary += "\n"
            
        if self.files_removed:
            summary += f"Files Removed ({len(self.files_removed)}):\n"
            for file in self.files_removed[:5]:
                summary += f"  - {file}\n"
            if len(self.files_removed) > 5:
                summary += f"  - ... and {len(self.files_removed) - 5} more\n"
            summary += "\n"
        
        if self.issues:
            summary += f"Issues Found ({len(self.issues)}):\n"
            for issue in self.issues:
                location = f" at {issue.file_path}:{issue.line_number}" if issue.file_path else ""
                summary += f"  - [{issue.severity.upper()}] {issue.issue_type}{location}: {issue.message}\n"
            summary += "\n"
            
        if self.metrics_diff:
            summary += "Metrics Changes:\n"
            for metric, change in self.metrics_diff.items():
                if isinstance(change, dict) and "before" in change and "after" in change:
                    if isinstance(change["before"], (int, float)) and isinstance(change["after"], (int, float)):
                        diff = change["after"] - change["before"]
                        direction = "↑" if diff > 0 else "↓" if diff < 0 else "→"
                        summary += f"  - {metric}: {change['before']} → {change['after']} ({direction} {abs(diff):.2f})\n"
                    else:
                        summary += f"  - {metric}: {change['before']} → {change['after']}\n"
                else:
                    summary += f"  - {metric}: {change}\n"
        
        return summary


class CommitAnalyzer:
    """
    Analyzer for comparing and evaluating commits.
    
    This class provides functionality to analyze two versions of a codebase (original and commit),
    compare them, and determine if the commit is properly implemented.
    """
    
    def __init__(self, original_codebase: Codebase, commit_codebase: Codebase) -> None:
        """
        Initialize the CommitAnalyzer with two codebases.
        
        Args:
            original_codebase: The original codebase before the commit
            commit_codebase: The codebase after the commit
        """
        self.original_codebase = original_codebase
        self.commit_codebase = commit_codebase
        self.result = CommitAnalysisResult(is_properly_implemented=True)
        
    @classmethod
    def from_paths(cls, original_path: str, commit_path: str) -> "CommitAnalyzer":
        """
        Create a CommitAnalyzer from two repository paths.
        
        Args:
            original_path: Path to the original repository
            commit_path: Path to the commit repository
            
        Returns:
            A CommitAnalyzer instance
        """
        original_codebase = Codebase.from_directory(original_path)
        commit_codebase = Codebase.from_directory(commit_path)
        
        return cls(original_codebase, commit_codebase)
    
    @classmethod
    def from_repo_and_commit(cls, repo_url: str, commit_hash: str) -> "CommitAnalyzer":
        """
        Create a CommitAnalyzer from a repository URL and commit hash.
        
        Args:
            repo_url: URL of the repository
            commit_hash: Hash of the commit to analyze
            
        Returns:
            A CommitAnalyzer instance
        """
        # Clone the repository
        with tempfile.TemporaryDirectory() as temp_dir:
            # Clone the repository
            subprocess.run(
                ["git", "clone", repo_url, temp_dir],
                check=True,
                capture_output=True,
                text=True,
            )
            
            # Create a codebase from the current state
            original_codebase = Codebase.from_directory(temp_dir)
            
            # Checkout the commit
            subprocess.run(
                ["git", "-C", temp_dir, "checkout", commit_hash],
                check=True,
                capture_output=True,
                text=True,
            )
            
            # Create a codebase from the commit
            commit_codebase = Codebase.from_directory(temp_dir)
            
            return cls(original_codebase, commit_codebase)
    
    def analyze_commit(self) -> CommitAnalysisResult:
        """
        Analyze the commit by comparing the original and commit codebases.
        
        Returns:
            A CommitAnalysisResult object containing the analysis results
        """
        # Compare files
        self._compare_files()
        
        # Check for issues
        self._check_for_issues()
        
        # Compare metrics
        self._compare_metrics()
        
        return self.result
    
    def _compare_files(self) -> None:
        """Compare files between the original and commit codebases."""
        original_files = {file.path: file for file in self.original_codebase.files}
        commit_files = {file.path: file for file in self.commit_codebase.files}
        
        # Find added, modified, and removed files
        self.result.files_added = [path for path in commit_files if path not in original_files]
        self.result.files_removed = [path for path in original_files if path not in commit_files]
        
        # Find modified files
        for path, commit_file in commit_files.items():
            if path in original_files:
                original_file = original_files[path]
                if original_file.content != commit_file.content:
                    self.result.files_modified.append(path)
    
    def _check_for_issues(self) -> None:
        """Check for issues in the commit."""
        # Check for large file additions
        for file_path in self.result.files_added:
            file = next((f for f in self.commit_codebase.files if f.path == file_path), None)
            if file and len(file.content.splitlines()) > 500:
                self.result.issues.append(
                    CommitIssue(
                        issue_type="Large File Addition",
                        severity="warning",
                        message=f"Added file with {len(file.content.splitlines())} lines",
                        file_path=file_path,
                    )
                )
        
        # Check for large file modifications
        for file_path in self.result.files_modified:
            original_file = next((f for f in self.original_codebase.files if f.path == file_path), None)
            commit_file = next((f for f in self.commit_codebase.files if f.path == file_path), None)
            
            if original_file and commit_file:
                original_lines = original_file.content.splitlines()
                commit_lines = commit_file.content.splitlines()
                
                # Check if more than 50% of the file was changed
                diff = difflib.unified_diff(original_lines, commit_lines, n=0)
                diff_lines = list(diff)
                
                # Count changed lines (lines starting with + or -)
                changed_lines = sum(1 for line in diff_lines if line.startswith("+") or line.startswith("-"))
                
                if changed_lines > len(original_lines) * 0.5:
                    self.result.issues.append(
                        CommitIssue(
                            issue_type="Large File Modification",
                            severity="info",
                            message=f"Modified more than 50% of the file ({changed_lines} lines changed)",
                            file_path=file_path,
                        )
                    )
        
        # Check for function complexity increases
        for file_path in self.result.files_modified:
            original_file = next((f for f in self.original_codebase.files if f.path == file_path), None)
            commit_file = next((f for f in self.commit_codebase.files if f.path == file_path), None)
            
            if original_file and commit_file:
                original_functions = {f.name: f for f in self.original_codebase.functions if f.file_path == file_path}
                commit_functions = {f.name: f for f in self.commit_codebase.functions if f.file_path == file_path}
                
                for name, commit_func in commit_functions.items():
                    if name in original_functions:
                        original_func = original_functions[name]
                        
                        # Calculate complexity
                        original_complexity = self._calculate_complexity(original_func)
                        commit_complexity = self._calculate_complexity(commit_func)
                        
                        # Check if complexity increased significantly
                        if commit_complexity > original_complexity * 1.5 and commit_complexity > 10:
                            self.result.issues.append(
                                CommitIssue(
                                    issue_type="Complexity Increase",
                                    severity="warning",
                                    message=f"Function complexity increased from {original_complexity} to {commit_complexity}",
                                    file_path=file_path,
                                    line_number=commit_func.start_line,
                                    code_snippet=commit_func.name,
                                )
                            )
        
        # Set is_properly_implemented based on critical issues
        critical_issues = [issue for issue in self.result.issues if issue.severity == "critical"]
        if critical_issues:
            self.result.is_properly_implemented = False
    
    def _calculate_complexity(self, func: Function) -> int:
        """
        Calculate the complexity of a function.
        
        Args:
            func: The function to analyze
            
        Returns:
            The complexity score
        """
        # Simple complexity calculation based on function length
        if not hasattr(func, "code_block") or not func.code_block:
            return 1
        
        # Start with base complexity of 1
        complexity = 1
        
        # Add complexity for each line
        complexity += len(func.code_block.source.splitlines()) // 10
        
        return complexity
    
    def _compare_metrics(self) -> None:
        """Compare metrics between the original and commit codebases."""
        # Create analyzers for both codebases
        original_analyzer = CodeAnalyzer(self.original_codebase)
        commit_analyzer = CodeAnalyzer(self.commit_codebase)
        
        # Get complexity metrics
        original_complexity = original_analyzer.analyze_complexity()
        commit_complexity = commit_analyzer.analyze_complexity()
        
        # Compare metrics
        self.result.metrics_diff = {
            "files_count": {
                "before": len(self.original_codebase.files),
                "after": len(self.commit_codebase.files),
            },
            "functions_count": {
                "before": len(self.original_codebase.functions),
                "after": len(self.commit_codebase.functions),
            },
            "classes_count": {
                "before": len(self.original_codebase.classes),
                "after": len(self.commit_codebase.classes),
            },
        }
        
        # Add complexity metrics if available
        if "cyclomatic_complexity" in original_complexity and "cyclomatic_complexity" in commit_complexity:
            self.result.metrics_diff["average_cyclomatic_complexity"] = {
                "before": original_complexity["cyclomatic_complexity"].get("average", 0),
                "after": commit_complexity["cyclomatic_complexity"].get("average", 0),
            }
    
    def get_diff_summary(self, file_path: str) -> str:
        """
        Get a diff summary for a specific file.
        
        Args:
            file_path: Path to the file to get the diff for
            
        Returns:
            A string containing the diff summary
        """
        original_file = next((f for f in self.original_codebase.files if f.path == file_path), None)
        commit_file = next((f for f in self.commit_codebase.files if f.path == file_path), None)
        
        if not original_file or not commit_file:
            return "File not found in one of the codebases"
        
        original_lines = original_file.content.splitlines()
        commit_lines = commit_file.content.splitlines()
        
        diff = difflib.unified_diff(
            original_lines,
            commit_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm="",
        )
        
        return "\n".join(diff)
    
    def get_detailed_report(self) -> Dict[str, Any]:
        """
        Get a detailed report of the commit analysis.
        
        Returns:
            A dictionary containing detailed analysis information
        """
        report: Dict[str, Any] = {
            "summary": self.result.get_summary(),
            "is_properly_implemented": self.result.is_properly_implemented,
            "issues": [issue.to_dict() for issue in self.result.issues],
            "metrics_diff": self.result.metrics_diff,
            "file_changes": {
                "added": self.result.files_added,
                "modified": self.result.files_modified,
                "removed": self.result.files_removed
            },
            "diffs": {}
        }
        
        # Add diffs for modified files
        for file_path in self.result.files_modified[:10]:  # Limit to 10 files for brevity
            report["diffs"][file_path] = self.get_diff_summary(file_path)
        
        return report
