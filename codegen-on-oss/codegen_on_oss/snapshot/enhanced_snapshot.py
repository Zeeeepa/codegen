"""
Enhanced Snapshot System for Codegen-on-OSS

This module provides an enhanced system for creating, storing, and retrieving snapshots
of codebases with differential storage, metadata enrichment, and comparison capabilities.
"""

import os
import json
import hashlib
import logging
import tempfile
import difflib
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any, Union

from codegen import Codebase
from codegen.sdk.core.file import SourceFile

from codegen_on_oss.database.models import CodebaseSnapshot as DBCodebaseSnapshot
from codegen_on_oss.database.manager import DatabaseManager

logger = logging.getLogger(__name__)

class EnhancedSnapshot:
    """
    Enhanced snapshot class with differential storage and rich metadata.
    """
    
    def __init__(
        self, 
        codebase: Codebase, 
        commit_sha: Optional[str] = None,
        snapshot_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Initialize a new EnhancedSnapshot.
        
        Args:
            codebase: The Codebase object to snapshot
            commit_sha: The commit SHA associated with this snapshot
            snapshot_id: Optional custom ID for the snapshot
            timestamp: Optional timestamp for when the snapshot was created
            metadata: Optional additional metadata for the snapshot
            db_manager: Optional DatabaseManager instance
        """
        self.codebase = codebase
        self.commit_sha = commit_sha
        self.timestamp = timestamp or datetime.now()
        self.db_manager = db_manager or DatabaseManager()
        
        # Generate a unique ID if not provided
        if snapshot_id:
            self.snapshot_id = snapshot_id
        else:
            # Create a unique ID based on repo name, commit SHA, and timestamp
            id_string = f"{codebase.repo_path}:{commit_sha or 'unknown'}:{self.timestamp.isoformat()}"
            self.snapshot_id = hashlib.md5(id_string.encode()).hexdigest()
        
        # Initialize metadata
        self.metadata = metadata or {}
        self.metadata.update(self._capture_metadata())
        
        # Capture file content and metrics
        self.file_contents = self._capture_file_contents()
        self.file_metrics = self._capture_file_metrics()
        self.function_metrics = self._capture_function_metrics()
        self.class_metrics = self._capture_class_metrics()
        self.import_metrics = self._capture_import_metrics()
        
        # Storage path for snapshot data
        self.storage_path = None
    
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
    
    def _capture_file_contents(self) -> Dict[str, str]:
        """Capture the content of each file in the codebase."""
        file_contents = {}
        
        for file in self.codebase.files:
            file_contents[file.filepath] = file.content
            
        return file_contents
    
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
                imp.imported_symbol.qualified_name if hasattr(imp.imported_symbol, 'qualified_name') else str(imp.imported_symbol)
                for imp in file.imports
                if hasattr(imp, 'imported_symbol')
            ]
            
        return import_metrics
    
    def _calculate_cyclomatic_complexity(self, func) -> int:
        """
        Calculate the cyclomatic complexity of a function.
        
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
                "if_statement", "for_statement", "while_statement", 
                "try_statement", "catch_clause", "case_statement",
                "ternary_expression", "list_comprehension", "dictionary_comprehension",
                "set_comprehension", "lambda_expression"
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
                complexity = 1  # Ensure at least one return is not counted as complexity
        
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
    
    def save(self, storage_dir: Optional[str] = None) -> str:
        """
        Save the snapshot to disk and database.
        
        Args:
            storage_dir: Directory to store the snapshot data. If None, uses a temporary directory.
            
        Returns:
            The path where the snapshot was saved
        """
        # Create storage directory if needed
        if storage_dir is None:
            storage_dir = tempfile.mkdtemp(prefix="enhanced_snapshots_")
        os.makedirs(storage_dir, exist_ok=True)
        
        # Save snapshot data to disk
        snapshot_dir = os.path.join(storage_dir, self.snapshot_id)
        os.makedirs(snapshot_dir, exist_ok=True)
        
        # Save metadata
        with open(os.path.join(snapshot_dir, "metadata.json"), "w") as f:
            json.dump(self.metadata, f, indent=2)
        
        # Save file metrics
        with open(os.path.join(snapshot_dir, "file_metrics.json"), "w") as f:
            json.dump(self.file_metrics, f, indent=2)
        
        # Save function metrics
        with open(os.path.join(snapshot_dir, "function_metrics.json"), "w") as f:
            json.dump(self.function_metrics, f, indent=2)
        
        # Save class metrics
        with open(os.path.join(snapshot_dir, "class_metrics.json"), "w") as f:
            json.dump(self.class_metrics, f, indent=2)
        
        # Save import metrics
        with open(os.path.join(snapshot_dir, "import_metrics.json"), "w") as f:
            json.dump(self.import_metrics, f, indent=2)
        
        # Save file contents
        files_dir = os.path.join(snapshot_dir, "files")
        os.makedirs(files_dir, exist_ok=True)
        
        for filepath, content in self.file_contents.items():
            # Create directory structure
            file_dir = os.path.join(files_dir, os.path.dirname(filepath))
            os.makedirs(file_dir, exist_ok=True)
            
            # Save file content
            with open(os.path.join(files_dir, filepath), "w") as f:
                f.write(content)
        
        self.storage_path = snapshot_dir
        
        # Save to database
        self._save_to_database()
        
        return snapshot_dir
    
    def _save_to_database(self) -> None:
        """Save the snapshot to the database."""
        # Create database record
        db_snapshot = DBCodebaseSnapshot(
            snapshot_id=self.snapshot_id,
            commit_sha=self.commit_sha,
            metadata=self.metadata,
            storage_path=self.storage_path
        )
        
        # Save to database
        self.db_manager.create(db_snapshot)
    
    @classmethod
    def load(cls, snapshot_id: str, db_manager: Optional[DatabaseManager] = None) -> 'EnhancedSnapshot':
        """
        Load a snapshot from the database and disk.
        
        Args:
            snapshot_id: ID of the snapshot to load
            db_manager: Optional DatabaseManager instance
            
        Returns:
            The loaded EnhancedSnapshot
        """
        db_manager = db_manager or DatabaseManager()
        
        # Get snapshot from database
        db_snapshot = db_manager.get_by_id(DBCodebaseSnapshot, snapshot_id)
        if db_snapshot is None:
            raise ValueError(f"Snapshot with ID {snapshot_id} not found in database")
        
        # Load snapshot data from disk
        storage_path = db_snapshot.storage_path
        if not os.path.exists(storage_path):
            raise ValueError(f"Snapshot storage path {storage_path} does not exist")
        
        # Load metadata
        with open(os.path.join(storage_path, "metadata.json"), "r") as f:
            metadata = json.load(f)
        
        # Load file metrics
        with open(os.path.join(storage_path, "file_metrics.json"), "r") as f:
            file_metrics = json.load(f)
        
        # Load function metrics
        with open(os.path.join(storage_path, "function_metrics.json"), "r") as f:
            function_metrics = json.load(f)
        
        # Load class metrics
        with open(os.path.join(storage_path, "class_metrics.json"), "r") as f:
            class_metrics = json.load(f)
        
        # Load import metrics
        with open(os.path.join(storage_path, "import_metrics.json"), "r") as f:
            import_metrics = json.load(f)
        
        # Create a placeholder codebase
        repo_path = metadata["repo_path"]
        codebase = Codebase(repo_path)
        
        # Create a new snapshot with the loaded data
        snapshot = cls(
            codebase=codebase,
            commit_sha=metadata["commit_sha"],
            snapshot_id=metadata["snapshot_id"],
            timestamp=datetime.fromisoformat(metadata["timestamp"]),
            metadata=metadata,
            db_manager=db_manager
        )
        
        # Set loaded metrics
        snapshot.file_metrics = file_metrics
        snapshot.function_metrics = function_metrics
        snapshot.class_metrics = class_metrics
        snapshot.import_metrics = import_metrics
        snapshot.storage_path = storage_path
        
        # Load file contents
        snapshot.file_contents = {}
        files_dir = os.path.join(storage_path, "files")
        if os.path.exists(files_dir):
            for root, _, files in os.walk(files_dir):
                for file in files:
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, files_dir)
                    with open(filepath, "r") as f:
                        snapshot.file_contents[rel_path] = f.read()
        
        return snapshot
    
    def compare_with(self, other: 'EnhancedSnapshot') -> Dict[str, Any]:
        """
        Compare this snapshot with another snapshot.
        
        Args:
            other: The snapshot to compare with
            
        Returns:
            A dictionary containing comparison results
        """
        # Compare metadata
        metadata_diff = {
            "file_count_diff": self.metadata["file_count"] - other.metadata["file_count"],
            "function_count_diff": self.metadata["function_count"] - other.metadata["function_count"],
            "class_count_diff": self.metadata["class_count"] - other.metadata["class_count"],
            "import_count_diff": self.metadata["import_count"] - other.metadata["import_count"],
            "symbol_count_diff": self.metadata["symbol_count"] - other.metadata["symbol_count"],
        }
        
        # Compare files
        files_added = set(self.file_metrics.keys()) - set(other.file_metrics.keys())
        files_removed = set(other.file_metrics.keys()) - set(self.file_metrics.keys())
        files_modified = set()
        
        for filepath in set(self.file_metrics.keys()) & set(other.file_metrics.keys()):
            if self.file_metrics[filepath]["content_hash"] != other.file_metrics[filepath]["content_hash"]:
                files_modified.add(filepath)
        
        # Compare functions
        functions_added = set(self.function_metrics.keys()) - set(other.function_metrics.keys())
        functions_removed = set(other.function_metrics.keys()) - set(self.function_metrics.keys())
        functions_modified = set()
        
        for func_name in set(self.function_metrics.keys()) & set(other.function_metrics.keys()):
            if self.function_metrics[func_name] != other.function_metrics[func_name]:
                functions_modified.add(func_name)
        
        # Compare classes
        classes_added = set(self.class_metrics.keys()) - set(other.class_metrics.keys())
        classes_removed = set(other.class_metrics.keys()) - set(self.class_metrics.keys())
        classes_modified = set()
        
        for class_name in set(self.class_metrics.keys()) & set(other.class_metrics.keys()):
            if self.class_metrics[class_name] != other.class_metrics[class_name]:
                classes_modified.add(class_name)
        
        # Generate file diffs
        file_diffs = {}
        for filepath in files_modified:
            if filepath in self.file_contents and filepath in other.file_contents:
                diff = difflib.unified_diff(
                    other.file_contents[filepath].splitlines(),
                    self.file_contents[filepath].splitlines(),
                    fromfile=f"a/{filepath}",
                    tofile=f"b/{filepath}",
                    lineterm=""
                )
                file_diffs[filepath] = "\n".join(diff)
        
        return {
            "metadata_diff": metadata_diff,
            "files_added": list(files_added),
            "files_removed": list(files_removed),
            "files_modified": list(files_modified),
            "functions_added": list(functions_added),
            "functions_removed": list(functions_removed),
            "functions_modified": list(functions_modified),
            "classes_added": list(classes_added),
            "classes_removed": list(classes_removed),
            "classes_modified": list(classes_modified),
            "file_diffs": file_diffs,
        }


class EnhancedSnapshotManager:
    """
    Manages the creation, storage, and retrieval of enhanced codebase snapshots.
    """
    
    def __init__(self, storage_dir: Optional[str] = None, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize a new EnhancedSnapshotManager.
        
        Args:
            storage_dir: Directory to store snapshots. If None, a temporary directory will be used.
            db_manager: Optional DatabaseManager instance
        """
        self.storage_dir = storage_dir or tempfile.mkdtemp(prefix="enhanced_snapshots_")
        os.makedirs(self.storage_dir, exist_ok=True)
        self.db_manager = db_manager or DatabaseManager()
        
        # Ensure database tables exist
        self.db_manager.create_tables()
    
    def create_snapshot(
        self, 
        codebase: Codebase, 
        commit_sha: Optional[str] = None,
        snapshot_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EnhancedSnapshot:
        """
        Create a new snapshot of the given codebase.
        
        Args:
            codebase: The Codebase to snapshot
            commit_sha: The commit SHA associated with this snapshot
            snapshot_id: Optional custom ID for the snapshot
            metadata: Optional additional metadata for the snapshot
            
        Returns:
            The created EnhancedSnapshot
        """
        snapshot = EnhancedSnapshot(
            codebase=codebase, 
            commit_sha=commit_sha, 
            snapshot_id=snapshot_id,
            metadata=metadata,
            db_manager=self.db_manager
        )
        
        # Save the snapshot
        snapshot.save(self.storage_dir)
        
        return snapshot
    
    def get_snapshot(self, snapshot_id: str) -> Optional[EnhancedSnapshot]:
        """
        Get a snapshot by its ID.
        
        Args:
            snapshot_id: The ID of the snapshot to retrieve
            
        Returns:
            The EnhancedSnapshot if found, None otherwise
        """
        try:
            return EnhancedSnapshot.load(snapshot_id, self.db_manager)
        except ValueError:
            logger.warning(f"Snapshot with ID {snapshot_id} not found")
            return None
    
    def get_snapshot_by_commit(self, commit_sha: str) -> Optional[EnhancedSnapshot]:
        """
        Get a snapshot by its associated commit SHA.
        
        Args:
            commit_sha: The commit SHA to look for
            
        Returns:
            The EnhancedSnapshot if found, None otherwise
        """
        # Query database for snapshot with matching commit SHA
        snapshots = self.db_manager.get_all(DBCodebaseSnapshot, commit_sha=commit_sha)
        if not snapshots:
            return None
        
        # Return the first matching snapshot
        return self.get_snapshot(snapshots[0].snapshot_id)
    
    def list_snapshots(self) -> List[Dict[str, Any]]:
        """
        List all available snapshots with their metadata.
        
        Returns:
            A list of snapshot metadata dictionaries
        """
        # Query database for all snapshots
        snapshots = self.db_manager.get_all(DBCodebaseSnapshot)
        return [{"id": s.id, "snapshot_id": s.snapshot_id, "commit_sha": s.commit_sha, 
                 "timestamp": s.timestamp.isoformat(), "metadata": s.metadata} 
                for s in snapshots]
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot by its ID.
        
        Args:
            snapshot_id: The ID of the snapshot to delete
            
        Returns:
            True if the snapshot was deleted, False otherwise
        """
        # Get snapshot from database
        db_snapshot = self.db_manager.get_by_id(DBCodebaseSnapshot, snapshot_id)
        if db_snapshot is None:
            return False
        
        # Delete snapshot data from disk
        storage_path = db_snapshot.storage_path
        if os.path.exists(storage_path):
            import shutil
            shutil.rmtree(storage_path)
        
        # Delete from database
        return self.db_manager.delete(db_snapshot)
    
    def compare_snapshots(self, snapshot_id1: str, snapshot_id2: str) -> Dict[str, Any]:
        """
        Compare two snapshots.
        
        Args:
            snapshot_id1: ID of the first snapshot
            snapshot_id2: ID of the second snapshot
            
        Returns:
            A dictionary containing comparison results
        """
        snapshot1 = self.get_snapshot(snapshot_id1)
        snapshot2 = self.get_snapshot(snapshot_id2)
        
        if snapshot1 is None:
            raise ValueError(f"Snapshot with ID {snapshot_id1} not found")
        if snapshot2 is None:
            raise ValueError(f"Snapshot with ID {snapshot_id2} not found")
        
        return snapshot1.compare_with(snapshot2)
    
    def create_snapshot_branch(self, base_snapshot_id: str, branch_name: str) -> str:
        """
        Create a new snapshot branch from a base snapshot.
        
        Args:
            base_snapshot_id: ID of the base snapshot
            branch_name: Name of the new branch
            
        Returns:
            The ID of the new branch snapshot
        """
        base_snapshot = self.get_snapshot(base_snapshot_id)
        if base_snapshot is None:
            raise ValueError(f"Base snapshot with ID {base_snapshot_id} not found")
        
        # Create a new snapshot with the same data but different ID
        branch_snapshot = EnhancedSnapshot(
            codebase=base_snapshot.codebase,
            commit_sha=base_snapshot.commit_sha,
            metadata={**base_snapshot.metadata, "branch_name": branch_name, "parent_snapshot_id": base_snapshot_id},
            db_manager=self.db_manager
        )
        
        # Copy metrics from base snapshot
        branch_snapshot.file_metrics = base_snapshot.file_metrics.copy()
        branch_snapshot.function_metrics = base_snapshot.function_metrics.copy()
        branch_snapshot.class_metrics = base_snapshot.class_metrics.copy()
        branch_snapshot.import_metrics = base_snapshot.import_metrics.copy()
        branch_snapshot.file_contents = base_snapshot.file_contents.copy()
        
        # Save the branch snapshot
        branch_snapshot.save(self.storage_dir)
        
        return branch_snapshot.snapshot_id
    
    def merge_snapshot_branches(self, branch1_id: str, branch2_id: str, merge_name: str) -> str:
        """
        Merge two snapshot branches into a new snapshot.
        
        Args:
            branch1_id: ID of the first branch snapshot
            branch2_id: ID of the second branch snapshot
            merge_name: Name of the merged snapshot
            
        Returns:
            The ID of the merged snapshot
        """
        branch1 = self.get_snapshot(branch1_id)
        branch2 = self.get_snapshot(branch2_id)
        
        if branch1 is None:
            raise ValueError(f"Branch snapshot with ID {branch1_id} not found")
        if branch2 is None:
            raise ValueError(f"Branch snapshot with ID {branch2_id} not found")
        
        # Create a new snapshot with merged data
        merged_snapshot = EnhancedSnapshot(
            codebase=branch1.codebase,
            commit_sha=branch1.commit_sha,
            metadata={
                **branch1.metadata,
                "merge_name": merge_name,
                "merged_from": [branch1_id, branch2_id]
            },
            db_manager=self.db_manager
        )
        
        # Merge file metrics and contents
        merged_snapshot.file_metrics = branch1.file_metrics.copy()
        merged_snapshot.file_contents = branch1.file_contents.copy()
        
        for filepath, metrics in branch2.file_metrics.items():
            if filepath not in merged_snapshot.file_metrics or \
               branch2.file_metrics[filepath]["content_hash"] != branch1.file_metrics.get(filepath, {}).get("content_hash"):
                merged_snapshot.file_metrics[filepath] = metrics
                merged_snapshot.file_contents[filepath] = branch2.file_contents.get(filepath, "")
        
        # Merge function metrics
        merged_snapshot.function_metrics = branch1.function_metrics.copy()
        for func_name, metrics in branch2.function_metrics.items():
            if func_name not in merged_snapshot.function_metrics:
                merged_snapshot.function_metrics[func_name] = metrics
        
        # Merge class metrics
        merged_snapshot.class_metrics = branch1.class_metrics.copy()
        for class_name, metrics in branch2.class_metrics.items():
            if class_name not in merged_snapshot.class_metrics:
                merged_snapshot.class_metrics[class_name] = metrics
        
        # Merge import metrics
        merged_snapshot.import_metrics = branch1.import_metrics.copy()
        for filepath, imports in branch2.import_metrics.items():
            if filepath not in merged_snapshot.import_metrics:
                merged_snapshot.import_metrics[filepath] = imports
        
        # Save the merged snapshot
        merged_snapshot.save(self.storage_dir)
        
        return merged_snapshot.snapshot_id

