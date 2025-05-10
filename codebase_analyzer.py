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
from collections.abc import Collection, Iterator, Sized
from typing import Any, Dict, List, Optional, Tuple, Union, cast

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
        self.codebase: Any = None
        self.console = Console()
        self.results: Dict[str, Any] = {}
        self.comparison_codebase: Any = None
        self.comparison_results: Dict[str, Any] = {}

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

            # Use Any type to avoid the attribute error
            self.codebase = cast(Any, Codebase).from_github(repo_full_name=repo_full_name, tmp_dir=tmp_dir, language=prog_lang, config=config, secrets=secrets, full_history=True)

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

            # Initialize the codebase with proper type
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

    def count_untyped_return_statements(self) -> Dict[str, Any]:
        """Count the number of functions without return type annotations."""
        try:
            if self.codebase is None:
                return {"error": "Codebase not initialized"}
                
            untyped_returns = 0
            untyped_functions: List[str] = []
            
            # Iterate through all Python files
            for file in self.codebase.files:
                if file.language == ProgrammingLanguage.PYTHON:
                    # Check each function in the file
                    for func in file.functions:
                        if func.return_type is None or isinstance(func.return_type, TypePlaceholder):
                            untyped_returns += 1
                            untyped_functions.append(f"{file.path}:{func.name}")
            
            return {
                "untyped_return_count": untyped_returns,
                "untyped_functions": untyped_functions
            }
        except Exception as e:
            return {"error": str(e)}

    def count_untyped_parameters(self) -> Dict[str, Any]:
        """Count the number of function parameters without type annotations."""
        try:
            if self.codebase is None:
                return {"error": "Codebase not initialized"}
                
            untyped_params = 0
            functions_with_untyped_params: List[Dict[str, Any]] = []
            
            # Iterate through all Python files
            for file in self.codebase.files:
                if file.language == ProgrammingLanguage.PYTHON:
                    # Check each function in the file
                    for func in file.functions:
                        untyped_in_func = 0
                        for param in func.parameters:
                            if param.type is None or isinstance(param.type, TypePlaceholder):
                                untyped_in_func += 1
                                untyped_params += 1
                        
                        if untyped_in_func > 0:
                            functions_with_untyped_params.append({
                                "file": file.path,
                                "function": func.name,
                                "untyped_params": untyped_in_func
                            })
            
            return {
                "untyped_parameter_count": untyped_params,
                "functions_with_untyped_params": functions_with_untyped_params
            }
        except Exception as e:
            return {"error": str(e)}

    def count_untyped_attributes(self) -> Dict[str, Any]:
        """Count the number of class attributes without type annotations."""
        try:
            if self.codebase is None:
                return {"error": "Codebase not initialized"}
                
            untyped_attrs = 0
            classes_with_untyped_attrs: List[Dict[str, Any]] = []
            
            # Iterate through all Python files
            for file in self.codebase.classes:
                if file.language == ProgrammingLanguage.PYTHON:
                    # Check each class in the file
                    for cls in self.codebase.classes:
                        untyped_in_class = 0
                        for attr in cls.attributes:
                            if attr.type is None or isinstance(attr.type, TypePlaceholder):
                                untyped_in_class += 1
                                untyped_attrs += 1
                        
                        if untyped_in_class > 0:
                            classes_with_untyped_attrs.append({
                                "file": file.path,
                                "class": cls.name,
                                "untyped_attributes": untyped_in_class
                            })
            
            return {
                "untyped_attribute_count": untyped_attrs,
                "classes_with_untyped_attrs": classes_with_untyped_attrs
            }
        except Exception as e:
            return {"error": str(e)}

    def count_unnamed_keyword_arguments(self) -> Dict[str, Any]:
        """Count the number of **kwargs parameters without type annotations."""
        try:
            if self.codebase is None:
                return {"error": "Codebase not initialized"}
                
            unnamed_kwargs = 0
            functions_with_unnamed_kwargs: List[Dict[str, Any]] = []
            
            # Iterate through all Python files
            for file in self.codebase.files:
                if file.language == ProgrammingLanguage.PYTHON:
                    # Check each function in the file
                    for func in file.functions:
                        has_unnamed_kwargs = False
                        for param in func.parameters:
                            if param.name.startswith("**") and (param.type is None or isinstance(param.type, TypePlaceholder)):
                                has_unnamed_kwargs = True
                                unnamed_kwargs += 1
                        
                        if has_unnamed_kwargs:
                            functions_with_unnamed_kwargs.append({
                                "file": file.path,
                                "function": func.name
                            })
            
            return {
                "unnamed_kwargs_count": unnamed_kwargs,
                "functions_with_unnamed_kwargs": functions_with_unnamed_kwargs
            }
        except Exception as e:
            return {"error": str(e)}

    def detect_import_cycles(self) -> Dict[str, Any]:
        """Detect import cycles in the codebase."""
        try:
            if self.codebase is None:
                return {"error": "Codebase not initialized"}
                
            # Create a directed graph for imports
            G: nx.DiGraph = nx.DiGraph()
            
            # Add nodes for each file
            for file in self.codebase.files:
                file_path = file.path
                G.add_node(file_path)
            
            # Add edges for imports
            for file in self.codebase.files:
                file_path = file.path
                
                for imp in file.imports:
                    # Find the file that corresponds to this import
                    for target_file in self.codebase.files:
                        if target_file.path.endswith(f"{imp.module.replace('.', '/')}.py"):
                            G.add_edge(file_path, target_file.path)
                            break
            
            # Find cycles
            cycles = list(nx.simple_cycles(G))
            
            return {
                "import_cycles_count": len(cycles),
                "import_cycles": cycles
            }
        except Exception as e:
            return {"error": str(e)}

    def visualize_import_cycles(self) -> Dict[str, Any]:
        """Visualize import cycles in the codebase."""
        try:
            if self.codebase is None:
                return {"error": "Codebase not initialized"}
                
            # Create a directed graph for imports
            G: nx.DiGraph = nx.DiGraph()
            
            # Add nodes for each file
            for file in self.codebase.files:
                file_path = file.path
                G.add_node(file_path)
            
            # Add edges for imports
            for file in self.codebase.files:
                file_path = file.path
                
                for imp in file.imports:
                    # Find the file that corresponds to this import
                    for target_file in self.codebase.files:
                        if target_file.path.endswith(f"{imp.module.replace('.', '/')}.py"):
                            G.add_edge(file_path, target_file.path)
                            break
            
            # Find cycles
            cycles = list(nx.simple_cycles(G))
            
            # Create a visualization
            if not cycles:
                return {
                    "message": "No import cycles found",
                    "visualization": None
                }
            
            # Create a subgraph with only the nodes and edges in cycles
            cycle_nodes = set()
            for cycle in cycles:
                cycle_nodes.update(cycle)
            
            cycle_graph = G.subgraph(cycle_nodes)
            
            # Create a Plotly figure
            pos = nx.spring_layout(cycle_graph)
            
            edge_x = []
            edge_y = []
            for edge in cycle_graph.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
            
            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=0.5, color='#888'),
                hoverinfo='none',
                mode='lines')
            
            node_x = []
            node_y = []
            for node in cycle_graph.nodes():
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
            
            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                hoverinfo='text',
                text=list(cycle_graph.nodes()),
                textposition="top center",
                marker=dict(
                    showscale=True,
                    colorscale='YlGnBu',
                    size=10,
                    colorbar=dict(
                        thickness=15,
                        title='Node Connections',
                        xanchor='left',
                        titleside='right'
                    ),
                    line_width=2))
            
            # Color nodes by their degree
            node_adjacencies = []
            for node in cycle_graph.nodes():
                node_adjacencies.append(len(list(cycle_graph.neighbors(node))))
            
            node_trace.marker.color = node_adjacencies
            
            # Create the figure
            fig = go.Figure(data=[edge_trace, node_trace],
                            layout=go.Layout(
                                title='Import Cycles Visualization',
                                titlefont_size=16,
                                showlegend=False,
                                hovermode='closest',
                                margin=dict(b=20, l=5, r=5, t=40),
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                            )
            
            # Convert to HTML
            html_content = fig.to_html(full_html=False)
            
            # Generate a list of cycle descriptions
            cycle_descriptions: List[str] = []
            for i, cycle in enumerate(cycles):
                cycle_descriptions.append(f"Cycle {i+1}: {' -> '.join(cycle)} -> {cycle[0]}")
            
            return {
                "import_cycles_count": len(cycles),
                "import_cycles": cycles,
                "cycle_descriptions": cycle_descriptions,
                "visualization_html": html_content
            }
        except Exception as e:
            return {"error": str(e)}

    def visualize_call_graph(self, function_name: Optional[str] = None) -> Dict[str, Any]:
        """Visualize the call graph of the codebase or a specific function."""
        try:
            if self.codebase is None:
                return {"error": "Codebase not initialized"}
                
            # Create a directed graph for function calls
            G: nx.DiGraph = nx.DiGraph()
            
            # Add nodes for each function
            for file in self.codebase.files:
                for func in file.functions:
                    func_id = f"{file.path}:{func.name}"
                    G.add_node(func_id, name=func.name, file=file.path)
            
            # Add edges for function calls
            for file in self.codebase.files:
                for func in file.functions:
                    caller_id = f"{file.path}:{func.name}"
                    
                    # Parse the function body to find function calls
                    # This is a simplified approach and might miss some calls
                    if func.code_block and func.code_block.content:
                        code = func.code_block.content
                        # Simple regex to find function calls
                        calls = re.findall(r'(\w+)\s*\(', code)
                        
                        for callee_name in calls:
                            # Find the function being called
                            for target_file in self.codebase.files:
                                for target_func in target_file.functions:
                                    if target_func.name == callee_name:
                                        callee_id = f"{target_file.path}:{target_func.name}"
                                        G.add_edge(caller_id, callee_id)
            
            # If a specific function is provided, create a subgraph
            if function_name:
                # Find the function node
                function_nodes = []
                for node in G.nodes():
                    if node.split(":")[-1] == function_name:
                        function_nodes.append(node)
                
                if not function_nodes:
                    return {
                        "message": f"Function '{function_name}' not found",
                        "visualization": None
                    }
                
                # Create a subgraph with the function and its neighbors
                subgraph_nodes = set()
                for func_node in function_nodes:
                    subgraph_nodes.add(func_node)
                    subgraph_nodes.update(nx.descendants(G, func_node))
                    subgraph_nodes.update(nx.ancestors(G, func_node))
                
                G = G.subgraph(subgraph_nodes)
            
            # Convert to undirected for better visualization
            undirected_G = G.to_undirected()
            
            # Create a Plotly figure
            pos = nx.spring_layout(undirected_G)
            
            edge_x = []
            edge_y = []
            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
            
            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=0.5, color='#888'),
                hoverinfo='none',
                mode='lines')
            
            node_x = []
            node_y = []
            node_text = []
            for node in G.nodes():
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                node_text.append(node.split(":")[-1])  # Just the function name
            
            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                hoverinfo='text',
                text=node_text,
                textposition="top center",
                marker=dict(
                    showscale=True,
                    colorscale='YlGnBu',
                    size=10,
                    colorbar=dict(
                        thickness=15,
                        title='Node Connections',
                        xanchor='left',
                        titleside='right'
                    ),
                    line_width=2))
            
            # Color nodes by their degree
            node_adjacencies = []
            for node in G.nodes():
                node_adjacencies.append(len(list(G.neighbors(node))))
            
            node_trace.marker.color = node_adjacencies
            
            # Create the figure
            fig = go.Figure(data=[edge_trace, node_trace],
                            layout=go.Layout(
                                title=f'Call Graph Visualization{" for " + function_name if function_name else ""}',
                                titlefont_size=16,
                                showlegend=False,
                                hovermode='closest',
                                margin=dict(b=20, l=5, r=5, t=40),
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                            )
            
            # Convert to HTML
            html_content = fig.to_html(full_html=False)
            
            # Generate statistics
            stats = {
                "total_functions": len(G.nodes()),
                "total_calls": len(G.edges()),
                "most_called_functions": [],
                "functions_with_most_dependencies": []
            }
            
            # Find most called functions
            in_degree = dict(G.in_degree())
            most_called = sorted(in_degree.items(), key=lambda x: x[1], reverse=True)[:5]
            stats["most_called_functions"] = [{"function": node.split(":")[-1], "calls": count} for node, count in most_called]
            
            # Find functions with most dependencies
            out_degree = dict(G.out_degree())
            most_deps = sorted(out_degree.items(), key=lambda x: x[1], reverse=True)[:5]
            stats["functions_with_most_dependencies"] = [{"function": node.split(":")[-1], "dependencies": count} for node, count in most_deps]
            
            # Find longest call chains
            longest_paths = []
            for source in G.nodes():
                for target in G.nodes():
                    if source != target:
                        try:
                            paths = list(nx.all_simple_paths(G, source, target))
                            if paths:
                                longest_path = max(paths, key=len)
                                if len(longest_path) > 1:  # Only include paths with at least 2 nodes
                                    longest_paths.append({
                                        "path": [node.split(":")[-1] for node in longest_path],
                                        "length": len(longest_path)
                                    })
                        except nx.NetworkXNoPath:
                            pass
            
            # Sort by path length and take top 5
            longest_paths = sorted(longest_paths, key=lambda x: x["length"], reverse=True)[:5]
            stats["longest_call_chains"] = longest_paths
            
            return {
                "statistics": stats,
                "visualization_html": html_content
            }
        except Exception as e:
            return {"error": str(e)}

    def visualize_dependency_map(self) -> Dict[str, Any]:
        """Visualize the dependency map of the codebase."""
        try:
            if self.codebase is None:
                return {"error": "Codebase not initialized"}
                
            # Create a directed graph for dependencies
            G: nx.DiGraph = nx.DiGraph()
            
            # Add nodes for each file
            for file in self.codebase.files:
                file_path = file.path
                G.add_node(file_path)
            
            # Add edges for imports
            for file in self.codebase.files:
                file_path = file.path
                
                for imp in file.imports:
                    # Find the file that corresponds to this import
                    for target_file in self.codebase.files:
                        if target_file.path.endswith(f"{imp.module.replace('.', '/')}.py"):
                            G.add_edge(file_path, target_file.path)
                            break
            
            # Create a Plotly figure
            pos = nx.spring_layout(G)
            
            edge_x = []
            edge_y = []
            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
            
            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=0.5, color='#888'),
                hoverinfo='none',
                mode='lines')
            
            node_x = []
            node_y = []
            node_text = []
            for node in G.nodes():
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                node_text.append(os.path.basename(node))  # Just the filename
            
            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                hoverinfo='text',
                text=node_text,
                textposition="top center",
                marker=dict(
                    showscale=True,
                    colorscale='YlGnBu',
                    size=10,
                    colorbar=dict(
                        thickness=15,
                        title='Node Connections',
                        xanchor='left',
                        titleside='right'
                    ),
                    line_width=2))
            
            # Color nodes by their degree
            node_adjacencies = []
            for node in G.nodes():
                node_adjacencies.append(len(list(G.neighbors(node))))
            
            node_trace.marker.color = node_adjacencies
            
            # Create the figure
            fig = go.Figure(data=[edge_trace, node_trace],
                            layout=go.Layout(
                                title='Dependency Map Visualization',
                                titlefont_size=16,
                                showlegend=False,
                                hovermode='closest',
                                margin=dict(b=20, l=5, r=5, t=40),
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                            )
            
            # Convert to HTML
            html_content = fig.to_html(full_html=False)
            
            # Generate statistics
            stats = {
                "total_files": len(G.nodes()),
                "total_dependencies": len(G.edges()),
                "most_imported_files": [],
                "files_with_most_imports": []
            }
            
            # Find most imported files
            in_degree = dict(G.in_degree())
            most_imported = sorted(in_degree.items(), key=lambda x: x[1], reverse=True)[:5]
            stats["most_imported_files"] = [{"file": os.path.basename(node), "imports": count} for node, count in most_imported]
            
            # Find files with most imports
            out_degree = dict(G.out_degree())
            most_imports = sorted(out_degree.items(), key=lambda x: x[1], reverse=True)[:5]
            stats["files_with_most_imports"] = [{"file": os.path.basename(node), "imports": count} for node, count in most_imports]
            
            # Find strongly connected components (potential circular dependencies)
            sccs = list(nx.strongly_connected_components(G))
            circular_deps = [list(scc) for scc in sccs if len(scc) > 1]
            stats["circular_dependencies"] = [{"files": [os.path.basename(f) for f in scc]} for scc in circular_deps]
            
            # Find isolated files (no imports or importers)
            isolated = [node for node, degree in dict(G.degree()).items() if degree == 0]
            stats["isolated_files"] = [os.path.basename(f) for f in isolated]
            
            return {
                "statistics": stats,
                "visualization_html": html_content
            }
        except Exception as e:
            return {"error": str(e)}

    def visualize_directory_tree(self) -> Dict[str, Any]:
        """Visualize the directory structure of the codebase."""
        try:
            if self.codebase is None:
                return {"error": "Codebase not initialized"}
                
            # Create a directed graph for the directory structure
            G: nx.DiGraph = nx.DiGraph()
            
            # Add nodes for each file and directory
            directories = set()
            for file in self.codebase.files:
                file_path = file.path
                G.add_node(file_path, type="file")
                
                # Add directory nodes
                dir_path = os.path.dirname(file_path)
                while dir_path:
                    if dir_path not in directories:
                        G.add_node(dir_path, type="directory")
                        directories.add(dir_path)
                    
                    parent_dir = os.path.dirname(dir_path)
                    if parent_dir and parent_dir != dir_path:
                        G.add_edge(parent_dir, dir_path)
                    
                    dir_path = parent_dir
            
            # Add edges from directories to files
            for file in self.codebase.files:
                file_path = file.path
                dir_path = os.path.dirname(file_path)
                if dir_path:
                    G.add_edge(dir_path, file_path)
            
            # Create a Plotly figure
            pos = nx.spring_layout(G)
            
            # Create separate traces for directories and files
            dir_nodes = [node for node in G.nodes() if G.nodes[node].get("type") == "directory"]
            file_nodes = [node for node in G.nodes() if G.nodes[node].get("type") == "file"]
            
            # Create edges
            edge_x = []
            edge_y = []
            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
            
            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=0.5, color='#888'),
                hoverinfo='none',
                mode='lines')
            
            # Create directory nodes
            dir_x = []
            dir_y = []
            dir_text = []
            for node in dir_nodes:
                x, y = pos[node]
                dir_x.append(x)
                dir_y.append(y)
                dir_text.append(os.path.basename(node) or "root")
            
            dir_trace = go.Scatter(
                x=dir_x, y=dir_y,
                mode='markers+text',
                hoverinfo='text',
                text=dir_text,
                textposition="top center",
                marker=dict(
                    color='rgba(255, 165, 0, 0.8)',
                    size=15,
                    symbol='square',
                    line=dict(color='rgb(50,50,50)', width=1)
                ),
                name='Directories')
            
            # Create file nodes
            file_x = []
            file_y = []
            file_text = []
            for node in file_nodes:
                x, y = pos[node]
                file_x.append(x)
                file_y.append(y)
                file_text.append(os.path.basename(node))
            
            file_trace = go.Scatter(
                x=file_x, y=file_y,
                mode='markers+text',
                hoverinfo='text',
                text=file_text,
                textposition="top center",
                marker=dict(
                    color='rgba(0, 116, 217, 0.8)',
                    size=8,
                    symbol='circle',
                    line=dict(color='rgb(50,50,50)', width=1)
                ),
                name='Files')
            
            # Create the figure
            fig = go.Figure(data=[edge_trace, dir_trace, file_trace],
                            layout=go.Layout(
                                title='Directory Structure Visualization',
                                titlefont_size=16,
                                showlegend=True,
                                hovermode='closest',
                                margin=dict(b=20, l=5, r=5, t=40),
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                            )
            
            # Convert to HTML
            html_content = fig.to_html(full_html=False)
            
            # Generate statistics
            stats = {
                "total_files": len(file_nodes),
                "total_directories": len(dir_nodes),
                "directory_breakdown": []
            }
            
            # Count files per directory
            dir_file_counts: Dict[str, int] = {}
            for file_node in file_nodes:
                dir_path = os.path.dirname(file_node)
                if dir_path in dir_file_counts:
                    dir_file_counts[dir_path] += 1
                else:
                    dir_file_counts[dir_path] = 1
            
            # Sort by file count
            sorted_dirs = sorted(dir_file_counts.items(), key=lambda x: x[1], reverse=True)
            stats["directory_breakdown"] = [{"directory": dir_path or "root", "file_count": count} for dir_path, count in sorted_dirs]
            
            return {
                "statistics": stats,
                "visualization_html": html_content
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
        if self.codebase is None or not hasattr(self.codebase, "github") or not self.codebase.github:
            return {"error": "GitHub client not available. Make sure the codebase was initialized from a GitHub repository."}
        
        try:
            # Get the PR
            pr = self.codebase.github.repo.get_pull(pr_number)
            
            # Get the diff
            diff = pr.get_files()
            
            # Analyze the diff
            analysis = {
                "pr_number": pr_number,
                "title": pr.title,
                "state": pr.state,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "files_changed": [],
                "total_additions": pr.additions,
                "total_deletions": pr.deletions,
                "total_changes": pr.additions + pr.deletions,
                "file_types": {},
                "most_changed_files": []
            }
            
            # Analyze each file
            file_changes = []
            for file in diff:
                file_info = {
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.additions + file.deletions
                }
                
                file_changes.append(file_info)
                
                # Track file types
                ext = os.path.splitext(file.filename)[1]
                if ext:
                    if ext in analysis["file_types"]:
                        analysis["file_types"][ext] += 1
                    else:
                        analysis["file_types"][ext] = 1
            
            # Sort files by number of changes
            file_changes.sort(key=lambda x: x["changes"], reverse=True)
            analysis["files_changed"] = file_changes
            analysis["most_changed_files"] = file_changes[:5]
            
            return analysis
            
        except Exception as e:
            return {"error": str(e)}

    def get_pr_quality_metrics(self, pr_number: int) -> Dict[str, Any]:
        """Get quality metrics for a pull request.

        Args:
            pr_number: The number of the pull request to analyze

        Returns:
            Dict containing the quality metrics of the PR
        """
        if self.codebase is None or not hasattr(self.codebase, "github") or not self.codebase.github:
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

    def get_monthly_commits(self) -> Dict[str, int]:
        """Get the number of commits per month."""
        try:
            if self.codebase is None or not hasattr(self.codebase, "github") or not self.codebase.github:
                return {"error": "GitHub client not available. Make sure the codebase was initialized from a GitHub repository."}
            
            # Get commit history
            commits = list(self.codebase.github.repo.get_commits())
            
            # Group commits by month
            commits_by_month: Dict[str, int] = {}
            
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

    def main(self):
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
