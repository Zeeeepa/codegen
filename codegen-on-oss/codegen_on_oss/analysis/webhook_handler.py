"""
Webhook Handler Module

This module provides functionality for handling webhooks from Git providers
and triggering analysis based on webhook events.
"""

import logging
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
        self.webhooks = {}
        self.handlers = {
            'github': self.handle_github_webhook,
            'gitlab': self.handle_gitlab_webhook,
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
        # ... rest of the method ...
    
    def handle_webhook(self, provider: str, payload: Dict[str, Any], headers: Dict[str, str]) -> None:
        """
        Handle a webhook from a Git provider.
        
        Args:
            provider: The Git provider (github, gitlab, etc.).
            payload: The webhook payload.
            headers: The webhook headers.
        """
        # ... rest of the method ...
