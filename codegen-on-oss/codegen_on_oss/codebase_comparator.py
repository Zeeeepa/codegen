#!/usr/bin/env python3
"""
Codebase Comparator

This module provides functionality to compare two codebases and identify differences
between them. It can compare different repositories or different branches of the same
repository.
"""

import os
import sys
import json
import time
import logging
import argparse
import tempfile
import datetime
import difflib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional, Union

try:
    from .codebase_analyzer import CodebaseAnalyzer
except ImportError:
    try:
        from codebase_analyzer import CodebaseAnalyzer
    except ImportError:
        print("Codebase analyzer module not found. Please ensure it's in the same directory.")
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
    Compares two codebases and identifies differences between them.
    
    This class can compare different repositories or different branches of the same
    repository. It provides methods to analyze and compare various aspects of the
    codebases, such as structure, dependencies, code quality, etc.
    """
    
    def __init__(
        self, 
        base_repo_url: Optional[str] = None, 
        base_repo_path: Optional[str] = None,
        compare_repo_url: Optional[str] = None,
        compare_repo_path: Optional[str] = None,
        base_branch: Optional[str] = None,
        compare_branch: Optional[str] = None,
        language: Optional[str] = None
    ):
        """
        Initialize the CodebaseComparator.
        
        Args:
            base_repo_url: URL of the base repository to compare
            base_repo_path: Local path to the base repository to compare
            compare_repo_url: URL of the repository to compare against the base
            compare_repo_path: Local path to the repository to compare against the base
            base_branch: Branch of the base repository to compare
            compare_branch: Branch of the repository to compare against the base
            language: Programming language of the codebases (auto-detected if not provided)
        """
        self.base_repo_url = base_repo_url
        self.base_repo_path = base_repo_path
        self.compare_repo_url = compare_repo_url
        self.compare_repo_path = compare_repo_path
        self.base_branch = base_branch
        self.compare_branch = compare_branch
        self.language = language
        
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
            self.base_analyzer = CodebaseAnalyzer(
                repo_url=self.base_repo_url,
                repo_path=self.base_repo_path,
                language=self.language
            )
            
            # If branches are specified, checkout the base branch
            if self.base_branch and self.base_analyzer.codebase:
                self.base_analyzer.codebase.checkout_branch(self.base_branch)
            
        except Exception as e:
            logger.error(f"Error initializing base analyzer: {e}")
            raise
    
    def _init_compare_analyzer(self):
        """Initialize the compare codebase analyzer."""
        try:
            self.compare_analyzer = CodebaseAnalyzer(
                repo_url=self.compare_repo_url,
                repo_path=self.compare_repo_path,
                language=self.language
            )
            
            # If branches are specified, checkout the compare branch
            if self.compare_branch and self.compare_analyzer.codebase:
                self.compare_analyzer.codebase.checkout_branch(self.compare_branch)
            
        except Exception as e:
            logger.error(f"Error initializing compare analyzer: {e}")
            raise
    
    def compare(
        self, 
        categories: Optional[List[str]] = None, 
        output_format: str = "json", 
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare the two codebases and identify differences.
        
        Args:
            categories: List of categories to compare. If None, all categories are compared.
            output_format: Format of the output (json, html, console)
            output_file: Path to the output file
            
        Returns:
            Dict containing the comparison results
        """
        if not self.base_analyzer or not self.compare_analyzer:
            raise ValueError("Both base and compare analyzers must be initialized.")
        
        # Analyze both codebases
        base_results = self.base_analyzer.analyze(categories=categories)
        compare_results = self.compare_analyzer.analyze(categories=categories)
        
        # Compare the results
        comparison_results = self._compare_results(base_results, compare_results)
        
        # Output the results
        if output_format == "json" and output_file:
            with open(output_file, "w") as f:
                json.dump(comparison_results, f, indent=2)
        elif output_format == "html" and output_file:
            self._generate_html_report(comparison_results, output_file)
        elif output_format == "console":
            self._print_console_report(comparison_results)
        
        return comparison_results
    
    def _compare_results(self, base_results: Dict[str, Any], compare_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare the analysis results of the two codebases.
        
        Args:
            base_results: Analysis results of the base codebase
            compare_results: Analysis results of the compare codebase
            
        Returns:
            Dict containing the comparison results
        """
        comparison = {
            "metadata": {
                "base_repo": base_results["metadata"]["repo_name"],
                "compare_repo": compare_results["metadata"]["repo_name"],
                "base_branch": self.base_branch,
                "compare_branch": self.compare_branch,
                "comparison_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "language": self.language or "auto-detected"
            },
            "categories": {}
        }
        
        # Compare each category
        for category in base_results["categories"]:
            if category in compare_results["categories"]:
                comparison["categories"][category] = self._compare_category(
                    base_results["categories"][category],
                    compare_results["categories"][category]
                )
        
        return comparison
    
    def _compare_category(self, base_category: Dict[str, Any], compare_category: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare a specific category between the two codebases.
        
        Args:
            base_category: Category results from the base codebase
            compare_category: Category results from the compare codebase
            
        Returns:
            Dict containing the comparison results for the category
        """
        category_comparison = {}
        
        # Compare each metric in the category
        for metric in base_category:
            if metric in compare_category:
                category_comparison[metric] = self._compare_metric(
                    base_category[metric],
                    compare_category[metric]
                )
        
        return category_comparison
    
    def _compare_metric(self, base_metric: Any, compare_metric: Any) -> Dict[str, Any]:
        """
        Compare a specific metric between the two codebases.
        
        Args:
            base_metric: Metric value from the base codebase
            compare_metric: Metric value from the compare codebase
            
        Returns:
            Dict containing the comparison results for the metric
        """
        # Handle different types of metrics
        if isinstance(base_metric, dict) and isinstance(compare_metric, dict):
            return self._compare_dict_metric(base_metric, compare_metric)
        elif isinstance(base_metric, list) and isinstance(compare_metric, list):
            return self._compare_list_metric(base_metric, compare_metric)
        elif isinstance(base_metric, (int, float)) and isinstance(compare_metric, (int, float)):
            return self._compare_numeric_metric(base_metric, compare_metric)
        else:
            # For other types, just return both values
            return {
                "base": base_metric,
                "compare": compare_metric,
                "difference": "Cannot compute difference for this type"
            }
    
    def _compare_dict_metric(self, base_metric: Dict[str, Any], compare_metric: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare a dictionary metric between the two codebases.
        
        Args:
            base_metric: Dictionary metric from the base codebase
            compare_metric: Dictionary metric from the compare codebase
            
        Returns:
            Dict containing the comparison results for the metric
        """
        comparison = {
            "base": base_metric,
            "compare": compare_metric,
            "differences": {}
        }
        
        # Find keys in both dictionaries
        common_keys = set(base_metric.keys()) & set(compare_metric.keys())
        only_in_base = set(base_metric.keys()) - set(compare_metric.keys())
        only_in_compare = set(compare_metric.keys()) - set(base_metric.keys())
        
        # Compare common keys
        for key in common_keys:
            if isinstance(base_metric[key], dict) and isinstance(compare_metric[key], dict):
                comparison["differences"][key] = self._compare_dict_metric(
                    base_metric[key],
                    compare_metric[key]
                )
            elif isinstance(base_metric[key], list) and isinstance(compare_metric[key], list):
                comparison["differences"][key] = self._compare_list_metric(
                    base_metric[key],
                    compare_metric[key]
                )
            elif isinstance(base_metric[key], (int, float)) and isinstance(compare_metric[key], (int, float)):
                comparison["differences"][key] = self._compare_numeric_metric(
                    base_metric[key],
                    compare_metric[key]
                )
            else:
                comparison["differences"][key] = {
                    "base": base_metric[key],
                    "compare": compare_metric[key],
                    "difference": "Cannot compute difference for this type"
                }
        
        # Add keys only in base
        for key in only_in_base:
            comparison["differences"][key] = {
                "base": base_metric[key],
                "compare": None,
                "difference": "Only in base"
            }
        
        # Add keys only in compare
        for key in only_in_compare:
            comparison["differences"][key] = {
                "base": None,
                "compare": compare_metric[key],
                "difference": "Only in compare"
            }
        
        return comparison
    
    def _compare_list_metric(self, base_metric: List[Any], compare_metric: List[Any]) -> Dict[str, Any]:
        """
        Compare a list metric between the two codebases.
        
        Args:
            base_metric: List metric from the base codebase
            compare_metric: List metric from the compare codebase
            
        Returns:
            Dict containing the comparison results for the metric
        """
        comparison = {
            "base": base_metric,
            "compare": compare_metric,
            "differences": {
                "length_difference": len(compare_metric) - len(base_metric),
                "common_items": [],
                "only_in_base": [],
                "only_in_compare": []
            }
        }
        
        # If the lists contain dictionaries with a 'name' key, use that for comparison
        if (base_metric and isinstance(base_metric[0], dict) and "name" in base_metric[0] and
            compare_metric and isinstance(compare_metric[0], dict) and "name" in compare_metric[0]):
            
            base_names = {item["name"]: item for item in base_metric}
            compare_names = {item["name"]: item for item in compare_metric}
            
            common_names = set(base_names.keys()) & set(compare_names.keys())
            only_in_base = set(base_names.keys()) - set(compare_names.keys())
            only_in_compare = set(compare_names.keys()) - set(base_names.keys())
            
            comparison["differences"]["common_items"] = [
                {"name": name, "base": base_names[name], "compare": compare_names[name]}
                for name in common_names
            ]
            comparison["differences"]["only_in_base"] = [base_names[name] for name in only_in_base]
            comparison["differences"]["only_in_compare"] = [compare_names[name] for name in only_in_compare]
        else:
            # For simple lists, use set operations
            try:
                base_set = set(base_metric)
                compare_set = set(compare_metric)
                
                comparison["differences"]["common_items"] = list(base_set & compare_set)
                comparison["differences"]["only_in_base"] = list(base_set - compare_set)
                comparison["differences"]["only_in_compare"] = list(compare_set - base_set)
            except:
                # If items are not hashable, use a different approach
                comparison["differences"]["common_items"] = "Cannot compute common items for this list type"
                comparison["differences"]["only_in_base"] = "Cannot compute items only in base for this list type"
                comparison["differences"]["only_in_compare"] = "Cannot compute items only in compare for this list type"
        
        return comparison
    
    def _compare_numeric_metric(self, base_metric: Union[int, float], compare_metric: Union[int, float]) -> Dict[str, Any]:
        """
        Compare a numeric metric between the two codebases.
        
        Args:
            base_metric: Numeric metric from the base codebase
            compare_metric: Numeric metric from the compare codebase
            
        Returns:
            Dict containing the comparison results for the metric
        """
        absolute_diff = compare_metric - base_metric
        
        # Calculate percentage difference
        if base_metric != 0:
            percentage_diff = (absolute_diff / base_metric) * 100
        else:
            percentage_diff = float('inf') if compare_metric > 0 else 0
        
        return {
            "base": base_metric,
            "compare": compare_metric,
            "absolute_difference": absolute_diff,
            "percentage_difference": percentage_diff
        }
    
    def _generate_html_report(self, comparison_results: Dict[str, Any], output_file: str) -> None:
        """
        Generate an HTML report of the comparison results.
        
        Args:
            comparison_results: Results of the comparison
            output_file: Path to the output file
        """
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
                .positive {{ color: green; }}
                .negative {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>Codebase Comparison Report</h1>
            <div class="section">
                <h2>Metadata</h2>
                <p><strong>Base Repository:</strong> {comparison_results["metadata"]["base_repo"]}</p>
                <p><strong>Compare Repository:</strong> {comparison_results["metadata"]["compare_repo"]}</p>
                <p><strong>Base Branch:</strong> {comparison_results["metadata"]["base_branch"] or "N/A"}</p>
                <p><strong>Compare Branch:</strong> {comparison_results["metadata"]["compare_branch"] or "N/A"}</p>
                <p><strong>Comparison Time:</strong> {comparison_results["metadata"]["comparison_time"]}</p>
                <p><strong>Language:</strong> {comparison_results["metadata"]["language"]}</p>
            </div>
        """
        
        # Add each category
        for category, metrics in comparison_results["categories"].items():
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
        
        logger.info(f"HTML report saved to {output_file}")
    
    def _print_console_report(self, comparison_results: Dict[str, Any]) -> None:
        """
        Print a summary report to the console.
        
        Args:
            comparison_results: Results of the comparison
        """
        from rich.console import Console
        from rich.table import Table
        
        console = Console()
        
        console.print(f"[bold blue]Codebase Comparison Report[/bold blue]")
        console.print(f"[bold]Base Repository:[/bold] {comparison_results['metadata']['base_repo']}")
        console.print(f"[bold]Compare Repository:[/bold] {comparison_results['metadata']['compare_repo']}")
        console.print(f"[bold]Base Branch:[/bold] {comparison_results['metadata']['base_branch'] or 'N/A'}")
        console.print(f"[bold]Compare Branch:[/bold] {comparison_results['metadata']['compare_branch'] or 'N/A'}")
        console.print(f"[bold]Comparison Time:[/bold] {comparison_results['metadata']['comparison_time']}")
        console.print(f"[bold]Language:[/bold] {comparison_results['metadata']['language']}")
        
        for category, metrics in comparison_results["categories"].items():
            console.print(f"\n[bold green]{category.replace('_', ' ').title()}[/bold green]")
            
            for metric_name, metric_value in metrics.items():
                console.print(f"[bold]{metric_name.replace('_', ' ').title()}:[/bold]")
                
                if "base" in metric_value and "compare" in metric_value:
                    table = Table(show_header=True)
                    table.add_column("Metric")
                    table.add_column("Base")
                    table.add_column("Compare")
                    table.add_column("Difference")
                    
                    if isinstance(metric_value["base"], (int, float)) and isinstance(metric_value["compare"], (int, float)):
                        diff = metric_value["compare"] - metric_value["base"]
                        diff_str = f"{diff:+g}"
                        if diff > 0:
                            diff_str = f"[green]{diff_str}[/green]"
                        elif diff < 0:
                            diff_str = f"[red]{diff_str}[/red]"
                        
                        table.add_row(
                            metric_name.replace("_", " ").title(),
                            str(metric_value["base"]),
                            str(metric_value["compare"]),
                            diff_str
                        )
                    else:
                        table.add_row(
                            metric_name.replace("_", " ").title(),
                            str(metric_value["base"]),
                            str(metric_value["compare"]),
                            "N/A"
                        )
                    
                    console.print(table)
                else:
                    console.print(str(metric_value))


def main():
    """Main entry point for the codebase comparator."""
    parser = argparse.ArgumentParser(description="Codebase Comparator")
    
    # Repository sources
    base_group = parser.add_mutually_exclusive_group(required=True)
    base_group.add_argument("--base-repo-url", help="URL of the base repository to compare")
    base_group.add_argument("--base-repo-path", help="Local path to the base repository to compare")
    
    compare_group = parser.add_mutually_exclusive_group(required=True)
    compare_group.add_argument("--compare-repo-url", help="URL of the repository to compare against the base")
    compare_group.add_argument("--compare-repo-path", help="Local path to the repository to compare against the base")
    
    # Branch options
    parser.add_argument("--base-branch", help="Branch of the base repository to compare")
    parser.add_argument("--compare-branch", help="Branch of the repository to compare against the base")
    
    # Analysis options
    parser.add_argument("--language", help="Programming language of the codebases (auto-detected if not provided)")
    parser.add_argument("--categories", nargs="+", help="Categories to compare (default: all)")
    
    # Output options
    parser.add_argument("--output-format", choices=["json", "html", "console"], default="console", help="Output format")
    parser.add_argument("--output-file", help="Path to the output file")
    
    args = parser.parse_args()
    
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
