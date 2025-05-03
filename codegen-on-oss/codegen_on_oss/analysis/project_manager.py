"""
Project Manager Module

This module provides functionality for managing projects in the analysis server.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import from existing analysis modules
from codegen_on_oss.analysis.analysis import CodeAnalyzer
from codegen_on_oss.analysis.codebase_context import CodebaseContext
from codegen_on_oss.bucket_store import BucketStore
from codegen_on_oss.cache import Cache


class Project:
    """
    Represents a project in the analysis server.

    A project is a repository that can be analyzed by the server.
    """

    def __init__(
        self,
        repo_url: str,
        name: str,
        description: Optional[str] = None,
        default_branch: str = "main",
    ):
        """
        Initialize a new Project.

        Args:
            repo_url: URL of the repository
            name: Name of the project
            description: Optional description of the project
            default_branch: Default branch of the repository
        """
        self.project_id = str(uuid.uuid4())
        self.repo_url = repo_url
        self.name = name
        self.description = description
        self.default_branch = default_branch
        self.created_at = datetime.now()
        self.last_analyzed = None
        self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the project to a dictionary.

        Returns:
            A dictionary representation of the project
        """
        return {
            "project_id": self.project_id,
            "repo_url": self.repo_url,
            "name": self.name,
            "description": self.description,
            "default_branch": self.default_branch,
            "created_at": self.created_at.isoformat(),
            "last_analyzed": (
                self.last_analyzed.isoformat() if self.last_analyzed else None
            ),
            "metadata": self.metadata,
        }

    def update_metadata(self, key: str, value: Any) -> None:
        """
        Update a metadata value for the project.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value

    def mark_analyzed(self) -> None:
        """Mark the project as analyzed."""
        self.last_analyzed = datetime.now()


class ProjectManager:
    """
    Manages projects in the analysis server.

    This class provides functionality for registering, retrieving, and managing
    projects in the analysis server.
    """

    def __init__(self):
        """Initialize a new ProjectManager."""
        self.projects: Dict[str, Project] = {}
        self.logger = logging.getLogger(__name__)

    def register_project(
        self,
        repo_url: str,
        name: str,
        description: Optional[str] = None,
        default_branch: str = "main",
    ) -> Project:
        """
        Register a new project.

        Args:
            repo_url: URL of the repository
            name: Name of the project
            description: Optional description of the project
            default_branch: Default branch of the repository

        Returns:
            The registered project
        """
        project = Project(
            repo_url=repo_url,
            name=name,
            description=description,
            default_branch=default_branch,
        )

        self.projects[project.project_id] = project
        self.logger.info(f"Registered project {name} with ID {project.project_id}")

        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        """
        Get a project by ID.

        Args:
            project_id: ID of the project

        Returns:
            The project, or None if not found
        """
        return self.projects.get(project_id)

    def get_projects(self) -> List[Project]:
        """
        Get all projects.

        Returns:
            A list of all projects
        """
        return list(self.projects.values())

    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project.

        Args:
            project_id: ID of the project

        Returns:
            True if the project was deleted, False otherwise
        """
        if project_id in self.projects:
            del self.projects[project_id]
            self.logger.info(f"Deleted project with ID {project_id}")
            return True

        return False

