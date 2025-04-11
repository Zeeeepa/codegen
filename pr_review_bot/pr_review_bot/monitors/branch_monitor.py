"""
Branch monitor for the PR Review Bot.
This module provides functionality for monitoring branches in GitHub repositories.
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

class BranchMonitor:
    """
    Monitor for branches in GitHub repositories.
    
    This class provides functionality for monitoring branches in GitHub repositories
    and triggering reviews for new or updated branches.
    """
    
    def __init__(self, github_client: GitHubClient, pr_reviewer: PRReviewer):
        """
        Initialize the branch monitor.
        
        Args:
            github_client: GitHub client
            pr_reviewer: PR reviewer
        """
        self.github_client = github_client
        self.pr_reviewer = pr_reviewer
        self.max_workers = 10
        self.skip_empty_branches = False
        self.last_check = {}
    
    def run_monitor(self, interval: int = 300) -> None:
        """
        Run the branch monitor.
        
        Args:
            interval: Interval in seconds between checks
        """
        logger.info(f"Starting branch monitor with interval {interval} seconds")
        
        while True:
            try:
                self.check_branches()
            except Exception as e:
                logger.error(f"Error checking branches: {e}")
            
            time.sleep(interval)
    
    def check_branches(self) -> None:
        """
        Check branches in all repositories.
        """
        logger.info("Checking branches in all repositories")
        
        # Get all repositories
        repos = self.github_client.get_repositories()
        
        # Check branches in each repository
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for repo in repos:
                executor.submit(self.check_repository_branches, repo["full_name"])
    
    def check_repository_branches(self, repo_name: str) -> None:
        """
        Check branches in a repository.
        
        Args:
            repo_name: Name of the repository
        """
        logger.info(f"Checking branches in repository {repo_name}")
        
        try:
            # Get the repository
            repo = self.github_client.get_repository(repo_name)
            
            # Get all branches
            branches = list(repo.get_branches())
            
            # Check each branch
            for branch in branches:
                # Skip the default branch
                if branch.name == repo.default_branch:
                    continue
                
                # Check if branch has been checked before
                branch_key = f"{repo_name}:{branch.name}"
                last_commit_sha = branch.commit.sha
                
                if branch_key in self.last_check and self.last_check[branch_key] == last_commit_sha:
                    # Branch has not changed since last check
                    continue
                
                # Update last check
                self.last_check[branch_key] = last_commit_sha
                
                # Check if branch has a PR
                prs = list(repo.get_pulls(state="open", head=f"{repo.owner.login}:{branch.name}"))
                
                if prs:
                    # Branch has a PR, skip
                    logger.info(f"Branch {branch_key} has an open PR, skipping")
                    continue
                
                # Check if branch is empty
                if self.skip_empty_branches:
                    try:
                        # Get the comparison between the default branch and this branch
                        comparison = repo.compare(repo.default_branch, branch.name)
                        
                        if not comparison.files:
                            # Branch has no changes compared to the default branch
                            logger.info(f"Branch {branch_key} has no changes, skipping")
                            continue
                    except Exception as e:
                        logger.error(f"Error comparing branches for {branch_key}: {e}")
                        continue
                
                # Branch has no PR and has changes, review it
                logger.info(f"Reviewing branch {branch_key}")
                self.review_branch(repo_name, branch.name)
        except Exception as e:
            logger.error(f"Error checking branches in repository {repo_name}: {e}")
    
    def review_branch(self, repo_name: str, branch_name: str) -> None:
        """
        Review a branch.
        
        Args:
            repo_name: Name of the repository
            branch_name: Name of the branch
        """
        logger.info(f"Reviewing branch {repo_name}:{branch_name}")
        
        try:
            # Get the repository
            repo = self.github_client.get_repository(repo_name)
            
            # Get the default branch
            default_branch = repo.default_branch
            
            # Create a PR for the branch
            pr = repo.create_pull(
                title=f"Review branch {branch_name}",
                body=f"Automated PR created by PR Review Bot to review branch {branch_name}",
                head=branch_name,
                base=default_branch
            )
            
            # Review the PR
            self.pr_reviewer.review_pr(repo_name, pr.number)
        except Exception as e:
            logger.error(f"Error reviewing branch {repo_name}:{branch_name}: {e}")
    
    def get_recent_merges(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get recent merges in all repositories.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of merge dictionaries
        """
        logger.info(f"Getting recent merges in the last {days} days")
        
        merges = []
        
        # Get all repositories
        repos = self.github_client.get_repositories()
        
        # Get merges in each repository
        for repo_data in repos:
            try:
                repo_name = repo_data["full_name"]
                repo = self.github_client.get_repository(repo_name)
                
                # Get closed PRs
                prs = repo.get_pulls(state="closed")
                
                # Filter merged PRs
                for pr in prs:
                    if pr.merged:
                        merges.append({
                            "repo_name": repo_name,
                            "pr_number": pr.number,
                            "pr_title": pr.title,
                            "merged_at": pr.merged_at,
                            "merged_by": pr.merged_by.login if pr.merged_by else None,
                            "html_url": pr.html_url
                        })
            except Exception as e:
                logger.error(f"Error getting merges for repository {repo_name}: {e}")
        
        # Sort by merged_at
        merges.sort(key=lambda x: x["merged_at"], reverse=True)
        
        return merges
    
    def get_project_implementation_stats(self) -> Dict[str, int]:
        """
        Get project implementation statistics.
        
        Returns:
            Dictionary mapping project names to implementation counts
        """
        logger.info("Getting project implementation statistics")
        
        stats = {}
        
        # Get all repositories
        repos = self.github_client.get_repositories()
        
        # Get stats for each repository
        for repo_data in repos:
            try:
                repo_name = repo_data["full_name"]
                repo = self.github_client.get_repository(repo_name)
                
                # Get the default branch
                default_branch = repo.default_branch
                
                # Get the README file
                try:
                    readme = self.github_client.get_file_content(repo_name, "README.md", default_branch)
                    
                    # Extract project name from README
                    lines = readme.split("\n")
                    project_name = None
                    
                    for line in lines:
                        if line.startswith("# "):
                            project_name = line[2:].strip()
                            break
                    
                    if project_name:
                        stats[project_name] = stats.get(project_name, 0) + 1
                except Exception:
                    # No README file
                    pass
            except Exception as e:
                logger.error(f"Error getting stats for repository {repo_name}: {e}")
        
        return stats
