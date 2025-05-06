"""
Commit analysis module for codegen-on-oss.

This module provides functionality for analyzing git commits and diffs.
It combines the functionality from the previous commit_analyzer.py and diff_analyzer.py files.
"""

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any, Union

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.file import SourceFile


@dataclass
class CommitAnalysisResult:
    """Result of a commit analysis."""
    
    commit_hash: str
    commit_message: str
    author: str
    date: str
    files_changed: List[str]
    insertions: int
    deletions: int
    total_changes: int
    file_changes: Dict[str, Dict[str, int]]
    summary: str
    
    # Additional fields for detailed analysis
    complexity_score: Optional[float] = None
    risk_score: Optional[float] = None
    affected_components: List[str] = field(default_factory=list)
    affected_functions: List[str] = field(default_factory=list)
    affected_classes: List[str] = field(default_factory=list)
    potential_issues: List[str] = field(default_factory=list)


class CommitAnalyzer:
    """Analyzer for git commits."""
    
    def __init__(self, codebase: Codebase, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the commit analyzer.
        
        Args:
            codebase: The codebase to analyze
            config: Optional configuration options for the analyzer
        """
        self.codebase = codebase
        self.config = config or {}
    
    def analyze_commit(self, commit_hash: str) -> CommitAnalysisResult:
        """
        Analyze a specific commit.
        
        Args:
            commit_hash: The hash of the commit to analyze
            
        Returns:
            Analysis results for the commit
        """
        # This is a simplified implementation
        # In a real implementation, we would use git commands to get commit details
        # and analyze the changes in the commit
        
        # Placeholder for commit details
        commit_details = {
            "commit_hash": commit_hash,
            "commit_message": "Example commit message",
            "author": "Example Author",
            "date": "2025-01-01",
            "files_changed": ["example.py"],
            "insertions": 10,
            "deletions": 5,
            "total_changes": 15,
            "file_changes": {"example.py": {"insertions": 10, "deletions": 5}},
            "summary": "Example commit summary",
        }
        
        # Create and return the result
        result = CommitAnalysisResult(
            commit_hash=commit_details["commit_hash"],
            commit_message=commit_details["commit_message"],
            author=commit_details["author"],
            date=commit_details["date"],
            files_changed=commit_details["files_changed"],
            insertions=commit_details["insertions"],
            deletions=commit_details["deletions"],
            total_changes=commit_details["total_changes"],
            file_changes=commit_details["file_changes"],
            summary=commit_details["summary"],
        )
        
        # Add additional analysis
        result.complexity_score = self._calculate_complexity_score(result)
        result.risk_score = self._calculate_risk_score(result)
        result.affected_components = self._identify_affected_components(result)
        result.affected_functions = self._identify_affected_functions(result)
        result.affected_classes = self._identify_affected_classes(result)
        result.potential_issues = self._identify_potential_issues(result)
        
        return result
    
    def analyze_commit_range(self, start_commit: str, end_commit: str) -> List[CommitAnalysisResult]:
        """
        Analyze a range of commits.
        
        Args:
            start_commit: The starting commit hash
            end_commit: The ending commit hash
            
        Returns:
            List of analysis results for each commit in the range
        """
        # This is a simplified implementation
        # In a real implementation, we would use git commands to get the list of commits
        # in the range and analyze each one
        
        # Placeholder for commit list
        commit_list = [start_commit, end_commit]
        
        # Analyze each commit
        results = []
        for commit in commit_list:
            results.append(self.analyze_commit(commit))
        
        return results
    
    def _calculate_complexity_score(self, result: CommitAnalysisResult) -> float:
        """
        Calculate a complexity score for the commit.
        
        Args:
            result: The commit analysis result
            
        Returns:
            A complexity score (higher means more complex)
        """
        # This is a simplified implementation
        # In a real implementation, we would consider factors like:
        # - Number of files changed
        # - Number of lines changed
        # - Types of files changed
        # - Complexity of the affected code
        
        # Simple formula: (files_changed * 0.5) + (total_changes * 0.1)
        return len(result.files_changed) * 0.5 + result.total_changes * 0.1
    
    def _calculate_risk_score(self, result: CommitAnalysisResult) -> float:
        """
        Calculate a risk score for the commit.
        
        Args:
            result: The commit analysis result
            
        Returns:
            A risk score (higher means more risky)
        """
        # This is a simplified implementation
        # In a real implementation, we would consider factors like:
        # - Complexity score
        # - Files changed in critical components
        # - Amount of code deleted
        # - Presence of certain patterns (e.g., security-related changes)
        
        # Simple formula: complexity_score * 0.7 + (deletions / total_changes) * 0.3
        deletion_ratio = result.deletions / result.total_changes if result.total_changes > 0 else 0
        return result.complexity_score * 0.7 + deletion_ratio * 0.3
    
    def _identify_affected_components(self, result: CommitAnalysisResult) -> List[str]:
        """
        Identify the components affected by the commit.
        
        Args:
            result: The commit analysis result
            
        Returns:
            List of affected components
        """
        # This is a simplified implementation
        # In a real implementation, we would map files to components based on
        # the project's structure
        
        # Placeholder implementation
        components = set()
        for file_path in result.files_changed:
            # Extract component from file path (e.g., first directory)
            parts = file_path.split("/")
            if len(parts) > 1:
                components.add(parts[0])
        
        return list(components)
    
    def _identify_affected_functions(self, result: CommitAnalysisResult) -> List[str]:
        """
        Identify the functions affected by the commit.
        
        Args:
            result: The commit analysis result
            
        Returns:
            List of affected functions
        """
        # This is a simplified implementation
        # In a real implementation, we would parse the diff to identify
        # which functions were modified
        
        # Placeholder implementation
        return ["example_function1", "example_function2"]
    
    def _identify_affected_classes(self, result: CommitAnalysisResult) -> List[str]:
        """
        Identify the classes affected by the commit.
        
        Args:
            result: The commit analysis result
            
        Returns:
            List of affected classes
        """
        # This is a simplified implementation
        # In a real implementation, we would parse the diff to identify
        # which classes were modified
        
        # Placeholder implementation
        return ["ExampleClass1", "ExampleClass2"]
    
    def _identify_potential_issues(self, result: CommitAnalysisResult) -> List[str]:
        """
        Identify potential issues in the commit.
        
        Args:
            result: The commit analysis result
            
        Returns:
            List of potential issues
        """
        # This is a simplified implementation
        # In a real implementation, we would look for patterns that might
        # indicate issues, such as:
        # - Large commits
        # - Commits that touch many files
        # - Commits that modify critical components
        # - Commits with certain keywords in the message
        
        issues = []
        
        # Check for large commits
        if result.total_changes > 100:
            issues.append("Large commit (>100 lines changed)")
        
        # Check for commits that touch many files
        if len(result.files_changed) > 5:
            issues.append("Many files changed (>5 files)")
        
        # Check for high risk score
        if result.risk_score > 0.7:
            issues.append("High risk score (>0.7)")
        
        return issues


class DiffAnalyzer:
    """Analyzer for git diffs."""
    
    def __init__(self, codebase: Codebase, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the diff analyzer.
        
        Args:
            codebase: The codebase to analyze
            config: Optional configuration options for the analyzer
        """
        self.codebase = codebase
        self.config = config or {}
    
    def analyze_diff(self, diff_text: str) -> Dict[str, Any]:
        """
        Analyze a git diff.
        
        Args:
            diff_text: The text of the diff to analyze
            
        Returns:
            Analysis results for the diff
        """
        # This is a simplified implementation
        # In a real implementation, we would parse the diff to extract
        # information about the changes
        
        # Initialize analysis dictionary
        analysis = {
            "files_changed": [],
            "insertions": 0,
            "deletions": 0,
            "total_changes": 0,
            "file_changes": {},
        }
        
        current_file = ""
        
        # Parse the diff text
        for line in diff_text.split("\n"):
            # Check for file header
            file_header_match = re.match(r"^diff --git a/(.*) b/(.*)$", line)
            if file_header_match:
                current_file = file_header_match.group(1)
                if isinstance(analysis["files_changed"], list) and current_file not in analysis["files_changed"]:
                    analysis["files_changed"].append(current_file)
                    analysis["file_changes"][current_file] = {"insertions": 0, "deletions": 0}
                continue
            
            # Check for line changes
            if current_file:
                if line.startswith("+") and not line.startswith("+++"):
                    analysis["insertions"] += 1
                    analysis["file_changes"][current_file]["insertions"] += 1
                elif line.startswith("-") and not line.startswith("---"):
                    analysis["deletions"] += 1
                    analysis["file_changes"][current_file]["deletions"] += 1
        
        # Calculate total changes
        insertions = analysis["insertions"] if isinstance(analysis["insertions"], int) else 0
        deletions = analysis["deletions"] if isinstance(analysis["deletions"], int) else 0
        analysis["total_changes"] = insertions + deletions
        
        return analysis
    
    def analyze_diff_between_commits(self, commit1: str, commit2: str) -> Dict[str, Any]:
        """
        Analyze the diff between two commits.
        
        Args:
            commit1: The first commit hash
            commit2: The second commit hash
            
        Returns:
            Analysis results for the diff
        """
        # This is a simplified implementation
        # In a real implementation, we would use git commands to get the diff
        # between the two commits and then analyze it
        
        # Placeholder for diff text
        diff_text = f"diff --git a/example.py b/example.py\n--- a/example.py\n+++ b/example.py\n@@ -1,5 +1,10 @@\n def example_function():\n-    return 'old'\n+    return 'new'\n+\n+def new_function():\n+    return 'added'\n"
        
        return self.analyze_diff(diff_text)


def analyze_commit(codebase: Codebase, commit_hash: str, config: Optional[Dict[str, Any]] = None) -> CommitAnalysisResult:
    """
    Analyze a specific commit.
    
    Args:
        codebase: The codebase to analyze
        commit_hash: The hash of the commit to analyze
        config: Optional configuration options for the analyzer
        
    Returns:
        Analysis results for the commit
    """
    analyzer = CommitAnalyzer(codebase, config)
    return analyzer.analyze_commit(commit_hash)


def analyze_diff(codebase: Codebase, diff_text: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Analyze a git diff.
    
    Args:
        codebase: The codebase to analyze
        diff_text: The text of the diff to analyze
        config: Optional configuration options for the analyzer
        
    Returns:
        Analysis results for the diff
    """
    analyzer = DiffAnalyzer(codebase, config)
    return analyzer.analyze_diff(diff_text)


def analyze_diff_between_commits(codebase: Codebase, commit1: str, commit2: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Analyze the diff between two commits.
    
    Args:
        codebase: The codebase to analyze
        commit1: The first commit hash
        commit2: The second commit hash
        config: Optional configuration options for the analyzer
        
    Returns:
        Analysis results for the diff
    """
    analyzer = DiffAnalyzer(codebase, config)
    return analyzer.analyze_diff_between_commits(commit1, commit2)
