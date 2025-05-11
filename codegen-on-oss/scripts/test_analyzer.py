#!/usr/bin/env python3
"""
Test the codebase analyzer with various repositories.

This script tests the codebase analyzer with a variety of repositories
to ensure it works correctly with different codebases.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codegen_on_oss.analysis.codebase_analyzer import CodebaseAnalyzer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn


# Test repositories
TEST_REPOS = [
    # Small repositories
    "https://github.com/pallets/click",
    "https://github.com/psf/black",
    
    # Medium repositories
    "https://github.com/django/django",
    "https://github.com/pandas-dev/pandas",
    
    # Large repositories
    "https://github.com/tensorflow/tensorflow",
    "https://github.com/pytorch/pytorch",
    
    # Different languages
    "https://github.com/facebook/react",  # JavaScript
    "https://github.com/golang/go",       # Go
    "https://github.com/rust-lang/rust",  # Rust
]


def test_repository(repo_url: str, categories: List[str] = None, output_dir: Path = None) -> Dict[str, Any]:
    """
    Test the codebase analyzer with a repository.
    
    Args:
        repo_url: URL of the repository to test
        categories: List of categories to analyze
        output_dir: Directory to save the analysis results
        
    Returns:
        Dict containing the test results
    """
    console = Console()
    console.print(f"[bold blue]Testing repository: {repo_url}[/bold blue]")
    
    start_time = time.time()
    
    try:
        # Initialize the analyzer
        analyzer = CodebaseAnalyzer(repo_url=repo_url)
        
        # Perform the analysis
        results = analyzer.analyze(categories=categories)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Save the results if output_dir is provided
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            repo_name = repo_url.split("/")[-1]
            output_file = output_dir / f"{repo_name}.json"
            
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)
            
            console.print(f"[bold green]Results saved to {output_file}[/bold green]")
        
        console.print(f"[bold green]Analysis completed in {duration:.2f} seconds[/bold green]")
        
        return {
            "repo_url": repo_url,
            "success": True,
            "duration": duration,
            "error": None,
            "results": results
        }
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        console.print(f"[bold red]Error analyzing repository: {e}[/bold red]")
        
        return {
            "repo_url": repo_url,
            "success": False,
            "duration": duration,
            "error": str(e),
            "results": None
        }


def main():
    """Main entry point for the test script."""
    parser = argparse.ArgumentParser(description="Test the codebase analyzer with various repositories")
    
    parser.add_argument(
        "--repos",
        nargs="+",
        help="List of repository URLs to test (default: predefined list)",
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        help="Categories to analyze (default: all)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory to save the analysis results",
    )
    
    args = parser.parse_args()
    
    repos = args.repos or TEST_REPOS
    categories = args.categories
    output_dir = args.output_dir
    
    console = Console()
    
    # Create a table to display the results
    table = Table(title="Codebase Analyzer Test Results")
    table.add_column("Repository")
    table.add_column("Success")
    table.add_column("Duration (s)")
    table.add_column("Error")
    
    # Test each repository
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("[cyan]Testing repositories...", total=len(repos))
        
        results = []
        
        for repo_url in repos:
            progress.update(task, description=f"[cyan]Testing {repo_url}...")
            
            result = test_repository(repo_url, categories, output_dir)
            results.append(result)
            
            progress.advance(task)
    
    # Display the results
    for result in results:
        table.add_row(
            result["repo_url"],
            "[green]✓[/green]" if result["success"] else "[red]✗[/red]",
            f"{result['duration']:.2f}",
            result["error"] or ""
        )
    
    console.print(table)
    
    # Print summary
    success_count = sum(1 for result in results if result["success"])
    console.print(f"[bold]Summary:[/bold] {success_count}/{len(results)} repositories analyzed successfully")


if __name__ == "__main__":
    main()

