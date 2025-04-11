"""
GitHub client for the PR Review Bot.
This module provides a wrapper around the GitHub API.
"""

import os
import logging
from typing import Dict, Any, Optional, List, Union
from github import Github
from github.Repository import Repository
from github.PullRequest import PullRequest
from github.GithubException import GithubException

logger = logging.getLogger(__name__)

class GitHubClient:
    """
    GitHub client for the PR Review Bot.
    
    This class provides a wrapper around the GitHub API for interacting with repositories,
    pull requests, and other GitHub resources.
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
        Get a repository by name.
        
        Args:
            repo_name: Name of the repository (e.g., "owner/repo")
            
        Returns:
            Repository object
        """
        logger.info(f"Getting repository {repo_name}")
        return self.client.get_repo(repo_name)
    
    def get_repositories(self) -> List[Dict[str, Any]]:
        """
        Get all repositories accessible to the authenticated user.
        
        Returns:
            List of repository dictionaries
        """
        logger.info("Getting all repositories")
        repos = []
        
        try:
            for repo in self.client.get_user().get_repos():
                repos.append({
                    "id": repo.id,
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "url": repo.html_url,
                    "private": repo.private,
                    "fork": repo.fork,
                    "default_branch": repo.default_branch
                })
            
            logger.info(f"Found {len(repos)} repositories")
            return repos
        except GithubException as e:
            logger.error(f"Error getting repositories: {e}")
            return []
    
    def get_pull_request(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """
        Get a pull request by number.
        
        Args:
            repo_name: Name of the repository (e.g., "owner/repo")
            pr_number: Number of the pull request
            
        Returns:
            Pull request dictionary
        """
        logger.info(f"Getting pull request {repo_name}#{pr_number}")
        
        try:
            repo = self.get_repository(repo_name)
            pr = repo.get_pull(pr_number)
            
            return {
                "id": pr.id,
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "html_url": pr.html_url,
                "user": {
                    "login": pr.user.login,
                    "id": pr.user.id,
                    "avatar_url": pr.user.avatar_url,
                    "html_url": pr.user.html_url
                },
                "created_at": pr.created_at,
                "updated_at": pr.updated_at,
                "merged": pr.merged,
                "mergeable": pr.mergeable,
                "mergeable_state": pr.mergeable_state,
                "head": {
                    "ref": pr.head.ref,
                    "sha": pr.head.sha,
                    "repo": {
                        "full_name": pr.head.repo.full_name if pr.head.repo else None
                    }
                },
                "base": {
                    "ref": pr.base.ref,
                    "sha": pr.base.sha,
                    "repo": {
                        "full_name": pr.base.repo.full_name
                    }
                }
            }
        except GithubException as e:
            logger.error(f"Error getting pull request {repo_name}#{pr_number}: {e}")
            raise
    
    def get_pull_request_files(self, repo_name: str, pr_number: int) -> List[Dict[str, Any]]:
        """
        Get the files changed in a pull request.
        
        Args:
            repo_name: Name of the repository (e.g., "owner/repo")
            pr_number: Number of the pull request
            
        Returns:
            List of file dictionaries
        """
        logger.info(f"Getting files for pull request {repo_name}#{pr_number}")
        
        try:
            repo = self.get_repository(repo_name)
            pr = repo.get_pull(pr_number)
            
            files = []
            for file in pr.get_files():
                files.append({
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "blob_url": file.blob_url,
                    "raw_url": file.raw_url,
                    "contents_url": file.contents_url,
                    "patch": file.patch
                })
            
            logger.info(f"Found {len(files)} files in pull request {repo_name}#{pr_number}")
            return files
        except GithubException as e:
            logger.error(f"Error getting files for pull request {repo_name}#{pr_number}: {e}")
            raise
    
    def get_pull_request_diff(self, repo_name: str, pr_number: int) -> str:
        """
        Get the diff for a pull request.
        
        Args:
            repo_name: Name of the repository (e.g., "owner/repo")
            pr_number: Number of the pull request
            
        Returns:
            Diff string
        """
        logger.info(f"Getting diff for pull request {repo_name}#{pr_number}")
        
        try:
            repo = self.get_repository(repo_name)
            pr = repo.get_pull(pr_number)
            
            # Get the diff
            diff = pr.get_files()
            
            # Convert to string
            diff_str = ""
            for file in diff:
                diff_str += f"diff --git a/{file.filename} b/{file.filename}\n"
                diff_str += f"index {file.status}\n"
                diff_str += f"--- a/{file.filename}\n"
                diff_str += f"+++ b/{file.filename}\n"
                if file.patch:
                    diff_str += file.patch + "\n"
            
            return diff_str
        except GithubException as e:
            logger.error(f"Error getting diff for pull request {repo_name}#{pr_number}: {e}")
            raise
    
    def get_pull_request_comments(self, repo_name: str, pr_number: int) -> List[Dict[str, Any]]:
        """
        Get the comments on a pull request.
        
        Args:
            repo_name: Name of the repository (e.g., "owner/repo")
            pr_number: Number of the pull request
            
        Returns:
            List of comment dictionaries
        """
        logger.info(f"Getting comments for pull request {repo_name}#{pr_number}")
        
        try:
            repo = self.get_repository(repo_name)
            pr = repo.get_pull(pr_number)
            
            comments = []
            for comment in pr.get_issue_comments():
                comments.append({
                    "id": comment.id,
                    "body": comment.body,
                    "user": {
                        "login": comment.user.login,
                        "id": comment.user.id,
                        "avatar_url": comment.user.avatar_url,
                        "html_url": comment.user.html_url
                    },
                    "created_at": comment.created_at,
                    "updated_at": comment.updated_at,
                    "html_url": comment.html_url
                })
            
            logger.info(f"Found {len(comments)} comments on pull request {repo_name}#{pr_number}")
            return comments
        except GithubException as e:
            logger.error(f"Error getting comments for pull request {repo_name}#{pr_number}: {e}")
            raise
    
    def create_pull_request_comment(self, repo_name: str, pr_number: int, body: str) -> Dict[str, Any]:
        """
        Create a comment on a pull request.
        
        Args:
            repo_name: Name of the repository (e.g., "owner/repo")
            pr_number: Number of the pull request
            body: Comment body
            
        Returns:
            Comment dictionary
        """
        logger.info(f"Creating comment on pull request {repo_name}#{pr_number}")
        
        try:
            repo = self.get_repository(repo_name)
            pr = repo.get_pull(pr_number)
            
            comment = pr.create_issue_comment(body)
            
            return {
                "id": comment.id,
                "body": comment.body,
                "user": {
                    "login": comment.user.login,
                    "id": comment.user.id,
                    "avatar_url": comment.user.avatar_url,
                    "html_url": comment.user.html_url
                },
                "created_at": comment.created_at,
                "updated_at": comment.updated_at,
                "html_url": comment.html_url
            }
        except GithubException as e:
            logger.error(f"Error creating comment on pull request {repo_name}#{pr_number}: {e}")
            raise
    
    def create_pull_request_review(self, repo_name: str, pr_number: int, body: str, event: str = "COMMENT") -> Dict[str, Any]:
        """
        Create a review on a pull request.
        
        Args:
            repo_name: Name of the repository (e.g., "owner/repo")
            pr_number: Number of the pull request
            body: Review body
            event: Review event (APPROVE, REQUEST_CHANGES, COMMENT)
            
        Returns:
            Review dictionary
        """
        logger.info(f"Creating review on pull request {repo_name}#{pr_number}")
        
        try:
            repo = self.get_repository(repo_name)
            pr = repo.get_pull(pr_number)
            
            review = pr.create_review(body=body, event=event)
            
            return {
                "id": review.id,
                "body": review.body,
                "state": review.state,
                "user": {
                    "login": review.user.login,
                    "id": review.user.id,
                    "avatar_url": review.user.avatar_url,
                    "html_url": review.user.html_url
                },
                "submitted_at": review.submitted_at,
                "html_url": review.html_url
            }
        except GithubException as e:
            logger.error(f"Error creating review on pull request {repo_name}#{pr_number}: {e}")
            raise
    
    def get_file_content(self, repo_name: str, path: str, ref: Optional[str] = None) -> str:
        """
        Get the content of a file in a repository.
        
        Args:
            repo_name: Name of the repository (e.g., "owner/repo")
            path: Path to the file
            ref: Reference (branch, tag, or commit SHA)
            
        Returns:
            File content
        """
        logger.info(f"Getting content of file {path} in repository {repo_name}")
        
        try:
            repo = self.get_repository(repo_name)
            content = repo.get_contents(path, ref=ref)
            
            if isinstance(content, list):
                raise ValueError(f"Path {path} is a directory, not a file")
            
            return content.decoded_content.decode("utf-8")
        except GithubException as e:
            logger.error(f"Error getting content of file {path} in repository {repo_name}: {e}")
            raise
    
    def get_webhooks(self, repo_name: str) -> List[Dict[str, Any]]:
        """
        Get all webhooks for a repository.
        
        Args:
            repo_name: Name of the repository (e.g., "owner/repo")
            
        Returns:
            List of webhook dictionaries
        """
        logger.info(f"Getting webhooks for repository {repo_name}")
        
        try:
            repo = self.get_repository(repo_name)
            
            webhooks = []
            for hook in repo.get_hooks():
                webhooks.append({
                    "id": hook.id,
                    "name": hook.name,
                    "active": hook.active,
                    "events": hook.events,
                    "config": hook.config,
                    "created_at": hook.created_at,
                    "updated_at": hook.updated_at
                })
            
            logger.info(f"Found {len(webhooks)} webhooks in repository {repo_name}")
            return webhooks
        except GithubException as e:
            logger.error(f"Error getting webhooks for repository {repo_name}: {e}")
            raise
    
    def create_webhook(self, repo_name: str, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a webhook for a repository.
        
        Args:
            repo_name: Name of the repository (e.g., "owner/repo")
            webhook_data: Webhook data
            
        Returns:
            Webhook dictionary
        """
        logger.info(f"Creating webhook for repository {repo_name}")
        
        try:
            repo = self.get_repository(repo_name)
            
            hook = repo.create_hook(
                name=webhook_data["name"],
                config=webhook_data["config"],
                events=webhook_data["events"],
                active=webhook_data["active"]
            )
            
            return {
                "id": hook.id,
                "name": hook.name,
                "active": hook.active,
                "events": hook.events,
                "config": hook.config,
                "created_at": hook.created_at,
                "updated_at": hook.updated_at
            }
        except GithubException as e:
            logger.error(f"Error creating webhook for repository {repo_name}: {e}")
            raise
    
    def update_webhook(self, repo_name: str, webhook_id: int, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a webhook for a repository.
        
        Args:
            repo_name: Name of the repository (e.g., "owner/repo")
            webhook_id: ID of the webhook
            webhook_data: Webhook data
            
        Returns:
            Webhook dictionary
        """
        logger.info(f"Updating webhook {webhook_id} for repository {repo_name}")
        
        try:
            repo = self.get_repository(repo_name)
            hook = repo.get_hook(webhook_id)
            
            hook.edit(
                config=webhook_data["config"],
                events=webhook_data["events"],
                active=webhook_data["active"]
            )
            
            return {
                "id": hook.id,
                "name": hook.name,
                "active": hook.active,
                "events": hook.events,
                "config": hook.config,
                "created_at": hook.created_at,
                "updated_at": hook.updated_at
            }
        except GithubException as e:
            logger.error(f"Error updating webhook {webhook_id} for repository {repo_name}: {e}")
            raise
    
    def delete_webhook(self, repo_name: str, webhook_id: int) -> None:
        """
        Delete a webhook for a repository.
        
        Args:
            repo_name: Name of the repository (e.g., "owner/repo")
            webhook_id: ID of the webhook
        """
        logger.info(f"Deleting webhook {webhook_id} for repository {repo_name}")
        
        try:
            repo = self.get_repository(repo_name)
            hook = repo.get_hook(webhook_id)
            hook.delete()
        except GithubException as e:
            logger.error(f"Error deleting webhook {webhook_id} for repository {repo_name}: {e}")
            raise
