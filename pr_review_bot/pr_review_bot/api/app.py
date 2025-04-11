"""
FastAPI application for the PR Review Bot.
Provides API endpoints for webhook events and manual PR reviews.
"""

import os
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Response, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..core.github_client import GitHubClient
from ..core.pr_reviewer import PRReviewer
from ..core.pr_review_controller import PRReviewController
from .webhook_handler import WebhookHandler

logger = logging.getLogger(__name__)

class PRReviewRequest(BaseModel):
    """
    Request model for manual PR review.
    """
    repo_name: str
    pr_number: int

class PRReviewBotApp:
    """
    FastAPI application for the PR Review Bot.
    
    This class provides API endpoints for webhook events and manual PR reviews.
    """
    
    def __init__(self, github_token: Optional[str] = None, webhook_secret: Optional[str] = None, slack_channel: Optional[str] = None):
        """
        Initialize the PR Review Bot API.
        
        Args:
            github_token: GitHub API token
            webhook_secret: Secret for webhook verification
            slack_channel: Slack channel to send notifications to
        """
        # Get tokens from environment variables if not provided
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        self.webhook_secret = webhook_secret or os.environ.get("GITHUB_WEBHOOK_SECRET")
        self.slack_channel = slack_channel or os.environ.get("SLACK_CHANNEL")
        
        if not self.github_token:
            logger.warning("No GitHub token provided, some functionality may be limited")
        
        self.app = FastAPI(
            title="PR Review Bot API",
            description="API for the PR Review Bot",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize GitHub client
        self.github_client = GitHubClient(self.github_token) if self.github_token else None
        
        # Initialize PR reviewer
        self.pr_reviewer = PRReviewer(self.github_token, slack_channel=self.slack_channel) if self.github_token else None
        
        # Initialize webhook handler
        self.webhook_handler = WebhookHandler(
            github_client=self.github_client,
            pr_reviewer=self.pr_reviewer,
            webhook_secret=self.webhook_secret
        ) if self.github_client and self.pr_reviewer else None
        
        # Register routes
        self.register_routes()
    
    def register_routes(self):
        """
        Register API routes.
        """
        # Health check endpoint
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "github_client": self.github_client is not None,
                "pr_reviewer": self.pr_reviewer is not None,
                "webhook_handler": self.webhook_handler is not None
            }
        
        # Webhook endpoint
        @self.app.post("/webhook")
        async def webhook(request: Request):
            if not self.webhook_handler:
                logger.error("Webhook handler not initialized")
                raise HTTPException(status_code=500, detail="Webhook handler not initialized")
            
            return await self.webhook_handler.handle_webhook(request)
        
        # Manual PR review endpoint
        @self.app.post("/api/reviews/manual")
        async def manual_review(request: PRReviewRequest):
            if not self.pr_reviewer:
                logger.error("PR reviewer not initialized")
                raise HTTPException(status_code=500, detail="PR reviewer not initialized")
            
            try:
                # Use the PR Review Controller to review the PR
                result = self.pr_reviewer.pr_review_controller.review_pr(
                    request.repo_name,
                    request.pr_number
                )
                
                return {
                    "status": "success",
                    "message": f"PR {request.repo_name}#{request.pr_number} review triggered",
                    "result": result
                }
            except Exception as e:
                logger.error(f"Error reviewing PR: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Get PR review status endpoint
        @self.app.get("/api/reviews/{repo_name}/{pr_number}")
        async def get_review_status(repo_name: str, pr_number: int):
            if not self.pr_reviewer:
                logger.error("PR reviewer not initialized")
                raise HTTPException(status_code=500, detail="PR reviewer not initialized")
            
            try:
                # Get the review status from the storage manager
                storage_manager = self.pr_reviewer.pr_review_controller.storage_manager
                review_results = storage_manager.get_review_results(repo_name, pr_number)
                
                if not review_results:
                    return {
                        "status": "not_found",
                        "message": f"No review found for PR {repo_name}#{pr_number}"
                    }
                
                return {
                    "status": "success",
                    "review": review_results
                }
            except Exception as e:
                logger.error(f"Error getting review status: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Get documentation validation status endpoint
        @self.app.get("/api/docs/validate/{repo_name}/{pr_number}")
        async def validate_documentation(repo_name: str, pr_number: int):
            if not self.pr_reviewer:
                logger.error("PR reviewer not initialized")
                raise HTTPException(status_code=500, detail="PR reviewer not initialized")
            
            try:
                # Validate the PR against documentation requirements
                doc_validation_service = self.pr_reviewer.pr_review_controller.doc_validation_service
                validation_results = doc_validation_service.validate_pr(repo_name, pr_number)
                
                return {
                    "status": "success",
                    "validation": validation_results
                }
            except Exception as e:
                logger.error(f"Error validating documentation: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def get_app(self):
        """
        Get the FastAPI application.
        
        Returns:
            FastAPI application
        """
        return self.app

# Create the application instance with environment variables
github_token = os.environ.get("GITHUB_TOKEN")
webhook_secret = os.environ.get("GITHUB_WEBHOOK_SECRET")
slack_channel = os.environ.get("SLACK_CHANNEL")

# Only create the app instance if we have a GitHub token
if github_token:
    app_instance = PRReviewBotApp(
        github_token=github_token,
        webhook_secret=webhook_secret,
        slack_channel=slack_channel
    )
    app = app_instance.get_app()
else:
    # Create a minimal app for testing
    app = FastAPI(
        title="PR Review Bot API (Limited)",
        description="Limited API for the PR Review Bot (No GitHub token provided)",
        version="1.0.0"
    )
    
    @app.get("/health")
    async def health_check():
        return {
            "status": "limited",
            "message": "No GitHub token provided, functionality is limited"
        }
