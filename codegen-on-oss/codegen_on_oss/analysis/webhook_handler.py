"""
Webhook Handler Module

This module provides functionality for handling webhooks from Git providers.
"""

import json
import logging
import uuid
import hmac
import hashlib
import os
import tempfile
import subprocess
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from pathlib import Path

# Import from existing analysis modules
from codegen import Codebase
from codegen_on_oss.analysis.analysis import CodeAnalyzer
from codegen_on_oss.analysis.codebase_context import CodebaseContext
from codegen_on_oss.analysis.commit_analysis import CommitAnalyzer
from codegen_on_oss.snapshot.codebase_snapshot import CodebaseSnapshot
from codegen_on_oss.outputs.base import OutputHandler

logger = logging.getLogger(__name__)

class Webhook:
    """
    Represents a webhook registered for a project.
    
    A webhook is a way for the analysis server to notify external services
    about events that occur in the server.
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
            project_id: ID of the project the webhook is registered for
            webhook_url: URL to send webhook events to
            events: List of event types to trigger the webhook for
            secret: Optional secret for signing webhook payloads
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


class WebhookHandler:
    """
    Handler for webhooks.
    
    This class provides functionality for registering, triggering, and managing webhooks.
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize a new WebhookHandler.
        
        Args:
            data_dir: Directory to store webhook data
        """
        self.data_dir = data_dir or os.path.expanduser("~/.codegen_analysis/webhooks")
        os.makedirs(self.data_dir, exist_ok=True)
        self.webhooks: Dict[str, Webhook] = {}
        self._load_webhooks()
    
    def _load_webhooks(self) -> None:
        """Load webhooks from disk."""
        webhook_file = os.path.join(self.data_dir, "webhooks.json")
        
        if os.path.exists(webhook_file):
            try:
                with open(webhook_file, "r") as f:
                    webhook_data = json.load(f)
                
                for webhook_id, data in webhook_data.items():
                    self.webhooks[webhook_id] = Webhook.from_dict(data)
            except Exception as e:
                logger.error(f"Failed to load webhooks: {e}")
    
    def _save_webhooks(self) -> None:
        """Save webhooks to disk."""
        webhook_file = os.path.join(self.data_dir, "webhooks.json")
        
        try:
            webhook_data = {
                webhook_id: webhook.to_dict()
                for webhook_id, webhook in self.webhooks.items()
            }
            
            with open(webhook_file, "w") as f:
                json.dump(webhook_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save webhooks: {e}")
    
    def register_webhook(
        self,
        project_id: str,
        webhook_url: str,
        events: List[str],
        secret: Optional[str] = None
    ) -> Webhook:
        """
        Register a new webhook.
        
        Args:
            project_id: ID of the project to register the webhook for
            webhook_url: URL to send webhook events to
            events: List of event types to trigger the webhook for
            secret: Optional secret for signing webhook payloads
            
        Returns:
            The registered webhook
        """
        webhook_id = str(uuid.uuid4())
        
        webhook = Webhook(
            webhook_id=webhook_id,
            project_id=project_id,
            webhook_url=webhook_url,
            events=events,
            secret=secret
        )
        
        self.webhooks[webhook_id] = webhook
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
            List of webhooks for the project
        """
        return [
            webhook for webhook in self.webhooks.values()
            if webhook.project_id == project_id
        ]
    
    def update_webhook(
        self,
        webhook_id: str,
        webhook_url: Optional[str] = None,
        events: Optional[List[str]] = None,
        secret: Optional[str] = None
    ) -> Optional[Webhook]:
        """
        Update a webhook.
        
        Args:
            webhook_id: ID of the webhook to update
            webhook_url: New URL for the webhook
            events: New list of event types
            secret: New secret for signing webhook payloads
            
        Returns:
            The updated webhook, or None if not found
        """
        webhook = self.get_webhook(webhook_id)
        
        if not webhook:
            return None
        
        if webhook_url is not None:
            webhook.webhook_url = webhook_url
        
        if events is not None:
            webhook.events = events
        
        if secret is not None:
            webhook.secret = secret
        
        self._save_webhooks()
        
        return webhook
    
    def delete_webhook(self, webhook_id: str) -> bool:
        """
        Delete a webhook.
        
        Args:
            webhook_id: ID of the webhook to delete
            
        Returns:
            True if the webhook was deleted, False otherwise
        """
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            self._save_webhooks()
            return True
        
        return False
    
    def trigger_webhook(
        self,
        webhook: Webhook,
        event_type: str,
        payload: Dict[str, Any]
    ) -> bool:
        """
        Trigger a webhook.
        
        Args:
            webhook: The webhook to trigger
            event_type: Type of event that triggered the webhook
            payload: Data to send to the webhook
            
        Returns:
            True if the webhook was triggered successfully, False otherwise
        """
        import requests
        
        if event_type not in webhook.events:
            return False
        
        # Add metadata to the payload
        full_payload = {
            "event_type": event_type,
            "webhook_id": webhook.webhook_id,
            "project_id": webhook.project_id,
            "timestamp": datetime.now().isoformat(),
            "data": payload
        }
        
        # Sign the payload if a secret is provided
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": event_type
        }
        
        if webhook.secret:
            signature = self._sign_payload(full_payload, webhook.secret)
            headers["X-Webhook-Signature"] = signature
        
        try:
            response = requests.post(
                webhook.webhook_url,
                json=full_payload,
                headers=headers,
                timeout=10
            )
            
            # Update last triggered timestamp
            webhook.last_triggered = datetime.now()
            self._save_webhooks()
            
            return response.status_code >= 200 and response.status_code < 300
        except Exception as e:
            logger.error(f"Failed to trigger webhook {webhook.webhook_id}: {e}")
            return False
    
    def trigger_webhooks_for_project(
        self,
        project_id: str,
        event_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, bool]:
        """
        Trigger all webhooks for a project.
        
        Args:
            project_id: ID of the project to trigger webhooks for
            event_type: Type of event that triggered the webhooks
            payload: Data to send to the webhooks
            
        Returns:
            Dictionary mapping webhook IDs to success status
        """
        webhooks = self.get_webhooks_for_project(project_id)
        results = {}
        
        for webhook in webhooks:
            results[webhook.webhook_id] = self.trigger_webhook(
                webhook,
                event_type,
                payload
            )
        
        return results
    
    def _sign_payload(self, payload: Dict[str, Any], secret: str) -> str:
        """
        Sign a webhook payload.
        
        Args:
            payload: The payload to sign
            secret: The secret to use for signing
            
        Returns:
            The signature
        """
        payload_str = json.dumps(payload, sort_keys=True)
        hmac_obj = hmac.new(
            secret.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256
        )
        return hmac_obj.hexdigest()


class GitWebhookHandler:
    """
    Handler for Git webhooks.
    
    This class provides functionality for handling webhooks from Git providers
    like GitHub, GitLab, and Bitbucket.
    """
    
    def __init__(
        self,
        webhook_handler: WebhookHandler,
        output_handler: Optional[OutputHandler] = None
    ):
        """
        Initialize a new GitWebhookHandler.
        
        Args:
            webhook_handler: WebhookHandler to use for managing webhooks
            output_handler: OutputHandler to use for saving analysis results
        """
        self.webhook_handler = webhook_handler
        self.output_handler = output_handler
    
    def handle_github_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any],
        signature: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle a webhook from GitHub.
        
        Args:
            event_type: Type of event from GitHub
            payload: Webhook payload from GitHub
            signature: Optional signature for verifying the webhook
            
        Returns:
            Dictionary with the result of handling the webhook
        """
        # Map GitHub event types to our event types
        event_map = {
            "push": "commit",
            "pull_request": "pr",
            "pull_request_review": "pr_review",
            "issues": "issue",
            "issue_comment": "issue_comment"
        }
        
        our_event_type = event_map.get(event_type, event_type)
        
        # Extract repository information
        repo_info = payload.get("repository", {})
        repo_name = repo_info.get("full_name", "")
        repo_url = repo_info.get("clone_url", "")
        
        # Handle different event types
        if event_type == "push":
            return self._handle_github_push(payload, repo_name, repo_url)
        elif event_type == "pull_request":
            return self._handle_github_pr(payload, repo_name, repo_url)
        else:
            return {
                "status": "ignored",
                "message": f"Event type {event_type} is not handled"
            }
    
    def _handle_github_push(
        self,
        payload: Dict[str, Any],
        repo_name: str,
        repo_url: str
    ) -> Dict[str, Any]:
        """
        Handle a push event from GitHub.
        
        Args:
            payload: Webhook payload from GitHub
            repo_name: Name of the repository
            repo_url: URL of the repository
            
        Returns:
            Dictionary with the result of handling the webhook
        """
        # Extract commit information
        commits = payload.get("commits", [])
        
        if not commits:
            return {
                "status": "ignored",
                "message": "No commits in the push"
            }
        
        # Analyze the latest commit
        latest_commit = commits[-1]
        commit_hash = latest_commit.get("id", "")
        
        if not commit_hash:
            return {
                "status": "error",
                "message": "No commit hash found"
            }
        
        try:
            # Create a temporary directory for the repository
            with tempfile.TemporaryDirectory() as temp_dir:
                # Clone the repository
                subprocess.run(
                    ["git", "clone", repo_url, temp_dir],
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                # Create a codebase from the repository
                codebase = Codebase.from_directory(temp_dir)
                
                # Create a snapshot
                snapshot = CodebaseSnapshot.create_from_codebase(
                    codebase=codebase,
                    repo_url=repo_url,
                    commit_hash=commit_hash
                )
                
                # Analyze the commit
                analyzer = CommitAnalyzer(repo_path=temp_dir)
                result = analyzer.analyze_commit(commit_hash)
                
                # Save the result if we have an output handler
                if self.output_handler:
                    self.output_handler.save_result(
                        result_type="commit_analysis",
                        result=result.to_dict(),
                        metadata={
                            "repo_name": repo_name,
                            "repo_url": repo_url,
                            "commit_hash": commit_hash
                        }
                    )
                
                # Trigger webhooks for the project
                # Note: In a real implementation, you would look up the project ID
                # based on the repository name or URL
                project_id = repo_name.replace("/", "-")
                
                self.webhook_handler.trigger_webhooks_for_project(
                    project_id=project_id,
                    event_type="commit",
                    payload={
                        "repo_name": repo_name,
                        "repo_url": repo_url,
                        "commit_hash": commit_hash,
                        "analysis_result": result.to_dict()
                    }
                )
                
                return {
                    "status": "success",
                    "message": f"Analyzed commit {commit_hash}",
                    "result": result.to_dict()
                }
        except Exception as e:
            logger.error(f"Failed to analyze commit {commit_hash}: {e}")
            
            return {
                "status": "error",
                "message": f"Failed to analyze commit: {str(e)}"
            }
    
    def _handle_github_pr(
        self,
        payload: Dict[str, Any],
        repo_name: str,
        repo_url: str
    ) -> Dict[str, Any]:
        """
        Handle a pull request event from GitHub.
        
        Args:
            payload: Webhook payload from GitHub
            repo_name: Name of the repository
            repo_url: URL of the repository
            
        Returns:
            Dictionary with the result of handling the webhook
        """
        # Extract pull request information
        pr = payload.get("pull_request", {})
        pr_number = pr.get("number")
        
        if not pr_number:
            return {
                "status": "error",
                "message": "No pull request number found"
            }
        
        # Only handle opened or synchronized pull requests
        action = payload.get("action")
        
        if action not in ["opened", "synchronize", "reopened"]:
            return {
                "status": "ignored",
                "message": f"Pull request action {action} is not handled"
            }
        
        try:
            # Create a temporary directory for the repository
            with tempfile.TemporaryDirectory() as temp_dir:
                # Clone the repository
                subprocess.run(
                    ["git", "clone", repo_url, temp_dir],
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                # Fetch the pull request
                subprocess.run(
                    [
                        "git",
                        "-C",
                        temp_dir,
                        "fetch",
                        "origin",
                        f"pull/{pr_number}/head:pr-{pr_number}"
                    ],
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                # Checkout the pull request
                subprocess.run(
                    [
                        "git",
                        "-C",
                        temp_dir,
                        "checkout",
                        f"pr-{pr_number}"
                    ],
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                # Create a codebase from the repository
                codebase = Codebase.from_directory(temp_dir)
                
                # Create a snapshot
                snapshot = CodebaseSnapshot.create_from_codebase(
                    codebase=codebase,
                    repo_url=repo_url,
                    commit_hash=pr.get("head", {}).get("sha", "")
                )
                
                # Analyze the codebase
                analyzer = CodeAnalyzer(codebase)
                analysis_result = {
                    "summary": analyzer.get_codebase_summary(),
                    "complexity": analyzer.analyze_complexity(),
                    "imports": analyzer.analyze_imports()
                }
                
                # Save the result if we have an output handler
                if self.output_handler:
                    self.output_handler.save_result(
                        result_type="pr_analysis",
                        result=analysis_result,
                        metadata={
                            "repo_name": repo_name,
                            "repo_url": repo_url,
                            "pr_number": pr_number
                        }
                    )
                
                # Trigger webhooks for the project
                # Note: In a real implementation, you would look up the project ID
                # based on the repository name or URL
                project_id = repo_name.replace("/", "-")
                
                self.webhook_handler.trigger_webhooks_for_project(
                    project_id=project_id,
                    event_type="pr",
                    payload={
                        "repo_name": repo_name,
                        "repo_url": repo_url,
                        "pr_number": pr_number,
                        "analysis_result": analysis_result
                    }
                )
                
                return {
                    "status": "success",
                    "message": f"Analyzed pull request {pr_number}",
                    "result": analysis_result
                }
        except Exception as e:
            logger.error(f"Failed to analyze pull request {pr_number}: {e}")
            
            return {
                "status": "error",
                "message": f"Failed to analyze pull request: {str(e)}"
            }
