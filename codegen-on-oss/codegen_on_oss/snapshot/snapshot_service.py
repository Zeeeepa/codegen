"""
Enhanced snapshot service for the codegen-on-oss system.

This module provides a service for creating, storing, and retrieving snapshots
of codebases with efficient incremental storage.
"""

import os
import json
import hashlib
import tempfile
import logging
import shutil
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any, Union, Iterator

from sqlalchemy.orm import Session
from sqlalchemy import select

from codegen import Codebase
from codegen.sdk.core.file import SourceFile

from codegen_on_oss.config import settings
from codegen_on_oss.database.models import CodebaseSnapshot, FileManifest
from codegen_on_oss.storage.service import StorageService

logger = logging.getLogger(__name__)


class SnapshotService:
    """Enhanced snapshot service with incremental storage"""
    
    def __init__(self, db_session: Session, storage_service: StorageService):
        """
        Initialize the snapshot service.
        
        Args:
            db_session: SQLAlchemy database session
            storage_service: Storage service for file content
        """
        self.db_session = db_session
        self.storage_service = storage_service
    
    async def create_snapshot(
        self, 
        repo_url: str, 
        commit_sha: Optional[str] = None,
        branch: Optional[str] = None,
        repo_path: Optional[str] = None
    ) -> CodebaseSnapshot:
        """
        Create a new snapshot with efficient storage.
        
        Args:
            repo_url: URL of the repository
            commit_sha: Optional commit SHA to snapshot
            branch: Optional branch name
            repo_path: Optional local path to repository (to avoid cloning)
            
        Returns:
            CodebaseSnapshot: The created snapshot
        """
        # Generate unique snapshot ID
        snapshot_id = uuid.uuid4()
        
        # Check if we already have this snapshot
        existing = await self._get_existing_snapshot(repo_url, commit_sha)
        if existing:
            logger.info(f"Found existing snapshot for {repo_url}@{commit_sha}")
            return existing
        
        # Clone repository if needed
        temp_dir = None
        try:
            if not repo_path:
                temp_dir = tempfile.mkdtemp()
                repo_path = await self._clone_repository(repo_url, commit_sha, temp_dir)
            
            # Create file manifest (paths, hashes)
            manifest = await self._create_file_manifest(repo_path)
            manifest_hash = self._compute_manifest_hash(manifest)
            
            # Check if we have a snapshot with the same manifest hash
            existing_by_hash = await self._get_snapshot_by_manifest(manifest_hash)
            if existing_by_hash:
                logger.info(f"Found existing snapshot with identical content (manifest hash: {manifest_hash})")
                return existing_by_hash
            
            # Store only changed files compared to previous snapshots
            changed_files = await self._identify_changed_files(manifest)
            await self._store_changed_files(repo_path, changed_files)
            
            # Create snapshot record
            snapshot = CodebaseSnapshot(
                id=snapshot_id,
                repository=repo_url,
                commit_sha=commit_sha,
                branch=branch,
                manifest_hash=manifest_hash,
                metadata={
                    "file_count": len(manifest),
                    "changed_file_count": len(changed_files),
                    "languages": self._extract_languages(manifest),
                    "created_at": datetime.now().isoformat()
                }
            )
            
            self.db_session.add(snapshot)
            
            # Add file manifest records
            for file_path, file_info in manifest.items():
                file_manifest = FileManifest(
                    snapshot_id=snapshot_id,
                    file_path=file_path,
                    file_hash=file_info["hash"],
                    file_size=file_info["size"],
                    language=file_info.get("language"),
                    is_stored=file_path in changed_files,
                    storage_path=self.storage_service.get_storage_path(snapshot_id, file_path) if file_path in changed_files else None
                )
                self.db_session.add(file_manifest)
            
            await self.db_session.commit()
            
            return snapshot
        
        finally:
            # Clean up temporary directory if we created one
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    async def get_snapshot(self, snapshot_id: uuid.UUID) -> Optional[CodebaseSnapshot]:
        """
        Get a snapshot by ID.
        
        Args:
            snapshot_id: ID of the snapshot to retrieve
            
        Returns:
            Optional[CodebaseSnapshot]: The snapshot if found, None otherwise
        """
        return await self.db_session.get(CodebaseSnapshot, snapshot_id)
    
    async def get_snapshot_files(
        self, 
        snapshot_id: uuid.UUID,
        path_prefix: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[FileManifest]:
        """
        Get files in a snapshot, optionally filtered by path prefix.
        
        Args:
            snapshot_id: ID of the snapshot
            path_prefix: Optional path prefix to filter by
            limit: Maximum number of files to return
            offset: Offset for pagination
            
        Returns:
            List[FileManifest]: List of file manifests
        """
        query = select(FileManifest).where(FileManifest.snapshot_id == snapshot_id)
        
        if path_prefix:
            query = query.where(FileManifest.file_path.startswith(path_prefix))
        
        query = query.order_by(FileManifest.file_path).limit(limit).offset(offset)
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    async def get_file_content(
        self, 
        snapshot_id: uuid.UUID, 
        file_path: str
    ) -> Optional[str]:
        """
        Get the content of a file in a snapshot.
        
        Args:
            snapshot_id: ID of the snapshot
            file_path: Path of the file
            
        Returns:
            Optional[str]: The file content if found, None otherwise
        """
        # Get the file manifest
        query = select(FileManifest).where(
            FileManifest.snapshot_id == snapshot_id,
            FileManifest.file_path == file_path
        )
        result = await self.db_session.execute(query)
        file_manifest = result.scalar_one_or_none()
        
        if not file_manifest:
            logger.warning(f"File not found in snapshot: {file_path}")
            return None
        
        # If the file is stored directly in this snapshot, retrieve it
        if file_manifest.is_stored:
            return await self.storage_service.get_file_content(snapshot_id, file_path)
        
        # Otherwise, find the snapshot that has this file stored
        stored_file = await self._find_stored_file(file_manifest.file_hash)
        if stored_file:
            return await self.storage_service.get_file_content(
                stored_file.snapshot_id, 
                stored_file.file_path
            )
        
        logger.warning(f"File content not found for {file_path} with hash {file_manifest.file_hash}")
        return None
    
    async def compare_snapshots(
        self, 
        snapshot_id_1: uuid.UUID, 
        snapshot_id_2: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Compare two snapshots and return detailed differences.
        
        Args:
            snapshot_id_1: ID of the first snapshot
            snapshot_id_2: ID of the second snapshot
            
        Returns:
            Dict[str, Any]: Comparison results
        """
        # Get file manifests for both snapshots
        files_1 = {f.file_path: f for f in await self.get_snapshot_files(snapshot_id_1, limit=100000)}
        files_2 = {f.file_path: f for f in await self.get_snapshot_files(snapshot_id_2, limit=100000)}
        
        # Find added, removed, and modified files
        paths_1 = set(files_1.keys())
        paths_2 = set(files_2.keys())
        
        added = paths_2 - paths_1
        removed = paths_1 - paths_2
        common = paths_1 & paths_2
        
        modified = {
            path for path in common 
            if files_1[path].file_hash != files_2[path].file_hash
        }
        
        unchanged = common - modified
        
        # Compute language statistics
        languages_1 = self._compute_language_stats(files_1.values())
        languages_2 = self._compute_language_stats(files_2.values())
        
        return {
            "snapshot_1": str(snapshot_id_1),
            "snapshot_2": str(snapshot_id_2),
            "summary": {
                "files_added": len(added),
                "files_removed": len(removed),
                "files_modified": len(modified),
                "files_unchanged": len(unchanged),
                "total_files_1": len(files_1),
                "total_files_2": len(files_2),
            },
            "added_files": sorted(added),
            "removed_files": sorted(removed),
            "modified_files": sorted(modified),
            "language_stats_1": languages_1,
            "language_stats_2": languages_2,
            "language_changes": self._compare_language_stats(languages_1, languages_2)
        }
    
    async def list_snapshots(
        self,
        repository: Optional[str] = None,
        branch: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[CodebaseSnapshot]:
        """
        List snapshots with optional filtering.
        
        Args:
            repository: Optional repository URL to filter by
            branch: Optional branch name to filter by
            limit: Maximum number of snapshots to return
            offset: Offset for pagination
            
        Returns:
            List[CodebaseSnapshot]: List of snapshots
        """
        query = select(CodebaseSnapshot)
        
        if repository:
            query = query.where(CodebaseSnapshot.repository == repository)
        
        if branch:
            query = query.where(CodebaseSnapshot.branch == branch)
        
        query = query.order_by(CodebaseSnapshot.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    async def delete_snapshot(self, snapshot_id: uuid.UUID) -> bool:
        """
        Delete a snapshot and its associated files.
        
        Args:
            snapshot_id: ID of the snapshot to delete
            
        Returns:
            bool: True if the snapshot was deleted, False otherwise
        """
        snapshot = await self.get_snapshot(snapshot_id)
        if not snapshot:
            logger.warning(f"Snapshot not found: {snapshot_id}")
            return False
        
        # Get files that are stored in this snapshot
        query = select(FileManifest).where(
            FileManifest.snapshot_id == snapshot_id,
            FileManifest.is_stored == True
        )
        result = await self.db_session.execute(query)
        stored_files = result.scalars().all()
        
        # Check if any of these files are used by other snapshots
        for file in stored_files:
            if await self._is_file_used_by_other_snapshots(file.file_hash, snapshot_id):
                # This file is used by other snapshots, so we need to copy it to another snapshot
                await self._migrate_file_to_another_snapshot(file)
            else:
                # This file is only used by this snapshot, so we can delete it
                await self.storage_service.delete_file(snapshot_id, file.file_path)
        
        # Delete the snapshot and its file manifests (cascade delete)
        await self.db_session.delete(snapshot)
        await self.db_session.commit()
        
        return True
    
    # Private helper methods
    
    async def _get_existing_snapshot(
        self, 
        repo_url: str, 
        commit_sha: Optional[str]
    ) -> Optional[CodebaseSnapshot]:
        """Get an existing snapshot for the repository and commit."""
        query = select(CodebaseSnapshot).where(CodebaseSnapshot.repository == repo_url)
        
        if commit_sha:
            query = query.where(CodebaseSnapshot.commit_sha == commit_sha)
        
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_snapshot_by_manifest(self, manifest_hash: str) -> Optional[CodebaseSnapshot]:
        """Get an existing snapshot with the same manifest hash."""
        query = select(CodebaseSnapshot).where(CodebaseSnapshot.manifest_hash == manifest_hash)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()
    
    async def _clone_repository(
        self, 
        repo_url: str, 
        commit_sha: Optional[str],
        temp_dir: str
    ) -> str:
        """Clone a repository to a temporary directory."""
        import subprocess
        
        logger.info(f"Cloning repository: {repo_url}")
        
        # Clone the repository
        clone_cmd = ["git", "clone", repo_url, temp_dir]
        subprocess.run(clone_cmd, check=True, capture_output=True)
        
        # Checkout specific commit if provided
        if commit_sha:
            logger.info(f"Checking out commit: {commit_sha}")
            checkout_cmd = ["git", "-C", temp_dir, "checkout", commit_sha]
            subprocess.run(checkout_cmd, check=True, capture_output=True)
        
        return temp_dir
    
    async def _create_file_manifest(self, repo_path: str) -> Dict[str, Dict[str, Any]]:
        """
        Create a manifest of all files in the repository.
        
        Returns a dictionary mapping file paths to file information:
        {
            "path/to/file.py": {
                "hash": "sha256_hash",
                "size": 1234,
                "language": "python"
            }
        }
        """
        manifest = {}
        exclude_patterns = settings.exclude_patterns
        max_file_size = settings.max_file_size_mb * 1024 * 1024
        
        for root, dirs, files in os.walk(repo_path):
            # Apply directory exclusions
            dirs[:] = [d for d in dirs if not any(
                d == pattern or d.startswith(pattern + os.sep)
                for pattern in exclude_patterns
            )]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_path)
                
                # Skip excluded files
                if any(
                    rel_path == pattern or rel_path.startswith(pattern + os.sep)
                    for pattern in exclude_patterns
                ):
                    continue
                
                # Skip files that are too large
                file_size = os.path.getsize(file_path)
                if file_size > max_file_size:
                    logger.info(f"Skipping large file: {rel_path} ({file_size} bytes)")
                    continue
                
                # Compute file hash
                file_hash = self._compute_file_hash(file_path)
                
                # Detect language
                language = self._detect_language(rel_path)
                
                manifest[rel_path] = {
                    "hash": file_hash,
                    "size": file_size,
                    "language": language
                }
        
        logger.info(f"Created manifest with {len(manifest)} files")
        return manifest
    
    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def _compute_manifest_hash(self, manifest: Dict[str, Dict[str, Any]]) -> str:
        """Compute a hash of the entire manifest to uniquely identify the codebase state."""
        manifest_str = json.dumps(manifest, sort_keys=True)
        return hashlib.sha256(manifest_str.encode()).hexdigest()
    
    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect the programming language of a file based on its extension."""
        ext = os.path.splitext(file_path)[1].lower()
        
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
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
            ".json": "json",
            ".md": "markdown",
            ".rs": "rust",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".sh": "shell",
            ".bash": "shell",
            ".sql": "sql",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".xml": "xml",
            ".toml": "toml",
            ".ini": "ini",
            ".cfg": "ini",
            ".conf": "ini",
        }
        
        return language_map.get(ext)
    
    async def _identify_changed_files(self, manifest: Dict[str, Dict[str, Any]]) -> Set[str]:
        """
        Identify files that need to be stored because they don't exist in previous snapshots.
        
        Returns a set of file paths that need to be stored.
        """
        changed_files = set()
        
        for file_path, file_info in manifest.items():
            file_hash = file_info["hash"]
            
            # Check if this file hash already exists in the database
            if not await self._find_stored_file(file_hash):
                changed_files.add(file_path)
        
        logger.info(f"Identified {len(changed_files)} changed files out of {len(manifest)} total files")
        return changed_files
    
    async def _find_stored_file(self, file_hash: str) -> Optional[FileManifest]:
        """Find a stored file with the given hash."""
        query = select(FileManifest).where(
            FileManifest.file_hash == file_hash,
            FileManifest.is_stored == True
        ).limit(1)
        
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()
    
    async def _store_changed_files(self, repo_path: str, changed_files: Set[str]) -> None:
        """Store changed files in the storage service."""
        for file_path in changed_files:
            full_path = os.path.join(repo_path, file_path)
            
            with open(full_path, "rb") as f:
                content = f.read()
            
            await self.storage_service.store_file(file_path, content)
    
    async def _is_file_used_by_other_snapshots(
        self, 
        file_hash: str, 
        current_snapshot_id: uuid.UUID
    ) -> bool:
        """Check if a file is used by snapshots other than the current one."""
        query = select(FileManifest).where(
            FileManifest.file_hash == file_hash,
            FileManifest.snapshot_id != current_snapshot_id
        ).limit(1)
        
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def _migrate_file_to_another_snapshot(self, file: FileManifest) -> None:
        """Migrate a file to another snapshot that uses it."""
        # Find another snapshot that uses this file
        query = select(FileManifest).where(
            FileManifest.file_hash == file.file_hash,
            FileManifest.snapshot_id != file.snapshot_id
        ).limit(1)
        
        result = await self.db_session.execute(query)
        other_file = result.scalar_one_or_none()
        
        if not other_file:
            logger.warning(f"No other snapshot found for file: {file.file_path}")
            return
        
        # Copy the file content to the other snapshot
        content = await self.storage_service.get_file_content(file.snapshot_id, file.file_path)
        if content:
            await self.storage_service.store_file(other_file.snapshot_id, other_file.file_path, content)
            
            # Update the other file's is_stored flag
            other_file.is_stored = True
            other_file.storage_path = self.storage_service.get_storage_path(
                other_file.snapshot_id, 
                other_file.file_path
            )
            
            await self.db_session.commit()
    
    def _extract_languages(self, manifest: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
        """Extract language statistics from a manifest."""
        languages = {}
        
        for file_info in manifest.values():
            language = file_info.get("language")
            if language:
                languages[language] = languages.get(language, 0) + 1
        
        return languages
    
    def _compute_language_stats(self, files: Iterator[FileManifest]) -> Dict[str, int]:
        """Compute language statistics from a list of files."""
        languages = {}
        
        for file in files:
            if file.language:
                languages[file.language] = languages.get(file.language, 0) + 1
        
        return languages
    
    def _compare_language_stats(
        self, 
        stats1: Dict[str, int], 
        stats2: Dict[str, int]
    ) -> Dict[str, Dict[str, Any]]:
        """Compare language statistics between two snapshots."""
        all_languages = set(stats1.keys()) | set(stats2.keys())
        changes = {}
        
        for lang in all_languages:
            count1 = stats1.get(lang, 0)
            count2 = stats2.get(lang, 0)
            diff = count2 - count1
            
            if diff != 0:
                changes[lang] = {
                    "before": count1,
                    "after": count2,
                    "diff": diff,
                    "percent_change": (diff / count1 * 100) if count1 > 0 else float("inf")
                }
        
        return changes

