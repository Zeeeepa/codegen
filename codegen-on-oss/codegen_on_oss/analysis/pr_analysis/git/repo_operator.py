"""
Repository operator for PR analysis.

This module provides a wrapper around GitPython for repository operations,
including cloning, fetching, and checking out repositories and pull requests.
"""

import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

import git
from git import Repo
from git.exc import GitCommandError

from codegen_on_oss.analysis.pr_analysis.git.models import Repository, PullRequest


logger = logging.getLogger(__name__)


class RepoOperator:
    """
    Wrapper around GitPython for repository operations.
    
    This class provides methods for repository operations, including cloning,
    fetching, and checking out repositories and pull requests.
    
    Attributes:
        repository: Repository information
        config: Repository operator configuration
        repo_path: Local repository path
        repo: GitPython repository object
    """
    
    def __init__(self, repository: Repository, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the repository operator.
        
        Args:
            repository: Repository information
            config: Repository operator configuration (optional)
        """
        self.repository = repository
        self.config = config or {}
        self.repo_path = self._get_repo_path()
        self.repo = None
    
    def _get_repo_path(self) -> str:
        """
        Get the local repository path.
        
        Returns:
            Local repository path
        """
        # Use configured path if available
        if 'repo_path' in self.config:
            base_path = self.config['repo_path']
        else:
            # Otherwise use a temporary directory
            base_path = os.path.join(tempfile.gettempdir(), 'pr_analysis')
        
        # Create the base path if it doesn't exist
        os.makedirs(base_path, exist_ok=True)
        
        # Use repository name as directory name
        repo_dir = self.repository.full_name.replace('/', '_')
        return os.path.join(base_path, repo_dir)
    
    def prepare_repository(self) -> Repo:
        """
        Prepare the repository for analysis.
        
        This method clones the repository if it doesn't exist, or fetches
        the latest changes if it does.
        
        Returns:
            GitPython repository object
        """
        if os.path.exists(self.repo_path):
            logger.info(f"Repository already exists at {self.repo_path}, updating")
            self.repo = Repo(self.repo_path)
            self._update_repository()
        else:
            logger.info(f"Cloning repository to {self.repo_path}")
            self.repo = self._clone_repository()
        
        return self.repo
    
    def _clone_repository(self) -> Repo:
        """
        Clone the repository.
        
        Returns:
            GitPython repository object
            
        Raises:
            GitCommandError: If the repository cannot be cloned
        """
        try:
            # Use authentication if configured
            clone_url = self.repository.clone_url
            if 'token' in self.config:
                # Insert token into clone URL
                if clone_url.startswith('https://'):
                    clone_url = clone_url.replace('https://', f'https://{self.config["token"]}@')
            
            # Clone the repository
            return Repo.clone_from(
                clone_url,
                self.repo_path,
                progress=None  # Disable progress reporting
            )
        except GitCommandError as e:
            logger.error(f"Failed to clone repository '{self.repository.full_name}': {e}")
            raise
    
    def _update_repository(self) -> None:
        """
        Update the repository with the latest changes.
        
        Raises:
            GitCommandError: If the repository cannot be updated
        """
        try:
            # Fetch the latest changes
            origin = self.repo.remotes.origin
            origin.fetch()
            
            # Reset any local changes
            self.repo.git.reset('--hard')
            
            # Checkout the default branch
            self.repo.git.checkout(self.repository.default_branch)
            
            # Pull the latest changes
            origin.pull()
        except GitCommandError as e:
            logger.error(f"Failed to update repository '{self.repository.full_name}': {e}")
            raise
    
    def checkout_branch(self, branch_name: str) -> None:
        """
        Checkout a branch.
        
        Args:
            branch_name: Branch name
            
        Raises:
            RuntimeError: If the repository is not prepared
            GitCommandError: If the branch cannot be checked out
        """
        if not self.repo:
            raise RuntimeError("Repository is not prepared")
        
        logger.info(f"Checking out branch: {branch_name}")
        
        try:
            # Fetch the branch if it's remote
            if branch_name.startswith('origin/'):
                self.repo.git.fetch('origin', branch_name[7:])
            
            # Checkout the branch
            self.repo.git.checkout(branch_name)
        except GitCommandError as e:
            logger.error(f"Failed to checkout branch '{branch_name}': {e}")
            raise
    
    def checkout_commit(self, commit_sha: str) -> None:
        """
        Checkout a commit.
        
        Args:
            commit_sha: Commit SHA
            
        Raises:
            RuntimeError: If the repository is not prepared
            GitCommandError: If the commit cannot be checked out
        """
        if not self.repo:
            raise RuntimeError("Repository is not prepared")
        
        logger.info(f"Checking out commit: {commit_sha}")
        
        try:
            # Checkout the commit
            self.repo.git.checkout(commit_sha)
        except GitCommandError as e:
            logger.error(f"Failed to checkout commit '{commit_sha}': {e}")
            raise
    
    def checkout_pull_request(self, pull_request: PullRequest) -> None:
        """
        Checkout a pull request.
        
        Args:
            pull_request: Pull request information
            
        Raises:
            RuntimeError: If the repository is not prepared
            GitCommandError: If the pull request cannot be checked out
        """
        if not self.repo:
            raise RuntimeError("Repository is not prepared")
        
        logger.info(f"Checking out PR #{pull_request.number}")
        
        try:
            # Fetch the PR head
            head_repo = pull_request.head.get('repo')
            head_ref = pull_request.head.get('ref')
            head_sha = pull_request.head.get('sha')
            
            if head_repo and head_ref:
                # If the PR is from a fork, add the fork as a remote
                if head_repo != self.repository.full_name:
                    remote_name = f"pr_{pull_request.number}"
                    try:
                        remote = self.repo.remote(remote_name)
                    except ValueError:
                        # Remote doesn't exist, create it
                        remote_url = f"https://github.com/{head_repo}.git"
                        if 'token' in self.config:
                            remote_url = remote_url.replace('https://', f'https://{self.config["token"]}@')
                        remote = self.repo.create_remote(remote_name, remote_url)
                    
                    # Fetch the PR head
                    remote.fetch(head_ref)
                    
                    # Checkout the PR head
                    self.repo.git.checkout(f"{remote_name}/{head_ref}")
                else:
                    # If the PR is from the same repository, just checkout the branch
                    self.repo.git.fetch('origin', head_ref)
                    self.repo.git.checkout(head_ref)
            elif head_sha:
                # If we only have the SHA, checkout that
                self.checkout_commit(head_sha)
            else:
                # If we don't have enough information, fetch the PR and checkout FETCH_HEAD
                self.repo.git.fetch('origin', f"pull/{pull_request.number}/head")
                self.repo.git.checkout('FETCH_HEAD')
        except GitCommandError as e:
            logger.error(f"Failed to checkout PR #{pull_request.number}: {e}")
            raise
    
    def get_diff(self, base: str, head: str) -> str:
        """
        Get the diff between two references.
        
        Args:
            base: Base reference (branch, tag, or commit)
            head: Head reference (branch, tag, or commit)
            
        Returns:
            Diff as a string
            
        Raises:
            RuntimeError: If the repository is not prepared
            GitCommandError: If the diff cannot be generated
        """
        if not self.repo:
            raise RuntimeError("Repository is not prepared")
        
        logger.info(f"Getting diff between {base} and {head}")
        
        try:
            return self.repo.git.diff(base, head)
        except GitCommandError as e:
            logger.error(f"Failed to get diff between '{base}' and '{head}': {e}")
            raise
    
    def get_file_content(self, file_path: str, ref: Optional[str] = None) -> str:
        """
        Get the content of a file.
        
        Args:
            file_path: File path
            ref: Reference (branch, tag, or commit) (optional)
            
        Returns:
            File content as a string
            
        Raises:
            RuntimeError: If the repository is not prepared
            FileNotFoundError: If the file does not exist
            GitCommandError: If the file content cannot be retrieved
        """
        if not self.repo:
            raise RuntimeError("Repository is not prepared")
        
        logger.info(f"Getting content of file: {file_path}")
        
        try:
            if ref:
                # Get file content at a specific reference
                return self.repo.git.show(f"{ref}:{file_path}")
            else:
                # Get file content in the current working tree
                file_path_full = os.path.join(self.repo_path, file_path)
                if not os.path.exists(file_path_full):
                    raise FileNotFoundError(f"File not found: {file_path}")
                
                with open(file_path_full, 'r', encoding='utf-8') as f:
                    return f.read()
        except GitCommandError as e:
            logger.error(f"Failed to get content of file '{file_path}': {e}")
            raise
    
    def cleanup(self) -> None:
        """
        Clean up the repository.
        
        This method removes the local repository directory.
        """
        if os.path.exists(self.repo_path):
            logger.info(f"Cleaning up repository at {self.repo_path}")
            shutil.rmtree(self.repo_path, ignore_errors=True)

