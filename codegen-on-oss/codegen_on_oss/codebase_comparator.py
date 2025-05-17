#!/usr/bin/env python3
"""
Codebase Comparator

This module provides functionality to compare two codebases and analyze their differences.
It builds on the CodebaseAnalyzer to provide comparative analysis between two repositories
or between two branches of the same repository.
"""

import os
import sys
import json
import logging
import argparse
import tempfile
from typing import Dict, List, Set, Tuple, Any, Optional, Union
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
import difflib
import networkx as nx
import matplotlib.pyplot as plt

try:
    from codegen_on_oss.codebase_analyzer import CodebaseAnalyzer, METRICS_CATEGORIES
except ImportError:
    print("CodebaseAnalyzer not found. Please ensure it's in the same directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class CodebaseComparator:
    """
    Compares two codebases and analyzes their differences.
    
    This class provides methods to compare two codebases (either different repositories
    or different branches of the same repository) and analyze their structural and
    functional differences.
    """
    
    def __init__(
        self, 
        base_repo_url: str = None, 
        base_repo_path: str = None,
        compare_repo_url: str = None, 
        compare_repo_path: str = None,
        base_branch: str = None,
        compare_branch: str = None,
        language: str = None
    ):
        """
        Initialize the CodebaseComparator.
        
        Args:
            base_repo_url: URL of the base repository
            base_repo_path: Local path to the base repository
            compare_repo_url: URL of the repository to compare against
            compare_repo_path: Local path to the repository to compare against
            base_branch: Branch name for the base repository (if comparing branches)
            compare_branch: Branch name for the comparison (if comparing branches)
            language: Programming language of the codebases (auto-detected if not provided)
        """
        self.base_repo_url = base_repo_url
        self.base_repo_path = base_repo_path
        self.compare_repo_url = compare_repo_url
        self.compare_repo_path = compare_repo_path
        self.base_branch = base_branch
        self.compare_branch = compare_branch
        self.language = language
        self.console = Console()
        self.results = {}
        
        # Initialize analyzers
        self.base_analyzer = None
        self.compare_analyzer = None
        
        # Initialize the analyzers
        if base_repo_url or base_repo_path:
            self._init_base_analyzer()
        
        if compare_repo_url or compare_repo_path:
            self._init_compare_analyzer()
    
    def _init_base_analyzer(self):
        """Initialize the base codebase analyzer."""
        try:
            self.console.print(f"[bold green]Initializing base codebase analyzer...[/bold green]")
            self.base_analyzer = CodebaseAnalyzer(
                repo_url=self.base_repo_url,
                repo_path=self.base_repo_path,
                language=self.language
            )
            self.console.print(f"[bold green]Successfully initialized base codebase analyzer[/bold green]")
        except Exception as e:
            self.console.print(f"[bold red]Error initializing base codebase analyzer: {e}[/bold red]")
            raise
    
    def _init_compare_analyzer(self):
        """Initialize the comparison codebase analyzer."""
        try:
            self.console.print(f"[bold green]Initializing comparison codebase analyzer...[/bold green]")
            self.compare_analyzer = CodebaseAnalyzer(
                repo_url=self.compare_repo_url,
                repo_path=self.compare_repo_path,
                language=self.language
            )
            self.console.print(f"[bold green]Successfully initialized comparison codebase analyzer[/bold green]")
        except Exception as e:
            self.console.print(f"[bold red]Error initializing comparison codebase analyzer: {e}[/bold red]")
            raise
    
    def compare(self, categories: List[str] = None, output_format: str = "json", output_file: str = None):
        """
        Perform a comparative analysis of the two codebases.
        
        Args:
            categories: List of categories to analyze. If None, all categories are analyzed.
            output_format: Format of the output (json, html, console)
            output_file: Path to the output file
            
        Returns:
            Dict containing the comparison results
        """
        if not self.base_analyzer or not self.compare_analyzer:
            raise ValueError("Both base and comparison codebases must be initialized.")
        
        # If no categories specified, analyze all
        if not categories:
            categories = list(METRICS_CATEGORIES.keys())
        
        # Initialize results dictionary
        self.results = {
            "metadata": {
                "base_repo": self.base_repo_url or self.base_repo_path,
                "compare_repo": self.compare_repo_url or self.compare_repo_path,
                "base_branch": self.base_branch,
                "compare_branch": self.compare_branch,
                "language": self.language,
                "categories_analyzed": categories
            },
            "categories": {}
        }
        
        # Analyze both codebases
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn()
        ) as progress:
            
            task = progress.add_task("[green]Analyzing codebases...", total=len(categories))
            
            for category in categories:
                progress.update(task, description=f"[green]Analyzing {category}...")
                
                # Get metrics for this category
                metrics = METRICS_CATEGORIES.get(category, [])
                
                # Initialize category in results
                self.results["categories"][category] = {}
                
                # Process each metric
                for metric_name in metrics:
                    # Get the metric method from both analyzers
                    base_metric_method = getattr(self.base_analyzer, metric_name, None)
                    compare_metric_method = getattr(self.compare_analyzer, metric_name, None)
                    
                    if base_metric_method and compare_metric_method:
                        try:
                            # Get results from both analyzers
                            base_result = base_metric_method()
                            compare_result = compare_metric_method()
                            
                            # Compare the results
                            comparison = self._compare_metric_results(base_result, compare_result)
                            
                            # Store the comparison
                            self.results["categories"][category][metric_name] = comparison
                        except Exception as e:
                            self.results["categories"][category][metric_name] = {
                                "error": str(e)
                            }
                
                progress.update(task, advance=1)
        
        # Output the results
        if output_format == "json":
            if output_file:
                with open(output_file, "w") as f:
                    json.dump(self.results, f, indent=2)
                self.console.print(f"[bold green]JSON results saved to {output_file}[/bold green]")
            else:
                self.console.print(json.dumps(self.results, indent=2))
        elif output_format == "html":
            self._generate_html_report(output_file)
        else:  # console
            self._print_console_report()
        
        return self.results
    
    def _compare_metric_results(self, base_result: Any, compare_result: Any) -> Dict[str, Any]:
        """
        Compare the results of a metric between the two codebases.
        
        Args:
            base_result: Result from the base codebase
            compare_result: Result from the comparison codebase
            
        Returns:
            Dict containing the comparison
        """
        comparison = {
            "base": base_result,
            "compare": compare_result,
            "differences": {}
        }
        
        # Handle different types of results
        if isinstance(base_result, dict) and isinstance(compare_result, dict):
            # Compare dictionaries
            all_keys = set(base_result.keys()) | set(compare_result.keys())
            
            for key in all_keys:
                if key in base_result and key in compare_result:
                    # Both have this key
                    if base_result[key] != compare_result[key]:
                        comparison["differences"][key] = {
                            "base": base_result[key],
                            "compare": compare_result[key]
                        }
                elif key in base_result:
                    # Only in base
                    comparison["differences"][key] = {
                        "base": base_result[key],
                        "compare": None,
                        "only_in": "base"
                    }
                else:
                    # Only in compare
                    comparison["differences"][key] = {
                        "base": None,
                        "compare": compare_result[key],
                        "only_in": "compare"
                    }
        elif isinstance(base_result, list) and isinstance(compare_result, list):
            # Compare lists
            base_set = set(str(item) for item in base_result)
            compare_set = set(str(item) for item in compare_result)
            
            comparison["differences"] = {
                "only_in_base": list(base_set - compare_set),
                "only_in_compare": list(compare_set - base_set),
                "common": list(base_set & compare_set)
            }
        else:
            # Simple comparison
            if base_result != compare_result:
                comparison["differences"] = {
                    "base": base_result,
                    "compare": compare_result
                }
        
        return comparison
    
    def _generate_html_report(self, output_file: str) -> None:
        """Generate an HTML report of the comparison results."""
        if not output_file:
            output_file = "codebase_comparison_report.html"
        
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
                .diff-added {{ background-color: #e6ffed; }}
                .diff-removed {{ background-color: #ffeef0; }}
            </style>
        </head>
        <body>
            <h1>Codebase Comparison Report</h1>
            <div class="section">
                <h2>Metadata</h2>
                <p><strong>Base Repository:</strong> {self.results["metadata"]["base_repo"]}</p>
                <p><strong>Compare Repository:</strong> {self.results["metadata"]["compare_repo"]}</p>
                <p><strong>Base Branch:</strong> {self.results["metadata"]["base_branch"] or "N/A"}</p>
                <p><strong>Compare Branch:</strong> {self.results["metadata"]["compare_branch"] or "N/A"}</p>
                <p><strong>Language:</strong> {self.results["metadata"]["language"] or "Auto-detected"}</p>
            </div>
        """
        
        # Add each category
        for category, metrics in self.results["categories"].items():
            html += f"""
            <div class="section">
                <h2>{category.replace("_", " ").title()}</h2>
            """
            
            for metric_name, metric_value in metrics.items():
                html += f"""
                <div class="metric">
                    <h3 class="metric-title">{metric_name.replace("_", " ").title()}</h3>
                    <pre>{json.dumps(metric_value, indent=2)}</pre>
                </div>
                """
            
            html += "</div>"
        
        html += """
        </body>
        </html>
        """
        
        with open(output_file, "w") as f:
            f.write(html)
        
        self.console.print(f"[bold green]HTML report saved to {output_file}[/bold green]")
    
    def _print_console_report(self) -> None:
        """Print a summary report to the console."""
        self.console.print(f"[bold blue]Codebase Comparison Report[/bold blue]")
        self.console.print(f"[bold]Base Repository:[/bold] {self.results['metadata']['base_repo']}")
        self.console.print(f"[bold]Compare Repository:[/bold] {self.results['metadata']['compare_repo']}")
        
        if self.results['metadata']['base_branch']:
            self.console.print(f"[bold]Base Branch:[/bold] {self.results['metadata']['base_branch']}")
        
        if self.results['metadata']['compare_branch']:
            self.console.print(f"[bold]Compare Branch:[/bold] {self.results['metadata']['compare_branch']}")
        
        self.console.print(f"[bold]Language:[/bold] {self.results['metadata']['language'] or 'Auto-detected'}")
        
        for category, metrics in self.results["categories"].items():
            self.console.print(f"\n[bold green]{category.replace('_', ' ').title()}[/bold green]")
            
            for metric_name, metric_value in metrics.items():
                self.console.print(f"[bold]{metric_name.replace('_', ' ').title()}:[/bold]")
                
                if "differences" in metric_value and metric_value["differences"]:
                    table = Table(show_header=True)
                    table.add_column("Difference")
                    table.add_column("Base")
                    table.add_column("Compare")
                    
                    for diff_key, diff_value in metric_value["differences"].items():
                        if isinstance(diff_value, dict) and "base" in diff_value and "compare" in diff_value:
                            table.add_row(
                                str(diff_key),
                                str(diff_value["base"]),
                                str(diff_value["compare"])
                            )
                        else:
                            table.add_row(str(diff_key), str(diff_value), "")
                    
                    self.console.print(table)
                else:
                    self.console.print("No significant differences found.")


def main():
    """Main entry point for the codebase comparator."""
    parser = argparse.ArgumentParser(description="Codebase Comparator")
    
    # Repository sources
    parser.add_argument("--base-repo-url", help="URL of the base repository")
    parser.add_argument("--base-repo-path", help="Local path to the base repository")
    parser.add_argument("--compare-repo-url", help="URL of the repository to compare against")
    parser.add_argument("--compare-repo-path", help="Local path to the repository to compare against")
    
    # Branch comparison
    parser.add_argument("--base-branch", help="Branch name for the base repository (if comparing branches)")
    parser.add_argument("--compare-branch", help="Branch name for the comparison (if comparing branches)")
    
    # Analysis options
    parser.add_argument("--language", help="Programming language of the codebases (auto-detected if not provided)")
    parser.add_argument("--categories", nargs="+", help="Categories to analyze (default: all)")
    
    # Output options
    parser.add_argument("--output-format", choices=["json", "html", "console"], default="console", help="Output format")
    parser.add_argument("--output-file", help="Path to the output file")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not ((args.base_repo_url or args.base_repo_path) and (args.compare_repo_url or args.compare_repo_path)):
        parser.error("You must specify both a base repository and a comparison repository.")
    
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
        elif args.output_format == "html":
            print(f"HTML report saved to {args.output_file or 'codebase_comparison_report.html'}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

