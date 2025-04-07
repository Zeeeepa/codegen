"""
Branch monitor module for the PR Review Bot.
Monitors repositories for new branches and automatically reviews them.
"""

import os
import logging
import time
import traceback
import concurrent.futures
from typing import Dict, List, Any, Optional, Set, Tuple
from github.Repository import Repository
from github.Branch import Branch
from datetime import datetime, timedelta

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
        self.recent_merges: List[Dict[str, Any]] = []  # List of recent merges
        self.project_implementations: Dict[str, int] = {}  # Map of project name to implementation count
        self.max_workers = 10  # Number of threads to use for parallel processing
    
    def initialize_known_branches(self):
        """
        Initialize the set of known branches for all repositories.
        This should be called once at startup.
        """
        logger.info("Initializing known branches for all repositories")
        
        try:
            repos = self.github_client.get_all_repositories()
            
            # Use ThreadPoolExecutor to parallelize initialization
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self._initialize_repo_branches, repo): repo.full_name for repo in repos}
                
                for future in concurrent.futures.as_completed(futures):
                    repo_name = futures[future]
                    try:
                        branch_names = future.result()
                        self.known_branches[repo_name] = branch_names
                        logger.info(f"Initialized {len(branch_names)} branches for {repo_name}")
                    except Exception as e:
                        logger.error(f"Error initializing branches for {repo_name}: {e}")
                        logger.error(traceback.format_exc())
                        self.known_branches[repo_name] = set()
        except Exception as e:
            logger.error(f"Error initializing known branches: {e}")
            logger.error(traceback.format_exc())
    
    def _initialize_repo_branches(self, repo: Repository) -> Set[str]:
        """
        Initialize branches for a single repository.
        
        Args:
            repo: Repository object
            
        Returns:
            Set of branch names
        """
        branches = self.github_client.get_repository_branches(repo)
        return {branch.name for branch in branches}
    
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
            
            # Use ThreadPoolExecutor to parallelize branch checking
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self._check_repo_branches, repo): repo for repo in repos}
                
                for future in concurrent.futures.as_completed(futures):
                    repo = futures[future]
                    try:
                        repo_new_branches = future.result()
                        new_branches.extend(repo_new_branches)
                    except Exception as e:
                        logger.error(f"Error checking branches for {repo.full_name}: {e}")
                        logger.error(traceback.format_exc())
        except Exception as e:
            logger.error(f"Error checking for new branches: {e}")
            logger.error(traceback.format_exc())
        
        return new_branches
    
    def _check_repo_branches(self, repo: Repository) -> List[Dict[str, Any]]:
        """
        Check a single repository for new branches.
        
        Args:
            repo: Repository object
            
        Returns:
            List of dictionaries with information about new branches
        """
        repo_new_branches = []
        
        try:
            # Skip if we haven't initialized this repo yet
            if repo.full_name not in self.known_branches:
                self.known_branches[repo.full_name] = set()
                branches = self.github_client.get_repository_branches(repo)
                self.known_branches[repo.full_name] = {branch.name for branch in branches}
                logger.info(f"Initialized {len(self.known_branches[repo.full_name])} branches for {repo.full_name}")
                return []
            
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
                repo_new_branches.append({
                    "repo_name": repo.full_name,
                    "branch_name": branch_name,
                    "branch": branch
                })
                
            # Update known branches
            self.known_branches[repo.full_name] = current_branch_names
            
        except Exception as e:
            logger.error(f"Error checking branches for {repo.full_name}: {e}")
            logger.error(traceback.format_exc())
        
        return repo_new_branches
    
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
    
    def get_recent_merges(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get a list of recent merges across all repositories.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of dictionaries with information about recent merges
        """
        logger.info(f"Getting recent merges for the past {days} days")
        merges = []
        
        try:
            repos = self.github_client.get_all_repositories()
            since_date = datetime.now() - timedelta(days=days)
            
            # Use ThreadPoolExecutor to parallelize merge checking
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self._get_repo_merges, repo, since_date): repo for repo in repos}
                
                for future in concurrent.futures.as_completed(futures):
                    repo = futures[future]
                    try:
                        repo_merges = future.result()
                        merges.extend(repo_merges)
                        
                        # Update project implementation counts
                        for merge in repo_merges:
                            project_name = merge.get("project_name", repo.name)
                            self.project_implementations[project_name] = self.project_implementations.get(project_name, 0) + 1
                            
                    except Exception as e:
                        logger.error(f"Error getting merges for {repo.full_name}: {e}")
                        logger.error(traceback.format_exc())
        except Exception as e:
            logger.error(f"Error getting recent merges: {e}")
            logger.error(traceback.format_exc())
        
        # Sort merges by date (newest first)
        merges.sort(key=lambda x: x.get("merged_at", datetime.now()), reverse=True)
        self.recent_merges = merges
        
        return merges
    
    def _get_repo_merges(self, repo: Repository, since_date: datetime) -> List[Dict[str, Any]]:
        """
        Get recent merges for a single repository.
        
        Args:
            repo: Repository object
            since_date: Date to look back from
            
        Returns:
            List of dictionaries with information about recent merges
        """
        repo_merges = []
        
        try:
            # Get closed PRs that were merged
            pulls = repo.get_pulls(state="closed", sort="updated", direction="desc")
            
            for pr in pulls:
                # Skip if not merged or merged before since_date
                if not pr.merged or pr.merged_at < since_date:
                    continue
                
                # Extract project name from branch or PR title
                project_name = repo.name
                if pr.head.ref.startswith("feature/") or pr.head.ref.startswith("project/"):
                    parts = pr.head.ref.split("/")
                    if len(parts) > 1:
                        project_name = parts[1]
                
                # Add to merges list
                repo_merges.append({
                    "repo_name": repo.full_name,
                    "pr_number": pr.number,
                    "pr_title": pr.title,
                    "pr_url": pr.html_url,
                    "merged_at": pr.merged_at,
                    "project_name": project_name
                })
        except Exception as e:
            logger.error(f"Error getting merges for {repo.full_name}: {e}")
            logger.error(traceback.format_exc())
        
        return repo_merges
    
    def get_project_implementation_stats(self) -> Dict[str, int]:
        """
        Get statistics on project implementations.
        
        Returns:
            Dictionary mapping project names to implementation counts
        """
        # Make sure we have up-to-date data
        if not self.recent_merges:
            self.get_recent_merges()
            
        # Sort by count (highest first)
        sorted_projects = sorted(
            self.project_implementations.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return dict(sorted_projects)
    
    def generate_status_report(self) -> str:
        """
        Generate a status report with recent merges and project statistics.
        
        Returns:
            Status report as a string
        """
        # Make sure we have up-to-date data
        merges = self.recent_merges or self.get_recent_merges()
        project_stats = self.get_project_implementation_stats()
        
        # Build the report
        report = []
        report.append("# PR Review Bot Status Report")
        report.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Recent merges
        report.append("## Recent Merges")
        if merges:
            for i, merge in enumerate(merges[:10], 1):  # Show top 10
                report.append(f"{i}. [{merge['pr_title']}]({merge['pr_url']}) - {merge['repo_name']} - {merge['merged_at'].strftime('%Y-%m-%d')}")
        else:
            report.append("No recent merges found.")
        report.append("")
        
        # Project implementation stats
        report.append("## Project Implementation Stats")
        if project_stats:
            for project, count in list(project_stats.items())[:10]:  # Show top 10
                report.append(f"- {project}: {count} implementations")
        else:
            report.append("No project implementation stats available.")
        
        return "\n".join(report)
    
    def run_monitor(self, interval: int = 300):
        """
        Run the branch monitor continuously.
        
        Args:
            interval: Interval in seconds between checks
        """
        logger.info(f"Starting branch monitor with interval {interval} seconds")
        
        # Initialize known branches
        self.initialize_known_branches()
        
        # Initialize recent merges
        self.get_recent_merges()
        
        while True:
            try:
                # Check for new branches
                new_branches = self.check_for_new_branches()
                
                # Process new branches in parallel
                if new_branches:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                        futures = {
                            executor.submit(self.process_new_branch, branch_info["repo_name"], branch_info["branch_name"]): 
                            branch_info for branch_info in new_branches
                        }
                        
                        for future in concurrent.futures.as_completed(futures):
                            branch_info = futures[future]
                            try:
                                result = future.result()
                                logger.info(f"Processed branch {branch_info['branch_name']} in {branch_info['repo_name']}: {result['status']}")
                            except Exception as e:
                                logger.error(f"Error processing branch {branch_info['branch_name']} in {branch_info['repo_name']}: {e}")
                                logger.error(traceback.format_exc())
                
                # Update recent merges every hour
                if int(time.time()) % 3600 < interval:
                    self.get_recent_merges()
                
                # Sleep for the specified interval
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in branch monitor: {e}")
                logger.error(traceback.format_exc())
                time.sleep(interval)  # Still sleep to avoid tight loop on error
