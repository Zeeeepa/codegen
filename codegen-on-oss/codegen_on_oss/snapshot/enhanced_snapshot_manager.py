"""
Enhanced snapshot manager for the codegen-on-oss system.

This module provides an enhanced snapshot manager with differential snapshots and improved comparison capabilities.
"""

import hashlib
import json
import logging
import os
import shutil
import tempfile
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import git
from codegen_on_oss.database.models import File, Repository, Snapshot
from codegen_on_oss.database.repositories import (
    FileRepository,
    RepositoryRepository,
    SnapshotRepository,
)
from codegen_on_oss.events.event_bus import Event, EventType, event_bus
from sqlalchemy.orm import Session

from codegen import Codebase

logger = logging.getLogger(__name__)


class EnhancedSnapshotManager:
    """Enhanced snapshot manager with differential snapshots and improved comparison capabilities."""

    def __init__(self, db_session: Session, storage_path: Optional[str] = None):
        """
        Initialize the enhanced snapshot manager.

        Args:
            db_session: Database session
            storage_path: Path to store snapshots
        """
        self.db_session = db_session
        self.storage_path = storage_path or os.environ.get(
            "CODEGEN_SNAPSHOT_STORAGE", "./snapshots"
        )

        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)

        # Initialize repositories
        self.repo_repository = RepositoryRepository(db_session)
        self.snapshot_repository = SnapshotRepository(db_session)
        self.file_repository = FileRepository(db_session)

    def snapshot_repo(
        self,
        repo_url: str,
        commit_sha: Optional[str] = None,
        branch: Optional[str] = None,
        is_incremental: bool = False,
        parent_snapshot_id: Optional[str] = None,
    ) -> Snapshot:
        """
        Create a snapshot of a repository.

        Args:
            repo_url: Repository URL
            commit_sha: Commit SHA
            branch: Branch name
            is_incremental: Whether to create an incremental snapshot
            parent_snapshot_id: Parent snapshot ID for incremental snapshots

        Returns:
            Created snapshot
        """
        # Get or create repository
        repository = self.repo_repository.get_by_url(repo_url)
        if not repository:
            repository = self.repo_repository.create(
                name=repo_url.split("/")[-1].replace(".git", ""),
                url=repo_url,
                default_branch=branch or "main",
            )

        # Get parent snapshot if incremental
        parent_snapshot = None
        if is_incremental and parent_snapshot_id:
            parent_snapshot = self.snapshot_repository.get_by_snapshot_id(
                parent_snapshot_id
            )
            if not parent_snapshot:
                raise ValueError(f"Parent snapshot not found: {parent_snapshot_id}")

        # Clone repository to temporary directory
        temp_dir = tempfile.mkdtemp()
        try:
            # Clone repository
            repo = git.Repo.clone_from(repo_url, temp_dir)

            # Checkout specific commit or branch
            if commit_sha:
                repo.git.checkout(commit_sha)
            elif branch:
                repo.git.checkout(branch)

            # Get actual commit SHA
            actual_commit_sha = repo.head.commit.hexsha

            # Create snapshot
            snapshot_id = str(uuid.uuid4())
            snapshot_dir = os.path.join(self.storage_path, snapshot_id)
            os.makedirs(snapshot_dir, exist_ok=True)

            # Create snapshot record
            snapshot = self.snapshot_repository.create(
                repository_id=repository.id,
                snapshot_id=snapshot_id,
                commit_sha=actual_commit_sha,
                branch=branch,
                storage_path=snapshot_dir,
                is_incremental=is_incremental,
                parent_snapshot_id=parent_snapshot.id if parent_snapshot else None,
                metadata={
                    "commit_message": repo.head.commit.message,
                    "commit_author": repo.head.commit.author.name,
                    "commit_date": repo.head.commit.committed_datetime.isoformat(),
                },
            )

            # Process files
            self._process_files(repo, snapshot, temp_dir, parent_snapshot)

            # Publish snapshot created event
            event_bus.publish(
                Event(
                    EventType.SNAPSHOT_CREATED,
                    {
                        "snapshot_id": snapshot.snapshot_id,
                        "repo_id": repository.id,
                        "repo_url": repository.url,
                        "commit_sha": actual_commit_sha,
                        "branch": branch,
                    },
                )
            )

            return snapshot
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir)

    def _process_files(
        self,
        repo: git.Repo,
        snapshot: Snapshot,
        repo_path: str,
        parent_snapshot: Optional[Snapshot] = None,
    ):
        """
        Process files in a repository.

        Args:
            repo: Git repository
            snapshot: Snapshot
            repo_path: Repository path
            parent_snapshot: Parent snapshot for incremental snapshots
        """
        # Get all files in the repository
        all_files = []
        for root, _, files in os.walk(repo_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_path)

                # Skip .git directory
                if rel_path.startswith(".git"):
                    continue

                all_files.append(rel_path)

        # Get parent snapshot files if incremental
        parent_files = {}
        if parent_snapshot:
            parent_files_db = self.file_repository.get_files_for_snapshot(
                parent_snapshot.id
            )
            for file in parent_files_db:
                parent_files[file.filepath] = file

        # Process each file
        for file_path in all_files:
            # Read file content
            with open(os.path.join(repo_path, file_path), "rb") as f:
                content = f.read()

            # Calculate content hash
            content_hash = hashlib.sha256(content).hexdigest()

            # Check if file exists in parent snapshot with same content
            if (
                parent_snapshot
                and file_path in parent_files
                and parent_files[file_path].content_hash == content_hash
            ):
                # File exists in parent snapshot with same content, just reference it
                self.file_repository.create(
                    snapshot_id=snapshot.id,
                    repository_id=snapshot.repository_id,
                    filepath=file_path,
                    name=os.path.basename(file_path),
                    extension=os.path.splitext(file_path)[1],
                    s3_key=parent_files[file_path].s3_key,
                    content_hash=content_hash,
                    line_count=parent_files[file_path].line_count,
                    language=self._get_language(file_path),
                )
            else:
                # File is new or modified, store it
                s3_key = f"{snapshot.snapshot_id}/{file_path}"
                file_storage_path = os.path.join(snapshot.storage_path, file_path)

                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(file_storage_path), exist_ok=True)

                # Write file content
                with open(file_storage_path, "wb") as f:
                    f.write(content)

                # Create file record
                self.file_repository.create(
                    snapshot_id=snapshot.id,
                    repository_id=snapshot.repository_id,
                    filepath=file_path,
                    name=os.path.basename(file_path),
                    extension=os.path.splitext(file_path)[1],
                    s3_key=s3_key,
                    content_hash=content_hash,
                    line_count=len(content.splitlines()),
                    language=self._get_language(file_path),
                )

    def _get_language(self, file_path: str) -> Optional[str]:
        """
        Get the language of a file based on its extension.

        Args:
            file_path: File path

        Returns:
            Language or None if unknown
        """
        extension = os.path.splitext(file_path)[1].lower()

        # Map extensions to languages
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".sass": "sass",
            ".less": "less",
            ".json": "json",
            ".xml": "xml",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".md": "markdown",
            ".txt": "text",
        }

        return extension_map.get(extension)

    def get_snapshot(self, snapshot_id: str) -> Optional[Snapshot]:
        """
        Get a snapshot by ID.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            Snapshot or None if not found
        """
        return self.snapshot_repository.get_by_snapshot_id(snapshot_id)

    def get_snapshot_files(self, snapshot_id: str) -> List[File]:
        """
        Get files for a snapshot.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            List of files
        """
        snapshot = self.snapshot_repository.get_by_snapshot_id(snapshot_id)
        if not snapshot:
            return []

        return self.file_repository.get_files_for_snapshot(snapshot.id)

    def get_file_content(self, snapshot_id: str, file_path: str) -> Optional[bytes]:
        """
        Get the content of a file in a snapshot.

        Args:
            snapshot_id: Snapshot ID
            file_path: File path

        Returns:
            File content or None if not found
        """
        snapshot = self.snapshot_repository.get_by_snapshot_id(snapshot_id)
        if not snapshot:
            return None

        file = self.file_repository.get_by_filepath(snapshot.id, file_path)
        if not file:
            return None

        # Read file content from storage
        file_storage_path = os.path.join(snapshot.storage_path, file_path)
        if os.path.exists(file_storage_path):
            with open(file_storage_path, "rb") as f:
                return f.read()

        # If file is not in storage, it might be in a parent snapshot
        if snapshot.parent_snapshot_id:
            parent_snapshot = self.snapshot_repository.get_by_id(
                snapshot.parent_snapshot_id
            )
            if parent_snapshot:
                return self.get_file_content(parent_snapshot.snapshot_id, file_path)

        return None

    def load_codebase_from_snapshot(self, snapshot_id: str) -> Optional[Codebase]:
        """
        Load a codebase from a snapshot.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            Codebase or None if not found
        """
        snapshot = self.snapshot_repository.get_by_snapshot_id(snapshot_id)
        if not snapshot:
            return None

        # Create a temporary directory for the codebase
        temp_dir = tempfile.mkdtemp()

        try:
            # Get all files for the snapshot
            files = self.file_repository.get_files_for_snapshot(snapshot.id)

            # Copy files to temporary directory
            for file in files:
                content = self.get_file_content(snapshot.snapshot_id, file.filepath)
                if content:
                    file_path = os.path.join(temp_dir, file.filepath)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, "wb") as f:
                        f.write(content)

            # Create codebase from directory
            return Codebase.from_directory(temp_dir)
        except Exception as e:
            logger.error(f"Error loading codebase from snapshot: {e}")
            return None
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir)

    def compare_snapshots(
        self, snapshot_id_1: str, snapshot_id_2: str
    ) -> Dict[str, Any]:
        """
        Compare two snapshots.

        Args:
            snapshot_id_1: First snapshot ID
            snapshot_id_2: Second snapshot ID

        Returns:
            Comparison results
        """
        snapshot_1 = self.snapshot_repository.get_by_snapshot_id(snapshot_id_1)
        snapshot_2 = self.snapshot_repository.get_by_snapshot_id(snapshot_id_2)

        if not snapshot_1 or not snapshot_2:
            raise ValueError("Snapshot not found")

        # Get files for both snapshots
        files_1 = {
            file.filepath: file
            for file in self.file_repository.get_files_for_snapshot(snapshot_1.id)
        }
        files_2 = {
            file.filepath: file
            for file in self.file_repository.get_files_for_snapshot(snapshot_2.id)
        }

        # Compare files
        added_files = [path for path in files_2 if path not in files_1]
        removed_files = [path for path in files_1 if path not in files_2]
        modified_files = [
            path
            for path in files_1
            if path in files_2
            and files_1[path].content_hash != files_2[path].content_hash
        ]

        # Get detailed diff for modified files
        diffs = {}
        for path in modified_files:
            content_1 = self.get_file_content(snapshot_id_1, path)
            content_2 = self.get_file_content(snapshot_id_2, path)

            if content_1 and content_2:
                import difflib

                diff = difflib.unified_diff(
                    content_1.decode("utf-8", errors="replace").splitlines(),
                    content_2.decode("utf-8", errors="replace").splitlines(),
                    fromfile=f"a/{path}",
                    tofile=f"b/{path}",
                    lineterm="",
                )

                diffs[path] = "\n".join(diff)

        return {
            "snapshot_1": {
                "id": snapshot_id_1,
                "commit_sha": snapshot_1.commit_sha,
                "timestamp": snapshot_1.timestamp.isoformat(),
            },
            "snapshot_2": {
                "id": snapshot_id_2,
                "commit_sha": snapshot_2.commit_sha,
                "timestamp": snapshot_2.timestamp.isoformat(),
            },
            "added_files": added_files,
            "removed_files": removed_files,
            "modified_files": modified_files,
            "diffs": diffs,
            "summary": {
                "added": len(added_files),
                "removed": len(removed_files),
                "modified": len(modified_files),
                "total_changes": len(added_files)
                + len(removed_files)
                + len(modified_files),
            },
        }

