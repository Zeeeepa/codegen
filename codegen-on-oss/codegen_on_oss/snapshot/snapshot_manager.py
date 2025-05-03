"""
Enhanced snapshot manager for Codegen-on-OSS

This module provides an enhanced snapshot manager with differential capabilities.
"""

import os
import json
import shutil
import tempfile
import logging
import difflib
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Set, Tuple

from sqlalchemy.orm import Session

from codegen import Codebase
from codegen_on_oss.database import (
    get_db,
    CodebaseEntity,
    SnapshotEntity,
)
from codegen_on_oss.events import EventBus, Event, EventType

logger = logging.getLogger(__name__)


class SnapshotManager:
    """
    Enhanced snapshot manager with differential capabilities.
    
    This class provides functionality for creating, comparing, and managing
    snapshots of codebases.
    """
    
    def __init__(
        self,
        storage_path: str = "./snapshots",
        event_bus: Optional[EventBus] = None,
        db_session: Optional[Session] = None,
    ):
        """
        Initialize the snapshot manager.
        
        Args:
            storage_path: Path to store snapshots.
            event_bus: Event bus for publishing events.
            db_session: Database session for storing snapshot metadata.
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.event_bus = event_bus or EventBus()
        self.db = db_session or next(get_db())
    
    def create_snapshot(
        self,
        codebase: Codebase,
        tag: Optional[str] = None,
        differential: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SnapshotEntity:
        """
        Create a snapshot of a codebase.
        
        Args:
            codebase: The codebase to snapshot.
            tag: Optional tag for the snapshot.
            differential: Whether to create a differential snapshot.
            metadata: Optional metadata for the snapshot.
            
        Returns:
            The created snapshot entity.
        """
        # Get codebase metadata
        repo_url = codebase.repo_url if hasattr(codebase, "repo_url") else None
        commit_hash = codebase.commit_hash if hasattr(codebase, "commit_hash") else None
        branch = codebase.branch if hasattr(codebase, "branch") else None
        
        # Get or create codebase entity
        codebase_entity = self._get_or_create_codebase(codebase)
        
        # Create snapshot directory
        snapshot_dir = self._create_snapshot_dir(codebase_entity.name, commit_hash)
        
        # Get previous snapshot for differential
        previous_snapshot = None
        if differential:
            previous_snapshot = self._get_latest_snapshot(codebase_entity.id)
        
        # Create snapshot files
        diff_from_previous = None
        if differential and previous_snapshot:
            # Create differential snapshot
            diff_from_previous = self._create_differential_snapshot(
                codebase, previous_snapshot, snapshot_dir
            )
        else:
            # Create full snapshot
            self._create_full_snapshot(codebase, snapshot_dir)
        
        # Create snapshot entity
        snapshot = SnapshotEntity(
            codebase_id=codebase_entity.id,
            commit_hash=commit_hash,
            branch=branch,
            tag=tag,
            metadata=metadata or {},
            storage_path=str(snapshot_dir),
            diff_from_previous=diff_from_previous,
        )
        
        # Save snapshot entity
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        
        # Publish event
        self.event_bus.publish(
            Event(
                type=EventType.SNAPSHOT_CREATED,
                source="snapshot_manager",
                data={
                    "snapshot_id": snapshot.id,
                    "codebase_id": codebase_entity.id,
                    "commit_hash": commit_hash,
                    "tag": tag,
                },
            )
        )
        
        return snapshot
    
    def get_snapshot(self, snapshot_id: int) -> Optional[SnapshotEntity]:
        """
        Get a snapshot by ID.
        
        Args:
            snapshot_id: The ID of the snapshot to get.
            
        Returns:
            The snapshot entity, or None if not found.
        """
        return self.db.query(SnapshotEntity).filter(SnapshotEntity.id == snapshot_id).first()
    
    def delete_snapshot(self, snapshot_id: int) -> bool:
        """
        Delete a snapshot.
        
        Args:
            snapshot_id: The ID of the snapshot to delete.
            
        Returns:
            True if the snapshot was deleted, False otherwise.
        """
        snapshot = self.get_snapshot(snapshot_id)
        if not snapshot:
            return False
        
        # Delete snapshot files
        if os.path.exists(snapshot.storage_path):
            shutil.rmtree(snapshot.storage_path)
        
        # Delete snapshot entity
        self.db.delete(snapshot)
        self.db.commit()
        
        # Publish event
        self.event_bus.publish(
            Event(
                type=EventType.SNAPSHOT_DELETED,
                source="snapshot_manager",
                data={"snapshot_id": snapshot_id},
            )
        )
        
        return True
    
    def compare_snapshots(
        self, snapshot_id1: int, snapshot_id2: int
    ) -> Dict[str, Any]:
        """
        Compare two snapshots.
        
        Args:
            snapshot_id1: The ID of the first snapshot.
            snapshot_id2: The ID of the second snapshot.
            
        Returns:
            A dictionary with comparison results.
        """
        snapshot1 = self.get_snapshot(snapshot_id1)
        snapshot2 = self.get_snapshot(snapshot_id2)
        
        if not snapshot1 or not snapshot2:
            raise ValueError("One or both snapshots not found")
        
        # Load snapshots
        files1 = self._load_snapshot_files(snapshot1)
        files2 = self._load_snapshot_files(snapshot2)
        
        # Compare files
        added_files = set(files2.keys()) - set(files1.keys())
        removed_files = set(files1.keys()) - set(files2.keys())
        modified_files = []
        
        for file_path in set(files1.keys()) & set(files2.keys()):
            if files1[file_path] != files2[file_path]:
                modified_files.append(file_path)
        
        # Generate diffs for modified files
        diffs = {}
        for file_path in modified_files:
            diff = difflib.unified_diff(
                files1[file_path].splitlines(),
                files2[file_path].splitlines(),
                fromfile=f"snapshot1/{file_path}",
                tofile=f"snapshot2/{file_path}",
                lineterm="",
            )
            diffs[file_path] = "\n".join(diff)
        
        # Create comparison result
        result = {
            "snapshot1_id": snapshot_id1,
            "snapshot2_id": snapshot_id2,
            "added_files": list(added_files),
            "removed_files": list(removed_files),
            "modified_files": modified_files,
            "diffs": diffs,
        }
        
        # Publish event
        self.event_bus.publish(
            Event(
                type=EventType.SNAPSHOT_COMPARED,
                source="snapshot_manager",
                data={
                    "snapshot1_id": snapshot_id1,
                    "snapshot2_id": snapshot_id2,
                    "added_files_count": len(added_files),
                    "removed_files_count": len(removed_files),
                    "modified_files_count": len(modified_files),
                },
            )
        )
        
        return result
    
    def _get_or_create_codebase(self, codebase: Codebase) -> CodebaseEntity:
        """
        Get or create a codebase entity.
        
        Args:
            codebase: The codebase to get or create an entity for.
            
        Returns:
            The codebase entity.
        """
        repo_url = codebase.repo_url if hasattr(codebase, "repo_url") else None
        name = codebase.name if hasattr(codebase, "name") else os.path.basename(repo_url or "")
        
        # Try to find existing codebase
        codebase_entity = (
            self.db.query(CodebaseEntity)
            .filter(CodebaseEntity.repository_url == repo_url)
            .first()
        )
        
        if not codebase_entity:
            # Create new codebase entity
            codebase_entity = CodebaseEntity(
                name=name,
                repository_url=repo_url,
                default_branch=codebase.branch if hasattr(codebase, "branch") else None,
                metadata={},
            )
            self.db.add(codebase_entity)
            self.db.commit()
            self.db.refresh(codebase_entity)
            
            # Publish event
            self.event_bus.publish(
                Event(
                    type=EventType.CODEBASE_ADDED,
                    source="snapshot_manager",
                    data={
                        "codebase_id": codebase_entity.id,
                        "name": name,
                        "repository_url": repo_url,
                    },
                )
            )
        
        return codebase_entity
    
    def _get_latest_snapshot(self, codebase_id: int) -> Optional[SnapshotEntity]:
        """
        Get the latest snapshot for a codebase.
        
        Args:
            codebase_id: The ID of the codebase.
            
        Returns:
            The latest snapshot entity, or None if no snapshots exist.
        """
        return (
            self.db.query(SnapshotEntity)
            .filter(SnapshotEntity.codebase_id == codebase_id)
            .order_by(SnapshotEntity.created_at.desc())
            .first()
        )
    
    def _create_snapshot_dir(self, codebase_name: str, commit_hash: Optional[str]) -> Path:
        """
        Create a directory for a snapshot.
        
        Args:
            codebase_name: The name of the codebase.
            commit_hash: The commit hash of the snapshot.
            
        Returns:
            The path to the created directory.
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        dir_name = f"{codebase_name}_{timestamp}"
        if commit_hash:
            dir_name += f"_{commit_hash[:8]}"
        
        snapshot_dir = self.storage_path / dir_name
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        return snapshot_dir
    
    def _create_full_snapshot(self, codebase: Codebase, snapshot_dir: Path) -> None:
        """
        Create a full snapshot of a codebase.
        
        Args:
            codebase: The codebase to snapshot.
            snapshot_dir: The directory to store the snapshot.
        """
        # Get all files in the codebase
        for file_path in codebase.get_all_files():
            try:
                # Skip binary files and large files
                if self._is_binary_file(file_path) or os.path.getsize(file_path) > 10 * 1024 * 1024:
                    continue
                
                # Read file content
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                # Create relative path
                rel_path = os.path.relpath(file_path, codebase.root_dir)
                
                # Write file to snapshot directory
                output_path = snapshot_dir / rel_path
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"Error creating snapshot for file {file_path}: {e}")
    
    def _create_differential_snapshot(
        self, codebase: Codebase, previous_snapshot: SnapshotEntity, snapshot_dir: Path
    ) -> str:
        """
        Create a differential snapshot of a codebase.
        
        Args:
            codebase: The codebase to snapshot.
            previous_snapshot: The previous snapshot to compare against.
            snapshot_dir: The directory to store the snapshot.
            
        Returns:
            A string containing the diff from the previous snapshot.
        """
        # Load previous snapshot files
        prev_files = self._load_snapshot_files(previous_snapshot)
        
        # Get all files in the codebase
        current_files = {}
        for file_path in codebase.get_all_files():
            try:
                # Skip binary files and large files
                if self._is_binary_file(file_path) or os.path.getsize(file_path) > 10 * 1024 * 1024:
                    continue
                
                # Read file content
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                # Create relative path
                rel_path = os.path.relpath(file_path, codebase.root_dir)
                current_files[rel_path] = content
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
        
        # Find added, removed, and modified files
        added_files = set(current_files.keys()) - set(prev_files.keys())
        removed_files = set(prev_files.keys()) - set(current_files.keys())
        modified_files = []
        
        for file_path in set(prev_files.keys()) & set(current_files.keys()):
            if prev_files[file_path] != current_files[file_path]:
                modified_files.append(file_path)
        
        # Create diff
        diff_lines = []
        
        # Add diff header
        diff_lines.append(f"Diff created at {datetime.now().isoformat()}")
        diff_lines.append(f"Previous snapshot ID: {previous_snapshot.id}")
        diff_lines.append("")
        
        # Add diffs for modified files
        for file_path in modified_files:
            diff = difflib.unified_diff(
                prev_files[file_path].splitlines(),
                current_files[file_path].splitlines(),
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
                lineterm="",
            )
            diff_lines.extend(diff)
            diff_lines.append("")
        
        # Add info about added and removed files
        if added_files:
            diff_lines.append("Added files:")
            for file_path in sorted(added_files):
                diff_lines.append(f"  {file_path}")
            diff_lines.append("")
        
        if removed_files:
            diff_lines.append("Removed files:")
            for file_path in sorted(removed_files):
                diff_lines.append(f"  {file_path}")
            diff_lines.append("")
        
        # Write diff to file
        diff_path = snapshot_dir / "diff.patch"
        with open(diff_path, "w", encoding="utf-8") as f:
            f.write("\n".join(diff_lines))
        
        # Write metadata
        metadata_path = snapshot_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "previous_snapshot_id": previous_snapshot.id,
                    "added_files": list(added_files),
                    "removed_files": list(removed_files),
                    "modified_files": modified_files,
                },
                f,
                indent=2,
            )
        
        # Write added and modified files
        for file_path in added_files | set(modified_files):
            output_path = snapshot_dir / file_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(current_files[file_path])
        
        return "\n".join(diff_lines)
    
    def _load_snapshot_files(self, snapshot: SnapshotEntity) -> Dict[str, str]:
        """
        Load files from a snapshot.
        
        Args:
            snapshot: The snapshot to load files from.
            
        Returns:
            A dictionary mapping file paths to file contents.
        """
        files = {}
        snapshot_path = Path(snapshot.storage_path)
        
        # Check if this is a differential snapshot
        if snapshot.diff_from_previous:
            # Load metadata
            metadata_path = snapshot_path / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                
                # Load previous snapshot
                previous_snapshot = self.get_snapshot(metadata["previous_snapshot_id"])
                if previous_snapshot:
                    # Load files from previous snapshot
                    files = self._load_snapshot_files(previous_snapshot)
                    
                    # Apply changes
                    for file_path in metadata.get("removed_files", []):
                        if file_path in files:
                            del files[file_path]
                    
                    # Add/update modified files
                    for file_path in metadata.get("added_files", []) + metadata.get("modified_files", []):
                        file_path_obj = snapshot_path / file_path
                        if file_path_obj.exists():
                            with open(file_path_obj, "r", encoding="utf-8", errors="ignore") as f:
                                files[file_path] = f.read()
            
            return files
        
        # This is a full snapshot, load all files
        for file_path in snapshot_path.glob("**/*"):
            if file_path.is_file() and file_path.name != "metadata.json" and file_path.name != "diff.patch":
                rel_path = str(file_path.relative_to(snapshot_path))
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    files[rel_path] = f.read()
        
        return files
    
    @staticmethod
    def _is_binary_file(file_path: str) -> bool:
        """
        Check if a file is binary.
        
        Args:
            file_path: The path to the file.
            
        Returns:
            True if the file is binary, False otherwise.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                f.read(1024)
            return False
        except UnicodeDecodeError:
            return True

