"""
Webhook handler module for the PR Review Bot.
Handles GitHub webhook events for pull requests and repositories.
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

# Configure logging
logger = logging.getLogger(__name__)

class WebhookHandler:
    """
    Handler for GitHub webhook events.
    Processes webhook events for pull requests and repositories.
    """
    
    def __init__(self, github_client: GitHubClient, pr_reviewer: PRReviewer, webhook_secret: Optional[str] = None):
        """
        Initialize the webhook handler.
        
        Args:
            github_client: GitHub client
            pr_reviewer: PR reviewer
            webhook_secret: Secret for GitHub webhook verification
        """
        self.github_client = github_client
        self.pr_reviewer = pr_reviewer
        self.webhook_secret = webhook_secret
    
    async def verify_signature(self, request: Request, x_hub_signature_256: Optional[str] = None) -> bool:
        """
        Verify the GitHub webhook signature.
        
        Args:
            request: FastAPI request
            x_hub_signature_256: GitHub signature header
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.webhook_secret or not x_hub_signature_256:
            return True
        
        body = await request.body()
        signature = hmac.new(
            self.webhook_secret.encode(),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()
        
        expected_signature = f"sha256={signature}"
        
        if not hmac.compare_digest(expected_signature, x_hub_signature_256):
            logger.warning("Invalid webhook signature")
            return False
        
        return True
    
    async def handle_webhook(self, request: Request) -> Dict[str, Any]:
        """
        Handle a GitHub webhook event.
        
        Args:
            request: FastAPI request
            
        Returns:
            Response data
        """
        # Verify signature
        x_hub_signature_256 = request.headers.get("X-Hub-Signature-256")
        if not await self.verify_signature(request, x_hub_signature_256):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Get event type
        event_type = request.headers.get("X-GitHub-Event", "")
        logger.info(f"Received {event_type} event")
        
        # Parse request body
        body = await request.body()
        event = json.loads(body)
        
        # Handle different event types
        if event_type == "pull_request":
            return await self.handle_pull_request_event(event)
        elif event_type == "repository":
            return await self.handle_repository_event(event)
        elif event_type == "push":
            return await self.handle_push_event(event)
        else:
            logger.info(f"Ignoring unsupported event type: {event_type}")
            return {"status": "ignored", "event_type": event_type}
    
    async def handle_pull_request_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a pull request event.
        
        Args:
            event: Event data
            
        Returns:
            Response data
        """
        action = event.get("action", "")
        logger.info(f"Pull request {action} event")
        
        # Get PR details
        pr_number = event["pull_request"]["number"]
        repo_name = event["repository"]["full_name"]
        
        # Process the event based on action
        if action in ["opened", "synchronize", "reopened"]:
            logger.info(f"Reviewing PR #{pr_number} in {repo_name}")
            
            try:
                # Review the PR
                result = self.pr_reviewer.review_pr(repo_name, pr_number)
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Error reviewing PR: {e}")
                return {"status": "error", "message": str(e)}
        
        # Handle labeled events
        elif action == "labeled":
            label_name = event["label"]["name"]
            
            if label_name == "Codegen":
                logger.info(f"PR #{pr_number} labeled with Codegen, starting review")
                
                try:
                    # Review the PR
                    result = self.pr_reviewer.review_pr(repo_name, pr_number)
                    return {"status": "success", "result": result}
                except Exception as e:
                    logger.error(f"Error reviewing PR: {e}")
                    return {"status": "error", "message": str(e)}
        
        # Handle unlabeled events
        elif action == "unlabeled":
            label_name = event["label"]["name"]
            
            if label_name == "Codegen":
                logger.info(f"PR #{pr_number} unlabeled, removing bot comments")
                
                try:
                    # Get repository and PR
                    repo = self.github_client.get_repository(repo_name)
                    pr = self.github_client.get_pull_request(repo, pr_number)
                    
                    # Remove bot comments
                    removed_count = self.github_client.remove_bot_comments(pr)
                    
                    return {
                        "status": "success",
                        "pr_number": pr_number,
                        "repo_name": repo_name,
                        "removed_comments": removed_count
                    }
                except Exception as e:
                    logger.error(f"Error removing bot comments: {e}")
                    return {"status": "error", "message": str(e)}
        
        return {"status": "ignored", "action": action}
    
    async def handle_repository_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a repository event.
        
        Args:
            event: Event data
            
        Returns:
            Response data
        """
        action = event.get("action", "")
        logger.info(f"Repository {action} event")
        
        # Handle repository creation
        if action == "created":
            repo_name = event["repository"]["full_name"]
            logger.info(f"New repository created: {repo_name}")
            
            # No specific action needed here, as the monitors will pick up the repository
            return {"status": "success", "message": f"Repository {repo_name} will be monitored"}
        
        return {"status": "ignored", "action": action}
    
    async def handle_push_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a push event.
        
        Args:
            event: Event data
            
        Returns:
            Response data
        """
        ref = event.get("ref", "")
        repo_name = event["repository"]["full_name"]
        
        # Extract branch name from ref
        branch_name = ref.replace("refs/heads/", "")
        
        logger.info(f"Push to {branch_name} in {repo_name}")
        
        # No specific action needed here, as the monitors will handle new branches
        return {"status": "success", "message": f"Push to {branch_name} in {repo_name} received"}
