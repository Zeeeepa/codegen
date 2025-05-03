"""
Webhook Handler Module

This module provides functionality for handling webhooks from Git providers
and triggering analysis based on webhook events.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

import requests
from fastapi import Request, HTTPException, status

from codegen_on_oss.analysis.project_manager import ProjectManager

logger = logging.getLogger(__name__)

class WebhookHandler:
    """
    Handler for webhooks from Git providers.
    """
    
    def __init__(self, project_manager: 'ProjectManager') -> None:
        """
        Initialize the webhook handler.
        
        Args:
            project_manager: The project manager instance.
        """
        self.project_manager = project_manager
        self.webhooks: Dict[str, Dict[str, Any]] = {}
        self.handlers: Dict[str, Any] = {
            'github': self.handle_webhook,
            'gitlab': self.handle_webhook,
        }
    
    def register_webhook(self, project_id: str, webhook_url: str, events: List[str], secret: Optional[str] = None) -> str:
        """
        Register a webhook for a project.
        
        Args:
            project_id: The ID of the project.
            webhook_url: The URL to send webhook notifications to.
            events: The events to trigger the webhook.
            secret: The secret to sign webhook payloads with.
            
        Returns:
            The ID of the registered webhook.
        """
        # Generate a unique ID for the webhook
        webhook_id = str(uuid.uuid4())
        
        # Create the webhook
        self.webhooks[webhook_id] = {
            'project_id': project_id,
            'webhook_url': webhook_url,
            'events': events,
            'secret': secret,
            'created_at': datetime.now().isoformat(),
        }
        
        return webhook_id
    
    def handle_webhook(self, provider: str, payload: Dict[str, Any], headers: Dict[str, str]) -> None:
        """
        Handle a webhook from a Git provider.
        
        Args:
            provider: The Git provider (github, gitlab, etc.).
            payload: The webhook payload.
            headers: The webhook headers.
        """
        # Get the event type from the headers
        event_type = headers.get(f"X-{provider.capitalize()}-Event")
        
        if not event_type:
            logger.warning(f"Missing event type header for {provider} webhook")
            return
        
        # Get the repository URL from the payload
        repo_url = None
        
        if provider == 'github':
            repo_url = payload.get("repository", {}).get("html_url")
        elif provider == 'gitlab':
            repo_url = payload.get("project", {}).get("web_url")
        
        if not repo_url:
            logger.warning(f"Missing repository URL in {provider} webhook payload")
            return
        
        # Log the webhook
        logger.info(f"Received {provider} webhook for {repo_url}, event: {event_type}")
