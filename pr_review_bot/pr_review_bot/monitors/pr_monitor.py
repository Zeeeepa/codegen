"""
PR monitor for the PR Review Bot.
This module provides functionality for monitoring pull requests in GitHub repositories.
"""

import os
import logging
import time
import threading
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor

from ..core.github_client import GitHubClient
from ..core.pr_reviewer import PRReviewer

logger = logging.getLogger(__name__)

class PRMonitor:
    """
    Monitor for pull requests in GitHub repositories.
    
    This class provides functionality for monitoring pull requests in GitHub repositories
    and triggering reviews for new or updated PRs.
    """
    
    def __init__(self, github_client: GitHubClient, pr_reviewer: PRReviewer):
        """
        Initialize the PR monitor.
        
        Args:
            github_client: GitHub client
            pr_reviewer: PR reviewer
        """
        self.github_client = github_client
        self.pr_reviewer = pr_reviewer
        self.max_workers = 10
        self.last_check = {}
    
    def run_monitor(self, interval: int = 300) -> None:
        """
        Run the PR monitor.
        
        Args:
            interval: Interval in seconds between checks
        """
        logger.info(f"Starting PR monitor with interval {interval} seconds")
        
        while True:
            try:
                self.check_pull_requests()
            except Exception as e:
                logger.error(f"Error checking pull requests: {e}")
            
            time.sleep(interval)
    
    def check_pull_requests(self) -> None:
        """
        Check pull requests in all repositories.
        """
        logger.info("Checking pull requests in all repositories")
        
        # Get all repositories
        repos = self.github_client.get_repositories()
        
        # Check pull requests in each repository
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for repo in repos:
                executor.submit(self.check_repository_pull_requests, repo["full_name"])
    
    def check_repository_pull_requests(self, repo_name: str) -> None:
        """
        Check pull requests in a repository.
        
        Args:
            repo_name: Name of the repository
        """
        logger.info(f"Checking pull requests in repository {repo_name}")
        
        try:
            # Get the repository
            repo = self.github_client.get_repository(repo_name)
            
            # Get all open pull requests
            pull_requests = list(repo.get_pulls(state="open"))
            
            # Check each pull request
            for pr in pull_requests:
                # Check if PR has been checked before
                pr_key = f"{repo_name}:{pr.number}"
                last_commit_sha = pr.head.sha
                
                if pr_key in self.last_check and self.last_check[pr_key] == last_commit_sha:
                    # PR has not changed since last check
                    continue
                
                # Update last check
                self.last_check[pr_key] = last_commit_sha
                
                # Check if PR has a review label
                has_review_label = False
                for label in pr.labels:
                    if label.name.lower() in ["needs-review", "review", "codegen"]:
                        has_review_label = True
                        break
                
                # Review the PR if it has a review label or if it's a new PR
                if has_review_label or pr_key not in self.last_check:
                    logger.info(f"Reviewing PR {pr_key}")
                    self.review_pull_request(repo_name, pr.number)
        except Exception as e:
            logger.error(f"Error checking pull requests in repository {repo_name}: {e}")
    
    def review_pull_request(self, repo_name: str, pr_number: int) -> None:
        """
        Review a pull request.
        
        Args:
            repo_name: Name of the repository
            pr_number: Number of the pull request
        """
        logger.info(f"Reviewing PR {repo_name}#{pr_number}")
        
        try:
            # Review the PR
            self.pr_reviewer.review_pr(repo_name, pr_number)
        except Exception as e:
            logger.error(f"Error reviewing PR {repo_name}#{pr_number}: {e}")
    
    def get_open_pull_requests(self) -> List[Dict[str, Any]]:
        """
        Get all open pull requests in all repositories.
        
        Returns:
            List of pull request dictionaries
        """
        logger.info("Getting all open pull requests")
        
        pull_requests = []
        
        # Get all repositories
        repos = self.github_client.get_repositories()
        
        # Get pull requests in each repository
        for repo_data in repos:
            try:
                repo_name = repo_data["full_name"]
                repo = self.github_client.get_repository(repo_name)
                
                # Get all open pull requests
                prs = repo.get_pulls(state="open")
                
                # Add to list
                for pr in prs:
                    pull_requests.append({
                        "repo_name": repo_name,
                        "pr_number": pr.number,
                        "pr_title": pr.title,
                        "pr_url": pr.html_url,
                        "created_at": pr.created_at,
                        "updated_at": pr.updated_at,
                        "user": pr.user.login,
                        "head_branch": pr.head.ref,
                        "base_branch": pr.base.ref
                    })
            except Exception as e:
                logger.error(f"Error getting pull requests for repository {repo_name}: {e}")
        
        # Sort by updated_at
        pull_requests.sort(key=lambda x: x["updated_at"], reverse=True)
        
        return pull_requests
