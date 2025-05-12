#!/usr/bin/env python3
"""
Snapshot Manager Module

This module provides functionality for creating, storing, and comparing
codebase snapshots. It allows tracking changes over time and validating
consistency between versions.
"""

import hashlib
import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


@dataclass
class SnapshotMetadata:
    """Metadata for a codebase snapshot."""

    snapshot_id: str
    timestamp: str
    description: str
    creator: str
    base_path: str
    commit_hash: str | None = None
    branch: str | None = None
    tag: str | None = None
    file_count: int = 0
    total_lines: int = 0
    language_stats: dict[str, int] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class FileSnapshot:
    """Snapshot of a file in the codebase."""

    path: str
    relative_path: str
    hash: str
    size: int
    lines: int
    language: str | None = None
    content_hash: str | None = None
    ast_hash: str | None = None
    last_modified: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class CodebaseSnapshot:
    """
    Codebase snapshot representation.

    This class stores a complete snapshot of a codebase at a point in time,
    including all files and their metadata.
    """

    def __init__(
        self,
        base_path: str,
        description: str = "",
        creator: str = "snapshot_manager",
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        snapshot_id: str | None = None,
        store_content: bool = False,
    ):
        """
        Initialize a codebase snapshot.

        Args:
            base_path: Base path of the codebase
            description: Description of the snapshot
            creator: Creator of the snapshot
            include_patterns: Patterns of files to include
            exclude_patterns: Patterns of files to exclude
            snapshot_id: Optional ID for the snapshot
            store_content: Whether to store file content
        """
        self.base_path = os.path.abspath(base_path)
        self.description = description
        self.creator = creator
        self.include_patterns = include_patterns or ["*"]
        self.exclude_patterns = exclude_patterns or []
        self.snapshot_id = snapshot_id or self._generate_id()
        self.store_content = store_content
        self.timestamp = datetime.now().isoformat()

        # Initialize data structures
        self.files: dict[str, FileSnapshot] = {}
        self.content: dict[str, str] = {}
        self.language_stats: dict[str, int] = {}

        # Get git information if available
        self.commit_hash = self._get_git_commit_hash()
        self.branch = self._get_git_branch()
        self.tag = self._get_git_tag()

    def _generate_id(self) -> str:
        """
        Generate a unique ID for the snapshot.

        Returns:
            Generated ID
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = hashlib.md5(os.urandom(16)).hexdigest()[:8]
        return f"snapshot_{timestamp}_{random_suffix}"

    def _get_git_commit_hash(self) -> str | None:
        """
        Get the current Git commit hash.

        Returns:
            Commit hash if available, None otherwise
        """
        try:
            import subprocess

            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None

    def _get_git_branch(self) -> str | None:
        """
        Get the current Git branch.

        Returns:
            Branch name if available, None otherwise
        """
        try:
            import subprocess

            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None

    def _get_git_tag(self) -> str | None:
        """
        Get the current Git tag.

        Returns:
            Tag name if available, None otherwise
        """
        try:
            import subprocess

            result = subprocess.run(
                ["git", "describe", "--tags", "--exact-match"],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None

    def _get_file_language(self, file_path: str) -> str | None:
        """
        Determine the programming language of a file based on its extension.

        Args:
            file_path: Path to the file

        Returns:
            Language name if recognized, None otherwise
        """
        extension = os.path.splitext(file_path)[1].lower()

        language_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".jsx": "JavaScript",
            ".ts": "TypeScript",
            ".tsx": "TypeScript",
            ".java": "Java",
            ".c": "C",
            ".cpp": "C++",
            ".h": "C/C++",
            ".hpp": "C++",
            ".cs": "C#",
            ".go": "Go",
            ".rb": "Ruby",
            ".php": "PHP",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".rs": "Rust",
            ".scala": "Scala",
            ".html": "HTML",
            ".css": "CSS",
            ".scss": "SCSS",
            ".less": "LESS",
            ".json": "JSON",
            ".xml": "XML",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".md": "Markdown",
            ".sql": "SQL",
            ".sh": "Shell",
            ".bat": "Batch",
            ".ps1": "PowerShell",
        }

        return language_map.get(extension)

    def _should_include_file(self, file_path: str) -> bool:
        """
        Check if a file should be included in the snapshot.

        Args:
            file_path: Path to the file

        Returns:
            True if the file should be included, False otherwise
        """
        import fnmatch

        # Convert to relative path
        rel_path = os.path.relpath(file_path, self.base_path)

        # Check exclude patterns first
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(rel_path, pattern):
                return False

        # Then check include patterns
        for pattern in self.include_patterns:
            if fnmatch.fnmatch(rel_path, pattern):
                return True

        return False

    def _compute_file_hash(self, file_path: str) -> str:
        """
        Compute a hash of a file's content.

        Args:
            file_path: Path to the file

        Returns:
            Hash of the file content
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _count_lines(self, file_path: str) -> int:
        """
        Count the number of lines in a file.

        Args:
            file_path: Path to the file

        Returns:
            Number of lines in the file
        """
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
        except Exception:
            # Fallback for binary files
            return 0

    def create(self):
        """
        Create a snapshot of the codebase.

        This method scans the codebase, collects file metadata, and
        optionally stores file content.
        """
        if not os.path.isdir(self.base_path):
            logger.error(f"Base path not found: {self.base_path}")
            return

        # Reset data structures
        self.files = {}
        self.content = {}
        self.language_stats = {}

        total_files = 0
        total_lines = 0

        # Walk the directory tree
        for root, _, files in os.walk(self.base_path):
            for file in files:
                file_path = os.path.join(root, file)

                # Skip if file should not be included
                if not self._should_include_file(file_path):
                    continue

                try:
                    # Get file stats
                    file_stats = os.stat(file_path)
                    file_size = file_stats.st_size
                    file_modified = datetime.fromtimestamp(
                        file_stats.st_mtime
                    ).isoformat()

                    # Get file language
                    language = self._get_file_language(file_path)

                    # Count lines
                    line_count = self._count_lines(file_path)

                    # Compute hash
                    file_hash = self._compute_file_hash(file_path)

                    # Get relative path
                    rel_path = os.path.relpath(file_path, self.base_path)

                    # Create file snapshot
                    file_snapshot = FileSnapshot(
                        path=file_path,
                        relative_path=rel_path,
                        hash=file_hash,
                        size=file_size,
                        lines=line_count,
                        language=language,
                        last_modified=file_modified,
                    )

                    # Store file content if requested
                    if self.store_content:
                        try:
                            with open(
                                file_path, encoding="utf-8", errors="ignore"
                            ) as f:
                                file_content = f.read()
                                self.content[rel_path] = file_content
                        except Exception as e:
                            logger.warning(
                                f"Could not read content of {file_path}: {e!s}"
                            )

                    # Store file snapshot
                    self.files[rel_path] = file_snapshot

                    # Update language stats
                    if language:
                        self.language_stats[language] = (
                            self.language_stats.get(language, 0) + 1
                        )

                    # Update totals
                    total_files += 1
                    total_lines += line_count
                except Exception as e:
                    logger.warning(f"Error processing file {file_path}: {e!s}")

        logger.info(
            f"Created snapshot with {total_files} files and {total_lines} lines"
        )

    def get_metadata(self) -> SnapshotMetadata:
        """
        Get metadata for the snapshot.

        Returns:
            Snapshot metadata
        """
        return SnapshotMetadata(
            snapshot_id=self.snapshot_id,
            timestamp=self.timestamp,
            description=self.description,
            creator=self.creator,
            base_path=self.base_path,
            commit_hash=self.commit_hash,
            branch=self.branch,
            tag=self.tag,
            file_count=len(self.files),
            total_lines=sum(file.lines for file in self.files.values()),
            language_stats=self.language_stats,
        )

    def save(self, output_path: str | None = None) -> str:
        """
        Save the snapshot to disk.

        Args:
            output_path: Optional path to save the snapshot to

        Returns:
            Path to the saved snapshot
        """
        # Create a temporary directory if output_path is not provided
        if not output_path:
            output_dir = tempfile.mkdtemp(prefix="codebase_snapshot_")
            output_path = os.path.join(output_dir, f"{self.snapshot_id}.json")

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Convert snapshot to JSON
        snapshot_data = {
            "metadata": self.get_metadata().__dict__,
            "files": {rel_path: file.__dict__ for rel_path, file in self.files.items()},
            "content": self.content if self.store_content else {},
        }

        # Save to disk
        with open(output_path, "w") as f:
            json.dump(snapshot_data, f, indent=2)

        logger.info(f"Saved snapshot to {output_path}")
        return output_path

    @classmethod
    def load(cls, snapshot_path: str) -> "CodebaseSnapshot":
        """
        Load a snapshot from disk.

        Args:
            snapshot_path: Path to the snapshot file

        Returns:
            Loaded snapshot
        """
        with open(snapshot_path) as f:
            snapshot_data = json.load(f)

        # Extract metadata
        metadata = snapshot_data["metadata"]

        # Create snapshot instance
        snapshot = cls(
            base_path=metadata["base_path"],
            description=metadata["description"],
            creator=metadata["creator"],
            snapshot_id=metadata["snapshot_id"],
        )

        # Set timestamp
        snapshot.timestamp = metadata["timestamp"]

        # Set Git information
        snapshot.commit_hash = metadata.get("commit_hash")
        snapshot.branch = metadata.get("branch")
        snapshot.tag = metadata.get("tag")

        # Load files
        snapshot.files = {}
        for rel_path, file_data in snapshot_data["files"].items():
            snapshot.files[rel_path] = FileSnapshot(
                path=file_data["path"],
                relative_path=file_data["relative_path"],
                hash=file_data["hash"],
                size=file_data["size"],
                lines=file_data["lines"],
                language=file_data.get("language"),
                last_modified=file_data.get("last_modified"),
                metadata=file_data.get("metadata", {}),
            )

        # Load content if available
        snapshot.content = snapshot_data.get("content", {})
        snapshot.store_content = bool(snapshot.content)

        # Load language stats
        snapshot.language_stats = metadata.get("language_stats", {})

        logger.info(f"Loaded snapshot from {snapshot_path}")
        return snapshot

    def diff(self, other: "CodebaseSnapshot") -> dict[str, Any]:
        """
        Compare this snapshot with another snapshot.

        Args:
            other: Snapshot to compare with

        Returns:
            Diff between the snapshots
        """
        # Get sets of file paths
        self_files = set(self.files.keys())
        other_files = set(other.files.keys())

        # Find added, deleted, and common files
        added_files = other_files - self_files
        deleted_files = self_files - other_files
        common_files = self_files & other_files

        # Find modified files
        modified_files = []
        for file_path in common_files:
            self_file = self.files[file_path]
            other_file = other.files[file_path]

            if self_file.hash != other_file.hash:
                modified_files.append(file_path)

        # Calculate content diff for modified files if content is available
        content_diff = {}
        if self.store_content and other.store_content:
            for file_path in modified_files:
                if file_path in self.content and file_path in other.content:
                    try:
                        # Use difflib to generate unified diff
                        import difflib

                        diff = difflib.unified_diff(
                            self.content[file_path].splitlines(keepends=True),
                            other.content[file_path].splitlines(keepends=True),
                            fromfile=f"a/{file_path}",
                            tofile=f"b/{file_path}",
                        )
                        content_diff[file_path] = "".join(diff)
                    except Exception as e:
                        logger.warning(f"Error generating diff for {file_path}: {e!s}")

        # Calculate statistics
        diff_stats = {
            "files_added": len(added_files),
            "files_deleted": len(deleted_files),
            "files_modified": len(modified_files),
            "files_unchanged": len(common_files) - len(modified_files),
            "lines_added": sum(
                other.files[file_path].lines for file_path in added_files
            ),
            "lines_deleted": sum(
                self.files[file_path].lines for file_path in deleted_files
            ),
            "lines_modified": sum(
                other.files[file_path].lines - self.files[file_path].lines
                for file_path in modified_files
                if file_path in other.files and file_path in self.files
            ),
        }

        # Calculate language stats diff
        language_diff = {}
        for language in set(self.language_stats.keys()) | set(
            other.language_stats.keys()
        ):
            self_count = self.language_stats.get(language, 0)
            other_count = other.language_stats.get(language, 0)

            if self_count != other_count:
                language_diff[language] = other_count - self_count

        return {
            "added_files": list(added_files),
            "deleted_files": list(deleted_files),
            "modified_files": modified_files,
            "stats": diff_stats,
            "language_diff": language_diff,
            "content_diff": content_diff,
            "from_snapshot": self.snapshot_id,
            "to_snapshot": other.snapshot_id,
            "timestamp": datetime.now().isoformat(),
        }


class SnapshotManager:
    """
    Manager for codebase snapshots.

    This class provides functionality to create, store, load, and
    compare codebase snapshots.
    """

    def __init__(self, storage_dir: str | None = None):
        """
        Initialize the snapshot manager.

        Args:
            storage_dir: Directory to store snapshots in
        """
        self.storage_dir = storage_dir or os.path.join(
            tempfile.gettempdir(), "codebase_snapshots"
        )
        os.makedirs(self.storage_dir, exist_ok=True)

        # Initialize data structures
        self.snapshots: dict[str, SnapshotMetadata] = {}
        self.load_index()

    def load_index(self):
        """Load the snapshot index."""
        index_path = os.path.join(self.storage_dir, "index.json")

        if os.path.isfile(index_path):
            try:
                with open(index_path) as f:
                    data = json.load(f)

                self.snapshots = {}
                for snapshot_id, metadata in data.items():
                    self.snapshots[snapshot_id] = SnapshotMetadata(**metadata)
            except Exception as e:
                logger.exception(f"Error loading snapshot index: {e!s}")
                self.snapshots = {}

    def save_index(self):
        """Save the snapshot index."""
        index_path = os.path.join(self.storage_dir, "index.json")

        try:
            with open(index_path, "w") as f:
                json.dump(
                    {id: metadata.__dict__ for id, metadata in self.snapshots.items()},
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.exception(f"Error saving snapshot index: {e!s}")

    def create_snapshot(
        self,
        base_path: str,
        description: str = "",
        creator: str = "snapshot_manager",
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        snapshot_id: str | None = None,
        store_content: bool = False,
    ) -> str:
        """
        Create a new snapshot of a codebase.

        Args:
            base_path: Base path of the codebase
            description: Description of the snapshot
            creator: Creator of the snapshot
            include_patterns: Patterns of files to include
            exclude_patterns: Patterns of files to exclude
            snapshot_id: Optional ID for the snapshot
            store_content: Whether to store file content

        Returns:
            ID of the created snapshot
        """
        # Create the snapshot
        snapshot = CodebaseSnapshot(
            base_path=base_path,
            description=description,
            creator=creator,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            snapshot_id=snapshot_id,
            store_content=store_content,
        )

        # Generate the snapshot
        snapshot.create()

        # Save the snapshot
        snapshot_path = os.path.join(self.storage_dir, f"{snapshot.snapshot_id}.json")
        snapshot.save(snapshot_path)

        # Update the index
        self.snapshots[snapshot.snapshot_id] = snapshot.get_metadata()
        self.save_index()

        return snapshot.snapshot_id

    def get_snapshot(self, snapshot_id: str) -> CodebaseSnapshot | None:
        """
        Get a snapshot by ID.

        Args:
            snapshot_id: ID of the snapshot

        Returns:
            Snapshot if found, None otherwise
        """
        if snapshot_id not in self.snapshots:
            logger.error(f"Snapshot not found: {snapshot_id}")
            return None

        snapshot_path = os.path.join(self.storage_dir, f"{snapshot_id}.json")

        if not os.path.isfile(snapshot_path):
            logger.error(f"Snapshot file not found: {snapshot_path}")
            return None

        return CodebaseSnapshot.load(snapshot_path)

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot.

        Args:
            snapshot_id: ID of the snapshot

        Returns:
            True if the snapshot was deleted, False otherwise
        """
        if snapshot_id not in self.snapshots:
            logger.error(f"Snapshot not found: {snapshot_id}")
            return False

        snapshot_path = os.path.join(self.storage_dir, f"{snapshot_id}.json")

        if os.path.isfile(snapshot_path):
            try:
                os.remove(snapshot_path)
            except Exception as e:
                logger.exception(f"Error deleting snapshot file: {e!s}")
                return False

        # Update the index
        del self.snapshots[snapshot_id]
        self.save_index()

        return True

    def compare_snapshots(
        self, snapshot_id1: str, snapshot_id2: str
    ) -> dict[str, Any] | None:
        """
        Compare two snapshots.

        Args:
            snapshot_id1: ID of the first snapshot
            snapshot_id2: ID of the second snapshot

        Returns:
            Diff between the snapshots if both exist, None otherwise
        """
        snapshot1 = self.get_snapshot(snapshot_id1)
        snapshot2 = self.get_snapshot(snapshot_id2)

        if not snapshot1 or not snapshot2:
            return None

        return snapshot1.diff(snapshot2)

    def get_latest_snapshot(self, base_path: str | None = None) -> str | None:
        """
        Get the latest snapshot ID.

        Args:
            base_path: Optional base path to filter snapshots

        Returns:
            ID of the latest snapshot if any exist, None otherwise
        """
        if not self.snapshots:
            return None

        filtered_snapshots = self.snapshots

        if base_path:
            filtered_snapshots = {
                id: metadata
                for id, metadata in self.snapshots.items()
                if metadata.base_path == base_path
            }

        if not filtered_snapshots:
            return None

        # Sort by timestamp and get the latest
        latest_id = max(
            filtered_snapshots.keys(), key=lambda id: filtered_snapshots[id].timestamp
        )
        return latest_id

    def list_snapshots(self, base_path: str | None = None) -> list[SnapshotMetadata]:
        """
        List all snapshots.

        Args:
            base_path: Optional base path to filter snapshots

        Returns:
            List of snapshot metadata
        """
        if base_path:
            return [
                metadata
                for metadata in self.snapshots.values()
                if metadata.base_path == base_path
            ]
        else:
            return list(self.snapshots.values())
