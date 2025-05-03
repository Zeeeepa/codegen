"""
Webhook Handler Module

This module provides functionality for handling webhooks from Git providers
and triggering analysis based on webhook events.
"""

import os
import json
import logging
import hmac
import hashlib
from typing import Dict, List, Optional, Any, Union, Set
from datetime import datetime

import requests
from fastapi import Request, HTTPException, status

from codegen_on_oss.analysis.project_manager import ProjectManager

logger = logging.getLogger(__name__)

class WebhookHandler:
    """
    Handles webhooks from Git providers and triggers analysis based on webhook events.
    """
    
    def __init__(self, project_manager: ProjectManager, server_url: str):
        """
        Initialize a new WebhookHandler.
        
        Args:
            project_manager: The ProjectManager instance to use
            server_url: The base URL of the server
        """
        self.project_manager = project_manager
        self.server_url = server_url
    
    async def handle_github_webhook(self, request: Request) -> Dict[str, Any]:
        """
        Handle a webhook from GitHub.
        
        Args:
            request: The FastAPI request object
            
        Returns:
            A dictionary with the result of handling the webhook
        """
        # Get the event type from the headers
        event_type = request.headers.get("X-GitHub-Event")
        
        if not event_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing X-GitHub-Event header"
            )
        
        # Get the payload
        payload = await request.json()
        
        # Get the repository URL
        repo_url = payload.get("repository", {}).get("html_url")
        
        if not repo_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing repository URL in payload"
            )
        
        # Get the project for the repository
        project = self.project_manager.get_project_by_repo_url(repo_url)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No project found for repository {repo_url}"
            )
        
        # Handle the event based on the event type
        if event_type == "push":
            return await self.handle_github_push(project.project_id, payload)
        elif event_type == "pull_request":
            return await self.handle_github_pull_request(project.project_id, payload)
        else:
            logger.info(f"Ignoring unsupported GitHub event type: {event_type}")
            return {
                "status": "ignored",
                "event_type": event_type,
                "reason": "Unsupported event type"
            }
    
    async def handle_github_push(self, project_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a push event from GitHub.
        
        Args:
            project_id: ID of the project
            payload: The webhook payload
        
        Returns:
            A dictionary with the result of handling the webhook
        """
        # Get the project
        project = self.project_manager.get_project(project_id)
        
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found"
            )
        
        # Get the branch name
        ref = payload.get("ref")
        
        if not ref:
            raise HTTPException(
                status_code=400,
                detail="Missing ref in payload"
            )
        
        # Extract the branch name from the ref
        branch = ref.replace("refs/heads/", "")
        
        # Get the commit hash
        commit_hash = payload.get("after")
        
        if not commit_hash:
            raise HTTPException(
                status_code=400,
                detail="Missing after (commit hash) in payload"
            )
        
        # Trigger analysis of the commit
        try:
            response = requests.post(
                f"{self.server_url}/analyze_commit",
                json={
                    "repo_url": project.repo_url,
                    "commit_hash": commit_hash
                }
            )
            
            response.raise_for_status()
            
            # Get the analysis result
            analysis_result = response.json()
            
            # Trigger webhooks for the project
            self.project_manager.trigger_webhooks_for_project(
                project_id=project_id,
                event="commit",
                payload={
                    "commit_hash": commit_hash,
                    "branch": branch,
                    "analysis_result": analysis_result
                }
            )
            
            return {
                "status": "success",
                "commit_hash": commit_hash,
                "branch": branch,
                "analysis_result": analysis_result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def handle_github_pull_request(self, project_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a pull request event from GitHub.
        
        Args:
            project_id: ID of the project
            payload: The webhook payload
        
        Returns:
            A dictionary with the result of handling the webhook
        """
        # Get the project
        project = self.project_manager.get_project(project_id)
        
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found"
            )
        
        # Get the pull request action
        action = payload.get("action")
        
        if not action:
            raise HTTPException(
                status_code=400,
                detail="Missing action in payload"
            )
        
        # Only handle opened, reopened, and synchronize events
        if action not in ["opened", "reopened", "synchronize"]:
            return {
                "status": "skipped",
                "reason": "Unsupported action"
            }
        
        # Get the pull request number
        pr_number = payload.get("pull_request", {}).get("number")
        
        if not pr_number:
            raise HTTPException(
                status_code=400,
                detail="Missing pull request number in payload"
            )
        
        # Trigger analysis of the pull request
        try:
            response = requests.post(
                f"{self.server_url}/analyze_pr",
                json={
                    "repo_url": project.repo_url,
                    "pr_number": pr_number
                }
            )
            
            response.raise_for_status()
            
            # Get the analysis result
            analysis_result = response.json()
            
            # Trigger webhooks for the project
            self.project_manager.trigger_webhooks_for_project(
                project_id=project_id,
                event="pr",
                payload={
                    "pr_number": pr_number,
                    "action": action,
                    "analysis_result": analysis_result
                }
            )
            
            return {
                "status": "success",
                "pr_number": pr_number,
                "action": action,
                "analysis_result": analysis_result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def handle_gitlab_webhook(self, request: Request) -> Dict[str, Any]:
        """
        Handle a webhook from GitLab.
        
        Args:
            request: The FastAPI request object
            
        Returns:
            A dictionary with the result of handling the webhook
        """
        # Get the event type from the headers
        event_type = request.headers.get("X-Gitlab-Event")
        
        if not event_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing X-Gitlab-Event header"
            )
        
        # Get the payload
        payload = await request.json()
        
        # Get the repository URL
        repo_url = payload.get("project", {}).get("web_url")
        
        if not repo_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing repository URL in payload"
            )
        
        # Get the project for the repository
        project = self.project_manager.get_project_by_repo_url(repo_url)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No project found for repository {repo_url}"
            )
        
        # Handle the event based on the event type
        if event_type == "Push Hook":
            return await self.handle_gitlab_push(project.project_id, payload)
        elif event_type == "Merge Request Hook":
            return await self.handle_gitlab_merge_request(project.project_id, payload)
        else:
            logger.info(f"Ignoring unsupported GitLab event type: {event_type}")
            return {
                "status": "ignored",
                "event_type": event_type,
                "reason": "Unsupported event type"
            }
    
    async def handle_gitlab_push(self, project_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a push event from GitLab.
        
        Args:
            project_id: ID of the project
            payload: The webhook payload
        
        Returns:
            A dictionary with the result of handling the webhook
        """
        # Get the project
        project = self.project_manager.get_project(project_id)
        
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found"
            )
        
        # Get the branch name
        ref = payload.get("ref")
        
        if not ref:
            raise HTTPException(
                status_code=400,
                detail="Missing ref in payload"
            )
        
        # Extract the branch name from the ref
        branch = ref.replace("refs/heads/", "")
        
        # Get the commit hash
        commit_hash = payload.get("after")
        
        if not commit_hash:
            raise HTTPException(
                status_code=400,
                detail="Missing after (commit hash) in payload"
            )
        
        # Trigger analysis of the commit
        try:
            response = requests.post(
                f"{self.server_url}/analyze_commit",
                json={
                    "repo_url": project.repo_url,
                    "commit_hash": commit_hash
                }
            )
            
            response.raise_for_status()
            
            # Get the analysis result
            analysis_result = response.json()
            
            # Trigger webhooks for the project
            self.project_manager.trigger_webhooks_for_project(
                project_id=project_id,
                event="commit",
                payload={
                    "commit_hash": commit_hash,
                    "branch": branch,
                    "analysis_result": analysis_result
                }
            )
            
            return {
                "status": "success",
                "commit_hash": commit_hash,
                "branch": branch,
                "analysis_result": analysis_result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def handle_gitlab_merge_request(self, project_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a merge request event from GitLab.
        
        Args:
            project_id: ID of the project
            payload: The webhook payload
        
        Returns:
            A dictionary with the result of handling the webhook
        """
        # Get the project
        project = self.project_manager.get_project(project_id)
        
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found"
            )
        
        # Get the merge request action
        action = payload.get("object_attributes", {}).get("action")
        
        if not action:
            raise HTTPException(
                status_code=400,
                detail="Missing action in payload"
            )
        
        # Only handle open, reopen, and update events
        if action not in ["open", "reopen", "update"]:
            return {
                "status": "skipped",
                "reason": "Unsupported action"
            }
        
        # Get the merge request number
        mr_number = payload.get("object_attributes", {}).get("iid")
        
        if not mr_number:
            raise HTTPException(
                status_code=400,
                detail="Missing merge request number in payload"
            )
        
        # Get the source branch and commit hash
        source_branch = payload.get("object_attributes", {}).get("source_branch")
        commit_hash = payload.get("object_attributes", {}).get("last_commit", {}).get("id")
        
        if not source_branch or not commit_hash:
            raise HTTPException(
                status_code=400,
                detail="Missing source branch or commit hash in payload"
            )
        
        # Trigger analysis of the merge request
        try:
            response = requests.post(
                f"{self.server_url}/compare_branches",
                json={
                    "repo_url": project.repo_url,
                    "base_branch": project.default_branch,
                    "compare_branch": source_branch
                }
            )
            
            response.raise_for_status()
            
            # Get the analysis result
            analysis_result = response.json()
            
            # Trigger webhooks for the project
            self.project_manager.trigger_webhooks_for_project(
                project_id=project_id,
                event="mr",
                payload={
                    "mr_number": mr_number,
                    "action": action,
                    "source_branch": source_branch,
                    "commit_hash": commit_hash,
                    "analysis_result": analysis_result
                }
            )
            
            return {
                "status": "success",
                "mr_number": mr_number,
                "action": action,
                "source_branch": source_branch,
                "commit_hash": commit_hash,
                "analysis_result": analysis_result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
