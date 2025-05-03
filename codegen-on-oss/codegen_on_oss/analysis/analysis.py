"""
Unified Analysis Module for Codegen-on-OSS

This module serves as a central hub for all code analysis functionality, integrating
various specialized analysis components into a cohesive system.
"""

from typing import Any

import networkx as nx
import uvicorn
from codegen import Codebase
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.directory import Directory
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.enums import EdgeType, SymbolType
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from codegen_on_oss.analysis.analysis_import import (
    create_graph_from_codebase,
    find_import_cycles,
    find_problematic_import_loops,
)
from codegen_on_oss.analysis.codebase_analysis import (
    get_class_summary,
    get_codebase_summary,
    get_file_summary,
    get_function_summary,
    get_symbol_summary,
)

# Import from other analysis modules
from codegen_on_oss.analysis.codebase_context import CodebaseContext
from codegen_on_oss.analysis.document_functions import run as document_functions_run
from codegen_on_oss.analysis.error_context import CodeError, ErrorContextAnalyzer
from codegen_on_oss.analysis.symbolattr import print_symbol_attribution

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
        self._error_analyzer = None

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
        from codegen.configs.models.codebase import CodebaseConfig
        from codegen.sdk.codebase.config import ProjectConfig

        # Create a project config from the codebase
        project_config = ProjectConfig(
            repo_operator=self.codebase.repo_operator,
            programming_language=self.codebase.programming_language,
            base_path=self.codebase.base_path,
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

    @property
    def error_analyzer(self) -> ErrorContextAnalyzer:
        """
        Get the ErrorContextAnalyzer for the current codebase.

        Returns:
            An ErrorContextAnalyzer object for the codebase
        """
        if self._error_analyzer is None:
            self._error_analyzer = ErrorContextAnalyzer(self.codebase)

        return self._error_analyzer

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

    def find_symbol_by_name(self, symbol_name: str) -> Symbol | None:
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

    def find_file_by_path(self, file_path: str) -> SourceFile | None:
        """
        Find a file by its path.

        Args:
            file_path: Path to the file to find

        Returns:
            The SourceFile object if found, None otherwise
        """
        return self.codebase.get_file(file_path)

    def find_class_by_name(self, class_name: str) -> Class | None:
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

    def find_function_by_name(self, function_name: str) -> Function | None:
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

    def analyze_imports(self) -> dict[str, Any]:
        """
        Analyze import relationships in the codebase.

        Returns:
            A dictionary containing import analysis results
        """
        graph = create_graph_from_codebase(self.codebase)
        cycles = find_import_cycles(graph)
        problematic_loops = find_problematic_import_loops(graph, cycles)

        return {
            "import_graph": graph,
            "cycles": cycles,
            "problematic_loops": problematic_loops,
        }

    def get_dependency_graph(self) -> nx.DiGraph:
        """
        Get a dependency graph for the codebase files.

        Returns:
            A directed graph representing file dependencies
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

    def get_context_for_symbol(self, symbol_name: str) -> dict[str, Any]:
        """
        Get context information for a symbol.

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
                    "type": pred.symbol_type.name
                    if hasattr(pred, "symbol_type")
                    else "Unknown",
                })

        # Get successors (symbols used by this symbol)
        successors = []
        for succ in ctx.successors(node_id):
            if isinstance(succ, Symbol):
                successors.append({
                    "name": succ.name,
                    "type": succ.symbol_type.name
                    if hasattr(succ, "symbol_type")
                    else "Unknown",
                })

        return {
            "symbol": {
                "name": symbol.name,
                "type": symbol.symbol_type.name
                if hasattr(symbol, "symbol_type")
                else "Unknown",
                "file": symbol.file.name if hasattr(symbol, "file") else "Unknown",
            },
            "predecessors": predecessors,
            "successors": successors,
        }

    def get_file_dependencies(self, file_path: str) -> dict[str, Any]:
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

        imported = []
        for succ in ctx.successors(node_id, edge_type=EdgeType.IMPORT):
            if isinstance(succ, SourceFile):
                imported.append(succ.name)

        return {"file": file.name, "importers": importers, "imported": imported}

    def analyze_codebase_structure(self) -> dict[str, Any]:
        """
        Analyze the overall structure of the codebase using CodebaseContext.

        Returns:
            A dictionary containing structural analysis results
        """
        ctx = self.context

        # Count nodes by type
        node_types: dict[str, int] = {}
        for node in ctx.nodes:
            node_type = type(node).__name__
            node_types[node_type] = node_types.get(node_type, 0) + 1

        edge_types: dict[str, int] = {}
        for _, _, edge in ctx.edges:
            edge_type = edge.type.name
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1

        directories = {}
        for path, directory in ctx.directories.items():
            directories[str(path)] = {
                "files": len([
                    item for item in directory.items if isinstance(item, SourceFile)
                ]),
                "subdirectories": len([
                    item for item in directory.items if isinstance(item, Directory)
                ]),
            }

        return {
            "node_types": node_types,
            "edge_types": edge_types,
            "directories": directories,
        }

    def get_symbol_dependencies(self, symbol_name: str) -> dict[str, list[str]]:
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

        dependencies: dict[str, list[str]] = {
            "imports": [],
            "functions": [],
            "classes": [],
            "variables": [],
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

    def analyze_errors(self) -> dict[str, list[dict[str, Any]]]:
        """
        Analyze the codebase for errors.

        Returns:
            A dictionary mapping file paths to lists of errors
        """
        return self.error_analyzer.analyze_codebase()

    def get_function_error_context(self, function_name: str) -> dict[str, Any]:
        """
        Get detailed error context for a specific function.

        Args:
            function_name: The name of the function to analyze

        Returns:
            A dictionary with detailed error context
        """
        return self.error_analyzer.get_function_error_context(function_name)

    def get_file_error_context(self, file_path: str) -> dict[str, Any]:
        """
        Get detailed error context for a specific file.

        Args:
            file_path: The path of the file to analyze

        Returns:
            A dictionary with detailed error context
        """
        return self.error_analyzer.get_file_error_context(file_path)

    def get_error_context(self, error: CodeError) -> dict[str, Any]:
        """
        Get detailed context information for an error.

        Args:
            error: The error to get context for

        Returns:
            A dictionary with detailed context information
        """
        return self.error_analyzer.get_error_context(error)


# Request models for API endpoints
class RepoRequest(BaseModel):
    """Request model for repository analysis."""

    repo_url: str


class SymbolRequest(BaseModel):
    """Request model for symbol analysis."""

    repo_url: str
    symbol_name: str


class FileRequest(BaseModel):
    """Request model for file analysis."""

    repo_url: str
    file_path: str


class FunctionRequest(BaseModel):
    """Request model for function analysis."""

    repo_url: str
    function_name: str


class ErrorRequest(BaseModel):
    """Request model for error analysis."""

    repo_url: str
    file_path: str | None = None
    function_name: str | None = None


# API endpoints
@app.post("/analyze_repo")
async def analyze_repo(request: RepoRequest) -> dict[str, Any]:
    """
    Analyze a repository and return various metrics.

    Args:
        request: The repository request containing the repo URL

    Returns:
        A dictionary of analysis results
    """
    repo_url = request.repo_url

    try:
        codebase = Codebase.from_repo(repo_url)
        analyzer = CodeAnalyzer(codebase)

        # Get import analysis
        import_analysis = analyzer.analyze_imports()

        # Get structure analysis
        structure_analysis = analyzer.analyze_codebase_structure()

        # Get error analysis
        error_analysis = analyzer.analyze_errors()

        # Combine all results
        results = {
            "repo_url": repo_url,
            "num_files": len(codebase.files),
            "num_functions": len(codebase.functions),
            "num_classes": len(codebase.classes),
            "import_analysis": import_analysis,
            "structure_analysis": structure_analysis,
            "error_analysis": error_analysis
        }
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing repository: {str(e)}") from e


@app.post("/analyze_symbol")
async def analyze_symbol(request: SymbolRequest) -> dict[str, Any]:
    """
    Analyze a symbol and return detailed information.

    Args:
        request: The symbol request containing the repo URL and symbol name

    Returns:
        A dictionary of analysis results
    """
    repo_url = request.repo_url
    symbol_name = request.symbol_name

    try:
        codebase = Codebase.from_repo(repo_url)
        analyzer = CodeAnalyzer(codebase)

        # Get symbol context
        symbol_context = analyzer.get_context_for_symbol(symbol_name)

        # Get symbol dependencies
        dependencies = analyzer.get_symbol_dependencies(symbol_name)

        # Get symbol attribution
        attribution = analyzer.get_symbol_attribution(symbol_name)

        return {
            "symbol_name": symbol_name,
            "context": symbol_context,
            "dependencies": dependencies,
            "attribution": attribution,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error analyzing symbol: {e!s}"
        ) from e


@app.post("/analyze_file")
async def analyze_file(request: FileRequest) -> dict[str, Any]:
    """
    Analyze a file and return detailed information.

    Args:
        request: The file request containing the repo URL and file path

    Returns:
        A dictionary of analysis results
    """
    repo_url = request.repo_url
    file_path = request.file_path

    try:
        codebase = Codebase.from_repo(repo_url)
        analyzer = CodeAnalyzer(codebase)

        # Get file summary
        file_summary = analyzer.get_file_summary(file_path)

        # Get file dependencies
        file_dependencies = analyzer.get_file_dependencies(file_path)

        # Get file error context
        file_error_context = analyzer.get_file_error_context(file_path)

        return {
            "file_path": file_path,
            "summary": file_summary,
            "dependencies": file_dependencies,
            "error_context": file_error_context,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error analyzing file: {e!s}"
        ) from e


@app.post("/analyze_function")
async def analyze_function(request: FunctionRequest) -> dict[str, Any]:
    """
    Analyze a function and return detailed information.

    Args:
        request: The function request containing the repo URL and function name

    Returns:
        A dictionary of analysis results
    """
    repo_url = request.repo_url
    function_name = request.function_name

    try:
        codebase = Codebase.from_repo(repo_url)
        analyzer = CodeAnalyzer(codebase)

        # Get function summary
        function_summary = analyzer.get_function_summary(function_name)

        # Get function error context
        function_error_context = analyzer.get_function_error_context(function_name)

        return {
            "function_name": function_name,
            "summary": function_summary,
            "error_context": function_error_context,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error analyzing function: {e!s}"
        ) from e


@app.post("/analyze_errors")
async def analyze_errors(request: ErrorRequest) -> dict[str, Any]:
    """
    Analyze errors in a repository, file, or function.

    Args:
        request: The error request containing the repo URL and optional file path or function name

    Returns:
        A dictionary of error analysis results
    """
    repo_url = request.repo_url
    file_path = request.file_path
    function_name = request.function_name

    try:
        codebase = Codebase.from_repo(repo_url)
        analyzer = CodeAnalyzer(codebase)

        if function_name:
            # Analyze errors in a specific function
            return analyzer.get_function_error_context(function_name)
        elif file_path:
            # Analyze errors in a specific file
            return analyzer.get_file_error_context(file_path)
        else:
            # Analyze errors in the entire codebase
            return {"error_analysis": analyzer.analyze_errors()}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error analyzing errors: {e!s}"
        ) from e


if __name__ == "__main__":
    # Run the FastAPI app locally with uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
