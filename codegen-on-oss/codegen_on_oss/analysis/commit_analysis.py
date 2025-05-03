"""
Commit Analysis Module

This module provides functionality for analyzing Git commits.
"""

import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from codegen_on_oss.analysis.analysis import CodeAnalyzer
from codegen_on_oss.analysis.codebase_context import CodebaseContext
from codegen_on_oss.snapshot.codebase_snapshot import CodebaseSnapshot

from codegen import Codebase
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.enums import EdgeType, SymbolType


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
