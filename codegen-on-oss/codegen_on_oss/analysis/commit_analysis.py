"""
Commit analysis module for codegen-on-oss.

This module provides functionality for analyzing commits and diffs.
It combines the functionality from the previous commit_analyzer.py and diff_analyzer.py files.
"""

import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple, Any, Union

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.file import SourceFile

@dataclass
class CommitAnalysisResult:
    """Result of a commit analysis."""
    
    summary: str
    files_changed: List[str]
    lines_added: int
    lines_removed: int
    file_summaries: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "summary": self.summary,
            "files_changed": self.files_changed,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "file_summaries": self.file_summaries,
        }


class CommitAnalyzer:
    """Analyzer for commits."""
    
    def __init__(self, original_codebase: Codebase, commit_codebase: Codebase):
        """
        Initialize the commit analyzer.
        
        Args:
            original_codebase: The original codebase before the commit
            commit_codebase: The codebase after the commit
        """
        self.original_codebase = original_codebase
        self.commit_codebase = commit_codebase
        self.diff_analyzer = DiffAnalyzer(original_codebase, commit_codebase)
    
    def analyze(self) -> CommitAnalysisResult:
        """
        Analyze the commit.
        
        Returns:
            A CommitAnalysisResult object
        """
        files_changed = self.diff_analyzer.get_changed_files()
        lines_added, lines_removed = self.diff_analyzer.get_lines_changed()
        file_summaries = {}
        
        for file_path in files_changed:
            file_summary = self.diff_analyzer.get_file_diff_summary(file_path)
            file_summaries[file_path] = file_summary
        
        summary = self._generate_commit_summary(files_changed, file_summaries, lines_added, lines_removed)
        
        return CommitAnalysisResult(
            summary=summary,
            files_changed=files_changed,
            lines_added=lines_added,
            lines_removed=lines_removed,
            file_summaries=file_summaries,
        )
    
    def _generate_commit_summary(
        self, 
        files_changed: List[str], 
        file_summaries: Dict[str, str],
        lines_added: int,
        lines_removed: int
    ) -> str:
        """
        Generate a summary of the commit.
        
        Args:
            files_changed: List of files changed in the commit
            file_summaries: Summaries of the changes in each file
            lines_added: Number of lines added in the commit
            lines_removed: Number of lines removed in the commit
            
        Returns:
            A summary of the commit
        """
        if not files_changed:
            return "No files were changed in this commit."
        
        summary = f"This commit changes {len(files_changed)} files with {lines_added} lines added and {lines_removed} lines removed.\n\n"
        
        # Group files by directory
        dir_files: Dict[str, List[str]] = {}
        for file_path in files_changed:
            dir_name = os.path.dirname(file_path)
            if not dir_name:
                dir_name = "."
            if dir_name not in dir_files:
                dir_files[dir_name] = []
            dir_files[dir_name].append(file_path)
        
        # Add file summaries grouped by directory
        for dir_name, files in dir_files.items():
            summary += f"\nChanges in {dir_name}:\n"
            for file_path in files:
                file_name = os.path.basename(file_path)
                file_summary = file_summaries.get(file_path, "No summary available")
                summary += f"- {file_name}: {file_summary}\n"
        
        return summary


class DiffAnalyzer:
    """Analyzer for diffs between two codebases."""
    
    def __init__(self, original_codebase: Codebase, modified_codebase: Codebase):
        """
        Initialize the diff analyzer.
        
        Args:
            original_codebase: The original codebase
            modified_codebase: The modified codebase
        """
        self.original_codebase = original_codebase
        self.modified_codebase = modified_codebase
    
    def get_changed_files(self) -> List[str]:
        """
        Get a list of files that were changed between the two codebases.
        
        Returns:
            A list of file paths that were changed
        """
        # This is a simplified implementation
        # In a real implementation, we would compare the files in both codebases
        # and detect additions, modifications, and deletions
        changed_files = []
        
        # Check for modified files
        for file_path in self._get_all_file_paths(self.modified_codebase):
            original_file = self._get_file(self.original_codebase, file_path)
            modified_file = self._get_file(self.modified_codebase, file_path)
            
            if original_file and modified_file:
                if original_file.content != modified_file.content:
                    changed_files.append(file_path)
            elif modified_file:  # File was added
                changed_files.append(file_path)
        
        # Check for deleted files
        for file_path in self._get_all_file_paths(self.original_codebase):
            if not self._get_file(self.modified_codebase, file_path):
                changed_files.append(file_path)
        
        return changed_files
    
    def get_lines_changed(self) -> Tuple[int, int]:
        """
        Get the number of lines added and removed between the two codebases.
        
        Returns:
            A tuple of (lines_added, lines_removed)
        """
        lines_added = 0
        lines_removed = 0
        
        for file_path in self.get_changed_files():
            original_file = self._get_file(self.original_codebase, file_path)
            modified_file = self._get_file(self.modified_codebase, file_path)
            
            if original_file and modified_file:
                # File was modified
                original_lines = original_file.content.splitlines()
                modified_lines = modified_file.content.splitlines()
                
                # This is a simplified diff calculation
                # In a real implementation, we would use a proper diff algorithm
                if len(modified_lines) > len(original_lines):
                    lines_added += len(modified_lines) - len(original_lines)
                else:
                    lines_removed += len(original_lines) - len(modified_lines)
            elif original_file:
                # File was deleted
                lines_removed += len(original_file.content.splitlines())
            elif modified_file:
                # File was added
                lines_added += len(modified_file.content.splitlines())
        
        return lines_added, lines_removed
    
    def get_file_diff_summary(self, file_path: str) -> str:
        """
        Get a summary of the changes to a file.
        
        Args:
            file_path: The path of the file to summarize
            
        Returns:
            A summary of the changes to the file
        """
        original_file = self._get_file(self.original_codebase, file_path)
        modified_file = self._get_file(self.modified_codebase, file_path)
        
        if original_file and modified_file:
            # File was modified
            return "File was modified"
        elif original_file:
            # File was deleted
            return "File was deleted"
        elif modified_file:
            # File was added
            return "File was added"
        else:
            return "No changes"
    
    def _get_all_file_paths(self, codebase: Codebase) -> List[str]:
        """
        Get all file paths in a codebase.
        
        Args:
            codebase: The codebase to get file paths from
            
        Returns:
            A list of file paths
        """
        # This is a placeholder implementation
        # In a real implementation, we would get all file paths from the codebase
        return []
    
    def _get_file(self, codebase: Codebase, file_path: str) -> Optional[SourceFile]:
        """
        Get a file from a codebase.
        
        Args:
            codebase: The codebase to get the file from
            file_path: The path of the file to get
            
        Returns:
            The file, or None if it doesn't exist
        """
        # This is a placeholder implementation
        # In a real implementation, we would get the file from the codebase
        return codebase.get_file(file_path)


def analyze_commit_from_repo_and_commit(
    repo_url: str, 
    commit_hash: str, 
    base_commit: Optional[str] = None
) -> CommitAnalysisResult:
    """
    Analyze a commit from a repository and commit hash.
    
    Args:
        repo_url: The URL of the repository
        commit_hash: The hash of the commit to analyze
        base_commit: The hash of the base commit to compare against
        
    Returns:
        A CommitAnalysisResult object
    """
    # This is a placeholder implementation
    # In a real implementation, we would:
    # 1. Clone the repository
    # 2. Checkout the base commit and create a codebase
    # 3. Checkout the commit and create a codebase
    # 4. Analyze the commit
    return CommitAnalysisResult(
        summary=f"Analysis of commit {commit_hash} in {repo_url}",
        files_changed=[],
        lines_added=0,
        lines_removed=0,
        file_summaries={},
    )


def analyze_commit_from_paths(
    original_path: str, 
    commit_path: str
) -> CommitAnalysisResult:
    """
    Analyze a commit from two directory paths.
    
    Args:
        original_path: The path to the original codebase
        commit_path: The path to the codebase after the commit
        
    Returns:
        A CommitAnalysisResult object
    """
    # This is a placeholder implementation
    # In a real implementation, we would:
    # 1. Create a codebase from the original path
    # 2. Create a codebase from the commit path
    # 3. Analyze the commit
    return CommitAnalysisResult(
        summary=f"Analysis of changes between {original_path} and {commit_path}",
        files_changed=[],
        lines_added=0,
        lines_removed=0,
        file_summaries={},
    )

