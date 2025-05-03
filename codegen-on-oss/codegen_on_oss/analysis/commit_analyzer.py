"""
Commit Analyzer Module

This module provides functionality for analyzing Git commits by comparing
the codebase before and after the commit.
"""

import os
import subprocess
import tempfile
from typing import Dict, List, Optional, Union, Any, Tuple
from pathlib import Path

from codegen import Codebase
from codegen_on_oss.analysis.commit_analysis import CommitAnalysisOptions, CommitAnalysisResult, FileChange

class CommitAnalyzer:
    """
    Analyzer for commits in a repository.
    
    This class provides functionality to analyze specific commits in a repository,
    including getting commit metadata, file changes, and function changes.
    """
    
    def __init__(self, repo_path: Optional[str] = None):
        """
        Initialize the CommitAnalyzer.
        
        Args:
            repo_path: Path to the repository to analyze
        """
        self.repo_path = repo_path
        self.temp_dir: Optional[tempfile.TemporaryDirectory] = None
    
    def __enter__(self) -> 'CommitAnalyzer':
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager and cleanup resources."""
        self.cleanup()
    
    def cleanup(self) -> None:
        """Clean up temporary resources."""
        if self.temp_dir:
            self.temp_dir.cleanup()
            self.temp_dir = None
            
    def create_temp_dir(self) -> str:
        """Create a temporary directory if one doesn't exist."""
        if not self.temp_dir:
            self.temp_dir = tempfile.TemporaryDirectory()
        
        # Explicitly cast to str to satisfy mypy
        return str(self.temp_dir.name)
    
    def analyze_commit(
        self,
        commit_hash: str,
        options: Optional[CommitAnalysisOptions] = None
    ) -> CommitAnalysisResult:
        """
        Analyze a commit in the repository.
        
        Args:
            commit_hash: Hash of the commit to analyze
            options: Options for the analysis
            
        Returns:
            A CommitAnalysisResult object containing the analysis results
        """
        if not options:
            options = CommitAnalysisOptions()
            
        if not self.repo_path:
            raise ValueError("Repository path is required for commit analysis")
            
        # Get commit information
        commit_info = self._get_commit_info(commit_hash)
        
        # Get file changes
        files_changed = self._get_file_changes(commit_hash, options)
        
        # Create result
        result = CommitAnalysisResult(
            commit_hash=commit_hash,
            author=commit_info["author"],
            date=commit_info["date"],
            message=commit_info["message"],
            files_changed=files_changed
        )
        
        return result
        
    def _get_commit_info(self, commit_hash: str) -> Dict[str, str]:
        """
        Get information about a commit.
        
        Args:
            commit_hash: Hash of the commit
            
        Returns:
            A dictionary with commit information
        """
        # Run git show to get commit information
        command = [
            "git", "-C", str(self.repo_path), "show",
            "--no-patch",
            "--format=%an%n%ad%n%s",
            "--date=iso",
            commit_hash
        ]
        
        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True
            )
            
            lines = result.stdout.strip().split("\n")
            
            return {
                "author": lines[0],
                "date": lines[1],
                "message": "\n".join(lines[2:])
            }
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to get commit information: {e}")
            
    def _get_file_changes(
        self,
        commit_hash: str,
        options: CommitAnalysisOptions
    ) -> List[FileChange]:
        """
        Get file changes in a commit.
        
        Args:
            commit_hash: Hash of the commit
            options: Options for the analysis
            
        Returns:
            A list of FileChange objects
        """
        # Run git diff to get file changes
        command = [
            "git", "-C", str(self.repo_path), "diff-tree",
            "--no-commit-id", "--name-status", "-r",
            commit_hash
        ]
        
        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True
            )
            
            file_changes = []
            
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                    
                parts = line.split("\t")
                status = parts[0]
                filepath = parts[1] if len(parts) > 1 else ""
                
                file_change = FileChange(
                    filepath=filepath,
                    status=status
                )
                
                # Get file content if requested
                if options.include_file_content and status != "D":
                    file_change.content = self._get_file_content(commit_hash, filepath)
                    
                # Get file diff if requested
                if options.include_diff and status != "A":
                    file_change.diff = self._get_file_diff(commit_hash, filepath)
                    
                # Get function changes if requested
                if options.include_function_changes and status != "D":
                    self._add_function_changes(file_change, commit_hash, filepath)
                    
                file_changes.append(file_change)
                
            return file_changes
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to get file changes: {e}")
            
    def _get_file_content(self, commit_hash: str, filepath: str) -> str:
        """
        Get the content of a file at a specific commit.
        
        Args:
            commit_hash: Hash of the commit
            filepath: Path to the file
            
        Returns:
            The content of the file
        """
        command = [
            "git", "-C", str(self.repo_path), "show",
            f"{commit_hash}:{filepath}"
        ]
        
        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True
            )
            
            return result.stdout
        except subprocess.CalledProcessError:
            return ""
            
    def _get_file_diff(self, commit_hash: str, filepath: str) -> str:
        """
        Get the diff of a file at a specific commit.
        
        Args:
            commit_hash: Hash of the commit
            filepath: Path to the file
            
        Returns:
            The diff of the file
        """
        command = [
            "git", "-C", str(self.repo_path), "diff",
            f"{commit_hash}^..{commit_hash}", "--", filepath
        ]
        
        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True
            )
            
            return result.stdout
        except subprocess.CalledProcessError:
            return ""
            
    def _add_function_changes(
        self,
        file_change: FileChange,
        commit_hash: str,
        filepath: str
    ) -> None:
        """
        Add function changes to a file change.
        
        Args:
            file_change: FileChange object to update
            commit_hash: Hash of the commit
            filepath: Path to the file
        """
        # This would require parsing the file before and after the commit
        # and comparing the functions, which is beyond the scope of this example
        pass
        
    @classmethod
    def from_repo_url(cls, repo_url: str) -> "CommitAnalyzer":
        """
        Create a CommitAnalyzer from a repository URL.
        
        Args:
            repo_url: URL of the repository
            
        Returns:
            A CommitAnalyzer instance
        """
        # Create a temporary directory
        temp_dir = tempfile.TemporaryDirectory()
        
        # Clone the repository
        subprocess.run(
            ["git", "clone", repo_url, temp_dir.name],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Create analyzer
        analyzer = cls(repo_path=temp_dir.name)
        analyzer.temp_dir = temp_dir
        
        return analyzer
        
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
        # This would require comparing two repositories, which is beyond
        # the scope of this example
        raise NotImplementedError("from_paths is not implemented yet")
        
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
        # Create analyzer from repo URL
        analyzer = cls.from_repo_url(repo_url)
        
        return analyzer
