"""
Repository Analyzer for Codegen-on-OSS

This module provides a repository analyzer that analyzes repositories
and extracts metadata about them.
"""

import logging
import os
import tempfile
import subprocess
from typing import Dict, List, Optional, Any, Union

from codegen import Codebase
from codegen_on_oss.database import get_db_session, RepositoryRepository
from codegen_on_oss.analysis.coordinator import AnalysisContext

logger = logging.getLogger(__name__)

class RepositoryAnalyzer:
    """
    Repository analyzer for analyzing repositories.
    
    This class analyzes repositories and extracts metadata about them,
    such as the number of files, languages used, and contributors.
    """
    
    def __init__(self):
        """Initialize the repository analyzer."""
        self.repo_repo = RepositoryRepository()
    
    async def analyze(self, context: AnalysisContext) -> Dict[str, Any]:
        """
        Analyze a repository.
        
        Args:
            context: The analysis context.
            
        Returns:
            Repository metadata.
        """
        logger.info(f"Analyzing repository: {context.repo_url}")
        
        # Clone repository if codebase is not provided
        if not context.codebase:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Clone repository
                clone_cmd = [
                    "git", "clone", 
                    "--branch", context.branch or "main", 
                    "--single-branch", "--depth", "1",
                    context.repo_url, temp_dir
                ]
                
                if context.commit_sha:
                    # If commit SHA is provided, clone without branch and checkout the commit
                    clone_cmd = [
                        "git", "clone", 
                        "--single-branch", "--depth", "1",
                        context.repo_url, temp_dir
                    ]
                
                subprocess.run(clone_cmd, check=True)
                
                if context.commit_sha:
                    # Checkout specific commit
                    subprocess.run(
                        ["git", "checkout", context.commit_sha],
                        cwd=temp_dir,
                        check=True
                    )
                
                # Create codebase
                context.codebase = Codebase(temp_dir)
                
                # Get commit SHA if not provided
                if not context.commit_sha:
                    result = subprocess.run(
                        ["git", "rev-parse", "HEAD"],
                        cwd=temp_dir,
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    context.commit_sha = result.stdout.strip()
        
        # Extract repository metadata
        metadata = await self._extract_metadata(context)
        
        # Update repository in database
        with get_db_session() as session:
            self.repo_repo.update(
                session,
                context.repository_id,
                default_branch=metadata.get("default_branch", "main"),
                last_analyzed=metadata.get("analyzed_at")
            )
            session.commit()
        
        # Add results to context
        context.add_result("repository", metadata)
        
        return metadata
    
    async def _extract_metadata(self, context: AnalysisContext) -> Dict[str, Any]:
        """
        Extract metadata from a repository.
        
        Args:
            context: The analysis context.
            
        Returns:
            Repository metadata.
        """
        codebase = context.codebase
        repo_dir = codebase.root_path
        
        # Get repository metadata
        metadata = {
            "name": os.path.basename(context.repo_url.rstrip('/')),
            "url": context.repo_url,
            "commit_sha": context.commit_sha,
            "branch": context.branch,
            "analyzed_at": None,  # Will be set by the database
        }
        
        # Get default branch
        try:
            result = subprocess.run(
                ["git", "symbolic-ref", "--short", "HEAD"],
                cwd=repo_dir,
                check=True,
                capture_output=True,
                text=True
            )
            metadata["default_branch"] = result.stdout.strip()
        except subprocess.CalledProcessError:
            metadata["default_branch"] = context.branch or "main"
        
        # Get file statistics
        file_stats = {
            "total_files": 0,
            "languages": {},
            "file_extensions": {},
            "file_sizes": {
                "min": float("inf"),
                "max": 0,
                "avg": 0,
                "total": 0
            }
        }
        
        # Walk through repository and collect file statistics
        total_size = 0
        for root, _, files in os.walk(repo_dir):
            for file in files:
                # Skip .git directory
                if ".git" in root:
                    continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_dir)
                
                # Skip binary files and large files
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > 10 * 1024 * 1024:  # Skip files larger than 10MB
                        continue
                    
                    # Update file size statistics
                    file_stats["file_sizes"]["min"] = min(file_stats["file_sizes"]["min"], file_size)
                    file_stats["file_sizes"]["max"] = max(file_stats["file_sizes"]["max"], file_size)
                    total_size += file_size
                    
                    # Update file count
                    file_stats["total_files"] += 1
                    
                    # Update file extension statistics
                    ext = os.path.splitext(file)[1].lower()
                    if ext:
                        file_stats["file_extensions"][ext] = file_stats["file_extensions"].get(ext, 0) + 1
                    
                    # Determine language based on file extension
                    language = self._get_language_from_extension(ext)
                    if language:
                        file_stats["languages"][language] = file_stats["languages"].get(language, 0) + 1
                    
                    # Add file to context
                    context.add_file(
                        path=rel_path,
                        language=language,
                        content_hash=None,  # Will be set by the commit analyzer
                        loc=None  # Will be set by the commit analyzer
                    )
                    
                except (IOError, OSError):
                    continue
        
        # Calculate average file size
        if file_stats["total_files"] > 0:
            file_stats["file_sizes"]["avg"] = total_size / file_stats["total_files"]
            file_stats["file_sizes"]["total"] = total_size
        else:
            file_stats["file_sizes"]["min"] = 0
        
        # Get contributor statistics
        try:
            result = subprocess.run(
                ["git", "shortlog", "-sne", "--all"],
                cwd=repo_dir,
                check=True,
                capture_output=True,
                text=True
            )
            
            contributors = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    count, author = parts
                    contributors.append({
                        "name": author,
                        "commits": int(count.strip())
                    })
            
            metadata["contributors"] = contributors
            metadata["contributor_count"] = len(contributors)
        except subprocess.CalledProcessError:
            metadata["contributors"] = []
            metadata["contributor_count"] = 0
        
        # Add file statistics to metadata
        metadata["file_stats"] = file_stats
        
        return metadata
    
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

