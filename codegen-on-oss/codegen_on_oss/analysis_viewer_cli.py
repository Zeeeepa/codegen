#!/usr/bin/env python3
"""
Command-line interface for the codebase analysis viewer.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Optional, Any, Union

try:
    from .codebase_analyzer import CodebaseAnalyzer
    from .codebase_comparator import CodebaseComparator
except ImportError:
    try:
        from codebase_analyzer import CodebaseAnalyzer
        from codebase_comparator import CodebaseComparator
    except ImportError:
        print(
            "Codebase analysis modules not found. "
            "Please ensure they're in the same directory."
        )
        sys.exit(1)


def create_parser():
    """
    Create the command-line argument parser for the analysis viewer CLI.
    """
    parser = argparse.ArgumentParser(description="Codebase Analysis Viewer CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a codebase")
    source_group = analyze_parser.add_mutually_exclusive_group()
    source_group.add_argument("--repo-url", help="URL of the repository to analyze")
    source_group.add_argument("--repo-path", help="Local path to the repository to analyze")
    
    # Analysis options
    analyze_parser.add_argument(
        "--language", 
        help="Programming language of the codebase (auto-detected if not provided)"
    )
    analyze_parser.add_argument(
        "--categories", 
        nargs="+", 
        help="Categories to analyze (default: all)"
    )
    analyze_parser.add_argument(
        "--depth", 
        type=int, 
        choices=[1, 2, 3], 
        default=2, 
        help="Depth of analysis (1-3, where 3 is most detailed)"
    )
    
    # Output options
    analyze_parser.add_argument(
        "--output-format", 
        choices=["json", "html", "console"], 
        default="console", 
        help="Output format"
    )
    analyze_parser.add_argument("--output-file", help="Path to the output file")
    
    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two codebases")
    base_group = compare_parser.add_mutually_exclusive_group()
    base_group.add_argument("--base-repo-url", help="URL of the base repository")
    base_group.add_argument("--base-repo-path", help="Local path to the base repository")
    
    compare_group = compare_parser.add_mutually_exclusive_group()
    compare_group.add_argument(
        "--compare-repo-url", 
        help="URL of the repository to compare against the base"
    )
    compare_group.add_argument(
        "--compare-repo-path", 
        help="Local path to the repository to compare against the base"
    )
    
    # Branch options
    compare_parser.add_argument(
        "--base-branch", 
        help="Branch of the base repository to compare"
    )
    compare_parser.add_argument(
        "--compare-branch", 
        help="Branch of the repository to compare against the base"
    )
    
    # Comparison options
    compare_parser.add_argument(
        "--language", 
        help="Programming language of the codebases (auto-detected if not provided)"
    )
    compare_parser.add_argument(
        "--categories", 
        nargs="+", 
        help="Categories to compare (default: all)"
    )
    compare_parser.add_argument(
        "--depth", 
        type=int, 
        choices=[1, 2, 3], 
        default=2, 
        help="Depth of comparison (1-3, where 3 is most detailed)"
    )
    
    # Output options
    compare_parser.add_argument(
        "--output-format", 
        choices=["json", "html", "console"], 
        default="console", 
        help="Output format"
    )
    compare_parser.add_argument("--output-file", help="Path to the output file")
    
    # Interactive command
    interactive_parser = subparsers.add_parser(
        "interactive", 
        help="Run in interactive mode"
    )
    interactive_parser.add_argument(
        "--repo-path", 
        help="Path to the codebase to analyze initially"
    )
    
    return parser


class AnalysisViewerCLI:
    """
    Command-line interface for the codebase analysis viewer.
    
    This class provides an interactive command-line interface for analyzing
    and comparing codebases.
    """
    
    def __init__(self):
        """Initialize the CLI."""
        self.parser = self._setup_parser()
    
    def _setup_parser(self) -> argparse.ArgumentParser:
        """
        Set up the command-line argument parser.
        
        Returns:
            argparse.ArgumentParser: The configured argument parser.
        """
        return create_parser()
    
    def run(self, args=None):
        """
        Run the CLI with the given arguments.
        
        Args:
            args: Command-line arguments. If None, sys.argv is used.
        """
        args = self.parser.parse_args(args)
        
        if args.command == "analyze":
            self._run_analyze(args)
        elif args.command == "compare":
            self._run_compare(args)
        elif args.command == "interactive":
            self._run_interactive(args)
        else:
            self.parser.print_help()
    
    def _run_analyze(self, args):
        """
        Run the analyze command.
        
        Args:
            args: Command-line arguments for the analyze command.
        """
        try:
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
                print(f"Analysis results saved to {args.output_file}")
            elif args.output_format == "html" and args.output_file:
                print(f"HTML report saved to {args.output_file}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def _run_compare(self, args):
        """
        Run the compare command.
        
        Args:
            args: Command-line arguments for the compare command.
        """
        try:
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
                print(f"Comparison results saved to {args.output_file}")
            elif args.output_format == "html" and args.output_file:
                print(f"HTML report saved to {args.output_file}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def _run_interactive(self, args):
        """
        Run the interactive command.
        
        Args:
            args: Command-line arguments for the interactive command.
        """
        try:
            import cmd
            import readline  # noqa: F401
        except ImportError:
            pass
        
        class AnalysisShell(cmd.Cmd):
            intro = (
                "Welcome to the Codebase Analysis Interactive Shell. "
                "Type help or ? to list commands.\n"
            )
            prompt = "(analysis) "
            current_path = args.repo_path
            analyzer = None
            comparator = None
            last_results = None
            
            def do_analyze(self, arg):
                """
                Analyze a codebase: analyze [--repo-url URL | --repo-path PATH] 
                [--categories cat1 cat2] [--language lang] [--depth 1-3] 
                [--output-format format] [--output-file file]
                """
                parser = argparse.ArgumentParser(description="Analyze a codebase")
                source = parser.add_mutually_exclusive_group()
                source.add_argument("--repo-url", help="URL of the repository to analyze")
                source.add_argument("--repo-path", help="Local path to the repository to analyze")
                parser.add_argument("--language", help="Programming language of the codebase")
                parser.add_argument("--categories", nargs="+", help="Categories to analyze")
                parser.add_argument(
                    "--depth", 
                    type=int, 
                    choices=[1, 2, 3], 
                    default=2, 
                    help="Depth of analysis"
                )
                parser.add_argument(
                    "--output-format", 
                    choices=["json", "html", "console"], 
                    default="console", 
                    help="Output format"
                )
                parser.add_argument("--output-file", help="Path to the output file")
                
                try:
                    args = parser.parse_args(arg.split())
                except SystemExit:
                    return
                
                repo_url = args.repo_url
                repo_path = args.repo_path or self.current_path
                
                if not repo_url and not repo_path:
                    print("Please specify a repository URL or path")
                    return
                
                try:
                    self.analyzer = CodebaseAnalyzer(
                        repo_url=repo_url,
                        repo_path=repo_path,
                        language=args.language
                    )
                    
                    self.last_results = self.analyzer.analyze(
                        categories=args.categories,
                        output_format=args.output_format,
                        output_file=args.output_file
                    )
                    
                    if args.output_format == "json" and args.output_file:
                        print(f"Analysis results saved to {args.output_file}")
                    elif args.output_format == "html" and args.output_file:
                        print(f"HTML report saved to {args.output_file}")
                    
                    if repo_path:
                        self.current_path = repo_path
                    
                except Exception as e:
                    print(f"Error: {e}")
                    import traceback
                    traceback.print_exc()
            
            def do_compare(self, arg):
                """
                Compare two codebases: compare [--base-repo-url URL | --base-repo-path PATH]
                [--compare-repo-url URL | --compare-repo-path PATH] [--base-branch branch]
                [--compare-branch branch] [--categories cat1 cat2] [--language lang]
                [--depth 1-3] [--output-format format] [--output-file file]
                """
                parser = argparse.ArgumentParser(description="Compare two codebases")
                base_group = parser.add_mutually_exclusive_group()
                base_group.add_argument("--base-repo-url", help="URL of the base repository")
                base_group.add_argument(
                    "--base-repo-path", 
                    help="Local path to the base repository"
                )
                compare_group = parser.add_mutually_exclusive_group()
                compare_group.add_argument(
                    "--compare-repo-url", 
                    help="URL of the compare repository"
                )
                compare_group.add_argument(
                    "--compare-repo-path", 
                    help="Local path to the compare repository"
                )
                
                try:
                    args = parser.parse_args(arg.split())
                except SystemExit:
                    return
                
                base_repo_url = args.base_repo_url
                base_repo_path = args.base_repo_path or self.current_path
                compare_repo_url = args.compare_repo_url
                compare_repo_path = args.compare_repo_path
                
                if not (base_repo_url or base_repo_path) or not (compare_repo_url or compare_repo_path):
                    print("Please specify both base and compare repositories")
                    return
                
                try:
                    self.comparator = CodebaseComparator(
                        base_repo_url=base_repo_url,
                        base_repo_path=base_repo_path,
                        compare_repo_url=compare_repo_url,
                        compare_repo_path=compare_repo_path,
                        base_branch=args.base_branch,
                        compare_branch=args.compare_branch,
                        language=args.language
                    )
                    
                    self.last_results = self.comparator.compare(
                        categories=args.categories,
                        output_format=args.output_format,
                        output_file=args.output_file
                    )
                    
                    if args.output_format == "json" and args.output_file:
                        print(f"Comparison results saved to {args.output_file}")
                    elif args.output_format == "html" and args.output_file:
                        print(f"HTML report saved to {args.output_file}")
                    
                except Exception as e:
                    print(f"Error: {e}")
                    import traceback
                    traceback.print_exc()
            
            def do_set_path(self, arg):
                """Set the current repository path: set_path PATH"""
                if not arg:
                    print("Please specify a path")
                    return
                
                path = os.path.abspath(arg)
                if not os.path.exists(path):
                    print(f"Path does not exist: {path}")
                    return
                
                self.current_path = path
                print(f"Current path set to: {path}")
            
            def do_get_path(self, arg):
                """Get the current repository path"""
                print(f"Current path: {self.current_path or 'Not set'}")
            
            def do_save_results(self, arg):
                """
                Save the last analysis or comparison results: save_results [--format FORMAT] [--file FILE]
                """
                if not self.last_results:
                    print("No results to save. Run analyze or compare first.")
                    return
                
                parser = argparse.ArgumentParser(description="Save results")
                parser.add_argument("--format", choices=["json", "html"], default="json", help="Output format")
                parser.add_argument("--file", help="Output file")
                
                try:
                    args = parser.parse_args(arg.split())
                except SystemExit:
                    return
                
                output_format = args.format
                output_file = args.file
                
                if not output_file:
                    if self.analyzer:
                        output_file = "analysis_results"
                    else:
                        output_file = "comparison_results"
                    
                    if output_format == "json":
                        output_file += ".json"
                    elif output_format == "html":
                        output_file += ".html"
                
                try:
                    if output_format == "json":
                        with open(output_file, "w") as f:
                            json.dump(self.last_results, f, indent=2)
                        print(f"Results saved to {output_file}")
                    elif output_format == "html":
                        if self.analyzer:
                            self.analyzer._generate_html_report(output_file)
                        elif self.comparator:
                            self.comparator._generate_html_report(self.last_results, output_file)
                        print(f"HTML report saved to {output_file}")
                except Exception as e:
                    print(f"Error saving results: {e}")
            
            def do_exit(self, arg):
                """Exit the interactive shell"""
                print("Exiting...")
                return True
            
            def do_quit(self, arg):
                """Exit the interactive shell"""
                return self.do_exit(arg)
            
            def do_EOF(self, arg):
                """Exit on Ctrl-D"""
                print()
                return self.do_exit(arg)
        
        # Start the interactive shell
        AnalysisShell().cmdloop()


def main():
    """Main entry point for the analysis viewer CLI."""
    AnalysisViewerCLI().run()


if __name__ == "__main__":
    main()
