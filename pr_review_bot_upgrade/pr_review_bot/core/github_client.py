"""
GitHub client module for the PR Review Bot.
Provides functionality for interacting with GitHub repositories.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from github import Github
from github.Repository import Repository
from github.PullRequest import PullRequest
from github.Branch import Branch
from github.ContentFile import ContentFile
from github.GithubException import GithubException

# Configure logging
logger = logging.getLogger(__name__)

class GitHubClient:
    """
    Client for interacting with GitHub repositories.
    Provides methods for accessing repositories, pull requests, and branches.
    """
    
    def __init__(self, token: str):
        """
        Initialize the GitHub client.
        
        Args:
            token: GitHub API token
        """
        self.token = token
        self.client = Github(token)
    
    def get_repository(self, repo_name: str) -> Repository:
        """
        Get a GitHub repository instance.
        
        Args:
            repo_name: Repository name in format "owner/repo"
            
        Returns:
            Repository object
        """
        logger.info(f"Getting repository {repo_name}")
        return self.client.get_repo(repo_name)
    
    def get_pull_request(self, repo: Repository, pr_number: int) -> PullRequest:
        """
        Get a GitHub pull request instance.
        
        Args:
            repo: Repository object
            pr_number: Pull request number
            
        Returns:
            PullRequest object
        """
        logger.info(f"Getting PR #{pr_number} from {repo.full_name}")
        return repo.get_pull(pr_number)
    
    def get_all_repositories(self) -> List[Repository]:
        """
        Get all repositories accessible by the GitHub token.
        
        Returns:
            List of Repository objects
        """
        logger.info("Fetching all accessible repositories")
        return list(self.client.get_user().get_repos())
    
    def get_repository_branches(self, repo: Repository) -> List[Branch]:
        """
        Get all branches for a repository.
        
        Args:
            repo: Repository object
            
        Returns:
            List of Branch objects
        """
        logger.info(f"Getting branches for {repo.full_name}")
        return list(repo.get_branches())
    
    def get_branch(self, repo: Repository, branch_name: str) -> Branch:
        """
        Get a specific branch from a repository.
        
        Args:
            repo: Repository object
            branch_name: Branch name
            
        Returns:
            Branch object
        """
        logger.info(f"Getting branch {branch_name} from {repo.full_name}")
        return repo.get_branch(branch_name)
    
    def get_file_content(self, repo: Repository, file_path: str, ref: Optional[str] = None) -> Optional[str]:
        """
        Get the content of a file from a repository.
        
        Args:
            repo: Repository object
            file_path: Path to the file
            ref: Optional reference (branch, tag, or commit SHA)
            
        Returns:
            File content as string, or None if file doesn't exist
        """
        logger.info(f"Getting content of {file_path} from {repo.full_name}")
        try:
            content_file = repo.get_contents(file_path, ref=ref)
            if isinstance(content_file, list):
                logger.warning(f"{file_path} is a directory, not a file")
                return None
            return content_file.decoded_content.decode('utf-8')
        except GithubException as e:
            if e.status == 404:
                logger.warning(f"File {file_path} not found in {repo.full_name}")
                return None
            raise
    
    def create_pull_request(self, repo: Repository, title: str, body: str, 
                           head: str, base: str) -> PullRequest:
        """
        Create a new pull request.
        
        Args:
            repo: Repository object
            title: PR title
            body: PR description
            head: Head branch
            base: Base branch
            
        Returns:
            Created PullRequest object
        """
        logger.info(f"Creating PR in {repo.full_name}: {title}")
        return repo.create_pull(
            title=title,
            body=body,
            head=head,
            base=base
        )
    
    def merge_pull_request(self, pr: PullRequest, commit_message: Optional[str] = None) -> bool:
        """
        Merge a pull request.
        
        Args:
            pr: PullRequest object
            commit_message: Optional commit message
            
        Returns:
            True if merged successfully, False otherwise
        """
        try:
            if not commit_message:
                commit_message = f"Merge PR #{pr.number}: {pr.title}"
                
            merge_result = pr.merge(
                commit_title=f"Merge PR #{pr.number}: {pr.title}",
                commit_message=commit_message,
                merge_method="merge"
            )
            logger.info(f"PR #{pr.number} merged successfully")
            return True
        except GithubException as e:
            logger.error(f"Error merging PR #{pr.number}: {e.status} - {e.data.get('message', '')}")
            return False
        except Exception as e:
            logger.error(f"Error merging PR #{pr.number}: {e}")
            return False
    
    def remove_bot_comments(self, pr: PullRequest, bot_usernames: List[str] = None) -> int:
        """
        Remove bot comments from a pull request.
        
        Args:
            pr: PullRequest object
            bot_usernames: List of bot usernames to remove comments from
            
        Returns:
            Number of comments removed
        """
        if bot_usernames is None:
            bot_usernames = ["github-actions[bot]", "codegen-team"]
            
        removed_count = 0
        
        # Remove PR comments
        comments = pr.get_comments()
        if comments:
            for comment in comments:
                if comment.user.login in bot_usernames:
                    comment.delete()
                    removed_count += 1
        
        # Remove PR reviews
        reviews = pr.get_reviews()
        if reviews:
            for review in reviews:
                if review.user.login in bot_usernames:
                    review.delete()
                    removed_count += 1
        
        # Remove issue comments
        issue_comments = pr.get_issue_comments()
        if issue_comments:
            for comment in issue_comments:
                if comment.user.login in bot_usernames:
                    comment.delete()
                    removed_count += 1
        
        logger.info(f"Removed {removed_count} bot comments from PR #{pr.number} in {pr.base.repo.full_name}")
        return removed_count
