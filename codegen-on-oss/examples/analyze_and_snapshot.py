#!/usr/bin/env python
"""
Example script demonstrating how to use the CodebaseAnalysisHarness and CodebaseContextSnapshot.

This script:
1. Creates a harness from a repository
2. Analyzes the codebase
3. Creates a snapshot of the analysis results
4. Loads the snapshot and verifies it
"""

import argparse
import json
import os
from pathlib import Path

from loguru import logger

from codegen_on_oss.analysis.harness_integration import CodebaseAnalysisHarness
from codegen_on_oss.bucket_store import BucketStore
from codegen_on_oss.snapshot.context_snapshot import CodebaseContextSnapshot


def main():
    """Run the example script."""
    parser = argparse.ArgumentParser(description="Analyze a codebase and create a snapshot")
    parser.add_argument(
        "--repo",
        type=str,
        required=True,
        help="Repository to analyze (e.g., 'owner/repo')",
    )
    parser.add_argument(
        "--commit",
        type=str,
        help="Optional commit hash to checkout",
    )
    parser.add_argument(
        "--language",
        type=str,
        default="python",
        choices=["python", "typescript", "javascript"],
        help="Primary language of the codebase",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="snapshots",
        help="Directory to save snapshots to",
    )
    parser.add_argument(
        "--s3-bucket",
        type=str,
        help="Optional S3 bucket name for snapshot storage",
    )
    parser.add_argument(
        "--s3-endpoint",
        type=str,
        default="https://s3.amazonaws.com",
        help="S3 endpoint URL",
    )
    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize BucketStore if S3 bucket is provided
    bucket_store = None
    if args.s3_bucket:
        bucket_store = BucketStore(
            bucket_name=args.s3_bucket,
            endpoint_url=args.s3_endpoint,
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        )
        logger.info(f"Initialized BucketStore with bucket: {args.s3_bucket}")

    # Step 1: Create a harness from the repository
    logger.info(f"Creating harness for repository: {args.repo}")
    harness = CodebaseAnalysisHarness.from_repo(
        repo_full_name=args.repo,
        commit=args.commit,
        language=args.language,
    )

    # Step 2: Analyze the codebase
    logger.info("Analyzing codebase...")
    results = harness.analyze_codebase()
    
    # Save analysis results to a file
    analysis_file = output_dir / f"{args.repo.replace('/', '_')}_analysis.json"
    with open(analysis_file, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Analysis results saved to {analysis_file}")

    # Step 3: Create a snapshot
    logger.info("Creating snapshot...")
    snapshot = CodebaseContextSnapshot(
        harness=harness,
        bucket_store=bucket_store,
    )
    snapshot_id = snapshot.create_snapshot(local_path=output_dir)
    logger.info(f"Created snapshot with ID: {snapshot_id}")

    # Step 4: Load the snapshot and verify
    logger.info(f"Loading snapshot with ID: {snapshot_id}")
    loaded_snapshot = CodebaseContextSnapshot.load_snapshot(
        snapshot_id=snapshot_id,
        local_path=output_dir,
        bucket_store=bucket_store,
    )
    
    if loaded_snapshot:
        logger.info("Successfully loaded snapshot")
        logger.info(f"Snapshot data: {loaded_snapshot.snapshot_data}")
    else:
        logger.error("Failed to load snapshot")


if __name__ == "__main__":
    main()

