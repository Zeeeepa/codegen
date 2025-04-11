"""
PR reviewer module for the PR Review Bot.
Provides functionality for reviewing pull requests using AI.
"""

import os
import logging
import traceback
from typing import Dict, List, Any, Optional, Tuple
from github.Repository import Repository
from github.PullRequest import PullRequest

# Import compatibility layer
from .compatibility import (
    Codebase, 
    HAS_CODEGEN, 
    HAS_LANGCHAIN,
    ChatPromptTemplate,
    ChatAnthropic,
    ChatOpenAI
)

# Import PR Review Controller
from .pr_review_controller import PRReviewController

# Import Slack notifier
from ..utils.slack_notifier import SlackNotifier

logger = logging.getLogger(__name__)

class PRReviewer:
    """
    PR reviewer for the PR Review Bot.
    
    This class provides functionality for reviewing pull requests using AI.
    It integrates with the PR Review Controller to coordinate the review process.
    """
    
    def __init__(self, github_token: str, slack_channel: Optional[str] = None):
        """
        Initialize the PR reviewer.
        
        Args:
            github_token: GitHub API token
            slack_channel: Slack channel to send notifications to
        """
        self.github_token = github_token
        self.github = Github(github_token)
        self.slack_channel = slack_channel
        
        # Initialize Slack notifier if channel is provided
        self.slack_notifier = None
        if slack_channel:
            slack_token = os.environ.get("SLACK_BOT_TOKEN")
            if slack_token:
                self.slack_notifier = SlackNotifier(slack_token, slack_channel)
            else:
                logger.warning("SLACK_BOT_TOKEN not set, Slack notifications disabled")
        
        # Initialize PR Review Controller
        config = {
            "github": {
                "token": github_token,
                "auto_merge": False,
                "auto_review": True
            },
            "validation": {
                "documentation": {
                    "enabled": True,
                    "files": ["README.md", "STRUCTURE.md", "PLAN.md"],
                    "required": False
                }
            },
            "notification": {
                "slack": {
                    "enabled": self.slack_notifier is not None,
                    "token": os.environ.get("SLACK_BOT_TOKEN", ""),
                    "channel": slack_channel or ""
                }
            },
            "storage": {
                "type": "local",
                "path": "data"
            },
            "ai": {
                "provider": "anthropic",
                "model": "claude-3-opus-20240229",
                "api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
                "temperature": 0.2,
                "max_tokens": 4000
            }
        }
        
        self.pr_review_controller = PRReviewController(config, os.getcwd())
    
    def review_pr(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """
        Review a pull request using AI.
        
        Args:
            repo_name: Repository name in format "owner/repo"
            pr_number: Pull request number
            
        Returns:
            Result of the review
        """
        try:
            logger.info(f"Reviewing PR {repo_name}#{pr_number}")
            
            # Use the PR Review Controller to review the PR
            review_results = self.pr_review_controller.review_pr(repo_name, pr_number)
            
            return review_results
            
        except Exception as e:
            logger.error(f"Error reviewing PR {repo_name}#{pr_number}: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return error result
            return {
                "status": "error",
                "error": str(e),
                "repo_name": repo_name,
                "pr_number": pr_number
            }
