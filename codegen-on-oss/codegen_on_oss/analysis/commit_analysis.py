"""
Commit Analysis Module for Codegen-on-OSS

This module provides functionality for analyzing and comparing commits,
determining if a commit is properly implemented, and identifying potential issues.
"""

import os
import tempfile
import subprocess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


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
            "functions_removed": self.functions_removed
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
            "files_changed": [file.to_dict() for file in self.files_changed]
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
            "files_changed": [file.to_dict() for file in self.files_changed]
        }
