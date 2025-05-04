"""
SWE Harness Agent Example

This script demonstrates how to use the SWE harness agent to analyze commits and pull requests.
"""

import argparse
import codegen
import logging
import os
from typing import Dict, Optional

from codegen import Codebase
from codegen_on_oss.analysis.swe_harness_agent import SWEHarnessAgent
from codegen_on_oss.snapshot.codebase_snapshot import SnapshotManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_snapshot_manager(repo_path: str) -> SnapshotManager:
    """
    Set up a snapshot manager for the repository.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        SnapshotManager instance
    """
    # Create a snapshot directory if it doesn't exist
    snapshot_dir = os.path.join(repo_path, ".snapshots")
    os.makedirs(snapshot_dir, exist_ok=True)
    
    return SnapshotManager(snapshot_dir)


@codegen.function("codegen-on-oss-swe-harness")
def run(
    repo_path: str,
    pr_number: Optional[int] = None,
    commit_hash: Optional[str] = None,
    github_token: Optional[str] = None
) -> Dict:
    """
    Run the SWE harness agent on a repository.
    
    This function:
    1. Sets up a snapshot manager for the repository
    2. Initializes the SWE harness agent
    3. Analyzes a PR or commit based on the provided parameters
    4. Returns the analysis results
    
    Args:
        repo_path: Path to the repository
        pr_number: Optional PR number to analyze
        commit_hash: Optional commit hash to analyze
        github_token: Optional GitHub token for API access
        
    Returns:
        dict: The analysis results
    """
    # Create a codebase from the repository
    codebase = Codebase(repo_path)
    
    # Set up the snapshot manager
    snapshot_manager = setup_snapshot_manager(repo_path)
    
    # Initialize the SWE harness agent
    agent = SWEHarnessAgent(
        codebase=codebase,
        snapshot_manager=snapshot_manager,
        github_token=github_token
    )
    
    if pr_number:
        logger.info(f"Analyzing PR #{pr_number}...")
        results = agent.analyze_pr(pr_number)
    elif commit_hash:
        logger.info(f"Analyzing commit {commit_hash}...")
        results = agent.analyze_commit(commit_hash)
    else:
        logger.info("No PR or commit specified. Analyzing the current codebase...")
        results = agent.analyze_codebase()
    
    logger.info("Analysis complete!")
    return results


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="SWE Harness Agent Example")
    parser.add_argument("--repo", required=True, help="Path to the repository")
    parser.add_argument("--pr", type=int, help="PR number to analyze")
    parser.add_argument("--commit", help="Commit hash to analyze")
    parser.add_argument("--github-token", help="GitHub token for API access")
    parser.add_argument("--output", help="Output file for analysis results (JSON)")
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    if args.pr and args.commit:
        logger.error("Cannot specify both PR and commit. Please choose one.")
        exit(1)
    
    results = run(args.repo, args.pr, args.commit, args.github_token)
    
    if args.output:
        import json
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {args.output}")
    else:
        import json
        print(json.dumps(results, indent=2))

