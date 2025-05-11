#!/usr/bin/env python3
"""
Codebase Analysis Viewer CLI

This module provides a command-line interface for the codebase analysis viewer,
allowing users to analyze a single codebase, compare two codebases, and view
the results in various formats.
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
import tempfile

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.tree import Tree
from rich.markdown import Markdown
from rich import print as rich_print

# Import the codebase analyzer
try:
    from codebase_analyzer import CodebaseAnalyzer, METRICS_CATEGORIES
except ImportError:
    # If running from within the package
    try:
        from codegen_on_oss.codebase_analyzer import CodebaseAnalyzer, METRICS_CATEGORIES
    except ImportError:
        print("Error: Could not import CodebaseAnalyzer. Make sure codebase_analyzer.py is in your path.")
        sys.exit(1)

# Initialize rich console
console = Console()

# Constants
OUTPUT_FORMATS = ["json", "html", "console"]
DEFAULT_OUTPUT_FORMAT = "console"
DEFAULT_OUTPUT_FILE = "analysis_results"

class CodebaseAnalysisViewer:
    """
    CLI interface for the codebase analysis viewer.
    
    This class provides methods to analyze a single codebase, compare two codebases,
    and view the results in various formats.
    """
    
    def __init__(self):
        """Initialize the codebase analysis viewer."""
        self.console = Console()
        self.analyzers = {}
        self.results = {}
        self.comparison_results = {}
    
    def analyze_codebase(
        self, 
        repo_source: str, 
        language: Optional[str] = None,
        categories: Optional[List[str]] = None,
        output_format: str = DEFAULT_OUTPUT_FORMAT,
        output_file: Optional[str] = None,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze a single codebase.
        
        Args:
            repo_source: URL or local path to the repository
            language: Programming language of the codebase
            categories: List of categories to analyze
            output_format: Format of the output (json, html, console)
            output_file: Path to the output file
            show_progress: Whether to show progress indicators
            
        Returns:
            Dict containing the analysis results
        """
        # Determine if the source is a URL or local path
        is_url = repo_source.startswith(("http://", "https://", "git://"))
        
        # Create a unique key for this analyzer
        analyzer_key = f"analyzer_{len(self.analyzers) + 1}"
        
        # Show progress
        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TimeElapsedColumn(),
                console=self.console
            ) as progress:
                task = progress.add_task(f"Analyzing {'repository' if is_url else 'local codebase'}: {repo_source}", total=100)
                
                # Initialize the analyzer
                progress.update(task, advance=10, description=f"Initializing analyzer for {repo_source}")
                
                if is_url:
                    analyzer = CodebaseAnalyzer(repo_url=repo_source, language=language)
                else:
                    analyzer = CodebaseAnalyzer(repo_path=repo_source, language=language)
                
                self.analyzers[analyzer_key] = analyzer
                
                # Perform the analysis
                progress.update(task, advance=20, description=f"Analyzing {repo_source}")
                results = analyzer.analyze(categories=categories, output_format=output_format, output_file=output_file)
                
                # Store the results
                self.results[analyzer_key] = results
                
                progress.update(task, advance=70, description=f"Analysis of {repo_source} complete")
        else:
            # Initialize the analyzer without progress indicators
            if is_url:
                analyzer = CodebaseAnalyzer(repo_url=repo_source, language=language)
            else:
                analyzer = CodebaseAnalyzer(repo_path=repo_source, language=language)
            
            self.analyzers[analyzer_key] = analyzer
            
            # Perform the analysis
            results = analyzer.analyze(categories=categories, output_format=output_format, output_file=output_file)
            
            # Store the results
            self.results[analyzer_key] = results
        
        return results
    
    def compare_codebases(
        self,
        repo_source1: str,
        repo_source2: str,
        language1: Optional[str] = None,
        language2: Optional[str] = None,
        categories: Optional[List[str]] = None,
        output_format: str = DEFAULT_OUTPUT_FORMAT,
        output_file: Optional[str] = None,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Compare two codebases.
        
        Args:
            repo_source1: URL or local path to the first repository
            repo_source2: URL or local path to the second repository
            language1: Programming language of the first codebase
            language2: Programming language of the second codebase
            categories: List of categories to analyze
            output_format: Format of the output (json, html, console)
            output_file: Path to the output file
            show_progress: Whether to show progress indicators
            
        Returns:
            Dict containing the comparison results
        """
        # Analyze both codebases
        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TimeElapsedColumn(),
                console=self.console
            ) as progress:
                task1 = progress.add_task(f"Analyzing first codebase: {repo_source1}", total=100)
                
                # Analyze the first codebase
                results1 = self.analyze_codebase(
                    repo_source=repo_source1,
                    language=language1,
                    categories=categories,
                    output_format="json",  # Always use JSON for comparison
                    show_progress=False
                )
                
                progress.update(task1, completed=100)
                
                task2 = progress.add_task(f"Analyzing second codebase: {repo_source2}", total=100)
                
                # Analyze the second codebase
                results2 = self.analyze_codebase(
                    repo_source=repo_source2,
                    language=language2,
                    categories=categories,
                    output_format="json",  # Always use JSON for comparison
                    show_progress=False
                )
                
                progress.update(task2, completed=100)
                
                # Compare the results
                task3 = progress.add_task("Comparing codebases", total=100)
                comparison_results = self._compare_results(results1, results2)
                progress.update(task3, completed=100)
        else:
            # Analyze both codebases without progress indicators
            results1 = self.analyze_codebase(
                repo_source=repo_source1,
                language=language1,
                categories=categories,
                output_format="json",  # Always use JSON for comparison
                show_progress=False
            )
            
            results2 = self.analyze_codebase(
                repo_source=repo_source2,
                language=language2,
                categories=categories,
                output_format="json",  # Always use JSON for comparison
                show_progress=False
            )
            
            # Compare the results
            comparison_results = self._compare_results(results1, results2)
        
        # Store the comparison results
        self.comparison_results["latest"] = comparison_results
        
        # Output the results
        if output_format == "json":
            if output_file:
                with open(output_file, "w") as f:
                    json.dump(comparison_results, f, indent=2)
                self.console.print(f"[bold green]Comparison results saved to {output_file}[/bold green]")
            else:
                self.console.print(json.dumps(comparison_results, indent=2))
        elif output_format == "html":
            output_file = output_file or f"{DEFAULT_OUTPUT_FILE}_comparison.html"
            self._generate_html_comparison_report(comparison_results, output_file)
        else:  # console
            self._print_console_comparison_report(comparison_results)
        
        return comparison_results
    
    def _compare_results(self, results1: Dict[str, Any], results2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare two analysis results.
        
        Args:
            results1: Results from the first codebase
            results2: Results from the second codebase
            
        Returns:
            Dict containing the comparison results
        """
        comparison = {
            "metadata": {
                "repo1": results1["metadata"]["repo_name"],
                "repo2": results2["metadata"]["repo_name"],
                "comparison_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "categories": {}
        }
        
        # Compare each category
        for category in results1["categories"]:
            if category in results2["categories"]:
                comparison["categories"][category] = {}
                
                # Compare each metric in the category
                for metric in results1["categories"][category]:
                    if metric in results2["categories"][category]:
                        metric1 = results1["categories"][category][metric]
                        metric2 = results2["categories"][category][metric]
                        
                        # Compare the metrics
                        comparison["categories"][category][metric] = {
                            "repo1": metric1,
                            "repo2": metric2,
                            "differences": self._compute_differences(metric1, metric2)
                        }
        
        return comparison
    
    def _compute_differences(self, value1: Any, value2: Any) -> Any:
        """
        Compute the differences between two values.
        
        Args:
            value1: Value from the first codebase
            value2: Value from the second codebase
            
        Returns:
            Differences between the two values
        """
        if isinstance(value1, dict) and isinstance(value2, dict):
            differences = {}
            
            # Find keys in both dictionaries
            all_keys = set(value1.keys()) | set(value2.keys())
            
            for key in all_keys:
                if key in value1 and key in value2:
                    # Both dictionaries have the key
                    if value1[key] != value2[key]:
                        differences[key] = {
                            "repo1": value1[key],
                            "repo2": value2[key]
                        }
                elif key in value1:
                    # Only the first dictionary has the key
                    differences[key] = {
                        "repo1": value1[key],
                        "repo2": None
                    }
                else:
                    # Only the second dictionary has the key
                    differences[key] = {
                        "repo1": None,
                        "repo2": value2[key]
                    }
            
            return differences
        elif isinstance(value1, list) and isinstance(value2, list):
            # For simplicity, just return both lists
            return {
                "repo1_count": len(value1),
                "repo2_count": len(value2),
                "count_difference": len(value1) - len(value2)
            }
        else:
            # For simple values, return both values
            return {
                "repo1": value1,
                "repo2": value2,
                "difference": value1 - value2 if isinstance(value1, (int, float)) and isinstance(value2, (int, float)) else "N/A"
            }
    
    def _generate_html_comparison_report(self, comparison_results: Dict[str, Any], output_file: str) -> None:
        """
        Generate an HTML report of the comparison results.
        
        Args:
            comparison_results: Results of the comparison
            output_file: Path to the output file
        """
        # Simple HTML template
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Codebase Comparison Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                .section {{ margin-bottom: 30px; }}
                .metric {{ margin-bottom: 20px; }}
                .metric-title {{ font-weight: bold; }}
                pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .highlight {{ background-color: #ffffcc; }}
            </style>
        </head>
        <body>
            <h1>Codebase Comparison Report</h1>
            <div class="section">
                <h2>Metadata</h2>
                <p><strong>Repository 1:</strong> {comparison_results["metadata"]["repo1"]}</p>
                <p><strong>Repository 2:</strong> {comparison_results["metadata"]["repo2"]}</p>
                <p><strong>Comparison Time:</strong> {comparison_results["metadata"]["comparison_time"]}</p>
            </div>
        """
        
        # Add each category
        for category, metrics in comparison_results["categories"].items():
            html += f"""
            <div class="section">
                <h2>{category.replace("_", " ").title()}</h2>
            """
            
            for metric_name, metric_comparison in metrics.items():
                html += f"""
                <div class="metric">
                    <h3 class="metric-title">{metric_name.replace("_", " ").title()}</h3>
                    <h4>Repository 1</h4>
                    <pre>{json.dumps(metric_comparison["repo1"], indent=2)}</pre>
                    <h4>Repository 2</h4>
                    <pre>{json.dumps(metric_comparison["repo2"], indent=2)}</pre>
                    <h4>Differences</h4>
                    <pre class="highlight">{json.dumps(metric_comparison["differences"], indent=2)}</pre>
                </div>
                """
            
            html += "</div>"
        
        html += """
        </body>
        </html>
        """
        
        with open(output_file, "w") as f:
            f.write(html)
        
        self.console.print(f"[bold green]HTML comparison report saved to {output_file}[/bold green]")
    
    def _print_console_comparison_report(self, comparison_results: Dict[str, Any]) -> None:
        """
        Print a comparison report to the console.
        
        Args:
            comparison_results: Results of the comparison
        """
        self.console.print(f"[bold blue]Codebase Comparison Report[/bold blue]")
        self.console.print(f"[bold]Repository 1:[/bold] {comparison_results['metadata']['repo1']}")
        self.console.print(f"[bold]Repository 2:[/bold] {comparison_results['metadata']['repo2']}")
        self.console.print(f"[bold]Comparison Time:[/bold] {comparison_results['metadata']['comparison_time']}")
        
        for category, metrics in comparison_results["categories"].items():
            self.console.print(f"\n[bold green]{category.replace('_', ' ').title()}[/bold green]")
            
            for metric_name, metric_comparison in metrics.items():
                self.console.print(f"[bold]{metric_name.replace('_', ' ').title()}:[/bold]")
                
                # Create a table for the comparison
                table = Table(show_header=True)
                table.add_column("Metric")
                table.add_column("Repository 1")
                table.add_column("Repository 2")
                table.add_column("Difference")
                
                # Add rows for each difference
                if isinstance(metric_comparison["differences"], dict):
                    for key, diff in metric_comparison["differences"].items():
                        if isinstance(diff, dict):
                            repo1_value = str(diff.get("repo1", "N/A"))
                            repo2_value = str(diff.get("repo2", "N/A"))
                            difference = str(diff.get("difference", "N/A"))
                            
                            table.add_row(str(key), repo1_value, repo2_value, difference)
                
                self.console.print(table)
    
    def run_interactive_mode(self) -> None:
        """Run the interactive mode with rich text formatting."""
        self.console.print(Panel.fit(
            "[bold blue]Codebase Analysis Viewer[/bold blue]\n\n"
            "This interactive mode allows you to analyze and compare codebases with ease.",
            title="Welcome",
            border_style="green"
        ))
        
        while True:
            self.console.print("\n[bold]Choose an option:[/bold]")
            self.console.print("1. Analyze a single codebase")
            self.console.print("2. Compare two codebases")
            self.console.print("3. View available analysis categories")
            self.console.print("4. Exit")
            
            choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4"], default="1")
            
            if choice == "1":
                self._interactive_analyze_codebase()
            elif choice == "2":
                self._interactive_compare_codebases()
            elif choice == "3":
                self._show_available_categories()
            elif choice == "4":
                self.console.print("[bold green]Goodbye![/bold green]")
                break
    
    def _interactive_analyze_codebase(self) -> None:
        """Interactive mode for analyzing a single codebase."""
        self.console.print("\n[bold]Analyze a Single Codebase[/bold]")
        
        # Get repository source
        repo_source = Prompt.ask(
            "Enter repository URL or local path",
            default="https://github.com/username/repo"
        )
        
        # Get language (optional)
        language = Prompt.ask(
            "Enter programming language (optional, press Enter to auto-detect)",
            default=""
        )
        language = language if language else None
        
        # Get categories (optional)
        self._show_available_categories()
        categories_input = Prompt.ask(
            "Enter categories to analyze (comma-separated, press Enter for all)",
            default=""
        )
        categories = [c.strip() for c in categories_input.split(",")] if categories_input else None
        
        # Get output format
        output_format = Prompt.ask(
            "Enter output format",
            choices=OUTPUT_FORMATS,
            default=DEFAULT_OUTPUT_FORMAT
        )
        
        # Get output file (optional)
        output_file = None
        if output_format in ["json", "html"]:
            output_file = Prompt.ask(
                f"Enter output file path (optional, press Enter for default: {DEFAULT_OUTPUT_FILE}.{output_format})",
                default=""
            )
            output_file = output_file if output_file else f"{DEFAULT_OUTPUT_FILE}.{output_format}"
        
        # Confirm and analyze
        self.console.print("\n[bold]Analysis Configuration:[/bold]")
        self.console.print(f"Repository: {repo_source}")
        self.console.print(f"Language: {language or 'Auto-detect'}")
        self.console.print(f"Categories: {', '.join(categories) if categories else 'All'}")
        self.console.print(f"Output Format: {output_format}")
        self.console.print(f"Output File: {output_file or 'N/A'}")
        
        if Confirm.ask("Proceed with analysis?", default=True):
            try:
                self.analyze_codebase(
                    repo_source=repo_source,
                    language=language,
                    categories=categories,
                    output_format=output_format,
                    output_file=output_file,
                    show_progress=True
                )
                self.console.print("[bold green]Analysis complete![/bold green]")
            except Exception as e:
                self.console.print(f"[bold red]Error during analysis: {e}[/bold red]")
    
    def _interactive_compare_codebases(self) -> None:
        """Interactive mode for comparing two codebases."""
        self.console.print("\n[bold]Compare Two Codebases[/bold]")
        
        # Get repository sources
        repo_source1 = Prompt.ask(
            "Enter first repository URL or local path",
            default="https://github.com/username/repo1"
        )
        
        repo_source2 = Prompt.ask(
            "Enter second repository URL or local path",
            default="https://github.com/username/repo2"
        )
        
        # Get languages (optional)
        language1 = Prompt.ask(
            "Enter programming language for first repository (optional, press Enter to auto-detect)",
            default=""
        )
        language1 = language1 if language1 else None
        
        language2 = Prompt.ask(
            "Enter programming language for second repository (optional, press Enter to auto-detect)",
            default=""
        )
        language2 = language2 if language2 else None
        
        # Get categories (optional)
        self._show_available_categories()
        categories_input = Prompt.ask(
            "Enter categories to analyze (comma-separated, press Enter for all)",
            default=""
        )
        categories = [c.strip() for c in categories_input.split(",")] if categories_input else None
        
        # Get output format
        output_format = Prompt.ask(
            "Enter output format",
            choices=OUTPUT_FORMATS,
            default=DEFAULT_OUTPUT_FORMAT
        )
        
        # Get output file (optional)
        output_file = None
        if output_format in ["json", "html"]:
            output_file = Prompt.ask(
                f"Enter output file path (optional, press Enter for default: {DEFAULT_OUTPUT_FILE}_comparison.{output_format})",
                default=""
            )
            output_file = output_file if output_file else f"{DEFAULT_OUTPUT_FILE}_comparison.{output_format}"
        
        # Confirm and compare
        self.console.print("\n[bold]Comparison Configuration:[/bold]")
        self.console.print(f"Repository 1: {repo_source1}")
        self.console.print(f"Repository 2: {repo_source2}")
        self.console.print(f"Language 1: {language1 or 'Auto-detect'}")
        self.console.print(f"Language 2: {language2 or 'Auto-detect'}")
        self.console.print(f"Categories: {', '.join(categories) if categories else 'All'}")
        self.console.print(f"Output Format: {output_format}")
        self.console.print(f"Output File: {output_file or 'N/A'}")
        
        if Confirm.ask("Proceed with comparison?", default=True):
            try:
                self.compare_codebases(
                    repo_source1=repo_source1,
                    repo_source2=repo_source2,
                    language1=language1,
                    language2=language2,
                    categories=categories,
                    output_format=output_format,
                    output_file=output_file,
                    show_progress=True
                )
                self.console.print("[bold green]Comparison complete![/bold green]")
            except Exception as e:
                self.console.print(f"[bold red]Error during comparison: {e}[/bold red]")
    
    def _show_available_categories(self) -> None:
        """Show available analysis categories."""
        self.console.print("\n[bold]Available Analysis Categories:[/bold]")
        
        for category, metrics in METRICS_CATEGORIES.items():
            self.console.print(f"[bold green]{category}[/bold green]")
            
            # Create a tree for the metrics
            tree = Tree(f"{len(metrics)} metrics")
            for metric in metrics:
                tree.add(metric)
            
            self.console.print(tree)


# Click command group
@click.group()
def cli():
    """
    Codebase Analysis Viewer CLI
    
    This tool allows you to analyze a single codebase, compare two codebases,
    and view the results in various formats.
    """
    pass


@cli.command(name="analyze")
@click.argument("repo_source", type=str)
@click.option(
    "--language",
    type=str,
    help="Programming language of the codebase (auto-detected if not provided)"
)
@click.option(
    "--categories",
    type=str,
    help="Categories to analyze (comma-separated, all if not provided)"
)
@click.option(
    "--output-format",
    type=click.Choice(OUTPUT_FORMATS),
    default=DEFAULT_OUTPUT_FORMAT,
    help=f"Output format (default: {DEFAULT_OUTPUT_FORMAT})"
)
@click.option(
    "--output-file",
    type=str,
    help="Path to the output file (default: analysis_results.<format>)"
)
@click.option(
    "--no-progress",
    is_flag=True,
    help="Disable progress indicators"
)
def analyze(
    repo_source: str,
    language: Optional[str] = None,
    categories: Optional[str] = None,
    output_format: str = DEFAULT_OUTPUT_FORMAT,
    output_file: Optional[str] = None,
    no_progress: bool = False
):
    """
    Analyze a single codebase.
    
    REPO_SOURCE can be a URL or local path to the repository.
    """
    # Parse categories
    categories_list = None
    if categories:
        categories_list = [c.strip() for c in categories.split(",")]
    
    # Set default output file if not provided
    if output_format in ["json", "html"] and not output_file:
        output_file = f"{DEFAULT_OUTPUT_FILE}.{output_format}"
    
    # Create the viewer and analyze the codebase
    viewer = CodebaseAnalysisViewer()
    try:
        viewer.analyze_codebase(
            repo_source=repo_source,
            language=language,
            categories=categories_list,
            output_format=output_format,
            output_file=output_file,
            show_progress=not no_progress
        )
        console.print("[bold green]Analysis complete![/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error during analysis: {e}[/bold red]")
        sys.exit(1)


@cli.command(name="compare")
@click.argument("repo_source1", type=str)
@click.argument("repo_source2", type=str)
@click.option(
    "--language1",
    type=str,
    help="Programming language of the first codebase (auto-detected if not provided)"
)
@click.option(
    "--language2",
    type=str,
    help="Programming language of the second codebase (auto-detected if not provided)"
)
@click.option(
    "--categories",
    type=str,
    help="Categories to analyze (comma-separated, all if not provided)"
)
@click.option(
    "--output-format",
    type=click.Choice(OUTPUT_FORMATS),
    default=DEFAULT_OUTPUT_FORMAT,
    help=f"Output format (default: {DEFAULT_OUTPUT_FORMAT})"
)
@click.option(
    "--output-file",
    type=str,
    help="Path to the output file (default: analysis_results_comparison.<format>)"
)
@click.option(
    "--no-progress",
    is_flag=True,
    help="Disable progress indicators"
)
def compare(
    repo_source1: str,
    repo_source2: str,
    language1: Optional[str] = None,
    language2: Optional[str] = None,
    categories: Optional[str] = None,
    output_format: str = DEFAULT_OUTPUT_FORMAT,
    output_file: Optional[str] = None,
    no_progress: bool = False
):
    """
    Compare two codebases.
    
    REPO_SOURCE1 and REPO_SOURCE2 can be URLs or local paths to the repositories.
    """
    # Parse categories
    categories_list = None
    if categories:
        categories_list = [c.strip() for c in categories.split(",")]
    
    # Set default output file if not provided
    if output_format in ["json", "html"] and not output_file:
        output_file = f"{DEFAULT_OUTPUT_FILE}_comparison.{output_format}"
    
    # Create the viewer and compare the codebases
    viewer = CodebaseAnalysisViewer()
    try:
        viewer.compare_codebases(
            repo_source1=repo_source1,
            repo_source2=repo_source2,
            language1=language1,
            language2=language2,
            categories=categories_list,
            output_format=output_format,
            output_file=output_file,
            show_progress=not no_progress
        )
        console.print("[bold green]Comparison complete![/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error during comparison: {e}[/bold red]")
        sys.exit(1)


@cli.command(name="interactive")
def interactive():
    """
    Run the interactive mode with rich text formatting.
    
    This mode provides a guided interface for analyzing and comparing codebases.
    """
    viewer = CodebaseAnalysisViewer()
    viewer.run_interactive_mode()


@cli.command(name="list-categories")
def list_categories():
    """
    List all available analysis categories.
    """
    console.print("[bold]Available Analysis Categories:[/bold]")
    
    for category, metrics in METRICS_CATEGORIES.items():
        console.print(f"[bold green]{category}[/bold green]")
        
        # Create a tree for the metrics
        tree = Tree(f"{len(metrics)} metrics")
        for metric in metrics:
            tree.add(metric)
        
        console.print(tree)


if __name__ == "__main__":
    cli()

