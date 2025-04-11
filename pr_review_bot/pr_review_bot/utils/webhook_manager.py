"""
Webhook manager module for the PR Review Bot.
Provides functionality for managing GitHub webhooks.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional

from ..core.github_client import GitHubClient

logger = logging.getLogger(__name__)

class WebhookManager:
    """
    Manager for GitHub webhooks.
    
    Provides functionality for setting up, updating, and deleting webhooks
    for GitHub repositories.
    """
    
    def __init__(self, github_client: GitHubClient, webhook_url: str, webhook_secret: Optional[str] = None):
        """
        Initialize the webhook manager.
        
        Args:
            github_client: GitHub client
            webhook_url: URL for the webhook
            webhook_secret: Secret for webhook verification
        """
        self.github_client = github_client
        self.webhook_url = webhook_url
        self.webhook_secret = webhook_secret
    
    def setup_webhook_for_repo(self, repo_name: str) -> Dict[str, Any]:
        """
        Set up a webhook for a repository.
        
        Args:
            repo_name: Repository name (owner/repo)
            
        Returns:
            Webhook data
        """
        logger.info(f"Setting up webhook for repository {repo_name}")
        
        # Check if webhook already exists
        existing_webhooks = self.github_client.get_webhooks(repo_name)
        
        for webhook in existing_webhooks:
            if webhook["config"].get("url") == self.webhook_url:
                logger.info(f"Webhook already exists for repository {repo_name}")
                return webhook
        
        # Create webhook data
        webhook_data = {
            "name": "web",
            "active": True,
            "events": ["pull_request", "push", "repository"],
            "config": {
                "url": self.webhook_url,
                "content_type": "json",
                "insecure_ssl": "0"
            }
        }
        
        # Add secret if provided
        if self.webhook_secret:
            webhook_data["config"]["secret"] = self.webhook_secret
        
        # Create webhook
        try:
            webhook = self.github_client.create_webhook(repo_name, webhook_data)
            logger.info(f"Created webhook for repository {repo_name}")
            return webhook
        except Exception as e:
            logger.error(f"Error creating webhook for repository {repo_name}: {e}")
            raise
    
    def update_webhook_for_repo(self, repo_name: str, webhook_id: int) -> Dict[str, Any]:
        """
        Update a webhook for a repository.
        
        Args:
            repo_name: Repository name (owner/repo)
            webhook_id: Webhook ID
            
        Returns:
            Updated webhook data
        """
        logger.info(f"Updating webhook {webhook_id} for repository {repo_name}")
        
        # Create webhook data
        webhook_data = {
            "active": True,
            "events": ["pull_request", "push", "repository"],
            "config": {
                "url": self.webhook_url,
                "content_type": "json",
                "insecure_ssl": "0"
            }
        }
        
        # Add secret if provided
        if self.webhook_secret:
            webhook_data["config"]["secret"] = self.webhook_secret
        
        # Update webhook
        try:
            webhook = self.github_client.update_webhook(repo_name, webhook_id, webhook_data)
            logger.info(f"Updated webhook {webhook_id} for repository {repo_name}")
            return webhook
        except Exception as e:
            logger.error(f"Error updating webhook {webhook_id} for repository {repo_name}: {e}")
            raise
    
    def delete_webhook_for_repo(self, repo_name: str, webhook_id: int) -> None:
        """
        Delete a webhook for a repository.
        
        Args:
            repo_name: Repository name (owner/repo)
            webhook_id: Webhook ID
        """
        logger.info(f"Deleting webhook {webhook_id} for repository {repo_name}")
        
        try:
            self.github_client.delete_webhook(repo_name, webhook_id)
            logger.info(f"Deleted webhook {webhook_id} for repository {repo_name}")
        except Exception as e:
            logger.error(f"Error deleting webhook {webhook_id} for repository {repo_name}: {e}")
            raise
    
    def setup_webhooks_for_all_repos(self) -> List[Dict[str, Any]]:
        """
        Set up webhooks for all repositories.
        
        Returns:
            List of webhook data
        """
        logger.info("Setting up webhooks for all repositories")
        
        # Get all repositories
        repos = self.github_client.get_repositories()
        
        # Set up webhooks for all repositories
        webhooks = []
        for repo in repos:
            try:
                webhook = self.setup_webhook_for_repo(repo["full_name"])
                webhooks.append({
                    "repo_name": repo["full_name"],
                    "webhook": webhook
                })
            except Exception as e:
                logger.error(f"Error setting up webhook for repository {repo['full_name']}: {e}")
        
        logger.info(f"Set up webhooks for {len(webhooks)} repositories")
        return webhooks
    
    def update_webhooks_for_all_repos(self) -> List[Dict[str, Any]]:
        """
        Update webhooks for all repositories.
        
        Returns:
            List of webhook data
        """
        logger.info("Updating webhooks for all repositories")
        
        # Get all repositories
        repos = self.github_client.get_repositories()
        
        # Update webhooks for all repositories
        webhooks = []
        for repo in repos:
            try:
                # Get existing webhooks
                existing_webhooks = self.github_client.get_webhooks(repo["full_name"])
                
                # Find webhook with matching URL
                for webhook in existing_webhooks:
                    if webhook["config"].get("url") == self.webhook_url:
                        # Update webhook
                        updated_webhook = self.update_webhook_for_repo(repo["full_name"], webhook["id"])
                        webhooks.append({
                            "repo_name": repo["full_name"],
                            "webhook": updated_webhook
                        })
                        break
                else:
                    # Webhook not found, create it
                    webhook = self.setup_webhook_for_repo(repo["full_name"])
                    webhooks.append({
                        "repo_name": repo["full_name"],
                        "webhook": webhook
                    })
            except Exception as e:
                logger.error(f"Error updating webhook for repository {repo['full_name']}: {e}")
        
        logger.info(f"Updated webhooks for {len(webhooks)} repositories")
        return webhooks
