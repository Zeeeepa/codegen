"""
Compatibility layer for the PR Review Bot.
Provides compatibility with older versions of the codebase.
"""

import os
import sys
import logging
from typing import Dict, Any, Optional, List

# Configure logging
logger = logging.getLogger(__name__)

class MockCodebase:
    """
    Mock implementation of the Codebase class from codegen.sdk.core.codebase.
    Provides basic functionality for PR review operations.
    """
    
    def __init__(self, repo_path: str, language: str = "python"):
        """
        Initialize the mock codebase.
        
        Args:
            repo_path: Repository path in format "owner/repo"
            language: Programming language of the codebase
        """
        self.repo_path = repo_path
        self.language = language
        self.repo_operator = MockRepoOperator(repo_path)

class MockRepoOperator:
    """
    Mock implementation of the RepoOperator class.
    Provides basic functionality for PR operations.
    """
    
    def __init__(self, repo_path: str):
        """
        Initialize the mock repo operator.
        
        Args:
            repo_path: Repository path in format "owner/repo"
        """
        self.repo_path = repo_path
        self.github_token = os.environ.get("GITHUB_TOKEN", "")
        
        # Import GitHub only when needed
        from github import Github
        self.github = Github(self.github_token)
        self.repo = self.github.get_repo(repo_path)
    
    def create_pr_comment(self, pr_number: int, comment: str):
        """
        Create a comment on a pull request.
        
        Args:
            pr_number: Pull request number
            comment: Comment text
            
        Returns:
            Created comment
        """
        pr = self.repo.get_pull(pr_number)
        return pr.create_issue_comment(comment)
    
    def get_pr(self, pr_number: int):
        """
        Get a pull request.
        
        Args:
            pr_number: Pull request number
            
        Returns:
            Pull request
        """
        return self.repo.get_pull(pr_number)
    
    def merge_pr(self, pr_number: int, commit_title: str, commit_message: str, merge_method: str = "merge"):
        """
        Merge a pull request.
        
        Args:
            pr_number: Pull request number
            commit_title: Commit title
            commit_message: Commit message
            merge_method: Merge method
            
        Returns:
            Merge result
        """
        pr = self.repo.get_pull(pr_number)
        return pr.merge(
            commit_title=commit_title,
            commit_message=commit_message,
            merge_method=merge_method
        )

def create_mock_codebase(repo_path: str, language: str = "python"):
    """
    Create a mock codebase instance.
    
    Args:
        repo_path: Repository path in format "owner/repo"
        language: Programming language of the codebase
        
    Returns:
        Mock codebase instance
    """
    return MockCodebase(repo_path, language)

def import_or_mock(module_name: str, mock_obj=None):
    """
    Try to import a module, or return a mock object if import fails.
    
    Args:
        module_name: Module name to import
        mock_obj: Mock object to return if import fails
        
    Returns:
        Imported module or mock object
    """
    try:
        return __import__(module_name, fromlist=[""])
    except ImportError:
        logger.warning(f"Could not import {module_name}, using mock implementation")
        return mock_obj

# Try to import Codebase from codegen.sdk.core.codebase
try:
    from codegen.sdk.core.codebase import Codebase
    HAS_CODEGEN = True
except ImportError:
    logger.warning("Could not import codegen.sdk.core.codebase, using mock implementation")
    Codebase = MockCodebase
    HAS_CODEGEN = False

# Try to import CodeAgent from agentgen.agents.code_agent
try:
    from agentgen.agents.code_agent import CodeAgent
    from agentgen.extensions.langchain.tools import (
        GithubViewPRTool,
        GithubCreatePRCommentTool,
        GithubCreatePRReviewCommentTool,
    )
    HAS_AGENTGEN = True
except ImportError:
    logger.warning("Could not import agentgen.agents.code_agent, AI review will be limited")
    CodeAgent = None
    GithubViewPRTool = None
    GithubCreatePRCommentTool = None
    GithubCreatePRReviewCommentTool = None
    HAS_AGENTGEN = False
