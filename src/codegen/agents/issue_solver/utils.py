"""Utility functions for the issue solver agent."""

import json
import pprint
import random
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

import lox

from codegen import Codebase
from codegen.configs.models.codebase import CodebaseConfig


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
    run_id: Optional[str] = None
) -> Dict[str, Any]:
    """Process one issue using the CodeAgent.
    
    Args:
        issue: The issue to process
        model: The model to use for the agent
        codebase: Optional pre-initialized codebase
        run_id: Optional run identifier for tracking
        
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
            disable_file_parse=True,  # Disable the graph AND disable file parsing (file.edit only)
        )
        codebase = Codebase.from_repo(
            repo_full_name=issue.repo, 
            commit=base_commit, 
            language="python", 
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
    message = """I need you to solve a coding issue in this repository.
The issue is described below.

Before making any modifications, analyze the codebase to understand the context.
After understanding the issue, propose and implement changes to fix the problem.

After every file edit, check your work to ensure you didn't break anything and that your edits are correct.
Use the Reflection tool if you get stuck or need to reassess your approach.

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
    run_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Process a batch of issues, optionally in parallel.
    
    Args:
        issues: Dictionary of issues to process, keyed by issue ID
        threads: Number of issues to process concurrently
        output_dir: Optional directory to save results to
        model: The model to use for the agent
        run_id: Optional run identifier for tracking
        
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
            run_id=run_id
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
