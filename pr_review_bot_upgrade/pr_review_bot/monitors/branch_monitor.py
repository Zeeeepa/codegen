"""
Branch monitor module for the PR Review Bot.
Monitors repositories for new branches and automatically reviews them.
"""

import os
import logging
import time
import traceback
from typing import Dict, List, Any, Optional, Set
from github.Repository import Repository
from github.Branch import Branch

from ..core.github_client import GitHubClient
from ..core.pr_reviewer import PRReviewer

# Configure logging
logger = logging.getLogger(__name__)

class BranchMonitor:
    """
    Monitor for new branches in repositories.
    Detects new branches and can automatically create PRs for them.
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
        self.known_branches: Dict[str, Set[str]] = {}  # Map of repo name to set of branch names
    
    def initialize_known_branches(self):
        """
        Initialize the set of known branches for all repositories.
        This should be called once at startup.
        """
        logger.info("Initializing known branches for all repositories")
        
        try:
            repos = self.github_client.get_all_repositories()
            
            for repo in repos:
                try:
                    branches = self.github_client.get_repository_branches(repo)
                    branch_names = {branch.name for branch in branches}
                    self.known_branches[repo.full_name] = branch_names
                    logger.info(f"Initialized {len(branch_names)} branches for {repo.full_name}")
                except Exception as e:
                    logger.error(f"Error initializing branches for {repo.full_name}: {e}")
                    logger.error(traceback.format_exc())
                    self.known_branches[repo.full_name] = set()
        except Exception as e:
            logger.error(f"Error initializing known branches: {e}")
            logger.error(traceback.format_exc())
    
    def check_for_new_branches(self) -> List[Dict[str, Any]]:
        """
        Check all repositories for new branches.
        
        Returns:
            List of dictionaries with information about new branches
        """
        logger.info("Checking for new branches in all repositories")
        new_branches = []
        
        try:
            repos = self.github_client.get_all_repositories()
            
            for repo in repos:
                try:
                    # Skip if we haven't initialized this repo yet
                    if repo.full_name not in self.known_branches:
                        self.known_branches[repo.full_name] = set()
                        branches = self.github_client.get_repository_branches(repo)
                        self.known_branches[repo.full_name] = {branch.name for branch in branches}
                        logger.info(f"Initialized {len(self.known_branches[repo.full_name])} branches for {repo.full_name}")
                        continue
                    
                    # Get current branches
                    branches = self.github_client.get_repository_branches(repo)
                    current_branch_names = {branch.name for branch in branches}
                    
                    # Find new branches
                    known_branch_names = self.known_branches[repo.full_name]
                    new_branch_names = current_branch_names - known_branch_names
                    
                    # Process new branches
                    for branch_name in new_branch_names:
                        logger.info(f"Found new branch {branch_name} in {repo.full_name}")
                        branch = self.github_client.get_branch(repo, branch_name)
                        
                        # Skip if it's the default branch
                        if branch_name == repo.default_branch:
                            continue
                        
                        # Add to new branches list
                        new_branches.append({
                            "repo_name": repo.full_name,
                            "branch_name": branch_name,
                            "branch": branch
                        })
                        
                    # Update known branches
                    self.known_branches[repo.full_name] = current_branch_names
                    
                except Exception as e:
                    logger.error(f"Error checking branches for {repo.full_name}: {e}")
                    logger.error(traceback.format_exc())
        except Exception as e:
            logger.error(f"Error checking for new branches: {e}")
            logger.error(traceback.format_exc())
        
        return new_branches
    
    def process_new_branch(self, repo_name: str, branch_name: str) -> Dict[str, Any]:
        """
        Process a new branch by creating a PR for it.
        
        Args:
            repo_name: Repository name in format "owner/repo"
            branch_name: Branch name
            
        Returns:
            Result of the operation
        """
        logger.info(f"Processing new branch {branch_name} in {repo_name}")
        
        try:
            # Get repository
            repo = self.github_client.get_repository(repo_name)
            
            # Skip if it's the default branch
            if branch_name == repo.default_branch:
                return {
                    "status": "skipped",
                    "message": f"Branch {branch_name} is the default branch"
                }
            
            # Check if a PR already exists for this branch
            existing_prs = list(repo.get_pulls(state="open", head=f"{repo.owner.login}:{branch_name}"))
            if existing_prs:
                logger.info(f"PR already exists for branch {branch_name} in {repo_name}")
                return {
                    "status": "skipped",
                    "message": f"PR already exists for branch {branch_name}",
                    "pr_number": existing_prs[0].number,
                    "pr_url": existing_prs[0].html_url
                }
            
            # Create a PR for the branch
            pr_title = f"Auto PR: {branch_name}"
            pr_body = f"Automatically created PR for branch {branch_name}"
            
            pr = self.github_client.create_pull_request(
                repo=repo,
                title=pr_title,
                body=pr_body,
                head=branch_name,
                base=repo.default_branch
            )
            
            logger.info(f"Created PR #{pr.number} for branch {branch_name} in {repo_name}")
            
            # Review the PR
            review_result = self.pr_reviewer.review_pr(repo_name, pr.number)
            
            return {
                "status": "success",
                "message": f"Created and reviewed PR for branch {branch_name}",
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "review_result": review_result
            }
        except Exception as e:
            logger.error(f"Error processing branch {branch_name} in {repo_name}: {e}")
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "message": f"Error processing branch: {str(e)}"
            }
    
    def run_monitor(self, interval: int = 300):
        """
        Run the branch monitor continuously.
        
        Args:
            interval: Interval in seconds between checks
        """
        logger.info(f"Starting branch monitor with interval {interval} seconds")
        
        # Initialize known branches
        self.initialize_known_branches()
        
        while True:
            try:
                # Check for new branches
                new_branches = self.check_for_new_branches()
                
                # Process new branches
                for branch_info in new_branches:
                    self.process_new_branch(branch_info["repo_name"], branch_info["branch_name"])
                
                # Sleep for the specified interval
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in branch monitor: {e}")
                logger.error(traceback.format_exc())
                time.sleep(interval)  # Still sleep to avoid tight loop on error
