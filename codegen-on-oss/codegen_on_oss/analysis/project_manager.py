"""
Project Manager Module

This module provides functionality for managing projects and webhooks
for the analysis server.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Set
from pathlib import Path

logger = logging.getLogger(__name__)

class Project:
    """
    Represents a project registered for analysis.
    """
    
    def __init__(
        self,
        project_id: str,
        name: str,
        repo_url: str,
        description: Optional[str] = None,
        default_branch: str = "main",
        webhook_url: Optional[str] = None,
        github_token: Optional[str] = None,
        created_at: Optional[datetime] = None,
        last_analyzed: Optional[datetime] = None
    ):
        """
        Initialize a new Project.
        
        Args:
            project_id: Unique identifier for the project
            name: Name of the project
            repo_url: URL of the repository
            description: Optional description of the project
            default_branch: Default branch of the repository
            webhook_url: Optional webhook URL to notify when analysis is complete
            github_token: Optional GitHub token for private repositories
            created_at: When the project was created
            last_analyzed: When the project was last analyzed
        """
        self.project_id = project_id
        self.name = name
        self.repo_url = repo_url
        self.description = description
        self.default_branch = default_branch
        self.webhook_url = webhook_url
        self.github_token = github_token
        self.created_at = created_at or datetime.now()
        self.last_analyzed = last_analyzed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the project to a dictionary."""
        return {
            "project_id": self.project_id,
            "name": self.name,
            "repo_url": self.repo_url,
            "description": self.description,
            "default_branch": self.default_branch,
            "webhook_url": self.webhook_url,
            "github_token": self.github_token,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_analyzed": self.last_analyzed.isoformat() if self.last_analyzed else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        """Create a project from a dictionary."""
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        last_analyzed = datetime.fromisoformat(data["last_analyzed"]) if data.get("last_analyzed") else None
        
        return cls(
            project_id=data["project_id"],
            name=data["name"],
            repo_url=data["repo_url"],
            description=data.get("description"),
            default_branch=data.get("default_branch", "main"),
            webhook_url=data.get("webhook_url"),
            github_token=data.get("github_token"),
            created_at=created_at,
            last_analyzed=last_analyzed
        )

class Webhook:
    """
    Represents a webhook registered for a project.
    """
    
    def __init__(
        self,
        webhook_id: str,
        project_id: str,
        webhook_url: str,
        events: List[str],
        secret: Optional[str] = None,
        created_at: Optional[datetime] = None,
        last_triggered: Optional[datetime] = None
    ):
        """
        Initialize a new Webhook.
        
        Args:
            webhook_id: Unique identifier for the webhook
            project_id: ID of the project the webhook is for
            webhook_url: URL to send webhook notifications to
            events: Events to trigger the webhook
            secret: Optional secret to sign webhook payloads with
            created_at: When the webhook was created
            last_triggered: When the webhook was last triggered
        """
        self.webhook_id = webhook_id
        self.project_id = project_id
        self.webhook_url = webhook_url
        self.events = events
        self.secret = secret
        self.created_at = created_at or datetime.now()
        self.last_triggered = last_triggered
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the webhook to a dictionary."""
        return {
            "webhook_id": self.webhook_id,
            "project_id": self.project_id,
            "webhook_url": self.webhook_url,
            "events": self.events,
            "secret": self.secret,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Webhook":
        """Create a webhook from a dictionary."""
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        last_triggered = datetime.fromisoformat(data["last_triggered"]) if data.get("last_triggered") else None
        
        return cls(
            webhook_id=data["webhook_id"],
            project_id=data["project_id"],
            webhook_url=data["webhook_url"],
            events=data["events"],
            secret=data.get("secret"),
            created_at=created_at,
            last_triggered=last_triggered
        )

class ProjectManager:
    """
    Manager for projects registered for analysis.
    """
    
    def __init__(self) -> None:
        """
        Initialize the project manager.
        """
        self.projects: Dict[str, Dict[str, Any]] = {}
        self.webhooks: Dict[str, Dict[str, Any]] = {}
    
    def register_project(self, repo_url: str, name: str, description: Optional[str] = None, 
                         default_branch: str = "main", webhook_url: Optional[str] = None, 
                         github_token: Optional[str] = None) -> str:
        """
        Register a project for analysis.
        
        Args:
            repo_url: The URL of the repository.
            name: The name of the project.
            description: The description of the project.
            default_branch: The default branch of the repository.
            webhook_url: The webhook URL to notify when analysis is complete.
            github_token: The GitHub token for private repositories.
            
        Returns:
            The ID of the registered project.
        """
        # Generate a unique ID for the project
        project_id = str(uuid.uuid4())
        
        # Create the project
        self.projects[project_id] = {
            "project_id": project_id,
            "name": name,
            "repo_url": repo_url,
            "description": description,
            "default_branch": default_branch,
            "webhook_url": webhook_url,
            "github_token": github_token,
            "created_at": datetime.now().isoformat(),
        }
        
        return project_id
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a project by ID.
        
        Args:
            project_id: The ID of the project.
            
        Returns:
            The project data, or None if not found.
        """
        return self.projects.get(project_id)
