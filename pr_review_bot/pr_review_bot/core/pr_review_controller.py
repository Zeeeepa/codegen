"""
PR Review Controller for PR Review Agent.
This module provides the main controller for coordinating the PR review process.
"""
import os
import logging
import traceback
from typing import Dict, List, Any, Optional, Tuple
from github import Github, PullRequest, Repository
from ..validator.documentation_service import DocumentationValidationService
from .github_client import GitHubClient
from ..utils.slack_notifier import SlackNotifier
from ..utils.storage_manager import StorageManager
from ..utils.ai_service import AIService

logger = logging.getLogger(__name__)

class PRReviewController:
    """
    Controller for coordinating the PR review process.
    
    Handles the workflow for reviewing PRs, validating them against requirements,
    and providing feedback.
    """
    
    def __init__(self, config: Dict[str, Any], repo_path: str):
        """
        Initialize the PR review controller.
        
        Args:
            config: Configuration dictionary
            repo_path: Path to the repository
        """
        self.config = config
        self.repo_path = repo_path
        
        # Initialize GitHub client
        github_token = config["github"]["token"]
        self.github_client = GitHubClient(github_token)
        
        # Initialize documentation validation service
        self.doc_validation_service = DocumentationValidationService(config, repo_path)
        
        # Initialize Slack notifier
        slack_enabled = config["notification"]["slack"]["enabled"]
        slack_token = config["notification"]["slack"]["token"]
        slack_channel = config["notification"]["slack"]["channel"]
        
        self.slack_notifier = SlackNotifier(
            enabled=slack_enabled,
            token=slack_token,
            default_channel=slack_channel
        )
