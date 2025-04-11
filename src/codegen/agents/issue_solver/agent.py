"""Issue Solver Agent for resolving coding issues in repositories."""

import json
import uuid
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple

from codegen import Codebase
from codegen.agents.base import Agent
from codegen.agents.code.code_agent import CodeAgent
from codegen.agents.issue_solver.utils import (
    Issue, 
    process_issue, 
    process_issues_batch, 
    calculate_success_rates,
    generate_report,
    load_predictions
)
from codegen.shared.enums.programming_language import ProgrammingLanguage


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
        language: Union[str, ProgrammingLanguage] = "python",
        disable_file_parse: bool = True,
        **kwargs
    ):
        """Initialize the IssueSolverAgent.
        
        Args:
            codebase: Optional codebase to use for solving issues
            model_provider: The model provider to use (default: "anthropic")
            model_name: The model name to use (default: "claude-3-5-sonnet-latest")
            output_dir: Optional directory to save results to
            language: Programming language of the codebase (default: "python")
            disable_file_parse: Whether to disable file parsing (default: True)
            **kwargs: Additional arguments to pass to the parent class
        """
        super().__init__(model_provider=model_provider, model_name=model_name, **kwargs)
        self.codebase = codebase
        self.output_dir = output_dir
        self.language = language if isinstance(language, ProgrammingLanguage) else ProgrammingLanguage(language)
        self.disable_file_parse = disable_file_parse
        
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
            language=self.language,
            disable_file_parse=self.disable_file_parse,
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
            language=self.language,
            disable_file_parse=self.disable_file_parse,
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
    
    def load_swe_bench_examples(
        self,
        dataset_name: str = "lite",
        subset: Optional[str] = None,
        max_examples: Optional[int] = None
    ) -> Dict[str, Issue]:
        """Load examples from the SWE Bench dataset.
        
        Args:
            dataset_name: Name of the dataset to load (default: "lite")
            subset: Optional subset of the dataset to load
            max_examples: Maximum number of examples to load
            
        Returns:
            Dictionary of Issue objects, keyed by instance ID
        """
        try:
            # Import here to avoid requiring datasets package for all users
            from datasets import load_dataset
            
            # Map dataset names to HuggingFace dataset paths
            dataset_paths = {
                "lite": "princeton-nlp/SWE-bench_Lite",
                "full": "princeton-nlp/SWE-bench",
                "verified": "princeton-nlp/SWE-bench-verified"
            }
            
            if dataset_name not in dataset_paths:
                raise ValueError(f"Unknown dataset: {dataset_name}. Available datasets: {', '.join(dataset_paths.keys())}")
            
            # Load the dataset
            dataset_path = dataset_paths[dataset_name]
            dataset = load_dataset(dataset_path)
            
            # Filter by subset if specified
            if subset:
                if "subset" in dataset["train"].features:
                    dataset = dataset.filter(lambda x: x["subset"] == subset, input_columns=["subset"])
                else:
                    print(f"Warning: Dataset {dataset_name} does not have a 'subset' feature. Ignoring subset filter.")
            
            # Convert to Issue objects
            issues = {}
            for i, example in enumerate(dataset["train"]):
                if max_examples and i >= max_examples:
                    break
                    
                issue = Issue(
                    id=example["instance_id"],
                    repo=example["repo"],
                    base_commit=example["base_commit"],
                    problem_statement=example["problem_statement"],
                    patch=example.get("patch"),
                    difficulty=example.get("difficulty"),
                    metadata={
                        "source": "swe-bench",
                        "dataset": dataset_name,
                        "subset": subset
                    }
                )
                issues[issue.id] = issue
                
            return issues
            
        except ImportError:
            print("Error: The 'datasets' package is required to load SWE Bench examples.")
            print("Please install it with: pip install datasets")
            return {}
    
    def generate_report(self, results_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Generate a report from the results of processing issues.
        
        Args:
            results_dir: Directory containing result files (default: self.output_dir)
            
        Returns:
            Dictionary with report statistics
        """
        if results_dir is None:
            results_dir = self.output_dir
            
        if not results_dir or not results_dir.exists():
            raise ValueError(f"Results directory does not exist: {results_dir}")
            
        # Load predictions
        predictions = load_predictions([results_dir])
        
        # Calculate success rates
        success_rates = calculate_success_rates(predictions)
        
        # Generate report
        report = generate_report(predictions, success_rates)
        
        # Save report to file
        report_path = results_dir / "report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
            
        print(f"Report saved to {report_path}")
        
        return report
    
    def evaluate_solution(
        self,
        result: Dict[str, Any],
        reference_patch: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Evaluate a solution against a reference patch or by running tests.
        
        Args:
            result: The result dictionary from processing an issue
            reference_patch: Optional reference patch to compare against
            **kwargs: Additional arguments to pass to the evaluation function
            
        Returns:
            Dictionary with evaluation results
        """
        # If no reference patch is provided, check if the result has one
        if not reference_patch and "reference_patch" in result:
            reference_patch = result["reference_patch"]
            
        # If we have a reference patch, compare the patches
        if reference_patch:
            from difflib import SequenceMatcher
            
            model_patch = result.get("model_patch", "")
            
            # Calculate similarity ratio
            similarity = SequenceMatcher(None, reference_patch, model_patch).ratio()
            
            # Compare modified files
            reference_files = set(result.get("reference_files", []))
            edited_files = set(result.get("edited_files", []))
            
            file_overlap = len(reference_files.intersection(edited_files))
            file_precision = file_overlap / len(edited_files) if edited_files else 0
            file_recall = file_overlap / len(reference_files) if reference_files else 0
            file_f1 = 2 * (file_precision * file_recall) / (file_precision + file_recall) if (file_precision + file_recall) > 0 else 0
            
            evaluation = {
                "patch_similarity": similarity,
                "file_precision": file_precision,
                "file_recall": file_recall,
                "file_f1": file_f1,
                "success": similarity > 0.7 or file_f1 > 0.7  # Simple heuristic for success
            }
            
            # Update the result with evaluation
            result["evaluation"] = evaluation
            
            # Save updated result to file if output directory is specified
            if self.output_dir:
                with open(self.output_dir / f"{result['issue_id']}.json", "w") as f:
                    json.dump(result, f, indent=2)
                    
            return evaluation
            
        # If no reference patch is available, we can't evaluate
        return {"success": None, "reason": "No reference patch available for evaluation"}
