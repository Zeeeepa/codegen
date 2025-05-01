"""
CodebaseContextSnapshot: Allows saving and restoring codebase state.
Integrates with S3-compatible storage via BucketStore.
"""

import json
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

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
        bucket_name: Optional[str] = None,
    ):
        """
        Initialize the CodebaseContextSnapshot.

        Args:
            harness: The CodebaseAnalysisHarness to snapshot
            bucket_name: Optional bucket name for storage (defaults to environment variable)
        """
        self.harness = harness
        self.bucket_name = bucket_name or os.environ.get("CODEGEN_BUCKET_NAME", "codegen-snapshots")
        self.snapshot_id = str(uuid.uuid4())
        self.timestamp = datetime.now().isoformat()
        self.metadata = {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "repo_name": harness.codebase.repo_full_name,
            "commit": harness.codebase.commit,
        }

    def create_snapshot(self) -> str:
        """
        Create a snapshot of the current codebase state.

        Returns:
            The snapshot ID
        """
        logger.info(f"Creating snapshot for {self.harness.codebase.repo_full_name}")
        
        # Ensure we have analysis results
        if not self.harness.analysis_results:
            self.harness.analyze_codebase()
        
        # Create a temporary directory for the snapshot
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Save the analysis results
            analysis_path = temp_path / "analysis.json"
            with open(analysis_path, "w") as f:
                json.dump(self.harness.analysis_results, f)
            
            # Save the metadata
            metadata_path = temp_path / "metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(self.metadata, f)
            
            # Save the diff if there is one
            diff = self.harness.get_diff()
            if diff:
                diff_path = temp_path / "diff.patch"
                with open(diff_path, "w") as f:
                    f.write(diff)
            
            # Create a zip archive of the snapshot
            snapshot_path = temp_path / f"{self.snapshot_id}.zip"
            os.system(f"cd {temp_dir} && zip -r {snapshot_path} .")
            
            # Upload to bucket store
            bucket_store = BucketStore(self.bucket_name)
            remote_path = f"snapshots/{self.harness.codebase.repo_full_name}/{self.snapshot_id}.zip"
            key = bucket_store.upload_file(str(snapshot_path), remote_path)
            
            logger.info(f"Snapshot created with ID {self.snapshot_id} at {key}")
            
            return self.snapshot_id

    @classmethod
    def load_snapshot(
        cls,
        snapshot_id: str,
        bucket_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Load a snapshot from storage.

        Args:
            snapshot_id: The ID of the snapshot to load
            bucket_name: Optional bucket name for storage (defaults to environment variable)

        Returns:
            The loaded snapshot data
        """
        bucket_name = bucket_name or os.environ.get("CODEGEN_BUCKET_NAME", "codegen-snapshots")
        bucket_store = BucketStore(bucket_name)
        
        # Create a temporary directory for the snapshot
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / f"{snapshot_id}.zip"
            
            # Download the snapshot
            s3_client = bucket_store.s3_client
            
            # List objects to find the snapshot
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=f"{bucket_store.key_prefix}/snapshots",
            )
            
            snapshot_key = None
            for obj in response.get("Contents", []):
                if snapshot_id in obj["Key"]:
                    snapshot_key = obj["Key"]
                    break
            
            if not snapshot_key:
                raise ValueError(f"Snapshot {snapshot_id} not found")
            
            # Download the snapshot
            s3_client.download_file(bucket_name, snapshot_key, str(zip_path))
            
            # Extract the snapshot
            os.system(f"cd {temp_dir} && unzip {zip_path}")
            
            # Load the metadata
            metadata_path = temp_path / "metadata.json"
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            
            # Load the analysis results
            analysis_path = temp_path / "analysis.json"
            with open(analysis_path, "r") as f:
                analysis = json.load(f)
            
            # Load the diff if it exists
            diff = None
            diff_path = temp_path / "diff.patch"
            if diff_path.exists():
                with open(diff_path, "r") as f:
                    diff = f.read()
            
            return {
                "metadata": metadata,
                "analysis": analysis,
                "diff": diff,
            }

    def list_snapshots(
        self,
        repo_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List all snapshots for a repository.

        Args:
            repo_name: Optional repository name to filter by

        Returns:
            A list of snapshot metadata
        """
        bucket_store = BucketStore(self.bucket_name)
        s3_client = bucket_store.s3_client
        
        # List objects to find snapshots
        prefix = f"{bucket_store.key_prefix}/snapshots"
        if repo_name:
            prefix = f"{prefix}/{repo_name}"
        
        response = s3_client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=prefix,
        )
        
        snapshots = []
        for obj in response.get("Contents", []):
            key = obj["Key"]
            # Extract snapshot ID from key
            snapshot_id = key.split("/")[-1].split(".")[0]
            snapshots.append({
                "snapshot_id": snapshot_id,
                "key": key,
                "last_modified": obj["LastModified"].isoformat(),
                "size": obj["Size"],
            })
        
        return snapshots

