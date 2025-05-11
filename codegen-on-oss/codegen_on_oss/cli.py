#!/usr/bin/env python3
"""
Command-line interface for the codegen-on-oss package.
"""

import argparse
import sys
from typing import Optional, List

try:
    from .analysis_viewer_cli import AnalysisViewerCLI
    from .analysis_viewer_web import AnalysisViewerWeb
except ImportError:
    try:
        from analysis_viewer_cli import AnalysisViewerCLI
        from analysis_viewer_web import AnalysisViewerWeb
    except ImportError:
        pass  # Will be handled in the respective commands


def main():
    """Main entry point for the codegen-on-oss CLI."""
    parser = argparse.ArgumentParser(
        description="Codegen on OSS - Repository parsing, analysis, and comparison"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Parse command
    parse_parser = subparsers.add_parser("parse", help="Parse repositories")
    parse_parser.add_argument(
        "--source",
        choices=["csv", "github", "single"],
        default="csv",
        help="Source of repositories to parse",
    )
    parse_parser.add_argument(
        "--output-path",
        default="metrics.csv",
        help="Path to the output metrics file",
    )
    parse_parser.add_argument(
        "--error-output-path",
        default="errors.log",
        help="Path to the error output file",
    )
    parse_parser.add_argument(
        "--cache-dir",
        help="Directory to cache repositories",
    )
    parse_parser.add_argument(
        "--force-pull",
        action="store_true",
        help="Force pull repositories even if they already exist",
    )
    parse_parser.add_argument(
        "--limit",
        type=int,
        help="Limit the number of repositories to parse",
    )
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a codebase")
    analyze_source = analyze_parser.add_mutually_exclusive_group(required=True)
    analyze_source.add_argument("--repo-url", help="URL of the repository to analyze")
    analyze_source.add_argument("--repo-path", help="Local path to the repository to analyze")
    analyze_parser.add_argument("--language", help="Programming language of the codebase (auto-detected if not provided)")
    analyze_parser.add_argument("--categories", nargs="+", help="Categories to analyze (default: all)")
    analyze_parser.add_argument("--depth", type=int, choices=[1, 2, 3], default=2, help="Depth of analysis (1-3, where 3 is most detailed)")
    analyze_parser.add_argument("--output-format", choices=["json", "html", "console"], default="console", help="Output format")
    analyze_parser.add_argument("--output-file", help="Path to the output file")
    
    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two codebases")
    base_group = compare_parser.add_mutually_exclusive_group(required=True)
    base_group.add_argument("--base-repo-url", help="URL of the base repository to compare")
    base_group.add_argument("--base-repo-path", help="Local path to the base repository to compare")
    compare_group = compare_parser.add_mutually_exclusive_group(required=True)
    compare_group.add_argument("--compare-repo-url", help="URL of the repository to compare against the base")
    compare_group.add_argument("--compare-repo-path", help="Local path to the repository to compare against the base")
    compare_parser.add_argument("--base-branch", help="Branch of the base repository to compare")
    compare_parser.add_argument("--compare-branch", help="Branch of the repository to compare against the base")
    compare_parser.add_argument("--language", help="Programming language of the codebases (auto-detected if not provided)")
    compare_parser.add_argument("--categories", nargs="+", help="Categories to compare (default: all)")
    compare_parser.add_argument("--depth", type=int, choices=[1, 2, 3], default=2, help="Depth of comparison (1-3, where 3 is most detailed)")
    compare_parser.add_argument("--output-format", choices=["json", "html", "console"], default="console", help="Output format")
    compare_parser.add_argument("--output-file", help="Path to the output file")
    
    # Interactive command
    interactive_parser = subparsers.add_parser("interactive", help="Run in interactive mode")
    interactive_parser.add_argument("--repo-path", help="Path to the codebase to analyze initially")
    
    # Web command
    web_parser = subparsers.add_parser("web", help="Launch the web interface")
    web_parser.add_argument("--port", type=int, default=7860, help="Port to run the web interface on")
    web_parser.add_argument("--host", default="127.0.0.1", help="Host to run the web interface on")
    web_parser.add_argument("--share", action="store_true", help="Create a shareable link")
    web_parser.add_argument("--no-browser", action="store_true", help="Don't open the browser automatically")
    
    args = parser.parse_args()
    
    if args.command == "parse":
        # Import parse-related modules only if needed
        try:
            from .sources import get_source_class
            from .metrics import MetricsProfiler
            from .parser import CodegenParser
        except ImportError:
            print("Parse functionality not available. Please install the required dependencies.")
            sys.exit(1)
        
        # Run the parse command
        run_parse(args)
    
    elif args.command == "analyze":
        # Run the analyze command
        try:
            from .analysis_viewer_cli import AnalysisViewerCLI
        except ImportError:
            print("Analysis functionality not available. Please install the required dependencies.")
            sys.exit(1)
        
        cli = AnalysisViewerCLI()
        cli._run_analyze(args)
    
    elif args.command == "compare":
        # Run the compare command
        try:
            from .analysis_viewer_cli import AnalysisViewerCLI
        except ImportError:
            print("Comparison functionality not available. Please install the required dependencies.")
            sys.exit(1)
        
        cli = AnalysisViewerCLI()
        cli._run_compare(args)
    
    elif args.command == "interactive":
        # Run the interactive command
        try:
            from .analysis_viewer_cli import AnalysisViewerCLI
        except ImportError:
            print("Interactive mode not available. Please install the required dependencies.")
            sys.exit(1)
        
        cli = AnalysisViewerCLI()
        cli._run_interactive(args)
    
    elif args.command == "web":
        # Run the web command
        try:
            from .analysis_viewer_web import AnalysisViewerWeb
        except ImportError:
            print("Web interface not available. Please install the required dependencies.")
            sys.exit(1)
        
        viewer = AnalysisViewerWeb()
        viewer.launch(
            port=args.port,
            host=args.host,
            share=args.share,
            open_browser=not args.no_browser
        )
    
    else:
        parser.print_help()


def run_parse(args):
    """Run the parse command."""
    from .sources import get_source_class
    from .metrics import MetricsProfiler
    from .parser import CodegenParser
    
    # Get the source class
    source_class = get_source_class(args.source)
    
    # Create the source
    source = source_class()
    
    # Create the metrics profiler
    metrics_profiler = MetricsProfiler(args.output_path)
    
    # Create the parser
    parser = CodegenParser(
        metrics_profiler=metrics_profiler,
        error_output_path=args.error_output_path,
        cache_dir=args.cache_dir,
        force_pull=args.force_pull,
    )
    
    # Parse the repositories
    count = 0
    for repo_url in source.get_repo_urls():
        if args.limit and count >= args.limit:
            break
        
        try:
            parser.parse(repo_url)
        except Exception as e:
            print(f"Error parsing repository {repo_url}: {e}")
        
        count += 1


if __name__ == "__main__":
    main()
