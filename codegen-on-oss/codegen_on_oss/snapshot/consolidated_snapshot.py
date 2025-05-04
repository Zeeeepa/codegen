"""
Consolidated Snapshot Module

This module provides a unified interface for codebase snapshot functionality,
including snapshot creation, management, PR review, and PR tasks.
"""

import hashlib
import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from codegen import Codebase
from codegen.configs.models.secrets import SecretsConfig
from codegen.sdk.core.function import Function

# Import from existing modules
from codegen_on_oss.analysis.consolidated_analyzer import CodeAnalyzer

logger = logging.getLogger(__name__)


class CodebaseSnapshot:
    """
    Class for creating, storing, and retrieving snapshots of codebases.
    """
    
    def __init__(
        self,
        codebase: Optional[Codebase] = None,
        repo_path: Optional[str] = None,
        snapshot_dir: Optional[str] = None,
    ):
        """
        Initialize the codebase snapshot.
        
        Args:
            codebase: A Codebase object to snapshot
            repo_path: Path to the repository to snapshot
            snapshot_dir: Directory to store snapshots in
        """
        self.codebase = codebase
        self.repo_path = repo_path
        self.snapshot_dir = snapshot_dir or os.path.join(os.getcwd(), "snapshots")
        
        if not os.path.exists(self.snapshot_dir):
            os.makedirs(self.snapshot_dir)
        
        if self.codebase is None and self.repo_path:
            self.codebase = Codebase.from_directory(self.repo_path)
    
    def create_snapshot(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a snapshot of the codebase.
        
        Args:
            name: Optional name for the snapshot
            
        Returns:
            A dictionary containing snapshot metadata
        """
        if not self.codebase:
            return {"error": "No codebase loaded"}
        
        # Generate a snapshot ID
        timestamp = datetime.now().isoformat()
        snapshot_id = hashlib.md5(f"{timestamp}_{name or ''}".encode()).hexdigest()
        
        # Create snapshot metadata
        metadata = {
            "id": snapshot_id,
            "name": name or f"snapshot_{timestamp}",
            "timestamp": timestamp,
            "files": len(self.codebase.files),
            "functions": len(list(self.codebase.functions)),
            "classes": len(list(self.codebase.classes)),
        }
        
        # Create file metrics
        file_metrics = {}
        for file in self.codebase.files:
            file_metrics[file.file_path] = {
                "functions": len(list(file.functions)),
                "classes": len(list(file.classes)),
                "imports": len(list(file.imports)),
                "lines": len(file.source.splitlines()),
            }
        
        # Create function metrics
        function_metrics = {}
        for func in self.codebase.functions:
            function_metrics[func.name] = {
                "file": func.file.file_path if hasattr(func, "file") else "Unknown",
                "parameters": len(func.parameters),
                "lines": len(func.source.splitlines()),
            }
        
        # Create class metrics
        class_metrics = {}
        for cls in self.codebase.classes:
            class_metrics[cls.name] = {
                "file": cls.file.file_path if hasattr(cls, "file") else "Unknown",
                "methods": len(list(cls.methods)),
                "attributes": len(list(cls.attributes)),
            }
        
        # Create the snapshot data
        snapshot_data = {
            "metadata": metadata,
            "file_metrics": file_metrics,
            "function_metrics": function_metrics,
            "class_metrics": class_metrics,
        }
        
        # Save the snapshot
        snapshot_path = os.path.join(self.snapshot_dir, f"{snapshot_id}.json")
        with open(snapshot_path, "w") as f:
            json.dump(snapshot_data, f, indent=2)
        
        return metadata
    
    def get_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Get a snapshot by ID.
        
        Args:
            snapshot_id: ID of the snapshot to retrieve
            
        Returns:
            The snapshot data
        """
        snapshot_path = os.path.join(self.snapshot_dir, f"{snapshot_id}.json")
        
        if not os.path.exists(snapshot_path):
            return {"error": f"Snapshot not found: {snapshot_id}"}
        
        with open(snapshot_path, "r") as f:
            snapshot_data = json.load(f)
        
        return snapshot_data
    
    def list_snapshots(self) -> List[Dict[str, Any]]:
        """
        List all available snapshots.
        
        Returns:
            A list of snapshot metadata
        """
        snapshots = []
        
        for filename in os.listdir(self.snapshot_dir):
            if filename.endswith(".json"):
                snapshot_path = os.path.join(self.snapshot_dir, filename)
                
                with open(snapshot_path, "r") as f:
                    snapshot_data = json.load(f)
                
                snapshots.append(snapshot_data["metadata"])
        
        return snapshots
    
    def delete_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Delete a snapshot by ID.
        
        Args:
            snapshot_id: ID of the snapshot to delete
            
        Returns:
            A status message
        """
        snapshot_path = os.path.join(self.snapshot_dir, f"{snapshot_id}.json")
        
        if not os.path.exists(snapshot_path):
            return {"error": f"Snapshot not found: {snapshot_id}"}
        
        os.remove(snapshot_path)
        
        return {"status": "success", "message": f"Snapshot {snapshot_id} deleted"}
    
    def compare_snapshots(self, snapshot_id_1: str, snapshot_id_2: str) -> Dict[str, Any]:
        """
        Compare two snapshots.
        
        Args:
            snapshot_id_1: ID of the first snapshot
            snapshot_id_2: ID of the second snapshot
            
        Returns:
            A comparison of the two snapshots
        """
        snapshot_1 = self.get_snapshot(snapshot_id_1)
        snapshot_2 = self.get_snapshot(snapshot_id_2)
        
        if "error" in snapshot_1:
            return snapshot_1
        
        if "error" in snapshot_2:
            return snapshot_2
        
        # Compare file metrics
        file_diff = {
            "added": [],
            "removed": [],
            "modified": [],
        }
        
        files_1 = set(snapshot_1["file_metrics"].keys())
        files_2 = set(snapshot_2["file_metrics"].keys())
        
        file_diff["added"] = list(files_2 - files_1)
        file_diff["removed"] = list(files_1 - files_2)
        
        for file in files_1.intersection(files_2):
            if snapshot_1["file_metrics"][file] != snapshot_2["file_metrics"][file]:
                file_diff["modified"].append(file)
        
        # Compare function metrics
        function_diff = {
            "added": [],
            "removed": [],
            "modified": [],
        }
        
        functions_1 = set(snapshot_1["function_metrics"].keys())
        functions_2 = set(snapshot_2["function_metrics"].keys())
        
        function_diff["added"] = list(functions_2 - functions_1)
        function_diff["removed"] = list(functions_1 - functions_2)
        
        for func in functions_1.intersection(functions_2):
            if snapshot_1["function_metrics"][func] != snapshot_2["function_metrics"][func]:
                function_diff["modified"].append(func)
        
        # Compare class metrics
        class_diff = {
            "added": [],
            "removed": [],
            "modified": [],
        }
        
        classes_1 = set(snapshot_1["class_metrics"].keys())
        classes_2 = set(snapshot_2["class_metrics"].keys())
        
        class_diff["added"] = list(classes_2 - classes_1)
        class_diff["removed"] = list(classes_1 - classes_2)
        
        for cls in classes_1.intersection(classes_2):
            if snapshot_1["class_metrics"][cls] != snapshot_2["class_metrics"][cls]:
                class_diff["modified"].append(cls)
        
        # Create comparison result
        comparison = {
            "snapshot_1": snapshot_1["metadata"],
            "snapshot_2": snapshot_2["metadata"],
            "file_diff": file_diff,
            "function_diff": function_diff,
            "class_diff": class_diff,
        }
        
        return comparison


class PRReviewer:
    """
    Class for reviewing pull requests using codebase snapshots.
    """
    
    def __init__(
        self,
        repo_url: str,
        pr_number: int,
        snapshot_dir: Optional[str] = None,
    ):
        """
        Initialize the PR reviewer.
        
        Args:
            repo_url: URL of the repository
            pr_number: PR number to review
            snapshot_dir: Directory to store snapshots in
        """
        self.repo_url = repo_url
        self.pr_number = pr_number
        self.snapshot_dir = snapshot_dir or os.path.join(os.getcwd(), "snapshots")
        
        if not os.path.exists(self.snapshot_dir):
            os.makedirs(self.snapshot_dir)
    
    def review_pr(self) -> Dict[str, Any]:
        """
        Review a pull request.
        
        Returns:
            A dictionary containing review results
        """
        # Clone the repository
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_dir = os.path.join(temp_dir, "repo")
            
            # Clone the repository
            os.system(f"git clone {self.repo_url} {repo_dir}")
            
            # Fetch the PR
            os.system(f"cd {repo_dir} && git fetch origin pull/{self.pr_number}/head:pr-{self.pr_number}")
            
            # Get the base branch
            base_branch = "main"  # Default to main
            pr_info = os.popen(f"cd {repo_dir} && git show pr-{self.pr_number}").read()
            
            for line in pr_info.splitlines():
                if line.startswith("Merge:"):
                    base_branch = line.split()[1]
                    break
            
            # Create temporary directories for base and head
            base_dir = os.path.join(temp_dir, "base")
            head_dir = os.path.join(temp_dir, "head")
            
            os.makedirs(base_dir)
            os.makedirs(head_dir)
            
            # Copy the base branch to base_dir
            os.system(f"cd {repo_dir} && git checkout {base_branch}")
            os.system(f"cp -r {repo_dir}/. {base_dir}")
            
            # Copy the PR branch to head_dir
            os.system(f"cd {repo_dir} && git checkout pr-{self.pr_number}")
            os.system(f"cp -r {repo_dir}/. {head_dir}")
            
            # Create snapshots
            base_snapshot = CodebaseSnapshot(repo_path=base_dir, snapshot_dir=self.snapshot_dir)
            head_snapshot = CodebaseSnapshot(repo_path=head_dir, snapshot_dir=self.snapshot_dir)
            
            base_metadata = base_snapshot.create_snapshot(name=f"pr-{self.pr_number}-base")
            head_metadata = head_snapshot.create_snapshot(name=f"pr-{self.pr_number}-head")
            
            # Compare snapshots
            comparison = base_snapshot.compare_snapshots(base_metadata["id"], head_metadata["id"])
            
            # Analyze the PR
            analyzer = CodeAnalyzer()
            diff_analysis = analyzer.analyze_diff(base_path=base_dir, head_path=head_dir)
            
            # Create review result
            review_result = {
                "pr_number": self.pr_number,
                "repo_url": self.repo_url,
                "base_branch": base_branch,
                "comparison": comparison,
                "diff_analysis": diff_analysis,
            }
            
            return review_result


class PRTaskManager:
    """
    Class for managing PR-related tasks.
    """
    
    def __init__(
        self,
        repo_url: str,
        snapshot_dir: Optional[str] = None,
    ):
        """
        Initialize the PR task manager.
        
        Args:
            repo_url: URL of the repository
            snapshot_dir: Directory to store snapshots in
        """
        self.repo_url = repo_url
        self.snapshot_dir = snapshot_dir or os.path.join(os.getcwd(), "snapshots")
        
        if not os.path.exists(self.snapshot_dir):
            os.makedirs(self.snapshot_dir)
    
    def create_pr_task(self, pr_number: int, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a PR task.
        
        Args:
            pr_number: PR number
            task_type: Type of task (e.g., "review", "fix", "test")
            task_data: Task-specific data
            
        Returns:
            A dictionary containing task metadata
        """
        # Generate a task ID
        timestamp = datetime.now().isoformat()
        task_id = hashlib.md5(f"{timestamp}_{pr_number}_{task_type}".encode()).hexdigest()
        
        # Create task metadata
        metadata = {
            "id": task_id,
            "pr_number": pr_number,
            "repo_url": self.repo_url,
            "task_type": task_type,
            "timestamp": timestamp,
            "status": "created",
        }
        
        # Create the task data
        task = {
            "metadata": metadata,
            "data": task_data,
        }
        
        # Save the task
        task_path = os.path.join(self.snapshot_dir, f"task_{task_id}.json")
        with open(task_path, "w") as f:
            json.dump(task, f, indent=2)
        
        return metadata
    
    def get_pr_task(self, task_id: str) -> Dict[str, Any]:
        """
        Get a PR task by ID.
        
        Args:
            task_id: ID of the task to retrieve
            
        Returns:
            The task data
        """
        task_path = os.path.join(self.snapshot_dir, f"task_{task_id}.json")
        
        if not os.path.exists(task_path):
            return {"error": f"Task not found: {task_id}"}
        
        with open(task_path, "r") as f:
            task = json.load(f)
        
        return task
    
    def list_pr_tasks(self, pr_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List PR tasks.
        
        Args:
            pr_number: Optional PR number to filter by
            
        Returns:
            A list of task metadata
        """
        tasks = []
        
        for filename in os.listdir(self.snapshot_dir):
            if filename.startswith("task_") and filename.endswith(".json"):
                task_path = os.path.join(self.snapshot_dir, filename)
                
                with open(task_path, "r") as f:
                    task = json.load(f)
                
                if pr_number is None or task["metadata"]["pr_number"] == pr_number:
                    tasks.append(task["metadata"])
        
        return tasks
    
    def update_pr_task_status(self, task_id: str, status: str) -> Dict[str, Any]:
        """
        Update the status of a PR task.
        
        Args:
            task_id: ID of the task to update
            status: New status for the task
            
        Returns:
            The updated task metadata
        """
        task = self.get_pr_task(task_id)
        
        if "error" in task:
            return task
        
        task["metadata"]["status"] = status
        
        # Save the updated task
        task_path = os.path.join(self.snapshot_dir, f"task_{task_id}.json")
        with open(task_path, "w") as f:
            json.dump(task, f, indent=2)
        
        return task["metadata"]
    
    def delete_pr_task(self, task_id: str) -> Dict[str, Any]:
        """
        Delete a PR task by ID.
        
        Args:
            task_id: ID of the task to delete
            
        Returns:
            A status message
        """
        task_path = os.path.join(self.snapshot_dir, f"task_{task_id}.json")
        
        if not os.path.exists(task_path):
            return {"error": f"Task not found: {task_id}"}
        
        os.remove(task_path)
        
        return {"status": "success", "message": f"Task {task_id} deleted"}

