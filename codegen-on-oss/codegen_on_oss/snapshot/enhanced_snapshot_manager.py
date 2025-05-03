"""
Enhanced Snapshot Manager Module

This module provides an enhanced snapshot manager that integrates with the database
and S3 storage for efficient snapshot creation, storage, and retrieval.
"""

import os
import json
import hashlib
import tempfile
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Set, Tuple

from sqlalchemy.orm import Session
import boto3

from codegen import Codebase
from codegen.configs.models.secrets import SecretsConfig

from codegen_on_oss.database.models import Repository, Snapshot, File
from codegen_on_oss.database.repositories import (
    RepositoryRepository, SnapshotRepository, FileRepository
)
from codegen_on_oss.events.event_bus import EventType, Event, event_bus

logger = logging.getLogger(__name__)

class EnhancedSnapshotManager:
    """
    Enhanced snapshot manager for creating, storing, and retrieving snapshots.
    
    This class provides methods for creating snapshots of codebases, storing them
    in the database and S3, and retrieving them for analysis.
    """
    
    def __init__(
        self, 
        db_session: Session,
        s3_bucket: Optional[str] = None,
        s3_prefix: Optional[str] = None
    ):
        """
        Initialize the enhanced snapshot manager.
        
        Args:
            db_session: The database session
            s3_bucket: Optional S3 bucket name for storing file content
            s3_prefix: Optional prefix for S3 keys
        """
        self.db_session = db_session
        self.s3_bucket = s3_bucket or os.environ.get("SNAPSHOT_S3_BUCKET", "codegen-snapshots")
        self.s3_prefix = s3_prefix or "snapshots"
        
        # Initialize repositories
        self.repo_repository = RepositoryRepository(db_session)
        self.snapshot_repository = SnapshotRepository(db_session)
        self.file_repository = FileRepository(db_session)
        
        # Initialize S3 client if bucket is provided
        self.s3_client = boto3.client("s3") if self.s3_bucket else None
    
    def create_snapshot(
        self, 
        codebase: Codebase, 
        repo_id: int,
        commit_sha: Optional[str] = None,
        branch: Optional[str] = None,
        snapshot_id: Optional[str] = None
    ) -> Snapshot:
        """
        Create a snapshot of a codebase.
        
        Args:
            codebase: The codebase to snapshot
            repo_id: The repository ID
            commit_sha: Optional commit SHA
            branch: Optional branch name
            snapshot_id: Optional custom snapshot ID
            
        Returns:
            The created snapshot
        """
        # Generate a snapshot ID if not provided
        if not snapshot_id:
            id_string = f"{codebase.repo_path}:{commit_sha or 'unknown'}:{branch or 'unknown'}:{datetime.now().isoformat()}"
            snapshot_id = hashlib.md5(id_string.encode()).hexdigest()
        
        # Create metadata
        metadata = {
            "repo_path": codebase.repo_path,
            "commit_sha": commit_sha,
            "branch": branch,
            "timestamp": datetime.now().isoformat(),
            "file_count": len(list(codebase.files)),
            "function_count": len(list(codebase.functions)),
            "class_count": len(list(codebase.classes)),
            "import_count": len(list(codebase.imports)),
            "symbol_count": len(list(codebase.symbols)),
        }
        
        # Create snapshot record
        snapshot = self.snapshot_repository.create(
            snapshot_id=snapshot_id,
            repo_id=repo_id,
            commit_sha=commit_sha,
            branch=branch,
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        # Process files
        for file in codebase.files:
            # Skip non-source files or files without content
            if not file.content:
                continue
            
            # Calculate file hash
            file_hash = hashlib.md5(file.content.encode()).hexdigest()
            
            # Store file content in S3 if enabled
            s3_key = None
            if self.s3_client:
                s3_key = f"{self.s3_prefix}/{snapshot_id}/{file.filepath}"
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=s3_key,
                    Body=file.content.encode()
                )
            
            # Create file record
            self.file_repository.create(
                repo_id=repo_id,
                snapshot_id=snapshot.id,
                filepath=file.filepath,
                name=file.name,
                extension=os.path.splitext(file.name)[1] if "." in file.name else None,
                s3_key=s3_key,
                content_hash=file_hash,
                line_count=len(file.content.splitlines())
            )
        
        # Publish snapshot created event
        event_bus.publish(Event(
            EventType.SNAPSHOT_CREATED,
            {
                "repo_id": repo_id,
                "snapshot_id": snapshot_id,
                "commit_sha": commit_sha,
                "branch": branch
            }
        ))
        
        return snapshot
    
    def snapshot_repo(
        self, 
        repo_url: str, 
        commit_sha: Optional[str] = None,
        branch: Optional[str] = None,
        github_token: Optional[str] = None,
        snapshot_id: Optional[str] = None
    ) -> Snapshot:
        """
        Create a snapshot directly from a repository URL.
        
        Args:
            repo_url: The repository URL
            commit_sha: Optional commit SHA to checkout
            branch: Optional branch to checkout
            github_token: Optional GitHub token for private repositories
            snapshot_id: Optional custom snapshot ID
            
        Returns:
            The created snapshot
        """
        # Get or create repository record
        repo_name = repo_url.split("/")[-1] if "/" in repo_url else repo_url
        repository = self.repo_repository.get_by_url(repo_url)
        
        if not repository:
            repository = self.repo_repository.create(
                name=repo_name,
                url=repo_url,
                description=f"Repository {repo_name}",
                default_branch=branch or "main"
            )
            
            # Publish repository added event
            event_bus.publish(Event(
                EventType.REPOSITORY_ADDED,
                {
                    "repo_id": repository.id,
                    "repo_url": repo_url,
                    "repo_name": repo_name
                }
            ))
        
        # Check if snapshot already exists for this commit
        if commit_sha:
            existing_snapshot = self.snapshot_repository.get_by_commit_sha(repository.id, commit_sha)
            if existing_snapshot:
                logger.info(f"Snapshot already exists for commit {commit_sha}")
                return existing_snapshot
        
        # Create a codebase from the repository
        secrets = None
        if github_token:
            secrets = SecretsConfig(github_token=github_token)
        
        codebase = Codebase.from_repo(repo_url, secrets=secrets)
        
        # Checkout the specified commit or branch if provided
        if commit_sha:
            codebase.checkout(commit=commit_sha)
        elif branch:
            codebase.checkout(branch=branch)
        
        # Create a snapshot
        return self.create_snapshot(
            codebase=codebase,
            repo_id=repository.id,
            commit_sha=commit_sha,
            branch=branch,
            snapshot_id=snapshot_id
        )
    
    def get_snapshot(self, snapshot_id: str) -> Optional[Snapshot]:
        """
        Get a snapshot by its ID.
        
        Args:
            snapshot_id: The snapshot ID
            
        Returns:
            The snapshot if found, None otherwise
        """
        return self.snapshot_repository.get_by_snapshot_id(snapshot_id)
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot.
        
        Args:
            snapshot_id: The snapshot ID
            
        Returns:
            True if the snapshot was deleted, False otherwise
        """
        snapshot = self.snapshot_repository.get_by_snapshot_id(snapshot_id)
        if not snapshot:
            return False
        
        # Delete files from S3 if enabled
        if self.s3_client:
            # List all objects with the snapshot prefix
            prefix = f"{self.s3_prefix}/{snapshot_id}/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=prefix
            )
            
            if "Contents" in response:
                # Delete all objects
                objects = [{"Key": obj["Key"]} for obj in response["Contents"]]
                self.s3_client.delete_objects(
                    Bucket=self.s3_bucket,
                    Delete={"Objects": objects}
                )
        
        # Delete the snapshot from the database
        # This will cascade to delete files and other related records
        result = self.snapshot_repository.delete(snapshot.id)
        
        if result:
            # Publish snapshot deleted event
            event_bus.publish(Event(
                EventType.SNAPSHOT_DELETED,
                {
                    "snapshot_id": snapshot_id,
                    "repo_id": snapshot.repo_id
                }
            ))
        
        return result
    
    def load_codebase_from_snapshot(self, snapshot: Snapshot) -> Codebase:
        """
        Load a codebase from a snapshot.
        
        Args:
            snapshot: The snapshot to load
            
        Returns:
            A codebase object
        """
        # Get the repository
        repository = self.repo_repository.get_by_id(snapshot.repo_id)
        if not repository:
            raise ValueError(f"Repository not found for snapshot {snapshot.snapshot_id}")
        
        # Create a temporary directory for the codebase
        temp_dir = tempfile.mkdtemp(prefix=f"snapshot_{snapshot.snapshot_id}_")
        
        # Get all files for the snapshot
        files = self.file_repository.get_files_for_snapshot(snapshot.id)
        
        # Create the directory structure
        for file in files:
            # Create the directory if it doesn't exist
            file_dir = os.path.dirname(os.path.join(temp_dir, file.filepath))
            os.makedirs(file_dir, exist_ok=True)
            
            # Get the file content
            content = None
            if file.s3_key and self.s3_client:
                # Get content from S3
                try:
                    response = self.s3_client.get_object(
                        Bucket=self.s3_bucket,
                        Key=file.s3_key
                    )
                    content = response["Body"].read().decode()
                except Exception as e:
                    logger.error(f"Error getting file content from S3: {e}")
            
            # If content is not available from S3, use a placeholder
            if not content:
                content = f"# Placeholder content for {file.filepath}\n# Original content not available"
            
            # Write the content to the file
            with open(os.path.join(temp_dir, file.filepath), "w") as f:
                f.write(content)
        
        # Create a codebase from the directory
        codebase = Codebase.from_directory(temp_dir)
        
        # Set additional metadata
        codebase.repo_path = repository.url
        
        return codebase
    
    def compare_snapshots(self, snapshot1_id: str, snapshot2_id: str) -> Dict[str, Any]:
        """
        Compare two snapshots.
        
        Args:
            snapshot1_id: The first snapshot ID
            snapshot2_id: The second snapshot ID
            
        Returns:
            A dictionary with comparison results
        """
        snapshot1 = self.snapshot_repository.get_by_snapshot_id(snapshot1_id)
        snapshot2 = self.snapshot_repository.get_by_snapshot_id(snapshot2_id)
        
        if not snapshot1 or not snapshot2:
            raise ValueError("One or both snapshots not found")
        
        # Get files for both snapshots
        files1 = {file.filepath: file for file in self.file_repository.get_files_for_snapshot(snapshot1.id)}
        files2 = {file.filepath: file for file in self.file_repository.get_files_for_snapshot(snapshot2.id)}
        
        # Compare files
        files_added = [path for path in files2 if path not in files1]
        files_removed = [path for path in files1 if path not in files2]
        files_modified = [
            path for path in files1 if path in files2 and files1[path].content_hash != files2[path].content_hash
        ]
        
        # Compare metadata
        metadata1 = snapshot1.metadata or {}
        metadata2 = snapshot2.metadata or {}
        
        metrics_diff = {
            "file_count": (metadata2.get("file_count", 0) - metadata1.get("file_count", 0)),
            "function_count": (metadata2.get("function_count", 0) - metadata1.get("function_count", 0)),
            "class_count": (metadata2.get("class_count", 0) - metadata1.get("class_count", 0)),
            "import_count": (metadata2.get("import_count", 0) - metadata1.get("import_count", 0)),
            "symbol_count": (metadata2.get("symbol_count", 0) - metadata1.get("symbol_count", 0))
        }
        
        return {
            "snapshot1_id": snapshot1_id,
            "snapshot2_id": snapshot2_id,
            "files_added": files_added,
            "files_removed": files_removed,
            "files_modified": files_modified,
            "metrics_diff": metrics_diff
        }
"""

