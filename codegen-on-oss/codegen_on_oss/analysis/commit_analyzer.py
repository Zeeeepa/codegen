"""
Commit Analyzer for Codegen-on-OSS

This module provides a commit analyzer that analyzes commits in a repository
and extracts metadata about them, such as files changed, lines added/removed,
and commit messages.
"""

import logging
import os
import subprocess
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Set, Tuple

from codegen import Codebase
from codegen_on_oss.database import (
    get_db_session, RepositoryRepository, CommitRepository, FileRepository
)
from codegen_on_oss.analysis.coordinator import AnalysisContext

logger = logging.getLogger(__name__)

class CommitAnalyzer:
    """
    Commit analyzer for analyzing commits in a repository.
    
    This class analyzes commits in a repository and extracts metadata about them,
    such as files changed, lines added/removed, and commit messages.
    """
    
    def __init__(self):
        """Initialize the commit analyzer."""
        self.repo_repo = RepositoryRepository()
        self.commit_repo = CommitRepository()
        self.file_repo = FileRepository()
    
    async def analyze(self, context: AnalysisContext) -> Dict[str, Any]:
        """
        Analyze a commit.
        
        Args:
            context: The analysis context.
            
        Returns:
            Commit metadata.
        """
        logger.info(f"Analyzing commit: {context.commit_sha}")
        
        codebase = context.codebase
        repo_dir = codebase.root_path
        
        # Get commit metadata
        commit_metadata = await self._get_commit_metadata(context, repo_dir)
        
        # Get file changes
        file_changes = await self._get_file_changes(context, repo_dir)
        
        # Store commit in database
        with get_db_session() as session:
            # Create commit
            commit = self.commit_repo.create(
                session,
                repository_id=context.repository_id,
                sha=context.commit_sha,
                author=commit_metadata.get("author"),
                message=commit_metadata.get("message"),
                timestamp=commit_metadata.get("timestamp")
            )
            context.commit_id = commit.id
            
            # Create files
            for file_path, file_data in file_changes.items():
                # Skip non-source files
                if not file_data.get("is_source_file", True):
                    continue
                
                # Create file
                file = self.file_repo.create(
                    session,
                    commit_id=commit.id,
                    path=file_path,
                    language=file_data.get("language"),
                    content_hash=file_data.get("content_hash"),
                    loc=file_data.get("loc")
                )
            
            session.commit()
        
        # Add results to context
        commit_data = {
            "sha": context.commit_sha,
            "author": commit_metadata.get("author"),
            "message": commit_metadata.get("message"),
            "timestamp": commit_metadata.get("timestamp"),
            "file_changes": file_changes
        }
        
        context.add_result("commit", commit_data)
        
        return commit_data
    
    async def _get_commit_metadata(self, context: AnalysisContext, repo_dir: str) -> Dict[str, Any]:
        """
        Get metadata for a commit.
        
        Args:
            context: The analysis context.
            repo_dir: The repository directory.
            
        Returns:
            Commit metadata.
        """
        # Get commit metadata
        try:
            # Get commit author
            result = subprocess.run(
                ["git", "show", "-s", "--format=%an <%ae>", context.commit_sha],
                cwd=repo_dir,
                check=True,
                capture_output=True,
                text=True
            )
            author = result.stdout.strip()
            
            # Get commit message
            result = subprocess.run(
                ["git", "show", "-s", "--format=%B", context.commit_sha],
                cwd=repo_dir,
                check=True,
                capture_output=True,
                text=True
            )
            message = result.stdout.strip()
            
            # Get commit timestamp
            result = subprocess.run(
                ["git", "show", "-s", "--format=%ci", context.commit_sha],
                cwd=repo_dir,
                check=True,
                capture_output=True,
                text=True
            )
            timestamp_str = result.stdout.strip()
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S %z")
            
            return {
                "author": author,
                "message": message,
                "timestamp": timestamp
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting commit metadata: {e}")
            return {
                "author": "Unknown",
                "message": "",
                "timestamp": datetime.utcnow()
            }
    
    async def _get_file_changes(self, context: AnalysisContext, repo_dir: str) -> Dict[str, Dict[str, Any]]:
        """
        Get file changes for a commit.
        
        Args:
            context: The analysis context.
            repo_dir: The repository directory.
            
        Returns:
            File changes.
        """
        codebase = context.codebase
        
        # Get all files in the repository
        file_changes = {}
        for file_path in codebase.get_all_file_paths():
            try:
                source_file = codebase.get_source_file(file_path)
                
                # Skip non-source files
                if not source_file or not source_file.content:
                    file_changes[file_path] = {
                        "is_source_file": False
                    }
                    continue
                
                # Calculate file hash
                content_hash = hashlib.md5(source_file.content.encode()).hexdigest()
                
                # Count lines
                loc = len(source_file.content.split('\n'))
                
                # Determine language
                ext = os.path.splitext(file_path)[1].lower()
                language = self._get_language_from_extension(ext)
                
                file_changes[file_path] = {
                    "is_source_file": True,
                    "content_hash": content_hash,
                    "loc": loc,
                    "language": language
                }
            except Exception as e:
                logger.warning(f"Error processing file {file_path}: {e}")
                file_changes[file_path] = {
                    "is_source_file": False
                }
        
        return file_changes
    
    def _get_language_from_extension(self, ext: str) -> Optional[str]:
        """
        Get the programming language from a file extension.
        
        Args:
            ext: The file extension.
            
        Returns:
            The programming language or None if unknown.
        """
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

