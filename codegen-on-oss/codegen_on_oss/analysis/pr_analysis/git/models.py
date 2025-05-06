"""
Data models for Git and GitHub entities.

This module provides data models for Git and GitHub entities used in PR analysis,
including repositories, pull requests, commits, and files.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union


class FileStatus(Enum):
    """File status in a pull request."""
    ADDED = "added"
    MODIFIED = "modified"
    REMOVED = "removed"
    RENAMED = "renamed"


@dataclass
class User:
    """
    GitHub user model.
    
    Attributes:
        id: User ID
        login: Username
        name: Full name
        email: Email address
        avatar_url: Avatar URL
    """
    id: int
    login: str
    name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None


@dataclass
class Repository:
    """
    Repository model.
    
    Attributes:
        id: Repository ID
        name: Repository name
        full_name: Full repository name (owner/name)
        owner: Repository owner
        description: Repository description
        html_url: Repository URL
        clone_url: Repository clone URL
        default_branch: Default branch name
        private: Whether the repository is private
        created_at: Repository creation time
        updated_at: Repository update time
        metadata: Additional metadata
    """
    id: int
    name: str
    full_name: str
    owner: User
    description: Optional[str] = None
    html_url: Optional[str] = None
    clone_url: Optional[str] = None
    default_branch: str = "main"
    private: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class File:
    """
    File model in a pull request.
    
    Attributes:
        filename: File path
        status: File status
        additions: Number of added lines
        deletions: Number of deleted lines
        changes: Total number of changes
        patch: Diff patch
        blob_url: URL to the file blob
        raw_url: URL to the raw file
        contents_url: URL to the file contents API
        previous_filename: Previous filename (for renamed files)
    """
    filename: str
    status: FileStatus
    additions: int = 0
    deletions: int = 0
    changes: int = 0
    patch: Optional[str] = None
    blob_url: Optional[str] = None
    raw_url: Optional[str] = None
    contents_url: Optional[str] = None
    previous_filename: Optional[str] = None


@dataclass
class Commit:
    """
    Commit model.
    
    Attributes:
        sha: Commit SHA
        message: Commit message
        author: Commit author
        committer: Commit committer
        authored_at: Commit authoring time
        committed_at: Commit committing time
        html_url: Commit URL
        files: Files changed in the commit
        stats: Commit statistics
        parents: Parent commit SHAs
    """
    sha: str
    message: str
    author: User
    committer: Optional[User] = None
    authored_at: Optional[datetime] = None
    committed_at: Optional[datetime] = None
    html_url: Optional[str] = None
    files: List[File] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=dict)
    parents: List[str] = field(default_factory=list)


@dataclass
class PullRequest:
    """
    Pull request model.
    
    Attributes:
        id: Pull request ID
        number: Pull request number
        title: Pull request title
        body: Pull request description
        state: Pull request state
        html_url: Pull request URL
        diff_url: Pull request diff URL
        patch_url: Pull request patch URL
        user: Pull request author
        created_at: Pull request creation time
        updated_at: Pull request update time
        closed_at: Pull request closing time
        merged_at: Pull request merging time
        merge_commit_sha: Merge commit SHA
        head: Head branch information
        base: Base branch information
        commits: Commits in the pull request
        files: Files changed in the pull request
        additions: Number of added lines
        deletions: Number of deleted lines
        changed_files: Number of changed files
        mergeable: Whether the pull request is mergeable
        merged: Whether the pull request is merged
        mergeable_state: Mergeable state
        labels: Pull request labels
        assignees: Pull request assignees
        reviewers: Pull request reviewers
        requested_reviewers: Requested reviewers
        draft: Whether the pull request is a draft
        metadata: Additional metadata
    """
    id: int
    number: int
    title: str
    body: Optional[str]
    state: str
    html_url: str
    diff_url: str
    patch_url: str
    user: User
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    merged_at: Optional[datetime] = None
    merge_commit_sha: Optional[str] = None
    head: Dict[str, Any] = field(default_factory=dict)
    base: Dict[str, Any] = field(default_factory=dict)
    commits: List[Commit] = field(default_factory=list)
    files: List[File] = field(default_factory=list)
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    mergeable: Optional[bool] = None
    merged: bool = False
    mergeable_state: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    assignees: List[User] = field(default_factory=list)
    reviewers: List[User] = field(default_factory=list)
    requested_reviewers: List[User] = field(default_factory=list)
    draft: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

