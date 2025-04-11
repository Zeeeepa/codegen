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
    
    def __init__(self, github_token: str, webhook_secret: Optional[str] = None, slack_channel: Optional[str] = None):
        """
        Initialize the PR Review Bot API.
        
        Args:
            github_token: GitHub API token
            webhook_secret: Secret for webhook verification
            slack_channel: Slack channel to send notifications to
        """
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
        self.github_client = GitHubClient(github_token)
        
        # Initialize PR reviewer
        self.pr_reviewer = PRReviewer(github_token, slack_channel=slack_channel)
        
        # Initialize webhook handler
        self.webhook_handler = WebhookHandler(
            github_client=self.github_client,
            pr_reviewer=self.pr_reviewer,
            webhook_secret=webhook_secret
        )
        
        # Register routes
        self.register_routes()
    
    def register_routes(self):
        """
        Register API routes.
        """
        # Health check endpoint
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy"}
        
        # Webhook endpoint
        @self.app.post("/webhook")
        async def webhook(request: Request):
            return await self.webhook_handler.handle_webhook(request)
        
        # Manual PR review endpoint
        @self.app.post("/api/reviews/manual")
        async def manual_review(request: PRReviewRequest):
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

# Create the application
app_instance = PRReviewBotApp()
app = app_instance.get_app()
