"""
Enhanced Codebase Snapshot Module

This module extends the basic CodebaseSnapshot with more capabilities,
including incremental snapshots, enhanced comparison, and better metadata.
"""

import os
import json
import hashlib
import logging
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any, Union

from codegen import Codebase
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.symbol import Symbol

from .codebase_snapshot import CodebaseSnapshot

logger = logging.getLogger(__name__)


class EnhancedCodebaseSnapshot(CodebaseSnapshot):
    """
    Enhanced version of CodebaseSnapshot with additional capabilities.
    """
    
    def __init__(
        self, 
        codebase: Codebase, 
        commit_sha: Optional[str] = None,
        snapshot_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        parent_snapshot_id: Optional[str] = None,
        is_incremental: bool = False
    ):
        """
        Initialize a new EnhancedCodebaseSnapshot.
        
        Args:
            codebase: The Codebase object to snapshot
            commit_sha: The commit SHA associated with this snapshot
            snapshot_id: Optional custom ID for the snapshot
            timestamp: Optional timestamp for when the snapshot was created
            parent_snapshot_id: Optional ID of the parent snapshot
            is_incremental: Whether this is an incremental snapshot
        """
        super().__init__(codebase, commit_sha, snapshot_id, timestamp)
        
        self.parent_snapshot_id = parent_snapshot_id
        self.is_incremental = is_incremental
        
        # Enhanced metadata
        self.enhanced_metadata = self._capture_enhanced_metadata()
        self.security_metrics = self._capture_security_metrics()
        self.test_coverage = self._capture_test_coverage()
        self.dependency_graph = self._capture_dependency_graph()
    
    def _capture_enhanced_metadata(self) -> Dict[str, Any]:
        """Capture enhanced metadata about the codebase."""
        # Get language distribution
        language_counts = {}
        for file in self.codebase.files:
            ext = os.path.splitext(file.filepath)[1].lstrip('.')
            if ext:
                language_counts[ext] = language_counts.get(ext, 0) + 1
        
        # Get directory structure
        directories = set()
        for file in self.codebase.files:
            directory = os.path.dirname(file.filepath)
            if directory:
                directories.add(directory)
        
        return {
            "language_distribution": language_counts,
            "directory_count": len(directories),
            "average_file_size": sum(len(file.content) for file in self.codebase.files) / max(1, len(list(self.codebase.files))),
            "largest_file": max((len(file.content), file.filepath) for file in self.codebase.files)[1] if list(self.codebase.files) else None,
            "average_function_complexity": sum(self._calculate_cyclomatic_complexity(func) for func in self.codebase.functions) / max(1, len(list(self.codebase.functions))),
        }
    
    def _capture_security_metrics(self) -> Dict[str, Any]:
        """Capture security-related metrics."""
        # This would be implemented with actual security analysis
        # For now, we'll return a placeholder
        return {
            "potential_vulnerabilities": 0,
            "security_hotspots": 0,
            "sensitive_data_patterns": 0,
        }
    
    def _capture_test_coverage(self) -> Dict[str, Any]:
        """Capture test coverage metrics."""
        # This would be implemented with actual test coverage analysis
        # For now, we'll return a placeholder
        return {
            "overall_coverage": 0.0,
            "covered_lines": 0,
            "total_lines": sum(len(file.content.splitlines()) for file in self.codebase.files),
            "covered_functions": 0,
            "total_functions": len(list(self.codebase.functions)),
        }
    
    def _capture_dependency_graph(self) -> Dict[str, List[str]]:
        """Capture the dependency graph of the codebase."""
        dependency_graph = {}
        
        for file in self.codebase.files:
            dependencies = set()
            
            # Add imported files as dependencies
            for imp in file.imports:
                if hasattr(imp, 'imported_symbol') and hasattr(imp.imported_symbol, 'file'):
                    imported_file = imp.imported_symbol.file
                    if imported_file and imported_file.filepath != file.filepath:
                        dependencies.add(imported_file.filepath)
            
            dependency_graph[file.filepath] = list(dependencies)
        
        return dependency_graph
    
    def compare_with(self, other_snapshot: 'EnhancedCodebaseSnapshot', detail_level: str = 'summary') -> Dict[str, Any]:
        """
        Compare this snapshot with another one at different detail levels.
        
        Args:
            other_snapshot: The snapshot to compare with
            detail_level: Level of detail for the comparison ('summary', 'detailed', 'full')
            
        Returns:
            A dictionary with comparison results
        """
        # Basic comparison data
        comparison = {
            "snapshot1": {
                "id": self.snapshot_id,
                "commit_sha": self.commit_sha,
                "timestamp": self.timestamp.isoformat(),
            },
            "snapshot2": {
                "id": other_snapshot.snapshot_id,
                "commit_sha": other_snapshot.commit_sha,
                "timestamp": other_snapshot.timestamp.isoformat(),
            },
            "detail_level": detail_level,
        }
        
        # Compare files
        files1 = {filepath: metrics for filepath, metrics in self.file_metrics.items()}
        files2 = {filepath: metrics for filepath, metrics in other_snapshot.file_metrics.items()}
        
        added_files = [filepath for filepath in files2 if filepath not in files1]
        removed_files = [filepath for filepath in files1 if filepath not in files2]
        modified_files = []
        
        for filepath in files1:
            if filepath in files2 and files1[filepath]["content_hash"] != files2[filepath]["content_hash"]:
                modified_files.append(filepath)
        
        comparison["files"] = {
            "added": added_files,
            "removed": removed_files,
            "modified": modified_files,
            "unchanged": [filepath for filepath in files1 if filepath in files2 and files1[filepath]["content_hash"] == files2[filepath]["content_hash"]],
            "total_added": len(added_files),
            "total_removed": len(removed_files),
            "total_modified": len(modified_files),
            "total_unchanged": len([filepath for filepath in files1 if filepath in files2 and files1[filepath]["content_hash"] == files2[filepath]["content_hash"]]),
        }
        
        # Compare functions
        if detail_level in ['detailed', 'full']:
            functions1 = {name: metrics for name, metrics in self.function_metrics.items()}
            functions2 = {name: metrics for name, metrics in other_snapshot.function_metrics.items()}
            
            added_functions = [name for name in functions2 if name not in functions1]
            removed_functions = [name for name in functions1 if name not in functions2]
            modified_functions = []
            
            for name in functions1:
                if name in functions2:
                    # Check if function source has changed
                    if functions1[name]["line_count"] != functions2[name]["line_count"] or \
                       functions1[name]["parameter_count"] != functions2[name]["parameter_count"] or \
                       functions1[name]["return_statement_count"] != functions2[name]["return_statement_count"]:
                        modified_functions.append(name)
            
            comparison["functions"] = {
                "added": added_functions,
                "removed": removed_functions,
                "modified": modified_functions,
                "total_added": len(added_functions),
                "total_removed": len(removed_functions),
                "total_modified": len(modified_functions),
            }
            
            # Compare classes
            classes1 = {name: metrics for name, metrics in self.class_metrics.items()}
            classes2 = {name: metrics for name, metrics in other_snapshot.class_metrics.items()}
            
            added_classes = [name for name in classes2 if name not in classes1]
            removed_classes = [name for name in classes1 if name not in classes2]
            modified_classes = []
            
            for name in classes1:
                if name in classes2:
                    # Check if class has changed
                    if classes1[name]["method_count"] != classes2[name]["method_count"] or \
                       classes1[name]["attribute_count"] != classes2[name]["attribute_count"]:
                        modified_classes.append(name)
            
            comparison["classes"] = {
                "added": added_classes,
                "removed": removed_classes,
                "modified": modified_classes,
                "total_added": len(added_classes),
                "total_removed": len(removed_classes),
                "total_modified": len(modified_classes),
            }
        
        # Full comparison includes all metrics
        if detail_level == 'full':
            # Compare complexity metrics
            complexity_changes = {}
            for name in functions1:
                if name in functions2:
                    complexity1 = functions1[name]["cyclomatic_complexity"]
                    complexity2 = functions2[name]["cyclomatic_complexity"]
                    if complexity1 != complexity2:
                        complexity_changes[name] = {
                            "before": complexity1,
                            "after": complexity2,
                            "change": complexity2 - complexity1,
                        }
            
            comparison["complexity_changes"] = complexity_changes
            
            # Compare dependency graph
            dependency_changes = {}
            for filepath in self.dependency_graph:
                if filepath in other_snapshot.dependency_graph:
                    deps1 = set(self.dependency_graph[filepath])
                    deps2 = set(other_snapshot.dependency_graph[filepath])
                    
                    added_deps = deps2 - deps1
                    removed_deps = deps1 - deps2
                    
                    if added_deps or removed_deps:
                        dependency_changes[filepath] = {
                            "added_dependencies": list(added_deps),
                            "removed_dependencies": list(removed_deps),
                        }
            
            comparison["dependency_changes"] = dependency_changes
        
        return comparison
    
    def export_for_visualization(self, format: str = 'json') -> Dict[str, Any]:
        """
        Export snapshot data in a format suitable for frontend visualization.
        
        Args:
            format: Output format ('json', 'graph', 'tree')
            
        Returns:
            Data in the specified format
        """
        if format == 'json':
            return self._export_json()
        elif format == 'graph':
            return self._export_graph()
        elif format == 'tree':
            return self._export_tree()
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_json(self) -> Dict[str, Any]:
        """Export snapshot data as a JSON-compatible dictionary."""
        return {
            "metadata": self.metadata,
            "enhanced_metadata": self.enhanced_metadata,
            "files": {
                filepath: {
                    "name": metrics["name"],
                    "line_count": metrics["line_count"],
                    "function_count": metrics["function_count"],
                    "class_count": metrics["class_count"],
                    "import_count": metrics["import_count"],
                }
                for filepath, metrics in self.file_metrics.items()
            },
            "functions": {
                name: {
                    "name": metrics["name"],
                    "filepath": metrics["filepath"],
                    "line_count": metrics["line_count"],
                    "parameter_count": metrics["parameter_count"],
                    "cyclomatic_complexity": metrics["cyclomatic_complexity"],
                }
                for name, metrics in self.function_metrics.items()
            },
            "classes": {
                name: {
                    "name": metrics["name"],
                    "filepath": metrics["filepath"],
                    "method_count": metrics["method_count"],
                    "attribute_count": metrics["attribute_count"],
                }
                for name, metrics in self.class_metrics.items()
            },
            "security": self.security_metrics,
            "test_coverage": self.test_coverage,
        }
    
    def _export_graph(self) -> Dict[str, Any]:
        """Export snapshot data as a graph structure for visualization."""
        nodes = []
        edges = []
        
        # Add file nodes
        for filepath, metrics in self.file_metrics.items():
            nodes.append({
                "id": filepath,
                "label": metrics["name"],
                "type": "file",
                "metrics": {
                    "line_count": metrics["line_count"],
                    "function_count": metrics["function_count"],
                    "class_count": metrics["class_count"],
                    "import_count": metrics["import_count"],
                }
            })
        
        # Add dependency edges
        for source, targets in self.dependency_graph.items():
            for target in targets:
                edges.append({
                    "source": source,
                    "target": target,
                    "type": "imports",
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": self.metadata,
        }
    
    def _export_tree(self) -> Dict[str, Any]:
        """Export snapshot data as a tree structure for visualization."""
        # Create a directory tree
        tree = {}
        
        for filepath in self.file_metrics:
            parts = filepath.split('/')
            current = tree
            
            # Build the tree structure
            for i, part in enumerate(parts):
                if i == len(parts) - 1:  # Leaf node (file)
                    current[part] = {
                        "type": "file",
                        "metrics": self.file_metrics[filepath],
                    }
                else:  # Directory
                    if part not in current:
                        current[part] = {
                            "type": "directory",
                            "children": {},
                        }
                    current = current[part]["children"]
        
        return {
            "tree": tree,
            "metadata": self.metadata,
        }
    
    def create_incremental_snapshot(self, new_codebase: Codebase, new_commit_sha: Optional[str] = None) -> 'EnhancedCodebaseSnapshot':
        """
        Create an incremental snapshot based on this snapshot and a new codebase.
        
        Args:
            new_codebase: The new Codebase to create an incremental snapshot from
            new_commit_sha: Optional commit SHA for the new snapshot
            
        Returns:
            A new EnhancedCodebaseSnapshot that only contains the changes
        """
        # Create a full snapshot of the new codebase
        new_snapshot = EnhancedCodebaseSnapshot(
            codebase=new_codebase,
            commit_sha=new_commit_sha,
            parent_snapshot_id=self.snapshot_id,
            is_incremental=True,
        )
        
        # Identify changed files
        changed_files = set()
        
        # Check for added, removed, or modified files
        files1 = {filepath: metrics for filepath, metrics in self.file_metrics.items()}
        files2 = {filepath: metrics for filepath, metrics in new_snapshot.file_metrics.items()}
        
        for filepath in files2:
            if filepath not in files1 or files1[filepath]["content_hash"] != files2[filepath]["content_hash"]:
                changed_files.add(filepath)
        
        # Filter metrics to only include changed files
        new_snapshot.file_metrics = {
            filepath: metrics
            for filepath, metrics in new_snapshot.file_metrics.items()
            if filepath in changed_files
        }
        
        # Filter function metrics to only include functions in changed files
        new_snapshot.function_metrics = {
            name: metrics
            for name, metrics in new_snapshot.function_metrics.items()
            if metrics["filepath"] in changed_files
        }
        
        # Filter class metrics to only include classes in changed files
        new_snapshot.class_metrics = {
            name: metrics
            for name, metrics in new_snapshot.class_metrics.items()
            if metrics["filepath"] in changed_files
        }
        
        # Update metadata to reflect that this is an incremental snapshot
        new_snapshot.metadata["is_incremental"] = True
        new_snapshot.metadata["parent_snapshot_id"] = self.snapshot_id
        new_snapshot.metadata["changed_file_count"] = len(changed_files)
        
        return new_snapshot


class EnhancedSnapshotManager:
    """
    Enhanced manager for creating, storing, and retrieving codebase snapshots.
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize a new EnhancedSnapshotManager.
        
        Args:
            storage_dir: Directory to store snapshots. If None, a temporary directory will be used.
        """
        self.storage_dir = storage_dir or tempfile.mkdtemp(prefix="enhanced_codebase_snapshots_")
        os.makedirs(self.storage_dir, exist_ok=True)
        self.snapshots: Dict[str, EnhancedCodebaseSnapshot] = {}
        self._load_existing_snapshots()
    
    def _load_existing_snapshots(self) -> None:
        """Load existing snapshots from the storage directory."""
        if not os.path.exists(self.storage_dir):
            return
        
        for filename in os.listdir(self.storage_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.storage_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    # Check if this is an enhanced snapshot
                    if "enhanced_metadata" in data:
                        # We would need to reconstruct the codebase to fully deserialize
                        # For now, just store the metadata
                        snapshot_id = data["metadata"]["snapshot_id"]
                        self.snapshots[snapshot_id] = data
                except Exception as e:
                    logger.warning(f"Failed to load snapshot from {filepath}: {e}")
    
    def create_snapshot(
        self, 
        codebase: Codebase, 
        commit_sha: Optional[str] = None,
        snapshot_id: Optional[str] = None,
        parent_snapshot_id: Optional[str] = None,
        is_incremental: bool = False
    ) -> EnhancedCodebaseSnapshot:
        """
        Create a new enhanced snapshot of the given codebase.
        
        Args:
            codebase: The Codebase to snapshot
            commit_sha: The commit SHA associated with this snapshot
            snapshot_id: Optional custom ID for the snapshot
            parent_snapshot_id: Optional ID of the parent snapshot
            is_incremental: Whether this is an incremental snapshot
            
        Returns:
            The created EnhancedCodebaseSnapshot
        """
        snapshot = EnhancedCodebaseSnapshot(
            codebase=codebase,
            commit_sha=commit_sha,
            snapshot_id=snapshot_id,
            parent_snapshot_id=parent_snapshot_id,
            is_incremental=is_incremental
        )
        self.snapshots[snapshot.snapshot_id] = snapshot
        
        # Save the snapshot to disk
        filepath = os.path.join(self.storage_dir, f"{snapshot.snapshot_id}.json")
        with open(filepath, 'w') as f:
            json.dump(snapshot.serialize(), f, indent=2)
        
        return snapshot
    
    def create_incremental_snapshot(
        self,
        base_snapshot_id: str,
        codebase: Codebase,
        commit_sha: Optional[str] = None,
        snapshot_id: Optional[str] = None
    ) -> EnhancedCodebaseSnapshot:
        """
        Create an incremental snapshot based on a previous snapshot.
        
        Args:
            base_snapshot_id: ID of the base snapshot
            codebase: The new Codebase to create an incremental snapshot from
            commit_sha: Optional commit SHA for the new snapshot
            snapshot_id: Optional custom ID for the snapshot
            
        Returns:
            A new EnhancedCodebaseSnapshot that only contains the changes
        """
        base_snapshot = self.get_snapshot(base_snapshot_id)
        if not base_snapshot:
            raise ValueError(f"Base snapshot with ID {base_snapshot_id} not found")
        
        incremental_snapshot = base_snapshot.create_incremental_snapshot(
            new_codebase=codebase,
            new_commit_sha=commit_sha
        )
        
        if snapshot_id:
            incremental_snapshot.snapshot_id = snapshot_id
        
        self.snapshots[incremental_snapshot.snapshot_id] = incremental_snapshot
        
        # Save the snapshot to disk
        filepath = os.path.join(self.storage_dir, f"{incremental_snapshot.snapshot_id}.json")
        with open(filepath, 'w') as f:
            json.dump(incremental_snapshot.serialize(), f, indent=2)
        
        return incremental_snapshot
    
    def get_snapshot(self, snapshot_id: str) -> Optional[EnhancedCodebaseSnapshot]:
        """Get a snapshot by its ID."""
        return self.snapshots.get(snapshot_id)
    
    def compare_snapshots(
        self,
        snapshot_id_1: str,
        snapshot_id_2: str,
        detail_level: str = 'summary'
    ) -> Dict[str, Any]:
        """
        Compare two snapshots and return the differences.
        
        Args:
            snapshot_id_1: ID of the first snapshot
            snapshot_id_2: ID of the second snapshot
            detail_level: Level of detail for the comparison ('summary', 'detailed', 'full')
            
        Returns:
            A dictionary with comparison results
        """
        snapshot1 = self.get_snapshot(snapshot_id_1)
        snapshot2 = self.get_snapshot(snapshot_id_2)
        
        if not snapshot1 or not snapshot2:
            raise ValueError("One or both snapshots not found")
        
        return snapshot1.compare_with(snapshot2, detail_level=detail_level)
    
    def export_for_visualization(
        self,
        snapshot_id: str,
        format: str = 'json'
    ) -> Dict[str, Any]:
        """
        Export snapshot data in a format suitable for frontend visualization.
        
        Args:
            snapshot_id: ID of the snapshot to export
            format: Output format ('json', 'graph', 'tree')
            
        Returns:
            Data in the specified format
        """
        snapshot = self.get_snapshot(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot with ID {snapshot_id} not found")
        
        return snapshot.export_for_visualization(format=format)

