#!/usr/bin/env python3
"""
Codebase Analysis API Client

This script demonstrates how to use the Codebase Analysis API to analyze a repository
and display the results in a user-friendly format.
"""

import argparse
import json
import requests
import sys
from typing import Dict, Any, Optional
from enum import Enum
from rich.console import Console
from rich.tree import Tree
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich import print as rprint

# Configuration
API_URL = "http://localhost:8000"

class VisualizationType(str, Enum):
    CALL_GRAPH = "call_graph"
    DEPENDENCY_GRAPH = "dependency_graph"
    SYMBOL_TREE = "symbol_tree"
    MODULE_DEPENDENCY = "module_dependency"
    INHERITANCE_HIERARCHY = "inheritance_hierarchy"

class LanguageType(str, Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    AUTO = "auto"

console = Console()

def analyze_repo(repo_url: str, language: LanguageType = LanguageType.AUTO) -> Dict[str, Any]:
    """Analyze a repository using the API"""
    url = f"{API_URL}/analyze/{repo_url}"
    params = {"language": language}
    
    with console.status(f"Analyzing repository {repo_url}..."):
        response = requests.get(url, params=params)
    
    if response.status_code != 200:
        console.print(f"[bold red]Error:[/bold red] {response.text}")
        sys.exit(1)
    
    return response.json()

def visualize_repo(repo_url: str, viz_type: VisualizationType, target: Optional[str] = None, language: LanguageType = LanguageType.AUTO) -> Dict[str, Any]:
    """Generate visualization for a repository"""
    url = f"{API_URL}/visualize/{repo_url}/{viz_type}"
    params = {"language": language}
    if target:
        params["target"] = target
    
    with console.status(f"Generating {viz_type} visualization..."):
        response = requests.get(url, params=params)
    
    if response.status_code != 200:
        console.print(f"[bold red]Error:[/bold red] {response.text}")
        sys.exit(1)
    
    return response.json()

def display_overall_statistics(stats: Dict[str, Any]) -> None:
    """Display overall statistics in a rich table"""
    console.print("\n[bold cyan]Overall Statistics[/bold cyan]")
    
    table = Table(show_header=False)
    table.add_column("Metric", style="green")
    table.add_column("Value", style="yellow")
    
    table.add_row("Total Files", str(stats["total_files"]))
    
    # Display files by language
    lang_breakdown = []
    for lang, count in stats["files_by_language"].items():
        percentage = (count / stats["total_files"]) * 100
        lang_breakdown.append(f"{lang.capitalize()}: {count} ({percentage:.1f}%)")
    
    table.add_row("Files by Language", "\n".join(lang_breakdown))
    table.add_row("Total Lines of Code", f"{stats['total_lines_of_code']:,}")
    table.add_row("Total Classes", str(stats["total_classes"]))
    table.add_row("Total Functions", str(stats["total_functions"]))
    table.add_row("Total Symbols", str(stats["total_symbols"]))
    table.add_row("Average Cyclomatic Complexity", str(stats["average_cyclomatic_complexity"]))
    
    console.print(table)

def display_important_files(files: list) -> None:
    """Display important files in a rich table"""
    console.print("\n[bold cyan]Important Files and Entry Points[/bold cyan]")
    
    table = Table()
    table.add_column("Type", style="green")
    table.add_column("Name", style="yellow")
    table.add_column("Filepath", style="blue")
    table.add_column("Details", style="magenta")
    
    for file in files:
        file_type = file["type"]
        name = file["name"]
        filepath = file["filepath"]
        
        if file_type == "function":
            details = f"Complexity: {file.get('complexity', 'N/A')}"
        elif file_type == "class":
            details = f"Methods: {file.get('methods', 'N/A')}"
        else:
            details = f"Symbols: {file.get('symbols', 'N/A')}"
        
        table.add_row(file_type.capitalize(), name, filepath, details)
    
    console.print(table)

def display_project_structure(structure: Dict[str, Any]) -> None:
    """Display project structure as a tree"""
    console.print("\n[bold cyan]Project Structure[/bold cyan]")
    
    def add_to_tree(node: Dict[str, Any], tree: Tree) -> None:
        if node["type"] == "directory":
            for child in node.get("children", []):
                if child["type"] == "directory":
                    branch = tree.add(f"[bold blue]{child['name']}[/bold blue]")
                    add_to_tree(child, branch)
                else:
                    # File node
                    file_details = f"[green]{child['name']}[/green]"
                    if "language" in child:
                        file_details += f" ([yellow]{child['language']}[/yellow])"
                    if "classes" in child and "functions" in child:
                        file_details += f" - {child['classes']} classes, {child['functions']} functions"
                    if "lines" in child:
                        file_details += f", {child['lines']} lines"
                    
                    file_branch = tree.add(file_details)
                    
                    # Add class and function details if available
                    if "details" in child:
                        for detail in child["details"]:
                            if detail["type"] == "class":
                                class_details = f"[bold magenta]class {detail['name']}[/bold magenta]"
                                class_details += f" - {detail.get('methods', 0)} methods"
                                class_branch = file_branch.add(class_details)
                                
                                # Add method details
                                if "methods_details" in detail:
                                    for method in detail["methods_details"]:
                                        method_details = f"[cyan]method {method['name']}[/cyan]"
                                        method_details += f" (line {method['line']}, {method['parameters']} params)"
                                        class_branch.add(method_details)
                            
                            elif detail["type"] == "function":
                                func_details = f"[cyan]function {detail['name']}[/cyan]"
                                func_details += f" (line {detail['line']}, {detail['parameters']} params)"
                                file_branch.add(func_details)
    
    tree = Tree(f"[bold red]{structure['name']}[/bold red]")
    add_to_tree(structure, tree)
    console.print(tree)

def display_code_quality_issues(issues: Dict[str, Any]) -> None:
    """Display code quality issues"""
    console.print("\n[bold cyan]Code Quality Issues[/bold cyan]")
    
    # Unused imports
    unused_imports = issues["unused_imports"]
    console.print(f"\n[bold yellow]Unused Imports:[/bold yellow] {unused_imports['count']} items")
    
    if unused_imports["count"] > 0:
        table = Table(show_header=True)
        table.add_column("Filepath", style="blue")
        table.add_column("Import", style="green")
        table.add_column("Line", style="yellow")
        
        for item in unused_imports["items"][:10]:  # Show first 10
            table.add_row(item["filepath"], item["import"], str(item["line"]))
        
        console.print(table)
        if len(unused_imports["items"]) > 10:
            console.print(f"[italic]...and {len(unused_imports['items']) - 10} more[/italic]")
    
    # Unused functions
    unused_functions = issues["unused_functions"]
    console.print(f"\n[bold yellow]Unused Functions:[/bold yellow] {unused_functions['count']} items")
    
    if unused_functions["count"] > 0:
        table = Table(show_header=True)
        table.add_column("Filepath", style="blue")
        table.add_column("Function", style="green")
        table.add_column("Line", style="yellow")
        
        for item in unused_functions["items"][:10]:  # Show first 10
            table.add_row(item["filepath"], item["name"], str(item["line"]))
        
        console.print(table)
        if len(unused_functions["items"]) > 10:
            console.print(f"[italic]...and {len(unused_functions['items']) - 10} more[/italic]")
    
    # Unused classes
    unused_classes = issues["unused_classes"]
    console.print(f"\n[bold yellow]Unused Classes:[/bold yellow] {unused_classes['count']} items")
    
    if unused_classes["count"] > 0:
        table = Table(show_header=True)
        table.add_column("Filepath", style="blue")
        table.add_column("Class", style="green")
        table.add_column("Line", style="yellow")
        
        for item in unused_classes["items"][:10]:  # Show first 10
            table.add_row(item["filepath"], item["name"], str(item["line"]))
        
        console.print(table)
        if len(unused_classes["items"]) > 10:
            console.print(f"[italic]...and {len(unused_classes['items']) - 10} more[/italic]")
    
    # High complexity functions
    complex_functions = issues["high_complexity_functions"]
    console.print(f"\n[bold yellow]High Complexity Functions:[/bold yellow] {complex_functions['count']} items")
    
    if complex_functions["count"] > 0:
        table = Table(show_header=True)
        table.add_column("Filepath", style="blue")
        table.add_column("Function", style="green")
        table.add_column("Complexity", style="red")
        table.add_column("Rank", style="yellow")
        table.add_column("Line", style="magenta")
        
        for item in complex_functions["items"][:10]:  # Show first 10
            table.add_row(
                item["filepath"], 
                item["name"], 
                str(item["complexity"]), 
                item["rank"], 
                str(item["line"])
            )
        
        console.print(table)
        if len(complex_functions["items"]) > 10:
            console.print(f"[italic]...and {len(complex_functions['items']) - 10} more[/italic]")

def display_visualization_options(options: list) -> None:
    """Display available visualization options"""
    console.print("\n[bold cyan]Available Visualizations[/bold cyan]")
    
    for option in options:
        console.print(f"- [green]{option}[/green]")
    
    console.print("\nTo generate a visualization, use:")
    console.print("[yellow]python client.py visualize REPO_URL VISUALIZATION_TYPE [--target TARGET] [--language LANGUAGE][/yellow]")

def display_visualization(viz_data: Dict[str, Any], viz_type: VisualizationType) -> None:
    """Display visualization data"""
    console.print(f"\n[bold cyan]{viz_type.value.replace('_', ' ').title()} Visualization[/bold cyan]")
    
    if "error" in viz_data:
        console.print(f"[bold red]Error:[/bold red] {viz_data['error']}")
        return
    
    if viz_type in [VisualizationType.CALL_GRAPH, VisualizationType.DEPENDENCY_GRAPH]:
        # Display graph data
        console.print(f"\nNodes: {len(viz_data['nodes'])}")
        console.print(f"Edges: {len(viz_data['edges'])}")
        
        # Display sample of nodes
        console.print("\n[bold yellow]Sample Nodes:[/bold yellow]")
        table = Table(show_header=True)
        table.add_column("ID", style="green")
        table.add_column("Type", style="blue")
        
        for node in viz_data["nodes"][:10]:  # Show first 10
            table.add_row(node["id"], node.get("type", "unknown"))
        
        console.print(table)
        if len(viz_data["nodes"]) > 10:
            console.print(f"[italic]...and {len(viz_data['nodes']) - 10} more nodes[/italic]")
        
        # Display sample of edges
        console.print("\n[bold yellow]Sample Edges:[/bold yellow]")
        table = Table(show_header=True)
        table.add_column("Source", style="green")
        table.add_column("Target", style="blue")
        
        for edge in viz_data["edges"][:10]:  # Show first 10
            table.add_row(edge["source"], edge["target"])
        
        console.print(table)
        if len(viz_data["edges"]) > 10:
            console.print(f"[italic]...and {len(viz_data['edges']) - 10} more edges[/italic]")
    
    elif viz_type in [VisualizationType.SYMBOL_TREE, VisualizationType.INHERITANCE_HIERARCHY]:
        # Display tree data
        def add_to_tree(node: Dict[str, Any], tree: Tree) -> None:
            if "children" in node:
                for child in node["children"]:
                    child_name = child["name"]
                    child_type = child.get("type", "unknown")
                    
                    if child_type == "class":
                        branch = tree.add(f"[bold magenta]{child_name}[/bold magenta]")
                        if "methods" in child:
                            branch.add(f"[cyan]Methods: {child['methods']}[/cyan]")
                        if "filepath" in child:
                            branch.add(f"[blue]Path: {child['filepath']}[/blue]")
                    elif child_type == "function" or child_type == "method":
                        branch = tree.add(f"[bold green]{child_name}[/bold green]")
                        if "parameters" in child:
                            branch.add(f"[cyan]Parameters: {child['parameters']}[/cyan]")
                    elif child_type == "category":
                        branch = tree.add(f"[bold yellow]{child_name}[/bold yellow]")
                    else:
                        branch = tree.add(f"[bold]{child_name}[/bold]")
                    
                    add_to_tree(child, branch)
        
        tree = Tree(f"[bold red]{viz_data['name']}[/bold red]")
        add_to_tree(viz_data, tree)
        console.print(tree)

def main():
    parser = argparse.ArgumentParser(description="Codebase Analysis API Client")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a repository")
    analyze_parser.add_argument("repo_url", help="Repository URL (e.g., github.com/username/repo)")
    analyze_parser.add_argument("--language", choices=[e.value for e in LanguageType], default="auto", help="Programming language")
    analyze_parser.add_argument("--output", help="Output file for JSON results")
    
    # Visualize command
    visualize_parser = subparsers.add_parser("visualize", help="Generate visualization for a repository")
    visualize_parser.add_argument("repo_url", help="Repository URL (e.g., github.com/username/repo)")
    visualize_parser.add_argument("viz_type", choices=[e.value for e in VisualizationType], help="Visualization type")
    visualize_parser.add_argument("--target", help="Target symbol for visualization (e.g., function name or Class.method)")
    visualize_parser.add_argument("--language", choices=[e.value for e in LanguageType], default="auto", help="Programming language")
    visualize_parser.add_argument("--output", help="Output file for JSON results")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "analyze":
        # Analyze repository
        results = analyze_repo(args.repo_url, args.language)
        
        # Save results to file if requested
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            console.print(f"[green]Results saved to {args.output}[/green]")
        
        # Display results
        console.print(Panel(f"[bold]Analysis Results for {args.repo_url}[/bold]", style="cyan"))
        console.print(f"Analysis completed in [bold green]{results['analysis_time']:.2f}[/bold green] seconds")
        
        display_overall_statistics(results["overall_statistics"])
        display_important_files(results["important_files"])
        display_project_structure(results["project_structure"])
        display_code_quality_issues(results["code_quality_issues"])
        display_visualization_options(results["visualization_options"])
    
    elif args.command == "visualize":
        # Generate visualization
        viz_data = visualize_repo(args.repo_url, args.viz_type, args.target, args.language)
        
        # Save results to file if requested
        if args.output:
            with open(args.output, "w") as f:
                json.dump(viz_data, f, indent=2)
            console.print(f"[green]Visualization data saved to {args.output}[/green]")
        
        # Display visualization
        console.print(Panel(f"[bold]Visualization for {args.repo_url}[/bold]", style="cyan"))
        display_visualization(viz_data, args.viz_type)

if __name__ == "__main__":
    main()

