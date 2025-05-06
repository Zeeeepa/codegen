"""
GitHub Models Module

This module provides data models for GitHub entities like pull requests.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any


@dataclass
class PRPartContext:
    """
    Context for a part of a pull request (base or head).
    
    Attributes:
        ref: Git reference (e.g., branch name)
        sha: Commit SHA
        repo_name: Repository name (e.g., "owner/repo")
    """
    ref: str
    sha: str
    repo_name: str


@dataclass
class PullRequestContext:
    """
    Context for a pull request.
    
    Attributes:
        number: PR number
        title: PR title
        body: PR description
        state: PR state (e.g., "open", "closed")
        base: Base branch context
        head: Head branch context
        user: User who created the PR
        html_url: URL to the PR on GitHub
    """
    number: int
    title: str
    body: str
    state: str
    base: PRPartContext
    head: PRPartContext
    user: Dict[str, Any]
    html_url: str


@dataclass
class FileChange:
    """
    Represents a file change in a pull request.
    
    Attributes:
        filename: Path to the file
        status: Status of the file (added, modified, removed)
        additions: Number of lines added
        deletions: Number of lines deleted
        changes: Total number of lines changed
        patch: Git patch for the file
        content_before: Content of the file before the change
        content_after: Content of the file after the change
    """
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: Optional[str] = None
    content_before: Optional[str] = None
    content_after: Optional[str] = None


@dataclass
class PRDiff:
    """
    Represents the diff of a pull request.
    
    Attributes:
        files: List of file changes
        total_additions: Total number of lines added
        total_deletions: Total number of lines deleted
        total_changes: Total number of lines changed
    """
    files: List[FileChange]
    total_additions: int
    total_deletions: int
    total_changes: int

