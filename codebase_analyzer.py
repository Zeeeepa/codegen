#!/usr/bin/env python3
"""
Comprehensive Codebase Analyzer

This module provides a complete static code analysis system using the Codegen SDK.
It analyzes a codebase and provides extensive information about its structure,
dependencies, code quality, and more.
"""

import os
import sys
import json
import time
import logging
import argparse
import tempfile
import datetime
import re
import math
import networkx as nx
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional, Union, Callable
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

try:
    from codegen.sdk.core.codebase import Codebase
    from codegen.configs.models.codebase import CodebaseConfig
    from codegen.configs.models.secrets import SecretsConfig
    from codegen.shared.enums.programming_language import ProgrammingLanguage
except ImportError:
    print("Codegen SDK not found. Please install it first.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
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
        "get_dependency_graph_creation",  # Added new function
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
        "get_type_resolution",  # Added new function
        "get_generic_type_analysis",  # Added new function
        "get_union_type_analysis",  # Added new function
        "get_comprehensive_type_coverage_analysis",  # Added new function
        "get_enhanced_return_type_analysis",  # Added new function
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
        "get_path_finding_in_call_graphs",  # Added new function
        "get_dead_symbol_detection",  # Added new function
        "get_dependency_graph_traversal",  # Added new function
        "get_dead_code_detection_with_filtering",  # Added new function
        "get_unused_variable_detection",  # Added new function
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
        "get_circular_dependency_breaking",  # Added new function
        "get_module_coupling_analysis",  # Added new function
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
    ]
}


class CodebaseAnalyzer:
    """
    Comprehensive codebase analyzer using Codegen SDK.
    
    This class provides methods to analyze a codebase and extract detailed information
    about its structure, dependencies, code quality, and more.
    """
    
    def __init__(self, repo_url: str = None, repo_path: str = None, language: str = None):
        """
        Initialize the CodebaseAnalyzer.
        
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
    
    def _init_from_url(self, repo_url: str, language: str = None):
        """Initialize codebase from a repository URL."""
        try:
            # Extract owner and repo name from URL
            if repo_url.endswith('.git'):
                repo_url = repo_url[:-4]
            
            parts = repo_url.rstrip('/').split('/')
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
            
            self.codebase = Codebase.from_github(
                repo_full_name=repo_full_name,
                tmp_dir=tmp_dir,
                language=prog_lang,
                config=config,
                secrets=secrets,
                full_history=True
            )
            
            self.console.print(f"[bold green]Successfully initialized codebase from {repo_url}[/bold green]")
            
        except Exception as e:
            self.console.print(f"[bold red]Error initializing codebase from URL: {e}[/bold red]")
            raise
    
    def _init_from_path(self, repo_path: str, language: str = None):
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
            
            self.codebase = Codebase(
                repo_path=repo_path,
                language=prog_lang,
                config=config,
                secrets=secrets
            )
            
            self.console.print(f"[bold green]Successfully initialized codebase from {repo_path}[/bold green]")
            
        except Exception as e:
            self.console.print(f"[bold red]Error initializing codebase from path: {e}[/bold red]")
            raise
    
    def analyze(self, categories: List[str] = None, output_format: str = "json", output_file: str = None):
        """
        Perform a comprehensive analysis of the codebase.
        
        Args:
            categories: List of categories to analyze. If None, all categories are analyzed.
            output_format: Format of the output (json, html, console)
            output_file: Path to the output file
            
        Returns:
            Dict containing the analysis results
        """
        if not self.codebase:
            raise ValueError("Codebase not initialized. Please initialize the codebase first.")
        
        # If no categories specified, analyze all
        if not categories:
            categories = list(METRICS_CATEGORIES.keys())
        
        # Initialize results dictionary
        self.results = {
            "metadata": {
                "repo_name": self.codebase.ctx.repo_name,
                "analysis_time": datetime.datetime.now().isoformat(),
                "language": str(self.codebase.ctx.programming_language),
            },
            "categories": {}
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
                with open(output_file, 'w') as f:
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
    
    def get_file_count(self) -> Dict[str, int]:
        """Get the total number of files in the codebase."""
        files = list(self.codebase.files)
        return {
            "total_files": len(files),
            "source_files": len([f for f in files if not f.is_binary])
        }
    
    def get_files_by_language(self) -> Dict[str, int]:
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
    
    def get_file_size_distribution(self) -> Dict[str, int]:
        """Get the distribution of file sizes."""
        files = list(self.codebase.files)
        size_ranges = {
            "small (< 1KB)": 0,
            "medium (1KB - 10KB)": 0,
            "large (10KB - 100KB)": 0,
            "very large (> 100KB)": 0
        }
        
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
    
    def get_directory_structure(self) -> Dict[str, Any]:
        """Get the directory structure of the codebase."""
        directories = {}
        
        for directory in self.codebase.directories:
            path = str(directory.path)
            parent_path = str(directory.path.parent) if directory.path.parent != self.codebase.repo_path else "/"
            
            if parent_path not in directories:
                directories[parent_path] = []
            
            directories[parent_path].append({
                "name": directory.path.name,
                "path": path,
                "files": len(directory.files),
                "subdirectories": len(directory.subdirectories)
            })
        
        return directories
    
    def get_symbol_count(self) -> Dict[str, int]:
        """Get the total count of symbols in the codebase."""
        return {
            "total_symbols": len(list(self.codebase.symbols)),
            "classes": len(list(self.codebase.classes)),
            "functions": len(list(self.codebase.functions)),
            "global_vars": len(list(self.codebase.global_vars)),
            "interfaces": len(list(self.codebase.interfaces))
        }
    
    def get_symbol_type_distribution(self) -> Dict[str, int]:
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
    
    def get_symbol_hierarchy(self) -> Dict[str, Any]:
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
                "attributes": [attr.name for attr in cls.attributes] if hasattr(cls, "attributes") else []
            }
        
        return hierarchy
    
    def get_top_level_vs_nested_symbols(self) -> Dict[str, int]:
        """Get the count of top-level vs nested symbols."""
        symbols = list(self.codebase.symbols)
        top_level = 0
        nested = 0
        
        for symbol in symbols:
            if hasattr(symbol, "is_top_level") and symbol.is_top_level:
                top_level += 1
            else:
                nested += 1
        
        return {
            "top_level": top_level,
            "nested": nested
        }
    
    def get_import_dependency_map(self) -> Dict[str, List[str]]:
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
    
    def get_external_vs_internal_dependencies(self) -> Dict[str, int]:
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
        
        return {
            "internal": internal,
            "external": external
        }
    
    def get_circular_imports(self) -> List[List[str]]:
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
    
    def get_unused_imports(self) -> List[Dict[str, str]]:
        """Get a list of unused imports."""
        files = list(self.codebase.files)
        unused_imports = []
        
        for file in files:
            if file.is_binary:
                continue
            
            for imp in file.imports:
                if hasattr(imp, "usages") and len(imp.usages) == 0:
                    unused_imports.append({
                        "file": file.file_path,
                        "import": imp.source
                    })
        
        return unused_imports
    
    def get_module_coupling_metrics(self) -> Dict[str, float]:
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
            return {
                "average_dependencies_per_file": 0,
                "max_dependencies": 0,
                "coupling_factor": 0
            }
        
        max_dependencies = max(len(deps) for deps in dependency_map.values()) if dependency_map else 0
        coupling_factor = total_dependencies / (total_files * (total_files - 1)) if total_files > 1 else 0
        
        return {
            "average_dependencies_per_file": total_dependencies / total_files,
            "max_dependencies": max_dependencies,
            "coupling_factor": coupling_factor
        }
    
    def get_module_cohesion_analysis(self) -> Dict[str, float]:
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
        
        return {
            "average_cohesion": avg_cohesion,
            "file_cohesion": cohesion_metrics
        }
    
    def get_package_structure(self) -> Dict[str, Any]:
        """Get the package structure of the codebase."""
        directories = {}
        
        for directory in self.codebase.directories:
            path = str(directory.path)
            parent_path = str(directory.path.parent) if directory.path.parent != self.codebase.repo_path else "/"
            
            if parent_path not in directories:
                directories[parent_path] = []
            
            # Check if this is a package (has __init__.py)
            is_package = any(f.name == "__init__.py" for f in directory.files)
            
            directories[parent_path].append({
                "name": directory.path.name,
                "path": path,
                "is_package": is_package,
                "files": len(directory.files),
                "subdirectories": len(directory.subdirectories)
            })
        
        return directories
    
    def get_module_dependency_graph(self) -> Dict[str, List[str]]:
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
    
    def get_function_parameter_analysis(self) -> Dict[str, Any]:
        """Analyze function parameters."""
        functions = list(self.codebase.functions)
        parameter_stats = {
            "total_parameters": 0,
            "avg_parameters_per_function": 0,
            "functions_with_no_parameters": 0,
            "functions_with_many_parameters": 0,  # > 5 parameters
            "parameter_type_coverage": 0,
            "functions_with_default_params": 0
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
    
    def get_return_type_analysis(self) -> Dict[str, Any]:
        """Analyze function return types."""
        functions = list(self.codebase.functions)
        return_type_stats = {
            "functions_with_return_type": 0,
            "return_type_coverage": 0,
            "common_return_types": {}
        }
        
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
    
    def get_function_complexity_metrics(self) -> Dict[str, Any]:
        """Calculate function complexity metrics."""
        functions = list(self.codebase.functions)
        complexity_metrics = {
            "avg_function_length": 0,
            "max_function_length": 0,
            "functions_by_complexity": {
                "simple": 0,      # < 10 lines
                "moderate": 0,    # 10-30 lines
                "complex": 0,     # 30-100 lines
                "very_complex": 0 # > 100 lines
            }
        }
        
        if not functions:
            return complexity_metrics
        
        total_length = 0
        max_length = 0
        
        for func in functions:
            # Calculate function length in lines
            func_source = func.source
            func_lines = func_source.count('\n') + 1
            
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
    
    def get_call_site_tracking(self) -> Dict[str, Any]:
        """Track function call sites."""
        functions = list(self.codebase.functions)
        call_site_stats = {
            "functions_with_no_calls": 0,
            "functions_with_many_calls": 0,  # > 10 calls
            "avg_call_sites_per_function": 0,
            "most_called_functions": []
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
    
    def get_async_function_detection(self) -> Dict[str, Any]:
        """Detect async functions."""
        functions = list(self.codebase.functions)
        async_stats = {
            "total_async_functions": 0,
            "async_function_percentage": 0,
            "async_functions": []
        }
        
        if not functions:
            return async_stats
        
        async_functions = []
        
        for func in functions:
            if hasattr(func, "is_async") and func.is_async:
                async_functions.append({
                    "name": func.name,
                    "file": func.file.file_path if hasattr(func, "file") else "Unknown"
                })
        
        async_stats["total_async_functions"] = len(async_functions)
        async_stats["async_function_percentage"] = len(async_functions) / len(functions)
        async_stats["async_functions"] = async_functions
        
        return async_stats
    
    def get_function_overload_analysis(self) -> Dict[str, Any]:
        """Analyze function overloads."""
        functions = list(self.codebase.functions)
        overload_stats = {
            "total_overloaded_functions": 0,
            "overloaded_function_percentage": 0,
            "overloaded_functions": []
        }
        
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
                overloaded_functions.append({
                    "name": name,
                    "overloads": len(funcs),
                    "file": funcs[0].file.file_path if hasattr(funcs[0], "file") else "Unknown"
                })
        
        overload_stats["total_overloaded_functions"] = len(overloaded_functions)
        overload_stats["overloaded_function_percentage"] = len(overloaded_functions) / len(function_names) if function_names else 0
        overload_stats["overloaded_functions"] = overloaded_functions
        
        return overload_stats
    
    def get_inheritance_hierarchy(self) -> Dict[str, Any]:
        """Get the inheritance hierarchy of classes."""
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
                "file": cls.file.file_path if hasattr(cls, "file") else "Unknown"
            }
        
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
        
        return {
            "class_hierarchy": hierarchy,
            "inheritance_tree": inheritance_tree
        }
    
    def get_method_analysis(self) -> Dict[str, Any]:
        """Analyze class methods."""
        classes = list(self.codebase.classes)
        method_stats = {
            "total_methods": 0,
            "avg_methods_per_class": 0,
            "classes_with_no_methods": 0,
            "classes_with_many_methods": 0,  # > 10 methods
            "method_types": {
                "instance": 0,
                "static": 0,
                "class": 0,
                "property": 0
            }
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
    
    def get_attribute_analysis(self) -> Dict[str, Any]:
        """Analyze class attributes."""
        classes = list(self.codebase.classes)
        attribute_stats = {
            "total_attributes": 0,
            "avg_attributes_per_class": 0,
            "classes_with_no_attributes": 0,
            "classes_with_many_attributes": 0,  # > 10 attributes
            "attribute_types": {}
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
    
    def get_constructor_analysis(self) -> Dict[str, Any]:
        """Analyze class constructors."""
        classes = list(self.codebase.classes)
        constructor_stats = {
            "classes_with_constructor": 0,
            "constructor_percentage": 0,
            "avg_constructor_params": 0
        }
        
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
    
    def get_interface_implementation_verification(self) -> Dict[str, Any]:
        """Verify interface implementations."""
        classes = list(self.codebase.classes)
        interfaces = list(self.codebase.interfaces)
        implementation_stats = {
            "total_interfaces": len(interfaces),
            "classes_implementing_interfaces": 0,
            "interface_implementations": {}
        }
        
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
    
    def get_access_modifier_usage(self) -> Dict[str, Any]:
        """Analyze access modifier usage."""
        symbols = list(self.codebase.symbols)
        access_stats = {
            "public": 0,
            "private": 0,
            "protected": 0,
            "internal": 0,
            "unknown": 0
        }
        
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
    
    def get_unused_functions(self) -> List[Dict[str, str]]:
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
                
                unused_functions.append({
                    "name": func.name,
                    "file": func.file.file_path if hasattr(func, "file") else "Unknown"
                })
        
        return unused_functions
    
    def get_unused_classes(self) -> List[Dict[str, str]]:
        """Get a list of unused classes."""
        classes = list(self.codebase.classes)
        unused_classes = []
        
        for cls in classes:
            if hasattr(cls, "symbol_usages") and len(cls.symbol_usages) == 0:
                unused_classes.append({
                    "name": cls.name,
                    "file": cls.file.file_path if hasattr(cls, "file") else "Unknown"
                })
        
        return unused_classes
    
    def get_unused_variables(self) -> List[Dict[str, str]]:
        """Get a list of unused variables."""
        global_vars = list(self.codebase.global_vars)
        unused_vars = []
        
        for var in global_vars:
            if hasattr(var, "symbol_usages") and len(var.symbol_usages) == 0:
                unused_vars.append({
                    "name": var.name,
                    "file": var.file.file_path if hasattr(var, "file") else "Unknown"
                })
        
        return unused_vars
    
    def get_unused_imports(self) -> List[Dict[str, str]]:
        """Get a list of unused imports."""
        files = list(self.codebase.files)
        unused_imports = []
        
        for file in files:
            if file.is_binary:
                continue
            
            for imp in file.imports:
                if hasattr(imp, "usages") and len(imp.usages) == 0:
                    unused_imports.append({
                        "file": file.file_path,
                        "import": imp.source
                    })
        
        return unused_imports
    
    def get_similar_function_detection(self) -> List[Dict[str, Any]]:
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
                similar_functions.append({
                    "name": name,
                    "count": len(funcs),
                    "files": [func.file.file_path if hasattr(func, "file") else "Unknown" for func in funcs]
                })
        
        return similar_functions
    
    def get_repeated_code_patterns(self) -> Dict[str, Any]:
        """Detect repeated code patterns."""
        functions = list(self.codebase.functions)
        
        # This is a simplified implementation that looks for functions with similar structure
        # A more advanced implementation would use code clone detection algorithms
        
        # Group functions by length (in lines)
        functions_by_length = {}
        
        for func in functions:
            func_source = func.source
            func_lines = func_source.count('\n') + 1
            
            if func_lines in functions_by_length:
                functions_by_length[func_lines].append(func)
            else:
                functions_by_length[func_lines] = [func]
        
        # Find potential code clones (functions with same length)
        potential_clones = {}
        
        for length, funcs in functions_by_length.items():
            if len(funcs) > 1:
                potential_clones[length] = [func.name for func in funcs]
        
        return {
            "potential_code_clones": potential_clones
        }
    
    def get_refactoring_opportunities(self) -> Dict[str, Any]:
        """Identify refactoring opportunities."""
        refactoring_opportunities = {
            "long_functions": [],
            "large_classes": [],
            "high_coupling_files": [],
            "low_cohesion_files": []
        }
        
        # Find long functions
        functions = list(self.codebase.functions)
        for func in functions:
            func_source = func.source
            func_lines = func_source.count('\n') + 1
            
            if func_lines > 50:  # Threshold for long functions
                refactoring_opportunities["long_functions"].append({
                    "name": func.name,
                    "file": func.file.file_path if hasattr(func, "file") else "Unknown",
                    "lines": func_lines
                })
        
        # Find large classes
        classes = list(self.codebase.classes)
        for cls in classes:
            methods = cls.methods if hasattr(cls, "methods") else []
            attributes = cls.attributes if hasattr(cls, "attributes") else []
            
            if len(methods) + len(attributes) > 20:  # Threshold for large classes
                refactoring_opportunities["large_classes"].append({
                    "name": cls.name,
                    "file": cls.file.file_path if hasattr(cls, "file") else "Unknown",
                    "methods": len(methods),
                    "attributes": len(attributes)
                })
        
        # Find high coupling files
        files = list(self.codebase.files)
        for file in files:
            if file.is_binary:
                continue
            
            imports = file.imports
            if len(imports) > 15:  # Threshold for high coupling
                refactoring_opportunities["high_coupling_files"].append({
                    "file": file.file_path,
                    "imports": len(imports)
                })
        
        # Find low cohesion files
        cohesion_metrics = self.get_module_cohesion_analysis()
        file_cohesion = cohesion_metrics.get("file_cohesion", {})
        
        for file_path, cohesion in file_cohesion.items():
            if cohesion < 0.3:  # Threshold for low cohesion
                refactoring_opportunities["low_cohesion_files"].append({
                    "file": file_path,
                    "cohesion": cohesion
                })
        
        return refactoring_opportunities
    
    def calculate_cyclomatic_complexity(self) -> Dict[str, Any]:
        """Calculate cyclomatic complexity for functions."""
        functions = list(self.codebase.functions)
        complexity_results = {
            "avg_complexity": 0,
            "max_complexity": 0,
            "complexity_distribution": {
                "low": 0,      # 1-5
                "moderate": 0, # 6-10
                "high": 0,     # 11-20
                "very_high": 0 # > 20
            },
            "complex_functions": []
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
                complex_functions.append({
                    "name": func.name,
                    "file": func.file.file_path if hasattr(func, "file") else "Unknown",
                    "complexity": complexity
                })
        
        complexity_results["avg_complexity"] = total_complexity / len(functions)
        complexity_results["max_complexity"] = max_complexity
        complexity_results["complex_functions"] = sorted(complex_functions, key=lambda x: x["complexity"], reverse=True)[:10]  # Top 10 most complex
        
        return complexity_results
    
    def cc_rank(self) -> Dict[str, str]:
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
        
        return {
            "rank": rank,
            "description": description,
            "avg_complexity": avg_complexity
        }
    
    def get_operators_and_operands(self) -> Dict[str, Any]:
        """Get operators and operands for Halstead metrics."""
        files = list(self.codebase.files)
        
        # Define common operators
        operators = ["+", "-", "*", "/", "%", "=", "==", "!=", "<", ">", "<=", ">=", 
                    "&&", "||", "!", "&", "|", "^", "~", "<<", ">>", "++", "--", 
                    "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>="]
        
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
            words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content)
            for word in words:
                if word not in ["if", "else", "for", "while", "return", "break", "continue", 
                               "class", "def", "function", "import", "from", "as", "try", 
                               "except", "finally", "with", "in", "is", "not", "and", "or"]:
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
            "top_operands": dict(sorted(operand_count.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def calculate_halstead_volume(self) -> Dict[str, float]:
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
            "bugs": bugs
        }
    
    def count_lines(self) -> Dict[str, int]:
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
            lines = content.split('\n')
            
            total_lines += len(lines)
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    blank_lines += 1
                elif line.startswith('#') or line.startswith('//') or line.startswith('/*') or line.startswith('*'):
                    comment_lines += 1
                else:
                    code_lines += 1
        
        return {
            "total_lines": total_lines,
            "code_lines": code_lines,
            "comment_lines": comment_lines,
            "blank_lines": blank_lines,
            "comment_ratio": comment_lines / code_lines if code_lines > 0 else 0
        }
    
    def calculate_maintainability_index(self) -> Dict[str, float]:
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
        
        return {
            "maintainability_index": mi,
            "normalized_maintainability_index": normalized_mi
        }
    
    def get_maintainability_rank(self) -> Dict[str, str]:
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
        
        return {
            "rank": rank,
            "description": description,
            "maintainability_index": mi
        }
    
    def get_cognitive_complexity(self) -> Dict[str, Any]:
        """Calculate cognitive complexity for functions."""
        functions = list(self.codebase.functions)
        complexity_results = {
            "avg_complexity": 0,
            "max_complexity": 0,
            "complexity_distribution": {
                "low": 0,      # 0-5
                "moderate": 0, # 6-10
                "high": 0,     # 11-20
                "very_high": 0 # > 20
            },
            "complex_functions": []
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
            
            lines = source.split('\n')
            for line in lines:
                line = line.strip()
                
                # Increase nesting level
                if re.search(r'\b(if|for|while|switch|case|catch|try)\b', line):
                    cognitive_complexity += 1 + nesting_level
                    nesting_level += 1
                
                # Decrease nesting level
                if line.startswith('}') or line.endswith(':'):
                    nesting_level = max(0, nesting_level - 1)
                
                # Add complexity for boolean operators
                cognitive_complexity += line.count(" && ") + line.count(" and ")
                cognitive_complexity += line.count(" || ") + line.count(" or ")
                
                # Add complexity for jumps
                if re.search(r'\b(break|continue|goto|return)\b', line):
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
                complex_functions.append({
                    "name": func.name,
                    "file": func.file.file_path if hasattr(func, "file") else "Unknown",
                    "complexity": cognitive_complexity
                })
        
        complexity_results["avg_complexity"] = total_complexity / len(functions)
        complexity_results["max_complexity"] = max_complexity
        complexity_results["complex_functions"] = sorted(complex_functions, key=lambda x: x["complexity"], reverse=True)[:10]  # Top 10 most complex
        
        return complexity_results
    
    def get_nesting_depth_analysis(self) -> Dict[str, Any]:
        """Analyze nesting depth in functions."""
        functions = list(self.codebase.functions)
        nesting_results = {
            "avg_max_nesting": 0,
            "max_nesting": 0,
            "nesting_distribution": {
                "low": 0,      # 0-2
                "moderate": 0, # 3-4
                "high": 0,     # 5-6
                "very_high": 0 # > 6
            },
            "deeply_nested_functions": []
        }
        
        if not functions:
            return nesting_results
        
        total_max_nesting = 0
        max_nesting_overall = 0
        deeply_nested_functions = []
        
        for func in functions:
            source = func.source
            lines = source.split('\n')
            
            max_nesting = 0
            current_nesting = 0
            
            for line in lines:
                line = line.strip()
                
                # Increase nesting level
                if re.search(r'\b(if|for|while|switch|case|catch|try)\b', line) and not line.startswith('}'):
                    current_nesting += 1
                    max_nesting = max(max_nesting, current_nesting)
                
                # Decrease nesting level
                if line.startswith('}'):
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
                deeply_nested_functions.append({
                    "name": func.name,
                    "file": func.file.file_path if hasattr(func, "file") else "Unknown",
                    "max_nesting": max_nesting
                })
        
        nesting_results["avg_max_nesting"] = total_max_nesting / len(functions)
        nesting_results["max_nesting"] = max_nesting_overall
        nesting_results["deeply_nested_functions"] = sorted(deeply_nested_functions, key=lambda x: x["max_nesting"], reverse=True)[:10]  # Top 10 most nested
        
        return nesting_results
    
    def get_function_size_metrics(self) -> Dict[str, Any]:
        """Get function size metrics."""
        functions = list(self.codebase.functions)
        size_metrics = {
            "avg_function_length": 0,
            "max_function_length": 0,
            "function_size_distribution": {
                "small": 0,      # < 10 lines
                "medium": 0,     # 10-30 lines
                "large": 0,      # 30-100 lines
                "very_large": 0  # > 100 lines
            },
            "largest_functions": []
        }
        
        if not functions:
            return size_metrics
        
        total_length = 0
        max_length = 0
        largest_functions = []
        
        for func in functions:
            func_source = func.source
            func_lines = func_source.count('\n') + 1
            
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
                largest_functions.append({
                    "name": func.name,
                    "file": func.file.file_path if hasattr(func, "file") else "Unknown",
                    "lines": func_lines
                })
        
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
    def get_monthly_commits(self) -> Dict[str, int]:
        pass

    def get_call_chain_analysis(self) -> Dict[str, Any]:
        """
        Analyze call chains between functions.
        
        This function traces and analyzes function call chains in the codebase,
        identifying the longest chains, most called functions, and complex call patterns.
        
        Returns:
            Dict containing call chain analysis results
        """
        call_chain_analysis = {
            "longest_chains": [],
            "most_called_functions": [],
            "complex_call_patterns": [],
            "average_chain_length": 0,
            "max_chain_length": 0,
            "total_chains": 0
        }
        
        try:
            # Create a directed graph of function calls
            G = nx.DiGraph()
            
            # Map to store function objects by their qualified name
            function_map = {}
            
            # Add nodes and edges to the graph
            for function in self.codebase.functions:
                function_name = f"{function.file.file_path}::{function.name}"
                G.add_node(function_name)
                function_map[function_name] = function
                
                # Add edges for each function call
                for call in function.function_calls:
                    if hasattr(call, "function_definition") and call.function_definition:
                        called_func = call.function_definition
                        called_name = f"{called_func.file.file_path if hasattr(called_func, 'file') else 'external'}::{called_func.name}"
                        G.add_node(called_name)
                        G.add_edge(function_name, called_name)
                        function_map[called_name] = called_func
            
            # Find all simple paths in the graph
            all_chains = []
            for source in G.nodes():
                for target in G.nodes():
                    if source != target:
                        try:
                            paths = list(nx.all_simple_paths(G, source, target, cutoff=10))
                            all_chains.extend(paths)
                        except (nx.NetworkXNoPath, nx.NodeNotFound):
                            continue
            
            # Calculate chain statistics
            if all_chains:
                call_chain_analysis["total_chains"] = len(all_chains)
                chain_lengths = [len(chain) for chain in all_chains]
                call_chain_analysis["average_chain_length"] = sum(chain_lengths) / len(chain_lengths)
                call_chain_analysis["max_chain_length"] = max(chain_lengths)
                
                # Find the longest chains
                longest_chains = sorted(all_chains, key=len, reverse=True)[:5]  # Top 5 longest chains
                for chain in longest_chains:
                    call_chain_analysis["longest_chains"].append({
                        "length": len(chain),
                        "path": [node.split("::")[-1] for node in chain],
                        "files": [node.split("::")[0] for node in chain]
                    })
                
                # Find most called functions
                in_degree = dict(G.in_degree())
                most_called = sorted(in_degree.items(), key=lambda x: x[1], reverse=True)[:10]  # Top 10 most called
                for func_name, call_count in most_called:
                    if call_count > 0:  # Only include functions that are actually called
                        call_chain_analysis["most_called_functions"].append({
                            "function": func_name.split("::")[-1],
                            "file": func_name.split("::")[0],
                            "call_count": call_count
                        })
                
                # Identify complex call patterns (cycles, etc.)
                try:
                    cycles = list(nx.simple_cycles(G))
                    for cycle in cycles:
                        call_chain_analysis["complex_call_patterns"].append({
                            "type": "cycle",
                            "length": len(cycle),
                            "functions": [node.split("::")[-1] for node in cycle],
                            "files": [node.split("::")[0] for node in cycle]
                        })
                except nx.NetworkXNoCycle:
                    pass
            
        except Exception as e:
            call_chain_analysis["error"] = str(e)
        
        return call_chain_analysis
    
    def get_dead_code_detection_with_filtering(self, exclude_patterns: List[str] = None) -> Dict[str, Any]:
        """
        Detect unused code with configurable filters.
        
        This function identifies dead code (unused functions, classes, etc.) in the codebase
        while allowing for customizable filters to exclude certain patterns.
        
        Args:
            exclude_patterns: List of regex patterns to exclude from dead code detection
                             (e.g., ["test_", ".*Controller", ".*Handler"])
        
        Returns:
            Dict containing dead code analysis results with filtering
        """
        if exclude_patterns is None:
            exclude_patterns = ["test_", ".*Test", ".*test", ".*Handler", ".*Controller", ".*Route"]
        
        dead_code_results = {
            "unused_functions": [],
            "unused_classes": [],
            "unused_methods": [],
            "total_unused_symbols": 0,
            "excluded_symbols": [],
            "filters_applied": exclude_patterns
        }
        
        try:
            # Compile regex patterns
            compiled_patterns = [re.compile(pattern) for pattern in exclude_patterns]
            
            # Check for unused functions
            for function in self.codebase.functions:
                # Skip if function matches any exclude pattern
                if any(pattern.search(function.name) for pattern in compiled_patterns):
                    dead_code_results["excluded_symbols"].append({
                        "type": "function",
                        "name": function.name,
                        "file": function.file.file_path if hasattr(function, "file") else "Unknown",
                        "reason": "Matched exclude pattern"
                    })
                    continue
                
                # Skip if function has decorators (might be used indirectly)
                if hasattr(function, "decorators") and function.decorators:
                    dead_code_results["excluded_symbols"].append({
                        "type": "function",
                        "name": function.name,
                        "file": function.file.file_path if hasattr(function, "file") else "Unknown",
                        "reason": "Has decorators"
                    })
                    continue
                
                # Check if function has no usages
                if not function.usages:
                    dead_code_results["unused_functions"].append({
                        "name": function.name,
                        "file": function.file.file_path if hasattr(function, "file") else "Unknown",
                        "line": function.span.start.line if hasattr(function, "span") else 0
                    })
            
            # Check for unused classes
            for cls in self.codebase.classes:
                # Skip if class matches any exclude pattern
                if any(pattern.search(cls.name) for pattern in compiled_patterns):
                    dead_code_results["excluded_symbols"].append({
                        "type": "class",
                        "name": cls.name,
                        "file": cls.file.file_path if hasattr(cls, "file") else "Unknown",
                        "reason": "Matched exclude pattern"
                    })
                    continue
                
                # Check if class has no usages
                if not cls.usages:
                    dead_code_results["unused_classes"].append({
                        "name": cls.name,
                        "file": cls.file.file_path if hasattr(cls, "file") else "Unknown",
                        "line": cls.span.start.line if hasattr(cls, "span") else 0
                    })
                
                # Check for unused methods in the class
                if hasattr(cls, "methods"):
                    for method in cls.methods:
                        # Skip if method matches any exclude pattern
                        if any(pattern.search(method.name) for pattern in compiled_patterns):
                            continue
                        
                        # Skip special methods (e.g., __init__, __str__)
                        if method.name.startswith("__") and method.name.endswith("__"):
                            continue
                        
                        # Check if method has no usages
                        if not method.usages:
                            dead_code_results["unused_methods"].append({
                                "name": f"{cls.name}.{method.name}",
                                "file": cls.file.file_path if hasattr(cls, "file") else "Unknown",
                                "line": method.span.start.line if hasattr(method, "span") else 0
                            })
            
            # Calculate total unused symbols
            dead_code_results["total_unused_symbols"] = (
                len(dead_code_results["unused_functions"]) +
                len(dead_code_results["unused_classes"]) +
                len(dead_code_results["unused_methods"])
            )
            
        except Exception as e:
            dead_code_results["error"] = str(e)
        
        return dead_code_results
    
    def get_path_finding_in_call_graphs(self, source_function: str = None, target_function: str = None, max_depth: int = 10) -> Dict[str, Any]:
        """
        Find paths between functions in the call graph.
        
        This function analyzes the call graph to find paths between specified functions,
        or identifies interesting paths if no specific functions are provided.
        
        Args:
            source_function: Name of the source function (optional)
            target_function: Name of the target function (optional)
            max_depth: Maximum depth for path finding (default: 10)
        
        Returns:
            Dict containing path analysis results
        """
        path_finding_results = {
            "paths": [],
            "total_paths_found": 0,
            "average_path_length": 0,
            "max_path_length": 0,
            "source_function": source_function,
            "target_function": target_function
        }
        
        try:
            # Create a directed graph of function calls
            G = nx.DiGraph()
            
            # Map to store function objects by their name
            function_map = {}
            
            # Add nodes and edges to the graph
            for function in self.codebase.functions:
                function_name = function.name
                G.add_node(function_name)
                function_map[function_name] = function
                
                # Add edges for each function call
                for call in function.function_calls:
                    if hasattr(call, "function_definition") and call.function_definition:
                        called_func = call.function_definition
                        G.add_node(called_func.name)
                        G.add_edge(function_name, called_func.name)
                        function_map[called_func.name] = called_func
            
            # Find paths between specified functions
            if source_function and target_function:
                if source_function in G.nodes() and target_function in G.nodes():
                    try:
                        all_paths = list(nx.all_simple_paths(G, source_function, target_function, cutoff=max_depth))
                        path_finding_results["total_paths_found"] = len(all_paths)
                        
                        if all_paths:
                            path_lengths = [len(path) for path in all_paths]
                            path_finding_results["average_path_length"] = sum(path_lengths) / len(path_lengths)
                            path_finding_results["max_path_length"] = max(path_lengths)
                            
                            # Store the paths
                            for path in all_paths:
                                path_info = {
                                    "length": len(path),
                                    "path": path,
                                    "files": [function_map[func].file.file_path if hasattr(function_map[func], "file") else "Unknown" for func in path]
                                }
                                path_finding_results["paths"].append(path_info)
                    except (nx.NetworkXNoPath, nx.NodeNotFound):
                        path_finding_results["error"] = f"No path found between {source_function} and {target_function}"
                else:
                    missing = []
                    if source_function not in G.nodes():
                        missing.append(source_function)
                    if target_function not in G.nodes():
                        missing.append(target_function)
                    path_finding_results["error"] = f"Function(s) not found in codebase: {', '.join(missing)}"
            else:
                # If no specific functions provided, find interesting paths
                # (e.g., longest paths, paths between entry points and leaf functions)
                
                # Find entry points (functions with no incoming edges)
                entry_points = [node for node, in_degree in G.in_degree() if in_degree == 0]
                
                # Find leaf functions (functions with no outgoing edges)
                leaf_functions = [node for node, out_degree in G.out_degree() if out_degree == 0]
                
                # Find paths from entry points to leaf functions
                all_paths = []
                for entry in entry_points[:5]:  # Limit to first 5 entry points for performance
                    for leaf in leaf_functions[:5]:  # Limit to first 5 leaf functions for performance
                        if entry != leaf:
                            try:
                                paths = list(nx.all_simple_paths(G, entry, leaf, cutoff=max_depth))
                                all_paths.extend(paths)
                            except (nx.NetworkXNoPath, nx.NodeNotFound):
                                continue
                
                # Sort paths by length and take the top 10
                all_paths.sort(key=len, reverse=True)
                top_paths = all_paths[:10]
                
                path_finding_results["total_paths_found"] = len(top_paths)
                
                if top_paths:
                    path_lengths = [len(path) for path in top_paths]
                    path_finding_results["average_path_length"] = sum(path_lengths) / len(path_lengths)
                    path_finding_results["max_path_length"] = max(path_lengths)
                    
                    # Store the paths
                    for path in top_paths:
                        path_info = {
                            "length": len(path),
                            "path": path,
                            "files": [function_map[func].file.file_path if hasattr(function_map[func], "file") else "Unknown" for func in path]
                        }
                        path_finding_results["paths"].append(path_info)
        
        except Exception as e:
            path_finding_results["error"] = str(e)
        
        return path_finding_results
    
    def get_dead_symbol_detection(self) -> Dict[str, Any]:
        """
        Detect unused symbols in the codebase.
        
        This function identifies unused symbols (variables, functions, classes, etc.)
        across the entire codebase.
        
        Returns:
            Dict containing dead symbol analysis results
        """
        dead_symbol_results = {
            "unused_symbols": [],
            "unused_by_type": {},
            "total_unused": 0,
            "total_symbols": 0,
            "unused_percentage": 0
        }
        
        try:
            # Count total symbols
            all_symbols = list(self.codebase.symbols)
            dead_symbol_results["total_symbols"] = len(all_symbols)
            
            # Initialize counters for each symbol type
            symbol_type_counts = defaultdict(int)
            unused_type_counts = defaultdict(int)
            
            # Check each symbol for usages
            unused_symbols = []
            for symbol in all_symbols:
                symbol_type = type(symbol).__name__
                symbol_type_counts[symbol_type] += 1
                
                # Skip certain symbols that might appear unused but are actually used
                # (e.g., entry points, special methods, etc.)
                if (hasattr(symbol, "name") and symbol.name.startswith("__") and symbol.name.endswith("__")):
                    continue
                
                # Check if symbol has no usages
                if not symbol.usages:
                    unused_type_counts[symbol_type] += 1
                    
                    # Get file and line information if available
                    file_path = "Unknown"
                    line_number = 0
                    if hasattr(symbol, "file") and symbol.file:
                        file_path = symbol.file.file_path
                    if hasattr(symbol, "span") and symbol.span:
                        line_number = symbol.span.start.line
                    
                    unused_symbols.append({
                        "name": symbol.name if hasattr(symbol, "name") else "Unknown",
                        "type": symbol_type,
                        "file": file_path,
                        "line": line_number
                    })
            
            # Store results
            dead_symbol_results["unused_symbols"] = unused_symbols
            dead_symbol_results["unused_by_type"] = dict(unused_type_counts)
            dead_symbol_results["total_unused"] = len(unused_symbols)
            
            # Calculate percentage
            if dead_symbol_results["total_symbols"] > 0:
                dead_symbol_results["unused_percentage"] = (
                    dead_symbol_results["total_unused"] / dead_symbol_results["total_symbols"] * 100
                )
            
        except Exception as e:
            dead_symbol_results["error"] = str(e)
        
        return dead_symbol_results
    
    def get_symbol_import_analysis(self) -> Dict[str, Any]:
        """
        Analyze how symbols are imported and used.
        
        This function analyzes import patterns across the codebase, identifying
        how symbols are imported and used.
        
        Returns:
            Dict containing symbol import analysis results
        """
        import_analysis = {
            "import_patterns": {},
            "most_imported_symbols": [],
            "import_style_distribution": {},
            "cross_file_imports": [],
            "import_chains": [],
            "total_imports": 0
        }
        
        try:
            # Analyze all imports in the codebase
            all_imports = []
            for file in self.codebase.files:
                for imp in file.imports:
                    all_imports.append(imp)
            
            import_analysis["total_imports"] = len(all_imports)
            
            # Analyze import styles
            import_styles = defaultdict(int)
            for imp in all_imports:
                if hasattr(imp, "import_type"):
                    import_styles[str(imp.import_type)] += 1
                elif "from" in imp.source:
                    import_styles["from_import"] += 1
                else:
                    import_styles["direct_import"] += 1
            
            import_analysis["import_style_distribution"] = dict(import_styles)
            
            # Track imported symbols and their usage
            imported_symbols = defaultdict(list)
            for file in self.codebase.files:
                for symbol in file.symbols:
                    if hasattr(symbol, "usages"):
                        # Find usages in other files
                        for usage in symbol.usages:
                            if hasattr(usage, "file") and usage.file != file:
                                imported_symbols[symbol.name].append({
                                    "symbol": symbol.name,
                                    "defined_in": file.file_path,
                                    "used_in": usage.file.file_path if hasattr(usage.file, "file_path") else "Unknown",
                                    "usage_type": str(usage.usage_type) if hasattr(usage, "usage_type") else "Unknown"
                                })
            
            # Find most imported symbols
            symbol_import_counts = {symbol: len(usages) for symbol, usages in imported_symbols.items()}
            most_imported = sorted(symbol_import_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            import_analysis["most_imported_symbols"] = [
                {"symbol": symbol, "import_count": count} for symbol, count in most_imported
            ]
            
            # Analyze import patterns
            import_patterns = defaultdict(int)
            for imp in all_imports:
                pattern = "unknown"
                if hasattr(imp, "module_name") and imp.module_name:
                    if "." in imp.module_name:
                        pattern = "nested_module"
                    else:
                        pattern = "top_level_module"
                
                if hasattr(imp, "symbols") and imp.symbols:
                    if len(imp.symbols) == 1:
                        pattern += "_single_symbol"
                    else:
                        pattern += "_multiple_symbols"
                
                import_patterns[pattern] += 1
            
            import_analysis["import_patterns"] = dict(import_patterns)
            
            # Find cross-file imports (files that import from many other files)
            file_import_counts = defaultdict(int)
            for file in self.codebase.files:
                unique_imported_files = set()
                for imp in file.imports:
                    if hasattr(imp, "from_file") and imp.from_file:
                        unique_imported_files.add(imp.from_file.file_path)
                
                file_import_counts[file.file_path] = len(unique_imported_files)
            
            # Get top 10 files with most imports
            top_importing_files = sorted(file_import_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            import_analysis["cross_file_imports"] = [
                {"file": file, "imports_from_unique_files": count} for file, count in top_importing_files
            ]
            
            # Analyze import chains (A imports B imports C)
            # This is a simplified version - a full analysis would be more complex
            import_chains = []
            for file in self.codebase.files:
                for imp in file.imports:
                    if hasattr(imp, "from_file") and imp.from_file:
                        imported_file = imp.from_file
                        if hasattr(imported_file, "imports") and imported_file.imports:
                            for second_level_imp in imported_file.imports:
                                if hasattr(second_level_imp, "from_file") and second_level_imp.from_file:
                                    import_chains.append({
                                        "chain": [file.file_path, imported_file.file_path, second_level_imp.from_file.file_path],
                                        "length": 3
                                    })
            
            # Limit to top 10 chains
            import_analysis["import_chains"] = import_chains[:10]
            
        except Exception as e:
            import_analysis["error"] = str(e)
        
        return import_analysis
    
    def get_dependency_graph_traversal(self, start_symbol: str = None, max_depth: int = 5) -> Dict[str, Any]:
        """
        Traverse and analyze dependency graphs.
        
        This function traverses the dependency graph starting from a specified symbol
        (or from key entry points if no symbol is specified) and analyzes the relationships.
        
        Args:
            start_symbol: Name of the symbol to start traversal from (optional)
            max_depth: Maximum depth for traversal (default: 5)
        
        Returns:
            Dict containing dependency graph traversal results
        """
        traversal_results = {
            "dependencies": {},
            "dependency_counts": {},
            "max_depth_reached": 0,
            "total_dependencies": 0,
            "start_symbol": start_symbol
        }
        
        try:
            # Find the starting symbol if specified
            start_symbols = []
            if start_symbol:
                for symbol in self.codebase.symbols:
                    if hasattr(symbol, "name") and symbol.name == start_symbol:
                        start_symbols.append(symbol)
                        break
                
                if not start_symbols:
                    traversal_results["error"] = f"Symbol '{start_symbol}' not found in codebase"
                    return traversal_results
            else:
                # If no start symbol specified, use entry points or important symbols
                # (e.g., main functions, public classes, etc.)
                for symbol in self.codebase.symbols:
                    if (hasattr(symbol, "name") and 
                        (symbol.name == "main" or 
                         symbol.name.startswith("public") or 
                         (hasattr(symbol, "is_public") and symbol.is_public))):
                        start_symbols.append(symbol)
                
                # Limit to top 5 symbols for performance
                start_symbols = start_symbols[:5]
                
                if not start_symbols:
                    # If still no symbols found, just use the first 5 symbols
                    start_symbols = list(self.codebase.symbols)[:5]
            
            # Traverse the dependency graph for each start symbol
            all_dependencies = {}
            dependency_counts = {}
            max_depth_reached = 0
            
            for start in start_symbols:
                visited = set()
                current_depth = 0
                
                def traverse(symbol, depth):
                    nonlocal current_depth, max_depth_reached
                    
                    if depth > max_depth or symbol in visited:
                        return
                    
                    visited.add(symbol)
                    current_depth = max(current_depth, depth)
                    max_depth_reached = max(max_depth_reached, depth)
                    
                    # Get symbol name and file
                    symbol_name = symbol.name if hasattr(symbol, "name") else "Unknown"
                    symbol_file = symbol.file.file_path if hasattr(symbol, "file") and symbol.file else "Unknown"
                    symbol_key = f"{symbol_file}::{symbol_name}"
                    
                    # Initialize dependency list for this symbol
                    if symbol_key not in all_dependencies:
                        all_dependencies[symbol_key] = []
                    
                    # Get direct dependencies
                    direct_deps = []
                    if hasattr(symbol, "dependencies"):
                        direct_deps = list(symbol.dependencies)
                    
                    # Record dependencies
                    for dep in direct_deps:
                        dep_name = dep.name if hasattr(dep, "name") else "Unknown"
                        dep_file = dep.file.file_path if hasattr(dep, "file") and dep.file else "Unknown"
                        dep_key = f"{dep_file}::{dep_name}"
                        
                        # Add to dependencies list
                        all_dependencies[symbol_key].append({
                            "name": dep_name,
                            "file": dep_file,
                            "type": type(dep).__name__
                        })
                        
                        # Update dependency count
                        if dep_key not in dependency_counts:
                            dependency_counts[dep_key] = 0
                        dependency_counts[dep_key] += 1
                        
                        # Continue traversal
                        traverse(dep, depth + 1)
                
                # Start traversal from this symbol
                traverse(start, 0)
            
            # Store results
            traversal_results["dependencies"] = all_dependencies
            traversal_results["dependency_counts"] = dependency_counts
            traversal_results["max_depth_reached"] = max_depth_reached
            traversal_results["total_dependencies"] = sum(len(deps) for deps in all_dependencies.values())
            
        except Exception as e:
            traversal_results["error"] = str(e)
        
        return traversal_results

    def get_type_resolution(self) -> Dict[str, Any]:
        """
        Resolve and analyze type annotations.
        
        This function analyzes type annotations across the codebase, resolving
        types to their actual definitions and providing insights into type usage.
        
        Returns:
            Dict containing type resolution analysis results
        """
        type_resolution = {
            "resolved_types": [],
            "unresolved_types": [],
            "resolution_success_rate": 0,
            "type_distribution": {},
            "complex_type_examples": []
        }
        
        try:
            # Track all type annotations
            all_types = []
            resolved_count = 0
            unresolved_count = 0
            type_distribution = defaultdict(int)
            
            # Analyze function return types
            for function in self.codebase.functions:
                if hasattr(function, "return_type") and function.return_type:
                    return_type = function.return_type
                    all_types.append(return_type)
                    
                    # Get type name and kind
                    type_name = return_type.source if hasattr(return_type, "source") else "Unknown"
                    type_kind = type(return_type).__name__
                    type_distribution[type_kind] += 1
                    
                    # Try to resolve the type
                    resolved = False
                    resolved_value = None
                    if hasattr(return_type, "resolved_value"):
                        resolved_value = return_type.resolved_value
                        resolved = resolved_value is not None
                    
                    if resolved:
                        resolved_count += 1
                        type_resolution["resolved_types"].append({
                            "context": f"Return type of {function.name}",
                            "type": type_name,
                            "kind": type_kind,
                            "file": function.file.file_path if hasattr(function, "file") else "Unknown"
                        })
                    else:
                        unresolved_count += 1
                        type_resolution["unresolved_types"].append({
                            "context": f"Return type of {function.name}",
                            "type": type_name,
                            "kind": type_kind,
                            "file": function.file.file_path if hasattr(function, "file") else "Unknown"
                        })
                    
                    # Check for complex types (generic, union, etc.)
                    is_complex = False
                    if hasattr(return_type, "parameters") or hasattr(return_type, "options"):
                        is_complex = True
                    
                    if is_complex:
                        type_resolution["complex_type_examples"].append({
                            "context": f"Return type of {function.name}",
                            "type": type_name,
                            "kind": type_kind,
                            "file": function.file.file_path if hasattr(function, "file") else "Unknown"
                        })
            
            # Analyze parameter types
            for function in self.codebase.functions:
                for param in function.parameters:
                    if hasattr(param, "type") and param.type:
                        param_type = param.type
                        all_types.append(param_type)
                        
                        # Get type name and kind
                        type_name = param_type.source if hasattr(param_type, "source") else "Unknown"
                        type_kind = type(param_type).__name__
                        type_distribution[type_kind] += 1
                        
                        # Try to resolve the type
                        resolved = False
                        resolved_value = None
                        if hasattr(param_type, "resolved_value"):
                            resolved_value = param_type.resolved_value
                            resolved = resolved_value is not None
                        
                        if resolved:
                            resolved_count += 1
                            type_resolution["resolved_types"].append({
                                "context": f"Parameter {param.name} of {function.name}",
                                "type": type_name,
                                "kind": type_kind,
                                "file": function.file.file_path if hasattr(function, "file") else "Unknown"
                            })
                        else:
                            unresolved_count += 1
                            type_resolution["unresolved_types"].append({
                                "context": f"Parameter {param.name} of {function.name}",
                                "type": type_name,
                                "kind": type_kind,
                                "file": function.file.file_path if hasattr(function, "file") else "Unknown"
                            })
                        
                        # Check for complex types (generic, union, etc.)
                        is_complex = False
                        if hasattr(param_type, "parameters") or hasattr(param_type, "options"):
                            is_complex = True
                        
                        if is_complex:
                            type_resolution["complex_type_examples"].append({
                                "context": f"Parameter {param.name} of {function.name}",
                                "type": type_name,
                                "kind": type_kind,
                                "file": function.file.file_path if hasattr(function, "file") else "Unknown"
                            })
            
            # Calculate resolution success rate
            total_types = resolved_count + unresolved_count
            if total_types > 0:
                type_resolution["resolution_success_rate"] = (resolved_count / total_types) * 100
            
            # Store type distribution
            type_resolution["type_distribution"] = dict(type_distribution)
            
            # Limit the number of examples to avoid excessive output
            type_resolution["resolved_types"] = type_resolution["resolved_types"][:20]
            type_resolution["unresolved_types"] = type_resolution["unresolved_types"][:20]
            type_resolution["complex_type_examples"] = type_resolution["complex_type_examples"][:20]
            
        except Exception as e:
            type_resolution["error"] = str(e)
        
        return type_resolution
    
    def get_generic_type_analysis(self) -> Dict[str, Any]:
        """
        Analyze generic type usage.
        
        This function analyzes how generic types (e.g., List[T], Dict[K, V]) are used
        across the codebase, identifying patterns and potential issues.
        
        Returns:
            Dict containing generic type analysis results
        """
        generic_analysis = {
            "generic_types": [],
            "most_common_generics": [],
            "nested_generics": [],
            "generic_type_distribution": {},
            "total_generic_types": 0
        }
        
        try:
            # Track all generic types
            all_generics = []
            generic_counts = defaultdict(int)
            
            # Helper function to process a type annotation
            def process_type(type_annotation, context):
                if hasattr(type_annotation, "parameters"):  # It's a generic type
                    # Get base type and parameters
                    base_type = type_annotation.base if hasattr(type_annotation, "base") else "Unknown"
                    params = []
                    if hasattr(type_annotation, "parameters"):
                        params = [param.source if hasattr(param, "source") else "Unknown" 
                                 for param in type_annotation.parameters]
                    
                    # Create generic type info
                    generic_info = {
                        "base": base_type,
                        "parameters": params,
                        "source": type_annotation.source if hasattr(type_annotation, "source") else "Unknown",
                        "context": context,
                        "is_nested": any("List" in p or "Dict" in p or "Set" in p or "Tuple" in p for p in params)
                    }
                    
                    all_generics.append(generic_info)
                    generic_counts[base_type] += 1
                    
                    # Check for nested generics
                    if generic_info["is_nested"]:
                        generic_analysis["nested_generics"].append(generic_info)
            
            # Analyze function return types
            for function in self.codebase.functions:
                if hasattr(function, "return_type") and function.return_type:
                    process_type(function.return_type, 
                                f"Return type of {function.name} in {function.file.file_path if hasattr(function, 'file') else 'Unknown'}")
            
            # Analyze parameter types
            for function in self.codebase.functions:
                for param in function.parameters:
                    if hasattr(param, "type") and param.type:
                        process_type(param.type, 
                                    f"Parameter {param.name} of {function.name} in {function.file.file_path if hasattr(function, 'file') else 'Unknown'}")
            
            # Analyze variable types
            for file in self.codebase.files:
                for assignment in file.assignments:
                    if hasattr(assignment, "type") and assignment.type:
                        process_type(assignment.type, 
                                    f"Variable {assignment.name if hasattr(assignment, 'name') else 'Unknown'} in {file.file_path}")
            
            # Store results
            generic_analysis["generic_types"] = all_generics[:50]  # Limit to 50 examples
            generic_analysis["total_generic_types"] = len(all_generics)
            generic_analysis["generic_type_distribution"] = dict(generic_counts)
            
            # Get most common generic types
            most_common = sorted(generic_counts.items(), key=lambda x: x[1], reverse=True)
            generic_analysis["most_common_generics"] = [
                {"base": base, "count": count} for base, count in most_common[:10]
            ]
            
        except Exception as e:
            generic_analysis["error"] = str(e)
        
        return generic_analysis
    
    def get_union_type_analysis(self) -> Dict[str, Any]:
        """
        Analyze union type usage.
        
        This function analyzes how union types (e.g., A | B, Union[X, Y]) are used
        across the codebase, identifying patterns and potential issues.
        
        Returns:
            Dict containing union type analysis results
        """
        union_analysis = {
            "union_types": [],
            "common_union_patterns": [],
            "optional_types": [],  # Union with None/undefined
            "complex_unions": [],  # Unions with more than 2 types
            "total_union_types": 0
        }
        
        try:
            # Track all union types
            all_unions = []
            union_patterns = defaultdict(int)
            optional_types = []
            complex_unions = []
            
            # Helper function to process a type annotation
            def process_type(type_annotation, context):
                if hasattr(type_annotation, "options"):  # It's a union type
                    # Get options
                    options = []
                    if hasattr(type_annotation, "options"):
                        options = [opt.source if hasattr(opt, "source") else "Unknown" 
                                  for opt in type_annotation.options]
                    
                    # Create union type info
                    union_info = {
                        "options": options,
                        "source": type_annotation.source if hasattr(type_annotation, "source") else "Unknown",
                        "context": context,
                        "is_optional": any(opt in ["None", "null", "undefined"] for opt in options),
                        "is_complex": len(options) > 2
                    }
                    
                    all_unions.append(union_info)
                    
                    # Track union pattern
                    pattern = "|".join(sorted(options))
                    union_patterns[pattern] += 1
                    
                    # Track optional types
                    if union_info["is_optional"]:
                        optional_types.append(union_info)
                    
                    # Track complex unions
                    if union_info["is_complex"]:
                        complex_unions.append(union_info)
            
            # Analyze function return types
            for function in self.codebase.functions:
                if hasattr(function, "return_type") and function.return_type:
                    process_type(function.return_type, 
                                f"Return type of {function.name} in {function.file.file_path if hasattr(function, 'file') else 'Unknown'}")
            
            # Analyze parameter types
            for function in self.codebase.functions:
                for param in function.parameters:
                    if hasattr(param, "type") and param.type:
                        process_type(param.type, 
                                    f"Parameter {param.name} of {function.name} in {function.file.file_path if hasattr(function, 'file') else 'Unknown'}")
            
            # Analyze variable types
            for file in self.codebase.files:
                for assignment in file.assignments:
                    if hasattr(assignment, "type") and assignment.type:
                        process_type(assignment.type, 
                                    f"Variable {assignment.name if hasattr(assignment, 'name') else 'Unknown'} in {file.file_path}")
            
            # Store results
            union_analysis["union_types"] = all_unions[:50]  # Limit to 50 examples
            union_analysis["total_union_types"] = len(all_unions)
            union_analysis["optional_types"] = optional_types[:20]  # Limit to 20 examples
            union_analysis["complex_unions"] = complex_unions[:20]  # Limit to 20 examples
            
            # Get common union patterns
            common_patterns = sorted(union_patterns.items(), key=lambda x: x[1], reverse=True)
            union_analysis["common_union_patterns"] = [
                {"pattern": pattern, "count": count} for pattern, count in common_patterns[:10]
            ]
            
        except Exception as e:
            union_analysis["error"] = str(e)
        
        return union_analysis
    
    def get_comprehensive_type_coverage_analysis(self) -> Dict[str, Any]:
        """
        Analyze type coverage across the codebase.
        
        This function provides a comprehensive analysis of type coverage,
        including statistics by file, module, and symbol type.
        
        Returns:
            Dict containing comprehensive type coverage analysis results
        """
        coverage_analysis = {
            "overall_coverage": {
                "total_symbols": 0,
                "typed_symbols": 0,
                "coverage_percentage": 0
            },
            "coverage_by_file": [],
            "coverage_by_module": {},
            "coverage_by_symbol_type": {},
            "untyped_symbols": [],
            "partially_typed_functions": []
        }
        
        try:
            # Initialize counters
            total_symbols = 0
            typed_symbols = 0
            file_coverage = {}
            module_coverage = defaultdict(lambda: {"total": 0, "typed": 0})
            symbol_type_coverage = defaultdict(lambda: {"total": 0, "typed": 0})
            untyped_symbols = []
            partially_typed_functions = []
            
            # Analyze function return types and parameters
            for function in self.codebase.functions:
                function_file = function.file.file_path if hasattr(function, "file") else "Unknown"
                module_name = function_file.split("/")[0] if "/" in function_file else "root"
                
                # Initialize file coverage if needed
                if function_file not in file_coverage:
                    file_coverage[function_file] = {"total": 0, "typed": 0}
                
                # Check return type
                total_symbols += 1
                file_coverage[function_file]["total"] += 1
                module_coverage[module_name]["total"] += 1
                symbol_type_coverage["function_return"]["total"] += 1
                
                has_return_type = hasattr(function, "return_type") and function.return_type and function.return_type.is_typed
                if has_return_type:
                    typed_symbols += 1
                    file_coverage[function_file]["typed"] += 1
                    module_coverage[module_name]["typed"] += 1
                    symbol_type_coverage["function_return"]["typed"] += 1
                else:
                    untyped_symbols.append({
                        "name": function.name,
                        "type": "function_return",
                        "file": function_file
                    })
                
                # Check parameter types
                param_count = len(function.parameters)
                typed_param_count = sum(1 for param in function.parameters if hasattr(param, "type") and param.type and param.type.is_typed)
                
                total_symbols += param_count
                file_coverage[function_file]["total"] += param_count
                module_coverage[module_name]["total"] += param_count
                symbol_type_coverage["function_parameter"]["total"] += param_count
                
                typed_symbols += typed_param_count
                file_coverage[function_file]["typed"] += typed_param_count
                module_coverage[module_name]["typed"] += typed_param_count
                symbol_type_coverage["function_parameter"]["typed"] += typed_param_count
                
                # Track partially typed functions
                if 0 < typed_param_count < param_count or (not has_return_type and typed_param_count > 0):
                    partially_typed_functions.append({
                        "name": function.name,
                        "file": function_file,
                        "total_parameters": param_count,
                        "typed_parameters": typed_param_count,
                        "has_return_type": has_return_type
                    })
                
                # Track untyped parameters
                for param in function.parameters:
                    if not (hasattr(param, "type") and param.type and param.type.is_typed):
                        untyped_symbols.append({
                            "name": f"{function.name}.{param.name}",
                            "type": "function_parameter",
                            "file": function_file
                        })
            
            # Analyze variable types
            for file in self.codebase.files:
                file_path = file.file_path
                module_name = file_path.split("/")[0] if "/" in file_path else "root"
                
                # Initialize file coverage if needed
                if file_path not in file_coverage:
                    file_coverage[file_path] = {"total": 0, "typed": 0}
                
                for assignment in file.assignments:
                    total_symbols += 1
                    file_coverage[file_path]["total"] += 1
                    module_coverage[module_name]["total"] += 1
                    symbol_type_coverage["variable"]["total"] += 1
                    
                    if hasattr(assignment, "type") and assignment.type and assignment.type.is_typed:
                        typed_symbols += 1
                        file_coverage[file_path]["typed"] += 1
                        module_coverage[module_name]["typed"] += 1
                        symbol_type_coverage["variable"]["typed"] += 1
                    else:
                        untyped_symbols.append({
                            "name": assignment.name if hasattr(assignment, "name") else "Unknown",
                            "type": "variable",
                            "file": file_path
                        })
            
            # Analyze class attribute types
            for cls in self.codebase.classes:
                class_file = cls.file.file_path if hasattr(cls, "file") else "Unknown"
                module_name = class_file.split("/")[0] if "/" in class_file else "root"
                
                # Initialize file coverage if needed
                if class_file not in file_coverage:
                    file_coverage[class_file] = {"total": 0, "typed": 0}
                
                if hasattr(cls, "attributes"):
                    for attr in cls.attributes:
                        total_symbols += 1
                        file_coverage[class_file]["total"] += 1
                        module_coverage[module_name]["total"] += 1
                        symbol_type_coverage["class_attribute"]["total"] += 1
                        
                        if hasattr(attr, "is_typed") and attr.is_typed:
                            typed_symbols += 1
                            file_coverage[class_file]["typed"] += 1
                            module_coverage[module_name]["typed"] += 1
                            symbol_type_coverage["class_attribute"]["typed"] += 1
                        else:
                            untyped_symbols.append({
                                "name": f"{cls.name}.{attr.name if hasattr(attr, 'name') else 'Unknown'}",
                                "type": "class_attribute",
                                "file": class_file
                            })
            
            # Calculate overall coverage
            coverage_analysis["overall_coverage"]["total_symbols"] = total_symbols
            coverage_analysis["overall_coverage"]["typed_symbols"] = typed_symbols
            if total_symbols > 0:
                coverage_analysis["overall_coverage"]["coverage_percentage"] = (typed_symbols / total_symbols) * 100
            
            # Calculate file coverage percentages and sort by coverage
            file_coverage_list = []
            for file_path, counts in file_coverage.items():
                if counts["total"] > 0:
                    percentage = (counts["typed"] / counts["total"]) * 100
                    file_coverage_list.append({
                        "file": file_path,
                        "total_symbols": counts["total"],
                        "typed_symbols": counts["typed"],
                        "coverage_percentage": percentage
                    })
            
            # Sort by coverage percentage (ascending, so lowest coverage first)
            file_coverage_list.sort(key=lambda x: x["coverage_percentage"])
            coverage_analysis["coverage_by_file"] = file_coverage_list
            
            # Calculate module coverage percentages
            for module, counts in module_coverage.items():
                if counts["total"] > 0:
                    percentage = (counts["typed"] / counts["total"]) * 100
                    coverage_analysis["coverage_by_module"][module] = {
                        "total_symbols": counts["total"],
                        "typed_symbols": counts["typed"],
                        "coverage_percentage": percentage
                    }
            
            # Calculate symbol type coverage percentages
            for symbol_type, counts in symbol_type_coverage.items():
                if counts["total"] > 0:
                    percentage = (counts["typed"] / counts["total"]) * 100
                    coverage_analysis["coverage_by_symbol_type"][symbol_type] = {
                        "total_symbols": counts["total"],
                        "typed_symbols": counts["typed"],
                        "coverage_percentage": percentage
                    }
            
            # Limit the number of untyped symbols to avoid excessive output
            coverage_analysis["untyped_symbols"] = untyped_symbols[:100]
            coverage_analysis["partially_typed_functions"] = partially_typed_functions[:50]
            
        except Exception as e:
            coverage_analysis["error"] = str(e)
        
        return coverage_analysis
    
    def get_enhanced_return_type_analysis(self) -> Dict[str, Any]:
        """
        Analyze return type patterns.
        
        This function provides an enhanced analysis of return type patterns
        across the codebase, identifying common patterns and potential issues.
        
        Returns:
            Dict containing enhanced return type analysis results
        """
        return_type_analysis = {
            "return_type_distribution": {},
            "return_type_by_module": {},
            "functions_without_return_types": [],
            "inconsistent_return_types": [],
            "return_type_suggestions": [],
            "total_functions": 0,
            "functions_with_return_types": 0
        }
        
        try:
            # Initialize counters
            total_functions = 0
            functions_with_return_types = 0
            return_type_counts = defaultdict(int)
            module_return_types = defaultdict(lambda: defaultdict(int))
            functions_without_return_types = []
            inconsistent_return_types = []
            return_type_suggestions = []
            
            # Analyze all functions
            for function in self.codebase.functions:
                total_functions += 1
                function_file = function.file.file_path if hasattr(function, "file") else "Unknown"
                module_name = function_file.split("/")[0] if "/" in function_file else "root"
                
                # Check if function has a return type
                has_return_type = hasattr(function, "return_type") and function.return_type and function.return_type.is_typed
                
                if has_return_type:
                    functions_with_return_types += 1
                    return_type = function.return_type.source if hasattr(function.return_type, "source") else "Unknown"
                    return_type_counts[return_type] += 1
                    module_return_types[module_name][return_type] += 1
                else:
                    # Track functions without return types
                    functions_without_return_types.append({
                        "name": function.name,
                        "file": function_file,
                        "has_return_statements": len(function.return_statements) > 0 if hasattr(function, "return_statements") else "Unknown"
                    })
                    
                    # Try to suggest a return type based on return statements
                    if hasattr(function, "return_statements") and function.return_statements:
                        return_values = []
                        for ret_stmt in function.return_statements:
                            if hasattr(ret_stmt, "value") and ret_stmt.value:
                                return_values.append(ret_stmt.value.source if hasattr(ret_stmt.value, "source") else "Unknown")
                        
                        if return_values:
                            suggested_type = "Any"  # Default suggestion
                            
                            # Simple heuristic for suggesting types
                            if all("None" in val or val == "None" for val in return_values):
                                suggested_type = "None"
                            elif all(val.startswith('"') or val.startswith("'") for val in return_values):
                                suggested_type = "str"
                            elif all(val.isdigit() for val in return_values):
                                suggested_type = "int"
                            elif all("." in val and all(part.isdigit() for part in val.split(".")) for val in return_values):
                                suggested_type = "float"
                            elif all(val in ["True", "False"] for val in return_values):
                                suggested_type = "bool"
                            elif all("[" in val and "]" in val for val in return_values):
                                suggested_type = "List"
                            elif all("{" in val and "}" in val for val in return_values):
                                if all(":" in val for val in return_values):
                                    suggested_type = "Dict"
                                else:
                                    suggested_type = "Set"
                            
                            return_type_suggestions.append({
                                "function": function.name,
                                "file": function_file,
                                "return_values": return_values[:3],  # Limit to first 3 for brevity
                                "suggested_type": suggested_type
                            })
                
                # Check for inconsistent return types
                if hasattr(function, "return_statements") and len(function.return_statements) > 1:
                    return_values = []
                    for ret_stmt in function.return_statements:
                        if hasattr(ret_stmt, "value") and ret_stmt.value:
                            return_values.append(ret_stmt.value.source if hasattr(ret_stmt.value, "source") else "Unknown")
                    
                    # Check if return values appear to be of different types
                    value_types = set()
                    for val in return_values:
                        if val.startswith('"') or val.startswith("'"):
                            value_types.add("str")
                        elif val.isdigit():
                            value_types.add("int")
                        elif "." in val and all(part.isdigit() for part in val.split(".")):
                            value_types.add("float")
                        elif val in ["True", "False"]:
                            value_types.add("bool")
                        elif val == "None":
                            value_types.add("None")
                        elif "[" in val and "]" in val:
                            value_types.add("List")
                        elif "{" in val and "}" in val:
                            if ":" in val:
                                value_types.add("Dict")
                            else:
                                value_types.add("Set")
                        else:
                            value_types.add("Other")
                    
                    if len(value_types) > 1:
                        inconsistent_return_types.append({
                            "function": function.name,
                            "file": function_file,
                            "return_values": return_values[:3],  # Limit to first 3 for brevity
                            "apparent_types": list(value_types),
                            "has_return_type": has_return_type,
                            "return_type": function.return_type.source if has_return_type and hasattr(function.return_type, "source") else None
                        })
            
            # Store results
            return_type_analysis["total_functions"] = total_functions
            return_type_analysis["functions_with_return_types"] = functions_with_return_types
            return_type_analysis["return_type_distribution"] = dict(return_type_counts)
            return_type_analysis["return_type_by_module"] = {module: dict(types) for module, types in module_return_types.items()}
            
            # Limit the number of items to avoid excessive output
            return_type_analysis["functions_without_return_types"] = functions_without_return_types[:50]
            return_type_analysis["inconsistent_return_types"] = inconsistent_return_types[:30]
            return_type_analysis["return_type_suggestions"] = return_type_suggestions[:50]
            
        except Exception as e:
            return_type_analysis["error"] = str(e)
        
        return return_type_analysis

    def get_unused_variable_detection(self) -> Dict[str, Any]:
        """
        Detect unused variables.
        
        This function identifies unused variables across the codebase,
        helping to clean up dead code and improve code quality.
        
        Returns:
            Dict containing unused variable analysis results
        """
        unused_var_results = {
            "unused_local_variables": [],
            "unused_global_variables": [],
            "unused_class_attributes": [],
            "total_unused_variables": 0,
            "by_file": {}
        }
        
        try:
            # Track unused variables by file
            file_unused_vars = defaultdict(int)
            
            # Check for unused local variables in functions
            for function in self.codebase.functions:
                function_file = function.file.file_path if hasattr(function, "file") else "Unknown"
                
                if hasattr(function, "code_block") and hasattr(function.code_block, "local_var_assignments"):
                    for var_assignment in function.code_block.local_var_assignments:
                        # Check if variable has no usages
                        if hasattr(var_assignment, "local_usages") and not var_assignment.local_usages:
                            unused_var_results["unused_local_variables"].append({
                                "name": var_assignment.name if hasattr(var_assignment, "name") else "Unknown",
                                "function": function.name,
                                "file": function_file,
                                "line": var_assignment.span.start.line if hasattr(var_assignment, "span") else 0
                            })
                            file_unused_vars[function_file] += 1
            
            # Check for unused global variables
            for file in self.codebase.files:
                for assignment in file.assignments:
                    # Skip function and class definitions
                    if not (hasattr(assignment, "is_function") and assignment.is_function) and \
                       not (hasattr(assignment, "is_class") and assignment.is_class):
                        # Check if variable has no usages
                        if hasattr(assignment, "usages") and not assignment.usages:
                            unused_var_results["unused_global_variables"].append({
                                "name": assignment.name if hasattr(assignment, "name") else "Unknown",
                                "file": file.file_path,
                                "line": assignment.span.start.line if hasattr(assignment, "span") else 0
                            })
                            file_unused_vars[file.file_path] += 1
            
            # Check for unused class attributes
            for cls in self.codebase.classes:
                class_file = cls.file.file_path if hasattr(cls, "file") else "Unknown"
                
                if hasattr(cls, "attributes"):
                    for attr in cls.attributes:
                        # Skip special attributes (e.g., __init__, __dict__)
                        if hasattr(attr, "name") and attr.name.startswith("__") and attr.name.endswith("__"):
                            continue
                        
                        # Check if attribute has no usages
                        if hasattr(attr, "usages") and not attr.usages:
                            unused_var_results["unused_class_attributes"].append({
                                "name": attr.name if hasattr(attr, "name") else "Unknown",
                                "class": cls.name,
                                "file": class_file,
                                "line": attr.span.start.line if hasattr(attr, "span") else 0
                            })
                            file_unused_vars[class_file] += 1
            
            # Calculate total unused variables
            unused_var_results["total_unused_variables"] = (
                len(unused_var_results["unused_local_variables"]) +
                len(unused_var_results["unused_global_variables"]) +
                len(unused_var_results["unused_class_attributes"])
            )
            
            # Store unused variables by file
            unused_var_results["by_file"] = dict(file_unused_vars)
            
        except Exception as e:
            unused_var_results["error"] = str(e)
        
        return unused_var_results
    
    def get_dependency_graph_creation(self) -> Dict[str, Any]:
        """
        Create dependency graphs.
        
        This function creates and analyzes dependency graphs for the codebase,
        providing insights into module relationships and dependencies.
        
        Returns:
            Dict containing dependency graph analysis results
        """
        dependency_graph_results = {
            "module_graph": {},
            "file_graph": {},
            "symbol_graph": {},
            "stats": {
                "total_nodes": 0,
                "total_edges": 0,
                "avg_dependencies": 0,
                "max_dependencies": 0,
                "most_dependent_modules": []
            }
        }
        
        try:
            # Create module-level dependency graph
            module_graph = defaultdict(set)
            file_graph = defaultdict(set)
            symbol_graph = defaultdict(set)
            
            # Track dependencies at file level
            for file in self.codebase.files:
                file_path = file.file_path
                module_name = file_path.split("/")[0] if "/" in file_path else "root"
                
                # Track file dependencies through imports
                for imp in file.imports:
                    if hasattr(imp, "from_file") and imp.from_file:
                        imported_file = imp.from_file.file_path
                        imported_module = imported_file.split("/")[0] if "/" in imported_file else "root"
                        
                        # Add to file graph
                        file_graph[file_path].add(imported_file)
                        
                        # Add to module graph
                        if imported_module != module_name:
                            module_graph[module_name].add(imported_module)
            
            # Track dependencies at symbol level
            for symbol in self.codebase.symbols:
                if hasattr(symbol, "name") and hasattr(symbol, "file") and symbol.file:
                    symbol_name = symbol.name
                    symbol_file = symbol.file.file_path
                    symbol_key = f"{symbol_file}::{symbol_name}"
                    
                    # Track dependencies
                    if hasattr(symbol, "dependencies"):
                        for dep in symbol.dependencies:
                            if hasattr(dep, "name") and hasattr(dep, "file") and dep.file:
                                dep_name = dep.name
                                dep_file = dep.file.file_path
                                dep_key = f"{dep_file}::{dep_name}"
                                
                                symbol_graph[symbol_key].add(dep_key)
            
            # Convert to serializable format
            module_graph_dict = {module: list(deps) for module, deps in module_graph.items()}
            file_graph_dict = {file: list(deps) for file, deps in file_graph.items()}
            
            # For symbol graph, limit to most connected symbols to avoid excessive output
            symbol_deps_count = {symbol: len(deps) for symbol, deps in symbol_graph.items()}
            top_symbols = sorted(symbol_deps_count.items(), key=lambda x: x[1], reverse=True)[:100]
            symbol_graph_dict = {symbol: list(symbol_graph[symbol]) for symbol, _ in top_symbols}
            
            # Calculate statistics
            all_modules = set(module_graph.keys()) | {dep for deps in module_graph.values() for dep in deps}
            all_files = set(file_graph.keys()) | {dep for deps in file_graph.values() for dep in deps}
            
            total_nodes = len(all_modules) + len(all_files)
            total_edges = sum(len(deps) for deps in module_graph.values()) + sum(len(deps) for deps in file_graph.values())
            
            module_dep_counts = {module: len(deps) for module, deps in module_graph.items()}
            max_dependencies = max(module_dep_counts.values()) if module_dep_counts else 0
            avg_dependencies = sum(module_dep_counts.values()) / len(module_dep_counts) if module_dep_counts else 0
            
            most_dependent = sorted(module_dep_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Store results
            dependency_graph_results["module_graph"] = module_graph_dict
            dependency_graph_results["file_graph"] = file_graph_dict
            dependency_graph_results["symbol_graph"] = symbol_graph_dict
            
            dependency_graph_results["stats"]["total_nodes"] = total_nodes
            dependency_graph_results["stats"]["total_edges"] = total_edges
            dependency_graph_results["stats"]["avg_dependencies"] = avg_dependencies
            dependency_graph_results["stats"]["max_dependencies"] = max_dependencies
            dependency_graph_results["stats"]["most_dependent_modules"] = [
                {"module": module, "dependencies": count} for module, count in most_dependent
            ]
            
        except Exception as e:
            dependency_graph_results["error"] = str(e)
        
        return dependency_graph_results
    
    def get_circular_dependency_breaking(self) -> Dict[str, Any]:
        """
        Identify and suggest fixes for circular dependencies.
        
        This function analyzes the codebase for circular dependencies and
        provides suggestions for breaking them.
        
        Returns:
            Dict containing circular dependency analysis and fix suggestions
        """
        circular_dep_results = {
            "circular_dependencies": [],
            "suggested_fixes": [],
            "total_cycles": 0,
            "affected_modules": set(),
            "affected_files": set()
        }
        
        try:
            # Create file-level dependency graph
            G = nx.DiGraph()
            
            # Add nodes and edges
            for file in self.codebase.files:
                file_path = file.file_path
                G.add_node(file_path)
                
                for imp in file.imports:
                    if hasattr(imp, "from_file") and imp.from_file:
                        imported_file = imp.from_file.file_path
                        G.add_edge(file_path, imported_file)
            
            # Find circular dependencies (cycles in the graph)
            try:
                cycles = list(nx.simple_cycles(G))
                circular_dep_results["total_cycles"] = len(cycles)
                
                for cycle in cycles:
                    # Track affected modules and files
                    for file_path in cycle:
                        module = file_path.split("/")[0] if "/" in file_path else "root"
                        circular_dep_results["affected_modules"].add(module)
                        circular_dep_results["affected_files"].add(file_path)
                    
                    # Create cycle info
                    cycle_info = {
                        "files": cycle,
                        "length": len(cycle),
                        "modules": [file_path.split("/")[0] if "/" in file_path else "root" for file_path in cycle]
                    }
                    
                    circular_dep_results["circular_dependencies"].append(cycle_info)
                    
                    # Generate suggested fixes
                    suggested_fix = self._suggest_circular_dependency_fix(cycle)
                    circular_dep_results["suggested_fixes"].append(suggested_fix)
                
                # Convert sets to lists for JSON serialization
                circular_dep_results["affected_modules"] = list(circular_dep_results["affected_modules"])
                circular_dep_results["affected_files"] = list(circular_dep_results["affected_files"])
                
            except nx.NetworkXNoCycle:
                circular_dep_results["total_cycles"] = 0
            
        except Exception as e:
            circular_dep_results["error"] = str(e)
        
        return circular_dep_results
    
    def _suggest_circular_dependency_fix(self, cycle: List[str]) -> Dict[str, Any]:
        """
        Generate suggestions for breaking a circular dependency.
        
        Args:
            cycle: List of files forming a circular dependency
            
        Returns:
            Dict containing suggested fixes
        """
        suggested_fix = {
            "cycle": cycle,
            "strategies": []
        }
        
        try:
            # Strategy 1: Create a shared module
            shared_symbols = self._find_shared_symbols_between_files(cycle)
            if shared_symbols:
                suggested_fix["strategies"].append({
                    "type": "create_shared_module",
                    "description": "Create a shared module for common code",
                    "shared_symbols": shared_symbols[:5],  # Limit to 5 symbols
                    "suggested_module_name": "shared" if len(cycle) > 2 else f"shared_{cycle[0].split('/')[-1].split('.')[0]}_{cycle[1].split('/')[-1].split('.')[0]}"
                })
            
            # Strategy 2: Use dependency inversion
            suggested_fix["strategies"].append({
                "type": "dependency_inversion",
                "description": "Apply dependency inversion principle",
                "steps": [
                    "Create an interface/abstract class that defines the required functionality",
                    f"Implement the interface in {cycle[-1]}",
                    f"Update {cycle[0]} to depend on the interface instead of the concrete implementation"
                ]
            })
            
            # Strategy 3: Merge files
            if len(cycle) == 2:
                suggested_fix["strategies"].append({
                    "type": "merge_files",
                    "description": "Merge the files if they are closely related",
                    "merged_file_name": f"{cycle[0].split('/')[-1].split('.')[0]}_{cycle[1].split('/')[-1].split('.')[0]}.{cycle[0].split('.')[-1]}"
                })
            
            # Strategy 4: Restructure code
            suggested_fix["strategies"].append({
                "type": "restructure",
                "description": "Restructure the code to eliminate circular dependencies",
                "steps": [
                    "Identify the specific symbols causing the circular dependency",
                    "Move these symbols to break the cycle",
                    "Consider if the circular dependency indicates a design issue"
                ]
            })
            
        except Exception as e:
            suggested_fix["error"] = str(e)
        
        return suggested_fix
    
    def _find_shared_symbols_between_files(self, files: List[str]) -> List[Dict[str, str]]:
        """
        Find symbols that are shared between files in a cycle.
        
        Args:
            files: List of file paths
            
        Returns:
            List of shared symbols with their details
        """
        shared_symbols = []
        
        try:
            # Get all symbols in each file
            file_symbols = {}
            for file_path in files:
                file_obj = None
                for f in self.codebase.files:
                    if f.file_path == file_path:
                        file_obj = f
                        break
                
                if file_obj:
                    file_symbols[file_path] = list(file_obj.symbols)
            
            # Find symbols used across multiple files
            all_symbols = [symbol for symbols in file_symbols.values() for symbol in symbols]
            symbol_usage_count = defaultdict(int)
            
            for symbol in all_symbols:
                if hasattr(symbol, "usages"):
                    for usage in symbol.usages:
                        if hasattr(usage, "file") and usage.file and usage.file.file_path in files:
                            symbol_usage_count[symbol] += 1
            
            # Get symbols used in multiple files
            for symbol, count in symbol_usage_count.items():
                if count > 1 and hasattr(symbol, "name") and hasattr(symbol, "file") and symbol.file:
                    shared_symbols.append({
                        "name": symbol.name,
                        "type": type(symbol).__name__,
                        "defined_in": symbol.file.file_path,
                        "used_in_count": count
                    })
            
            # Sort by usage count
            shared_symbols.sort(key=lambda x: x["used_in_count"], reverse=True)
            
        except Exception:
            pass
        
        return shared_symbols
    
    def get_module_coupling_analysis(self) -> Dict[str, Any]:
        """
        Analyze module coupling.
        
        This function analyzes the coupling between modules in the codebase,
        identifying tightly coupled modules and suggesting improvements.
        
        Returns:
            Dict containing module coupling analysis results
        """
        coupling_results = {
            "module_coupling_scores": {},
            "highly_coupled_modules": [],
            "coupling_matrix": {},
            "suggested_improvements": [],
            "overall_coupling_score": 0
        }
        
        try:
            # Create module-level dependency graph
            module_dependencies = defaultdict(set)
            module_dependents = defaultdict(set)
            
            # Track all modules
            all_modules = set()
            
            # Analyze file dependencies
            for file in self.codebase.files:
                file_path = file.file_path
                module_name = file_path.split("/")[0] if "/" in file_path else "root"
                all_modules.add(module_name)
                
                # Track module dependencies through imports
                for imp in file.imports:
                    if hasattr(imp, "from_file") and imp.from_file:
                        imported_file = imp.from_file.file_path
                        imported_module = imported_file.split("/")[0] if "/" in imported_file else "root"
                        
                        if imported_module != module_name:
                            module_dependencies[module_name].add(imported_module)
                            module_dependents[imported_module].add(module_name)
            
            # Calculate coupling scores
            coupling_scores = {}
            coupling_matrix = {module: {} for module in all_modules}
            
            for module in all_modules:
                # Calculate afferent coupling (incoming dependencies)
                ca = len(module_dependents[module])
                
                # Calculate efferent coupling (outgoing dependencies)
                ce = len(module_dependencies[module])
                
                # Calculate instability (I = Ce / (Ca + Ce))
                instability = ce / (ca + ce) if (ca + ce) > 0 else 0
                
                # Calculate coupling score (higher is worse)
                coupling_score = (ca * ce) / len(all_modules) if len(all_modules) > 0 else 0
                
                coupling_scores[module] = {
                    "afferent_coupling": ca,
                    "efferent_coupling": ce,
                    "instability": instability,
                    "coupling_score": coupling_score,
                    "dependencies": list(module_dependencies[module]),
                    "dependents": list(module_dependents[module])
                }
                
                # Fill coupling matrix
                for other_module in all_modules:
                    if other_module in module_dependencies[module]:
                        coupling_matrix[module][other_module] = 1
                    else:
                        coupling_matrix[module][other_module] = 0
            
            # Identify highly coupled modules
            sorted_modules = sorted(coupling_scores.items(), key=lambda x: x[1]["coupling_score"], reverse=True)
            highly_coupled = sorted_modules[:5]  # Top 5 most coupled modules
            
            # Generate suggested improvements
            for module, metrics in highly_coupled:
                suggestions = []
                
                if metrics["afferent_coupling"] > 5:
                    suggestions.append(f"High afferent coupling ({metrics['afferent_coupling']}): Consider breaking this module into smaller, more focused modules")
                
                if metrics["efferent_coupling"] > 5:
                    suggestions.append(f"High efferent coupling ({metrics['efferent_coupling']}): Consider using dependency injection or interfaces to reduce direct dependencies")
                
                if metrics["instability"] > 0.7:
                    suggestions.append(f"High instability ({metrics['instability']:.2f}): This module depends on many others but few depend on it, making it volatile")
                
                if metrics["instability"] < 0.3:
                    suggestions.append(f"Low instability ({metrics['instability']:.2f}): This module is highly depended upon, changes could have wide impact")
                
                coupling_results["suggested_improvements"].append({
                    "module": module,
                    "coupling_score": metrics["coupling_score"],
                    "suggestions": suggestions
                })
            
            # Calculate overall coupling score
            overall_score = sum(metrics["coupling_score"] for metrics in coupling_scores.values()) / len(coupling_scores) if coupling_scores else 0
            
            # Store results
            coupling_results["module_coupling_scores"] = coupling_scores
            coupling_results["highly_coupled_modules"] = [
                {"module": module, "metrics": metrics} for module, metrics in highly_coupled
            ]
            coupling_results["coupling_matrix"] = coupling_matrix
            coupling_results["overall_coupling_score"] = overall_score
            
        except Exception as e:
            coupling_results["error"] = str(e)
        
        return coupling_results

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
    """Main entry point for the codebase analyzer."""
    
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
    
    # New function-specific options
    parser.add_argument("--call-chain-source", help="Source function for call chain analysis")
    parser.add_argument("--call-chain-target", help="Target function for call chain analysis")
    parser.add_argument("--exclude-patterns", nargs="+", help="Patterns to exclude in dead code detection")
    parser.add_argument("--max-depth", type=int, default=5, help="Maximum depth for graph traversal")
    parser.add_argument("--type-coverage-threshold", type=float, default=80.0, help="Threshold for type coverage warnings")
    
    args = parser.parse_args()
    
    try:
        # Initialize the analyzer
        analyzer = CodebaseAnalyzer(

            repo_path=args.repo_path,
            language=args.language
        )
        
        # Perform the analysis
        results = analyzer.analyze(
            categories=args.categories,
            output_format=args.output_format,
            output_file=args.output_file
        )
        
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
