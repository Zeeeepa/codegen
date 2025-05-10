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
from typing import Any, Dict, List, Optional

import networkx as nx
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

try:
    from codegen.configs.models.codebase import CodebaseConfig
    from codegen.configs.models.secrets import SecretsConfig
    from codegen.sdk.core.codebase import Codebase
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
        "visualize_component_tree",
        "visualize_inheritance_hierarchy",
        "visualize_module_dependencies",
        "analyze_function_modularity",
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
            task = progress.add_task("[bold green]Analyzing codebase...", total=len(categories))

            for category in categories:
                if category not in METRICS_CATEGORIES:
                    self.console.print(f"[bold yellow]Warning: Unknown category '{category}'. Skipping.[/bold yellow]")
                    progress.update(task, advance=1)
                    continue

                self.console.print(f"[bold blue]Analyzing {category}...[/bold blue]")

                # Get the metrics for this category
                metrics = METRICS_CATEGORIES[category]
                category_results = {}

                # Run each metric
                for metric in metrics:
                    try:
                        method = getattr(self, metric, None)
                        if method and callable(method):
                            result = method()
                            category_results[metric] = result
                        else:
                            category_results[metric] = {"error": f"Method {metric} not implemented"}
                    except Exception as e:
                        category_results[metric] = {"error": str(e)}

                # Add the results to the main results dictionary
                self.results["categories"][category] = category_results

                progress.update(task, advance=1)

        # Output the results
        if output_format == "json":
            if output_file:
                with open(output_file, "w") as f:
                    json.dump(self.results, f, indent=2)
                self.console.print(f"[bold green]Results saved to {output_file}[/bold green]")
            else:
                return self.results
        elif output_format == "html":
            self._generate_html_report(output_file)
        elif output_format == "console":
            self._print_console_report()

        return self.results

    #
    # Codebase Structure Analysis Methods
    #

    def get_file_count(self) -> dict[str, int]:
        """Get the total number of files in the codebase."""
        files = list(self.codebase.files)
        return {"total_files": len(files), "source_files": len([f for f in files if not f.is_binary])}

    def get_files_by_language(self) -> dict[str, int]:
        """Get the distribution of files by language/extension."""
        files = list(self.codebase.files)
        extensions = {}

        for file in files:
            if file.is_binary:
                continue

            ext = file.extension
            if not ext:
                ext = "(no extension)"

            if ext in extensions:
                extensions[ext] += 1
            else:
                extensions[ext] = 1

        return extensions

    def get_file_size_distribution(self) -> dict[str, int]:
        """Get the distribution of file sizes."""
        files = list(self.codebase.files)
        size_ranges = {"small (< 1KB)": 0, "medium (1KB - 10KB)": 0, "large (10KB - 100KB)": 0, "very large (> 100KB)": 0}

        for file in files:
            if file.is_binary:
                continue

            size = len(file.content)

            if size < 1024:
                size_ranges["small (< 1KB)"] += 1
            elif size < 10240:
                size_ranges["medium (1KB - 10KB)"] += 1
            elif size < 102400:
                size_ranges["large (10KB - 100KB)"] += 1
            else:
                size_ranges["very large (> 100KB)"] += 1

        return size_ranges

    def get_directory_structure(self) -> dict[str, Any]:
        """Get the directory structure of the codebase."""
        directories = {}

        for directory in self.codebase.directories:
            path = str(directory.path)
            parent_path = str(directory.path.parent) if directory.path.parent != self.codebase.repo_path else "/"

            if parent_path not in directories:
                directories[parent_path] = []

            directories[parent_path].append({"name": directory.path.name, "path": path, "files": len(directory.files), "subdirectories": len(directory.subdirectories)})

        return directories

    def get_symbol_count(self) -> dict[str, int]:
        """Get the total count of symbols in the codebase."""
        return {
            "total_symbols": len(list(self.codebase.symbols)),
            "classes": len(list(self.codebase.classes)),
            "functions": len(list(self.codebase.functions)),
            "global_vars": len(list(self.codebase.global_vars)),
            "interfaces": len(list(self.codebase.interfaces)),
        }

    def get_symbol_type_distribution(self) -> dict[str, int]:
        """Get the distribution of symbol types."""
        symbols = list(self.codebase.symbols)
        distribution = {}

        for symbol in symbols:
            symbol_type = str(symbol.symbol_type)

            if symbol_type in distribution:
                distribution[symbol_type] += 1
            else:
                distribution[symbol_type] = 1

        return distribution

    def get_symbol_hierarchy(self) -> dict[str, Any]:
        """Get the hierarchy of symbols in the codebase."""
        classes = list(self.codebase.classes)
        hierarchy = {}

        for cls in classes:
            class_name = cls.name
            parent_classes = []

            # Get parent classes if available
            if hasattr(cls, "parent_class_names"):
                parent_classes = cls.parent_class_names

            hierarchy[class_name] = {
                "parent_classes": parent_classes,
                "methods": [method.name for method in cls.methods],
                "attributes": [attr.name for attr in cls.attributes] if hasattr(cls, "attributes") else [],
            }

        return hierarchy

    def get_top_level_vs_nested_symbols(self) -> dict[str, int]:
        """Get the count of top-level vs nested symbols."""
        symbols = list(self.codebase.symbols)
        top_level = 0
        nested = 0

        for symbol in symbols:
            if hasattr(symbol, "is_top_level") and symbol.is_top_level:
                top_level += 1
            else:
                nested += 1

        return {"top_level": top_level, "nested": nested}

    def get_import_dependency_map(self) -> dict[str, list[str]]:
        """Get a map of import dependencies."""
        files = list(self.codebase.files)
        dependency_map = {}

        for file in files:
            if file.is_binary:
                continue

            file_path = file.file_path
            imports = []

            for imp in file.imports:
                if hasattr(imp, "imported_symbol") and imp.imported_symbol:
                    imported_symbol = imp.imported_symbol
                    if hasattr(imported_symbol, "file") and imported_symbol.file:
                        imports.append(imported_symbol.file.file_path)

            dependency_map[file_path] = imports

        return dependency_map

    def get_external_vs_internal_dependencies(self) -> dict[str, int]:
        """Get the count of external vs internal dependencies."""
        files = list(self.codebase.files)
        internal = 0
        external = 0

        for file in files:
            if file.is_binary:
                continue

            for imp in file.imports:
                if hasattr(imp, "imported_symbol") and imp.imported_symbol:
                    imported_symbol = imp.imported_symbol
                    if hasattr(imported_symbol, "file") and imported_symbol.file:
                        internal += 1
                    else:
                        external += 1
                else:
                    external += 1

        return {"internal": internal, "external": external}

    def get_circular_imports(self) -> list[list[str]]:
        """Detect circular imports in the codebase."""
        files = list(self.codebase.files)
        dependency_map = {}

        # Build dependency graph
        for file in files:
            if file.is_binary:
                continue

            file_path = file.file_path
            imports = []

            for imp in file.imports:
                if hasattr(imp, "imported_symbol") and imp.imported_symbol:
                    imported_symbol = imp.imported_symbol
                    if hasattr(imported_symbol, "file") and imported_symbol.file:
                        imports.append(imported_symbol.file.file_path)

            dependency_map[file_path] = imports

        # Create a directed graph
        G = nx.DiGraph()

        # Add nodes and edges
        for file_path, imports in dependency_map.items():
            G.add_node(file_path)
            for imp in imports:
                G.add_edge(file_path, imp)

        # Find cycles
        cycles = list(nx.simple_cycles(G))

        return cycles

    def get_unused_imports(self) -> list[dict[str, str]]:
        """Get a list of unused imports."""
        files = list(self.codebase.files)
        unused_imports = []

        for file in files:
            if file.is_binary:
                continue

            for imp in file.imports:
                if hasattr(imp, "usages") and len(imp.usages) == 0:
                    unused_imports.append({"file": file.file_path, "import": imp.source})

        return unused_imports

    def get_module_coupling_metrics(self) -> dict[str, float]:
        """Calculate module coupling metrics."""
        files = list(self.codebase.files)
        dependency_map = {}

        # Build dependency graph
        for file in files:
            if file.is_binary:
                continue

            file_path = file.file_path
            imports = []

            for imp in file.imports:
                if hasattr(imp, "imported_symbol") and imp.imported_symbol:
                    imported_symbol = imp.imported_symbol
                    if hasattr(imported_symbol, "file") and imported_symbol.file:
                        imports.append(imported_symbol.file.file_path)

            dependency_map[file_path] = imports

        # Calculate metrics
        total_files = len(dependency_map)
        total_dependencies = sum(len(deps) for deps in dependency_map.values())

        if total_files == 0:
            return {"average_dependencies_per_file": 0, "max_dependencies": 0, "coupling_factor": 0}

        max_dependencies = max(len(deps) for deps in dependency_map.values()) if dependency_map else 0
        coupling_factor = total_dependencies / (total_files * (total_files - 1)) if total_files > 1 else 0

        return {"average_dependencies_per_file": total_dependencies / total_files, "max_dependencies": max_dependencies, "coupling_factor": coupling_factor}

    def get_module_cohesion_analysis(self) -> dict[str, float]:
        """Analyze module cohesion."""
        files = list(self.codebase.files)
        cohesion_metrics = {}

        for file in files:
            if file.is_binary:
                continue

            symbols = list(file.symbols)
            total_symbols = len(symbols)

            if total_symbols <= 1:
                continue

            # Count internal references
            internal_refs = 0

            for symbol in symbols:
                if hasattr(symbol, "symbol_usages"):
                    for usage in symbol.symbol_usages:
                        if hasattr(usage, "file") and usage.file == file:
                            internal_refs += 1

            max_possible_refs = total_symbols * (total_symbols - 1)
            cohesion = internal_refs / max_possible_refs if max_possible_refs > 0 else 0

            cohesion_metrics[file.file_path] = cohesion

        # Calculate average cohesion
        if cohesion_metrics:
            avg_cohesion = sum(cohesion_metrics.values()) / len(cohesion_metrics)
        else:
            avg_cohesion = 0

        return {"average_cohesion": avg_cohesion, "file_cohesion": cohesion_metrics}

    def get_package_structure(self) -> dict[str, Any]:
        """Get the package structure of the codebase."""
        directories = {}

        for directory in self.codebase.directories:
            path = str(directory.path)
            parent_path = str(directory.path.parent) if directory.path.parent != self.codebase.repo_path else "/"

            if parent_path not in directories:
                directories[parent_path] = []

            # Check if this is a package (has __init__.py)
            is_package = any(f.name == "__init__.py" for f in directory.files)

            directories[parent_path].append({"name": directory.path.name, "path": path, "is_package": is_package, "files": len(directory.files), "subdirectories": len(directory.subdirectories)})

        return directories

    def get_module_dependency_graph(self) -> dict[str, list[str]]:
        """Get the module dependency graph."""
        files = list(self.codebase.files)
        dependency_graph = {}

        for file in files:
            if file.is_binary:
                continue

            file_path = file.file_path
            imports = []

            for imp in file.imports:
                if hasattr(imp, "imported_symbol") and imp.imported_symbol:
                    imported_symbol = imp.imported_symbol
                    if hasattr(imported_symbol, "file") and imported_symbol.file:
                        imports.append(imported_symbol.file.file_path)

            dependency_graph[file_path] = imports

        return dependency_graph

    #
    # Symbol-Level Analysis Methods
    #

    def get_function_parameter_analysis(self) -> dict[str, Any]:
        """Analyze function parameters."""
        functions = list(self.codebase.functions)
        parameter_stats = {
            "total_parameters": 0,
            "avg_parameters_per_function": 0,
            "functions_with_no_parameters": 0,
            "functions_with_many_parameters": 0,  # > 5 parameters
            "parameter_type_coverage": 0,
            "functions_with_default_params": 0,
        }

        if not functions:
            return parameter_stats

        total_params = 0
        functions_with_types = 0
        functions_with_defaults = 0

        for func in functions:
            params = func.parameters
            param_count = len(params)
            total_params += param_count

            if param_count == 0:
                parameter_stats["functions_with_no_parameters"] += 1
            elif param_count > 5:
                parameter_stats["functions_with_many_parameters"] += 1

            # Check for type annotations
            has_type_annotations = all(hasattr(p, "type") and p.type for p in params)
            if has_type_annotations:
                functions_with_types += 1

            # Check for default values
            has_defaults = any(hasattr(p, "default") and p.default for p in params)
            if has_defaults:
                functions_with_defaults += 1

        parameter_stats["total_parameters"] = total_params
        parameter_stats["avg_parameters_per_function"] = total_params / len(functions)
        parameter_stats["parameter_type_coverage"] = functions_with_types / len(functions) if functions else 0
        parameter_stats["functions_with_default_params"] = functions_with_defaults

        return parameter_stats

    def get_return_type_analysis(self) -> dict[str, Any]:
        """Analyze function return types."""
        functions = list(self.codebase.functions)
        return_type_stats = {"functions_with_return_type": 0, "return_type_coverage": 0, "common_return_types": {}}

        if not functions:
            return return_type_stats

        functions_with_return_type = 0
        return_types = {}

        for func in functions:
            if hasattr(func, "return_type") and func.return_type:
                functions_with_return_type += 1

                return_type = str(func.return_type.source) if hasattr(func.return_type, "source") else str(func.return_type)

                if return_type in return_types:
                    return_types[return_type] += 1
                else:
                    return_types[return_type] = 1

        return_type_stats["functions_with_return_type"] = functions_with_return_type
        return_type_stats["return_type_coverage"] = functions_with_return_type / len(functions)

        # Get the most common return types
        sorted_types = sorted(return_types.items(), key=lambda x: x[1], reverse=True)
        return_type_stats["common_return_types"] = dict(sorted_types[:10])  # Top 10 return types

        return return_type_stats

    def get_function_complexity_metrics(self) -> dict[str, Any]:
        """Calculate function complexity metrics."""
        functions = list(self.codebase.functions)
        complexity_metrics = {
            "avg_function_length": 0,
            "max_function_length": 0,
            "functions_by_complexity": {
                "simple": 0,  # < 10 lines
                "moderate": 0,  # 10-30 lines
                "complex": 0,  # 30-100 lines
                "very_complex": 0,  # > 100 lines
            },
        }

        if not functions:
            return complexity_metrics

        total_length = 0
        max_length = 0

        for func in functions:
            # Calculate function length in lines
            func_source = func.source
            func_lines = func_source.count("\n") + 1

            total_length += func_lines
            max_length = max(max_length, func_lines)

            # Categorize by complexity
            if func_lines < 10:
                complexity_metrics["functions_by_complexity"]["simple"] += 1
            elif func_lines < 30:
                complexity_metrics["functions_by_complexity"]["moderate"] += 1
            elif func_lines < 100:
                complexity_metrics["functions_by_complexity"]["complex"] += 1
            else:
                complexity_metrics["functions_by_complexity"]["very_complex"] += 1

        complexity_metrics["avg_function_length"] = total_length / len(functions)
        complexity_metrics["max_function_length"] = max_length

        return complexity_metrics

    def get_call_site_tracking(self) -> dict[str, Any]:
        """Track function call sites."""
        functions = list(self.codebase.functions)
        call_site_stats = {
            "functions_with_no_calls": 0,
            "functions_with_many_calls": 0,  # > 10 calls
            "avg_call_sites_per_function": 0,
            "most_called_functions": [],
        }

        if not functions:
            return call_site_stats

        function_calls = {}
        total_calls = 0

        for func in functions:
            if hasattr(func, "call_sites"):
                call_count = len(func.call_sites)
                total_calls += call_count

                if call_count == 0:
                    call_site_stats["functions_with_no_calls"] += 1
                elif call_count > 10:
                    call_site_stats["functions_with_many_calls"] += 1

                function_calls[func.name] = call_count

        call_site_stats["avg_call_sites_per_function"] = total_calls / len(functions)

        # Get the most called functions
        sorted_functions = sorted(function_calls.items(), key=lambda x: x[1], reverse=True)
        call_site_stats["most_called_functions"] = [{"name": name, "calls": calls} for name, calls in sorted_functions[:10]]

        return call_site_stats

    def get_async_function_detection(self) -> dict[str, Any]:
        """Detect async functions."""
        functions = list(self.codebase.functions)
        async_stats = {"total_async_functions": 0, "async_function_percentage": 0, "async_functions": []}

        if not functions:
            return async_stats

        async_functions = []

        for func in functions:
            if hasattr(func, "is_async") and func.is_async:
                async_functions.append({"name": func.name, "file": func.file.file_path if hasattr(func, "file") else "Unknown"})

        async_stats["total_async_functions"] = len(async_functions)
        async_stats["async_function_percentage"] = len(async_functions) / len(functions)
        async_stats["async_functions"] = async_functions

        return async_stats

    def get_function_overload_analysis(self) -> dict[str, Any]:
        """Analyze function overloads."""
        functions = list(self.codebase.functions)
        overload_stats = {"total_overloaded_functions": 0, "overloaded_function_percentage": 0, "overloaded_functions": []}

        if not functions:
            return overload_stats

        overloaded_functions = []
        function_names = {}

        for func in functions:
            name = func.name

            if name in function_names:
                function_names[name].append(func)
            else:
                function_names[name] = [func]

        for name, funcs in function_names.items():
            if len(funcs) > 1:
                overloaded_functions.append({"name": name, "overloads": len(funcs), "file": funcs[0].file.file_path if hasattr(funcs[0], "file") else "Unknown"})

        overload_stats["total_overloaded_functions"] = len(overloaded_functions)
        overload_stats["overloaded_function_percentage"] = len(overloaded_functions) / len(function_names) if function_names else 0
        overload_stats["overloaded_functions"] = overloaded_functions

        return overload_stats

    def get_inheritance_hierarchy(self) -> dict[str, Any]:
        """Get the inheritance hierarchy of classes."""
        classes = list(self.codebase.classes)
        hierarchy = {}

        for cls in classes:
            class_name = cls.name
            parent_classes = []

            # Get parent classes if available
            if hasattr(cls, "parent_class_names"):
                parent_classes = cls.parent_class_names

            hierarchy[class_name] = {"parent_classes": parent_classes, "file": cls.file.file_path if hasattr(cls, "file") else "Unknown"}

        # Build inheritance tree
        inheritance_tree = {}

        for class_name, info in hierarchy.items():
            if not info["parent_classes"]:
                if class_name not in inheritance_tree:
                    inheritance_tree[class_name] = []
            else:
                for parent in info["parent_classes"]:
                    if parent not in inheritance_tree:
                        inheritance_tree[parent] = []
                    inheritance_tree[parent].append(class_name)

        return {"class_hierarchy": hierarchy, "inheritance_tree": inheritance_tree}

    def get_method_analysis(self) -> dict[str, Any]:
        """Analyze class methods."""
        classes = list(self.codebase.classes)
        method_stats = {
            "total_methods": 0,
            "avg_methods_per_class": 0,
            "classes_with_no_methods": 0,
            "classes_with_many_methods": 0,  # > 10 methods
            "method_types": {"instance": 0, "static": 0, "class": 0, "property": 0},
        }

        if not classes:
            return method_stats

        total_methods = 0

        for cls in classes:
            methods = cls.methods if hasattr(cls, "methods") else []
            method_count = len(methods)
            total_methods += method_count

            if method_count == 0:
                method_stats["classes_with_no_methods"] += 1
            elif method_count > 10:
                method_stats["classes_with_many_methods"] += 1

            # Analyze method types
            for method in methods:
                if hasattr(method, "is_static") and method.is_static:
                    method_stats["method_types"]["static"] += 1
                elif hasattr(method, "is_class_method") and method.is_class_method:
                    method_stats["method_types"]["class"] += 1
                elif hasattr(method, "is_property") and method.is_property:
                    method_stats["method_types"]["property"] += 1
                else:
                    method_stats["method_types"]["instance"] += 1

        method_stats["total_methods"] = total_methods
        method_stats["avg_methods_per_class"] = total_methods / len(classes) if classes else 0

        return method_stats

    def get_attribute_analysis(self) -> dict[str, Any]:
        """Analyze class attributes."""
        classes = list(self.codebase.classes)
        attribute_stats = {
            "total_attributes": 0,
            "avg_attributes_per_class": 0,
            "classes_with_no_attributes": 0,
            "classes_with_many_attributes": 0,  # > 10 attributes
            "attribute_types": {},
        }

        if not classes:
            return attribute_stats

        total_attributes = 0
        attribute_types = {}

        for cls in classes:
            attributes = cls.attributes if hasattr(cls, "attributes") else []
            attr_count = len(attributes)
            total_attributes += attr_count

            if attr_count == 0:
                attribute_stats["classes_with_no_attributes"] += 1
            elif attr_count > 10:
                attribute_stats["classes_with_many_attributes"] += 1

            # Analyze attribute types
            for attr in attributes:
                if hasattr(attr, "type") and attr.type:
                    attr_type = str(attr.type.source) if hasattr(attr.type, "source") else str(attr.type)

                    if attr_type in attribute_types:
                        attribute_types[attr_type] += 1
                    else:
                        attribute_types[attr_type] = 1

        attribute_stats["total_attributes"] = total_attributes
        attribute_stats["avg_attributes_per_class"] = total_attributes / len(classes) if classes else 0
        attribute_stats["attribute_types"] = attribute_types

        return attribute_stats

    def get_constructor_analysis(self) -> dict[str, Any]:
        """Analyze class constructors."""
        classes = list(self.codebase.classes)
        constructor_stats = {"classes_with_constructor": 0, "constructor_percentage": 0, "avg_constructor_params": 0}

        if not classes:
            return constructor_stats

        classes_with_constructor = 0
        total_constructor_params = 0

        for cls in classes:
            constructor = None

            # Find constructor
            for method in cls.methods:
                if hasattr(method, "is_constructor") and method.is_constructor:
                    constructor = method
                    break

            if constructor:
                classes_with_constructor += 1
                param_count = len(constructor.parameters) if hasattr(constructor, "parameters") else 0
                total_constructor_params += param_count

        constructor_stats["classes_with_constructor"] = classes_with_constructor
        constructor_stats["constructor_percentage"] = classes_with_constructor / len(classes)
        constructor_stats["avg_constructor_params"] = total_constructor_params / classes_with_constructor if classes_with_constructor else 0

        return constructor_stats

    def get_interface_implementation_verification(self) -> dict[str, Any]:
        """Verify interface implementations."""
        classes = list(self.codebase.classes)
        interfaces = list(self.codebase.interfaces)
        implementation_stats = {"total_interfaces": len(interfaces), "classes_implementing_interfaces": 0, "interface_implementations": {}}

        if not interfaces or not classes:
            return implementation_stats

        # Map interfaces to implementing classes
        interface_implementations = {}

        for interface in interfaces:
            interface_name = interface.name
            implementing_classes = []

            for cls in classes:
                if hasattr(cls, "parent_class_names") and interface_name in cls.parent_class_names:
                    implementing_classes.append(cls.name)

            interface_implementations[interface_name] = implementing_classes

        # Count classes implementing interfaces
        classes_implementing = set()
        for implementers in interface_implementations.values():
            classes_implementing.update(implementers)

        implementation_stats["classes_implementing_interfaces"] = len(classes_implementing)
        implementation_stats["interface_implementations"] = interface_implementations

        return implementation_stats

    def get_access_modifier_usage(self) -> dict[str, Any]:
        """Analyze access modifier usage."""
        symbols = list(self.codebase.symbols)
        access_stats = {"public": 0, "private": 0, "protected": 0, "internal": 0, "unknown": 0}

        for symbol in symbols:
            if hasattr(symbol, "is_private") and symbol.is_private:
                access_stats["private"] += 1
            elif hasattr(symbol, "is_protected") and symbol.is_protected:
                access_stats["protected"] += 1
            elif hasattr(symbol, "is_internal") and symbol.is_internal:
                access_stats["internal"] += 1
            elif hasattr(symbol, "is_public") and symbol.is_public:
                access_stats["public"] += 1
            else:
                access_stats["unknown"] += 1

        return access_stats

    #
    # Code Quality Analysis Methods
    #

    def get_unused_functions(self) -> list[dict[str, str]]:
        """Get a list of unused functions."""
        functions = list(self.codebase.functions)
        unused_functions = []

        for func in functions:
            if hasattr(func, "call_sites") and len(func.call_sites) == 0:
                # Skip special methods like __init__, __str__, etc.
                if hasattr(func, "is_magic") and func.is_magic:
                    continue

                # Skip entry points and main functions
                if func.name in ["main", "__main__"]:
                    continue

                unused_functions.append({"name": func.name, "file": func.file.file_path if hasattr(func, "file") else "Unknown"})

        return unused_functions

    def get_unused_classes(self) -> list[dict[str, str]]:
        """Get a list of unused classes."""
        classes = list(self.codebase.classes)
        unused_classes = []

        for cls in classes:
            if hasattr(cls, "symbol_usages") and len(cls.symbol_usages) == 0:
                unused_classes.append({"name": cls.name, "file": cls.file.file_path if hasattr(cls, "file") else "Unknown"})

        return unused_classes

    def get_unused_variables(self) -> list[dict[str, str]]:
        """Get a list of unused variables."""
        global_vars = list(self.codebase.global_vars)
        unused_vars = []

        for var in global_vars:
            if hasattr(var, "symbol_usages") and len(var.symbol_usages) == 0:
                unused_vars.append({"name": var.name, "file": var.file.file_path if hasattr(var, "file") else "Unknown"})

        return unused_vars

    def get_unused_imports_analysis(self) -> list[dict[str, str]]:
        """Get a list of unused imports."""
        files = list(self.codebase.files)
        unused_imports = []

        for file in files:
            if file.is_binary:
                continue

            for imp in file.imports:
                if hasattr(imp, "usages") and len(imp.usages) == 0:
                    unused_imports.append({"file": file.file_path, "import": imp.source})

        return unused_imports

    def get_similar_function_detection(self) -> list[dict[str, Any]]:
        """Detect similar functions."""
        functions = list(self.codebase.functions)
        similar_functions = []

        # Group functions by name
        function_groups = {}

        for func in functions:
            name = func.name

            if name in function_groups:
                function_groups[name].append(func)
            else:
                function_groups[name] = [func]

        # Find similar functions
        for name, funcs in function_groups.items():
            if len(funcs) > 1:
                similar_functions.append({"name": name, "count": len(funcs), "files": [func.file.file_path if hasattr(func, "file") else "Unknown" for func in funcs]})

        return similar_functions

    def get_repeated_code_patterns(self) -> dict[str, Any]:
        """Detect repeated code patterns."""
        functions = list(self.codebase.functions)

        # This is a simplified implementation that looks for functions with similar structure
        # A more advanced implementation would use code clone detection algorithms

        # Group functions by length (in lines)
        functions_by_length = {}

        for func in functions:
            func_source = func.source
            func_lines = func_source.count("\n") + 1

            if func_lines in functions_by_length:
                functions_by_length[func_lines].append(func)
            else:
                functions_by_length[func_lines] = [func]

        # Find potential code clones (functions with same length)
        potential_clones = {}

        for length, funcs in functions_by_length.items():
            if len(funcs) > 1:
                potential_clones[length] = [func.name for func in funcs]

        return {"potential_code_clones": potential_clones}

    def get_refactoring_opportunities(self) -> dict[str, Any]:
        """Identify refactoring opportunities."""
        refactoring_opportunities = {"long_functions": [], "large_classes": [], "high_coupling_files": [], "low_cohesion_files": []}

        # Find long functions
        functions = list(self.codebase.functions)
        for func in functions:
            func_source = func.source
            func_lines = func_source.count("\n") + 1

            if func_lines > 50:  # Threshold for long functions
                refactoring_opportunities["long_functions"].append({"name": func.name, "file": func.file.file_path if hasattr(func, "file") else "Unknown", "lines": func_lines})

        # Find large classes
        classes = list(self.codebase.classes)
        for cls in classes:
            methods = cls.methods if hasattr(cls, "methods") else []
            attributes = cls.attributes if hasattr(cls, "attributes") else []

            if len(methods) + len(attributes) > 20:  # Threshold for large classes
                refactoring_opportunities["large_classes"].append(
                    {"name": cls.name, "file": cls.file.file_path if hasattr(cls, "file") else "Unknown", "methods": len(methods), "attributes": len(attributes)}
                )

        # Find high coupling files
        files = list(self.codebase.files)
        for file in files:
            if file.is_binary:
                continue

            imports = file.imports
            if len(imports) > 15:  # Threshold for high coupling
                refactoring_opportunities["high_coupling_files"].append({"file": file.file_path, "imports": len(imports)})

        # Find low cohesion files
        cohesion_metrics = self.get_module_cohesion_analysis()
        file_cohesion = cohesion_metrics.get("file_cohesion", {})

        for file_path, cohesion in file_cohesion.items():
            if cohesion < 0.3:  # Threshold for low cohesion
                refactoring_opportunities["low_cohesion_files"].append({"file": file_path, "cohesion": cohesion})

        return refactoring_opportunities

    def calculate_cyclomatic_complexity(self) -> dict[str, Any]:
        """Calculate cyclomatic complexity for functions."""
        functions = list(self.codebase.functions)
        complexity_results = {
            "avg_complexity": 0,
            "max_complexity": 0,
            "complexity_distribution": {
                "low": 0,  # 1-5
                "moderate": 0,  # 6-10
                "high": 0,  # 11-20
                "very_high": 0,  # > 20
            },
            "complex_functions": [],
        }

        if not functions:
            return complexity_results

        total_complexity = 0
        max_complexity = 0
        complex_functions = []

        for func in functions:
            # A simple approximation of cyclomatic complexity
            # In a real implementation, we would parse the AST and count decision points
            source = func.source

            # Count decision points
            if_count = source.count("if ") + source.count("elif ")
            for_count = source.count("for ")
            while_count = source.count("while ")
            case_count = source.count("case ") + source.count("switch ") + source.count("match ")
            catch_count = source.count("catch ") + source.count("except ")
            and_count = source.count(" && ") + source.count(" and ")
            or_count = source.count(" || ") + source.count(" or ")

            # Calculate complexity
            complexity = 1 + if_count + for_count + while_count + case_count + catch_count + and_count + or_count

            total_complexity += complexity
            max_complexity = max(max_complexity, complexity)

            # Categorize complexity
            if complexity <= 5:
                complexity_results["complexity_distribution"]["low"] += 1
            elif complexity <= 10:
                complexity_results["complexity_distribution"]["moderate"] += 1
            elif complexity <= 20:
                complexity_results["complexity_distribution"]["high"] += 1
            else:
                complexity_results["complexity_distribution"]["very_high"] += 1

            # Track complex functions
            if complexity > 10:
                complex_functions.append({"name": func.name, "file": func.file.file_path if hasattr(func, "file") else "Unknown", "complexity": complexity})

        complexity_results["avg_complexity"] = total_complexity / len(functions)
        complexity_results["max_complexity"] = max_complexity
        complexity_results["complex_functions"] = sorted(complex_functions, key=lambda x: x["complexity"], reverse=True)[:10]  # Top 10 most complex

        return complexity_results

    def cc_rank(self) -> dict[str, str]:
        """Rank the codebase based on cyclomatic complexity."""
        complexity_results = self.calculate_cyclomatic_complexity()
        avg_complexity = complexity_results["avg_complexity"]

        if avg_complexity < 5:
            rank = "A"
            description = "Excellent: Low complexity, highly maintainable code"
        elif avg_complexity < 10:
            rank = "B"
            description = "Good: Moderate complexity, maintainable code"
        elif avg_complexity < 15:
            rank = "C"
            description = "Fair: Moderate to high complexity, some maintenance challenges"
        elif avg_complexity < 20:
            rank = "D"
            description = "Poor: High complexity, difficult to maintain"
        else:
            rank = "F"
            description = "Very Poor: Very high complexity, extremely difficult to maintain"

        return {"rank": rank, "description": description, "avg_complexity": avg_complexity}

    def get_operators_and_operands(self) -> dict[str, Any]:
        """Get operators and operands for Halstead metrics."""
        files = list(self.codebase.files)

        # Define common operators
        operators = [
            "+",
            "-",
            "*",
            "/",
            "%",
            "=",
            "==",
            "!=",
            "<",
            ">",
            "<=",
            ">=",
            "&&",
            "||",
            "!",
            "&",
            "|",
            "^",
            "~",
            "<<",
            ">>",
            "++",
            "--",
            "+=",
            "-=",
            "*=",
            "/=",
            "%=",
            "&=",
            "|=",
            "^=",
            "<<=",
            ">>=",
        ]

        # Count operators and operands
        operator_count = {}
        operand_count = {}

        for file in files:
            if file.is_binary:
                continue

            content = file.content

            # Count operators
            for op in operators:
                count = content.count(op)
                if count > 0:
                    if op in operator_count:
                        operator_count[op] += count
                    else:
                        operator_count[op] = count

            # Simplified operand counting (this is a rough approximation)
            # In a real implementation, we would parse the AST and extract identifiers
            words = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", content)
            for word in words:
                if word not in [
                    "if",
                    "else",
                    "for",
                    "while",
                    "return",
                    "break",
                    "continue",
                    "class",
                    "def",
                    "function",
                    "import",
                    "from",
                    "as",
                    "try",
                    "except",
                    "finally",
                    "with",
                    "in",
                    "is",
                    "not",
                    "and",
                    "or",
                ]:
                    if word in operand_count:
                        operand_count[word] += 1
                    else:
                        operand_count[word] = 1

        return {
            "unique_operators": len(operator_count),
            "total_operators": sum(operator_count.values()),
            "unique_operands": len(operand_count),
            "total_operands": sum(operand_count.values()),
            "top_operators": dict(sorted(operator_count.items(), key=lambda x: x[1], reverse=True)[:10]),
            "top_operands": dict(sorted(operand_count.items(), key=lambda x: x[1], reverse=True)[:10]),
        }

    def calculate_halstead_volume(self) -> dict[str, float]:
        """Calculate Halstead volume metrics."""
        operators_and_operands = self.get_operators_and_operands()

        n1 = operators_and_operands["unique_operators"]
        n2 = operators_and_operands["unique_operands"]
        N1 = operators_and_operands["total_operators"]
        N2 = operators_and_operands["total_operands"]

        # Calculate Halstead metrics
        vocabulary = n1 + n2
        length = N1 + N2
        volume = length * math.log2(vocabulary) if vocabulary > 0 else 0
        difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
        effort = volume * difficulty
        time = effort / 18  # Time in seconds (18 is a constant from empirical studies)
        bugs = volume / 3000  # Estimated bugs (3000 is a constant from empirical studies)

        return {
            "vocabulary": vocabulary,
            "length": length,
            "volume": volume,
            "difficulty": difficulty,
            "effort": effort,
            "time": time,  # in seconds
            "bugs": bugs,
        }

    def count_lines(self) -> dict[str, int]:
        """Count lines of code."""
        files = list(self.codebase.files)

        total_lines = 0
        code_lines = 0
        comment_lines = 0
        blank_lines = 0

        for file in files:
            if file.is_binary:
                continue

            content = file.content
            lines = content.split("\n")

            total_lines += len(lines)

            for line in lines:
                line = line.strip()

                if not line:
                    blank_lines += 1
                elif line.startswith("#") or line.startswith("//") or line.startswith("/*") or line.startswith("*"):
                    comment_lines += 1
                else:
                    code_lines += 1

        return {"total_lines": total_lines, "code_lines": code_lines, "comment_lines": comment_lines, "blank_lines": blank_lines, "comment_ratio": comment_lines / code_lines if code_lines > 0 else 0}

    def calculate_maintainability_index(self) -> dict[str, float]:
        """Calculate maintainability index."""
        halstead = self.calculate_halstead_volume()
        complexity = self.calculate_cyclomatic_complexity()
        lines = self.count_lines()

        # Calculate maintainability index
        # MI = 171 - 5.2 * ln(V) - 0.23 * CC - 16.2 * ln(LOC)
        volume = halstead["volume"]
        avg_complexity = complexity["avg_complexity"]
        loc = lines["code_lines"]

        mi = 171 - 5.2 * math.log(volume) - 0.23 * avg_complexity - 16.2 * math.log(loc) if volume > 0 and loc > 0 else 0

        # Normalize to 0-100 scale
        normalized_mi = max(0, min(100, mi * 100 / 171))

        return {"maintainability_index": mi, "normalized_maintainability_index": normalized_mi}

    def get_maintainability_rank(self) -> dict[str, str]:
        """Rank the codebase based on maintainability index."""
        mi = self.calculate_maintainability_index()["normalized_maintainability_index"]

        if mi >= 85:
            rank = "A"
            description = "Highly maintainable"
        elif mi >= 65:
            rank = "B"
            description = "Maintainable"
        elif mi >= 40:
            rank = "C"
            description = "Moderately maintainable"
        elif mi >= 20:
            rank = "D"
            description = "Difficult to maintain"
        else:
            rank = "F"
            description = "Very difficult to maintain"

        return {"rank": rank, "description": description, "maintainability_index": mi}

    def get_cognitive_complexity(self) -> dict[str, Any]:
        """Calculate cognitive complexity for functions."""
        functions = list(self.codebase.functions)
        complexity_results = {
            "avg_complexity": 0,
            "max_complexity": 0,
            "complexity_distribution": {
                "low": 0,  # 0-5
                "moderate": 0,  # 6-10
                "high": 0,  # 11-20
                "very_high": 0,  # > 20
            },
            "complex_functions": [],
        }

        if not functions:
            return complexity_results

        total_complexity = 0
        max_complexity = 0
        complex_functions = []

        for func in functions:
            # A simple approximation of cognitive complexity
            # In a real implementation, we would parse the AST and analyze control flow
            source = func.source

            # Count decision points with nesting
            nesting_level = 0
            cognitive_complexity = 0

            lines = source.split("\n")
            for line in lines:
                line = line.strip()

                # Increase nesting level
                if re.search(r"\b(if|for|while|switch|case|catch|try)\b", line):
                    cognitive_complexity += 1 + nesting_level
                    nesting_level += 1

                # Decrease nesting level
                if line.startswith("}") or line.endswith(":"):
                    nesting_level = max(0, nesting_level - 1)

                # Add complexity for boolean operators
                cognitive_complexity += line.count(" && ") + line.count(" and ")
                cognitive_complexity += line.count(" || ") + line.count(" or ")

                # Add complexity for jumps
                if re.search(r"\b(break|continue|goto|return)\b", line):
                    cognitive_complexity += 1

            total_complexity += cognitive_complexity
            max_complexity = max(max_complexity, cognitive_complexity)

            # Categorize complexity
            if cognitive_complexity <= 5:
                complexity_results["complexity_distribution"]["low"] += 1
            elif cognitive_complexity <= 10:
                complexity_results["complexity_distribution"]["moderate"] += 1
            elif cognitive_complexity <= 20:
                complexity_results["complexity_distribution"]["high"] += 1
            else:
                complexity_results["complexity_distribution"]["very_high"] += 1

            # Track complex functions
            if cognitive_complexity > 10:
                complex_functions.append({"name": func.name, "file": func.file.file_path if hasattr(func, "file") else "Unknown", "complexity": cognitive_complexity})

        complexity_results["avg_complexity"] = total_complexity / len(functions)
        complexity_results["max_complexity"] = max_complexity
        complexity_results["complex_functions"] = sorted(complex_functions, key=lambda x: x["complexity"], reverse=True)[:10]  # Top 10 most complex

        return complexity_results

    def get_nesting_depth_analysis(self) -> dict[str, Any]:
        """Analyze nesting depth in functions."""
        functions = list(self.codebase.functions)
        nesting_results = {
            "avg_max_nesting": 0,
            "max_nesting": 0,
            "nesting_distribution": {
                "low": 0,  # 0-2
                "moderate": 0,  # 3-4
                "high": 0,  # 5-6
                "very_high": 0,  # > 6
            },
            "deeply_nested_functions": [],
        }

        if not functions:
            return nesting_results

        total_max_nesting = 0
        max_nesting_overall = 0
        deeply_nested_functions = []

        for func in functions:
            source = func.source
            lines = source.split("\n")

            max_nesting = 0
            current_nesting = 0

            for line in lines:
                line = line.strip()

                # Increase nesting level
                if re.search(r"\b(if|for|while|switch|case|catch|try)\b", line) and not line.startswith("}"):
                    current_nesting += 1
                    max_nesting = max(max_nesting, current_nesting)

                # Decrease nesting level
                if line.startswith("}"):
                    current_nesting = max(0, current_nesting - 1)

            total_max_nesting += max_nesting
            max_nesting_overall = max(max_nesting_overall, max_nesting)

            # Categorize nesting
            if max_nesting <= 2:
                nesting_results["nesting_distribution"]["low"] += 1
            elif max_nesting <= 4:
                nesting_results["nesting_distribution"]["moderate"] += 1
            elif max_nesting <= 6:
                nesting_results["nesting_distribution"]["high"] += 1
            else:
                nesting_results["nesting_distribution"]["very_high"] += 1

            # Track deeply nested functions
            if max_nesting > 4:
                deeply_nested_functions.append({"name": func.name, "file": func.file.file_path if hasattr(func, "file") else "Unknown", "max_nesting": max_nesting})

        nesting_results["avg_max_nesting"] = total_max_nesting / len(functions)
        nesting_results["max_nesting"] = max_nesting_overall
        nesting_results["deeply_nested_functions"] = sorted(deeply_nested_functions, key=lambda x: x["max_nesting"], reverse=True)[:10]  # Top 10 most nested

        return nesting_results

    def get_function_size_metrics(self) -> dict[str, Any]:
        """Get function size metrics."""
        functions = list(self.codebase.functions)
        size_metrics = {
            "avg_function_length": 0,
            "max_function_length": 0,
            "function_size_distribution": {
                "small": 0,  # < 10 lines
                "medium": 0,  # 10-30 lines
                "large": 0,  # 30-100 lines
                "very_large": 0,  # > 100 lines
            },
            "largest_functions": [],
        }

        if not functions:
            return size_metrics

        total_length = 0
        max_length = 0
        largest_functions = []

        for func in functions:
            func_source = func.source
            func_lines = func_source.count("\n") + 1

            total_length += func_lines
            max_length = max(max_length, func_lines)

            # Categorize by size
            if func_lines < 10:
                size_metrics["function_size_distribution"]["small"] += 1
            elif func_lines < 30:
                size_metrics["function_size_distribution"]["medium"] += 1
            elif func_lines < 100:
                size_metrics["function_size_distribution"]["large"] += 1
            else:
                size_metrics["function_size_distribution"]["very_large"] += 1

            # Track large functions
            if func_lines > 30:
                largest_functions.append({"name": func.name, "file": func.file.file_path if hasattr(func, "file") else "Unknown", "lines": func_lines})

        size_metrics["avg_function_length"] = total_length / len(functions)
        size_metrics["max_function_length"] = max_length
        size_metrics["largest_functions"] = sorted(largest_functions, key=lambda x: x["lines"], reverse=True)[:10]  # Top 10 largest

        return size_metrics

    #
    # Visualization and Output Methods
    #

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
"""
Visualization functions for codebase_analyzer.py

This module contains the implementation of visualization functions mentioned in the
codebase-visualization.mdx documentation but not yet implemented in codebase_analyzer.py.
"""

from typing import Dict, Any
import networkx as nx

    def visualize_component_tree(self, root_component: str) -> Dict[str, Any]:
    """Visualize the hierarchy of React components.
    
    This function creates a directed graph representing the hierarchy of React components,
    starting from a root component and traversing through its children.
    
    Args:
        root_component: The name of the root component to start visualization from
        
    Returns:
        A dictionary containing the component tree visualization data
    """
    result = {
        "nodes": [],
        "edges": [],
        "metadata": {
            "root_component": root_component,
            "component_count": 0,
            "max_depth": 0,
            "visualization_type": "component_tree"
        }
    }
    
    try:
        # Get the root component class
        root = None
        for cls in self.codebase.classes:
            if cls.name == root_component:
                root = cls
                break
                
        if not root:
            return {"error": f"Root component '{root_component}' not found"}
            
        # Create a directed graph
        graph = nx.DiGraph()
        
        # Track visited components to avoid cycles
        visited = set()
        
        # Track depth for metadata
        max_depth = 0
        
        def add_children(component, depth=0):
            nonlocal max_depth
            
            if depth > max_depth:
                max_depth = depth
                
            if component.name in visited:
                return
                
            visited.add(component.name)
            
            # Add the component as a node
            if component not in graph:
                graph.add_node(component)
                
            # Look for child components in the source code
            for usage in component.usages:
                # Check if the usage is within a React component
                if hasattr(usage, 'parent') and usage.parent and hasattr(usage.parent, 'bases'):
                    parent = usage.parent
                    if "Component" in parent.bases or "React.Component" in parent.bases:
                        if parent not in graph:
                            graph.add_node(parent)
                        graph.add_edge(component, parent)
                        add_children(parent, depth + 1)
        
        # Start building the tree from the root
        add_children(root)
        
        # Convert graph to result format
        for node in graph.nodes():
            result["nodes"].append({
                "id": node.name,
                "label": node.name,
                "file": node.file.file_path if hasattr(node, "file") else "Unknown"
            })
            
        for edge in graph.edges():
            result["edges"].append({
                "source": edge[0].name,
                "target": edge[1].name
            })
            
        # Update metadata
        result["metadata"]["component_count"] = len(graph.nodes())
        result["metadata"]["max_depth"] = max_depth
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

    def visualize_inheritance_hierarchy(self, base_class: str) -> Dict[str, Any]:
    """Visualize class inheritance hierarchies.
    
    This function creates a directed graph representing the inheritance hierarchy,
    starting from a base class and recursively adding all subclasses.
    
    Args:
        base_class: The name of the base class to start visualization from
        
    Returns:
        A dictionary containing the inheritance hierarchy visualization data
    """
    result = {
        "nodes": [],
        "edges": [],
        "metadata": {
            "base_class": base_class,
            "class_count": 0,
            "max_depth": 0,
            "visualization_type": "inheritance_hierarchy"
        }
    }
    
    try:
        # Get the base class
        base = None
        for cls in self.codebase.classes:
            if cls.name == base_class:
                base = cls
                break
                
        if not base:
            return {"error": f"Base class '{base_class}' not found"}
            
        # Create a directed graph
        graph = nx.DiGraph()
        
        # Track depth for metadata
        max_depth = 0
        
        def add_subclasses(cls, depth=0):
            nonlocal max_depth
            
            if depth > max_depth:
                max_depth = depth
            
            # Add the class as a node
            if cls not in graph:
                graph.add_node(cls)
            
            # Find all subclasses
            for subclass in self.codebase.classes:
                if hasattr(subclass, 'bases') and cls.name in subclass.bases:
                    if subclass not in graph:
                        graph.add_node(subclass)
                    graph.add_edge(cls, subclass)
                    add_subclasses(subclass, depth + 1)
        
        # Start building the hierarchy from the base class
        add_subclasses(base)
        
        # Convert graph to result format
        for node in graph.nodes():
            result["nodes"].append({
                "id": node.name,
                "label": node.name,
                "file": node.file.file_path if hasattr(node, "file") else "Unknown"
            })
            
        for edge in graph.edges():
            result["edges"].append({
                "source": edge[0].name,
                "target": edge[1].name
            })
            
        # Update metadata
        result["metadata"]["class_count"] = len(graph.nodes())
        result["metadata"]["max_depth"] = max_depth
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

    def visualize_module_dependencies(self, start_file: str) -> Dict[str, Any]:
    """Visualize dependencies between modules.
    
    This function creates a directed graph representing the dependencies between modules,
    starting from a specific file and following all import relationships.
    
    Args:
        start_file: The path to the file to start visualization from
        
    Returns:
        A dictionary containing the module dependency visualization data
    """
    result = {
        "nodes": [],
        "edges": [],
        "metadata": {
            "start_file": start_file,
            "module_count": 0,
            "external_dependencies": 0,
            "internal_dependencies": 0,
            "visualization_type": "module_dependencies"
        }
    }
    
    try:
        # Get the starting file
        file_obj = None
        for file in self.codebase.files:
            if file.file_path == start_file or file.file_path.endswith(start_file):
                file_obj = file
                break
                
        if not file_obj:
            return {"error": f"Start file '{start_file}' not found"}
            
        # Create a directed graph
        graph = nx.DiGraph()
        
        # Track visited files to avoid cycles
        visited = set()
        
        # Count internal and external dependencies
        internal_deps = 0
        external_deps = 0
        
        def add_imports(file):
            nonlocal internal_deps, external_deps
            
            if file.file_path in visited:
                return
                
            visited.add(file.file_path)
            
            # Add the file as a node
            if file not in graph:
                graph.add_node(file)
            
            # Process all imports in the file
            if hasattr(file, 'imports'):
                for imp in file.imports:
                    # Check if the import resolves to a file in the codebase
                    if hasattr(imp, 'resolved_symbol') and imp.resolved_symbol and hasattr(imp.resolved_symbol, 'file'):
                        target_file = imp.resolved_symbol.file
                        
                        # Skip if it's the same file
                        if target_file.file_path == file.file_path:
                            continue
                            
                        if target_file not in graph:
                            graph.add_node(target_file)
                            
                        # Add the dependency edge
                        graph.add_edge(file, target_file)
                        
                        # Count as internal dependency
                        internal_deps += 1
                        
                        # Recursively process the imported file
                        add_imports(target_file)
                    else:
                        # This is an external dependency
                        external_deps += 1
        
        # Start building the dependency graph from the start file
        add_imports(file_obj)
        
        # Convert graph to result format
        for node in graph.nodes():
            result["nodes"].append({
                "id": node.file_path,
                "label": node.file_path.split("/")[-1],
                "file_path": node.file_path
            })
            
        for edge in graph.edges():
            result["edges"].append({
                "source": edge[0].file_path,
                "target": edge[1].file_path
            })
            
        # Update metadata
        result["metadata"]["module_count"] = len(graph.nodes())
        result["metadata"]["internal_dependencies"] = internal_deps
        result["metadata"]["external_dependencies"] = external_deps
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

    def analyze_function_modularity(self) -> Dict[str, Any]:
    """Analyze function groupings by modularity.
    
    This function creates an undirected graph representing the relationships between functions
    based on shared dependencies, then applies community detection to identify modules.
    
    Returns:
        A dictionary containing the function modularity analysis data
    """
    result = {
        "modules": [],
        "function_count": 0,
        "module_count": 0,
        "modularity_score": 0.0,
        "visualization_type": "function_modularity"
    }
    
    try:
        # Get all functions
        functions = list(self.codebase.functions)
        
        if not functions:
            return {"error": "No functions found in the codebase"}
            
        # Create an undirected graph
        graph = nx.Graph()
        
        # Add all functions as nodes
        for func in functions:
            graph.add_node(func)
        
        # Connect functions based on shared dependencies
        for i, func1 in enumerate(functions):
            func1_deps = set()
            
            # Collect dependencies of func1
            if hasattr(func1, 'dependencies'):
                func1_deps = set(func1.dependencies)
            elif hasattr(func1, 'call_sites'):
                func1_deps = {call.resolved_symbol for call in func1.call_sites if call.resolved_symbol}
            
            for j in range(i + 1, len(functions)):
                func2 = functions[j]
                func2_deps = set()
                
                # Collect dependencies of func2
                if hasattr(func2, 'dependencies'):
                    func2_deps = set(func2.dependencies)
                elif hasattr(func2, 'call_sites'):
                    func2_deps = {call.resolved_symbol for call in func2.call_sites if call.resolved_symbol}
                
                # Calculate shared dependencies
                shared_deps = len(func1_deps.intersection(func2_deps))
                
                # Add edge if there are shared dependencies
                if shared_deps > 0:
                    graph.add_edge(func1, func2, weight=shared_deps)
        
        # Apply community detection to identify modules
        # Using Louvain method for community detection
        try:
            from community import best_partition
            partition = best_partition(graph)
        except ImportError:
            # Fallback to connected components if community detection is not available
            partition = {}
            for i, component in enumerate(nx.connected_components(graph)):
                for node in component:
                    partition[node] = i
        
        # Calculate modularity score
        try:
            modularity = nx.algorithms.community.modularity(graph, 
                                                          [list(nodes) for nodes in nx.community.label_propagation.asyn_lpa_communities(graph)])
        except:
            modularity = 0.0
        
        # Group functions by module
        modules = {}
        for func, module_id in partition.items():
            if module_id not in modules:
                modules[module_id] = []
            modules[module_id].append({
                "name": func.name,
                "file": func.file.file_path if hasattr(func, "file") else "Unknown"
            })
        
        # Convert modules to result format
        for module_id, funcs in modules.items():
            result["modules"].append({
                "id": module_id,
                "functions": funcs,
                "size": len(funcs)
            })
        
        # Update metadata
        result["function_count"] = len(functions)
        result["module_count"] = len(modules)
        result["modularity_score"] = modularity
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

