"""
GitHub client for PR analysis.

This module provides a wrapper around PyGithub for interacting with the GitHub API.
"""

import logging
from typing import Dict, List, Optional, Any

from github import Github
from github.Repository import Repository as GithubRepository
from github.PullRequest import PullRequest as GithubPullRequest

from codegen_on_oss.analysis.pr_analysis.git.models import Repository, PullRequest

logger = logging.getLogger(__name__)


class GitHubClient:
    """
    Client for interacting with GitHub API.

    This class provides methods for retrieving repository and PR data from GitHub.

    Attributes:
        github: PyGithub client
        api_url: GitHub API URL
    """

    def __init__(self, token: Optional[str] = None, api_url: Optional[str] = None):
        """
        Initialize the GitHub client.

        Args:
            token: GitHub API token
            api_url: GitHub API URL
        """
        self.api_url = api_url
        if token and api_url:
            self.github = Github(token, base_url=api_url)
        elif token:
            self.github = Github(token)
        else:
            self.github = Github()

    def get_repository(self, repo_url: str) -> Repository:
        """
        Get repository information.

        Args:
            repo_url: Repository URL or owner/repo string

        Returns:
            Repository object

        Raises:
            ValueError: If the repository cannot be found
        """
        # Parse the repo URL to get owner and repo name
        if "/" in repo_url and "github.com" not in repo_url:
            owner, repo_name = repo_url.split("/")
        else:
            # Extract owner/repo from a full GitHub URL
            parts = repo_url.rstrip("/").split("/")
            owner = parts[-2]
            repo_name = parts[-1]
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]

        try:
            # Get the repository from GitHub
            github_repo = self.github.get_repo(f"{owner}/{repo_name}")
            return self._convert_github_repo(github_repo)
        except Exception as e:
            logger.error(f"Failed to get repository {repo_url}: {e}")
            raise ValueError(f"Failed to get repository {repo_url}: {e}")

    def get_pull_request(self, repository: Repository, pr_number: int) -> PullRequest:
        """
        Get pull request information.

        Args:
            repository: Repository object
            pr_number: Pull request number

        Returns:
            Pull request object

        Raises:
            ValueError: If the pull request cannot be found
        """
        try:
            # Get the repository from GitHub
            github_repo = self.github.get_repo(repository.full_name)
            # Get the pull request from GitHub
            github_pr = github_repo.get_pull(pr_number)
            return self._convert_github_pr(github_pr)
        except Exception as e:
            logger.error(f"Failed to get PR {pr_number} in {repository.full_name}: {e}")
            raise ValueError(f"Failed to get PR {pr_number} in {repository.full_name}: {e}")

    def post_pr_comment(self, repository: Repository, pull_request: PullRequest, comment: str) -> None:
        """
        Post a comment to a pull request.

        Args:
            repository: Repository object
            pull_request: Pull request object
            comment: Comment text

        Raises:
            ValueError: If the comment cannot be posted
        """
        try:
            # Get the repository from GitHub
            github_repo = self.github.get_repo(repository.full_name)
            # Get the pull request from GitHub
            github_pr = github_repo.get_pull(pull_request.number)
            # Post the comment
            github_pr.create_issue_comment(comment)
        except Exception as e:
            logger.error(f"Failed to post comment to PR {pull_request.number} in {repository.full_name}: {e}")
            raise ValueError(f"Failed to post comment to PR {pull_request.number} in {repository.full_name}: {e}")

    def _convert_github_repo(self, github_repo: GithubRepository) -> Repository:
        """
        Convert a PyGithub Repository to our Repository model.

        Args:
            github_repo: PyGithub Repository object

        Returns:
            Repository object
        """
        return Repository(
            full_name=github_repo.full_name,
            owner=github_repo.owner.login,
            name=github_repo.name,
            url=github_repo.html_url,
            clone_url=github_repo.clone_url,
            default_branch=github_repo.default_branch,
            metadata={
                "description": github_repo.description,
                "language": github_repo.language,
                "private": github_repo.private,
                "fork": github_repo.fork,
                "created_at": github_repo.created_at.isoformat() if github_repo.created_at else None,
                "updated_at": github_repo.updated_at.isoformat() if github_repo.updated_at else None,
            },
        )

    def _convert_github_pr(self, github_pr: GithubPullRequest) -> PullRequest:
        """
        Convert a PyGithub PullRequest to our PullRequest model.

        Args:
            github_pr: PyGithub PullRequest object

        Returns:
            PullRequest object
        """
        # Get the files changed in the PR
        files = []
        for file in github_pr.get_files():
            files.append({
                "filename": file.filename,
                "status": file.status,
                "additions": file.additions,
                "deletions": file.deletions,
                "changes": file.changes,
                "patch": file.patch,
            })

        return PullRequest(
            number=github_pr.number,
            title=github_pr.title,
            body=github_pr.body,
            author=github_pr.user.login,
            base_branch=github_pr.base.ref,
            head_branch=github_pr.head.ref,
            base_sha=github_pr.base.sha,
            head_sha=github_pr.head.sha,
            state=github_pr.state,
            url=github_pr.html_url,
            files=files,
            metadata={
                "created_at": github_pr.created_at.isoformat() if github_pr.created_at else None,
                "updated_at": github_pr.updated_at.isoformat() if github_pr.updated_at else None,
                "merged": github_pr.merged,
                "mergeable": github_pr.mergeable,
                "mergeable_state": github_pr.mergeable_state,
                "comments": github_pr.comments,
                "commits": github_pr.commits,
                "additions": github_pr.additions,
                "deletions": github_pr.deletions,
                "changed_files": github_pr.changed_files,
            },
        )

