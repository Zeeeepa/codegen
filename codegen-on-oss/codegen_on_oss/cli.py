#!/usr/bin/env python3
import argparse
import logging
import os
import sys
from typing import List, Optional

from codegen_on_oss.parser import parse_repo
from codegen_on_oss.sources import get_source
from codegen_on_oss.sources.base import SourceSettings

# Add imports for the new analysis viewer functionality
from codegen_on_oss.analysis_viewer_cli import CodebaseAnalysisViewerCLI
from codegen_on_oss.analysis_viewer_web import CodebaseAnalysisViewerWeb

logger = logging.getLogger(__name__)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Codegen on OSS")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Original parse command
    parse_parser = subparsers.add_parser("parse", help="Parse repositories")
    parse_parser.add_argument(
        "--source",
        choices=["csv", "github"],
        default="csv",
        help="Source of repositories to parse",
    )
    parse_parser.add_argument(
        "--limit", type=int, default=None, help="Limit the number of repositories to parse"
    )
    parse_parser.add_argument(
        "--force-pull",
        action="store_true",
        help="Force pull repositories even if they already exist",
    )
    parse_parser.add_argument(
        "--skip-parse",
        action="store_true",
        help="Skip parsing repositories (useful for testing)",
    )
    parse_parser.add_argument(
        "--skip-errors",
        action="store_true",
        help="Skip repositories that fail to parse",
    )
    parse_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    # New analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a single codebase")
    analyze_parser.add_argument("--repo-url", help="URL of the repository to analyze")
    analyze_parser.add_argument("--repo-path", help="Local path to the repository to analyze")
    analyze_parser.add_argument("--language", help="Programming language of the codebase (auto-detected if not provided)")
    analyze_parser.add_argument("--categories", nargs="+", help="Categories to analyze (default: all)")
    analyze_parser.add_argument("--output-format", choices=["json", "html", "console"], default="console", help="Output format")
    analyze_parser.add_argument("--output-file", help="Path to the output file")

    # New compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two codebases")
    compare_parser.add_argument("--base-repo-url", help="URL of the base repository")
    compare_parser.add_argument("--base-repo-path", help="Local path to the base repository")
    compare_parser.add_argument("--compare-repo-url", help="URL of the repository to compare against")
    compare_parser.add_argument("--compare-repo-path", help="Local path to the repository to compare against")
    compare_parser.add_argument("--base-branch", help="Branch name for the base repository (if comparing branches)")
    compare_parser.add_argument("--compare-branch", help="Branch name for the comparison (if comparing branches)")
    compare_parser.add_argument("--language", help="Programming language of the codebases (auto-detected if not provided)")
    compare_parser.add_argument("--categories", nargs="+", help="Categories to analyze (default: all)")
    compare_parser.add_argument("--output-format", choices=["json", "html", "console"], default="console", help="Output format")
    compare_parser.add_argument("--output-file", help="Path to the output file")

    # New interactive command
    interactive_parser = subparsers.add_parser("interactive", help="Run in interactive mode")

    # New web command
    web_parser = subparsers.add_parser("web", help="Launch the web interface")
    web_parser.add_argument("--share", action="store_true", help="Create a shareable link")
    web_parser.add_argument("--no-browser", action="store_true", help="Don't open the browser automatically")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    if args.command == "parse":
        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG if args.verbose else logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        # Get the source
        source = get_source(args.source)
        if source is None:
            logger.error(f"Source {args.source} not found")
            return 1

        # Parse repositories
        for i, repo in enumerate(source.get_repos()):
            if args.limit is not None and i >= args.limit:
                break

            logger.info(f"Parsing repository {repo.url}")
            try:
                parse_repo(
                    repo,
                    force_pull=args.force_pull,
                    skip_parse=args.skip_parse,
                )
            except Exception as e:
                if args.skip_errors:
                    logger.error(f"Error parsing repository {repo.url}: {e}")
                else:
                    raise
    elif args.command == "analyze":
        # Handle analyze command
        from codegen_on_oss.codebase_analyzer import CodebaseAnalyzer
        
        # Validate arguments
        if not args.repo_url and not args.repo_path:
            logger.error("You must specify either --repo-url or --repo-path")
            return 1
        
        # Initialize the analyzer
        analyzer = CodebaseAnalyzer(
            repo_url=args.repo_url,
            repo_path=args.repo_path,
            language=args.language
        )
        
        # Perform the analysis
        results = analyzer.analyze(
            categories=args.categories,
            output_format=args.output_format,
            output_file=args.output_file
        )
        
        # Print success message
        if args.output_format == "json" and args.output_file:
            logger.info(f"Analysis results saved to {args.output_file}")
        elif args.output_format == "html":
            logger.info(f"HTML report saved to {args.output_file or 'codebase_analysis_report.html'}")
    elif args.command == "compare":
        # Handle compare command
        from codegen_on_oss.codebase_comparator import CodebaseComparator
        
        # Validate arguments
        if not ((args.base_repo_url or args.base_repo_path) and (args.compare_repo_url or args.compare_repo_path)):
            logger.error("You must specify both a base repository and a comparison repository.")
            return 1
        
        # Initialize the comparator
        comparator = CodebaseComparator(
            base_repo_url=args.base_repo_url,
            base_repo_path=args.base_repo_path,
            compare_repo_url=args.compare_repo_url,
            compare_repo_path=args.compare_repo_path,
            base_branch=args.base_branch,
            compare_branch=args.compare_branch,
            language=args.language
        )
        
        # Perform the comparison
        results = comparator.compare(
            categories=args.categories,
            output_format=args.output_format,
            output_file=args.output_file
        )
        
        # Print success message
        if args.output_format == "json" and args.output_file:
            logger.info(f"Comparison results saved to {args.output_file}")
        elif args.output_format == "html":
            logger.info(f"HTML report saved to {args.output_file or 'codebase_comparison_report.html'}")
    elif args.command == "interactive":
        # Handle interactive command
        cli = CodebaseAnalysisViewerCLI()
        cli.run()
    elif args.command == "web":
        # Handle web command
        app = CodebaseAnalysisViewerWeb()
        app.launch(share=args.share, inbrowser=not args.no_browser)

    return 0


if __name__ == "__main__":
    sys.exit(main())
