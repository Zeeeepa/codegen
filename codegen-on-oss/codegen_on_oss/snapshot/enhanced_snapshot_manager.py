"""
Enhanced Snapshot Manager Module

This module provides an enhanced version of the SnapshotManager with additional
functionality for creating, comparing, and managing snapshots.
"""

import logging
import os
import shutil
import tempfile
from typing import Any, Dict, List, Optional, Tuple

from codegen_on_oss.analysis.diff_analyzer import DiffAnalyzer
from codegen_on_oss.snapshot.codebase_snapshot import CodebaseSnapshot, SnapshotManager

from codegen import Codebase
from codegen.configs.models.secrets import SecretsConfig

logger = logging.getLogger(__name__)


class EnhancedSnapshotManager(SnapshotManager):
    """
    An enhanced version of the SnapshotManager with additional functionality
    for creating, comparing, and managing snapshots.
    """

    def __init__(self, storage_dir: Optional[str] = None, cleanup_temp: bool = True):
        """
        Initialize a new EnhancedSnapshotManager.

        Args:
            storage_dir: Directory to store snapshots. If None, a temporary directory will be used.
            cleanup_temp: Whether to clean up temporary directories after operations
        """
        super().__init__(storage_dir)
        self.cleanup_temp = cleanup_temp
        self.temp_dirs = []

    def create_snapshot_from_repo(
        self,
        repo_url: str,
        commit_sha: Optional[str] = None,
        snapshot_id: Optional[str] = None,
        github_token: Optional[str] = None,
    ) -> CodebaseSnapshot:
        """
        Create a snapshot directly from a repository URL.

        Args:
            repo_url: The repository URL or owner/repo string
            commit_sha: Optional commit SHA to checkout
            snapshot_id: Optional custom ID for the snapshot
            github_token: Optional GitHub token for private repositories

        Returns:
            The created CodebaseSnapshot
        """
        # Create a codebase from the repo
        codebase = self.create_codebase_from_repo(repo_url, commit_sha, github_token)

        # Create a snapshot from the codebase
        snapshot = self.create_snapshot(codebase, commit_sha, snapshot_id)

        return snapshot

    def compare_snapshots(
        self, snapshot1_id: str, snapshot2_id: str
    ) -> Optional[DiffAnalyzer]:
        """
        Compare two snapshots and return a DiffAnalyzer.

        Args:
            snapshot1_id: ID of the first snapshot
            snapshot2_id: ID of the second snapshot

        Returns:
            A DiffAnalyzer for the two snapshots, or None if either snapshot is not found
        """
        snapshot1 = self.get_snapshot(snapshot1_id)
        snapshot2 = self.get_snapshot(snapshot2_id)

        if not snapshot1 or not snapshot2:
            logger.error(
                f"Cannot compare snapshots: snapshot1_id={snapshot1_id}, snapshot2_id={snapshot2_id}"
            )
            return None

        return DiffAnalyzer(snapshot1, snapshot2)

    def compare_commits(
        self,
        repo_url: str,
        base_commit: str,
        head_commit: str,
        github_token: Optional[str] = None,
    ) -> Optional[DiffAnalyzer]:
        """
        Compare two commits in a repository and return a DiffAnalyzer.

        Args:
            repo_url: The repository URL or owner/repo string
            base_commit: The base commit SHA
            head_commit: The head commit SHA
            github_token: Optional GitHub token for private repositories

        Returns:
            A DiffAnalyzer for the two commits, or None if snapshots cannot be created
        """
        # Check if we already have snapshots for these commits
        base_snapshot = self.get_snapshot_by_commit(base_commit)
        head_snapshot = self.get_snapshot_by_commit(head_commit)

        # Create snapshots if they don't exist
        if not base_snapshot:
            base_snapshot = self.create_snapshot_from_repo(
                repo_url, base_commit, github_token=github_token
            )

        if not head_snapshot:
            head_snapshot = self.create_snapshot_from_repo(
                repo_url, head_commit, github_token=github_token
            )

        # Create a DiffAnalyzer for the two snapshots
        return DiffAnalyzer(base_snapshot, head_snapshot)

    def get_or_create_snapshot(
        self,
        repo_url: str,
        commit_sha: str,
        github_token: Optional[str] = None,
    ) -> Optional[CodebaseSnapshot]:
        """
        Get an existing snapshot for a commit or create a new one if it doesn't exist.

        Args:
            repo_url: The repository URL or owner/repo string
            commit_sha: The commit SHA
            github_token: Optional GitHub token for private repositories

        Returns:
            The existing or newly created CodebaseSnapshot, or None if creation fails
        """
        # Check if we already have a snapshot for this commit
        snapshot = self.get_snapshot_by_commit(commit_sha)
        if snapshot:
            return snapshot

        # Create a new snapshot if one doesn't exist
        try:
            return self.create_snapshot_from_repo(
                repo_url, commit_sha, github_token=github_token
            )
        except Exception as e:
            logger.error(f"Failed to create snapshot for {repo_url}@{commit_sha}: {e}")
            return None

    def cleanup(self) -> None:
        """
        Clean up temporary directories created by this manager.
        """
        if self.cleanup_temp:
            for temp_dir in self.temp_dirs:
                if os.path.exists(temp_dir):
                    try:
                        shutil.rmtree(temp_dir, ignore_errors=True)
                        logger.info(f"Cleaned up temporary directory: {temp_dir}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up {temp_dir}: {e}")

            self.temp_dirs = []

    def __del__(self) -> None:
        """
        Clean up when the manager is deleted.
        """
        self.cleanup()

