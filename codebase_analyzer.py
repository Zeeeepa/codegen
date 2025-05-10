#!/usr/bin/env python3
"""Comprehensive Codebase Analyzer

This module provides a complete static code analysis system using the Codegen SDK.
It analyzes a codebase and provides extensive information about its structure,
dependencies, code quality, and more.
"""

import argparse
import datetime
import json
import logging
import math
import os
import re
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple, Union

import networkx as nx
import plotly.graph_objects as go
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

try:
    from codegen.configs.models.codebase import CodebaseConfig
    from codegen.configs.models.secrets import SecretsConfig
    from codegen.sdk.core.codebase import Codebase
    from codegen.sdk.core.placeholder.placeholder import Placeholder
    from codegen.sdk.core.placeholder.placeholder_type import TypePlaceholder
    from codegen.sdk.codebase.codebase_analysis import (
        get_codebase_summary, 
        analyze_codebase_quality,
        analyze_code_complexity,
        analyze_type_coverage,
        analyze_dependency_structure,
        analyze_code_duplication,
        analyze_naming_conventions,
        analyze_documentation_quality,
        analyze_error_handling,
        analyze_performance_issues,
        analyze_security_vulnerabilities,
        analyze_test_coverage
    )
    from codegen.sdk.codebase.codebase_context import (
        DiffLite, 
        CodebaseContext,
        SymbolContext,
        FileContext,
        ImportContext,
        DependencyContext,
        CallGraphContext,
        TypeContext
    )
    from codegen.sdk.codebase.dependency_trace import (
        trace_dependencies,
        visualize_dependency_trace,
        calculate_blast_radius,
        find_import_cycles
    )
    from codegen.sdk.codebase.method_relationships import (
        analyze_method_relationships,
        visualize_method_relationships,
        find_related_methods,
        analyze_method_coupling
    )
    from codegen.sdk.codebase.call_trace import (
        trace_function_calls,
        visualize_call_trace,
        analyze_call_hierarchy,
        find_entry_points
    )
    from codegen.shared.enums.programming_language import ProgrammingLanguage
except ImportError:
    print("Codegen SDK not found. Please install it first.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

# Constants
METRICS_CATEGORIES = {
    "codebase_structure": [
        "get_file_count",
        "get_files_by_language",
        "get_file_size_distribution",
        "get_directory_structure",
        "get_symbol_count",
        "get_symbol_type_distribution",
        "get_symbol_hierarchy",
        "get_top_level_vs_nested_symbols",
        "get_import_dependency_map",
        "get_external_vs_internal_dependencies",
        "get_circular_imports",
        "get_unused_imports",
        "get_module_coupling_metrics",
        "get_module_cohesion_analysis",
        "get_package_structure",
METRICS_CATEGORIES = {
    "codebase_structure": [
        "get_file_count",
        "get_files_by_language",
        "get_file_size_distribution",
        "get_directory_structure",
        "get_symbol_count",
        "get_symbol_type_distribution",
        "get_symbol_hierarchy",
        "get_top_level_vs_nested_symbols",
        "get_import_dependency_map",
        "get_external_vs_internal_dependencies",
        "get_circular_imports",
        "get_unused_imports",
        "get_module_coupling_metrics",
        "get_module_cohesion_analysis",
        "get_package_structure",
        "get_module_dependency_graph",
    ],
    "symbol_level": [
        "get_function_parameter_analysis",
        "get_return_type_analysis",
        "get_function_complexity_metrics",
        "get_call_site_tracking",
        "get_async_function_detection",
        "get_function_overload_analysis",
        "get_inheritance_hierarchy",
        "get_method_analysis",
        "get_attribute_analysis",
        "get_constructor_analysis",
        "get_interface_implementation_verification",
        "get_access_modifier_usage",
        "get_type_inference",
        "get_usage_tracking",
        "get_scope_analysis",
        "get_constant_vs_mutable_usage",
        "get_global_variable_detection",
        "get_type_alias_resolution",
        "get_generic_type_usage",
        "get_type_consistency_checking",
        "get_union_intersection_type_analysis",
        "get_symbol_import_analysis",  # Added new function
    ],
    "dependency_flow": [
        "get_function_call_relationships",
        "get_call_hierarchy_visualization",
        "get_entry_point_analysis",
        "get_dead_code_detection",
        "get_variable_usage_tracking",
        "get_data_transformation_paths",
        "get_input_output_parameter_analysis",
        "get_conditional_branch_analysis",
        "get_loop_structure_analysis",
        "get_exception_handling_paths",
        "get_return_statement_analysis",
        "get_symbol_reference_tracking",
        "get_usage_frequency_metrics",
        "get_cross_file_symbol_usage",
        "get_call_chain_analysis",  # Added new function
        "get_dead_code_detection_with_filtering",  # Added new function
        "get_path_finding_in_call_graphs",  # Added new function
        "get_dead_symbol_detection",  # Added new function
    ],
    # ... rest of the categories ...
}
class CodebaseAnalyzer:
    """Comprehensive codebase analyzer using Codegen SDK.

    This class provides methods to analyze a codebase and extract detailed information
    about its structure, dependencies, code quality, and more.
    """

    def __init__(self, repo_url: Optional[str] = None, repo_path: Optional[str] = None, language: Optional[str] = None):
        """Initialize the CodebaseAnalyzer.

        Args:
            repo_url: URL of the repository to analyze
            repo_path: Local path to the repository to analyze
            language: Programming language of the codebase (auto-detected if not provided)
        """
        self.repo_url = repo_url
        self.repo_path = repo_path
        self.language = language
        self.codebase = None
        self.codebase_context = None
        self.console = Console()
        self.results = {}
        self.comparison_codebase = None
        self.comparison_codebase_context = None
        self.comparison_results = {}

        # Initialize the codebase
        if repo_url:
            self._init_from_url(repo_url, language)
        elif repo_path:
            self._init_from_path(repo_path, language)
            
        # Initialize the codebase context if codebase was successfully initialized
        if self.codebase:
            self.codebase_context = CodebaseContext(self.codebase)

    def _init_from_url(self, repo_url: str, language: Optional[str] = None):
        """Initialize codebase from a repository URL."""
        try:
            # Extract owner and repo name from URL
            if repo_url.endswith(".git"):
                repo_url = repo_url[:-4]

            parts = repo_url.rstrip("/").split("/")
            repo_name = parts[-1]
            owner = parts[-2]
            repo_full_name = f"{owner}/{repo_name}"

            # Create a temporary directory for cloning
            tmp_dir = tempfile.mkdtemp(prefix="codebase_analyzer_")

            # Configure the codebase
            config = CodebaseConfig(
                debug=False,
                allow_external=True,
                py_resolve_syspath=True,
            )

            secrets = SecretsConfig()

            # Initialize the codebase
            self.console.print(f"[bold green]Initializing codebase from {repo_url}...[/bold green]")

            prog_lang = None
            if language:
                prog_lang = ProgrammingLanguage(language.upper())

            self.codebase = Codebase.from_github(repo_full_name=repo_full_name, tmp_dir=tmp_dir, language=prog_lang, config=config, secrets=secrets, full_history=True)

            self.console.print(f"[bold green]Successfully initialized codebase from {repo_url}[/bold green]")

        except Exception as e:
            self.console.print(f"[bold red]Error initializing codebase from URL: {e}[/bold red]")
            raise

    def _init_from_path(self, repo_path: str, language: Optional[str] = None):
        """Initialize codebase from a local repository path."""
        try:
            # Configure the codebase
            config = CodebaseConfig(
                debug=False,
                allow_external=True,
                py_resolve_syspath=True,
            )

            secrets = SecretsConfig()

            # Initialize the codebase
            self.console.print(f"[bold green]Initializing codebase from {repo_path}...[/bold green]")

            prog_lang = None
            if language:
                prog_lang = ProgrammingLanguage(language.upper())

            self.codebase = Codebase(repo_path=repo_path, language=prog_lang, config=config, secrets=secrets)

            self.console.print(f"[bold green]Successfully initialized codebase from {repo_path}[/bold green]")

        except Exception as e:
            self.console.print(f"[bold red]Error initializing codebase from path: {e}[/bold red]")
            raise

    def analyze(self, categories: Optional[list[str]] = None, output_format: str = "json", output_file: Optional[str] = None):
        """Perform a comprehensive analysis of the codebase.

        Args:
            categories: List of categories to analyze. If None, all categories are analyzed.
            output_format: Format of the output (json, html, console)
            output_file: Path to the output file

        Returns:
            Dict containing the analysis results
        """
        if not self.codebase:
            msg = "Codebase not initialized. Please initialize the codebase first."
            raise ValueError(msg)

        # If no categories specified, analyze all
        if not categories:
            categories = list(METRICS_CATEGORIES.keys())

        # Initialize results dictionary
        self.results = {
            "metadata": {
                "repo_name": self.codebase.ctx.repo_name,
                "analysis_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "language": str(self.codebase.ctx.programming_language),
            },
            "categories": {},
        }

        # Analyze each category
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[bold green]{task.completed}/{task.total}"),
            TimeElapsedColumn(),
        ) as progress:
            for category in categories:
                if category not in METRICS_CATEGORIES:
                    self.console.print(f"[bold yellow]Warning: Category '{category}' not found. Skipping.[/bold yellow]")
                    continue

                self.results["categories"][category] = {}
                metrics = METRICS_CATEGORIES[category]

                task = progress.add_task(f"Analyzing {category}...", total=len(metrics))

                for metric in metrics:
                    try:
                        method = getattr(self, metric, None)
                        if method and callable(method):
                            self.results["categories"][category][metric] = method()
                        else:
                            self.console.print(f"[bold yellow]Warning: Method '{metric}' not implemented. Skipping.[/bold yellow]")
                    except Exception as e:
                        self.console.print(f"[bold red]Error analyzing {metric}: {e}[/bold red]")
                        self.results["categories"][category][metric] = {"error": str(e)}

                    progress.update(task, advance=1)

        # Output the results
        if output_format == "json" and output_file:
            with open(output_file, "w") as f:
                json.dump(self.results, f, indent=2)
        elif output_format == "html":
            self._generate_html_report(output_file)
        elif output_format == "console":
            self._print_console_report()

        return self.results

    def init_comparison_codebase(self, commit_sha: str) -> None:
        """Initialize a comparison codebase from a specific commit.

        Args:
            commit_sha: The SHA of the commit to compare with
        """
        if not hasattr(self.codebase, "github") or not self.codebase.github:
            self.console.print("[bold red]GitHub client not available. Make sure the codebase was initialized from a GitHub repository.[/bold red]")
            return

        try:
            # Create a temporary directory for the comparison codebase
            tmp_dir = tempfile.mkdtemp(prefix="codebase_analyzer_comparison_")

            # Configure the codebase
            config = CodebaseConfig(
                debug=False,
                allow_external=True,
                py_resolve_syspath=True,
            )

            secrets = SecretsConfig()

            # Get the repository information
            repo_full_name = self.codebase.github.repo.full_name

            # Initialize the comparison codebase
            self.console.print(f"[bold green]Initializing comparison codebase from commit {commit_sha}...[/bold green]")

            self.comparison_codebase = Codebase.from_github(
                repo_full_name=repo_full_name,
                tmp_dir=tmp_dir,
                language=self.codebase.language,
                config=config,
                secrets=secrets,
                commit_sha=commit_sha,
            )
            
            # Initialize the comparison codebase context
            self.comparison_codebase_context = CodebaseContext(self.comparison_codebase)

            self.console.print(f"[bold green]Successfully initialized comparison codebase from commit {commit_sha}[/bold green]")

        except Exception as e:
            self.console.print(f"[bold red]Error initializing comparison codebase: {e}[/bold red]")
            raise

    def compare_codebases(self) -> dict[str, Any]:
        """Compare the primary codebase with the comparison codebase.

        Returns:
            Dict containing the comparison results
        """
        if not self.codebase or not self.comparison_codebase:
            msg = "Both primary and comparison codebases must be initialized."
            raise ValueError(msg)

        comparison_results = {
            "metadata": {
                "primary_repo": self.codebase.ctx.repo_name,
                "comparison_repo": self.comparison_codebase.ctx.repo_name,
                "comparison_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
            "file_changes": {
                "added": [],
                "modified": [],
                "deleted": [],
            },
            "symbol_changes": {
                "added": [],
                "modified": [],
                "deleted": [],
            },
            "quality_metrics": {
                "primary": {},
                "comparison": {},
                "diff": {},
            },
        }

        # Compare files
        primary_files = {file.file_path: file for file in self.codebase.files}
        comparison_files = {file.file_path: file for file in self.comparison_codebase.files}

        # Find added, modified, and deleted files
        for path, file in primary_files.items():
            if path not in comparison_files:
                comparison_results["file_changes"]["added"].append(path)
            else:
                # Check if file content has changed
                if file.source != comparison_files[path].source:
                    comparison_results["file_changes"]["modified"].append(path)

        for path in comparison_files:
            if path not in primary_files:
                comparison_results["file_changes"]["deleted"].append(path)

        # Compare quality metrics
        # Run quality metrics on both codebases
        primary_metrics = {
            "untyped_returns": self.count_untyped_return_statements(),
            "untyped_parameters": self.count_untyped_parameters(),
            "untyped_attributes": self.count_untyped_attributes(),
            "unnamed_kwargs": self.count_unnamed_keyword_arguments(),
            "import_cycles": self.detect_import_cycles(),
        }

        # Store the current codebase
        temp_codebase = self.codebase
        
        # Switch to comparison codebase for analysis
        self.codebase = self.comparison_codebase
        
        comparison_metrics = {
            "untyped_returns": self.count_untyped_return_statements(),
            "untyped_parameters": self.count_untyped_parameters(),
            "untyped_attributes": self.count_untyped_attributes(),
            "unnamed_kwargs": self.count_unnamed_keyword_arguments(),
            "import_cycles": self.detect_import_cycles(),
        }
        
        # Switch back to the primary codebase
        self.codebase = temp_codebase

        # Calculate differences
        diff_metrics = {}
        for metric in primary_metrics:
            if isinstance(primary_metrics[metric], dict) and "count" in primary_metrics[metric]:
                diff_metrics[metric] = {
                    "count_diff": primary_metrics[metric]["count"] - comparison_metrics[metric]["count"],
                    "percentage_change": (
                        ((primary_metrics[metric]["count"] - comparison_metrics[metric]["count"]) / max(1, comparison_metrics[metric]["count"])) * 100
                    ),
                }
            elif isinstance(primary_metrics[metric], int):
                diff_metrics[metric] = {
                    "count_diff": primary_metrics[metric] - comparison_metrics[metric],
                    "percentage_change": (
                        ((primary_metrics[metric] - comparison_metrics[metric]) / max(1, comparison_metrics[metric])) * 100
                    ),
                }

        comparison_results["quality_metrics"]["primary"] = primary_metrics
        comparison_results["quality_metrics"]["comparison"] = comparison_metrics
        comparison_results["quality_metrics"]["diff"] = diff_metrics

        self.comparison_results = comparison_results
        return comparison_results

    def count_untyped_return_statements(self) -> Dict[str, Any]:
        """Count untyped return statements in the codebase.

        Returns:
            Dict containing the count of untyped return statements by file
        """
        if not self.codebase or not self.codebase_context:
            return {"error": "Codebase or codebase context not initialized"}
            
        try:
            # Get all Python files
            python_files = [f for f in self.codebase.get_all_files() if f.endswith(".py")]
            
            results = {}
            for file_path in python_files:
                try:
                    file_content = self.codebase.get_file_content(file_path)
                    
                    # Use regex to find function definitions with return statements but no return type
                    # This is a simplified approach and might not catch all cases
                    pattern = r"def\s+(\w+)\s*\([^)]*\)\s*(?!->):"
                    matches = re.findall(pattern, file_content)
                    
                    if matches:
                        results[file_path] = len(matches)
                except Exception as e:
                    logger.warning(f"Error processing file {file_path}: {e}")
            
            return {
                "total_count": sum(results.values()),
                "files": results
            }
        except Exception as e:
            return {"error": str(e)}
            
    def count_untyped_parameters(self) -> Dict[str, Any]:
        """Count untyped parameters in function definitions.

        Returns:
            Dict containing the count of untyped parameters by file
        """
        if not self.codebase or not self.codebase_context:
            return {"error": "Codebase or codebase context not initialized"}
            
        try:
            # Get all Python files
            python_files = [f for f in self.codebase.get_all_files() if f.endswith(".py")]
            
            results = {}
            for file_path in python_files:
                try:
                    file_content = self.codebase.get_file_content(file_path)
                    
                    # Use regex to find function parameters without type annotations
                    # This is a simplified approach and might not catch all cases
                    pattern = r"def\s+\w+\s*\((.*?)\)"
                    param_blocks = re.findall(pattern, file_content, re.DOTALL)
                    
                    untyped_params_count = 0
                    for param_block in param_blocks:
                        params = [p.strip() for p in param_block.split(",") if p.strip()]
                        for param in params:
                            # Check if parameter has no type annotation
                            if param and ":" not in param and param != "self" and param != "cls":
                                untyped_params_count += 1
                    
                    if untyped_params_count > 0:
                        results[file_path] = untyped_params_count
                except Exception as e:
                    logger.warning(f"Error processing file {file_path}: {e}")
            
            return {
                "total_count": sum(results.values()),
                "files": results
            }
        except Exception as e:
            return {"error": str(e)}
            
    def count_untyped_attributes(self) -> Dict[str, Any]:
        """Count untyped class attributes in the codebase.

        Returns:
            Dict containing the count of untyped class attributes by file
        """
        if not self.codebase or not self.codebase_context:
            return {"error": "Codebase or codebase context not initialized"}
            
        try:
            # Get all Python files
            python_files = [f for f in self.codebase.get_all_files() if f.endswith(".py")]
            
            results = {}
            for file_path in python_files:
                try:
                    file_content = self.codebase.get_file_content(file_path)
                    
                    # Use regex to find class attribute definitions without type annotations
                    # This is a simplified approach and might not catch all cases
                    pattern = r"class\s+\w+.*?:\s*(.*?)(?=\n\S|\Z)"
                    class_bodies = re.findall(pattern, file_content, re.DOTALL)
                    
                    untyped_attrs_count = 0
                    for body in class_bodies:
                        # Find attribute assignments in class body
                        attr_pattern = r"^\s+self\.(\w+)\s*="
                        attrs = re.findall(attr_pattern, body, re.MULTILINE)
                        untyped_attrs_count += len(attrs)
                    
                    if untyped_attrs_count > 0:
                        results[file_path] = untyped_attrs_count
                except Exception as e:
                    logger.warning(f"Error processing file {file_path}: {e}")
            
            return {
                "total_count": sum(results.values()),
                "files": results
            }
        except Exception as e:
            return {"error": str(e)}
            
    def count_unnamed_keyword_arguments(self) -> Dict[str, Any]:
        """Count unnamed keyword arguments in function calls.

        Returns:
            Dict containing the count of unnamed keyword arguments by file
        """
        if not self.codebase or not self.codebase_context:
            return {"error": "Codebase or codebase context not initialized"}
            
        try:
            # Get all Python files
            python_files = [f for f in self.codebase.get_all_files() if f.endswith(".py")]
            
            results = {}
            for file_path in python_files:
                try:
                    file_content = self.codebase.get_file_content(file_path)
                    
                    # Use regex to find function calls with unnamed keyword arguments (**kwargs)
                    # This is a simplified approach and might not catch all cases
                    pattern = r"\w+\s*\(.*?\*\*\w+.*?\)"
                    matches = re.findall(pattern, file_content)
                    
                    if matches:
                        results[file_path] = len(matches)
                except Exception as e:
                    logger.warning(f"Error processing file {file_path}: {e}")
            
            return {
                "total_count": sum(results.values()),
                "files": results
            }
        except Exception as e:
            return {"error": str(e)}
            
    def detect_import_cycles(self) -> Dict[str, Any]:
        """Detect import cycles in the codebase.

        Returns:
            Dict containing the detected import cycles
        """
        if not self.codebase or not self.codebase_context:
            return {"error": "Codebase or codebase context not initialized"}
            
        try:
            # Create a directed graph
            G = nx.DiGraph()
            
            # Get all Python files
            python_files = [f for f in self.codebase.get_all_files() if f.endswith(".py")]
            
            # Process each file to extract imports
            for file_path in python_files:
                try:
                    file_content = self.codebase.get_file_content(file_path)
                    
                    # Add the file as a node
                    module_name = file_path.replace("/", ".").replace(".py", "")
                    G.add_node(module_name, file=file_path)
                    
                    # Extract imports
                    import_pattern = r"(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))"
                    imports = re.findall(import_pattern, file_content)
                    
                    for imp in imports:
                        imported_module = imp[0] if imp[0] else imp[1]
                        
                        # Check if the imported module is part of the codebase
                        for other_file in python_files:
                            other_module = other_file.replace("/", ".").replace(".py", "")
                            
                            if imported_module == other_module or other_module.endswith("." + imported_module):
                                G.add_edge(module_name, other_module)
                                break
                except Exception as e:
                    logger.warning(f"Error processing file {file_path}: {e}")
            
            # Find cycles
            cycles = list(nx.simple_cycles(G))
            
            # Convert cycles to a more readable format
            formatted_cycles = []
            for cycle in cycles:
                cycle_info = {
                    "modules": cycle,
                    "files": [G.nodes[module]["file"] for module in cycle],
                }
                formatted_cycles.append(cycle_info)
            
            return {
                "cycles": formatted_cycles,
                "count": len(formatted_cycles),
            }
        except Exception as e:
            return {"error": str(e)}
            
    def visualize_import_cycles(self) -> Dict[str, Any]:
        """Visualize import cycles in the codebase.

        Returns:
            Dict containing the visualization data
        """
        if not self.codebase or not self.codebase_context:
            return {"error": "Codebase or codebase context not initialized"}
            
        try:
            # Get import cycles
            cycles_data = self.detect_import_cycles()
            
            if "error" in cycles_data:
                return cycles_data
                
            cycles = cycles_data["cycles"]
            
            if not cycles:
                return {"message": "No import cycles detected"}
            
            # Create a directed graph
            G = nx.DiGraph()
            
            # Add nodes and edges from cycles
            for cycle in cycles:
                for module in cycle["modules"]:
                    G.add_node(module, file=cycle["files"][cycle["modules"].index(module)])
                
                for i in range(len(cycle["modules"])):
                    G.add_edge(cycle["modules"][i], cycle["modules"][(i + 1) % len(cycle["modules"])])
            
            # Convert the graph to a format suitable for visualization
            nodes = [{"id": node, "label": node.split(".")[-1], "file": G.nodes[node]["file"]} for node in G.nodes]
            edges = [{"source": u, "target": v} for u, v in G.edges]
            
            # Create a Plotly figure
            fig = go.Figure()
            
            # Add nodes
            for node in nodes:
                fig.add_trace(go.Scatter(
                    x=[0],
                    y=[0],
                    mode="markers+text",
                    marker=dict(size=20, color="red"),
                    text=node["label"],
                    name=node["label"],
                    hoverinfo="text",
                    hovertext=f"Module: {node['id']}<br>File: {node['file']}",
                ))
            
            # Add edges
            for edge in edges:
                fig.add_trace(go.Scatter(
                    x=[0, 1],
                    y=[0, 1],
                    mode="lines",
                    line=dict(width=1, color="gray"),
                    hoverinfo="none",
                    showlegend=False,
                ))
            
            # Update layout
            fig.update_layout(
                title="Import Cycles",
                showlegend=True,
                hovermode="closest",
                margin=dict(b=20, l=5, r=5, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            )
            
            # Convert the figure to JSON
            fig_json = fig.to_json()
            
            return {
                "cycles": cycles,
                "graph": {
                    "nodes": nodes,
                    "edges": edges,
                },
                "plotly_figure": json.loads(fig_json),
            }
        except Exception as e:
            return {"error": str(e)}
            
    def visualize_call_graph(self, function_name: Optional[str] = None) -> Dict[str, Any]:
        """Visualize the call graph of a function or the entire codebase.

        Args:
            function_name: Name of the function to visualize. If None, visualizes the entire codebase.

        Returns:
            Dict containing the visualization data
        """
        if not self.codebase or not self.codebase_context:
            return {"error": "Codebase or codebase context not initialized"}
            
        try:
            # Create a directed graph
            G = nx.DiGraph()
            
            # Get all Python files
            python_files = [f for f in self.codebase.get_all_files() if f.endswith(".py")]
            
            # Map of function names to their file paths
            function_map = {}
            
            # Map of function calls
            call_map = {}
            
            # Process each file to extract function definitions and calls
            for file_path in python_files:
                try:
                    file_content = self.codebase.get_file_content(file_path)
                    
                    # Extract function definitions
                    def_pattern = r"def\s+(\w+)\s*\("
                    function_defs = re.findall(def_pattern, file_content)
                    
                    for func in function_defs:
                        function_map[func] = file_path
                        G.add_node(func, file=file_path)
                    
                    # Extract function calls
                    for func in function_defs:
                        # Get the function body
                        func_pattern = r"def\s+" + func + r"\s*\(.*?\).*?:(.*?)(?=\n\S|\Z)"
                        func_bodies = re.findall(func_pattern, file_content, re.DOTALL)
                        
                        if func_bodies:
                            func_body = func_bodies[0]
                            # Find function calls in the body
                            call_pattern = r"(\w+)\s*\("
                            calls = re.findall(call_pattern, func_body)
                            
                            for call in calls:
                                if call in function_map and call != func:  # Avoid self-calls
                                    G.add_edge(func, call)
                                    if func not in call_map:
                                        call_map[func] = []
                                    call_map[func].append(call)
                except Exception as e:
                    logger.warning(f"Error processing file {file_path}: {e}")
            
            # Filter the graph if a specific function is provided
            if function_name:
                if function_name not in function_map:
                    return {"error": f"Function '{function_name}' not found in the codebase"}
                
                # Create a subgraph with the function and its neighbors
                nodes_to_keep = [function_name]
                nodes_to_keep.extend(list(G.successors(function_name)))
                nodes_to_keep.extend(list(G.predecessors(function_name)))
                
                G = G.subgraph(nodes_to_keep)
            
            # Convert the graph to a format suitable for visualization
            nodes = [{"id": node, "label": node, "file": G.nodes[node]["file"]} for node in G.nodes]
            edges = [{"source": u, "target": v} for u, v in G.edges]
            
            # Create a Plotly figure
            fig = go.Figure()
            
            # Add nodes
            for node in nodes:
                fig.add_trace(go.Scatter(
                    x=[0],
                    y=[0],
                    mode="markers+text",
                    marker=dict(size=20, color="blue"),
                    text=node["label"],
                    name=node["label"],
                    hoverinfo="text",
                    hovertext=f"Function: {node['label']}<br>File: {node['file']}",
                ))
            
            # Add edges
            for edge in edges:
                fig.add_trace(go.Scatter(
                    x=[0, 1],
                    y=[0, 1],
                    mode="lines",
                    line=dict(width=1, color="gray"),
                    hoverinfo="none",
                    showlegend=False,
                ))
            
            # Update layout
            fig.update_layout(
                title=f"Call Graph for {'the entire codebase' if not function_name else function_name}",
                showlegend=True,
                hovermode="closest",
                margin=dict(b=20, l=5, r=5, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            )
            
            # Convert the figure to JSON
            fig_json = fig.to_json()
            
            return {
                "graph": {
                    "nodes": nodes,
                    "edges": edges,
                },
                "plotly_figure": json.loads(fig_json),
            }
        except Exception as e:
            return {"error": str(e)}
            
    def visualize_dependency_map(self) -> Dict[str, Any]:
        """Visualize the dependency map of the codebase.

        Returns:
            Dict containing the visualization data
        """
        if not self.codebase or not self.codebase_context:
            return {"error": "Codebase or codebase context not initialized"}
            
        try:
            # Create a directed graph
            G = nx.DiGraph()
            
            # Get all Python files
            python_files = [f for f in self.codebase.get_all_files() if f.endswith(".py")]
            
            # Process each file to extract imports
            for file_path in python_files:
                try:
                    file_content = self.codebase.get_file_content(file_path)
                    
                    # Add the file as a node
                    module_name = file_path.replace("/", ".").replace(".py", "")
                    G.add_node(module_name, file=file_path)
                    
                    # Extract imports
                    import_pattern = r"(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))"
                    imports = re.findall(import_pattern, file_content)
                    
                    for imp in imports:
                        imported_module = imp[0] if imp[0] else imp[1]
                        
                        # Check if the imported module is part of the codebase
                        for other_file in python_files:
                            other_module = other_file.replace("/", ".").replace(".py", "")
                            
                            if imported_module == other_module or other_module.endswith("." + imported_module):
                                G.add_edge(module_name, other_module)
                                break
                except Exception as e:
                    logger.warning(f"Error processing file {file_path}: {e}")
            
            # Convert the graph to a format suitable for visualization
            nodes = [{"id": node, "label": node.split(".")[-1], "file": G.nodes[node]["file"]} for node in G.nodes]
            edges = [{"source": u, "target": v} for u, v in G.edges]
            
            # Create a Plotly figure
            fig = go.Figure()
            
            # Add nodes
            for node in nodes:
                fig.add_trace(go.Scatter(
                    x=[0],
                    y=[0],
                    mode="markers+text",
                    marker=dict(size=20, color="green"),
                    text=node["label"],
                    name=node["label"],
                    hoverinfo="text",
                    hovertext=f"Module: {node['id']}<br>File: {node['file']}",
                ))
            
            # Add edges
            for edge in edges:
                fig.add_trace(go.Scatter(
                    x=[0, 1],
                    y=[0, 1],
                    mode="lines",
                    line=dict(width=1, color="gray"),
                    hoverinfo="none",
                    showlegend=False,
                ))
            
            # Update layout
            fig.update_layout(
                title="Dependency Map",
                showlegend=True,
                hovermode="closest",
                margin=dict(b=20, l=5, r=5, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            )
            
            # Convert the figure to JSON
            fig_json = fig.to_json()
            
            return {
                "graph": {
                    "nodes": nodes,
                    "edges": edges,
                },
                "plotly_figure": json.loads(fig_json),
            }
        except Exception as e:
            return {"error": str(e)}
            
    def visualize_directory_tree(self) -> Dict[str, Any]:
        """Visualize the directory tree of the codebase.

        Returns:
            Dict containing the visualization data
        """
        if not self.codebase:
            return {"error": "Codebase not initialized"}
            
        try:
            # Get all files
            all_files = self.codebase.get_all_files()
            
            # Create a tree structure
            tree = {}
            
            for file_path in all_files:
                parts = file_path.split("/")
                current = tree
                
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:  # Leaf node (file)
                        if "files" not in current:
                            current["files"] = []
                        current["files"].append(part)
                    else:  # Directory
                        if "dirs" not in current:
                            current["dirs"] = {}
                        if part not in current["dirs"]:
                            current["dirs"][part] = {}
                        current = current["dirs"][part]
            
            # Convert the tree to a format suitable for visualization
            def build_tree_data(node, name="root", path=""):
                result = {"name": name, "path": path}
                
                if "dirs" in node:
                    result["children"] = []
                    for dir_name, dir_node in node["dirs"].items():
                        dir_path = f"{path}/{dir_name}" if path else dir_name
                        result["children"].append(build_tree_data(dir_node, dir_name, dir_path))
                
                if "files" in node:
                    if "children" not in result:
                        result["children"] = []
                    for file_name in node["files"]:
                        file_path = f"{path}/{file_name}" if path else file_name
                        result["children"].append({"name": file_name, "path": file_path, "type": "file"})
                
                return result
            
            tree_data = build_tree_data(tree)
            
            return {
                "tree": tree_data,
            }
        except Exception as e:
            return {"error": str(e)}
            
    def get_pr_diff_analysis(self, pr_number: int) -> Dict[str, Any]:
        """Analyze the diff of a pull request.

        Args:
            pr_number: The number of the pull request to analyze

        Returns:
            Dict containing the analysis of the PR diff
        """
        if not hasattr(self.codebase, "github") or not self.codebase.github:
            return {"error": "GitHub client not available. Make sure the codebase was initialized from a GitHub repository."}
        
        try:
            # Get the PR
            pr = self.codebase.github.repo.get_pull(pr_number)
            
            # Get the diff
            diff = pr.get_files()
            
            # Analyze the diff
            diff_analysis = {
                "pr_number": pr_number,
                "title": pr.title,
                "state": pr.state,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "files_changed": [],
                "total_additions": pr.additions,
                "total_deletions": pr.deletions,
                "total_changes": pr.additions + pr.deletions,
            }
            
            # Analyze each file
            for file in diff:
                file_analysis = {
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.additions + file.deletions,
                }
                
                diff_analysis["files_changed"].append(file_analysis)
            
            return diff_analysis
            
        except Exception as e:
            return {"error": str(e)}

    def get_pr_quality_metrics(self, pr_number: int) -> Dict[str, Any]:
        """Get quality metrics for a pull request.

        Args:
            pr_number: The number of the pull request to analyze

        Returns:
            Dict containing the quality metrics of the PR
        """
        if not hasattr(self.codebase, "github") or not self.codebase.github:
            return {"error": "GitHub client not available. Make sure the codebase was initialized from a GitHub repository."}
        
        try:
            # Get the PR
            pr = self.codebase.github.repo.get_pull(pr_number)
            
            # Get the base and head commits
            base_commit = pr.base.sha
            head_commit = pr.head.sha
            
            # Initialize comparison codebase with the base commit
            self.init_comparison_codebase(base_commit)
            
            # Compare the head commit (current codebase) with the base commit (comparison codebase)
            comparison = self.compare_codebases()
            
            # Add PR metadata
            comparison["pr_metadata"] = {
                "pr_number": pr_number,
                "title": pr.title,
                "state": pr.state,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "base_commit": base_commit,
                "head_commit": head_commit,
            }
            
            return comparison
            
        except Exception as e:
            return {"error": str(e)}
            
    def get_codebase_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of the codebase.
        
        Returns:
    def get_call_chain_analysis(self) -> Dict[str, Any]:
        """
        Analyze call chains between functions.
        
        This function traces and analyzes function call chains in the codebase,
        identifying the longest chains, most called functions, and complex call patterns.
        
        Returns:
            Dict containing call chain analysis results
        """
        if not self.codebase:
            return {"error": "Codebase not initialized"}
            
        return get_call_chain_analysis(self.codebase)
        
    def get_dead_code_detection_with_filtering(self, exclude_patterns: List[str] = None) -> Dict[str, Any]:
        """
        Detect dead code in the codebase with filtering options.
        
        This function identifies functions, classes, and methods that are defined but never used
        in the codebase, with the ability to exclude certain patterns from analysis.
        
        Args:
            exclude_patterns: List of regex patterns to exclude from dead code detection
            
        Returns:
            Dict containing dead code analysis results with filtering
        """
        if not self.codebase:
            return {"error": "Codebase not initialized"}
            
        return get_dead_code_detection_with_filtering(self.codebase, exclude_patterns)
        
    def get_path_finding_in_call_graphs(self, source_function: str = None, target_function: str = None, max_depth: int = 10) -> Dict[str, Any]:
        """
        Find paths between functions in the call graph.
        
        This function identifies all possible paths between a source function and a target function
        in the call graph, with options to limit the search depth.
        
        Args:
            source_function: Name of the source function (if None, all entry points are considered)
            target_function: Name of the target function (if None, all functions are considered)
            max_depth: Maximum depth of the search
            
        Returns:
            Dict containing path finding results
        """
        if not self.codebase:
            return {"error": "Codebase not initialized"}
            
        return get_path_finding_in_call_graphs(self.codebase, source_function, target_function, max_depth)
        
    def get_dead_symbol_detection(self) -> Dict[str, Any]:
        """
        Detect dead symbols in the codebase.
        
        This function identifies symbols (functions, classes, variables) that are defined
        but never used in the codebase.
        
        Returns:
            Dict containing dead symbol analysis results
        """
        if not self.codebase:
            return {"error": "Codebase not initialized"}
            
        return get_dead_symbol_detection(self.codebase)
        
    def get_symbol_import_analysis(self) -> Dict[str, Any]:
        """
        Analyze symbol imports in the codebase.
        
        This function analyzes how symbols are imported and used across the codebase,
        identifying patterns, potential issues, and optimization opportunities.
        
        Returns:
            Dict containing symbol import analysis results
        """
        if not self.codebase:
            return {"error": "Codebase not initialized"}
            
        return get_symbol_import_analysis(self.codebase)
    """Main entry point for the codebase analyzer."""
    parser = argparse.ArgumentParser(description="Comprehensive Codebase Analyzer")

    # Repository source
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--repo-url", help="URL of the repository to analyze")
    source_group.add_argument("--repo-path", help="Local path to the repository to analyze")

    # Analysis options
    parser.add_argument("--language", help="Programming language of the codebase (auto-detected if not provided)")
    parser.add_argument("--categories", nargs="+", help="Categories to analyze (default: all)")

    # PR comparison options
    parser.add_argument("--compare-commit", help="Commit SHA to compare with the current codebase")
    parser.add_argument("--pr-number", type=int, help="PR number to analyze")

    # Output options
    parser.add_argument("--output-format", choices=["json", "html", "console"], default="console", help="Output format")
    parser.add_argument("--output-file", help="Path to the output file")

    # Visualization options
    parser.add_argument("--visualize", choices=["call-graph", "dependency-map", "directory-tree", "import-cycles"], help="Generate visualization")
    parser.add_argument("--function-name", help="Function name for call graph visualization")
    
    # Type analysis options
    parser.add_argument("--analyze-types", action="store_true", help="Analyze untyped code in the codebase")
    parser.add_argument("--summary", action="store_true", help="Get a summary of the codebase")

    args = parser.parse_args()

    try:
        # Initialize the analyzer
        analyzer = CodebaseAnalyzer(repo_url=args.repo_url, repo_path=args.repo_path, language=args.language)

        # Handle PR analysis
        if args.pr_number:
            pr_analysis = analyzer.get_pr_diff_analysis(args.pr_number)
            print(json.dumps(pr_analysis, indent=2))
            return

        # Handle comparison
        if args.compare_commit:
            analyzer.init_comparison_codebase(args.compare_commit)
            comparison = analyzer.compare_codebases()
            print(json.dumps(comparison, indent=2))
            return

        # Handle visualization
        if args.visualize:
            if args.visualize == "call-graph":
                visualization = analyzer.visualize_call_graph(args.function_name)
            elif args.visualize == "dependency-map":
                visualization = analyzer.visualize_dependency_map()
            elif args.visualize == "directory-tree":
                visualization = analyzer.visualize_directory_tree()
            elif args.visualize == "import-cycles":
                visualization = analyzer.visualize_import_cycles()
            
            print(json.dumps(visualization, indent=2))
            return
            
        # Handle type analysis
        if args.analyze_types:
            type_analysis = {
                "untyped_return_statements": analyzer.count_untyped_return_statements(),
                "untyped_parameters": analyzer.count_untyped_parameters(),
                "untyped_attributes": analyzer.count_untyped_attributes(),
                "unnamed_keyword_arguments": analyzer.count_unnamed_keyword_arguments(),
            }
            print(json.dumps(type_analysis, indent=2))
            return
            
        # Handle codebase summary
        if args.summary:
            summary = analyzer.get_codebase_summary()
            print(json.dumps(summary, indent=2))
            return

        # Perform the analysis
        results = analyzer.analyze(categories=args.categories, output_format=args.output_format, output_file=args.output_file)

        # Print success message
        if args.output_format == "json" and args.output_file:
            print(f"Analysis results saved to {args.output_file}")
        elif args.output_format == "html":
            print(f"HTML report saved to {args.output_file or 'codebase_analysis_report.html'}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

    def analyze_call_trace(self, function_name: str) -> Dict[str, Any]:
        """Analyze the call trace for a specific function.
        
        Args:
            function_name: Name of the function to analyze
            
        Returns:
            A dictionary containing call trace information.
        """
        try:
            if not self.codebase:
                return {"error": "Codebase not initialized"}
                
            # Use the SDK's trace_function_calls function
            calls = trace_function_calls(self.codebase, function_name)
            
            # Analyze call hierarchy
            hierarchy = analyze_call_hierarchy(self.codebase, function_name)
            
            return {
                "calls": calls,
                "hierarchy": hierarchy,
                "visualization": visualize_call_trace(self.codebase, function_name)
            }
        except Exception as e:
            return {"error": str(e)}
            
    def find_import_cycles(self) -> Dict[str, Any]:
        """Find import cycles in the codebase.
        
        Returns:
            A dictionary containing import cycle information.
        """
        try:
            if not self.codebase:
                return {"error": "Codebase not initialized"}
                
            # Use the SDK's find_import_cycles function
            cycles = find_import_cycles(self.codebase)
            
            return {
                "cycles": cycles,
                "visualization": self.visualize_import_cycles()
            }
        except Exception as e:
            return {"error": str(e)}

def main():
    """Main entry point for the codebase analyzer."""
    parser = argparse.ArgumentParser(description="Comprehensive Codebase Analyzer")

    # Repository source
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--repo-url", help="URL of the repository to analyze")
    source_group.add_argument("--repo-path", help="Local path to the repository to analyze")

    # Analysis options
    parser.add_argument("--language", help="Programming language of the codebase (auto-detected if not provided)")
    parser.add_argument("--categories", nargs="+", help="Categories to analyze (default: all)")

    # PR comparison options
    parser.add_argument("--compare-commit", help="Commit SHA to compare with the current codebase")
    parser.add_argument("--pr-number", type=int, help="PR number to analyze")

    # Output options
    parser.add_argument("--output-format", choices=["json", "html", "console"], default="console", help="Output format")
    parser.add_argument("--output-file", help="Path to the output file")

    # Visualization options
    parser.add_argument("--visualize", choices=["call-graph", "dependency-map", "directory-tree", "import-cycles"], help="Generate visualization")
    parser.add_argument("--function-name", help="Function name for call graph visualization")
    parser.add_argument("--symbol-name", help="Symbol name for dependency trace visualization")
    parser.add_argument("--class-name", help="Class name for method relationships visualization")
    
    # Type analysis options
    parser.add_argument("--analyze-types", action="store_true", help="Analyze untyped code in the codebase")
    parser.add_argument("--summary", action="store_true", help="Get a summary of the codebase")
    parser.add_argument("--quality", action="store_true", help="Analyze code quality")
    parser.add_argument("--dependency-trace", action="store_true", help="Analyze dependency trace")
    parser.add_argument("--method-relationships", action="store_true", help="Analyze method relationships")
    parser.add_argument("--call-trace", action="store_true", help="Analyze call trace")
    parser.add_argument("--import-cycles", action="store_true", help="Find import cycles")

    args = parser.parse_args()

    try:
        # Initialize the analyzer
        analyzer = CodebaseAnalyzer(repo_url=args.repo_url, repo_path=args.repo_path, language=args.language)

        # Handle PR analysis
        if args.pr_number:
            pr_analysis = analyzer.get_pr_diff_analysis(args.pr_number)
            print(json.dumps(pr_analysis, indent=2))
            return

        # Handle comparison
        if args.compare_commit:
            analyzer.init_comparison_codebase(args.compare_commit)
            comparison = analyzer.compare_codebases()
            print(json.dumps(comparison, indent=2))
            return

        # Handle visualization
        if args.visualize:
            if args.visualize == "call-graph":
                visualization = analyzer.visualize_call_graph(args.function_name)
            elif args.visualize == "dependency-map":
                visualization = analyzer.visualize_dependency_map()
            elif args.visualize == "directory-tree":
                visualization = analyzer.visualize_directory_tree()
            elif args.visualize == "import-cycles":
                visualization = analyzer.visualize_import_cycles()
            
            print(json.dumps(visualization, indent=2))
            return
            
        # Handle type analysis
        if args.analyze_types:
            type_analysis = {
                "untyped_return_statements": analyzer.count_untyped_return_statements(),
                "untyped_parameters": analyzer.count_untyped_parameters(),
                "untyped_attributes": analyzer.count_untyped_attributes(),
                "unnamed_keyword_arguments": analyzer.count_unnamed_keyword_arguments(),
            }
            print(json.dumps(type_analysis, indent=2))
            return
            
        # Handle codebase summary
        if args.summary:
            summary = analyzer.get_codebase_summary()
            print(json.dumps(summary, indent=2))
            return
            
        # Handle code quality analysis
        if args.quality:
            quality = analyzer.analyze_codebase_quality()
            print(json.dumps(quality, indent=2))
            return
            
        # Handle dependency trace analysis
        if args.dependency_trace:
            if not args.symbol_name:
                print("Error: --symbol-name is required for dependency trace analysis")
                return
            dependency_trace = analyzer.analyze_dependency_trace(args.symbol_name)
            print(json.dumps(dependency_trace, indent=2))
            return
            
        # Handle method relationships analysis
        if args.method_relationships:
            if not args.class_name:
                print("Error: --class-name is required for method relationships analysis")
                return
            method_relationships = analyzer.analyze_method_relationships(args.class_name)
            print(json.dumps(method_relationships, indent=2))
            return
            
        # Handle call trace analysis
        if args.call_trace:
            if not args.function_name:
                print("Error: --function-name is required for call trace analysis")
                return
            call_trace = analyzer.analyze_call_trace(args.function_name)
            print(json.dumps(call_trace, indent=2))
            return
            
        # Handle import cycles analysis
        if args.import_cycles:
            import_cycles = analyzer.find_import_cycles()
            print(json.dumps(import_cycles, indent=2))
            return

        # Perform the analysis
        results = analyzer.analyze(categories=args.categories, output_format=args.output_format, output_file=args.output_file)

        # Print success message
        if args.output_format == "json" and args.output_file:
            print(f"Analysis results saved to {args.output_file}")
        elif args.output_format == "html":
            print(f"HTML report saved to {args.output_file or 'codebase_analysis_report.html'}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    def analyze_method_relationships(self, class_name: str) -> Dict[str, Any]:
        """Analyze the relationships between methods in a class.
        
        Args:
            class_name: Name of the class to analyze
            
        Returns:
            A dictionary containing method relationship information.
        """
        try:
            if not self.codebase:
                return {"error": "Codebase not initialized"}
                
            # Use the SDK's analyze_method_relationships function
            relationships = analyze_method_relationships(self.codebase, class_name)
            
            # Find related methods
            related_methods = find_related_methods(self.codebase, class_name)
            
            # Analyze method coupling
            method_coupling = analyze_method_coupling(self.codebase, class_name)
            
            return {
                "relationships": relationships,
                "related_methods": related_methods,
                "method_coupling": method_coupling,
                "visualization": visualize_method_relationships(self.codebase, class_name)
            }
        except Exception as e:
            return {"error": str(e)}
def main():
    """Main entry point for the codebase analyzer."""
    parser = argparse.ArgumentParser(description="Comprehensive Codebase Analyzer")

    # Repository source
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--repo-url", help="URL of the repository to analyze")
    source_group.add_argument("--repo-path", help="Local path to the repository to analyze")

    # Analysis options
    parser.add_argument("--language", help="Programming language of the codebase (auto-detected if not provided)")
    parser.add_argument("--categories", nargs="+", help="Categories to analyze (default: all)")

    # PR comparison options
    parser.add_argument("--compare-commit", help="Commit SHA to compare with the current codebase")
    parser.add_argument("--pr-number", type=int, help="PR number to analyze")

    # Output options
    parser.add_argument("--output-format", choices=["json", "html", "console"], default="console", help="Output format")
    parser.add_argument("--output-file", help="Path to the output file")

    # Visualization options
    parser.add_argument("--visualize", choices=["call-graph", "dependency-map", "directory-tree", "import-cycles"], help="Generate visualization")
    parser.add_argument("--function-name", help="Function name for call graph visualization")
    parser.add_argument("--symbol-name", help="Symbol name for dependency trace visualization")
    parser.add_argument("--class-name", help="Class name for method relationships visualization")
    
    # Type analysis options
    parser.add_argument("--analyze-types", action="store_true", help="Analyze untyped code in the codebase")
    parser.add_argument("--summary", action="store_true", help="Get a summary of the codebase")
    parser.add_argument("--quality", action="store_true", help="Analyze code quality")
    parser.add_argument("--dependency-trace", action="store_true", help="Analyze dependency trace")
    parser.add_argument("--method-relationships", action="store_true", help="Analyze method relationships")
    parser.add_argument("--call-trace", action="store_true", help="Analyze call trace")
    parser.add_argument("--import-cycles", action="store_true", help="Find import cycles")
    
    # New analysis options
    parser.add_argument("--call-chain", action="store_true", help="Analyze call chains between functions")
    parser.add_argument("--dead-code", action="store_true", help="Detect dead code with filtering")
    parser.add_argument("--exclude-patterns", nargs="+", help="Patterns to exclude from dead code detection")
    parser.add_argument("--path-finding", action="store_true", help="Find paths between functions in call graphs")
    parser.add_argument("--source-function", help="Source function for path finding")
    parser.add_argument("--target-function", help="Target function for path finding")
    parser.add_argument("--max-depth", type=int, default=10, help="Maximum depth for path finding")
    parser.add_argument("--dead-symbols", action="store_true", help="Detect dead symbols in the codebase")
    parser.add_argument("--import-analysis", action="store_true", help="Analyze symbol imports in the codebase")

    args = parser.parse_args()

    try:
        # Initialize the analyzer
        analyzer = CodebaseAnalyzer(repo_url=args.repo_url, repo_path=args.repo_path, language=args.language)

        # Handle PR analysis
        if args.pr_number:
            pr_analysis = analyzer.get_pr_diff_analysis(args.pr_number)
            print(json.dumps(pr_analysis, indent=2))
            return

        # Handle comparison
        if args.compare_commit:
            analyzer.init_comparison_codebase(args.compare_commit)
            comparison = analyzer.compare_codebases()
            print(json.dumps(comparison, indent=2))
            return

        # Handle visualization
        if args.visualize:
            if args.visualize == "call-graph":
                visualization = analyzer.visualize_call_graph(args.function_name)
            elif args.visualize == "dependency-map":
                visualization = analyzer.visualize_dependency_map()
            elif args.visualize == "directory-tree":
                visualization = analyzer.visualize_directory_tree()
            elif args.visualize == "import-cycles":
                visualization = analyzer.visualize_import_cycles()
            
            print(json.dumps(visualization, indent=2))
            return
            
        # Handle type analysis
        if args.analyze_types:
            type_analysis = {
                "untyped_return_statements": analyzer.count_untyped_return_statements(),
                "untyped_parameters": analyzer.count_untyped_parameters(),
                "untyped_attributes": analyzer.count_untyped_attributes(),
                "unnamed_keyword_arguments": analyzer.count_unnamed_keyword_arguments(),
            }
            print(json.dumps(type_analysis, indent=2))
            return
            
        # Handle codebase summary
        if args.summary:
            summary = analyzer.get_codebase_summary()
            print(json.dumps(summary, indent=2))
            return
            
        # Handle code quality analysis
        if args.quality:
            quality = analyzer.analyze_codebase_quality()
            print(json.dumps(quality, indent=2))
            return
            
        # Handle dependency trace analysis
        if args.dependency_trace:
            if not args.symbol_name:
                print("Error: --symbol-name is required for dependency trace analysis")
                return
            dependency_trace = analyzer.analyze_dependency_trace(args.symbol_name)
            print(json.dumps(dependency_trace, indent=2))
            return
            
        # Handle method relationships analysis
        if args.method_relationships:
            if not args.class_name:
                print("Error: --class-name is required for method relationships analysis")
                return
            method_relationships = analyzer.analyze_method_relationships(args.class_name)
            print(json.dumps(method_relationships, indent=2))
            return
            
        # Handle call trace analysis
        if args.call_trace:
            if not args.function_name:
                print("Error: --function-name is required for call trace analysis")
                return
            call_trace = analyzer.analyze_call_trace(args.function_name)
            print(json.dumps(call_trace, indent=2))
            return
            
        # Handle import cycles analysis
        if args.import_cycles:
            import_cycles = analyzer.find_import_cycles()
            print(json.dumps(import_cycles, indent=2))
            return
            
        # Handle call chain analysis
        if args.call_chain:
            call_chain = analyzer.get_call_chain_analysis()
            print(json.dumps(call_chain, indent=2))
            return
            
        # Handle dead code detection
        if args.dead_code:
            dead_code = analyzer.get_dead_code_detection_with_filtering(args.exclude_patterns)
            print(json.dumps(dead_code, indent=2))
            return
            
        # Handle path finding
        if args.path_finding:
            path_finding = analyzer.get_path_finding_in_call_graphs(args.source_function, args.target_function, args.max_depth)
            print(json.dumps(path_finding, indent=2))
            return
            
        # Handle dead symbol detection
        if args.dead_symbols:
            dead_symbols = analyzer.get_dead_symbol_detection()
            print(json.dumps(dead_symbols, indent=2))
            return
            
        # Handle import analysis
        if args.import_analysis:
            import_analysis = analyzer.get_symbol_import_analysis()
            print(json.dumps(import_analysis, indent=2))
            return

        # Perform the analysis
        results = analyzer.analyze(categories=args.categories, output_format=args.output_format, output_file=args.output_file)

        # Print success message
        if args.output_format == "json" and args.output_file:
            print(f"Analysis results saved to {args.output_file}")
        elif args.output_format == "html":
            print(f"HTML report saved to {args.output_file or 'codebase_analysis_report.html'}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
if __name__ == "__main__":
    main()

    def analyze_call_trace(self, function_name: str) -> Dict[str, Any]:
        """Analyze the call trace for a specific function.
        
        Args:
            function_name: Name of the function to analyze
            
        Returns:
            A dictionary containing call trace information.
