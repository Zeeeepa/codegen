"""
FastAPI application for the PR Review Bot.
Provides endpoints for handling GitHub webhook events.
"""

import os
import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, Response, HTTPException, Depends

from ..core.github_client import GitHubClient
from ..core.pr_reviewer import PRReviewer
from .webhook_handler import WebhookHandler

# Configure logging
logger = logging.getLogger(__name__)

class PRReviewBotApp:
    """
    FastAPI application for the PR Review Bot.
    """
    
    def __init__(self):
        """
        Initialize the FastAPI application.
        """
        self.app = FastAPI(title="PR Review Bot")
        self.setup_dependencies()
        self.setup_routes()
    
    def setup_dependencies(self):
        """
        Set up dependencies for the application.
        """
        # Get GitHub token
        github_token = os.environ.get("GITHUB_TOKEN")
        if not github_token:
            logger.error("GITHUB_TOKEN environment variable is required")
            raise ValueError("GITHUB_TOKEN environment variable is required")
        
        # Get webhook secret
        webhook_secret = os.environ.get("WEBHOOK_SECRET", "")
        
        # Create GitHub client
        self.github_client = GitHubClient(github_token)
        
        # Create PR reviewer
        self.pr_reviewer = PRReviewer(github_token)
        
        # Create webhook handler
        self.webhook_handler = WebhookHandler(
            github_client=self.github_client,
            pr_reviewer=self.pr_reviewer,
            webhook_secret=webhook_secret
        )
    
    def setup_routes(self):
        """
        Set up routes for the application.
        """
        @self.app.get("/")
        async def root():
            """
            Root endpoint for the PR Review Bot.
            """
            return {"message": "PR Review Bot is running"}
        
        @self.app.post("/webhook")
        async def webhook(request: Request):
            """
            GitHub webhook endpoint.
            """
            return await self.webhook_handler.handle_webhook(request)
        
        @self.app.get("/health")
        async def health():
            """
            Health check endpoint.
            """
            return {"status": "healthy"}

# Create the application
app_instance = PRReviewBotApp()
app = app_instance.app
