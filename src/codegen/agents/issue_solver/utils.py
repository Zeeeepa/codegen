"""Utility functions for the issue solver agent."""

import json
import pprint
import random
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Set

import lox

from codegen import Codebase
from codegen.configs.models.codebase import CodebaseConfig
from codegen.shared.enums.programming_language import ProgrammingLanguage


def diff_versus_commit(git_dname, commit):
    """Take a diff of `git_dname` current contents versus the `commit`."""
    diff_cmd = f"git -C {git_dname} diff {commit}"
    diff_output = subprocess.check_output(diff_cmd.split()).decode()
    return diff_output


def files_in_patch(patch):
    """Extract the list of modified files from a unified diff patch string."""
    files = []
    for line in patch.split("\n"):
        if line.startswith("--- a/") or line.startswith("+++ b/"):
            fname = line.split("/", 1)[1]
            if fname not in files:
                files.append(fname)
    return files


@dataclass
class Issue:
    """A representation of a code issue to be solved."""
    
    id: str
    repo: str
    base_commit: str
    problem_statement: str
    patch: Optional[str] = None
    difficulty: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


def process_issue(
    issue: Issue, 
    model: str = "claude-3-5-sonnet-latest", 
    codebase: Optional[Codebase] = None,
    run_id: Optional[str] = None,
    language: Union[str, ProgrammingLanguage] = "python",
    disable_file_parse: bool = True
) -> Dict[str, Any]:
    """Process one issue using the CodeAgent.
    
    Args:
        issue: The issue to process
        model: The model to use for the agent
        codebase: Optional pre-initialized codebase
        run_id: Optional run identifier for tracking
        language: Programming language of the codebase
        disable_file_parse: Whether to disable file parsing
        
    Returns:
        A dictionary with the results of the processing
    """
    from codegen.agents.code.code_agent import CodeAgent
    
    issue_id = issue.id
    base_commit = issue.base_commit

    print("=" * 60)
    pprint.pprint(issue_id)
    print("=" * 60)
    problem_statement = issue.problem_statement
    print(problem_statement)

    # If we have a patch, extract the modified files for reference
    modified_files = []
    if issue.patch:
        modified_files = files_in_patch(issue.patch)

    # Initialize codebase if not provided
    if codebase is None:
        config = CodebaseConfig(
            disable_file_parse=disable_file_parse,
        )
        codebase = Codebase.from_repo(
            repo_full_name=issue.repo, 
            commit=base_commit, 
            language=language, 
            config=config
        )

    # Set up metadata for the agent
    metadata = {
        "run_id": run_id, 
        "issue_id": issue_id,
        "difficulty": f"difficulty_{issue.difficulty}" if issue.difficulty is not None else None
    }
    if issue.metadata:
        metadata.update(issue.metadata)
        
    tags = [str(value) for value in metadata.values() if value is not None]
    agent = CodeAgent(codebase=codebase, tags=tags, metadata=metadata)

    pprint.pprint(issue_id)
    if modified_files:
        pprint.pprint(modified_files)

    # Construct the prompt for the agent
    message = """Below is a real coding issue from a repository.
The repository has been checked out at the specified commit.
If you are already familiar with this repo, be cautious!
You are working with a specific version of the repo!
Filenames, directory names, file contents, etc. may be different than what you're used to.

Propose changes to update the repo to fix the problem below.
*** IMPORTANT: *** DO NOT MODIFY ANY TESTS unless explicitly asked to do so!
*** IMPORTANT: *** DO NOT ADD ANY TESTS unless explicitly asked to do so!

Before committing to any modifications:
1. Analyze the codebase to understand the context
2. Identify the root cause of the issue
3. Consider different approaches to fix the problem
4. Choose the most appropriate solution
5. Implement the changes carefully
6. Double-check your work with the Reflection tool

After every file edit:
- Use the Reflection tool to check your work and sanity check yourself
- Use the ViewFiles tool to make sure you didn't break anything
- Verify that your edits are correct and address the issue

Here's the issue to solve:

"""
    message += problem_statement

    try:
        # Run the agent on the issue
        result = agent.run(prompt=message)
    except Exception as agent_error:
        pprint.pprint(f"Issue ID: {issue_id} terminated with error: {agent_error}")
        raise agent_error

    # Get the diff between the current state and the original commit
    model_patch = codebase.get_diff(base=base_commit)
    pprint.pprint(model_patch)

    # Record the results
    result = {
        "issue_id": issue_id,
        "model_patch": model_patch,
        "edited_files": files_in_patch(model_patch),
    }
    
    # Add reference to modified files if we have them
    if modified_files:
        result["reference_files"] = modified_files
        
    # Add reference patch if we have it
    if issue.patch:
        result["reference_patch"] = issue.patch

    # Check if we got a successful patch
    if not model_patch:
        pprint.pprint("=" * 60)
        pprint.pprint("Failed to generate a patch")
        pprint.pprint("=" * 60)

    return result


def process_issues_batch(
    issues: Dict[str, Issue], 
    threads: int = 1,
    output_dir: Optional[Path] = None,
    model: str = "claude-3-5-sonnet-latest",
    run_id: Optional[str] = None,
    language: Union[str, ProgrammingLanguage] = "python",
    disable_file_parse: bool = True
) -> List[Dict[str, Any]]:
    """Process a batch of issues, optionally in parallel.
    
    Args:
        issues: Dictionary of issues to process, keyed by issue ID
        threads: Number of issues to process concurrently
        output_dir: Optional directory to save results to
        model: The model to use for the agent
        run_id: Optional run identifier for tracking
        language: Programming language of the codebase
        disable_file_parse: Whether to disable file parsing
        
    Returns:
        List of results from processing each issue
    """
    # Create the output directory if specified
    if output_dir:
        output_dir.mkdir(exist_ok=True, parents=True)
        
    # Track which issues have already been processed
    done_issues = set()
    if output_dir:
        # Check for existing results
        done_files = list(output_dir.glob("*.json"))
        for file in done_files:
            try:
                with open(file, "r") as f:
                    result = json.load(f)
                    if "issue_id" in result:
                        done_issues.add(result["issue_id"])
            except (json.JSONDecodeError, IOError):
                pass
                
    print(f"Found {len(done_issues)} already processed issues")
    
    # Determine which issues still need to be processed
    all_issues = set(issues.keys())
    remaining_issues = list(all_issues - done_issues)
    random.shuffle(remaining_issues)  # Randomize order for better distribution
    
    print(f"Processing {len(remaining_issues)} remaining issues")
    
    results = []
    
    # Set up parallel processing if requested
    if threads > 1:
        process_one_issue_lox = lox.process(threads)(process_issue)
        process_one_issue_func = process_one_issue_lox.scatter
        gather = process_one_issue_lox.gather
    else:
        process_one_issue_func = process_issue
    
    # Process each issue
    for issue_id in remaining_issues:
        if issue_id in done_issues:
            print(f"Skipping {issue_id} (already processed)")
            continue
            
        print(f"Processing {issue_id}")
        result = process_one_issue_func(
            issues[issue_id],
            model=model,
            run_id=run_id,
            language=language,
            disable_file_parse=disable_file_parse
        )
        
        # If we're not using parallel processing, save the result immediately
        if threads <= 1:
            results.append(result)
            
            # Save to file if output directory is specified
            if output_dir:
                with open(output_dir / f"{issue_id}.json", "w") as f:
                    json.dump(result, f, indent=2)
                    
        print("#" * 60)
    
    # If using parallel processing, gather results
    if threads > 1:
        parallel_results = gather()
        results.extend(parallel_results)
        
        # Save results to files if output directory is specified
        if output_dir:
            for result in parallel_results:
                issue_id = result.get("issue_id")
                if issue_id:
                    with open(output_dir / f"{issue_id}.json", "w") as f:
                        json.dump(result, f, indent=2)
    
    return results


def load_predictions(prediction_dirs: List[Path]) -> Dict[str, Dict[str, Any]]:
    """Load predictions from JSON files in the specified directories.
    
    Args:
        prediction_dirs: List of directories containing prediction files
        
    Returns:
        Dictionary of predictions, keyed by issue ID
    """
    predictions = {}
    
    for pred_dir in prediction_dirs:
        if not pred_dir.exists() or not pred_dir.is_dir():
            print(f"Warning: Prediction directory {pred_dir} does not exist or is not a directory")
            continue
            
        # Find all JSON files in the directory
        json_files = list(pred_dir.glob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, "r") as f:
                    prediction = json.load(f)
                    
                # Check if this is a valid prediction
                if isinstance(prediction, dict) and "issue_id" in prediction:
                    # Store the file path for reference
                    prediction["json_fname"] = json_file
                    predictions[prediction["issue_id"]] = prediction
                    
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading prediction from {json_file}: {e}")
                
    return predictions


def calculate_success_rates(predictions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate success rates from predictions.
    
    Args:
        predictions: Dictionary of predictions, keyed by issue ID
        
    Returns:
        Dictionary with success rate statistics
    """
    # Track various categories
    categories = {
        "total": set(predictions.keys()),
        "with_patch": set(),
        "without_patch": set(),
        "evaluated": set(),
        "successful": set(),
        "failed": set(),
    }
    
    # Categorize predictions
    for issue_id, prediction in predictions.items():
        # Check if the prediction has a patch
        if prediction.get("model_patch"):
            categories["with_patch"].add(issue_id)
        else:
            categories["without_patch"].add(issue_id)
            
        # Check if the prediction has been evaluated
        if "evaluation" in prediction:
            categories["evaluated"].add(issue_id)
            
            # Check if the evaluation was successful
            if prediction["evaluation"].get("success") is True:
                categories["successful"].add(issue_id)
            elif prediction["evaluation"].get("success") is False:
                categories["failed"].add(issue_id)
    
    # Calculate success rates
    total = len(categories["total"])
    with_patch = len(categories["with_patch"])
    evaluated = len(categories["evaluated"])
    successful = len(categories["successful"])
    
    success_rates = {
        "total": total,
        "with_patch": with_patch,
        "with_patch_rate": with_patch / total if total > 0 else 0,
        "evaluated": evaluated,
        "evaluated_rate": evaluated / total if total > 0 else 0,
        "successful": successful,
        "successful_rate": successful / evaluated if evaluated > 0 else 0,
        "overall_success_rate": successful / total if total > 0 else 0,
    }
    
    return success_rates


def generate_report(
    predictions: Dict[str, Dict[str, Any]],
    success_rates: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate a report from predictions and success rates.
    
    Args:
        predictions: Dictionary of predictions, keyed by issue ID
        success_rates: Dictionary with success rate statistics
        
    Returns:
        Dictionary with report statistics
    """
    # Group predictions by various criteria
    by_difficulty = {}
    by_repo = {}
    
    for issue_id, prediction in predictions.items():
        # Group by difficulty
        difficulty = prediction.get("metadata", {}).get("difficulty")
        if difficulty:
            if difficulty not in by_difficulty:
                by_difficulty[difficulty] = []
            by_difficulty[difficulty].append(issue_id)
            
        # Group by repository
        repo = prediction.get("repo") or issue_id.split("#")[0] if "#" in issue_id else None
        if repo:
            if repo not in by_repo:
                by_repo[repo] = []
            by_repo[repo].append(issue_id)
    
    # Calculate success rates by difficulty
    difficulty_stats = {}
    for difficulty, issue_ids in by_difficulty.items():
        successful = sum(1 for issue_id in issue_ids if 
                         "evaluation" in predictions[issue_id] and 
                         predictions[issue_id]["evaluation"].get("success") is True)
        
        difficulty_stats[difficulty] = {
            "total": len(issue_ids),
            "successful": successful,
            "success_rate": successful / len(issue_ids) if len(issue_ids) > 0 else 0
        }
    
    # Calculate success rates by repository
    repo_stats = {}
    for repo, issue_ids in by_repo.items():
        successful = sum(1 for issue_id in issue_ids if 
                         "evaluation" in predictions[issue_id] and 
                         predictions[issue_id]["evaluation"].get("success") is True)
        
        repo_stats[repo] = {
            "total": len(issue_ids),
            "successful": successful,
            "success_rate": successful / len(issue_ids) if len(issue_ids) > 0 else 0
        }
    
    # Compile the report
    report = {
        "timestamp": str(Path.ctime(Path.cwd())),
        "overall": success_rates,
        "by_difficulty": difficulty_stats,
        "by_repo": repo_stats,
        "predictions": {
            issue_id: {
                "has_patch": bool(prediction.get("model_patch")),
                "success": prediction.get("evaluation", {}).get("success"),
                "edited_files": prediction.get("edited_files", []),
                "reference_files": prediction.get("reference_files", []),
            }
            for issue_id, prediction in predictions.items()
        }
    }
    
    return report
