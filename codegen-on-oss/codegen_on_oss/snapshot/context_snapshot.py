"""
CodebaseContextSnapshot - Module for saving and restoring codebase state.

This module provides functionality to save and restore codebase state,
integrating with S3-compatible storage via BucketStore.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from loguru import logger

from codegen_on_oss.analysis.harness_integration import CodebaseAnalysisHarness
from codegen_on_oss.bucket_store import BucketStore


class CodebaseContextSnapshot:
    """
    A class for saving and restoring codebase state, including analysis results and context.
    """

    def __init__(
        self,
        harness: CodebaseAnalysisHarness,
        bucket_store: Optional[BucketStore] = None,
        snapshot_id: Optional[str] = None,
    ):
        """
        Initialize the CodebaseContextSnapshot.

        Args:
            harness: The CodebaseAnalysisHarness containing the codebase to snapshot
            bucket_store: Optional BucketStore for S3 storage integration
            snapshot_id: Optional ID for an existing snapshot to load
        """
        self.harness = harness
        self.bucket_store = bucket_store
        self.snapshot_id = snapshot_id or str(uuid.uuid4())
        self.snapshot_data = {}
        self.snapshot_path = None

    def create_snapshot(self, local_path: Optional[Union[str, Path]] = None) -> str:
        """
        Create a snapshot of the current codebase state.

        Args:
            local_path: Optional local path to save the snapshot to

        Returns:
            The snapshot ID
        """
        # Ensure we have analysis results
        if not self.harness.analysis_results:
            logger.info("No analysis results found, running analysis...")
            self.harness.analyze_codebase()

        # Create snapshot data
        timestamp = datetime.now().isoformat()
        self.snapshot_data = {
            "snapshot_id": self.snapshot_id,
            "timestamp": timestamp,
            "repo_name": self.harness.codebase.repo_name,
            "analysis_results": self.harness.analysis_results,
            "metadata": self.harness.metadata,
            "tags": self.harness.tags,
        }

        # Save locally if path provided
        if local_path:
            self._save_local(local_path)

        # Save to S3 if bucket_store provided
        if self.bucket_store:
            self._save_to_s3()

        logger.info(f"Created snapshot with ID: {self.snapshot_id}")
        return self.snapshot_id

    def _save_local(self, local_path: Union[str, Path]) -> None:
        """
        Save the snapshot to a local file.

        Args:
            local_path: The local path to save the snapshot to
        """
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        snapshot_file = local_path / f"snapshot_{self.snapshot_id}.json"
        with open(snapshot_file, "w") as f:
            json.dump(self.snapshot_data, f, indent=2)
        
        self.snapshot_path = snapshot_file
        logger.info(f"Snapshot saved locally to {snapshot_file}")

    def _save_to_s3(self) -> None:
        """
        Save the snapshot to S3 using the bucket_store.
        """
        if not self.bucket_store:
            logger.warning("No bucket_store provided, cannot save to S3")
            return

        key = f"snapshots/{self.harness.codebase.repo_name}/{self.snapshot_id}.json"
        self.bucket_store.put_json(key, self.snapshot_data)
        logger.info(f"Snapshot saved to S3 with key: {key}")

    @classmethod
    def load_snapshot(
        cls,
        snapshot_id: str,
        local_path: Optional[Union[str, Path]] = None,
        bucket_store: Optional[BucketStore] = None,
    ) -> Optional["CodebaseContextSnapshot"]:
        """
        Load a snapshot from either local storage or S3.

        Args:
            snapshot_id: The ID of the snapshot to load
            local_path: Optional local path to load the snapshot from
            bucket_store: Optional BucketStore for S3 storage integration

        Returns:
            A CodebaseContextSnapshot instance or None if not found
        """
        snapshot_data = None

        # Try loading from local path
        if local_path:
            local_path = Path(local_path)
            snapshot_file = local_path / f"snapshot_{snapshot_id}.json"
            if snapshot_file.exists():
                with open(snapshot_file, "r") as f:
                    snapshot_data = json.load(f)
                logger.info(f"Loaded snapshot from local file: {snapshot_file}")

        # Try loading from S3
        if not snapshot_data and bucket_store:
            # We need to list snapshots to find the right repo name
            snapshots = cls.list_snapshots(bucket_store=bucket_store)
            for snapshot in snapshots:
                if snapshot["snapshot_id"] == snapshot_id:
                    repo_name = snapshot["repo_name"]
                    key = f"snapshots/{repo_name}/{snapshot_id}.json"
                    snapshot_data = bucket_store.get_json(key)
                    logger.info(f"Loaded snapshot from S3 with key: {key}")
                    break

        if not snapshot_data:
            logger.error(f"Snapshot with ID {snapshot_id} not found")
            return None

        # Create a harness from the snapshot data
        from codegen import Codebase
        from codegen.configs.models.codebase import CodebaseConfig

        config = CodebaseConfig()
        codebase = Codebase.from_repo(
            repo_full_name=snapshot_data["repo_name"],
            config=config,
        )
        harness = CodebaseAnalysisHarness(
            codebase=codebase,
            metadata=snapshot_data.get("metadata", {}),
            tags=snapshot_data.get("tags", []),
        )
        harness.analysis_results = snapshot_data.get("analysis_results", {})

        # Create and return the snapshot
        snapshot = cls(harness=harness, bucket_store=bucket_store, snapshot_id=snapshot_id)
        snapshot.snapshot_data = snapshot_data
        return snapshot

    @staticmethod
    def list_snapshots(
        bucket_store: BucketStore,
        repo_name: Optional[str] = None,
    ) -> List[Dict]:
        """
        List available snapshots in S3.

        Args:
            bucket_store: The BucketStore for S3 storage integration
            repo_name: Optional repository name to filter snapshots

        Returns:
            A list of snapshot metadata dictionaries
        """
        if not bucket_store:
            logger.warning("No bucket_store provided, cannot list snapshots")
            return []

        prefix = f"snapshots/{repo_name}/" if repo_name else "snapshots/"
        keys = bucket_store.list_keys(prefix=prefix)
        
        snapshots = []
        for key in keys:
            if key.endswith(".json"):
                snapshot_data = bucket_store.get_json(key)
                if snapshot_data:
                    snapshots.append({
                        "snapshot_id": snapshot_data.get("snapshot_id"),
                        "timestamp": snapshot_data.get("timestamp"),
                        "repo_name": snapshot_data.get("repo_name"),
                        "tags": snapshot_data.get("tags", []),
                    })
        
        return snapshots

