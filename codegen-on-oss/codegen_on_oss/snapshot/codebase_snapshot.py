"""
Codebase Snapshot Module

This module provides functionality for creating, storing, and retrieving snapshots
of codebases at specific points in time. It supports comparing snapshots to analyze
changes between different versions of a codebase.
"""

import hashlib
import json
import logging
import os
import tempfile
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from codegen import Codebase
from codegen.configs.models.secrets import SecretsConfig
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.symbol import Symbol

logger = logging.getLogger(__name__)


class CodebaseSnapshot:
    """
    A class that captures the state of a codebase at a specific point in time.
    Provides methods for serializing, deserializing, and comparing snapshots.
    """

    def __init__(
        self,
        codebase: Codebase,
        commit_sha: Optional[str] = None,
        snapshot_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        """
        Initialize a new CodebaseSnapshot.

        Args:
            codebase: The Codebase object to snapshot
            commit_sha: The commit SHA associated with this snapshot
            snapshot_id: Optional custom ID for the snapshot
            timestamp: Optional timestamp for when the snapshot was created
        """
        self.codebase = codebase
        self.commit_sha = commit_sha
        self.timestamp = timestamp or datetime.now()

        # Generate a unique ID if not provided
        if snapshot_id:
            self.snapshot_id = snapshot_id
        else:
            # Create a unique ID based on repo name, commit SHA, and timestamp
            id_string = f"{codebase.repo_path}:{commit_sha or 'unknown'}:{self.timestamp.isoformat()}"
            self.snapshot_id = hashlib.md5(id_string.encode()).hexdigest()

        # Capture key metrics and metadata
        self.metadata = self._capture_metadata()
        self.file_metrics = self._capture_file_metrics()
        self.function_metrics = self._capture_function_metrics()
        self.class_metrics = self._capture_class_metrics()
        self.import_metrics = self._capture_import_metrics()

    @classmethod
    def create_from_repo(
        cls,
        repo_url: str,
        commit_sha: Optional[str] = None,
        github_token: Optional[str] = None,
        snapshot_id: Optional[str] = None,
        cleanup: bool = True,
    ) -> "CodebaseSnapshot":
        """
        Create a snapshot directly from a repository URL.

        Args:
            repo_url: The repository URL or owner/repo string
            commit_sha: Optional commit SHA to checkout
            github_token: Optional GitHub token for private repositories
            snapshot_id: Optional custom ID for the snapshot
            cleanup: Whether to clean up temporary directories after creating the snapshot

        Returns:
            A new CodebaseSnapshot instance
        """
        # Set up secrets if a GitHub token is provided
        secrets = None
        if github_token:
            secrets = SecretsConfig(github_token=github_token)

        # Create a temporary directory for cloning if needed
        temp_dir = None
        try:
            # Create a temporary directory for cloning if needed
            temp_dir = tempfile.mkdtemp(prefix="codegen_snapshot_")
            logger.info(f"Created temporary directory: {temp_dir}")
            
            # Clone the repository
            codebase = Codebase.from_repo(repo_url, secrets=secrets, clone_path=temp_dir)

            # Checkout the specified commit if provided
            if commit_sha:
                codebase.checkout(commit=commit_sha)

            # Create the snapshot
            snapshot = cls(codebase, commit_sha, snapshot_id)

            return snapshot
        finally:
            # Clean up the temporary directory if requested
            if cleanup and temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")

    def _capture_metadata(self) -> Dict[str, Any]:
        """Capture general metadata about the codebase."""
        return {
            "repo_path": self.codebase.repo_path,
            "commit_sha": self.commit_sha,
            "timestamp": self.timestamp.isoformat(),
            "snapshot_id": self.snapshot_id,
            "file_count": len(list(self.codebase.files)),
            "function_count": len(list(self.codebase.functions)),
            "class_count": len(list(self.codebase.classes)),
            "import_count": len(list(self.codebase.imports)),
            "symbol_count": len(list(self.codebase.symbols)),
        }

    def _capture_file_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Capture metrics for each file in the codebase."""
        file_metrics = {}

        for file in self.codebase.files:
            file_hash = hashlib.md5(file.content.encode()).hexdigest()

            file_metrics[file.filepath] = {
                "name": file.name,
                "filepath": file.filepath,
                "content_hash": file_hash,
                "line_count": len(file.content.splitlines()),
                "symbol_count": len(file.symbols),
                "function_count": len(file.functions),
                "class_count": len(file.classes),
                "import_count": len(file.imports),
            }

        return file_metrics

    def _capture_function_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Capture metrics for each function in the codebase."""
        function_metrics = {}

        for func in self.codebase.functions:
            function_metrics[func.qualified_name] = {
                "name": func.name,
                "qualified_name": func.qualified_name,
                "filepath": func.file.filepath if func.file else None,
                "line_count": len(func.source.splitlines()) if func.source else 0,
                "parameter_count": len(func.parameters),
                "return_statement_count": len(func.return_statements),
                "function_call_count": len(func.function_calls),
                "call_site_count": len(func.call_sites),
                "decorator_count": len(func.decorators),
                "dependency_count": len(func.dependencies),
                "cyclomatic_complexity": self._calculate_cyclomatic_complexity(func),
            }

        return function_metrics

    def _capture_class_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Capture metrics for each class in the codebase."""
        class_metrics = {}

        for cls in self.codebase.classes:
            class_metrics[cls.qualified_name] = {
                "name": cls.name,
                "qualified_name": cls.qualified_name,
                "filepath": cls.file.filepath if cls.file else None,
                "method_count": len(cls.methods),
                "attribute_count": len(cls.attributes),
                "parent_class_count": len(cls.parent_class_names),
                "decorator_count": len(cls.decorators),
                "dependency_count": len(cls.dependencies),
            }

        return class_metrics

    def _capture_import_metrics(self) -> Dict[str, List[str]]:
        """Capture import relationships in the codebase."""
        import_metrics = {}

        for file in self.codebase.files:
            import_metrics[file.filepath] = [
                (
                    imp.imported_symbol.qualified_name
                    if hasattr(imp.imported_symbol, "qualified_name")
                    else str(imp.imported_symbol)
                )
                for imp in file.imports
                if hasattr(imp, "imported_symbol")
            ]

        return import_metrics

    def _calculate_cyclomatic_complexity(self, func: Function) -> int:
        """
        Calculate the cyclomatic complexity of a function.

        This is a more comprehensive implementation that considers:
        - If statements
        - For loops
        - While loops
        - Try/except blocks
        - Ternary operators
        - Logical operators (and, or)
        - List/dict/set comprehensions
        - Lambda expressions

        Args:
            func: The function to analyze

        Returns:
            The cyclomatic complexity score
        """
        # Base complexity
        complexity = 1

        if not func.ast_nodes:
            return complexity

        # Count decision points in AST nodes
        for node in func.ast_nodes:
            # Control flow statements
            if node.type in [
                "if_statement",
                "for_statement",
                "while_statement",
                "try_statement",
                "catch_clause",
                "case_statement",
                "ternary_expression",
                "list_comprehension",
                "dictionary_comprehension",
                "set_comprehension",
                "lambda_expression",
            ]:
                complexity += 1

        # Count logical operators in source code
        if func.source:
            # Count logical operators that create branches
            complexity += func.source.count(" and ") + func.source.count(" or ")

            # Count ternary operators if not already counted in AST
            complexity += func.source.count(" if ") - func.source.count("if ")

            # Count exception handling if not already counted in AST
            complexity += func.source.count("except ") - func.source.count("except:")

            # Count early returns which create additional paths
            complexity += func.source.count("return ") - 1
            if complexity < 1:
                complexity = (
                    1  # Ensure at least one return is not counted as complexity
                )

        return complexity

    def serialize(self) -> Dict[str, Any]:
        """Serialize the snapshot to a dictionary."""
        return {
            "metadata": self.metadata,
            "file_metrics": self.file_metrics,
            "function_metrics": self.function_metrics,
            "class_metrics": self.class_metrics,
            "import_metrics": self.import_metrics,
        }

    @classmethod
    def deserialize(
        cls, data: Dict[str, Any], codebase: Optional[Codebase] = None
    ) -> "CodebaseSnapshot":
        """
        Create a CodebaseSnapshot from serialized data.

        Args:
            data: The serialized snapshot data
            codebase: Optional Codebase object to associate with the snapshot

        Returns:
            A new CodebaseSnapshot instance
        """
        # If no codebase is provided, create a placeholder
        if codebase is None:
            # This creates a placeholder codebase - it won't have the actual code
            # but will allow the snapshot to be loaded for comparison
            repo_path = data["metadata"]["repo_path"]
            codebase = Codebase(repo_path)

        # Create a new snapshot with the provided codebase
        snapshot = cls(
            codebase=codebase,
            commit_sha=data["metadata"]["commit_sha"],
            snapshot_id=data["metadata"]["snapshot_id"],
            timestamp=datetime.fromisoformat(data["metadata"]["timestamp"]),
        )

        # Override the captured metrics with the deserialized data
        snapshot.metadata = data["metadata"]
        snapshot.file_metrics = data["file_metrics"]
        snapshot.function_metrics = data["function_metrics"]
        snapshot.class_metrics = data["class_metrics"]
        snapshot.import_metrics = data["import_metrics"]

        return snapshot

    def save_to_file(self, filepath: str) -> None:
        """Save the snapshot to a file."""
        with open(filepath, "w") as f:
            json.dump(self.serialize(), f, indent=2)

    @classmethod
    def load_from_file(
        cls, filepath: str, codebase: Optional[Codebase] = None
    ) -> "CodebaseSnapshot":
        """Load a snapshot from a file."""
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls.deserialize(data, codebase)

    def get_file_content_hash(self, filepath: str) -> Optional[str]:
        """Get the content hash for a specific file."""
        if filepath in self.file_metrics:
            return self.file_metrics[filepath]["content_hash"]
        return None

    def get_function_complexity(self, qualified_name: str) -> Optional[int]:
        """Get the cyclomatic complexity for a specific function."""
        if qualified_name in self.function_metrics:
            return self.function_metrics[qualified_name]["cyclomatic_complexity"]
        return None

    def get_summary(self) -> str:
        """Get a summary of the snapshot."""
        return f"""
Codebase Snapshot: {self.snapshot_id}
Repository: {self.metadata['repo_path']}
Commit: {self.metadata['commit_sha']}
Timestamp: {self.metadata['timestamp']}
Files: {self.metadata['file_count']}
Functions: {self.metadata['function_count']}
Classes: {self.metadata['class_count']}
Imports: {self.metadata['import_count']}
Symbols: {self.metadata['symbol_count']}
"""


class SnapshotManager:
    """
    Manages the creation, storage, and retrieval of codebase snapshots.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize a new SnapshotManager.

        Args:
            storage_dir: Directory to store snapshots. If None, a temporary directory will be used.
        """
        self.storage_dir = storage_dir or tempfile.mkdtemp(prefix="codebase_snapshots_")
        os.makedirs(self.storage_dir, exist_ok=True)
        self.snapshots: Dict[str, CodebaseSnapshot] = {}
        self._load_existing_snapshots()

    def _load_existing_snapshots(self) -> None:
        """Load existing snapshots from the storage directory."""
        if not os.path.exists(self.storage_dir):
            return

        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.storage_dir, filename)
                try:
                    snapshot = CodebaseSnapshot.load_from_file(filepath)
                    self.snapshots[snapshot.snapshot_id] = snapshot
                except Exception as e:
                    logger.warning(f"Failed to load snapshot from {filepath}: {e}")

    def create_snapshot(
        self,
        codebase: Codebase,
        commit_sha: Optional[str] = None,
        snapshot_id: Optional[str] = None,
    ) -> CodebaseSnapshot:
        """
        Create a new snapshot of the given codebase.

        Args:
            codebase: The Codebase to snapshot
            commit_sha: The commit SHA associated with this snapshot
            snapshot_id: Optional custom ID for the snapshot

        Returns:
            The created CodebaseSnapshot
        """
        snapshot = CodebaseSnapshot(codebase, commit_sha, snapshot_id)
        self.snapshots[snapshot.snapshot_id] = snapshot

        # Save the snapshot to disk
        filepath = os.path.join(self.storage_dir, f"{snapshot.snapshot_id}.json")
        snapshot.save_to_file(filepath)

        return snapshot

    def get_snapshot(self, snapshot_id: str) -> Optional[CodebaseSnapshot]:
        """Get a snapshot by its ID."""
        return self.snapshots.get(snapshot_id)

    def get_snapshot_by_commit(self, commit_sha: str) -> Optional[CodebaseSnapshot]:
        """Get a snapshot by its associated commit SHA."""
        for snapshot in self.snapshots.values():
            if snapshot.commit_sha == commit_sha:
                return snapshot
        return None

    def list_snapshots(self) -> List[Dict[str, Any]]:
        """List all available snapshots with their metadata."""
        return [snapshot.metadata for snapshot in self.snapshots.values()]

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a snapshot by its ID."""
        if snapshot_id not in self.snapshots:
            return False

        # Remove from memory
        del self.snapshots[snapshot_id]

        # Remove from disk
        filepath = os.path.join(self.storage_dir, f"{snapshot_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)

        return True

    def create_codebase_from_repo(
        self,
        repo_url: str,
        commit_sha: Optional[str] = None,
        github_token: Optional[str] = None,
    ) -> Codebase:
        """
        Create a Codebase object from a repository URL.

        Args:
            repo_url: The repository URL or owner/repo string
            commit_sha: Optional commit SHA to checkout
            github_token: Optional GitHub token for private repositories

        Returns:
            A Codebase object
        """
        secrets = None
        if github_token:
            secrets = SecretsConfig(github_token=github_token)

        codebase = Codebase.from_repo(repo_url, secrets=secrets)

        if commit_sha:
            codebase.checkout(commit=commit_sha)

        return codebase

    def snapshot_repo(
        self,
        repo_url: str,
        commit_sha: Optional[str] = None,
        snapshot_id: Optional[str] = None,
        github_token: Optional[str] = None,
    ) -> CodebaseSnapshot:
        """
        Create a snapshot directly from a repository URL.

        Args:
            repo_url: The repository URL or owner/repo string
            commit_sha: Optional commit SHA to checkout
            snapshot_id: Optional custom ID for the snapshot
            github_token: Optional GitHub token for private repositories

        Returns:
            The created CodebaseSnapshot
        """
        codebase = self.create_codebase_from_repo(repo_url, commit_sha, github_token)
        return self.create_snapshot(codebase, commit_sha, snapshot_id)
