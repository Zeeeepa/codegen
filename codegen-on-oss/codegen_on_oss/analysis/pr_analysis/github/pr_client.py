"""
PR Client

Client for interacting with GitHub pull requests.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from github import Github
from github.PullRequest import PullRequest

logger = logging.getLogger(__name__)


class PRClient:
    """
    Client for interacting with GitHub pull requests.

    This class provides methods for fetching PR data and posting comments.
    """

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize the PR client.

        Args:
            github_token: The GitHub API token to use
        """
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        if not self.github_token:
            logger.warning("No GitHub token provided. Some functionality may be limited.")

        self.github = Github(self.github_token) if self.github_token else None

    def get_pr_data(self, pr_number: int, repo_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get data for a specific pull request.

        Args:
            pr_number: The number of the pull request
            repo_name: The name of the repository (format: "owner/repo")

        Returns:
            A dictionary containing PR data

        Raises:
            ValueError: If no GitHub token is provided
            Exception: If there's an error fetching the PR data
        """
        if not self.github:
            raise ValueError("No GitHub token provided")

        repo_name = repo_name or os.environ.get("GITHUB_REPOSITORY")
        if not repo_name:
            raise ValueError("No repository name provided")

        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)

            # Get changed files
            changed_files = {}
            for file in pr.get_files():
                changed_files[file.filename] = {
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "patch": file.patch,
                }

            # Get commits
            commits = []
            for commit in pr.get_commits():
                commits.append(
                    {
                        "sha": commit.sha,
                        "message": commit.commit.message,
                        "author": commit.commit.author.name,
                        "date": commit.commit.author.date.isoformat(),
                    }
                )

            return {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "head_sha": pr.head.sha,
                "base_sha": pr.base.sha,
                "changed_files": changed_files,
                "commits": commits,
            }
        except Exception as e:
            logger.exception(f"Error fetching PR #{pr_number}: {e}")
            raise

    def post_comment(
        self, pr_number: int, comment: str, repo_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post a comment on a pull request.

        Args:
            pr_number: The number of the pull request
            comment: The comment to post
            repo_name: The name of the repository (format: "owner/repo")

        Returns:
            A dictionary containing the result of posting the comment

        Raises:
            ValueError: If no GitHub token is provided
            Exception: If there's an error posting the comment
        """
        if not self.github:
            raise ValueError("No GitHub token provided")

        repo_name = repo_name or os.environ.get("GITHUB_REPOSITORY")
        if not repo_name:
            raise ValueError("No repository name provided")

        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            comment_obj = pr.create_issue_comment(comment)

            return {
                "id": comment_obj.id,
                "body": comment_obj.body,
                "created_at": comment_obj.created_at.isoformat(),
                "html_url": comment_obj.html_url,
            }
        except Exception as e:
            logger.exception(f"Error posting comment on PR #{pr_number}: {e}")
            raise

    def post_review_comment(
        self,
        pr_number: int,
        comment: str,
        file_path: str,
        line: int,
        repo_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Post a review comment on a specific line of a pull request.

        Args:
            pr_number: The number of the pull request
            comment: The comment to post
            file_path: The path of the file to comment on
            line: The line number to comment on
            repo_name: The name of the repository (format: "owner/repo")

        Returns:
            A dictionary containing the result of posting the comment

        Raises:
            ValueError: If no GitHub token is provided
            Exception: If there's an error posting the comment
        """
        if not self.github:
            raise ValueError("No GitHub token provided")

        repo_name = repo_name or os.environ.get("GITHUB_REPOSITORY")
        if not repo_name:
            raise ValueError("No repository name provided")

        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)

            # Get the latest commit in the PR
            commits = list(pr.get_commits())
            if not commits:
                raise ValueError("No commits found in PR")

            latest_commit = commits[-1]

            # Create a review comment
            comment_obj = pr.create_review_comment(
                body=comment, commit=latest_commit, path=file_path, position=line
            )

            return {
                "id": comment_obj.id,
                "body": comment_obj.body,
                "created_at": comment_obj.created_at.isoformat(),
                "html_url": comment_obj.html_url,
            }
        except Exception as e:
            logger.exception(f"Error posting review comment on PR #{pr_number}: {e}")
            raise
