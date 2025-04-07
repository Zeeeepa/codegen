"""
GitHub integration for the Projector system.
"""
import os
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import github
from github import Github

class GitHubManager:
    """
    GitHub integration for the Projector system.
    """
    
    def __init__(
        self,
        github_token: str,
        github_username: str,
        default_repo: str = None
    ):
        """Initialize the GitHub manager."""
        self.github_token = github_token
        self.github_username = github_username
        self.default_repo = default_repo
        self.logger = logging.getLogger(__name__)
        
        # Initialize GitHub client
        self.github = Github(github_token)
        
        # Cache for repository objects
        self.repo_cache = {}
    
    def get_repository(self, owner: str, repo: str) -> Optional[github.Repository.Repository]:
        """
        Get a GitHub repository.
        
        Args:
            owner: The owner of the repository.
            repo: The name of the repository.
            
        Returns:
            The repository object, or None if not found.
        """
        cache_key = f"{owner}/{repo}"
        
        if cache_key in self.repo_cache:
            return self.repo_cache[cache_key]
        
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            self.repo_cache[cache_key] = repository
            return repository
        except Exception as e:
            self.logger.error(f"Error getting repository {owner}/{repo}: {e}")
            return None
    
    def get_repository_contents(self, owner: str, repo: str, path: str = "") -> Dict[str, Any]:
        """
        Get the contents of a repository.
        
        Args:
            owner: The owner of the repository.
            repo: The name of the repository.
            path: The path to get contents for.
            
        Returns:
            A dictionary containing the repository contents.
        """
        repository = self.get_repository(owner, repo)
        if not repository:
            return {}
        
        try:
            contents = repository.get_contents(path)
            
            result = {}
            
            # Process contents
            for content in contents:
                if content.type == "dir":
                    # Recursively get directory contents
                    result[content.name] = self.get_repository_contents(owner, repo, content.path)
                else:
                    # Get file content
                    result[content.name] = {
                        "type": "file",
                        "path": content.path,
                        "content": content.decoded_content.decode("utf-8"),
                        "sha": content.sha
                    }
            
            return result
        except Exception as e:
            self.logger.error(f"Error getting repository contents for {owner}/{repo}/{path}: {e}")
            return {}
    
    def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "main"
    ) -> Optional[Dict[str, Any]]:
        """
        Create a pull request.
        
        Args:
            owner: The owner of the repository.
            repo: The name of the repository.
            title: The title of the pull request.
            body: The body of the pull request.
            head: The name of the branch where your changes are implemented.
            base: The name of the branch you want the changes pulled into.
            
        Returns:
            The pull request data, or None if creation failed.
        """
        repository = self.get_repository(owner, repo)
        if not repository:
            return None
        
        try:
            pr = repository.create_pull(
                title=title,
                body=body,
                head=head,
                base=base
            )
            
            return {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "html_url": pr.html_url,
                "state": pr.state,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "merged": pr.merged,
                "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                "user": {
                    "login": pr.user.login,
                    "avatar_url": pr.user.avatar_url
                }
            }
        except Exception as e:
            self.logger.error(f"Error creating pull request for {owner}/{repo}: {e}")
            return None
    
    def get_pull_request(
        self,
        owner: str,
        repo: str,
        pr_number: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get a pull request.
        
        Args:
            owner: The owner of the repository.
            repo: The name of the repository.
            pr_number: The pull request number.
            
        Returns:
            The pull request data, or None if not found.
        """
        repository = self.get_repository(owner, repo)
        if not repository:
            return None
        
        try:
            pr = repository.get_pull(pr_number)
            
            return {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "html_url": pr.html_url,
                "state": pr.state,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "merged": pr.merged,
                "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                "user": {
                    "login": pr.user.login,
                    "avatar_url": pr.user.avatar_url
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting pull request {pr_number} for {owner}/{repo}: {e}")
            return None
    
    def get_recent_merges(
        self,
        owner: str,
        repo: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get recent merged pull requests.
        
        Args:
            owner: The owner of the repository.
            repo: The name of the repository.
            days: Number of days to look back.
            
        Returns:
            A list of merged pull requests.
        """
        repository = self.get_repository(owner, repo)
        if not repository:
            return []
        
        try:
            # Calculate the date to look back to
            since_date = datetime.now() - timedelta(days=days)
            
            # Get all pull requests
            pulls = repository.get_pulls(state='closed')
            
            # Filter for merged PRs within the time period
            recent_merges = []
            for pr in pulls:
                if pr.merged and pr.merged_at and pr.merged_at > since_date:
                    recent_merges.append({
                        "number": pr.number,
                        "title": pr.title,
                        "body": pr.body,
                        "html_url": pr.html_url,
                        "state": pr.state,
                        "created_at": pr.created_at.isoformat(),
                        "updated_at": pr.updated_at.isoformat(),
                        "merged": pr.merged,
                        "merged_at": pr.merged_at.isoformat(),
                        "user": {
                            "login": pr.user.login,
                            "avatar_url": pr.user.avatar_url
                        }
                    })
            
            return recent_merges
        except Exception as e:
            self.logger.error(f"Error getting recent merges for {owner}/{repo}: {e}")
            return []
    
    def create_comment(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str
    ) -> Optional[Dict[str, Any]]:
        """
        Create a comment on a pull request.
        
        Args:
            owner: The owner of the repository.
            repo: The name of the repository.
            pr_number: The pull request number.
            body: The comment body.
            
        Returns:
            The comment data, or None if creation failed.
        """
        repository = self.get_repository(owner, repo)
        if not repository:
            return None
        
        try:
            pr = repository.get_pull(pr_number)
            comment = pr.create_issue_comment(body)
            
            return {
                "id": comment.id,
                "body": comment.body,
                "created_at": comment.created_at.isoformat(),
                "updated_at": comment.updated_at.isoformat(),
                "user": {
                    "login": comment.user.login,
                    "avatar_url": comment.user.avatar_url
                }
            }
        except Exception as e:
            self.logger.error(f"Error creating comment on PR {pr_number} for {owner}/{repo}: {e}")
            return None
    
    def get_comments(
        self,
        owner: str,
        repo: str,
        pr_number: int
    ) -> List[Dict[str, Any]]:
        """
        Get comments on a pull request.
        
        Args:
            owner: The owner of the repository.
            repo: The name of the repository.
            pr_number: The pull request number.
            
        Returns:
            A list of comments.
        """
        repository = self.get_repository(owner, repo)
        if not repository:
            return []
        
        try:
            pr = repository.get_pull(pr_number)
            comments = pr.get_issue_comments()
            
            result = []
            for comment in comments:
                result.append({
                    "id": comment.id,
                    "body": comment.body,
                    "created_at": comment.created_at.isoformat(),
                    "updated_at": comment.updated_at.isoformat(),
                    "user": {
                        "login": comment.user.login,
                        "avatar_url": comment.user.avatar_url
                    }
                })
            
            return result
        except Exception as e:
            self.logger.error(f"Error getting comments for PR {pr_number} for {owner}/{repo}: {e}")
            return []
    
    def get_branches(
        self,
        owner: str,
        repo: str
    ) -> List[Dict[str, Any]]:
        """
        Get branches in a repository.
        
        Args:
            owner: The owner of the repository.
            repo: The name of the repository.
            
        Returns:
            A list of branches.
        """
        repository = self.get_repository(owner, repo)
        if not repository:
            return []
        
        try:
            branches = repository.get_branches()
            
            result = []
            for branch in branches:
                result.append({
                    "name": branch.name,
                    "commit": {
                        "sha": branch.commit.sha,
                        "url": branch.commit.html_url
                    }
                })
            
            return result
        except Exception as e:
            self.logger.error(f"Error getting branches for {owner}/{repo}: {e}")
            return []
    
    def get_commits(
        self,
        owner: str,
        repo: str,
        branch: str = None,
        path: str = None,
        since: datetime = None,
        until: datetime = None,
        max_count: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get commits in a repository.
        
        Args:
            owner: The owner of the repository.
            repo: The name of the repository.
            branch: The branch to get commits from.
            path: The path to get commits for.
            since: The date to get commits since.
            until: The date to get commits until.
            max_count: The maximum number of commits to get.
            
        Returns:
            A list of commits.
        """
        repository = self.get_repository(owner, repo)
        if not repository:
            return []
        
        try:
            # Build the query parameters
            kwargs = {}
            if branch:
                kwargs["sha"] = branch
            if path:
                kwargs["path"] = path
            if since:
                kwargs["since"] = since
            if until:
                kwargs["until"] = until
            
            commits = repository.get_commits(**kwargs)
            
            result = []
            for commit in commits[:max_count]:
                result.append({
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": {
                        "name": commit.commit.author.name,
                        "email": commit.commit.author.email,
                        "date": commit.commit.author.date.isoformat()
                    },
                    "committer": {
                        "name": commit.commit.committer.name,
                        "email": commit.commit.committer.email,
                        "date": commit.commit.committer.date.isoformat()
                    },
                    "html_url": commit.html_url
                })
            
            return result
        except Exception as e:
            self.logger.error(f"Error getting commits for {owner}/{repo}: {e}")
            return []
