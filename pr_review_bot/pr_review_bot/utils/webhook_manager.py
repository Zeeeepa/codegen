"""
Webhook manager for the PR Review Bot.
This module provides functionality for managing GitHub webhooks.
"""

import os
import logging
import hmac
import hashlib
import secrets
from typing import Dict, Any, Optional, List

from ..core.github_client import GitHubClient

logger = logging.getLogger(__name__)

class WebhookManager:
    """
    Manager for GitHub webhooks.
    
    This class provides functionality for setting up and managing GitHub webhooks.
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
        self.webhook_secret = webhook_secret or self._generate_webhook_secret()
    
    def _generate_webhook_secret(self) -> str:
        """
        Generate a random webhook secret.
        
        Returns:
            Random webhook secret
        """
        return secrets.token_hex(20)
    
    def setup_webhook(self, repo_name: str) -> Dict[str, Any]:
        """
        Set up a webhook for a repository.
        
        Args:
            repo_name: Name of the repository
            
        Returns:
            Webhook data
        """
        logger.info(f"Setting up webhook for repository {repo_name}")
        
        # Check if webhook already exists
        existing_webhook = self._get_existing_webhook(repo_name)
        if existing_webhook:
            logger.info(f"Webhook already exists for repository {repo_name}")
            return existing_webhook
        
        # Create webhook
        webhook_data = {
            "name": "web",
            "active": True,
            "events": ["pull_request", "push", "repository"],
            "config": {
                "url": self.webhook_url,
                "content_type": "json",
                "secret": self.webhook_secret,
                "insecure_ssl": "0"
            }
        }
        
        try:
            # Create webhook
            webhook = self.github_client.create_webhook(repo_name, webhook_data)
            
            logger.info(f"Webhook created for repository {repo_name}")
            return webhook
        except Exception as e:
            logger.error(f"Error creating webhook for repository {repo_name}: {e}")
            return {"error": str(e)}
    
    def _get_existing_webhook(self, repo_name: str) -> Optional[Dict[str, Any]]:
        """
        Get an existing webhook for a repository.
        
        Args:
            repo_name: Name of the repository
            
        Returns:
            Webhook data if it exists, None otherwise
        """
        try:
            # Get webhooks
            webhooks = self.github_client.get_webhooks(repo_name)
            
            # Check if webhook already exists
            for webhook in webhooks:
                if webhook.get("config", {}).get("url") == self.webhook_url:
                    return webhook
            
            return None
        except Exception as e:
            logger.error(f"Error getting webhooks for repository {repo_name}: {e}")
            return None
    
    def update_webhook(self, repo_name: str, webhook_id: int) -> Dict[str, Any]:
        """
        Update a webhook for a repository.
        
        Args:
            repo_name: Name of the repository
            webhook_id: ID of the webhook
            
        Returns:
            Webhook data
        """
        logger.info(f"Updating webhook {webhook_id} for repository {repo_name}")
        
        # Update webhook
        webhook_data = {
            "active": True,
            "events": ["pull_request", "push", "repository"],
            "config": {
                "url": self.webhook_url,
                "content_type": "json",
                "secret": self.webhook_secret,
                "insecure_ssl": "0"
            }
        }
        
        try:
            # Update webhook
            webhook = self.github_client.update_webhook(repo_name, webhook_id, webhook_data)
            
            logger.info(f"Webhook {webhook_id} updated for repository {repo_name}")
            return webhook
        except Exception as e:
            logger.error(f"Error updating webhook {webhook_id} for repository {repo_name}: {e}")
            return {"error": str(e)}
    
    def delete_webhook(self, repo_name: str, webhook_id: int) -> bool:
        """
        Delete a webhook for a repository.
        
        Args:
            repo_name: Name of the repository
            webhook_id: ID of the webhook
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Deleting webhook {webhook_id} for repository {repo_name}")
        
        try:
            # Delete webhook
            self.github_client.delete_webhook(repo_name, webhook_id)
            
            logger.info(f"Webhook {webhook_id} deleted for repository {repo_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting webhook {webhook_id} for repository {repo_name}: {e}")
            return False
    
    def setup_webhooks_for_all_repos(self) -> Dict[str, Any]:
        """
        Set up webhooks for all repositories.
        
        Returns:
            Dictionary with results for each repository
        """
        logger.info("Setting up webhooks for all repositories")
        
        # Get repositories
        repos = self.github_client.get_repositories()
        
        # Set up webhooks
        results = {}
        for repo in repos:
            repo_name = repo.get("full_name")
            if repo_name:
                results[repo_name] = self.setup_webhook(repo_name)
        
        return results
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify a webhook signature.
        
        Args:
            payload: Webhook payload
            signature: Webhook signature
            
        Returns:
            True if the signature is valid, False otherwise
        """
        if not self.webhook_secret:
            logger.warning("No webhook secret set, skipping signature verification")
            return True
        
        try:
            # Calculate the expected signature
            hmac_obj = hmac.new(
                key=self.webhook_secret.encode(),
                msg=payload,
                digestmod=hashlib.sha256
            )
            expected_signature = f"sha256={hmac_obj.hexdigest()}"
            
            # Compare signatures
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
