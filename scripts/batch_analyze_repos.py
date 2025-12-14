#!/usr/bin/env python3
"""
Batch Repository Analysis Script

Automatically analyzes all repositories using Codegen AI agents.
Creates comprehensive analysis reports and PRs for each repository.

Usage:
    python scripts/batch_analyze_repos.py --org-id YOUR_ORG_ID --token YOUR_TOKEN

Environment Variables:
    CODEGEN_ORG_ID: Organization ID
    CODEGEN_API_TOKEN: API authentication token
    GITHUB_TOKEN: GitHub personal access token (optional)
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codegen.batch_analysis import BatchAnalyzer, AnalysisPromptBuilder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("batch_analysis.log"),
    ],
)

logger = logging.getLogger(__name__)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Batch analyze repositories using Codegen AI agents"
    )

    # Required arguments
    parser.add_argument(
        "--org-id",
        type=str,
        default=os.getenv("CODEGEN_ORG_ID"),
        help="Codegen organization ID (or set CODEGEN_ORG_ID env var)",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=os.getenv("CODEGEN_API_TOKEN"),
        help="Codegen API token (or set CODEGEN_API_TOKEN env var)",
    )
    parser.add_argument(
        "--github-token",
        type=str,
        default=os.getenv("GITHUB_TOKEN"),
        help="GitHub token (or set GITHUB_TOKEN env var)",
    )

    # Optional arguments
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,
        help="Seconds between agent requests (default: 1.0)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="Timeout per analysis in minutes (default: 15)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="Libraries/API",
        help="Output directory for analysis files (default: Libraries/API)",
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        help="Path to save/resume checkpoint file",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from checkpoint file",
    )

    # Filtering options
    parser.add_argument(
        "--language",
        type=str,
        help="Filter by programming language",
    )
    parser.add_argument(
        "--topics",
        type=str,
        help="Comma-separated list of required topics",
    )
    parser.add_argument(
        "--min-stars",
        type=int,
        help="Minimum stars required",
    )

    # Analysis type
    parser.add_argument(
        "--analysis-type",
        type=str,
        choices=["default", "security", "api", "dependencies"],
        default="default",
        help="Type of analysis to perform",
    )

    # Control flags
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Don't wait for agent runs to complete",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be analyzed without executing",
    )

    args = parser.parse_args()

    # Validate required arguments
    if not args.org_id:
        parser.error("--org-id required (or set CODEGEN_ORG_ID environment variable)")
    if not args.token:
        parser.error("--token required (or set CODEGEN_API_TOKEN environment variable)")

    logger.info("=" * 80)
    logger.info("Batch Repository Analysis Tool")
    logger.info("=" * 80)
    logger.info(f"Organization ID: {args.org_id}")
    logger.info(f"Rate Limit: {args.rate_limit}s per request")
    logger.info(f"Timeout: {args.timeout} minutes per analysis")
    logger.info(f"Output Directory: {args.output_dir}")
    logger.info(f"Analysis Type: {args.analysis_type}")
    logger.info("=" * 80)

    try:
        # Initialize analyzer
        if args.resume and args.checkpoint:
            logger.info(f"Resuming from checkpoint: {args.checkpoint}")
            analyzer = BatchAnalyzer.from_checkpoint(args.checkpoint)
            # Must set credentials after loading
            analyzer.org_id = args.org_id
            analyzer.token = args.token
        else:
            analyzer = BatchAnalyzer(
                org_id=args.org_id,
                token=args.token,
                github_token=args.github_token,
            )

        # Configure analyzer
        analyzer.set_rate_limit(args.rate_limit)
        analyzer.set_timeout(args.timeout)
        analyzer.set_output_dir(args.output_dir)

        if args.checkpoint:
            analyzer.save_checkpoint(args.checkpoint)

        # Set analysis prompt based on type
        if args.analysis_type == "security":
            prompt_builder = AnalysisPromptBuilder.for_security_audit()
        elif args.analysis_type == "api":
            prompt_builder = AnalysisPromptBuilder.for_api_discovery()
        elif args.analysis_type == "dependencies":
            prompt_builder = AnalysisPromptBuilder.for_dependency_analysis()
        else:
            prompt_builder = AnalysisPromptBuilder()

        analyzer.set_analysis_prompt(prompt_builder.build())

        # Apply filters
        if args.language:
            analyzer.filter_by_language(args.language)
            logger.info(f"Filtering by language: {args.language}")

        if args.topics:
            topics = [t.strip() for t in args.topics.split(",")]
            analyzer.filter_by_topics(topics)
            logger.info(f"Filtering by topics: {topics}")

        if args.min_stars:
            analyzer.filter_repos(lambda repo: repo.stars >= args.min_stars)
            logger.info(f"Filtering by minimum stars: {args.min_stars}")

        # Fetch repositories
        logger.info("Fetching repositories...")
        repos = analyzer.fetch_repositories()

        if args.dry_run:
            logger.info("\n=== DRY RUN MODE ===")
            logger.info(f"Would analyze {len(repos)} repositories:")
            for i, repo in enumerate(repos[:10], 1):  # Show first 10
                logger.info(
                    f"  {i}. {repo.name} ({repo.language}) - {repo.stars} stars"
                )
            if len(repos) > 10:
                logger.info(f"  ... and {len(repos) - 10} more")
            logger.info("\nRun without --dry-run to execute analysis")
            return 0

        # Run batch analysis
        logger.info(f"\nStarting analysis of {len(repos)} repositories...")
        logger.info(
            f"Estimated time: ~{len(repos) * args.timeout} minutes (if all timeout)"
        )
        logger.info("Press Ctrl+C to interrupt (progress will be saved)\n")

        results = analyzer.analyze_all_repos(
            rate_limit=args.rate_limit,
            wait_for_completion=not args.no_wait,
        )

        # Generate summary report
        summary_file = Path(args.output_dir) / "analysis_summary.md"
        analyzer.generate_summary_report(str(summary_file))

        # Print summary
        progress = analyzer.get_status()
        logger.info("\n" + "=" * 80)
        logger.info("ANALYSIS COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total Repositories: {progress.total_repositories}")
        logger.info(f"Completed: {progress.completed}")
        logger.info(f"Failed: {progress.failed}")
        logger.info(f"Success Rate: {progress.success_rate:.1f}%")
        logger.info(f"Summary Report: {summary_file}")
        logger.info("=" * 80)

        return 0

    except KeyboardInterrupt:
        logger.warning("\n\nInterrupted by user")
        if args.checkpoint:
            logger.info(f"Progress saved to: {args.checkpoint}")
            logger.info("Resume with: --resume --checkpoint " + args.checkpoint)
        return 130  # Standard exit code for Ctrl+C

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

