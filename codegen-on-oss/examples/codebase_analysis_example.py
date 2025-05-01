#!/usr/bin/env python
"""
Example script demonstrating how to use the CodebaseAnalysisHarness.
"""

import json
import sys
from pathlib import Path

from codegen_on_oss.analysis import CodebaseAnalysisHarness
from codegen_on_oss.snapshot import CodebaseContextSnapshot


def main():
    """
    Main function to demonstrate the CodebaseAnalysisHarness.
    """
    # Check if a repository name was provided
    if len(sys.argv) < 2:
        print("Usage: python codebase_analysis_example.py <repo_full_name> [commit]")
        sys.exit(1)

    repo_full_name = sys.argv[1]
    commit = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Analyzing repository: {repo_full_name}")
    print(f"Commit: {commit or 'latest'}")

    # Create a harness
    harness = CodebaseAnalysisHarness.from_repo(
        repo_full_name=repo_full_name,
        commit=commit,
    )

    # Analyze the codebase
    results = harness.analyze_codebase()

    # Print the results
    print("\nAnalysis Results:")
    print(json.dumps(results, indent=2))

    # Create a snapshot
    snapshot = CodebaseContextSnapshot(harness)
    snapshot_id = snapshot.create_snapshot()

    print(f"\nSnapshot created with ID: {snapshot_id}")

    # Get a diff
    diff = harness.get_diff()
    if diff:
        print("\nDiff from base commit:")
        print(diff)
    else:
        print("\nNo changes detected from base commit.")

    # Save results to a file
    output_file = Path(f"{repo_full_name.replace('/', '_')}_analysis.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {output_file}")


if __name__ == "__main__":
    main()

