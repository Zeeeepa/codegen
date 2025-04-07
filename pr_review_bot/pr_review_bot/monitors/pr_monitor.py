"""
PR monitor module for the PR Review Bot.
Monitors repositories for new pull requests and automatically reviews them.
"""

import os
import logging
import time
import traceback
import concurrent.futures
from typing import Dict, List, Any, Optional, Set
from github.Repository import Repository
from github.PullRequest import PullRequest

from ..core.github_client import GitHubClient
from ..core.pr_reviewer import PRReviewer

# Configure logging
logger = logging.getLogger(__name__)

class PRMonitor:
    """
    Monitor for new pull requests in repositories.
    Detects new PRs and automatically reviews them.
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
        self.known_prs: Dict[str, Set[int]] = {}  # Map of repo name to set of PR numbers
        self.max_workers = 10  # Number of threads to use for parallel processing
    
    def initialize_known_prs(self):
        """
        Initialize the set of known PRs for all repositories.
        This should be called once at startup.
        """
        logger.info("Initializing known PRs for all repositories")
        
        try:
            repos = self.github_client.get_all_repositories()
            
            # Use ThreadPoolExecutor to parallelize initialization
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self._initialize_repo_prs, repo): repo.full_name for repo in repos}
                
                for future in concurrent.futures.as_completed(futures):
                    repo_name = futures[future]
                    try:
                        pr_numbers = future.result()
                        self.known_prs[repo_name] = pr_numbers
                        logger.info(f"Initialized {len(pr_numbers)} PRs for {repo_name}")
                    except Exception as e:
                        logger.error(f"Error initializing PRs for {repo_name}: {e}")
                        logger.error(traceback.format_exc())
                        self.known_prs[repo_name] = set()
        except Exception as e:
            logger.error(f"Error initializing known PRs: {e}")
            logger.error(traceback.format_exc())
    
    def _initialize_repo_prs(self, repo: Repository) -> Set[int]:
        """
        Initialize PRs for a single repository.
        
        Args:
            repo: Repository object
            
        Returns:
            Set of PR numbers
        """
        # Get open PRs
        prs = list(repo.get_pulls(state="open"))
        return {pr.number for pr in prs}
    
    def check_for_new_prs(self) -> List[Dict[str, Any]]:
        """
        Check all repositories for new pull requests.
        
        Returns:
            List of dictionaries with information about new PRs
        """
        logger.info("Checking for new PRs in all repositories")
        new_prs = []
        
        try:
            repos = self.github_client.get_all_repositories()
            
            # Use ThreadPoolExecutor to parallelize PR checking
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self._check_repo_prs, repo): repo for repo in repos}
                
                for future in concurrent.futures.as_completed(futures):
                    repo = futures[future]
                    try:
                        repo_new_prs = future.result()
                        new_prs.extend(repo_new_prs)
                    except Exception as e:
                        logger.error(f"Error checking PRs for {repo.full_name}: {e}")
                        logger.error(traceback.format_exc())
        except Exception as e:
            logger.error(f"Error checking for new PRs: {e}")
            logger.error(traceback.format_exc())
        
        return new_prs
    
    def _check_repo_prs(self, repo: Repository) -> List[Dict[str, Any]]:
        """
        Check a single repository for new PRs.
        
        Args:
            repo: Repository object
            
        Returns:
            List of dictionaries with information about new PRs
        """
        repo_new_prs = []
        
        try:
            # Skip if we haven't initialized this repo yet
            if repo.full_name not in self.known_prs:
                self.known_prs[repo.full_name] = set()
                prs = list(repo.get_pulls(state="open"))
                self.known_prs[repo.full_name] = {pr.number for pr in prs}
                logger.info(f"Initialized {len(self.known_prs[repo.full_name])} PRs for {repo.full_name}")
                return []
            
            # Get current PRs
            prs = list(repo.get_pulls(state="open"))
            current_pr_numbers = {pr.number for pr in prs}
            
            # Find new PRs
            known_pr_numbers = self.known_prs[repo.full_name]
            new_pr_numbers = current_pr_numbers - known_pr_numbers
            
            # Process new PRs
            for pr_number in new_pr_numbers:
                logger.info(f"Found new PR #{pr_number} in {repo.full_name}")
                pr = self.github_client.get_pull_request(repo, pr_number)
                
                # Add to new PRs list
                repo_new_prs.append({
                    "repo_name": repo.full_name,
                    "pr_number": pr_number,
                    "pr": pr
                })
                
            # Update known PRs
            self.known_prs[repo.full_name] = current_pr_numbers
            
        except Exception as e:
            logger.error(f"Error checking PRs for {repo.full_name}: {e}")
            logger.error(traceback.format_exc())
        
        return repo_new_prs
    
    def process_new_pr(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """
        Process a new pull request by reviewing it.
        
        Args:
            repo_name: Repository name in format "owner/repo"
            pr_number: Pull request number
            
        Returns:
            Result of the operation
        """
        logger.info(f"Processing new PR #{pr_number} in {repo_name}")
        
        try:
            # Review the PR
            review_result = self.pr_reviewer.review_pr(repo_name, pr_number)
            
            return {
                "status": "success",
                "message": f"Reviewed PR #{pr_number}",
                "pr_number": pr_number,
                "review_result": review_result
            }
        except Exception as e:
            logger.error(f"Error processing PR #{pr_number} in {repo_name}: {e}")
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "message": f"Error processing PR: {str(e)}"
            }
    
    def run_monitor(self, interval: int = 300):
        """
        Run the PR monitor continuously.
        
        Args:
            interval: Interval in seconds between checks
        """
        logger.info(f"Starting PR monitor with interval {interval} seconds")
        
        # Initialize known PRs
        self.initialize_known_prs()
        
        while True:
            try:
                # Check for new PRs
                new_prs = self.check_for_new_prs()
                
                # Process new PRs in parallel
                if new_prs:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                        futures = {
                            executor.submit(self.process_new_pr, pr_info["repo_name"], pr_info["pr_number"]): 
                            pr_info for pr_info in new_prs
                        }
                        
                        for future in concurrent.futures.as_completed(futures):
                            pr_info = futures[future]
                            try:
                                result = future.result()
                                logger.info(f"Processed PR #{pr_info['pr_number']} in {pr_info['repo_name']}: {result['status']}")
                            except Exception as e:
                                logger.error(f"Error processing PR #{pr_info['pr_number']} in {pr_info['repo_name']}: {e}")
                                logger.error(traceback.format_exc())
                
                # Sleep for the specified interval
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in PR monitor: {e}")
                logger.error(traceback.format_exc())
                time.sleep(interval)  # Still sleep to avoid tight loop on error
