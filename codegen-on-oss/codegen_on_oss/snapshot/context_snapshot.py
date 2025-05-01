"""
CodebaseContextSnapshot - Module for saving and restoring codebase state and analysis results.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from codegen_on_oss.analysis.harness_integration import CodebaseAnalysisHarness
from codegen_on_oss.bucket_store import BucketStore


class NoBucketStoreError(ValueError):
    """Error raised when no bucket store is configured for remote storage."""

    pass


class SnapshotNotFoundError(FileNotFoundError):
    """Error raised when a snapshot cannot be found locally."""

    pass


class SnapshotLoadError(ValueError):
    """Error raised when a snapshot could not be loaded."""

    pass


class NoHarnessError(ValueError):
    """Error raised when no harness is provided for snapshot creation."""

    pass


class NoSnapshotIdError(ValueError):
    """Error raised when no snapshot ID is provided."""

    pass


class CodebaseContextSnapshot:
    """
    Allows saving and restoring codebase state and analysis results.
    Integrates with S3-compatible storage via BucketStore.
    """

    def __init__(
        self,
        harness: CodebaseAnalysisHarness | None = None,
        snapshot_id: str | None = None,
        bucket_store: BucketStore | None = None,
    ):
        """
        Initialize a CodebaseContextSnapshot.

        Args:
            harness: Optional CodebaseAnalysisHarness to snapshot
            snapshot_id: Optional existing snapshot ID to load
            bucket_store: Optional BucketStore for remote storage
        """
        self.harness = harness
        self.snapshot_id = snapshot_id or str(uuid.uuid4())
        self.bucket_store = bucket_store
        self.snapshot_data: dict[str, Any] = {}

        if snapshot_id and bucket_store:
            self.load_snapshot()

    def create_snapshot(self, local_path: str | Path | None = None) -> str:
        """
        Create a snapshot of the current codebase state and analysis results.

        Args:
            local_path: Optional local path to save the snapshot

        Returns:
            The snapshot ID
        """
        if not self.harness:
            raise NoHarnessError()

        # Ensure we have analysis results
        if not self.harness.analysis_results:
            logger.info("No analysis results found, running analysis...")
            self.harness.analyze_codebase()

        # Create snapshot data
        self.snapshot_data = {
            "snapshot_id": self.snapshot_id,
            "created_at": datetime.now().isoformat(),
            "repo_info": {
                "repo_name": self.harness.codebase.repo_name,
                "commit": self.harness.base_commit,
            },
            "analysis_results": self.harness.analysis_results,
        }

        # Save locally if path provided
        if local_path:
            self._save_local(Path(local_path))

        # Save to bucket store if available
        if self.bucket_store:
            self._save_remote()

        logger.info(f"Created snapshot with ID: {self.snapshot_id}")
        return self.snapshot_id

    def load_snapshot(self, snapshot_id: str | None = None) -> dict[str, Any]:
        """
        Load a snapshot by ID.

        Args:
            snapshot_id: Optional snapshot ID to load (defaults to self.snapshot_id)

        Returns:
            The loaded snapshot data
        """
        snapshot_id = snapshot_id or self.snapshot_id
        if not snapshot_id:
            raise NoSnapshotIdError()

        # Try to load from bucket store first
        if self.bucket_store:
            try:
                self.snapshot_data = self._load_remote(snapshot_id)
            except Exception as e:
                logger.warning(f"Failed to load snapshot from remote: {e}")
            else:
                logger.info(f"Loaded snapshot {snapshot_id} from remote storage")
                return self.snapshot_data

        # Fall back to local storage
        try:
            self.snapshot_data = self._load_local(snapshot_id)
        except Exception as e:
            logger.error(f"Failed to load snapshot {snapshot_id}: {e}")
            raise SnapshotLoadError() from e
        else:
            logger.info(f"Loaded snapshot {snapshot_id} from local storage")
            return self.snapshot_data

    def save_to_remote(self) -> str:
        """
        Save the snapshot to remote storage.

        Returns:
            The snapshot ID.

        Raises:
            NoBucketStoreError: If no bucket store is configured.
        """
        if not self.bucket_store:
            raise NoBucketStoreError()

        key = f"snapshots/snapshot_{self.snapshot_id}.json"
        self.bucket_store.put_json(key, self.snapshot_data)
        logger.debug(f"Saved snapshot to remote storage with key {key}")
        return key

    def _save_local(self, directory: Path) -> Path:
        """
        Save the snapshot to a local file.

        Args:
            directory: Directory to save the snapshot in

        Returns:
            Path to the saved snapshot file
        """
        directory.mkdir(parents=True, exist_ok=True)
        snapshot_path = directory / f"snapshot_{self.snapshot_id}.json"

        with open(snapshot_path, "w") as f:
            json.dump(self.snapshot_data, f, indent=2)

        logger.debug(f"Saved snapshot to {snapshot_path}")
        return snapshot_path

    def _load_local(self, snapshot_id: str) -> dict[str, Any]:
        """
        Load a snapshot from a local file.

        Args:
            snapshot_id: ID of the snapshot to load

        Returns:
            The loaded snapshot data

        Raises:
            SnapshotNotFoundError: If the snapshot cannot be found locally
        """
        # Try common snapshot directories
        for directory in [Path("./snapshots"), Path("./data/snapshots")]:
            snapshot_path = directory / f"snapshot_{snapshot_id}.json"
            if snapshot_path.exists():
                with open(snapshot_path) as f:
                    return json.load(f)

        raise SnapshotNotFoundError(snapshot_id)

    def _load_remote(self, snapshot_id: str) -> dict[str, Any]:
        """
        Load a snapshot from remote storage.

        Args:
            snapshot_id: ID of the snapshot to load

        Returns:
            The loaded snapshot data

        Raises:
            NoBucketStoreError: If no bucket store is configured
        """
        if not self.bucket_store:
            raise NoBucketStoreError()

        key = f"snapshots/snapshot_{snapshot_id}.json"
        return self.bucket_store.get_json(key)

    def _save_remote(self) -> str:
        """
        Save the snapshot to remote storage.

        Returns:
            The key where the snapshot was saved.

        Raises:
            NoBucketStoreError: If no bucket store is configured.
        """
        return self.save_to_remote()

    @classmethod
    def load_from_remote(
        cls, snapshot_id: str, bucket_store: BucketStore
    ) -> "CodebaseContextSnapshot":
        """
        Load a snapshot from remote storage.

        Args:
            snapshot_id: The ID of the snapshot to load.
            bucket_store: The bucket store to use for loading.

        Returns:
            A CodebaseContextSnapshot instance.

        Raises:
            NoBucketStoreError: If no bucket store is provided.
            SnapshotLoadError: If the snapshot could not be loaded.
        """
        if not bucket_store:
            raise NoBucketStoreError()

        snapshot = cls(snapshot_id=snapshot_id, bucket_store=bucket_store)
        snapshot.load_snapshot()
        return snapshot
