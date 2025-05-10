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
import re
import sys
import tempfile
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

try:
    from codegen.configs.models.codebase import CodebaseConfig
    from codegen.configs.models.secrets import SecretsConfig
    from codegen.sdk.core.codebase import Codebase
    from codegen.shared.enums.programming_language import ProgrammingLanguage
    from codegen.shared.enums.usage_type import UsageType
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
        "analyze_symbol_imports",
        "get_external_vs_internal_dependencies",
        "get_circular_imports",
        "detect_cyclic_dependencies",
        "get_unused_imports",
        "get_module_coupling_metrics",
        "get_module_cohesion_analysis",
        "get_package_structure",
        "get_module_dependency_graph",
        "traverse_dependency_graph",
    ],
    "symbol_level": [
        "get_function_parameter_analysis",
        "get_return_type_analysis",
        "get_function_complexity_metrics",
        "get_call_site_tracking",
        "get_async_function_detection",
        "get_function_overload_analysis",
        "get_inheritance_hierarchy",
        "analyze_class_inheritance",
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
        "detect_dead_symbols",
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
                        # Check if the metric method exists
                        if hasattr(self, metric) and callable(getattr(self, metric)):
                            progress.update(task, description=f"Analyzing {category} - {metric}...")
                            metric_result = getattr(self, metric)()
                            self.results["categories"][category][metric] = metric_result
                        else:
                            self.results["categories"][category][metric] = {"error": f"Method '{metric}' not implemented"}
                    except Exception as e:
                        self.console.print(f"[bold red]Error analyzing {metric}: {e}[/bold red]")
                        self.results["categories"][category][metric] = {"error": str(e)}

                    progress.update(task, advance=1)

        # Output the results
        if output_format == "json":
            if output_file:
                with open(output_file, "w") as f:
                    json.dump(self.results, f, indent=2)
                self.console.print(f"[bold green]Analysis results saved to {output_file}[/bold green]")
            else:
                return self.results
        elif output_format == "html":
            self._generate_html_report(output_file)
        elif output_format == "console":
            self._print_console_report()

        return self.results

    # ... [existing methods] ...

    def detect_dead_symbols(self) -> List[Dict[str, Any]]:
        """Detect symbols that are not used anywhere in the codebase.
        
        This function identifies symbols (functions, classes, variables) that are defined
        but not used anywhere in the codebase, which could be candidates for removal.
        
        Returns:
            List[Dict[str, Any]]: A list of dead symbol names with their locations
        """
        dead_symbols = []
        
        # Check all symbols in the codebase
        for symbol in self.codebase.symbols:
            # Skip imported symbols as they might be used outside the analyzed codebase
            if hasattr(symbol, "is_imported") and symbol.is_imported:
                continue
                
            # Check if the symbol has any usages
            if not symbol.usages:
                # Get file path if available
                file_path = getattr(symbol, "file", None)
                file_path = file_path.file_path if file_path else "Unknown"
                
                dead_symbols.append({
                    "name": symbol.name,
                    "type": symbol.__class__.__name__,
                    "file": file_path,
                    "line": getattr(symbol, "line", "Unknown")
                })
        
        return dead_symbols
    
    def analyze_symbol_imports(self, symbol_name: str = None) -> Dict[str, Any]:
        """Analyze all imports that a symbol uses.
        
        This function identifies all imports that a given symbol depends on,
        categorized by usage type (direct, indirect, chained, aliased).
        
        Args:
            symbol_name: Name of the symbol to analyze. If None, analyzes the first symbol found.
            
        Returns:
            Dict[str, Any]: A dictionary containing import analysis information
        """
        # If no symbol name provided, use the first symbol found
        if not symbol_name and self.codebase.symbols:
            symbol_name = next(iter(self.codebase.symbols)).name
            
        if not symbol_name:
            return {"error": "No symbol name provided and no symbols found in codebase"}
            
        result = {
            "symbol": symbol_name,
            "imports": {
                "direct": [],
                "indirect": [],
                "chained": [],
                "aliased": [],
                "all": []
            },
            "total_imports": 0
        }
        
        # Get the symbol
        symbol = self.codebase.get_symbol(symbol_name)
        if not symbol:
            return {"error": f"Symbol '{symbol_name}' not found"}
        
        # Analyze direct imports
        direct_deps = symbol.dependencies(UsageType.DIRECT)
        for dep in direct_deps:
            if hasattr(dep, "is_import") and dep.is_import:
                result["imports"]["direct"].append({
                    "name": dep.name,
                    "file": dep.file.file_path if hasattr(dep, "file") else "Unknown"
                })
        
        # Analyze indirect imports
        indirect_deps = symbol.dependencies(UsageType.INDIRECT)
        for dep in indirect_deps:
            if hasattr(dep, "is_import") and dep.is_import:
                result["imports"]["indirect"].append({
                    "name": dep.name,
                    "file": dep.file.file_path if hasattr(dep, "file") else "Unknown"
                })
        
        # Analyze chained imports
        chained_deps = symbol.dependencies(UsageType.CHAINED)
        for dep in chained_deps:
            if hasattr(dep, "is_import") and dep.is_import:
                result["imports"]["chained"].append({
                    "name": dep.name,
                    "file": dep.file.file_path if hasattr(dep, "file") else "Unknown"
                })
        
        # Analyze aliased imports
        aliased_deps = symbol.dependencies(UsageType.ALIASED)
        for dep in aliased_deps:
            if hasattr(dep, "is_import") and dep.is_import:
                result["imports"]["aliased"].append({
                    "name": dep.name,
                    "file": dep.file.file_path if hasattr(dep, "file") else "Unknown"
                })
        
        # Get all imports
        all_deps = symbol.dependencies(UsageType.DIRECT | UsageType.INDIRECT | 
                                      UsageType.CHAINED | UsageType.ALIASED)
        for dep in all_deps:
            if hasattr(dep, "is_import") and dep.is_import:
                result["imports"]["all"].append({
                    "name": dep.name,
                    "file": dep.file.file_path if hasattr(dep, "file") else "Unknown"
                })
        
        # Calculate totals
        result["total_imports"] = len(result["imports"]["all"])
        
        return result
    
    def traverse_dependency_graph(self, symbol_name: str = None, max_depth: int = 5) -> Dict[str, Any]:
        """Traverse the dependency graph starting from a symbol up to a specified depth.
        
        This function analyzes the dependency graph of a symbol, showing all dependencies
        up to a certain depth level, which helps understand complex dependency chains.
        
        Args:
            symbol_name: Name of the symbol to start traversal from. If None, uses the first symbol found.
            max_depth: Maximum depth to traverse (default: 5)
            
        Returns:
            Dict[str, Any]: A dictionary containing the dependency graph information
        """
        # If no symbol name provided, use the first symbol found
        if not symbol_name and self.codebase.symbols:
            symbol_name = next(iter(self.codebase.symbols)).name
            
        if not symbol_name:
            return {"error": "No symbol name provided and no symbols found in codebase"}
            
        result = {
            "symbol": symbol_name,
            "max_depth": max_depth,
            "dependency_graph": {},
            "dependency_counts": {},
            "total_dependencies": 0,
            "unique_dependencies": 0
        }
        
        # Get the symbol
        symbol = self.codebase.get_symbol(symbol_name)
        if not symbol:
            return {"error": f"Symbol '{symbol_name}' not found"}
        
        # Create a directed graph to track dependencies
        graph = nx.DiGraph()
        
        # Helper function to recursively traverse dependencies
        def traverse_deps(sym, current_depth=0, visited=None):
            if visited is None:
                visited = set()
                
            if current_depth > max_depth or sym.name in visited:
                return
                
            visited.add(sym.name)
            
            # Get direct dependencies
            direct_deps = sym.dependencies()
            dep_list = []
            
            for dep in direct_deps:
                dep_name = dep.name
                dep_list.append({
                    "name": dep_name,
                    "type": dep.__class__.__name__
                })
                
                # Add edge to graph
                graph.add_edge(sym.name, dep_name)
                
                # Recursively traverse dependencies
                traverse_deps(dep, current_depth + 1, visited)
            
            # Store dependencies for this symbol
            result["dependency_graph"][sym.name] = dep_list
        
        # Start traversal
        traverse_deps(symbol)
        
        # Calculate dependency counts
        for node in graph.nodes():
            result["dependency_counts"][node] = len(list(graph.successors(node)))
        
        # Calculate totals
        result["total_dependencies"] = graph.number_of_edges()
        result["unique_dependencies"] = graph.number_of_nodes() - 1  # Exclude the starting symbol
        
        # Check for cycles
        try:
            cycles = list(nx.simple_cycles(graph))
            result["has_cycles"] = len(cycles) > 0
            result["cycles"] = [list(cycle) for cycle in cycles]
        except nx.NetworkXNoCycle:
            result["has_cycles"] = False
            result["cycles"] = []
        
        return result
    
    def analyze_class_inheritance(self, class_name: str = None) -> Dict[str, Any]:
        """Analyze the inheritance hierarchy of a class.
        
        This function identifies all parent classes and subclasses of a given class,
        showing the complete inheritance hierarchy.
        
        Args:
            class_name: Name of the class to analyze. If None, uses the first class found.
            
        Returns:
            Dict[str, Any]: A dictionary containing inheritance hierarchy information
        """
        # If no class name provided, use the first class found
        if not class_name:
            for symbol in self.codebase.symbols:
                if hasattr(symbol, "is_class") and symbol.is_class:
                    class_name = symbol.name
                    break
                    
        if not class_name:
            return {"error": "No class name provided and no classes found in codebase"}
            
        result = {
            "class": class_name,
            "parents": [],
            "subclasses": [],
            "inheritance_depth": 0,
            "inheritance_chain": [],
            "multiple_inheritance": False
        }
        
        # Get the class
        cls = self.codebase.get_class(class_name)
        if not cls:
            return {"error": f"Class '{class_name}' not found"}
        
        # Get parent classes
        parent_classes = []
        if hasattr(cls, "bases"):
            for base in cls.bases:
                parent_classes.append({
                    "name": base.name,
                    "file": base.file.file_path if hasattr(base, "file") else "Unknown"
                })
        
        result["parents"] = parent_classes
        result["multiple_inheritance"] = len(parent_classes) > 1
        
        # Get subclasses
        subclasses = []
        for symbol in cls.usages:
            if hasattr(symbol, "is_class") and symbol.is_class:
                if hasattr(symbol, "bases") and any(base.name == class_name for base in symbol.bases):
                    subclasses.append({
                        "name": symbol.name,
                        "file": symbol.file.file_path if hasattr(symbol, "file") else "Unknown"
                    })
        
        result["subclasses"] = subclasses
        
        # Build inheritance chain
        inheritance_chain = [class_name]
        current_class = cls
        depth = 0
        
        while hasattr(current_class, "bases") and current_class.bases:
            # For simplicity, follow only the first parent in case of multiple inheritance
            parent = current_class.bases[0]
            inheritance_chain.append(parent.name)
            current_class = parent
            depth += 1
        
        result["inheritance_depth"] = depth
        result["inheritance_chain"] = inheritance_chain
        
        return result
    
    def detect_cyclic_dependencies(self) -> Dict[str, Any]:
        """Detect cyclic dependencies between symbols in the codebase.
        
        This function identifies circular dependencies between symbols, which can
        lead to maintenance issues and potential bugs.
        
        Returns:
            Dict[str, Any]: A dictionary containing cyclic dependency information
        """
        result = {
            "symbol_cycles": [],
            "module_cycles": [],
            "total_cycles": 0
        }
        
        # Create a directed graph to represent symbol dependencies
        symbol_graph = nx.DiGraph()
        
        # Create a directed graph to represent module dependencies
        module_graph = nx.DiGraph()
        
        # Build the dependency graphs
        for symbol in self.codebase.symbols:
            symbol_name = symbol.name
            
            # Skip symbols without a file (e.g., built-ins)
            if not hasattr(symbol, "file") or not symbol.file:
                continue
                
            module_name = symbol.file.file_path
            
            # Add nodes to graphs
            symbol_graph.add_node(symbol_name)
            module_graph.add_node(module_name)
            
            # Add edges for dependencies
            for dep in symbol.dependencies():
                if hasattr(dep, "name"):
                    symbol_graph.add_edge(symbol_name, dep.name)
                    
                    # Add module dependency if the dependent symbol is from a different file
                    if hasattr(dep, "file") and dep.file and dep.file.file_path != module_name:
                        module_graph.add_edge(module_name, dep.file.file_path)
        
        # Find cycles in symbol dependencies
        try:
            symbol_cycles = list(nx.simple_cycles(symbol_graph))
            # Filter out self-loops
            symbol_cycles = [cycle for cycle in symbol_cycles if len(cycle) > 1]
            
            for cycle in symbol_cycles:
                result["symbol_cycles"].append({
                    "symbols": cycle,
                    "length": len(cycle)
                })
        except nx.NetworkXNoCycle:
            pass
        
        # Find cycles in module dependencies
        try:
            module_cycles = list(nx.simple_cycles(module_graph))
            # Filter out self-loops
            module_cycles = [cycle for cycle in module_cycles if len(cycle) > 1]
            
            for cycle in module_cycles:
                result["module_cycles"].append({
                    "modules": cycle,
                    "length": len(cycle)
                })
        except nx.NetworkXNoCycle:
            pass
        
        # Calculate totals
        result["total_cycles"] = len(result["symbol_cycles"]) + len(result["module_cycles"])
        
        return result

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

    # Output options
    parser.add_argument("--output-format", choices=["json", "html", "console"], default="console", help="Output format")
    parser.add_argument("--output-file", help="Path to the output file")

    args = parser.parse_args()

    try:
        # Initialize the analyzer
        analyzer = CodebaseAnalyzer(repo_url=args.repo_url, repo_path=args.repo_path, language=args.language)

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

