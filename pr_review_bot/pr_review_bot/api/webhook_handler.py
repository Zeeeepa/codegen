"""
Webhook handler for the PR Review Bot.
Handles GitHub webhook events.
"""

import os
import json
import logging
import hmac
import hashlib
from typing import Dict, Any, Optional
from fastapi import Request, Response, HTTPException, Depends, Header

from ..core.github_client import GitHubClient
from ..core.pr_reviewer import PRReviewer
from ..core.pr_review_controller import PRReviewController

logger = logging.getLogger(__name__)

class WebhookHandler:
    """
    Handler for GitHub webhook events.
    
    This class processes webhook events from GitHub and triggers the appropriate actions.
    """
    
    def __init__(self, github_client: GitHubClient, pr_reviewer: PRReviewer, webhook_secret: Optional[str] = None):
        """
        Initialize the webhook handler.
        
        Args:
            github_client: GitHub client
            pr_reviewer: PR reviewer
            webhook_secret: Secret for webhook verification
        """
        self.github_client = github_client
        self.pr_reviewer = pr_reviewer
        self.webhook_secret = webhook_secret
        
        # Get the PR Review Controller from the PR Reviewer
        self.pr_review_controller = self.pr_reviewer.pr_review_controller
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify the webhook signature.
        
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
            logger.error(f"Error verifying signature: {e}")
            return False
    
    async def handle_webhook(self, request: Request) -> Dict[str, Any]:
        """
        Handle a webhook event from GitHub.
        
        Args:
            request: FastAPI request
            
        Returns:
            Response data
        """
        # Get the event type
        event_type = request.headers.get("X-GitHub-Event")
        if not event_type:
            logger.warning("No event type in webhook")
            return {"status": "error", "message": "No event type"}
        
        # Get the signature
        signature = request.headers.get("X-Hub-Signature-256")
        if not signature and self.webhook_secret:
            logger.warning("No signature in webhook")
            return {"status": "error", "message": "No signature"}
        
        # Get the payload
        payload_bytes = await request.body()
        
        # Verify the signature
        if signature and not self.verify_signature(payload_bytes, signature):
            logger.warning("Invalid signature in webhook")
            return {"status": "error", "message": "Invalid signature"}
        
        # Parse the payload
        try:
            payload = json.loads(payload_bytes)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook payload")
            return {"status": "error", "message": "Invalid JSON"}
        
        # Handle the event
        logger.info(f"Received webhook event: {event_type}")
        
        if event_type == "ping":
            return {"status": "success", "message": "Pong!"}
        
        elif event_type == "pull_request":
            action = payload.get("action")
            pr = payload.get("pull_request", {})
            repo = payload.get("repository", {})
            
            if not pr or not repo:
                logger.warning("Missing PR or repo data in webhook")
                return {"status": "error", "message": "Missing PR or repo data"}
            
            pr_number = pr.get("number")
            repo_name = repo.get("full_name")
            
            if not pr_number or not repo_name:
                logger.warning("Missing PR number or repo name in webhook")
                return {"status": "error", "message": "Missing PR number or repo name"}
            
            logger.info(f"Received PR event: {action} for {repo_name}#{pr_number}")
            
            # Handle PR events
            if action in ["opened", "reopened", "synchronize"]:
                logger.info(f"Reviewing PR {repo_name}#{pr_number}")
                
                # Use the PR Review Controller to handle the PR event
                result = self.pr_review_controller.handle_pr_event("pull_request", payload)
                
                return {
                    "status": "success",
                    "message": f"PR {repo_name}#{pr_number} review triggered",
                    "result": result
                }
            
            elif action == "closed":
                if pr.get("merged"):
                    logger.info(f"PR {repo_name}#{pr_number} was merged")
                    return {
                        "status": "success",
                        "message": f"PR {repo_name}#{pr_number} was merged"
                    }
                else:
                    logger.info(f"PR {repo_name}#{pr_number} was closed without merging")
                    return {
                        "status": "success",
                        "message": f"PR {repo_name}#{pr_number} was closed without merging"
                    }
            
            else:
                logger.info(f"Ignoring PR action: {action}")
                return {
                    "status": "ignored",
                    "message": f"Ignoring PR action: {action}"
                }
        
        elif event_type == "push":
            ref = payload.get("ref")
            repo = payload.get("repository", {})
            
            if not ref or not repo:
                logger.warning("Missing ref or repo data in webhook")
                return {"status": "error", "message": "Missing ref or repo data"}
            
            repo_name = repo.get("full_name")
            
            if not repo_name:
                logger.warning("Missing repo name in webhook")
                return {"status": "error", "message": "Missing repo name"}
            
            # Extract branch name from ref
            branch = ref.replace("refs/heads/", "")
            
            logger.info(f"Received push event for {repo_name}:{branch}")
            
            # No specific action needed here, as the monitors will handle new branches
            return {
                "status": "success",
                "message": f"Push event for {repo_name}:{branch} received"
            }
        
        elif event_type == "repository":
            action = payload.get("action")
            repo = payload.get("repository", {})
            
            if not action or not repo:
                logger.warning("Missing action or repo data in webhook")
                return {"status": "error", "message": "Missing action or repo data"}
            
            repo_name = repo.get("full_name")
            
            if not repo_name:
                logger.warning("Missing repo name in webhook")
                return {"status": "error", "message": "Missing repo name"}
            
            logger.info(f"Received repository event: {action} for {repo_name}")
            
            # No specific action needed here, as the monitors will pick up the repository
            return {
                "status": "success",
                "message": f"Repository event for {repo_name} received"
            }
        
        else:
            logger.info(f"Ignoring event type: {event_type}")
            return {
                "status": "ignored",
                "message": f"Ignoring event type: {event_type}"
            }
