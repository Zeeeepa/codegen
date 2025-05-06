"""
Repository operator for PR analysis.

This module provides a wrapper around GitPython for Git operations.
"""

import logging
import os
import shutil
import tempfile
from typing import Dict, Optional, Any

import git

from codegen_on_oss.analysis.pr_analysis.git.models import Repository, PullRequest

logger = logging.getLogger(__name__)


class RepoOperator:
    """
    Operator for Git repository operations.

    This class provides methods for cloning, updating, and checking out repositories.

    Attributes:
        repository: Repository object
        config: Git configuration
        repo_path: Local path to the repository
        repo: GitPython repository object
    """

    def __init__(self, repository: Repository, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the repository operator.

        Args:
            repository: Repository object
            config: Git configuration
        """
        self.repository = repository
        self.config = config or {}
        self.repo_path = self._get_repo_path()
        self.repo = None

    def prepare_repository(self) -> None:
        """
        Clone or update the repository.

        This method clones the repository if it doesn't exist, or updates it if it does.
        """
        if os.path.exists(self.repo_path):
            self._update_repository()
        else:
            self._clone_repository()

    def checkout_pull_request(self, pull_request: PullRequest) -> None:
        """
        Checkout a pull request.

        Args:
            pull_request: Pull request object

        Raises:
            RuntimeError: If the repository is not prepared
        """
        if not self.repo:
            raise RuntimeError("Repository is not prepared")

        logger.info(f"Checking out PR #{pull_request.number} in {self.repository.full_name}")

        # Fetch the PR branch
        self.repo.git.fetch("origin", pull_request.head_branch)

        # Checkout the PR branch
        self.repo.git.checkout(pull_request.head_sha)

    def _get_repo_path(self) -> str:
        """
        Get the local path to the repository.

        Returns:
            Local path to the repository
        """
        repo_path = self.config.get("repo_path")
        if repo_path:
            return os.path.join(repo_path, self.repository.full_name.replace("/", "_"))
        else:
            return os.path.join(tempfile.gettempdir(), "pr_analysis", self.repository.full_name.replace("/", "_"))

    def _clone_repository(self) -> None:
        """
        Clone the repository.
        """
        logger.info(f"Cloning repository {self.repository.full_name} to {self.repo_path}")

        # Create the parent directory if it doesn't exist
        os.makedirs(os.path.dirname(self.repo_path), exist_ok=True)

        # Clone the repository
        self.repo = git.Repo.clone_from(self.repository.clone_url, self.repo_path)

    def _update_repository(self) -> None:
        """
        Update the repository.
        """
        logger.info(f"Updating repository {self.repository.full_name} in {self.repo_path}")

        # Open the repository
        self.repo = git.Repo(self.repo_path)

        # Fetch the latest changes
        self.repo.git.fetch("origin")

        # Reset to the default branch
        self.repo.git.checkout(self.repository.default_branch)
        self.repo.git.reset("--hard", f"origin/{self.repository.default_branch}")

    def cleanup(self) -> None:
        """
        Clean up the repository.
        """
        logger.info(f"Cleaning up repository {self.repository.full_name} in {self.repo_path}")

        # Close the repository
        if self.repo:
            self.repo.close()
            self.repo = None

        # Remove the repository directory if it's in a temporary directory
        if tempfile.gettempdir() in self.repo_path and os.path.exists(self.repo_path):
            shutil.rmtree(self.repo_path)

