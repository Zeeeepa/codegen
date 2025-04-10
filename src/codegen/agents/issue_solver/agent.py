"""Issue Solver Agent for resolving coding issues in repositories."""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from codegen import Codebase
from codegen.agents.base import Agent
from codegen.agents.code.code_agent import CodeAgent
from codegen.agents.issue_solver.utils import Issue, process_issue, process_issues_batch


class IssueSolverAgent(Agent):
    """Agent for solving coding issues in repositories.
    
    This agent is designed to analyze and fix coding issues in repositories.
    It can process individual issues or batches of issues, and can run in
    parallel for faster processing.
    """
    
    def __init__(
        self,
        codebase: Optional[Codebase] = None,
        model_provider: str = "anthropic",
        model_name: str = "claude-3-5-sonnet-latest",
        output_dir: Optional[Path] = None,
        **kwargs
    ):
        """Initialize the IssueSolverAgent.
        
        Args:
            codebase: Optional codebase to use for solving issues
            model_provider: The model provider to use (default: "anthropic")
            model_name: The model name to use (default: "claude-3-5-sonnet-latest")
            output_dir: Optional directory to save results to
            **kwargs: Additional arguments to pass to the parent class
        """
        super().__init__(model_provider=model_provider, model_name=model_name, **kwargs)
        self.codebase = codebase
        self.output_dir = output_dir
        
        if self.output_dir:
            self.output_dir.mkdir(exist_ok=True, parents=True)
    
    def run(
        self, 
        issue_or_issues: Union[Issue, Dict[str, Issue], List[Issue]],
        threads: int = 1,
        run_id: Optional[str] = None,
        **kwargs
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Run the agent on one or more issues.
        
        Args:
            issue_or_issues: A single issue or a collection of issues to process
            threads: Number of issues to process concurrently (default: 1)
            run_id: Optional run identifier for tracking
            **kwargs: Additional arguments to pass to the processing functions
            
        Returns:
            A dictionary with the results of processing a single issue,
            or a list of dictionaries with the results of processing multiple issues
        """
        # Generate a run ID if not provided
        if run_id is None:
            run_id = str(uuid.uuid4())
            
        # Process a single issue
        if isinstance(issue_or_issues, Issue):
            return self._process_single_issue(issue_or_issues, run_id, **kwargs)
            
        # Process a dictionary of issues
        elif isinstance(issue_or_issues, dict):
            return self._process_issues_dict(issue_or_issues, threads, run_id, **kwargs)
            
        # Process a list of issues
        elif isinstance(issue_or_issues, list):
            # Convert list to dictionary
            issues_dict = {issue.id: issue for issue in issue_or_issues}
            return self._process_issues_dict(issues_dict, threads, run_id, **kwargs)
            
        else:
            raise ValueError(f"Unsupported issue type: {type(issue_or_issues)}")
    
    def _process_single_issue(
        self, 
        issue: Issue, 
        run_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Process a single issue.
        
        Args:
            issue: The issue to process
            run_id: Run identifier for tracking
            **kwargs: Additional arguments to pass to process_issue
            
        Returns:
            A dictionary with the results of processing the issue
        """
        result = process_issue(
            issue=issue,
            model=self.model_name,
            codebase=self.codebase,
            run_id=run_id,
            **kwargs
        )
        
        # Save result to file if output directory is specified
        if self.output_dir:
            with open(self.output_dir / f"{issue.id}.json", "w") as f:
                json.dump(result, f, indent=2)
                
        return result
    
    def _process_issues_dict(
        self, 
        issues: Dict[str, Issue], 
        threads: int,
        run_id: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Process a dictionary of issues.
        
        Args:
            issues: Dictionary of issues to process, keyed by issue ID
            threads: Number of issues to process concurrently
            run_id: Run identifier for tracking
            **kwargs: Additional arguments to pass to process_issues_batch
            
        Returns:
            List of dictionaries with the results of processing each issue
        """
        return process_issues_batch(
            issues=issues,
            threads=threads,
            output_dir=self.output_dir,
            model=self.model_name,
            run_id=run_id,
            **kwargs
        )
        
    def solve_github_issue(
        self,
        repo: str,
        issue_number: int,
        base_branch: str = "main",
        **kwargs
    ) -> Dict[str, Any]:
        """Solve a GitHub issue.
        
        Args:
            repo: The repository name (e.g., "owner/repo")
            issue_number: The issue number to solve
            base_branch: The branch to use as the base for solving the issue
            **kwargs: Additional arguments to pass to process_issue
            
        Returns:
            A dictionary with the results of processing the issue
        """
        # Import here to avoid circular imports
        from codegen.extensions.github.client import GithubClient
        
        # Get the GitHub client
        github_client = GithubClient()
        
        # Get the issue
        issue_data = github_client.get_issue(repo, issue_number)
        
        # Create an Issue object
        issue = Issue(
            id=f"{repo}#{issue_number}",
            repo=repo,
            base_commit=base_branch,
            problem_statement=issue_data["body"],
            metadata={
                "title": issue_data["title"],
                "url": issue_data["html_url"],
                "user": issue_data["user"]["login"],
                "created_at": issue_data["created_at"],
                "updated_at": issue_data["updated_at"],
                "labels": [label["name"] for label in issue_data["labels"]],
            }
        )
        
        # Process the issue
        return self._process_single_issue(issue, run_id=f"github-{issue_number}", **kwargs)
        
    def create_pull_request(
        self,
        result: Dict[str, Any],
        branch_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a pull request from the results of solving an issue.
        
        Args:
            result: The result dictionary from processing an issue
            branch_name: Optional name for the branch to create
            **kwargs: Additional arguments to pass to the GitHub client
            
        Returns:
            A dictionary with the pull request information
        """
        # Import here to avoid circular imports
        from codegen.extensions.github.client import GithubClient
        
        # Get the GitHub client
        github_client = GithubClient()
        
        # Extract issue information
        issue_id = result["issue_id"]
        
        # Generate branch name if not provided
        if branch_name is None:
            branch_name = f"fix-{issue_id.replace('/', '-').replace('#', '-')}"
            
        # Create a new branch
        github_client.create_branch(branch_name)
        
        # Apply the patch
        patch = result["model_patch"]
        if not patch:
            raise ValueError("No patch to apply")
            
        # Create the pull request
        pr = github_client.create_pull_request(
            title=f"Fix {issue_id}",
            body=f"This PR fixes issue {issue_id}.\n\nAutomatically generated by IssueSolverAgent.",
            branch=branch_name,
            **kwargs
        )
        
        return pr
