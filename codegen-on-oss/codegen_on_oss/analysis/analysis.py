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
from typing import Any, Dict, List, Optional, Tuple, Union, cast
from urllib.parse import urlparse

import networkx as nx
import requests
import uvicorn
from codegen import Codebase
from codegen.sdk.core.binary_expression import BinaryExpression
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.conditional_expression import ConditionalExpression
from codegen.sdk.core.expressions.unary_expression import UnaryExpression
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.directory import Directory
from codegen.sdk.core.function import Function
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.statements.for_loop_statement import ForLoopStatement
from codegen.sdk.core.statements.if_statement import IfStatement
from codegen.sdk.core.statements.switch_statement import SwitchStatement
from codegen.sdk.core.statements.while_statement import WhileStatement
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.enums import EdgeType, SymbolType
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from zoneinfo import ZoneInfo

# Import from other analysis modules
from codegen_on_oss.analysis.codebase_context import CodebaseContext
from codegen_on_oss.analysis.codebase_analysis import (
    calculate_cyclomatic_complexity,
    calculate_doi,
    calculate_halstead_volume,
    calculate_maintainability_index,
    cc_rank,
    count_lines,
    get_maintainability_rank,
    get_operators_and_operands,
    print_symbol_attribution,
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
        Analyze imports in the codebase.
        
        Returns:
            A dictionary containing import analysis results
        """
        graph = create_graph_from_codebase(self.codebase)
        cycles = find_import_cycles(graph)
        problematic_loops = find_problematic_import_loops(graph, cycles)
        
        return {
            "import_graph": graph,
            "cycles": cycles,
            "problematic_loops": problematic_loops
        }
    
    def analyze_complexity(self) -> Dict[str, Any]:
        """
        Analyze code complexity metrics for the codebase.
        
        Returns:
            A dictionary containing complexity metrics
        """
        # Calculate cyclomatic complexity for all functions
        complexity_results = {}
        for func in self.codebase.functions:
            if hasattr(func, "code_block"):
                complexity = calculate_cyclomatic_complexity(func)
                complexity_results[func.name] = {
                    "complexity": complexity,
                    "rank": cc_rank(complexity)
                }
        
        # Calculate line metrics for all files
        line_metrics = {}
        for file in self.codebase.files:
            if hasattr(file, "source"):
                loc, lloc, sloc, comments = count_lines(file.source)
                line_metrics[file.name] = {
                    "loc": loc,
                    "lloc": lloc,
                    "sloc": sloc,
                    "comments": comments
                }
        
        return {
            "cyclomatic_complexity": complexity_results,
            "line_metrics": line_metrics
        }
    
    def get_dependency_graph(self) -> nx.DiGraph:
        """
        Generate a dependency graph for the codebase.
        
        Returns:
            A NetworkX DiGraph representing dependencies
        """
        G = nx.DiGraph()
        
        # Add nodes for all files
        for file in self.codebase.files:
            G.add_node(file.name, type="file")
        
        # Add edges for imports
        for file in self.codebase.files:
            for imp in file.imports:
                if imp.imported_symbol and hasattr(imp.imported_symbol, "file"):
                    imported_file = imp.imported_symbol.file
                    if imported_file and imported_file.name != file.name:
                        G.add_edge(file.name, imported_file.name)
        
        return G
    
    def get_symbol_attribution(self, symbol_name: str) -> str:
        """
        Get attribution information for a symbol.
        
        Args:
            symbol_name: Name of the symbol to analyze
            
        Returns:
            A string containing attribution information
        """
        symbol = self.find_symbol_by_name(symbol_name)
        if symbol is None:
            return f"Symbol not found: {symbol_name}"
        
        return print_symbol_attribution(symbol)
    
    def get_context_for_symbol(self, symbol_name: str) -> Dict[str, Any]:
        """
        Get extended context information for a symbol using CodebaseContext.
        
        Args:
            symbol_name: Name of the symbol to analyze
            
        Returns:
            A dictionary containing context information
        """
        symbol = self.find_symbol_by_name(symbol_name)
        if symbol is None:
            return {"error": f"Symbol not found: {symbol_name}"}
        
        # Use the context to get more information about the symbol
        ctx = self.context
        
        # Get symbol node ID in the context graph
        node_id = None
        for n_id, node in enumerate(ctx.nodes):
            if isinstance(node, Symbol) and node.name == symbol_name:
                node_id = n_id
                break
        
        if node_id is None:
            return {"error": f"Symbol not found in context: {symbol_name}"}
        
        # Get predecessors (symbols that use this symbol)
        predecessors = []
        for pred in ctx.predecessors(node_id):
            if isinstance(pred, Symbol):
                predecessors.append({
                    "name": pred.name,
                    "type": pred.symbol_type.name if hasattr(pred, "symbol_type") else "Unknown"
                })
        
        # Get successors (symbols used by this symbol)
        successors = []
        for succ in ctx.successors(node_id):
            if isinstance(succ, Symbol):
                successors.append({
                    "name": succ.name,
                    "type": succ.symbol_type.name if hasattr(succ, "symbol_type") else "Unknown"
                })
        
        return {
            "symbol": {
                "name": symbol.name,
                "type": symbol.symbol_type.name if hasattr(symbol, "symbol_type") else "Unknown",
                "file": symbol.file.name if hasattr(symbol, "file") else "Unknown"
            },
            "predecessors": predecessors,
            "successors": successors
        }
    
    def get_file_dependencies(self, file_path: str) -> Dict[str, Any]:
        """
        Get dependency information for a file using CodebaseContext.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            A dictionary containing dependency information
        """
        file = self.find_file_by_path(file_path)
        if file is None:
            return {"error": f"File not found: {file_path}"}
        
        # Use the context to get more information about the file
        ctx = self.context
        
        # Get file node ID in the context graph
        node_id = None
        for n_id, node in enumerate(ctx.nodes):
            if isinstance(node, SourceFile) and node.name == file.name:
                node_id = n_id
                break
        
        if node_id is None:
            return {"error": f"File not found in context: {file_path}"}
        
        # Get files that import this file
        importers = []
        for pred in ctx.predecessors(node_id, edge_type=EdgeType.IMPORT):
            if isinstance(pred, SourceFile):
                importers.append(pred.name)
        
        # Get files imported by this file
        imported = []
        for succ in ctx.successors(node_id, edge_type=EdgeType.IMPORT):
            if isinstance(succ, SourceFile):
                imported.append(succ.name)
        
        return {
            "file": file.name,
            "importers": importers,
            "imported": imported
        }
    
    def analyze_codebase_structure(self) -> Dict[str, Any]:
        """
        Analyze the overall structure of the codebase using CodebaseContext.
        
        Returns:
            A dictionary containing structural analysis results
        """
        ctx = self.context
        
        # Count nodes by type
        node_types: Dict[str, int] = {}
        for node in ctx.nodes:
            node_type = type(node).__name__
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        # Count edges by type
        edge_types: Dict[str, int] = {}
        for _, _, edge in ctx.edges:
            edge_type = edge.type.name
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        
        # Get directories structure
        directories = {}
        for path, directory in ctx.directories.items():
            directories[str(path)] = {
                "files": len([item for item in directory.items if isinstance(item, SourceFile)]),
                "subdirectories": len([item for item in directory.items if isinstance(item, Directory)])
            }
        
        return {
            "node_types": node_types,
            "edge_types": edge_types,
            "directories": directories
        }
    
    def get_symbol_dependencies(self, symbol_name: str) -> Dict[str, List[str]]:
        """
        Get direct dependencies of a symbol.
        
        Args:
            symbol_name: Name of the symbol to analyze
            
        Returns:
            A dictionary mapping dependency types to lists of symbol names
        """
        symbol = self.find_symbol_by_name(symbol_name)
        if symbol is None:
            return {"error": [f"Symbol not found: {symbol_name}"]}
        
        # Initialize result dictionary
        dependencies: Dict[str, List[str]] = {
            "imports": [],
            "functions": [],
            "classes": [],
            "variables": []
        }
        
        # Process dependencies based on symbol type
        if hasattr(symbol, "dependencies"):
            for dep in symbol.dependencies:
                if isinstance(dep, Import):
                    if dep.imported_symbol:
                        dependencies["imports"].append(dep.imported_symbol.name)
                elif isinstance(dep, Symbol):
                    if dep.symbol_type == SymbolType.Function:
                        dependencies["functions"].append(dep.name)
                    elif dep.symbol_type == SymbolType.Class:
                        dependencies["classes"].append(dep.name)
                    elif dep.symbol_type == SymbolType.GlobalVar:
                        dependencies["variables"].append(dep.name)
        
        return dependencies


def get_monthly_commits(repo_path: str) -> Dict[str, int]:
    """
    Get monthly commit counts for a repository.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        A dictionary mapping month strings to commit counts
    """
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=365)

    date_format = "%Y-%m-%d"
    since_date = start_date.strftime(date_format)
    until_date = end_date.strftime(date_format)

    # Validate repo_path format (should be owner/repo)
    if not re.match(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$", repo_path):
        print(f"Invalid repository path format: {repo_path}")
        return {}

    repo_url = f"https://github.com/{repo_path}"

    # Validate URL
    try:
        parsed_url = urlparse(repo_url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            print(f"Invalid URL: {repo_url}")
            return {}
    except Exception:
        print(f"Invalid URL: {repo_url}")
        return {}

    try:
        original_dir = os.getcwd()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Using a safer approach with a list of arguments and shell=False
            subprocess.run(
                ["git", "clone", repo_url, temp_dir],
                check=True,
                capture_output=True,
                shell=False,
                text=True,
            )
            os.chdir(temp_dir)

            # Using a safer approach with a list of arguments and shell=False
            result = subprocess.run(
                [
                    "git",
                    "log",
                    f"--since={since_date}",
                    f"--until={until_date}",
                    "--format=%aI",
                ],
                capture_output=True,
                text=True,
                check=True,
                shell=False,
            )
            commit_dates = result.stdout.strip().split("\n")

            monthly_counts = {}
            current_date = start_date
            while current_date <= end_date:
                month_key = current_date.strftime("%Y-%m")
                monthly_counts[month_key] = 0
                current_date = (
                    current_date.replace(day=1) + timedelta(days=32)
                ).replace(day=1)

            for date_str in commit_dates:
                if date_str:  # Skip empty lines
                    commit_date = datetime.fromisoformat(date_str.strip())
                    month_key = commit_date.strftime("%Y-%m")
                    if month_key in monthly_counts:
                        monthly_counts[month_key] += 1

            return dict(sorted(monthly_counts.items()))

    except subprocess.CalledProcessError as e:
        print(f"Error executing git command: {e}")
        return {}
    except Exception as e:
        print(f"Error processing git commits: {e}")
        return {}
    finally:
        with contextlib.suppress(Exception):
            os.chdir(original_dir)


def get_github_repo_description(repo_url: str) -> str:
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
    Analyze a repository and return various metrics.
    
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
    
    # Analyze codebase structure using CodebaseContext
    structure_analysis = analyzer.analyze_codebase_structure()
    
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
        "import_analysis": import_analysis,
        "structure_analysis": structure_analysis
    }
    
    return results


class SymbolRequest(BaseModel):
    """Request model for symbol analysis."""
    repo_url: str
    symbol_name: str


@app.post("/analyze_symbol")
async def analyze_symbol(request: SymbolRequest) -> Dict[str, Any]:
    """
    Analyze a symbol and its relationships in a repository.
    
    Args:
        request: The symbol request containing the repo URL and symbol name
        
    Returns:
        A dictionary of analysis results
    """
    repo_url = request.repo_url
    symbol_name = request.symbol_name
    
    codebase = Codebase.from_repo(repo_url)
    analyzer = CodeAnalyzer(codebase)
    
    # Get symbol context using CodebaseContext
    symbol_context = analyzer.get_context_for_symbol(symbol_name)
    
    # Get symbol dependencies
    dependencies = analyzer.get_symbol_dependencies(symbol_name)
    
    # Get symbol attribution
    attribution = analyzer.get_symbol_attribution(symbol_name)
    
    return {
        "symbol_name": symbol_name,
        "context": symbol_context,
        "dependencies": dependencies,
        "attribution": attribution
    }


class FileRequest(BaseModel):
    """Request model for file analysis."""
    repo_url: str
    file_path: str


@app.post("/analyze_file")
async def analyze_file(request: FileRequest) -> Dict[str, Any]:
    """
    Analyze a file and its relationships in a repository.
    
    Args:
        request: The file request containing the repo URL and file path
        
    Returns:
        A dictionary of analysis results
    """
    repo_url = request.repo_url
    file_path = request.file_path
    
    codebase = Codebase.from_repo(repo_url)
    analyzer = CodeAnalyzer(codebase)
    
    # Get file summary
    file_summary = analyzer.get_file_summary(file_path)
    
    # Get file dependencies using CodebaseContext
    file_dependencies = analyzer.get_file_dependencies(file_path)
    
    return {
        "file_path": file_path,
        "summary": file_summary,
        "dependencies": file_dependencies
    }


if __name__ == "__main__":
    # Run the FastAPI app locally with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

