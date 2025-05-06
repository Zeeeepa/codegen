"""
GitHub client for PR analysis.

This module provides a wrapper around PyGithub for interacting with the GitHub API,
including fetching repository and pull request data.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

import github
from github import Github
from github.GithubException import GithubException
from github.Repository import Repository as GithubRepository
from github.PullRequest import PullRequest as GithubPullRequest

from codegen_on_oss.analysis.pr_analysis.git.models import Repository, PullRequest, Commit, File, User, FileStatus


logger = logging.getLogger(__name__)


class GitHubClient:
    """
    Wrapper around PyGithub for GitHub API operations.
    
    This class provides methods for interacting with the GitHub API, including
    fetching repository and pull request data.
    
    Attributes:
        client: PyGithub client
    """
    
    def __init__(self, token: Optional[str] = None, api_url: Optional[str] = None):
        """
        Initialize the GitHub client.
        
        Args:
            token: GitHub API token (optional)
            api_url: GitHub API URL (optional, for GitHub Enterprise)
        """
        if api_url:
            self.client = Github(token, base_url=api_url)
        else:
            self.client = Github(token)
    
    def get_repository(self, repo_url: str) -> Repository:
        """
        Get repository information.
        
        Args:
            repo_url: Repository URL or full name (owner/name)
            
        Returns:
            Repository information
            
        Raises:
            GithubException: If the repository cannot be found
        """
        # Extract repository full name from URL if needed
        if '/' in repo_url and ('github.com' in repo_url or 'api.github.com' in repo_url):
            parts = repo_url.split('/')
            if 'github.com' in repo_url:
                # Format: https://github.com/owner/repo
                owner_idx = parts.index('github.com') + 1
                repo_name = f"{parts[owner_idx]}/{parts[owner_idx + 1]}"
            else:
                # Format: https://api.github.com/repos/owner/repo
                owner_idx = parts.index('repos') + 1
                repo_name = f"{parts[owner_idx]}/{parts[owner_idx + 1]}"
        else:
            # Assume it's already in the format owner/repo
            repo_name = repo_url
        
        logger.info(f"Fetching repository: {repo_name}")
        
        try:
            github_repo = self.client.get_repo(repo_name)
            
            # Convert to our model
            owner = User(
                id=github_repo.owner.id,
                login=github_repo.owner.login,
                name=github_repo.owner.name,
                email=github_repo.owner.email,
                avatar_url=github_repo.owner.avatar_url
            )
            
            return Repository(
                id=github_repo.id,
                name=github_repo.name,
                full_name=github_repo.full_name,
                owner=owner,
                description=github_repo.description,
                html_url=github_repo.html_url,
                clone_url=github_repo.clone_url,
                default_branch=github_repo.default_branch,
                private=github_repo.private,
                created_at=github_repo.created_at,
                updated_at=github_repo.updated_at
            )
        except GithubException as e:
            logger.error(f"Failed to fetch repository '{repo_name}': {e}")
            raise
    
    def get_pull_request(self, repository: Repository, pr_number: int) -> PullRequest:
        """
        Get pull request information.
        
        Args:
            repository: Repository information
            pr_number: Pull request number
            
        Returns:
            Pull request information
            
        Raises:
            GithubException: If the pull request cannot be found
        """
        logger.info(f"Fetching PR #{pr_number} from {repository.full_name}")
        
        try:
            github_repo = self.client.get_repo(repository.full_name)
            github_pr = github_repo.get_pull(pr_number)
            
            # Convert to our model
            user = User(
                id=github_pr.user.id,
                login=github_pr.user.login,
                name=github_pr.user.name,
                email=github_pr.user.email,
                avatar_url=github_pr.user.avatar_url
            )
            
            # Get files
            files = []
            for github_file in github_pr.get_files():
                file_status = FileStatus.MODIFIED
                if github_file.status == 'added':
                    file_status = FileStatus.ADDED
                elif github_file.status == 'removed':
                    file_status = FileStatus.REMOVED
                elif github_file.status == 'renamed':
                    file_status = FileStatus.RENAMED
                
                files.append(File(
                    filename=github_file.filename,
                    status=file_status,
                    additions=github_file.additions,
                    deletions=github_file.deletions,
                    changes=github_file.changes,
                    patch=github_file.patch,
                    blob_url=github_file.blob_url,
                    raw_url=github_file.raw_url,
                    contents_url=github_file.contents_url,
                    previous_filename=github_file.previous_filename
                ))
            
            # Get commits
            commits = []
            for github_commit in github_pr.get_commits():
                commit_author = User(
                    id=github_commit.author.id if github_commit.author else 0,
                    login=github_commit.author.login if github_commit.author else "unknown"
                )
                
                commit_committer = None
                if github_commit.committer:
                    commit_committer = User(
                        id=github_commit.committer.id,
                        login=github_commit.committer.login
                    )
                
                commits.append(Commit(
                    sha=github_commit.sha,
                    message=github_commit.commit.message,
                    author=commit_author,
                    committer=commit_committer,
                    authored_at=github_commit.commit.author.date,
                    committed_at=github_commit.commit.committer.date,
                    html_url=github_commit.html_url,
                    parents=[parent.sha for parent in github_commit.parents]
                ))
            
            # Get assignees
            assignees = []
            for github_assignee in github_pr.assignees:
                assignees.append(User(
                    id=github_assignee.id,
                    login=github_assignee.login,
                    name=github_assignee.name,
                    email=github_assignee.email,
                    avatar_url=github_assignee.avatar_url
                ))
            
            # Get requested reviewers
            requested_reviewers = []
            for github_reviewer in github_pr.requested_reviewers:
                requested_reviewers.append(User(
                    id=github_reviewer.id,
                    login=github_reviewer.login,
                    name=github_reviewer.name,
                    email=github_reviewer.email,
                    avatar_url=github_reviewer.avatar_url
                ))
            
            return PullRequest(
                id=github_pr.id,
                number=github_pr.number,
                title=github_pr.title,
                body=github_pr.body,
                state=github_pr.state,
                html_url=github_pr.html_url,
                diff_url=github_pr.diff_url,
                patch_url=github_pr.patch_url,
                user=user,
                created_at=github_pr.created_at,
                updated_at=github_pr.updated_at,
                closed_at=github_pr.closed_at,
                merged_at=github_pr.merged_at,
                merge_commit_sha=github_pr.merge_commit_sha,
                head={
                    'ref': github_pr.head.ref,
                    'sha': github_pr.head.sha,
                    'repo': github_pr.head.repo.full_name if github_pr.head.repo else None
                },
                base={
                    'ref': github_pr.base.ref,
                    'sha': github_pr.base.sha,
                    'repo': github_pr.base.repo.full_name
                },
                commits=commits,
                files=files,
                additions=github_pr.additions,
                deletions=github_pr.deletions,
                changed_files=github_pr.changed_files,
                mergeable=github_pr.mergeable,
                merged=github_pr.merged,
                mergeable_state=github_pr.mergeable_state,
                labels=[label.name for label in github_pr.labels],
                assignees=assignees,
                requested_reviewers=requested_reviewers,
                draft=github_pr.draft
            )
        except GithubException as e:
            logger.error(f"Failed to fetch PR #{pr_number} from '{repository.full_name}': {e}")
            raise
    
    def post_pr_comment(self, repository: Repository, pull_request: PullRequest, comment: str) -> None:
        """
        Post a comment to a pull request.
        
        Args:
            repository: Repository information
            pull_request: Pull request information
            comment: Comment text
            
        Raises:
            GithubException: If the comment cannot be posted
        """
        logger.info(f"Posting comment to PR #{pull_request.number} in {repository.full_name}")
        
        try:
            github_repo = self.client.get_repo(repository.full_name)
            github_pr = github_repo.get_pull(pull_request.number)
            github_pr.create_issue_comment(comment)
        except GithubException as e:
            logger.error(f"Failed to post comment to PR #{pull_request.number}: {e}")
            raise
    
    def post_pr_review(self, repository: Repository, pull_request: PullRequest, 
                      comments: List[Dict[str, Any]], body: str = "", 
                      event: str = "COMMENT") -> None:
        """
        Post a review to a pull request.
        
        Args:
            repository: Repository information
            pull_request: Pull request information
            comments: List of review comments (each with path, position, and body)
            body: Review body text
            event: Review event (APPROVE, REQUEST_CHANGES, COMMENT)
            
        Raises:
            GithubException: If the review cannot be posted
        """
        logger.info(f"Posting review to PR #{pull_request.number} in {repository.full_name}")
        
        try:
            github_repo = self.client.get_repo(repository.full_name)
            github_pr = github_repo.get_pull(pull_request.number)
            github_pr.create_review(body=body, event=event, comments=comments)
        except GithubException as e:
            logger.error(f"Failed to post review to PR #{pull_request.number}: {e}")
            raise

