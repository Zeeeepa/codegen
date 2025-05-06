"""
Data models for Git entities.

This module provides data models for Git entities like repositories and pull requests.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Repository:
    """
    Repository data model.

    Attributes:
        full_name: Full name of the repository (owner/repo)
        owner: Owner of the repository
        name: Name of the repository
        url: URL of the repository
        clone_url: Clone URL of the repository
        default_branch: Default branch of the repository
        metadata: Additional metadata
    """

    full_name: str
    owner: str
    name: str
    url: str
    clone_url: str
    default_branch: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PullRequest:
    """
    Pull request data model.

    Attributes:
        number: PR number
        title: PR title
        body: PR description
        author: PR author
        base_branch: Base branch
        head_branch: Head branch
        base_sha: Base commit SHA
        head_sha: Head commit SHA
        state: PR state
        url: PR URL
        files: List of files changed in the PR
        metadata: Additional metadata
    """

    number: int
    title: str
    body: Optional[str]
    author: str
    base_branch: str
    head_branch: str
    base_sha: str
    head_sha: str
    state: str
    url: str
    files: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
