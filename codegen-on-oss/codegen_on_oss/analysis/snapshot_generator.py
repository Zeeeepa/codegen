"""
Snapshot Generator for Codegen-on-OSS

This module provides a snapshot generator that creates snapshots of codebases
at specific points in time, with support for differential snapshots to reduce
storage requirements.
"""

import logging
import os
import json
import hashlib
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Set, Tuple

from codegen import Codebase
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.symbol import Symbol

from codegen_on_oss.database import (
    get_db_session, RepositoryRepository, CommitRepository,
    FileRepository, SymbolRepository, SnapshotRepository
)
from codegen_on_oss.analysis.coordinator import AnalysisContext

logger = logging.getLogger(__name__)

class SnapshotGenerator:
    """
    Snapshot generator for creating snapshots of codebases.
    
    This class creates snapshots of codebases at specific points in time,
    with support for differential snapshots to reduce storage requirements.
    """
    
    def __init__(self):
        """Initialize the snapshot generator."""
        self.repo_repo = RepositoryRepository()
        self.commit_repo = CommitRepository()
        self.file_repo = FileRepository()
        self.symbol_repo = SymbolRepository()
        self.snapshot_repo = SnapshotRepository()
    
    async def generate(self, context: AnalysisContext) -> Dict[str, Any]:
        """
        Generate a snapshot of a codebase.
        
        Args:
            context: The analysis context.
            
        Returns:
            Snapshot metadata.
        """
        logger.info(f"Generating snapshot for repository: {context.repo_url}")
        
        # Get previous snapshot for differential snapshot
        previous_snapshot = await self._get_previous_snapshot(context)
        
        # Generate snapshot data
        snapshot_data = await self._generate_snapshot_data(context, previous_snapshot)
        
        # Calculate snapshot hash
        snapshot_hash = self._calculate_snapshot_hash(snapshot_data)
        
        # Check if snapshot already exists
        with get_db_session() as session:
            existing_snapshot = self.snapshot_repo.get_by_hash(
                session, context.repository_id, snapshot_hash
            )
            
            if existing_snapshot:
                logger.info(f"Snapshot already exists with hash: {snapshot_hash}")
                return {
                    "id": existing_snapshot.id,
                    "repository_id": existing_snapshot.repository_id,
                    "commit_sha": existing_snapshot.commit_sha,
                    "snapshot_hash": existing_snapshot.snapshot_hash,
                    "created_at": existing_snapshot.created_at.isoformat(),
                    "is_new": False
                }
        
        # Store snapshot in database
        with get_db_session() as session:
            snapshot = self.snapshot_repo.create(
                session,
                repository_id=context.repository_id,
                commit_sha=context.commit_sha,
                snapshot_hash=snapshot_hash,
                description=f"Snapshot of {context.repo_url} at {context.commit_sha}",
                data=snapshot_data
            )
            
            # Add files to snapshot
            for file_data in context.files:
                file = self.file_repo.get_by_path(session, context.commit_id, file_data["path"])
                if file:
                    self.snapshot_repo.add_file(session, snapshot.id, file.id)
            
            session.commit()
            
            # Add snapshot to context
            snapshot_metadata = {
                "id": snapshot.id,
                "repository_id": snapshot.repository_id,
                "commit_sha": snapshot.commit_sha,
                "snapshot_hash": snapshot.snapshot_hash,
                "created_at": snapshot.created_at.isoformat(),
                "is_new": True,
                "is_differential": previous_snapshot is not None,
                "previous_snapshot_id": previous_snapshot["id"] if previous_snapshot else None
            }
            
            context.add_result("snapshot", snapshot_metadata)
            
            return snapshot_metadata
    
    async def _get_previous_snapshot(self, context: AnalysisContext) -> Optional[Dict[str, Any]]:
        """
        Get the previous snapshot for a repository.
        
        Args:
            context: The analysis context.
            
        Returns:
            The previous snapshot or None if not found.
        """
        with get_db_session() as session:
            snapshots = self.snapshot_repo.get_latest_snapshots(session, context.repository_id, limit=1)
            
            if snapshots:
                snapshot = snapshots[0]
                return {
                    "id": snapshot.id,
                    "repository_id": snapshot.repository_id,
                    "commit_sha": snapshot.commit_sha,
                    "snapshot_hash": snapshot.snapshot_hash,
                    "created_at": snapshot.created_at.isoformat(),
                    "data": snapshot.data
                }
            
            return None
    
    async def _generate_snapshot_data(
        self, 
        context: AnalysisContext,
        previous_snapshot: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate snapshot data for a codebase.
        
        Args:
            context: The analysis context.
            previous_snapshot: The previous snapshot for differential snapshot.
            
        Returns:
            Snapshot data.
        """
        codebase = context.codebase
        
        # Generate file data
        files_data = {}
        for file_path in codebase.get_all_file_paths():
            try:
                source_file = codebase.get_source_file(file_path)
                
                # Skip non-source files
                if not source_file or not source_file.content:
                    continue
                
                # Calculate file hash
                file_hash = hashlib.md5(source_file.content.encode()).hexdigest()
                
                # Check if file has changed since previous snapshot
                if (previous_snapshot and 
                    previous_snapshot["data"].get("files", {}).get(file_path, {}).get("hash") == file_hash):
                    # File hasn't changed, reference previous snapshot
                    files_data[file_path] = {
                        "hash": file_hash,
                        "reference": {
                            "snapshot_id": previous_snapshot["id"],
                            "path": file_path
                        }
                    }
                else:
                    # File has changed or is new, store full content
                    files_data[file_path] = {
                        "hash": file_hash,
                        "content": source_file.content,
                        "language": self._get_language_from_path(file_path),
                        "loc": len(source_file.content.split('\n'))
                    }
            except Exception as e:
                logger.warning(f"Error processing file {file_path}: {e}")
                continue
        
        # Generate symbol data
        symbols_data = {}
        for file_path, file_data in files_data.items():
            # Skip referenced files
            if "reference" in file_data:
                continue
            
            try:
                source_file = codebase.get_source_file(file_path)
                
                # Extract functions
                for function in source_file.get_functions():
                    symbol_id = f"{file_path}:{function.name}:{function.start_line}"
                    symbols_data[symbol_id] = {
                        "name": function.name,
                        "qualified_name": function.qualified_name,
                        "type": "function",
                        "file_path": file_path,
                        "line_start": function.start_line,
                        "line_end": function.end_line,
                        "content": function.content
                    }
                
                # Extract classes
                for class_def in source_file.get_classes():
                    symbol_id = f"{file_path}:{class_def.name}:{class_def.start_line}"
                    symbols_data[symbol_id] = {
                        "name": class_def.name,
                        "qualified_name": class_def.qualified_name,
                        "type": "class",
                        "file_path": file_path,
                        "line_start": class_def.start_line,
                        "line_end": class_def.end_line,
                        "content": class_def.content
                    }
            except Exception as e:
                logger.warning(f"Error extracting symbols from {file_path}: {e}")
                continue
        
        # Generate snapshot data
        snapshot_data = {
            "repository": {
                "name": os.path.basename(context.repo_url.rstrip('/')),
                "url": context.repo_url,
                "commit_sha": context.commit_sha
            },
            "files": files_data,
            "symbols": symbols_data,
            "created_at": datetime.utcnow().isoformat(),
            "is_differential": previous_snapshot is not None,
            "previous_snapshot_id": previous_snapshot["id"] if previous_snapshot else None
        }
        
        return snapshot_data
    
    def _calculate_snapshot_hash(self, snapshot_data: Dict[str, Any]) -> str:
        """
        Calculate a hash for snapshot data.
        
        Args:
            snapshot_data: The snapshot data.
            
        Returns:
            The snapshot hash.
        """
        # Create a deterministic representation of the snapshot data
        # Include only file hashes and repository info
        hash_data = {
            "repository": snapshot_data["repository"],
            "file_hashes": {
                path: data["hash"] 
                for path, data in snapshot_data["files"].items()
            }
        }
        
        # Calculate hash
        hash_str = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_str.encode()).hexdigest()
    
    def _get_language_from_path(self, file_path: str) -> Optional[str]:
        """
        Get the programming language from a file path.
        
        Args:
            file_path: The file path.
            
        Returns:
            The programming language or None if unknown.
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        # Map of file extensions to languages
        extension_map = {
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
            ".sass": "SASS",
            ".less": "LESS",
            ".json": "JSON",
            ".xml": "XML",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".md": "Markdown",
            ".sh": "Shell",
            ".bat": "Batch",
            ".ps1": "PowerShell",
            ".sql": "SQL",
            ".r": "R",
            ".dart": "Dart",
            ".lua": "Lua",
            ".pl": "Perl",
            ".pm": "Perl",
            ".t": "Perl",
            ".ex": "Elixir",
            ".exs": "Elixir",
            ".erl": "Erlang",
            ".hrl": "Erlang",
            ".clj": "Clojure",
            ".groovy": "Groovy",
            ".hs": "Haskell",
            ".lhs": "Haskell",
            ".fs": "F#",
            ".fsx": "F#",
            ".ml": "OCaml",
            ".mli": "OCaml",
        }
        
        return extension_map.get(ext)

