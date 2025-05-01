"""
CodebaseContextSnapshot - Module for saving and restoring codebase state and analysis results.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from loguru import logger

from codegen_on_oss.analysis.harness_integration import CodebaseAnalysisHarness
from codegen_on_oss.bucket_store import BucketStore


class CodebaseContextSnapshot:
    """
    Allows saving and restoring codebase state and analysis results.
    Integrates with S3-compatible storage via BucketStore.
    """

    def __init__(
        self,
        harness: Optional[CodebaseAnalysisHarness] = None,
        snapshot_id: Optional[str] = None,
        bucket_store: Optional[BucketStore] = None,
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
        self.snapshot_data: Dict[str, Any] = {}
        
        if snapshot_id and bucket_store:
            self.load_snapshot()

    def create_snapshot(self, local_path: Optional[Union[str, Path]] = None) -> str:
        """
        Create a snapshot of the current codebase state and analysis results.

        Args:
            local_path: Optional local path to save the snapshot

        Returns:
            The snapshot ID
        """
        if not self.harness:
            raise ValueError("No harness provided for snapshot creation")
        
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

    def load_snapshot(self, snapshot_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Load a snapshot by ID.

        Args:
            snapshot_id: Optional snapshot ID to load (defaults to self.snapshot_id)

        Returns:
            The loaded snapshot data
        """
        snapshot_id = snapshot_id or self.snapshot_id
        if not snapshot_id:
            raise ValueError("No snapshot ID provided")
        
        # Try to load from bucket store first
        if self.bucket_store:
            try:
                self.snapshot_data = self._load_remote(snapshot_id)
                logger.info(f"Loaded snapshot {snapshot_id} from remote storage")
                return self.snapshot_data
            except Exception as e:
                logger.warning(f"Failed to load snapshot from remote: {e}")
        
        # Fall back to local storage
        try:
            self.snapshot_data = self._load_local(snapshot_id)
            logger.info(f"Loaded snapshot {snapshot_id} from local storage")
            return self.snapshot_data
        except Exception as e:
            logger.error(f"Failed to load snapshot {snapshot_id}: {e}")
            raise ValueError(f"Could not load snapshot {snapshot_id}")

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

    def _load_local(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Load a snapshot from a local file.

        Args:
            snapshot_id: ID of the snapshot to load

        Returns:
            The loaded snapshot data
        """
        # Try common snapshot directories
        for directory in [Path("./snapshots"), Path("./data/snapshots")]:
            snapshot_path = directory / f"snapshot_{snapshot_id}.json"
            if snapshot_path.exists():
                with open(snapshot_path, "r") as f:
                    return json.load(f)
        
        raise FileNotFoundError(f"Snapshot {snapshot_id} not found locally")

    def _save_remote(self) -> str:
        """
        Save the snapshot to remote storage.

        Returns:
            The key of the saved snapshot
        """
        if not self.bucket_store:
            raise ValueError("No bucket store configured for remote storage")
        
        key = f"snapshots/snapshot_{self.snapshot_id}.json"
        self.bucket_store.put_json(key, self.snapshot_data)
        logger.debug(f"Saved snapshot to remote storage with key {key}")
        return key

    def _load_remote(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Load a snapshot from remote storage.

        Args:
            snapshot_id: ID of the snapshot to load

        Returns:
            The loaded snapshot data
        """
        if not self.bucket_store:
            raise ValueError("No bucket store configured for remote storage")
        
        key = f"snapshots/snapshot_{snapshot_id}.json"
        return self.bucket_store.get_json(key)

