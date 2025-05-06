"""
GitHub PR Client Module

This module provides a client for interacting with GitHub's API to get PR data.
"""

import logging
from typing import Dict, List, Optional, Any

from graph_sitter.git.clients.github_client import GithubClient as GSGithubClient
from ..github.models import PullRequestContext, PRPartContext, FileChange, PRDiff

logger = logging.getLogger(__name__)


class GitHubClient:
    """
    Client for interacting with GitHub's API to get PR data.
    """
    
    def __init__(self, github_client: GSGithubClient):
        """
        Initialize a new GitHub client.
        
        Args:
            github_client: graph-sitter GitHub client
        """
        self.github_client = github_client
    
    def get_pr(self, pr_number: int, repository: str) -> PullRequestContext:
        """
        Get a pull request by number.
        
        Args:
            pr_number: Number of the PR to get
            repository: Full name of the repository (e.g., "owner/repo")
            
        Returns:
            PullRequestContext for the PR
        """
        logger.info(f"Getting PR #{pr_number} from {repository}")
        
        # Get the PR from GitHub
        pr = self.github_client.get_pull_request(repository, pr_number)
        
        # Create base and head contexts
        base = PRPartContext(
            ref=pr.base.ref,
            sha=pr.base.sha,
            repo_name=pr.base.repo.full_name,
        )
        
        head = PRPartContext(
            ref=pr.head.ref,
            sha=pr.head.sha,
            repo_name=pr.head.repo.full_name,
        )
        
        # Create user dict
        user = {
            "login": pr.user.login,
            "id": pr.user.id,
            "html_url": pr.user.html_url,
        }
        
        # Create PR context
        return PullRequestContext(
            number=pr.number,
            title=pr.title,
            body=pr.body or "",
            state=pr.state,
            base=base,
            head=head,
            user=user,
            html_url=pr.html_url,
        )
    
    def get_pr_diff(self, pr_number: int, repository: str) -> PRDiff:
        """
        Get the diff for a pull request.
        
        Args:
            pr_number: Number of the PR to get the diff for
            repository: Full name of the repository (e.g., "owner/repo")
            
        Returns:
            PRDiff for the PR
        """
        logger.info(f"Getting diff for PR #{pr_number} from {repository}")
        
        # Get the PR from GitHub
        pr = self.github_client.get_pull_request(repository, pr_number)
        
        # Get the files from the PR
        files = []
        total_additions = 0
        total_deletions = 0
        total_changes = 0
        
        for file in pr.get_files():
            file_change = FileChange(
                filename=file.filename,
                status=file.status,
                additions=file.additions,
                deletions=file.deletions,
                changes=file.changes,
                patch=file.patch,
            )
            
            # Get file content before and after if available
            try:
                if file.status != "added":
                    content_before = self.github_client.get_file_content(
                        repository, file.filename, pr.base.sha
                    )
                    file_change.content_before = content_before
                
                if file.status != "removed":
                    content_after = self.github_client.get_file_content(
                        repository, file.filename, pr.head.sha
                    )
                    file_change.content_after = content_after
            except Exception as e:
                logger.warning(f"Error getting file content: {e}")
            
            files.append(file_change)
            total_additions += file.additions
            total_deletions += file.deletions
            total_changes += file.changes
        
        return PRDiff(
            files=files,
            total_additions=total_additions,
            total_deletions=total_deletions,
            total_changes=total_changes,
        )
    
    def comment_on_pr(self, pr_number: int, repository: str, body: str) -> None:
        """
        Add a comment to a pull request.
        
        Args:
            pr_number: Number of the PR to comment on
            repository: Full name of the repository (e.g., "owner/repo")
            body: Comment text
        """
        logger.info(f"Commenting on PR #{pr_number} in {repository}")
        
        # Get the PR from GitHub
        pr = self.github_client.get_pull_request(repository, pr_number)
        
        # Add the comment
        pr.create_issue_comment(body)

