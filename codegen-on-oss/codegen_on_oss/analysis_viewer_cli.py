#!/usr/bin/env python3
"""
Codebase Analysis Viewer CLI

This module provides a command-line interface for the codebase analysis viewer,
allowing users to analyze single codebases or compare multiple codebases.
"""

import os
import sys
import argparse
import logging
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

try:
    from codegen_on_oss.codebase_analyzer import CodebaseAnalyzer, METRICS_CATEGORIES
    from codegen_on_oss.codebase_comparator import CodebaseComparator
except ImportError:
    print("Codebase analysis modules not found. Please ensure they're in the same directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class CodebaseAnalysisViewerCLI:
    """
    Command-line interface for the codebase analysis viewer.
    
    This class provides a user-friendly interface for analyzing single codebases
    or comparing multiple codebases.
    """
    
    def __init__(self):
        """Initialize the CLI."""
        self.console = Console()
        self.mode = None  # 'single' or 'compare'
    
    def run(self):
        """Run the CLI application."""
        parser = argparse.ArgumentParser(
            description="Codebase Analysis Viewer - Analyze and compare codebases"
        )
        
        # Main subparsers
        subparsers = parser.add_subparsers(dest="command", help="Command to run")
        
        # Single codebase analysis command
        single_parser = subparsers.add_parser("analyze", help="Analyze a single codebase")
        single_parser.add_argument("--repo-url", help="URL of the repository to analyze")
        single_parser.add_argument("--repo-path", help="Local path to the repository to analyze")
        single_parser.add_argument("--language", help="Programming language of the codebase (auto-detected if not provided)")
        single_parser.add_argument("--categories", nargs="+", help="Categories to analyze (default: all)")
        single_parser.add_argument("--output-format", choices=["json", "html", "console"], default="console", help="Output format")
        single_parser.add_argument("--output-file", help="Path to the output file")
        
        # Compare codebases command
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
        
        # Interactive mode
        interactive_parser = subparsers.add_parser("interactive", help="Run in interactive mode")
        
        # Parse arguments
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return
        
        try:
            if args.command == "analyze":
                self._handle_analyze_command(args)
            elif args.command == "compare":
                self._handle_compare_command(args)
            elif args.command == "interactive":
                self._run_interactive_mode()
        except Exception as e:
            self.console.print(f"[bold red]Error: {e}[/bold red]")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def _handle_analyze_command(self, args):
        """Handle the 'analyze' command."""
        if not args.repo_url and not args.repo_path:
            self.console.print("[bold red]Error: You must specify either --repo-url or --repo-path[/bold red]")
            sys.exit(1)
        
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
            self.console.print(f"[bold green]Analysis results saved to {args.output_file}[/bold green]")
        elif args.output_format == "html":
            self.console.print(f"[bold green]HTML report saved to {args.output_file or 'codebase_analysis_report.html'}[/bold green]")
    
    def _handle_compare_command(self, args):
        """Handle the 'compare' command."""
        # Validate arguments
        if not ((args.base_repo_url or args.base_repo_path) and (args.compare_repo_url or args.compare_repo_path)):
            self.console.print("[bold red]Error: You must specify both a base repository and a comparison repository.[/bold red]")
            sys.exit(1)
        
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
            self.console.print(f"[bold green]Comparison results saved to {args.output_file}[/bold green]")
        elif args.output_format == "html":
            self.console.print(f"[bold green]HTML report saved to {args.output_file or 'codebase_comparison_report.html'}[/bold green]")
    
    def _run_interactive_mode(self):
        """Run the CLI in interactive mode."""
        self.console.print(Panel.fit(
            "[bold blue]Welcome to the Codebase Analysis Viewer[/bold blue]\n\n"
            "This tool allows you to analyze single codebases or compare multiple codebases.",
            title="Codebase Analysis Viewer",
            border_style="green"
        ))
        
        # Choose mode
        mode = Prompt.ask(
            "Choose a mode",
            choices=["analyze", "compare", "exit"],
            default="analyze"
        )
        
        if mode == "exit":
            return
        
        if mode == "analyze":
            self._run_interactive_analyze()
        else:  # compare
            self._run_interactive_compare()
    
    def _run_interactive_analyze(self):
        """Run interactive single codebase analysis."""
        self.console.print("\n[bold]Single Codebase Analysis[/bold]")
        
        # Get repository information
        repo_type = Prompt.ask(
            "Repository source",
            choices=["url", "local"],
            default="url"
        )
        
        repo_url = None
        repo_path = None
        
        if repo_type == "url":
            repo_url = Prompt.ask("Enter repository URL")
        else:
            repo_path = Prompt.ask("Enter local repository path")
        
        # Get language (optional)
        language = Prompt.ask("Programming language (leave empty for auto-detection)", default="")
        if not language:
            language = None
        
        # Get categories (optional)
        show_categories = Confirm.ask("Do you want to select specific categories to analyze?", default=False)
        categories = None
        
        if show_categories:
            table = Table(show_header=True)
            table.add_column("Category")
            table.add_column("Description")
            
            for category in METRICS_CATEGORIES.keys():
                table.add_row(
                    category,
                    f"{len(METRICS_CATEGORIES[category])} metrics"
                )
            
            self.console.print(table)
            
            categories_input = Prompt.ask("Enter categories (comma-separated)")
            if categories_input:
                categories = [c.strip() for c in categories_input.split(",")]
        
        # Get output format
        output_format = Prompt.ask(
            "Output format",
            choices=["json", "html", "console"],
            default="console"
        )
        
        output_file = None
        if output_format != "console":
            output_file = Prompt.ask(f"Output file path (leave empty for default)", default="")
            if not output_file:
                output_file = None
        
        # Initialize the analyzer
        try:
            analyzer = CodebaseAnalyzer(
                repo_url=repo_url,
                repo_path=repo_path,
                language=language
            )
            
            # Perform the analysis
            results = analyzer.analyze(
                categories=categories,
                output_format=output_format,
                output_file=output_file
            )
            
            # Print success message
            if output_format == "json" and output_file:
                self.console.print(f"[bold green]Analysis results saved to {output_file}[/bold green]")
            elif output_format == "html":
                self.console.print(f"[bold green]HTML report saved to {output_file or 'codebase_analysis_report.html'}[/bold green]")
        
        except Exception as e:
            self.console.print(f"[bold red]Error: {e}[/bold red]")
    
    def _run_interactive_compare(self):
        """Run interactive codebase comparison."""
        self.console.print("\n[bold]Codebase Comparison[/bold]")
        
        # Get base repository information
        base_repo_type = Prompt.ask(
            "Base repository source",
            choices=["url", "local"],
            default="url"
        )
        
        base_repo_url = None
        base_repo_path = None
        
        if base_repo_type == "url":
            base_repo_url = Prompt.ask("Enter base repository URL")
        else:
            base_repo_path = Prompt.ask("Enter local base repository path")
        
        # Get comparison repository information
        compare_repo_type = Prompt.ask(
            "Comparison repository source",
            choices=["url", "local", "branch"],
            default="url"
        )
        
        compare_repo_url = None
        compare_repo_path = None
        base_branch = None
        compare_branch = None
        
        if compare_repo_type == "branch":
            # Branch comparison (same repository, different branches)
            base_branch = Prompt.ask("Enter base branch name")
            compare_branch = Prompt.ask("Enter comparison branch name")
            
            # Use the same repository for both
            compare_repo_url = base_repo_url
            compare_repo_path = base_repo_path
        else:
            if compare_repo_type == "url":
                compare_repo_url = Prompt.ask("Enter comparison repository URL")
            else:
                compare_repo_path = Prompt.ask("Enter local comparison repository path")
        
        # Get language (optional)
        language = Prompt.ask("Programming language (leave empty for auto-detection)", default="")
        if not language:
            language = None
        
        # Get categories (optional)
        show_categories = Confirm.ask("Do you want to select specific categories to analyze?", default=False)
        categories = None
        
        if show_categories:
            table = Table(show_header=True)
            table.add_column("Category")
            table.add_column("Description")
            
            for category in METRICS_CATEGORIES.keys():
                table.add_row(
                    category,
                    f"{len(METRICS_CATEGORIES[category])} metrics"
                )
            
            self.console.print(table)
            
            categories_input = Prompt.ask("Enter categories (comma-separated)")
            if categories_input:
                categories = [c.strip() for c in categories_input.split(",")]
        
        # Get output format
        output_format = Prompt.ask(
            "Output format",
            choices=["json", "html", "console"],
            default="console"
        )
        
        output_file = None
        if output_format != "console":
            output_file = Prompt.ask(f"Output file path (leave empty for default)", default="")
            if not output_file:
                output_file = None
        
        # Initialize the comparator
        try:
            comparator = CodebaseComparator(
                base_repo_url=base_repo_url,
                base_repo_path=base_repo_path,
                compare_repo_url=compare_repo_url,
                compare_repo_path=compare_repo_path,
                base_branch=base_branch,
                compare_branch=compare_branch,
                language=language
            )
            
            # Perform the comparison
            results = comparator.compare(
                categories=categories,
                output_format=output_format,
                output_file=output_file
            )
            
            # Print success message
            if output_format == "json" and output_file:
                self.console.print(f"[bold green]Comparison results saved to {output_file}[/bold green]")
            elif output_format == "html":
                self.console.print(f"[bold green]HTML report saved to {output_file or 'codebase_comparison_report.html'}[/bold green]")
        
        except Exception as e:
            self.console.print(f"[bold red]Error: {e}[/bold red]")


def main():
    """Main entry point for the CLI."""
    cli = CodebaseAnalysisViewerCLI()
    cli.run()


if __name__ == "__main__":
    main()

