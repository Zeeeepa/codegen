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
    Manages projects and webhooks for the analysis server.
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize a new ProjectManager.
        
        Args:
            data_dir: Directory to store project data
        """
        self.data_dir = data_dir or os.path.join(os.path.expanduser("~"), ".codegen_analysis")
        self.projects_file = os.path.join(self.data_dir, "projects.json")
        self.webhooks_file = os.path.join(self.data_dir, "webhooks.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load projects and webhooks
        self.projects: Dict[str, Project] = {}
        self.webhooks: Dict[str, Webhook] = {}
        
        self._load_projects()
        self._load_webhooks()
    
    def _load_projects(self):
        """Load projects from the projects file."""
        if os.path.exists(self.projects_file):
            try:
                with open(self.projects_file, "r") as f:
                    projects_data = json.load(f)
                
                for project_data in projects_data:
                    project = Project.from_dict(project_data)
                    self.projects[project.project_id] = project
                
                logger.info(f"Loaded {len(self.projects)} projects")
            except Exception as e:
                logger.error(f"Error loading projects: {e}")
    
    def _load_webhooks(self):
        """Load webhooks from the webhooks file."""
        if os.path.exists(self.webhooks_file):
            try:
                with open(self.webhooks_file, "r") as f:
                    webhooks_data = json.load(f)
                
                for webhook_data in webhooks_data:
                    webhook = Webhook.from_dict(webhook_data)
                    self.webhooks[webhook.webhook_id] = webhook
                
                logger.info(f"Loaded {len(self.webhooks)} webhooks")
            except Exception as e:
                logger.error(f"Error loading webhooks: {e}")
    
    def _save_projects(self):
        """Save projects to the projects file."""
        try:
            projects_data = [project.to_dict() for project in self.projects.values()]
            
            with open(self.projects_file, "w") as f:
                json.dump(projects_data, f, indent=2)
            
            logger.info(f"Saved {len(self.projects)} projects")
        except Exception as e:
            logger.error(f"Error saving projects: {e}")
    
    def _save_webhooks(self):
        """Save webhooks to the webhooks file."""
        try:
            webhooks_data = [webhook.to_dict() for webhook in self.webhooks.values()]
            
            with open(self.webhooks_file, "w") as f:
                json.dump(webhooks_data, f, indent=2)
            
            logger.info(f"Saved {len(self.webhooks)} webhooks")
        except Exception as e:
            logger.error(f"Error saving webhooks: {e}")
    
    def register_project(
        self,
        name: str,
        repo_url: str,
        description: Optional[str] = None,
        default_branch: str = "main",
        webhook_url: Optional[str] = None,
        github_token: Optional[str] = None
    ) -> Project:
        """
        Register a new project for analysis.
        
        Args:
            name: Name of the project
            repo_url: URL of the repository
            description: Optional description of the project
            default_branch: Default branch of the repository
            webhook_url: Optional webhook URL to notify when analysis is complete
            github_token: Optional GitHub token for private repositories
            
        Returns:
            The registered project
        """
        # Generate a unique ID for the project
        project_id = str(uuid.uuid4())
        
        # Create the project
        project = Project(
            project_id=project_id,
            name=name,
            repo_url=repo_url,
            description=description,
            default_branch=default_branch,
            webhook_url=webhook_url,
            github_token=github_token
        )
        
        # Add the project to the projects dictionary
        self.projects[project_id] = project
        
        # Save the projects
        self._save_projects()
        
        return project
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """
        Get a project by ID.
        
        Args:
            project_id: ID of the project to get
            
        Returns:
            The project, or None if not found
        """
        return self.projects.get(project_id)
    
    def get_project_by_repo_url(self, repo_url: str) -> Optional[Project]:
        """
        Get a project by repository URL.
        
        Args:
            repo_url: URL of the repository
            
        Returns:
            The project, or None if not found
        """
        for project in self.projects.values():
            if project.repo_url == repo_url:
                return project
        
        return None
    
    def get_all_projects(self) -> List[Project]:
        """
        Get all projects.
        
        Returns:
            A list of all projects
        """
        return list(self.projects.values())
    
    def update_project(
        self,
        project_id: str,
        name: Optional[str] = None,
        repo_url: Optional[str] = None,
        description: Optional[str] = None,
        default_branch: Optional[str] = None,
        webhook_url: Optional[str] = None,
        github_token: Optional[str] = None,
        last_analyzed: Optional[datetime] = None
    ) -> Optional[Project]:
        """
        Update a project.
        
        Args:
            project_id: ID of the project to update
            name: New name for the project
            repo_url: New URL for the repository
            description: New description for the project
            default_branch: New default branch for the repository
            webhook_url: New webhook URL
            github_token: New GitHub token
            last_analyzed: New last analyzed timestamp
            
        Returns:
            The updated project, or None if not found
        """
        project = self.get_project(project_id)
        
        if not project:
            return None
        
        # Update the project
        if name is not None:
            project.name = name
        
        if repo_url is not None:
            project.repo_url = repo_url
        
        if description is not None:
            project.description = description
        
        if default_branch is not None:
            project.default_branch = default_branch
        
        if webhook_url is not None:
            project.webhook_url = webhook_url
        
        if github_token is not None:
            project.github_token = github_token
        
        if last_analyzed is not None:
            project.last_analyzed = last_analyzed
        
        # Save the projects
        self._save_projects()
        
        return project
    
    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project.
        
        Args:
            project_id: ID of the project to delete
            
        Returns:
            True if the project was deleted, False if not found
        """
        if project_id not in self.projects:
            return False
        
        # Delete the project
        del self.projects[project_id]
        
        # Delete any webhooks for the project
        webhooks_to_delete = []
        
        for webhook_id, webhook in self.webhooks.items():
            if webhook.project_id == project_id:
                webhooks_to_delete.append(webhook_id)
        
        for webhook_id in webhooks_to_delete:
            del self.webhooks[webhook_id]
        
        # Save the projects and webhooks
        self._save_projects()
        self._save_webhooks()
        
        return True
    
    def register_webhook(
        self,
        project_id: str,
        webhook_url: str,
        events: List[str],
        secret: Optional[str] = None
    ) -> Optional[Webhook]:
        """
        Register a new webhook for a project.
        
        Args:
            project_id: ID of the project to register the webhook for
            webhook_url: URL to send webhook notifications to
            events: Events to trigger the webhook
            secret: Optional secret to sign webhook payloads with
            
        Returns:
            The registered webhook, or None if the project doesn't exist
        """
        # Check if the project exists
        if project_id not in self.projects:
            return None
        
        # Generate a unique ID for the webhook
        webhook_id = str(uuid.uuid4())
        
        # Create the webhook
        webhook = Webhook(
            webhook_id=webhook_id,
            project_id=project_id,
            webhook_url=webhook_url,
            events=events,
            secret=secret
        )
        
        # Add the webhook to the webhooks dictionary
        self.webhooks[webhook_id] = webhook
        
        # Save the webhooks
        self._save_webhooks()
        
        return webhook
    
    def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """
        Get a webhook by ID.
        
        Args:
            webhook_id: ID of the webhook to get
            
        Returns:
            The webhook, or None if not found
        """
        return self.webhooks.get(webhook_id)
    
    def get_webhooks_for_project(self, project_id: str) -> List[Webhook]:
        """
        Get all webhooks for a project.
        
        Args:
            project_id: ID of the project to get webhooks for
            
        Returns:
            A list of webhooks for the project
        """
        return [webhook for webhook in self.webhooks.values() if webhook.project_id == project_id]
    
    def get_all_webhooks(self) -> List[Webhook]:
        """
        Get all webhooks.
        
        Returns:
            A list of all webhooks
        """
        return list(self.webhooks.values())
    
    def update_webhook(
        self,
        webhook_id: str,
        webhook_url: Optional[str] = None,
        events: Optional[List[str]] = None,
        secret: Optional[str] = None,
        last_triggered: Optional[datetime] = None
    ) -> Optional[Webhook]:
        """
        Update a webhook.
        
        Args:
            webhook_id: ID of the webhook to update
            webhook_url: New URL for the webhook
            events: New events for the webhook
            secret: New secret for the webhook
            last_triggered: New last triggered timestamp
            
        Returns:
            The updated webhook, or None if not found
        """
        webhook = self.get_webhook(webhook_id)
        
        if not webhook:
            return None
        
        # Update the webhook
        if webhook_url is not None:
            webhook.webhook_url = webhook_url
        
        if events is not None:
            webhook.events = events
        
        if secret is not None:
            webhook.secret = secret
        
        if last_triggered is not None:
            webhook.last_triggered = last_triggered
        
        # Save the webhooks
        self._save_webhooks()
        
        return webhook
    
    def delete_webhook(self, webhook_id: str) -> bool:
        """
        Delete a webhook.
        
        Args:
            webhook_id: ID of the webhook to delete
            
        Returns:
            True if the webhook was deleted, False if not found
        """
        if webhook_id not in self.webhooks:
            return False
        
        # Delete the webhook
        del self.webhooks[webhook_id]
        
        # Save the webhooks
        self._save_webhooks()
        
        return True
    
    def trigger_webhook(
        self,
        webhook: Webhook,
        event: str,
        payload: Dict[str, Any]
    ) -> bool:
        """
        Trigger a webhook.
        
        Args:
            webhook: The webhook to trigger
            event: The event that triggered the webhook
            payload: The payload to send to the webhook
            
        Returns:
            True if the webhook was triggered successfully, False otherwise
        """
        import requests
        import hmac
        import hashlib
        
        # Check if the webhook should be triggered for this event
        if event not in webhook.events:
            return False
        
        # Add the event to the payload
        payload["event"] = event
        
        # Add the webhook ID to the payload
        payload["webhook_id"] = webhook.webhook_id
        
        # Add the project ID to the payload
        payload["project_id"] = webhook.project_id
        
        # Convert the payload to JSON
        payload_json = json.dumps(payload)
        
        # Create the headers
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add the signature if a secret is provided
        if webhook.secret:
            signature = hmac.new(
                webhook.secret.encode(),
                payload_json.encode(),
                hashlib.sha256
            ).hexdigest()
            
            headers["X-Webhook-Signature"] = signature
        
        try:
            # Send the webhook
            response = requests.post(
                webhook.webhook_url,
                headers=headers,
                data=payload_json
            )
            
            # Update the last triggered timestamp
            webhook.last_triggered = datetime.now()
            
            # Save the webhooks
            self._save_webhooks()
            
            # Check if the webhook was successful
            return response.status_code >= 200 and response.status_code < 300
        except Exception as e:
            logger.error(f"Error triggering webhook {webhook.webhook_id}: {e}")
            return False
    
    def trigger_webhooks_for_project(
        self,
        project_id: str,
        event: str,
        payload: Dict[str, Any]
    ) -> int:
        """
        Trigger all webhooks for a project for a specific event.
        
        Args:
            project_id: ID of the project to trigger webhooks for
            event: The event that triggered the webhooks
            payload: The payload to send to the webhooks
            
        Returns:
            The number of webhooks triggered successfully
        """
        # Get all webhooks for the project
        webhooks = self.get_webhooks_for_project(project_id)
        
        # Trigger each webhook
        successful_webhooks = 0
        
        for webhook in webhooks:
            if self.trigger_webhook(webhook, event, payload):
                successful_webhooks += 1
        
        return successful_webhooks
