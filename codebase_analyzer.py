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
    from codegen.sdk.codebase.codebase_analysis import get_codebase_summary
    from codegen.sdk.codebase.codebase_context import DiffLite
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
    ],
    "code_quality": [
        "get_unused_functions",
        "get_unused_classes",
        "get_unused_variables",
        "get_unused_imports",
        "get_similar_function_detection",
        "get_repeated_code_patterns",
        "get_refactoring_opportunities",
        "get_cyclomatic_complexity",
        "get_cognitive_complexity",
        "get_nesting_depth_analysis",
        "get_function_size_metrics",
        "get_naming_convention_consistency",
        "get_comment_coverage",
        "get_documentation_completeness",
        "get_code_formatting_consistency",
        "count_untyped_return_statements",
        "count_untyped_parameters",
        "count_untyped_attributes",
        "count_unnamed_keyword_arguments",
    ],
    "visualization": [
        "get_module_dependency_visualization",
        "get_symbol_dependency_visualization",
        "get_import_relationship_graphs",
        "get_function_call_visualization",
        "get_call_hierarchy_trees",
        "get_entry_point_flow_diagrams",
        "get_class_hierarchy_visualization",
        "get_symbol_relationship_diagrams",
        "get_package_structure_visualization",
        "get_code_complexity_heat_maps",
        "get_usage_frequency_visualization",
        "get_change_frequency_analysis",
        "visualize_call_graph",
        "visualize_dependency_map",
        "visualize_directory_tree",
    ],
    "language_specific": [
        "get_decorator_usage_analysis",
        "get_dynamic_attribute_access_detection",
        "get_type_hint_coverage",
        "get_magic_method_usage",
        "get_interface_implementation_verification",
        "get_type_definition_completeness",
        "get_jsx_tsx_component_analysis",
        "get_type_narrowing_pattern_detection",
    ],
    "code_metrics": [
        "get_monthly_commits",
        "calculate_cyclomatic_complexity",
        "cc_rank",
        "get_operators_and_operands",
        "calculate_halstead_volume",
        "count_lines",
        "calculate_maintainability_index",
        "get_maintainability_rank",
    ],
    "import_analysis": [
        "detect_import_cycles",
        "visualize_import_cycles",
    ],
    "pr_comparison": [
        "compare_codebases",
        "get_pr_diff_analysis",
        "get_pr_quality_metrics",
    ],
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
        self.console = Console()
        self.results = {}
        self.comparison_codebase = None
        self.comparison_results = {}

        # Initialize the codebase
        if repo_url:
            self._init_from_url(repo_url, language)
        elif repo_path:
            self._init_from_path(repo_path, language)

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

    def init_comparison_codebase(self, commit_sha: str):
        """Initialize a comparison codebase from a specific commit.

        Args:
            commit_sha: The commit SHA to analyze
        """
        if not self.codebase:
            msg = "Primary codebase not initialized. Please initialize the primary codebase first."
            raise ValueError(msg)

        try:
            self.console.print(f"[bold green]Initializing comparison codebase from commit {commit_sha}...[/bold green]")
            
            # Create a temporary directory for the comparison codebase
            tmp_dir = tempfile.mkdtemp(prefix="codebase_analyzer_comparison_")
            
            # Configure the codebase
            config = CodebaseConfig(
                debug=False,
                allow_external=True,
                py_resolve_syspath=True,
            )
            
            secrets = SecretsConfig()
            
            # Clone the repository at the specific commit
            repo_path = self.codebase.ctx.repo_path
            repo_url = self.codebase.ctx.repo_url
            
            if repo_url:
                parts = repo_url.rstrip("/").split("/")
                repo_name = parts[-1]
                owner = parts[-2]
                repo_full_name = f"{owner}/{repo_name}"
                
                self.comparison_codebase = Codebase.from_github(
                    repo_full_name=repo_full_name,
                    tmp_dir=tmp_dir,
                    language=self.codebase.ctx.programming_language,
                    config=config,
                    secrets=secrets,
                    commit_sha=commit_sha,
                )
            else:
                # For local repositories, we need to create a copy at the specific commit
                import subprocess
                import shutil
                
                # Create a temporary clone
                subprocess.run(["git", "clone", repo_path, tmp_dir], check=True)
                
                # Checkout the specific commit
                subprocess.run(["git", "-C", tmp_dir, "checkout", commit_sha], check=True)
                
                self.comparison_codebase = Codebase(
                    repo_path=tmp_dir,
                    language=self.codebase.ctx.programming_language,
                    config=config,
                    secrets=secrets,
                )
            
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

    def count_untyped_return_statements(self) -> dict[str, Any]:
        """Count the number of untyped return statements in the codebase.

        Returns:
            Dict containing the count and details of untyped return statements
        """
        untyped_returns = {
            "count": 0,
            "functions": [],
        }

        for file in self.codebase.files:
            for function in file.functions:
                if isinstance(function.return_type, Placeholder):
                    untyped_returns["count"] += len(function.return_statements)
                    untyped_returns["functions"].append({
                        "name": function.name,
                        "file": function.file.file_path if hasattr(function, "file") else "Unknown",
                        "return_statements": len(function.return_statements),
                    })

        return untyped_returns

    def count_untyped_parameters(self) -> dict[str, Any]:
        """Count the number of untyped parameters in the codebase.

        Returns:
            Dict containing the count and details of untyped parameters
        """
        untyped_parameters = {
            "count": 0,
            "functions": [],
        }

        for file in self.codebase.files:
            for function in file.functions:
                untyped_count = sum(1 for param in function.parameters if not param.is_typed)
                if untyped_count > 0:
                    untyped_parameters["count"] += untyped_count
                    untyped_parameters["functions"].append({
                        "name": function.name,
                        "file": function.file.file_path if hasattr(function, "file") else "Unknown",
                        "untyped_parameters": untyped_count,
                        "total_parameters": len(function.parameters),
                    })

        return untyped_parameters

    def count_untyped_attributes(self) -> dict[str, Any]:
        """Count the number of untyped attributes in the codebase.

        Returns:
            Dict containing the count and details of untyped attributes
        """
        untyped_attributes = {
            "count": 0,
            "classes": [],
        }

        for cls in self.codebase.classes:
            untyped_count = sum(1 for attr in cls.attributes if isinstance(attr.assignment.type, TypePlaceholder))
            if untyped_count > 0:
                untyped_attributes["count"] += untyped_count
                untyped_attributes["classes"].append({
                    "name": cls.name,
                    "file": cls.file.file_path if hasattr(cls, "file") else "Unknown",
                    "untyped_attributes": untyped_count,
                    "total_attributes": len(cls.attributes),
                })

        return untyped_attributes

    def count_unnamed_keyword_arguments(self) -> dict[str, Any]:
        """Count the number of unnamed keyword arguments in the codebase.

        Returns:
            Dict containing the count and details of unnamed keyword arguments
        """
        unnamed_kwargs = {
            "count": 0,
            "calls": [],
        }

        for file in self.codebase.files:
            for call in file.function_calls:
                unnamed_count = sum(1 for arg in call.args if arg.is_named is False)
                if unnamed_count > 0:
                    unnamed_kwargs["count"] += unnamed_count
                    unnamed_kwargs["calls"].append({
                        "function": call.function.name if hasattr(call, "function") and call.function else "Unknown",
                        "file": file.file_path,
                        "line": call.line if hasattr(call, "line") else "Unknown",
                        "unnamed_args": unnamed_count,
                    })

        return unnamed_kwargs

    def detect_import_cycles(self) -> dict[str, Any]:
        """Detect import cycles in the codebase.

        Returns:
            Dict containing the detected import cycles
        """
        import_cycles = {
            "count": 0,
            "cycles": [],
        }

        # Create a directed graph of imports
        G = nx.DiGraph()

        # Add nodes for each file
        for file in self.codebase.files:
            G.add_node(file.file_path)

        # Add edges for imports
        for file in self.codebase.files:
            for imp in file.imports:
                if hasattr(imp, "module") and imp.module:
                    # Find the file that contains this module
                    for target_file in self.codebase.files:
                        if target_file.module_name == imp.module:
                            G.add_edge(file.file_path, target_file.file_path)
                            break

        # Find cycles
        try:
            cycles = list(nx.simple_cycles(G))
            import_cycles["count"] = len(cycles)
            import_cycles["cycles"] = [list(cycle) for cycle in cycles]
        except nx.NetworkXNoCycle:
            # No cycles found
            pass

        return import_cycles

    def visualize_import_cycles(self) -> dict[str, Any]:
        """Visualize import cycles in the codebase.

        Returns:
            Dict containing the visualization data for import cycles
        """
        cycles = self.detect_import_cycles()
        
        if cycles["count"] == 0:
            return {"message": "No import cycles detected."}
        
        # Create a directed graph for visualization
        G = nx.DiGraph()
        
        # Add nodes and edges for each cycle
        for cycle in cycles["cycles"]:
            for i in range(len(cycle)):
                G.add_node(cycle[i])
                G.add_edge(cycle[i], cycle[(i + 1) % len(cycle)])
        
        # Convert to a format suitable for visualization
        node_trace = {
            "x": [],
            "y": [],
            "text": [],
            "mode": "markers+text",
            "textposition": "top center",
            "marker": {
                "size": 15,
                "color": "lightblue",
                "line": {"width": 2, "color": "darkblue"},
            },
        }
        
        edge_trace = {
            "x": [],
            "y": [],
            "line": {"width": 1.5, "color": "darkblue"},
            "hoverinfo": "none",
            "mode": "lines",
        }
        
        # Use a layout algorithm to position nodes
        pos = nx.spring_layout(G)
        
        # Add node positions
        for node in G.nodes():
            x, y = pos[node]
            node_trace["x"].append(x)
            node_trace["y"].append(y)
            node_trace["text"].append(node)
        
        # Add edge positions
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace["x"].extend([x0, x1, None])
            edge_trace["y"].extend([y0, y1, None])
        
        # Create the figure
        fig_data = {
            "data": [edge_trace, node_trace],
            "layout": {
                "title": f"Import Cycles ({cycles['count']} cycles detected)",
                "showlegend": False,
                "hovermode": "closest",
                "margin": {"b": 20, "l": 5, "r": 5, "t": 40},
                "xaxis": {"showgrid": False, "zeroline": False, "showticklabels": False},
                "yaxis": {"showgrid": False, "zeroline": False, "showticklabels": False},
            },
        }
        
        return {
            "cycles": cycles["cycles"],
            "visualization": fig_data,
        }

    def visualize_call_graph(self, function_name: Optional[str] = None) -> dict[str, Any]:
        """Visualize the call graph for a specific function or the entire codebase.

        Args:
            function_name: Name of the function to visualize. If None, visualize the entire call graph.

        Returns:
            Dict containing the visualization data for the call graph
        """
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add nodes for each function
        for function in self.codebase.functions:
            G.add_node(function.name, type="function", file=function.file.file_path if hasattr(function, "file") else "Unknown")
        
        # Add edges for function calls
        for file in self.codebase.files:
            for call in file.function_calls:
                if hasattr(call, "function") and call.function and hasattr(call, "caller") and call.caller:
                    G.add_edge(call.caller.name, call.function.name)
        
        # If a specific function is provided, filter the graph
        if function_name:
            # Find the function node
            if function_name not in G:
                return {"error": f"Function '{function_name}' not found in the codebase."}
            
            # Get all functions that call or are called by this function
            predecessors = list(G.predecessors(function_name))
            successors = list(G.successors(function_name))
            
            # Create a subgraph with these functions
            nodes = set([function_name] + predecessors + successors)
            subgraph = G.subgraph(nodes)
            G = subgraph
        
        # Convert to a format suitable for visualization
        node_trace = {
            "x": [],
            "y": [],
            "text": [],
            "mode": "markers+text",
            "textposition": "top center",
            "marker": {
                "size": 15,
                "color": [],
                "line": {"width": 2, "color": "darkblue"},
            },
        }
        
        edge_trace = {
            "x": [],
            "y": [],
            "line": {"width": 1.5, "color": "darkblue"},
            "hoverinfo": "none",
            "mode": "lines",
        }
        
        # Use a layout algorithm to position nodes
        pos = nx.spring_layout(G)
        
        # Add node positions
        for node in G.nodes():
            x, y = pos[node]
            node_trace["x"].append(x)
            node_trace["y"].append(y)
            node_trace["text"].append(node)
            
            # Color the node based on its type
            if function_name and node == function_name:
                node_trace["marker"]["color"].append("red")  # Highlight the selected function
            else:
                node_trace["marker"]["color"].append("lightblue")
        
        # Add edge positions
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace["x"].extend([x0, x1, None])
            edge_trace["y"].extend([y0, y1, None])
        
        # Create the figure
        fig_data = {
            "data": [edge_trace, node_trace],
            "layout": {
                "title": f"Call Graph for {function_name if function_name else 'Entire Codebase'}",
                "showlegend": False,
                "hovermode": "closest",
                "margin": {"b": 20, "l": 5, "r": 5, "t": 40},
                "xaxis": {"showgrid": False, "zeroline": False, "showticklabels": False},
                "yaxis": {"showgrid": False, "zeroline": False, "showticklabels": False},
            },
        }
        
        return {
            "nodes": len(G.nodes()),
            "edges": len(G.edges()),
            "visualization": fig_data,
        }

    def visualize_dependency_map(self) -> dict[str, Any]:
        """Visualize the dependency map of the codebase.

        Returns:
            Dict containing the visualization data for the dependency map
        """
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add nodes for each file
        for file in self.codebase.files:
            G.add_node(file.file_path, type="file")
        
        # Add edges for imports
        for file in self.codebase.files:
            for imp in file.imports:
                if hasattr(imp, "module") and imp.module:
                    # Find the file that contains this module
                    for target_file in self.codebase.files:
                        if target_file.module_name == imp.module:
                            G.add_edge(file.file_path, target_file.file_path)
                            break
        
        # Convert to a format suitable for visualization
        node_trace = {
            "x": [],
            "y": [],
            "text": [],
            "mode": "markers+text",
            "textposition": "top center",
            "marker": {
                "size": 10,
                "color": "lightblue",
                "line": {"width": 2, "color": "darkblue"},
            },
        }
        
        edge_trace = {
            "x": [],
            "y": [],
            "line": {"width": 1, "color": "darkblue"},
            "hoverinfo": "none",
            "mode": "lines",
        }
        
        # Use a layout algorithm to position nodes
        pos = nx.spring_layout(G)
        
        # Add node positions
        for node in G.nodes():
            x, y = pos[node]
            node_trace["x"].append(x)
            node_trace["y"].append(y)
            node_trace["text"].append(os.path.basename(node))  # Show only the filename for clarity
        
        # Add edge positions
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace["x"].extend([x0, x1, None])
            edge_trace["y"].extend([y0, y1, None])
        
        # Create the figure
        fig_data = {
            "data": [edge_trace, node_trace],
            "layout": {
                "title": "Dependency Map",
                "showlegend": False,
                "hovermode": "closest",
                "margin": {"b": 20, "l": 5, "r": 5, "t": 40},
                "xaxis": {"showgrid": False, "zeroline": False, "showticklabels": False},
                "yaxis": {"showgrid": False, "zeroline": False, "showticklabels": False},
            },
        }
        
        return {
            "files": len(G.nodes()),
            "dependencies": len(G.edges()),
            "visualization": fig_data,
        }

    def visualize_directory_tree(self) -> dict[str, Any]:
        """Visualize the directory tree of the codebase.

        Returns:
            Dict containing the visualization data for the directory tree
        """
        # Create a directed graph
        G = nx.DiGraph()
        
        # Get all file paths
        file_paths = [file.file_path for file in self.codebase.files]
        
        # Add nodes for each directory and file
        directories = set()
        for path in file_paths:
            # Add the file node
            G.add_node(path, type="file")
            
            # Add directory nodes
            parts = path.split(os.sep)
            current_path = ""
            for i, part in enumerate(parts[:-1]):  # Exclude the filename
                if i == 0:
                    current_path = part
                else:
                    current_path = os.path.join(current_path, part)
                
                if current_path not in directories:
                    G.add_node(current_path, type="directory")
                    directories.add(current_path)
                
                # Add edge from directory to subdirectory or file
                if i < len(parts) - 2:  # Connect to subdirectory
                    next_path = os.path.join(current_path, parts[i + 1])
                    G.add_edge(current_path, next_path)
                else:  # Connect to file
                    G.add_edge(current_path, path)
        
        # Convert to a format suitable for visualization
        node_trace = {
            "x": [],
            "y": [],
            "text": [],
            "mode": "markers+text",
            "textposition": "top center",
            "marker": {
                "size": [],
                "color": [],
                "line": {"width": 2, "color": "darkblue"},
            },
        }
        
        edge_trace = {
            "x": [],
            "y": [],
            "line": {"width": 1, "color": "darkblue"},
            "hoverinfo": "none",
            "mode": "lines",
        }
        
        # Use a tree layout algorithm
        pos = nx.nx_agraph.graphviz_layout(G, prog="dot")
        
        # Add node positions
        for node in G.nodes():
            x, y = pos[node]
            node_trace["x"].append(x)
            node_trace["y"].append(y)
            
            # Show only the basename for clarity
            node_trace["text"].append(os.path.basename(node) or node)
            
            # Set node size and color based on type
            if G.nodes[node]["type"] == "directory":
                node_trace["marker"]["size"].append(15)
                node_trace["marker"]["color"].append("lightgreen")
            else:
                node_trace["marker"]["size"].append(10)
                node_trace["marker"]["color"].append("lightblue")
        
        # Add edge positions
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace["x"].extend([x0, x1, None])
            edge_trace["y"].extend([y0, y1, None])
        
        # Create the figure
        fig_data = {
            "data": [edge_trace, node_trace],
            "layout": {
                "title": "Directory Tree",
                "showlegend": False,
                "hovermode": "closest",
                "margin": {"b": 20, "l": 5, "r": 5, "t": 40},
                "xaxis": {"showgrid": False, "zeroline": False, "showticklabels": False},
                "yaxis": {"showgrid": False, "zeroline": False, "showticklabels": False},
            },
        }
        
        return {
            "directories": len(directories),
            "files": len(file_paths),
            "visualization": fig_data,
        }

    def get_pr_diff_analysis(self, pr_number: int) -> dict[str, Any]:
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

    def get_pr_quality_metrics(self, pr_number: int) -> dict[str, Any]:
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
    def _generate_html_report(self, output_file: str) -> None:
        """Generate an HTML report of the analysis results."""
        if not output_file:
            output_file = "codebase_analysis_report.html"

        # Simple HTML template
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Codebase Analysis Report</title>
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
            </style>
        </head>
        <body>
            <h1>Codebase Analysis Report</h1>
            <div class="section">
                <h2>Metadata</h2>
                <p><strong>Repository:</strong> {self.results["metadata"]["repo_name"]}</p>
                <p><strong>Analysis Time:</strong> {self.results["metadata"]["analysis_time"]}</p>
                <p><strong>Language:</strong> {self.results["metadata"]["language"]}</p>
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
        self.console.print(f"[bold blue]Codebase Analysis Report for {self.results['metadata']['repo_name']}[/bold blue]")
        self.console.print(f"[bold]Analysis Time:[/bold] {self.results['metadata']['analysis_time']}")
        self.console.print(f"[bold]Language:[/bold] {self.results['metadata']['language']}")

        for category, metrics in self.results["categories"].items():
            self.console.print(f"\n[bold green]{category.replace('_', ' ').title()}[/bold green]")

            for metric_name, metric_value in metrics.items():
                self.console.print(f"[bold]{metric_name.replace('_', ' ').title()}:[/bold]")

                if isinstance(metric_value, dict):
                    table = Table(show_header=True)
                    table.add_column("Key")
                    table.add_column("Value")

                    for k, v in metric_value.items():
                        if isinstance(v, dict):
                            table.add_row(k, str(v))
                        else:
                            table.add_row(str(k), str(v))

                    self.console.print(table)
                elif isinstance(metric_value, list):
                    if len(metric_value) > 0 and isinstance(metric_value[0], dict):
                        if len(metric_value) > 0:
                            table = Table(show_header=True)
                            for key in metric_value[0].keys():
                                table.add_column(key)

                            for item in metric_value[:10]:  # Show only first 10 items
                                table.add_row(*[str(v) for v in item.values()])

                            self.console.print(table)
                            if len(metric_value) > 10:
                                self.console.print(f"... and {len(metric_value) - 10} more items")
                    else:
                        self.console.print(str(metric_value))
                else:
                    self.console.print(str(metric_value))

    def get_monthly_commits(self) -> dict[str, int]:
        """Get the number of commits per month."""
        try:
            # Get commit history
            commits = list(self.codebase.github.repo.get_commits())

            # Group commits by month
            commits_by_month = {}

            for commit in commits:
                date = commit.commit.author.date
                month_key = f"{date.year}-{date.month:02d}"

                if month_key in commits_by_month:
                    commits_by_month[month_key] += 1
                else:
                    commits_by_month[month_key] = 1

            # Sort by month
            sorted_commits = dict(sorted(commits_by_month.items()))

            return sorted_commits
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
