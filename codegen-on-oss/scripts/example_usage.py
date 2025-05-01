#!/usr/bin/env python
"""
Example script demonstrating how to use the CodebaseAnalysisHarness and CodebaseContextSnapshot.
"""

import argparse
import json
from pathlib import Path

from loguru import logger

from codegen_on_oss.analysis import CodebaseAnalysisHarness
from codegen_on_oss.snapshot import CodebaseContextSnapshot


def analyze_repo(repo_name: str, output_dir: Path, commit: str = None):
    """
    Analyze a repository and save the results.
    
    Args:
        repo_name: The full name of the repository (e.g., "owner/repo")
        output_dir: Directory to save the results
        commit: Optional commit hash to analyze
    """
    logger.info(f"Analyzing repository: {repo_name}")
    
    # Create the harness
    harness = CodebaseAnalysisHarness.from_repo(
        repo_full_name=repo_name,
        commit=commit,
    )
    
    # Analyze the codebase
    results = harness.analyze_codebase()
    
    # Save the results
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{repo_name.replace('/', '_')}_analysis.json"
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Analysis results saved to {output_path}")
    
    # Create a snapshot
    snapshot = CodebaseContextSnapshot(harness=harness)
    snapshot_id = snapshot.create_snapshot(local_path=output_dir / "snapshots")
    
    logger.info(f"Created snapshot with ID: {snapshot_id}")
    
    return results, snapshot_id


def main():
    parser = argparse.ArgumentParser(description="Analyze a GitHub repository")
    parser.add_argument("repo", help="Repository name (e.g., 'owner/repo')")
    parser.add_argument("--commit", help="Commit hash to analyze")
    parser.add_argument("--output-dir", default="./output", help="Output directory")
    
    args = parser.parse_args()
    
    analyze_repo(
        repo_name=args.repo,
        output_dir=Path(args.output_dir),
        commit=args.commit,
    )


if __name__ == "__main__":
    main()

