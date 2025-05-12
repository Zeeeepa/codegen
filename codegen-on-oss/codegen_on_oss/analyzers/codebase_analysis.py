#!/usr/bin/env python3
"""
Codebase Analysis Module

This module provides basic code analysis functionality for codebases, including:
- Functions for getting codebase summaries
- Functions for getting file summaries
- Basic code analysis utilities

This is a dedicated implementation of the SDK's codebase_analysis.py module
for the analyzers directory, ensuring consistent analysis results.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Union

from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.enums import EdgeType, SymbolType


def get_codebase_summary(codebase: Codebase) -> str:
    """
    Generate a comprehensive summary of a codebase.

    Args:
        codebase: The Codebase object to summarize

    Returns:
        A formatted string containing a summary of the codebase's nodes and edges
    """
    node_summary = f"""Contains {len(codebase.ctx.get_nodes())} nodes
- {len(list(codebase.files))} files
- {len(list(codebase.imports))} imports
- {len(list(codebase.external_modules))} external_modules
- {len(list(codebase.symbols))} symbols
\t- {len(list(codebase.classes))} classes
\t- {len(list(codebase.functions))} functions
\t- {len(list(codebase.global_vars))} global_vars
\t- {len(list(codebase.interfaces))} interfaces
"""
    edge_summary = f"""Contains {len(codebase.ctx.edges)} edges
- {len([x for x in codebase.ctx.edges if x[2].type == EdgeType.SYMBOL_USAGE])} symbol -> used symbol
- {len([x for x in codebase.ctx.edges if x[2].type == EdgeType.IMPORT_SYMBOL_RESOLUTION])} import -> used symbol
- {len([x for x in codebase.ctx.edges if x[2].type == EdgeType.EXPORT])} export -> exported symbol
    """

    return f"{node_summary}\n{edge_summary}"


def get_file_summary(file: SourceFile) -> str:
    """
    Generate a summary of a source file.

    Args:
        file: The SourceFile object to summarize

    Returns:
        A formatted string containing a summary of the file's dependencies and usage
    """
    return f"""==== [ `{file.name}` (SourceFile) Dependency Summary ] ====
- {len(file.imports)} imports
- {len(file.symbols)} symbol references
\t- {len(file.classes)} classes
\t- {len(file.functions)} functions
\t- {len(file.global_vars)} global variables
\t- {len(file.interfaces)} interfaces

==== [ `{file.name}` Usage Summary ] ====
- {len(file.imports)} importers
"""


def get_class_summary(cls: Class) -> str:
    """
    Generate a summary of a class.

    Args:
        cls: The Class object to summarize

    Returns:
        A formatted string containing a summary of the class's dependencies and usage
    """
    return f"""==== [ `{cls.name}` (Class) Dependency Summary ] ====
- parent classes: {cls.parent_class_names}
- {len(cls.methods)} methods
- {len(cls.attributes)} attributes
- {len(cls.decorators)} decorators
- {len(cls.dependencies)} dependencies

{get_symbol_summary(cls)}
    """


def get_function_summary(func: Function) -> str:
    """
    Generate a summary of a function.

    Args:
        func: The Function object to summarize

    Returns:
        A formatted string containing a summary of the function's dependencies and usage
    """
    return f"""==== [ `{func.name}` (Function) Dependency Summary ] ====
- {len(func.return_statements)} return statements
- {len(func.parameters)} parameters
- {len(func.function_calls)} function calls
- {len(func.call_sites)} call sites
- {len(func.decorators)} decorators
- {len(func.dependencies)} dependencies

{get_symbol_summary(func)}
        """


def get_symbol_summary(symbol: Symbol) -> str:
    """
    Generate a summary of a symbol.

    Args:
        symbol: The Symbol object to summarize

    Returns:
        A formatted string containing a summary of the symbol's usage
    """
    usages = symbol.symbol_usages
    imported_symbols = [x.imported_symbol for x in usages if isinstance(x, Import)]

    return f"""==== [ `{symbol.name}` ({type(symbol).__name__}) Usage Summary ] ====
- {len(usages)} usages
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Function])} functions
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Class])} classes
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.GlobalVar])} global variables
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Interface])} interfaces
\t- {len(imported_symbols)} imports
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.Function])} functions
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.Class])} classes
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.GlobalVar])} global variables
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.Interface])} interfaces
\t\t- {len([x for x in imported_symbols if isinstance(x, ExternalModule)])} external modules
\t\t- {len([x for x in imported_symbols if isinstance(x, SourceFile)])} files
    """


def get_dependency_graph(
    codebase: Codebase, file_path: Optional[str] = None
) -> Dict[str, List[str]]:
    """
    Generate a dependency graph for a codebase or specific file.

    Args:
        codebase: The Codebase object to analyze
        file_path: Optional path to a specific file to analyze

    Returns:
        A dictionary mapping file paths to lists of dependencies
    """
    dependency_graph = {}

    files_to_analyze = [
        f for f in codebase.files if not file_path or f.file_path == file_path
    ]

    for file in files_to_analyze:
        dependencies = []

        # Add direct imports
        for imp in file.imports:
            if hasattr(imp, "imported_symbol") and hasattr(imp.imported_symbol, "file"):
                if hasattr(imp.imported_symbol.file, "file_path"):
                    dependencies.append(imp.imported_symbol.file.file_path)

        # Add symbol dependencies
        for symbol in file.symbols:
            for dep in symbol.dependencies:
                if hasattr(dep, "file") and hasattr(dep.file, "file_path"):
                    dependencies.append(dep.file.file_path)

        # Remove duplicates and self-references
        unique_deps = list(set([d for d in dependencies if d != file.file_path]))
        dependency_graph[file.file_path] = unique_deps

    return dependency_graph


def get_symbol_references(codebase: Codebase, symbol_name: str) -> List[Dict[str, Any]]:
    """
    Find all references to a symbol in the codebase.

    Args:
        codebase: The Codebase object to search
        symbol_name: The name of the symbol to find references for

    Returns:
        A list of dictionaries containing reference information
    """
    references = []

    # Find all symbols with the given name
    target_symbols = [s for s in codebase.symbols if s.name == symbol_name]

    for symbol in target_symbols:
        # Find all edges that reference this symbol
        for edge in codebase.ctx.edges:
            if edge[1] == symbol.id:  # If the edge points to our symbol
                source_node = codebase.ctx.get_node(edge[0])
                if source_node:
                    # Get file and line information if available
                    file_path = None
                    line_number = None

                    if hasattr(source_node, "file") and hasattr(
                        source_node.file, "file_path"
                    ):
                        file_path = source_node.file.file_path

                    if hasattr(source_node, "line"):
                        line_number = source_node.line

                    references.append(
                        {
                            "file_path": file_path,
                            "line": line_number,
                            "source_type": type(source_node).__name__,
                            "source_name": getattr(
                                source_node, "name", str(source_node)
                            ),
                            "edge_type": (
                                edge[2].type.name
                                if hasattr(edge[2], "type")
                                else "Unknown"
                            ),
                        }
                    )

    return references


def get_file_complexity_metrics(file: SourceFile) -> Dict[str, Any]:
    """
    Calculate complexity metrics for a source file.

    Args:
        file: The SourceFile object to analyze

    Returns:
        A dictionary containing complexity metrics
    """
    metrics = {
        "file_path": file.file_path,
        "name": file.name,
        "num_lines": 0,
        "num_imports": len(file.imports),
        "num_classes": len(file.classes),
        "num_functions": len(file.functions),
        "num_global_vars": len(file.global_vars),
        "cyclomatic_complexity": 0,
        "max_function_complexity": 0,
        "max_class_complexity": 0,
    }

    # Calculate lines of code if source is available
    if hasattr(file, "source") and file.source:
        metrics["num_lines"] = len(file.source.split("\n"))

    # Calculate function complexities
    function_complexities = []
    for func in file.functions:
        complexity = _calculate_function_complexity(func)
        function_complexities.append(complexity)
        metrics["cyclomatic_complexity"] += complexity

    if function_complexities:
        metrics["max_function_complexity"] = max(function_complexities)

    # Calculate class complexities
    class_complexities = []
    for cls in file.classes:
        complexity = 0
        for method in cls.methods:
            method_complexity = _calculate_function_complexity(method)
            complexity += method_complexity
        class_complexities.append(complexity)
        metrics["cyclomatic_complexity"] += complexity

    if class_complexities:
        metrics["max_class_complexity"] = max(class_complexities)

    return metrics


def _calculate_function_complexity(func: Function) -> int:
    """
    Calculate the cyclomatic complexity of a function.

    Args:
        func: The Function object to analyze

    Returns:
        An integer representing the cyclomatic complexity
    """
    complexity = 1  # Base complexity

    if not hasattr(func, "source") or not func.source:
        return complexity

    # Simple heuristic: count control flow statements
    source = func.source.lower()

    # Count if statements
    complexity += source.count(" if ") + source.count("\nif ")

    # Count else if / elif statements
    complexity += source.count("elif ") + source.count("else if ")

    # Count loops
    complexity += source.count(" for ") + source.count("\nfor ")
    complexity += source.count(" while ") + source.count("\nwhile ")

    # Count exception handlers
    complexity += source.count("except ") + source.count("catch ")

    # Count logical operators (each one creates a new path)
    complexity += source.count(" and ") + source.count(" && ")
    complexity += source.count(" or ") + source.count(" || ")

    return complexity
