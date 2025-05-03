"""
Unified Analysis Module for Codegen-on-OSS

This module serves as a central hub for all code analysis functionality, integrating
various specialized analysis components into a cohesive system.
"""

import contextlib
import math
import os
import re
import subprocess
import tempfile
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union, Set
from urllib.parse import urlparse

import networkx as nx
import requests
import uvicorn
from codegen import Codebase
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.expressions.binary_expression import BinaryExpression
from codegen.sdk.core.expressions.comparison_expression import ComparisonExpression
from codegen.sdk.core.expressions.unary_expression import UnaryExpression
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.statements.for_loop_statement import ForLoopStatement
from codegen.sdk.core.statements.if_block_statement import IfBlockStatement
from codegen.sdk.core.statements.try_catch_statement import TryCatchStatement
from codegen.sdk.core.statements.while_statement import WhileStatement
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.enums import EdgeType, SymbolType
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import from other analysis modules
from codegen_on_oss.analysis.codebase_context import CodebaseContext
from codegen_on_oss.analysis.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary
)
from codegen_on_oss.analysis.codegen_sdk_codebase import (
    get_codegen_sdk_subdirectories,
    get_codegen_sdk_codebase
)
from codegen_on_oss.analysis.current_code_codebase import (
    get_graphsitter_repo_path,
    get_codegen_codebase_base_path,
    get_current_code_codebase,
    import_all_codegen_sdk_modules,
    DocumentedObjects,
    get_documented_objects
)
from codegen_on_oss.analysis.document_functions import (
    hop_through_imports,
    get_extended_context,
    run as document_functions_run
)
from codegen_on_oss.analysis.mdx_docs_generation import (
    render_mdx_page_for_class,
    render_mdx_page_title,
    render_mdx_inheritence_section,
    render_mdx_attributes_section,
    render_mdx_methods_section,
    render_mdx_for_attribute,
    format_parameter_for_mdx,
    format_parameters_for_mdx,
    format_return_for_mdx,
    render_mdx_for_method,
    get_mdx_route_for_class,
    format_type_string,
    resolve_type_string,
    format_builtin_type_string,
    span_type_string_by_pipe,
    parse_link
)
from codegen_on_oss.analysis.module_dependencies import run as module_dependencies_run
from codegen_on_oss.analysis.symbolattr import print_symbol_attribution
from codegen_on_oss.analysis.analysis_import import (
    create_graph_from_codebase,
    convert_all_calls_to_kwargs,
    find_import_cycles,
    find_problematic_import_loops
)

# Create FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CodeAnalyzer:
    """
    Central class for code analysis that integrates all analysis components.
    
    This class serves as the main entry point for all code analysis functionality,
    providing a unified interface to access various analysis capabilities.
    """
    
    def __init__(self, codebase: Codebase):
        """
        Initialize the CodeAnalyzer with a codebase.
        
        Args:
            codebase: The Codebase object to analyze
        """
        self.codebase = codebase
        self._context = None
        self._initialized = False
        
    def initialize(self):
        """
        Initialize the analyzer by setting up the context and other necessary components.
        This is called automatically when needed but can be called explicitly for eager initialization.
        """
        if self._initialized:
            return
            
        # Initialize context if not already done
        if self._context is None:
            self._context = self._create_context()
            
        self._initialized = True
    
    def _create_context(self) -> CodebaseContext:
        """
        Create a CodebaseContext instance for the current codebase.
        
        Returns:
            A new CodebaseContext instance
        """
        # If the codebase already has a context, use it
        if hasattr(self.codebase, "ctx") and self.codebase.ctx is not None:
            return self.codebase.ctx
            
        # Otherwise, create a new context from the codebase's configuration
        from codegen.sdk.codebase.config import ProjectConfig
        from codegen.configs.models.codebase import CodebaseConfig
        
        # Create a project config from the codebase
        project_config = ProjectConfig(
            repo_operator=self.codebase.repo_operator,
            programming_language=self.codebase.programming_language,
            base_path=self.codebase.base_path
        )
        
        # Create and return a new context
        return CodebaseContext([project_config], config=CodebaseConfig())
    
    @property
    def context(self) -> CodebaseContext:
        """
        Get the CodebaseContext for the current codebase.
        
        Returns:
            A CodebaseContext object for the codebase
        """
        if not self._initialized:
            self.initialize()
            
        return self._context
    
    def get_codebase_summary(self) -> str:
        """
        Get a comprehensive summary of the codebase.
        
        Returns:
            A string containing summary information about the codebase
        """
        return get_codebase_summary(self.codebase)
    
    def get_file_summary(self, file_path: str) -> str:
        """
        Get a summary of a specific file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            A string containing summary information about the file
        """
        file = self.codebase.get_file(file_path)
        if file is None:
            return f"File not found: {file_path}"
        return get_file_summary(file)
    
    def get_class_summary(self, class_name: str) -> str:
        """
        Get a summary of a specific class.
        
        Args:
            class_name: Name of the class to analyze
            
        Returns:
            A string containing summary information about the class
        """
        for cls in self.codebase.classes:
            if cls.name == class_name:
                return get_class_summary(cls)
        return f"Class not found: {class_name}"
    
    def get_function_summary(self, function_name: str) -> str:
        """
        Get a summary of a specific function.
        
        Args:
            function_name: Name of the function to analyze
            
        Returns:
            A string containing summary information about the function
        """
        for func in self.codebase.functions:
            if func.name == function_name:
                return get_function_summary(func)
        return f"Function not found: {function_name}"
    
    def get_symbol_summary(self, symbol_name: str) -> str:
        """
        Get a summary of a specific symbol.
        
        Args:
            symbol_name: Name of the symbol to analyze
            
        Returns:
            A string containing summary information about the symbol
        """
        for symbol in self.codebase.symbols:
            if symbol.name == symbol_name:
                return get_symbol_summary(symbol)
        return f"Symbol not found: {symbol_name}"
    
    def find_symbol_by_name(self, symbol_name: str) -> Optional[Symbol]:
        """
        Find a symbol by its name.
        
        Args:
            symbol_name: Name of the symbol to find
            
        Returns:
            The Symbol object if found, None otherwise
        """
        for symbol in self.codebase.symbols:
            if symbol.name == symbol_name:
                return symbol
        return None
    
    def find_file_by_path(self, file_path: str) -> Optional[SourceFile]:
        """
        Find a file by its path.
        
        Args:
            file_path: Path to the file to find
            
        Returns:
            The SourceFile object if found, None otherwise
        """
        return self.codebase.get_file(file_path)
    
    def find_class_by_name(self, class_name: str) -> Optional[Class]:
        """
        Find a class by its name.
        
        Args:
            class_name: Name of the class to find
            
        Returns:
            The Class object if found, None otherwise
        """
        for cls in self.codebase.classes:
            if cls.name == class_name:
                return cls
        return None
    
    def find_function_by_name(self, function_name: str) -> Optional[Function]:
        """
        Find a function by its name.
        
        Args:
            function_name: Name of the function to find
            
        Returns:
            The Function object if found, None otherwise
        """
        for func in self.codebase.functions:
            if func.name == function_name:
                return func
        return None
    
    def document_functions(self) -> None:
        """
        Generate documentation for functions in the codebase.
        """
        document_functions_run(self.codebase)
    
    def analyze_imports(self) -> Dict[str, Any]:
        """
        Analyze import relationships in the codebase.
        
        Returns:
            A dictionary containing import analysis results
        """
        graph = create_graph_from_codebase(self.codebase.repo_name)
        cycles = find_import_cycles(graph)
        problematic_loops = find_problematic_import_loops(graph, cycles)
        
        return {
            "import_cycles": cycles,
            "problematic_loops": problematic_loops
        }
    
    def convert_args_to_kwargs(self) -> None:
        """
        Convert all function call arguments to keyword arguments.
        """
        convert_all_calls_to_kwargs(self.codebase)
    
    def visualize_module_dependencies(self) -> None:
        """
        Visualize module dependencies in the codebase.
        """
        module_dependencies_run(self.codebase)
    
    def generate_mdx_documentation(self, class_name: str) -> str:
        """
        Generate MDX documentation for a class.
        
        Args:
            class_name: Name of the class to document
            
        Returns:
            MDX documentation as a string
        """
        for cls in self.codebase.classes:
            if cls.name == class_name:
                return render_mdx_page_for_class(cls)
        return f"Class not found: {class_name}"
    
    def print_symbol_attribution(self) -> None:
        """
        Print attribution information for symbols in the codebase.
        """
        print_symbol_attribution(self.codebase)
    
    def get_extended_symbol_context(self, symbol_name: str, degree: int = 2) -> Dict[str, List[str]]:
        """
        Get extended context (dependencies and usages) for a symbol.
        
        Args:
            symbol_name: Name of the symbol to analyze
            degree: How many levels deep to collect dependencies and usages
            
        Returns:
            A dictionary containing dependencies and usages
        """
        symbol = self.find_symbol_by_name(symbol_name)
        if symbol:
            dependencies, usages = get_extended_context(symbol, degree)
            return {
                "dependencies": [dep.name for dep in dependencies],
                "usages": [usage.name for usage in usages]
            }
        return {"dependencies": [], "usages": []}
    
    def get_symbol_dependencies(self, symbol_name: str) -> List[str]:
        """
        Get direct dependencies of a symbol.
        
        Args:
            symbol_name: Name of the symbol to analyze
            
        Returns:
            A list of dependency symbol names
        """
        symbol = self.find_symbol_by_name(symbol_name)
        if symbol and hasattr(symbol, "dependencies"):
            return [dep.name for dep in symbol.dependencies]
        return []
    
    def get_symbol_usages(self, symbol_name: str) -> List[str]:
        """
        Get direct usages of a symbol.
        
        Args:
            symbol_name: Name of the symbol to analyze
            
        Returns:
            A list of usage symbol names
        """
        symbol = self.find_symbol_by_name(symbol_name)
        if symbol and hasattr(symbol, "symbol_usages"):
            return [usage.name for usage in symbol.symbol_usages]
        return []
    
    def get_file_imports(self, file_path: str) -> List[str]:
        """
        Get all imports in a file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            A list of import statements
        """
        file = self.find_file_by_path(file_path)
        if file and hasattr(file, "imports"):
            return [imp.source for imp in file.imports]
        return []
    
    def get_file_exports(self, file_path: str) -> List[str]:
        """
        Get all exports from a file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            A list of exported symbol names
        """
        file = self.find_file_by_path(file_path)
        if file is None:
            return []
            
        exports = []
        for symbol in file.symbols:
            # Check if this symbol is exported
            if hasattr(symbol, "is_exported") and symbol.is_exported:
                exports.append(symbol.name)
            # For TypeScript/JavaScript, check for export keyword
            elif hasattr(symbol, "modifiers") and "export" in symbol.modifiers:
                exports.append(symbol.name)
                
        return exports
    
    def analyze_complexity(self) -> Dict[str, Any]:
        """
        Analyze code complexity metrics for the codebase.
        
        Returns:
            A dictionary containing complexity metrics
        """
        results = {}
        
        # Analyze cyclomatic complexity
        complexity_results = []
        for func in self.codebase.functions:
            if hasattr(func, "code_block"):
                complexity = calculate_cyclomatic_complexity(func)
                complexity_results.append({
                    "name": func.name,
                    "complexity": complexity,
                    "rank": cc_rank(complexity)
                })
        
        # Calculate average complexity
        if complexity_results:
            avg_complexity = sum(item["complexity"] for item in complexity_results) / len(complexity_results)
        else:
            avg_complexity = 0
        
        results["cyclomatic_complexity"] = {
            "functions": complexity_results,
            "average": avg_complexity
        }
        
        # Analyze line metrics
        line_metrics = {}
        total_loc = 0
        total_lloc = 0
        total_sloc = 0
        total_comments = 0
        
        for file in self.codebase.files:
            if hasattr(file, "source"):
                loc, lloc, sloc, comments = count_lines(file.source)
                line_metrics[file.name] = {
                    "loc": loc,
                    "lloc": lloc,
                    "sloc": sloc,
                    "comments": comments,
                    "comment_ratio": comments / loc if loc > 0 else 0
                }
                total_loc += loc
                total_lloc += lloc
                total_sloc += sloc
                total_comments += comments
        
        results["line_metrics"] = {
            "files": line_metrics,
            "total": {
                "loc": total_loc,
                "lloc": total_lloc,
                "sloc": total_sloc,
                "comments": total_comments,
                "comment_ratio": total_comments / total_loc if total_loc > 0 else 0
            }
        }
        
        # Analyze Halstead metrics
        halstead_results = []
        total_volume = 0
        
        for func in self.codebase.functions:
            if hasattr(func, "code_block"):
                operators, operands = get_operators_and_operands(func)
                volume, N1, N2, n1, n2 = calculate_halstead_volume(operators, operands)
                
                # Calculate maintainability index
                loc = len(func.code_block.source.splitlines())
                complexity = calculate_cyclomatic_complexity(func)
                mi_score = calculate_maintainability_index(volume, complexity, loc)
                
                halstead_results.append({
                    "name": func.name,
                    "volume": volume,
                    "unique_operators": n1,
                    "unique_operands": n2,
                    "total_operators": N1,
                    "total_operands": N2,
                    "maintainability_index": mi_score,
                    "maintainability_rank": get_maintainability_rank(mi_score)
                })
                
                total_volume += volume
        
        results["halstead_metrics"] = {
            "functions": halstead_results,
            "total_volume": total_volume,
            "average_volume": total_volume / len(halstead_results) if halstead_results else 0
        }
        
        # Analyze inheritance depth
        inheritance_results = []
        total_doi = 0
        
        for cls in self.codebase.classes:
            doi = calculate_doi(cls)
            inheritance_results.append({
                "name": cls.name,
                "depth": doi
            })
            total_doi += doi
        
        results["inheritance_depth"] = {
            "classes": inheritance_results,
            "average": total_doi / len(inheritance_results) if inheritance_results else 0
        }
        
        # Analyze dependencies
        dependency_graph = nx.DiGraph()
        
        for symbol in self.codebase.symbols:
            dependency_graph.add_node(symbol.name)
            
            if hasattr(symbol, "dependencies"):
                for dep in symbol.dependencies:
                    dependency_graph.add_edge(symbol.name, dep.name)
        
        # Calculate centrality metrics
        if dependency_graph.nodes:
            try:
                in_degree_centrality = nx.in_degree_centrality(dependency_graph)
                out_degree_centrality = nx.out_degree_centrality(dependency_graph)
                betweenness_centrality = nx.betweenness_centrality(dependency_graph)
                
                # Find most central symbols
                most_imported = sorted(in_degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
                most_dependent = sorted(out_degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
                most_central = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
                
                results["dependency_metrics"] = {
                    "most_imported": most_imported,
                    "most_dependent": most_dependent,
                    "most_central": most_central
                }
            except Exception as e:
                results["dependency_metrics"] = {"error": str(e)}
        
        return results
    
    def get_file_dependencies(self, file_path: str) -> Dict[str, List[str]]:
        """
        Get all dependencies of a file, including imports and symbol dependencies.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            A dictionary containing different types of dependencies
        """
        file = self.find_file_by_path(file_path)
        if file is None:
            return {"imports": [], "symbols": [], "external": []}
            
        imports = []
        symbols = []
        external = []
        
        # Get imports
        if hasattr(file, "imports"):
            for imp in file.imports:
                if hasattr(imp, "module_name"):
                    imports.append(imp.module_name)
                elif hasattr(imp, "source"):
                    imports.append(imp.source)
        
        # Get symbol dependencies
        for symbol in file.symbols:
            if hasattr(symbol, "dependencies"):
                for dep in symbol.dependencies:
                    if isinstance(dep, ExternalModule):
                        external.append(dep.name)
                    else:
                        symbols.append(dep.name)
        
        return {
            "imports": list(set(imports)),
            "symbols": list(set(symbols)),
            "external": list(set(external))
        }
    
    def get_codebase_structure(self) -> Dict[str, Any]:
        """
        Get a hierarchical representation of the codebase structure.
        
        Returns:
            A dictionary representing the codebase structure
        """
        # Initialize the structure with root directories
        structure = {}
        
        # Process all files
        for file in self.codebase.files:
            path_parts = file.name.split('/')
            current = structure
            
            # Build the directory structure
            for i, part in enumerate(path_parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Add the file with its symbols
            file_info = {
                "type": "file",
                "symbols": []
            }
            
            # Add symbols in the file
            for symbol in file.symbols:
                symbol_info = {
                    "name": symbol.name,
                    "type": str(symbol.symbol_type) if hasattr(symbol, "symbol_type") else "unknown"
                }
                file_info["symbols"].append(symbol_info)
            
            current[path_parts[-1]] = file_info
        
        return structure
    
    def get_monthly_commit_activity(self) -> Dict[str, int]:
        """
        Get monthly commit activity for the codebase.
        
        Returns:
            A dictionary mapping month strings to commit counts
        """
        if not hasattr(self.codebase, "repo_operator") or not self.codebase.repo_operator:
            return {}
            
        try:
            # Get commits from the last year
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=365)
            
            # Get all commits in the date range
            commits = self.codebase.repo_operator.get_commits(since=start_date, until=end_date)
            
            # Group commits by month
            monthly_commits = {}
            for commit in commits:
                month_key = commit.committed_datetime.strftime("%Y-%m")
                if month_key in monthly_commits:
                    monthly_commits[month_key] += 1
                else:
                    monthly_commits[month_key] = 1
                    
            return monthly_commits
        except Exception as e:
            return {"error": str(e)}
    
    def get_file_change_frequency(self, limit: int = 10) -> Dict[str, int]:
        """
        Get the most frequently changed files in the codebase.
        
        Args:
            limit: Maximum number of files to return
            
        Returns:
            A dictionary mapping file paths to change counts
        """
        if not hasattr(self.codebase, "repo_operator") or not self.codebase.repo_operator:
            return {}
            
        try:
            # Get commits from the last year
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=365)
            
            # Get all commits in the date range
            commits = self.codebase.repo_operator.get_commits(since=start_date, until=end_date)
            
            # Count file changes
            file_changes = {}
            for commit in commits:
                for file in commit.stats.files:
                    if file in file_changes:
                        file_changes[file] += 1
                    else:
                        file_changes[file] = 1
            
            # Sort by change count and limit results
            sorted_files = sorted(file_changes.items(), key=lambda x: x[1], reverse=True)[:limit]
            return dict(sorted_files)
        except Exception as e:
            return {"error": str(e)}

def get_monthly_commits(repo_path: str) -> Dict[str, int]:
    """
    Get monthly commit activity for a repository.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        A dictionary mapping month strings to commit counts
    """
    # ... existing function body ...

def get_extended_context(symbol: Symbol, degree: int = 2) -> Tuple[Set[Symbol], Set[Symbol]]:
    """
    Get extended context for a symbol, including dependencies and usages.
    
    Args:
        symbol: The symbol to analyze
        degree: The degree of separation to include
        
    Returns:
        A tuple of (dependencies, usages) sets
    """
    # ... existing function body ...

def calculate_cyclomatic_complexity(func: Function) -> int:
    """
    Calculate cyclomatic complexity for a function.
    
    Args:
        func: The function to analyze
        
    Returns:
        The cyclomatic complexity score
    """
    # ... existing function body ...

def count_lines(source: str) -> Tuple[int, int, int, int]:
    """
    Count different types of lines in source code.
    
    Args:
        source: The source code to analyze
        
    Returns:
        A tuple of (total lines, logical lines, source lines, comment lines)
    """
    # ... existing function body ...

def cc_rank(score: float) -> str:
    """
    Get a rank for a cyclomatic complexity score.
    
    Args:
        score: The complexity score
        
    Returns:
        A rank string (A-F)
    """
    # ... existing function body ...

def get_operators_and_operands(func: Function) -> Tuple[List[str], List[str]]:
    """
    Extract operators and operands from a function.
    
    Args:
        func: The function to analyze
        
    Returns:
        A tuple of (operators, operands) lists
    """
    # ... existing function body ...

def calculate_halstead_volume(operators: List[str], operands: List[str]) -> Tuple[float, int, int, int, int]:
    """
    Calculate Halstead volume metrics.
    
    Args:
        operators: List of operators in the code
        operands: List of operands in the code
        
    Returns:
        A tuple of (volume, total operators, total operands, unique operators, unique operands)
    """
    # ... existing function body ...

def calculate_maintainability_index(volume: float, complexity: int, loc: int) -> float:
    """
    Calculate maintainability index.
    
    Args:
        volume: Halstead volume
        complexity: Cyclomatic complexity
        loc: Lines of code
        
    Returns:
        The maintainability index score
    """
    # ... existing function body ...

def get_maintainability_rank(score: float) -> str:
    """
    Get a rank for a maintainability index score.
    
    Args:
        score: The maintainability score
        
    Returns:
        A rank string (A-F)
    """
    # ... existing function body ...

def calculate_doi(cls: Class) -> int:
    """
    Calculate depth of inheritance for a class.
    
    Args:
        cls: The class to analyze
        
    Returns:
        The depth of inheritance
    """
    # ... existing function body ...

class CodebaseAnalyzer:
    """
    Analyzer for codebase structure and metrics.
    """
    
    def __init__(self, codebase: Codebase) -> None:
        """
        Initialize the analyzer with a codebase.
        
        Args:
            codebase: The codebase to analyze
        """
        self.codebase = codebase
        self._context = None
        self._initialized = False
        
    def initialize(self) -> None:
        """
        Initialize the analyzer by setting up the context and other necessary components.
        This is called automatically when needed but can be called explicitly for eager initialization.
        """
        if self._initialized:
            return
            
        # Initialize context if not already done
        if self._context is None:
            self._context = self._create_context()
            
        self._initialized = True
    
    def _create_context(self) -> CodebaseContext:
        """
        Create a CodebaseContext instance for the current codebase.
        
        Returns:
            A new CodebaseContext instance
        """
        # If the codebase already has a context, use it
        if hasattr(self.codebase, "ctx") and self.codebase.ctx is not None:
            return self.codebase.ctx
            
        # Otherwise, create a new context from the codebase's configuration
        from codegen.sdk.codebase.config import ProjectConfig
        from codegen.configs.models.codebase import CodebaseConfig
        
        # Create a project config from the codebase
        project_config = ProjectConfig(
            repo_operator=self.codebase.repo_operator,
            programming_language=self.codebase.programming_language,
            base_path=self.codebase.base_path
        )
        
        # Create and return a new context
        return CodebaseContext([project_config], config=CodebaseConfig())
    
    @property
    def context(self) -> CodebaseContext:
        """
        Get the CodebaseContext for the codebase.
        
        Returns:
            A CodebaseContext object for the codebase
        """
        if not self._initialized:
            self.initialize()
            
        return self._context
    
    def get_codebase_summary(self) -> str:
        """
        Generate a summary of the codebase.
        
        Returns:
            A string summary of the codebase
        """
        return get_codebase_summary(self.codebase)
    
    def get_file_summary(self, file_path: str) -> str:
        """
        Get a summary of a specific file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            A string containing summary information about the file
        """
        file = self.codebase.get_file(file_path)
        if file is None:
            return f"File not found: {file_path}"
        return get_file_summary(file)
    
    def get_class_summary(self, class_name: str) -> str:
        """
        Get a summary of a specific class.
        
        Args:
            class_name: Name of the class to analyze
            
        Returns:
            A string containing summary information about the class
        """
        for cls in self.codebase.classes:
            if cls.name == class_name:
                return get_class_summary(cls)
        return f"Class not found: {class_name}"
    
    def get_function_summary(self, function_name: str) -> str:
        """
        Get a summary of a specific function.
        
        Args:
            function_name: Name of the function to analyze
            
        Returns:
            A string containing summary information about the function
        """
        for func in self.codebase.functions:
            if func.name == function_name:
                return get_function_summary(func)
        return f"Function not found: {function_name}"
    
    def get_symbol_summary(self, symbol_name: str) -> str:
        """
        Get a summary of a specific symbol.
        
        Args:
            symbol_name: Name of the symbol to analyze
            
        Returns:
            A string containing summary information about the symbol
        """
        for symbol in self.codebase.symbols:
            if symbol.name == symbol_name:
                return get_symbol_summary(symbol)
        return f"Symbol not found: {symbol_name}"
    
    def find_symbol_by_name(self, symbol_name: str) -> Optional[Symbol]:
        """
        Find a symbol by its name.
        
        Args:
            symbol_name: Name of the symbol to find
            
        Returns:
            The Symbol object if found, None otherwise
        """
        for symbol in self.codebase.symbols:
            if symbol.name == symbol_name:
                return symbol
        return None
    
    def find_file_by_path(self, file_path: str) -> Optional[SourceFile]:
        """
        Find a file by its path.
        
        Args:
            file_path: Path to the file to find
            
        Returns:
            The SourceFile object if found, None otherwise
        """
        return self.codebase.get_file(file_path)
    
    def find_class_by_name(self, class_name: str) -> Optional[Class]:
        """
        Find a class by its name.
        
        Args:
            class_name: Name of the class to find
            
        Returns:
            The Class object if found, None otherwise
        """
        for cls in self.codebase.classes:
            if cls.name == class_name:
                return cls
        return None
    
    def find_function_by_name(self, function_name: str) -> Optional[Function]:
        """
        Find a function by its name.
        
        Args:
            function_name: Name of the function to find
            
        Returns:
            The Function object if found, None otherwise
        """
        for func in self.codebase.functions:
            if func.name == function_name:
                return func
        return None
    
    def document_functions(self) -> None:
        """
        Generate documentation for functions in the codebase.
        """
        document_functions_run(self.codebase)
    
    def analyze_imports(self) -> Dict[str, Any]:
        """
        Analyze import relationships in the codebase.
        
        Returns:
            A dictionary containing import analysis results
        """
        graph = create_graph_from_codebase(self.codebase.repo_name)
        cycles = find_import_cycles(graph)
        problematic_loops = find_problematic_import_loops(graph, cycles)
        
        return {
            "import_cycles": cycles,
            "problematic_loops": problematic_loops
        }
    
    def convert_args_to_kwargs(self) -> None:
        """
        Convert all function call arguments to keyword arguments.
        """
        convert_all_calls_to_kwargs(self.codebase)
    
    def visualize_module_dependencies(self) -> None:
        """
        Visualize module dependencies in the codebase.
        """
        module_dependencies_run(self.codebase)
    
    def generate_mdx_documentation(self, class_name: str) -> str:
        """
        Generate MDX documentation for a class.
        
        Args:
            class_name: Name of the class to document
            
        Returns:
            MDX documentation as a string
        """
        for cls in self.codebase.classes:
            if cls.name == class_name:
                return render_mdx_page_for_class(cls)
        return f"Class not found: {class_name}"
    
    def print_symbol_attribution(self) -> None:
        """
        Print attribution information for symbols in the codebase.
        """
        print_symbol_attribution(self.codebase)
    
    def get_extended_symbol_context(self, symbol_name: str, degree: int = 2) -> Dict[str, List[str]]:
        """
        Get extended context for a symbol, including dependencies and usages.
        
        Args:
            symbol_name: Name of the symbol to analyze
            degree: The degree of separation to include
            
        Returns:
            A dictionary containing dependencies and usages
        """
        symbol = self.find_symbol_by_name(symbol_name)
        if symbol:
            dependencies, usages = get_extended_context(symbol, degree)
            return {
                "dependencies": [dep.name for dep in dependencies],
                "usages": [usage.name for usage in usages]
            }
        return {"dependencies": [], "usages": []}
    
    def get_symbol_dependencies(self, symbol_name: str) -> List[str]:
        """
        Get direct dependencies of a symbol.
        
        Args:
            symbol_name: Name of the symbol to analyze
            
        Returns:
            A list of dependency symbol names
        """
        symbol = self.find_symbol_by_name(symbol_name)
        if symbol and hasattr(symbol, "dependencies"):
            return [dep.name for dep in symbol.dependencies]
        return []
    
    def get_symbol_usages(self, symbol_name: str) -> List[str]:
        """
        Get direct usages of a symbol.
        
        Args:
            symbol_name: Name of the symbol to analyze
            
        Returns:
            A list of usage symbol names
        """
        symbol = self.find_symbol_by_name(symbol_name)
        if symbol and hasattr(symbol, "symbol_usages"):
            return [usage.name for usage in symbol.symbol_usages]
        return []
    
    def get_file_imports(self, file_path: str) -> List[str]:
        """
        Get all imports in a file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            A list of import statements
        """
        file = self.find_file_by_path(file_path)
        if file and hasattr(file, "imports"):
            return [imp.source for imp in file.imports]
        return []
    
    def get_file_exports(self, file_path: str) -> List[str]:
        """
        Get all exports from a file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            A list of exported symbol names
        """
        file = self.find_file_by_path(file_path)
        if file is None:
            return []
            
        exports = []
        for symbol in file.symbols:
            # Check if this symbol is exported
            if hasattr(symbol, "is_exported") and symbol.is_exported:
                exports.append(symbol.name)
            # For TypeScript/JavaScript, check for export keyword
            elif hasattr(symbol, "modifiers") and "export" in symbol.modifiers:
                exports.append(symbol.name)
                
        return exports
    
    def analyze_complexity(self) -> Dict[str, Any]:
        """
        Analyze code complexity metrics for the codebase.
        
        Returns:
            A dictionary containing complexity metrics
        """
        results = {}
        
        # Analyze cyclomatic complexity
        complexity_results = []
        for func in self.codebase.functions:
            if hasattr(func, "code_block"):
                complexity = calculate_cyclomatic_complexity(func)
                complexity_results.append({
                    "name": func.name,
                    "complexity": complexity,
                    "rank": cc_rank(complexity)
                })
        
        # Calculate average complexity
        if complexity_results:
            avg_complexity = sum(item["complexity"] for item in complexity_results) / len(complexity_results)
        else:
            avg_complexity = 0
        
        results["cyclomatic_complexity"] = {
            "functions": complexity_results,
            "average": avg_complexity
        }
        
        # Analyze line metrics
        line_metrics = {}
        total_loc = 0
        total_lloc = 0
        total_sloc = 0
        total_comments = 0
        
        for file in self.codebase.files:
            if hasattr(file, "source"):
                loc, lloc, sloc, comments = count_lines(file.source)
                line_metrics[file.name] = {
                    "loc": loc,
                    "lloc": lloc,
                    "sloc": sloc,
                    "comments": comments,
                    "comment_ratio": comments / loc if loc > 0 else 0
                }
                total_loc += loc
                total_lloc += lloc
                total_sloc += sloc
                total_comments += comments
        
        results["line_metrics"] = {
            "files": line_metrics,
            "total": {
                "loc": total_loc,
                "lloc": total_lloc,
                "sloc": total_sloc,
                "comments": total_comments,
                "comment_ratio": total_comments / total_loc if total_loc > 0 else 0
            }
        }
        
        # Analyze Halstead metrics
        halstead_results = []
        total_volume = 0
        
        for func in self.codebase.functions:
            if hasattr(func, "code_block"):
                operators, operands = get_operators_and_operands(func)
                volume, N1, N2, n1, n2 = calculate_halstead_volume(operators, operands)
                
                # Calculate maintainability index
                loc = len(func.code_block.source.splitlines())
                complexity = calculate_cyclomatic_complexity(func)
                mi_score = calculate_maintainability_index(volume, complexity, loc)
                
                halstead_results.append({
                    "name": func.name,
                    "volume": volume,
                    "unique_operators": n1,
                    "unique_operands": n2,
                    "total_operators": N1,
                    "total_operands": N2,
                    "maintainability_index": mi_score,
                    "maintainability_rank": get_maintainability_rank(mi_score)
                })
                
                total_volume += volume
        
        results["halstead_metrics"] = {
            "functions": halstead_results,
            "total_volume": total_volume,
            "average_volume": total_volume / len(halstead_results) if halstead_results else 0
        }
        
        # Analyze inheritance depth
        inheritance_results = []
        total_doi = 0
        
        for cls in self.codebase.classes:
            doi = calculate_doi(cls)
            inheritance_results.append({
                "name": cls.name,
                "depth": doi
            })
            total_doi += doi
        
        results["inheritance_depth"] = {
            "classes": inheritance_results,
            "average": total_doi / len(inheritance_results) if inheritance_results else 0
        }
        
        # Analyze dependencies
        dependency_graph = nx.DiGraph()
        
        for symbol in self.codebase.symbols:
            dependency_graph.add_node(symbol.name)
            
            if hasattr(symbol, "dependencies"):
                for dep in symbol.dependencies:
                    dependency_graph.add_edge(symbol.name, dep.name)
        
        # Calculate centrality metrics
        if dependency_graph.nodes:
            try:
                in_degree_centrality = nx.in_degree_centrality(dependency_graph)
                out_degree_centrality = nx.out_degree_centrality(dependency_graph)
                betweenness_centrality = nx.betweenness_centrality(dependency_graph)
                
                # Find most central symbols
                most_imported = sorted(in_degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
                most_dependent = sorted(out_degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
                most_central = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
                
                results["dependency_metrics"] = {
                    "most_imported": most_imported,
                    "most_dependent": most_dependent,
                    "most_central": most_central
                }
            except Exception as e:
                results["dependency_metrics"] = {"error": str(e)}
        
        return results
    
    def get_file_dependencies(self, file_path: str) -> Dict[str, List[str]]:
        """
        Get all dependencies of a file, including imports and symbol dependencies.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            A dictionary containing different types of dependencies
        """
        file = self.find_file_by_path(file_path)
        if file is None:
            return {"imports": [], "symbols": [], "external": []}
            
        imports = []
        symbols = []
        external = []
        
        # Get imports
        if hasattr(file, "imports"):
            for imp in file.imports:
                if hasattr(imp, "module_name"):
                    imports.append(imp.module_name)
                elif hasattr(imp, "source"):
                    imports.append(imp.source)
        
        # Get symbol dependencies
        for symbol in file.symbols:
            if hasattr(symbol, "dependencies"):
                for dep in symbol.dependencies:
                    if isinstance(dep, ExternalModule):
                        external.append(dep.name)
                    else:
                        symbols.append(dep.name)
        
        return {
            "imports": list(set(imports)),
            "symbols": list(set(symbols)),
            "external": list(set(external))
        }
    
    def get_codebase_structure(self) -> Dict[str, Any]:
        """
        Get a hierarchical representation of the codebase structure.
        
        Returns:
            A dictionary representing the codebase structure
        """
        # Initialize the structure with root directories
        structure = {}
        
        # Process all files
        for file in self.codebase.files:
            path_parts = file.name.split('/')
            current = structure
            
            # Build the directory structure
            for i, part in enumerate(path_parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Add the file with its symbols
            file_info = {
                "type": "file",
                "symbols": []
            }
            
            # Add symbols in the file
            for symbol in file.symbols:
                symbol_info = {
                    "name": symbol.name,
                    "type": str(symbol.symbol_type) if hasattr(symbol, "symbol_type") else "unknown"
                }
                file_info["symbols"].append(symbol_info)
            
            current[path_parts[-1]] = file_info
        
        return structure
    
    def get_monthly_commit_activity(self) -> Dict[str, int]:
        """
        Get monthly commit activity for the codebase.
        
        Returns:
            A dictionary mapping month strings to commit counts
        """
        if not hasattr(self.codebase, "repo_operator") or not self.codebase.repo_operator:
            return {}
            
        try:
            # Get commits from the last year
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=365)
            
            # Get all commits in the date range
            commits = self.codebase.repo_operator.get_commits(since=start_date, until=end_date)
            
            # Group commits by month
            monthly_commits = {}
            for commit in commits:
                month_key = commit.committed_datetime.strftime("%Y-%m")
                if month_key in monthly_commits:
                    monthly_commits[month_key] += 1
                else:
                    monthly_commits[month_key] = 1
                    
            return monthly_commits
        except Exception as e:
            return {"error": str(e)}
    
    def get_file_change_frequency(self, limit: int = 10) -> Dict[str, int]:
        """
        Get the most frequently changed files in the codebase.
        
        Args:
            limit: Maximum number of files to return
            
        Returns:
            A dictionary mapping file paths to change counts
        """
        if not hasattr(self.codebase, "repo_operator") or not self.codebase.repo_operator:
            return {}
            
        try:
            # Get commits from the last year
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=365)
            
            # Get all commits in the date range
            commits = self.codebase.repo_operator.get_commits(since=start_date, until=end_date)
            
            # Count file changes
            file_changes = {}
            for commit in commits:
                for file in commit.stats.files:
                    if file in file_changes:
                        file_changes[file] += 1
                    else:
                        file_changes[file] = 1
            
            # Sort by change count and limit results
            sorted_files = sorted(file_changes.items(), key=lambda x: x[1], reverse=True)[:limit]
            return dict(sorted_files)
        except Exception as e:
            return {"error": str(e)}

def get_monthly_commits(repo_path: str) -> Dict[str, int]:
    """
    Get monthly commit activity for a repository.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        A dictionary mapping month strings to commit counts
    """
    # ... existing function body ...

def get_extended_context(symbol: Symbol, degree: int = 2) -> Tuple[Set[Symbol], Set[Symbol]]:
    """
    Get extended context for a symbol, including dependencies and usages.
    
    Args:
        symbol: The symbol to analyze
        degree: The degree of separation to include
        
    Returns:
        A tuple of (dependencies, usages) sets
    """
    # ... existing function body ...

def calculate_cyclomatic_complexity(func: Function) -> int:
    """
    Calculate cyclomatic complexity for a function.
    
    Args:
        func: The function to analyze
        
    Returns:
        The cyclomatic complexity score
    """
    # ... existing function body ...

def count_lines(source: str) -> Tuple[int, int, int, int]:
    """
    Count different types of lines in source code.
    
    Args:
        source: The source code to analyze
        
    Returns:
        A tuple of (total lines, logical lines, source lines, comment lines)
    """
    # ... existing function body ...

def cc_rank(score: float) -> str:
    """
    Get a rank for a cyclomatic complexity score.
    
    Args:
        score: The complexity score
        
    Returns:
        A rank string (A-F)
    """
    # ... existing function body ...

def get_operators_and_operands(func: Function) -> Tuple[List[str], List[str]]:
    """
    Extract operators and operands from a function.
    
    Args:
        func: The function to analyze
        
    Returns:
        A tuple of (operators, operands) lists
    """
    # ... existing function body ...

def calculate_halstead_volume(operators: List[str], operands: List[str]) -> Tuple[float, int, int, int, int]:
    """
    Calculate Halstead volume metrics.
    
    Args:
        operators: List of operators in the code
        operands: List of operands in the code
        
    Returns:
        A tuple of (volume, total operators, total operands, unique operators, unique operands)
    """
    # ... existing function body ...

def calculate_maintainability_index(volume: float, complexity: int, loc: int) -> float:
    """
    Calculate maintainability index.
    
    Args:
        volume: Halstead volume
        complexity: Cyclomatic complexity
        loc: Lines of code
        
    Returns:
        The maintainability index score
    """
    # ... existing function body ...

def get_maintainability_rank(score: float) -> str:
    """
    Get a rank for a maintainability index score.
    
    Args:
        score: The maintainability score
        
    Returns:
        A rank string (A-F)
    """
    # ... existing function body ...

def calculate_doi(cls: Class) -> int:
    """
    Calculate depth of inheritance for a class.
    
    Args:
        cls: The class to analyze
        
    Returns:
        The depth of inheritance
    """
    # ... existing function body ...

# ... rest of existing code ...

def get_github_repo_description(repo_url):
    """
    Get the description of a GitHub repository.
    
    Args:
        repo_url: The repository URL in the format 'owner/repo'
        
    Returns:
        The repository description
    """
    api_url = f"https://api.github.com/repos/{repo_url}"

    response = requests.get(api_url)

    if response.status_code == 200:
        repo_data = response.json()
        return repo_data.get("description", "No description available")
    else:
        return ""

class RepoRequest(BaseModel):
    """Request model for repository analysis."""
    repo_url: str


@app.post("/analyze_repo")
async def analyze_repo(request: RepoRequest) -> Dict[str, Any]:
    """
    Analyze a repository and return comprehensive metrics.
    
    Args:
        request: The repository request containing the repo URL
        
    Returns:
        A dictionary of analysis results
    """
    repo_url = request.repo_url
    codebase = Codebase.from_repo(repo_url)
    
    # Create analyzer instance
    analyzer = CodeAnalyzer(codebase)
    
    # Get complexity metrics
    complexity_results = analyzer.analyze_complexity()
    
    # Get monthly commits
    monthly_commits = get_monthly_commits(repo_url)
    
    # Get repository description
    desc = get_github_repo_description(repo_url)
    
    # Analyze imports
    import_analysis = analyzer.analyze_imports()
    
    # Combine all results
    results = {
        "repo_url": repo_url,
        "line_metrics": complexity_results["line_metrics"],
        "cyclomatic_complexity": complexity_results["cyclomatic_complexity"],
        "description": desc,
        "num_files": len(codebase.files),
        "num_functions": len(codebase.functions),
        "num_classes": len(codebase.classes),
        "monthly_commits": monthly_commits,
        "import_analysis": import_analysis
    }
    
    # Add depth of inheritance
    total_doi = sum(calculate_doi(cls) for cls in codebase.classes)
    results["depth_of_inheritance"] = {
        "average": (total_doi / len(codebase.classes) if codebase.classes else 0),
    }
    
    # Add Halstead metrics
    total_volume = 0
    num_callables = 0
    total_mi = 0
    
    for func in codebase.functions:
        if not hasattr(func, "code_block"):
            continue
            
        complexity = calculate_cyclomatic_complexity(func)
        operators, operands = get_operators_and_operands(func)
        volume, _, _, _, _ = calculate_halstead_volume(operators, operands)
        loc = len(func.code_block.source.splitlines())
        mi_score = calculate_maintainability_index(volume, complexity, loc)
        
        total_volume += volume
        total_mi += mi_score
        num_callables += 1
    
    results["halstead_metrics"] = {
        "total_volume": int(total_volume),
        "average_volume": (
            int(total_volume / num_callables) if num_callables > 0 else 0
        ),
    }
    
    results["maintainability_index"] = {
        "average": (
            int(total_mi / num_callables) if num_callables > 0 else 0
        ),
    }
    
    return results


if __name__ == "__main__":
    # Run the FastAPI app locally with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
