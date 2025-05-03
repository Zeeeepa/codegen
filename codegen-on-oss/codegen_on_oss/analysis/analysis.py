"""
Unified Analysis Module for Codegen-on-OSS

This module serves as a central hub for all code analysis functionality, integrating
various specialized analysis components into a cohesive system.
"""

import contextlib
import difflib
import math
import os
import re
import subprocess
import tempfile
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
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

from codegen_on_oss.analysis.analysis_import import (
    analyze_imports,
    find_import_cycles,
    visualize_import_graph,
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
from codegen_on_oss.analysis.codegen_sdk_codebase import (
    get_codegen_sdk_codebase,
    get_codegen_sdk_subdirectories,
)
from codegen_on_oss.analysis.commit_analysis import (
    CommitAnalysisResult,
    CommitAnalyzer,
    CommitIssue,
)
from codegen_on_oss.analysis.commit_analyzer import CommitAnalyzer
from codegen_on_oss.analysis.current_code_codebase import (
    get_current_code_codebase,
    get_current_code_file,
)

# Import new analysis modules
from codegen_on_oss.analysis.diff_analyzer import DiffAnalyzer
from codegen_on_oss.analysis.document_functions import (
    document_class,
    document_file,
    document_function,
)
from codegen_on_oss.analysis.module_dependencies import (
    get_module_dependencies,
    visualize_module_dependencies,
)
from codegen_on_oss.analysis.swe_harness_agent import SWEHarnessAgent
from codegen_on_oss.analysis.symbolattr import (
    get_file_attribution,
    get_symbol_attribution,
)
from codegen_on_oss.snapshot.codebase_snapshot import CodebaseSnapshot, SnapshotManager

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
        document_function(self.codebase)

    def analyze_imports(self) -> Dict[str, Any]:
        """
        Analyze import relationships in the codebase.

        Returns:
            A dictionary containing import analysis results
        """
        graph = create_graph_from_codebase(self.codebase.repo_name)
        cycles = find_import_cycles(graph)
        problematic_loops = find_problematic_import_loops(graph, cycles)

        return {"import_cycles": cycles, "problematic_loops": problematic_loops}

    def convert_args_to_kwargs(self) -> None:
        """
        Convert all function call arguments to keyword arguments.
        """
        convert_all_calls_to_kwargs(self.codebase)

    def visualize_module_dependencies(self) -> None:
        """
        Visualize module dependencies in the codebase.
        """
        visualize_module_dependencies(self.codebase)

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

    def get_extended_symbol_context(
        self, symbol_name: str, degree: int = 2
    ) -> Dict[str, List[str]]:
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
                "usages": [usage.name for usage in usages],
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
                complexity_results.append(
                    {
                        "name": func.name,
                        "complexity": complexity,
                        "rank": cc_rank(complexity),
                    }
                )

        # Calculate average complexity
        if complexity_results:
            avg_complexity = sum(item["complexity"] for item in complexity_results) / len(
                complexity_results
            )
        else:
            avg_complexity = 0

        results["cyclomatic_complexity"] = {
            "functions": complexity_results,
            "average": avg_complexity,
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
                    "comment_ratio": comments / loc if loc > 0 else 0,
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
                "comment_ratio": total_comments / total_loc if total_loc > 0 else 0,
            },
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

                halstead_results.append(
                    {
                        "name": func.name,
                        "volume": volume,
                        "unique_operators": n1,
                        "unique_operands": n2,
                        "total_operators": N1,
                        "total_operands": N2,
                        "maintainability_index": mi_score,
                        "maintainability_rank": get_maintainability_rank(mi_score),
                    }
                )

                total_volume += volume

        results["halstead_metrics"] = {
            "functions": halstead_results,
            "total_volume": total_volume,
            "average_volume": (total_volume / len(halstead_results) if halstead_results else 0),
        }

        # Analyze inheritance depth
        inheritance_results = []
        total_doi = 0

        for cls in self.codebase.classes:
            doi = calculate_doi(cls)
            inheritance_results.append({"name": cls.name, "depth": doi})
            total_doi += doi

        results["inheritance_depth"] = {
            "classes": inheritance_results,
            "average": (total_doi / len(inheritance_results) if inheritance_results else 0),
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
                most_imported = sorted(
                    in_degree_centrality.items(), key=lambda x: x[1], reverse=True
                )[:10]
                most_dependent = sorted(
                    out_degree_centrality.items(), key=lambda x: x[1], reverse=True
                )[:10]
                most_central = sorted(
                    betweenness_centrality.items(), key=lambda x: x[1], reverse=True
                )[:10]

                results["dependency_metrics"] = {
                    "most_imported": most_imported,
                    "most_dependent": most_dependent,
                    "most_central": most_central,
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
            "external": list(set(external)),
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
            path_parts = file.name.split("/")
            current = structure

            # Build the directory structure
            for i, part in enumerate(path_parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]

            # Add the file with its symbols
            file_info = {"type": "file", "symbols": []}

            # Add symbols in the file
            for symbol in file.symbols:
                symbol_info = {
                    "name": symbol.name,
                    "type": (
                        str(symbol.symbol_type) if hasattr(symbol, "symbol_type") else "unknown"
                    ),
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
                commit_date = commit.committed_datetime
                month_key = commit_date.strftime("%Y-%m")

                if month_key not in monthly_commits:
                    monthly_commits[month_key] = 0

                monthly_commits[month_key] += 1

            return monthly_commits
        except Exception as e:
            return {"error": str(e)}

    def analyze_commit(self, commit_codebase: Codebase) -> CommitAnalysisResult:
        """
        Analyze a commit by comparing the current codebase with a commit codebase.

        Args:
            commit_codebase: The codebase after the commit

        Returns:
            A CommitAnalysisResult object containing the analysis results
        """
        # Create a CommitAnalyzer instance
        analyzer = CommitAnalyzer(original_codebase=self.codebase, commit_codebase=commit_codebase)

        # Analyze the commit
        return analyzer.analyze_commit()

    @classmethod
    def analyze_commit_from_paths(
        cls, original_path: str, commit_path: str
    ) -> CommitAnalysisResult:
        """
        Analyze a commit by comparing two repository paths.

        Args:
            original_path: Path to the original repository
            commit_path: Path to the commit repository

        Returns:
            A CommitAnalysisResult object containing the analysis results
        """
        # Create a CommitAnalyzer instance from paths
        analyzer = CommitAnalyzer.from_paths(original_path, commit_path)

        # Analyze the commit
        return analyzer.analyze_commit()

    @classmethod
    def analyze_commit_from_repo_and_commit(
        cls, repo_url: str, commit_hash: str
    ) -> CommitAnalysisResult:
        """
        Analyze a commit by comparing a repository at two different commits.

        Args:
            repo_url: URL of the repository
            commit_hash: Hash of the commit to analyze

        Returns:
            A CommitAnalysisResult object containing the analysis results
        """
        # Create a CommitAnalyzer instance from repo and commit
        analyzer = CommitAnalyzer.from_repo_and_commit(repo_url, commit_hash)

        # Analyze the commit
        return analyzer.analyze_commit()

    def get_commit_diff(self, commit_codebase: Codebase, file_path: str) -> str:
        """
        Get the diff between the current codebase and a commit codebase for a file.

        Args:
            commit_codebase: The codebase after the commit
            file_path: Path to the file to get the diff for
        """
        try:
            # Get the file content from both codebases
            original_content = self.codebase.get_file_content(file_path)
            commit_content = commit_codebase.get_file_content(file_path)

            # Generate a diff
            diff = difflib.unified_diff(
                original_content.splitlines(keepends=True),
                commit_content.splitlines(keepends=True),
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
            )

            return "".join(diff)
        except Exception as e:
            return f"Error generating diff: {str(e)}"

    def create_snapshot(self, commit_sha: Optional[str] = None) -> CodebaseSnapshot:
        """
        Create a snapshot of the current codebase.

        Args:
            commit_sha: Optional commit SHA to associate with the snapshot

        Returns:
            A CodebaseSnapshot object
        """
        return CodebaseSnapshot(self.codebase, commit_sha)

    def analyze_commit(
        self, base_commit: str, head_commit: str, github_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a commit by comparing the codebase before and after the commit.

        Args:
            base_commit: The base commit SHA (before the changes)
            head_commit: The head commit SHA (after the changes)
            github_token: Optional GitHub token for accessing private repositories

        Returns:
            A dictionary with analysis results
        """
        # Create a commit analyzer
        snapshot_manager = SnapshotManager()
        commit_analyzer = CommitAnalyzer(snapshot_manager, github_token)

        # Analyze the commit
        return commit_analyzer.analyze_commit(self.codebase.repo_path, base_commit, head_commit)

    def analyze_pull_request(
        self, pr_number: int, github_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a pull request by comparing the base and head commits.

        Args:
            pr_number: The pull request number
            github_token: Optional GitHub token for accessing private repositories

        Returns:
            A dictionary with analysis results
        """
        # Create a commit analyzer
        snapshot_manager = SnapshotManager()
        commit_analyzer = CommitAnalyzer(snapshot_manager, github_token)

        # Analyze the pull request
        return commit_analyzer.analyze_pull_request(
            self.codebase.repo_path, pr_number, github_token
        )

    def create_swe_harness_agent(
        self,
        github_token: Optional[str] = None,
        snapshot_dir: Optional[str] = None,
        use_agent: bool = True,
    ) -> SWEHarnessAgent:
        """
        Create a SWE harness agent for analyzing commits and pull requests.

        Args:
            github_token: Optional GitHub token for accessing private repositories
            snapshot_dir: Optional directory to store snapshots
            use_agent: Whether to use an LLM-based agent for enhanced analysis

        Returns:
            A SWEHarnessAgent instance
        """
        return SWEHarnessAgent(github_token, snapshot_dir, use_agent)

    def compare_snapshots(
        self, original_snapshot: CodebaseSnapshot, modified_snapshot: CodebaseSnapshot
    ) -> Dict[str, Any]:
        """
        Compare two codebase snapshots and analyze the differences.

        Args:
            original_snapshot: The original/base codebase snapshot
            modified_snapshot: The modified/new codebase snapshot

        Returns:
            A dictionary with comparison results
        """
        # Create a diff analyzer
        diff_analyzer = DiffAnalyzer(original_snapshot, modified_snapshot)

        # Get the summary and high-risk changes
        summary = diff_analyzer.get_summary()
        high_risk_changes = diff_analyzer.get_high_risk_changes()

        return {
            "summary": summary,
            "high_risk_changes": high_risk_changes,
            "formatted_summary": diff_analyzer.format_summary_text(),
        }


def get_monthly_commits(repo_path: str) -> Dict[str, int]:
    """
    Get monthly commit activity for a repository.

    Args:
        repo_path: Path to the repository

    Returns:
        Dictionary mapping month strings to commit counts
    """
    original_dir = os.getcwd()
    try:
        # Change to repository directory
        os.chdir(repo_path)

        # Get all commits
        result = subprocess.run(
            ["git", "log", "--format=%cd", "--date=short"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Parse commit dates
        commit_dates = result.stdout.strip().split("\n")

        # Group by month
        monthly_counts = {}
        for date_str in commit_dates:
            if date_str:
                # Extract year and month
                year_month = date_str[:7]  # YYYY-MM
                month_key = year_month

                if month_key not in monthly_counts:
                    monthly_counts[month_key] = 0

                monthly_counts[month_key] += 1

        os.chdir(original_dir)
        return dict(sorted(monthly_counts.items()))
    except Exception as e:
        if "original_dir" in locals():
            os.chdir(original_dir)
        return {"error": str(e)}


# Helper functions for complexity analysis


def calculate_cyclomatic_complexity(func: Function) -> int:
    """
    Calculate the cyclomatic complexity of a function.

    Args:
        func: The function to analyze

    Returns:
        The cyclomatic complexity value
    """
    # Start with 1 (base complexity)
    complexity = 1

    # Count decision points
    if hasattr(func, "code_block"):
        # Count if statements
        if_statements = func.code_block.find_all(IfBlockStatement)
        complexity += len(if_statements)

        # Count for loops
        for_loops = func.code_block.find_all(ForLoopStatement)
        complexity += len(for_loops)

        # Count while loops
        while_loops = func.code_block.find_all(WhileStatement)
        complexity += len(while_loops)

        # Count try-catch blocks
        try_catches = func.code_block.find_all(TryCatchStatement)
        complexity += len(try_catches)

        # Count logical operators in conditions
        binary_expressions = func.code_block.find_all(BinaryExpression)
        for expr in binary_expressions:
            if hasattr(expr, "operator") and expr.operator in ["&&", "||"]:
                complexity += 1

        # Count comparison expressions
        comparison_expressions = func.code_block.find_all(ComparisonExpression)
        complexity += len(comparison_expressions)

        # Count unary expressions with logical not
        unary_expressions = func.code_block.find_all(UnaryExpression)
        for expr in unary_expressions:
            if hasattr(expr, "operator") and expr.operator == "!":
                complexity += 1

    return complexity


def cc_rank(complexity):
    """
    Convert cyclomatic complexity score to a letter grade.

    Args:
        complexity: The cyclomatic complexity score

    Returns:
        A letter grade from A to F
    """
    if complexity < 0:
        raise ValueError("Complexity must be a non-negative value")

    ranks = [
        (1, 5, "A"),
        (6, 10, "B"),
        (11, 20, "C"),
        (21, 30, "D"),
        (31, 40, "E"),
        (41, float("inf"), "F"),
    ]
    for low, high, rank in ranks:
        if low <= complexity <= high:
            return rank
    return "F"


def calculate_doi(cls):
    """
    Calculate the depth of inheritance for a given class.

    Args:
        cls: The class to analyze

    Returns:
        The depth of inheritance
    """
    return len(cls.superclasses)


def get_operators_and_operands(function):
    """
    Extract operators and operands from a function.

    Args:
        function: The function to analyze

    Returns:
        A tuple of (operators, operands)
    """
    operators = []
    operands = []

    for statement in function.code_block.statements:
        for call in statement.function_calls:
            operators.append(call.name)
            for arg in call.args:
                operands.append(arg.source)

        if hasattr(statement, "expressions"):
            for expr in statement.expressions:
                if isinstance(expr, BinaryExpression):
                    operators.extend([op.source for op in expr.operators])
                    operands.extend([elem.source for elem in expr.elements])
                elif isinstance(expr, UnaryExpression):
                    operators.append(expr.ts_node.type)
                    operands.append(expr.argument.source)
                elif isinstance(expr, ComparisonExpression):
                    operators.extend([op.source for op in expr.operators])
                    operands.extend([elem.source for elem in expr.elements])

        if hasattr(statement, "expression"):
            expr = statement.expression
            if isinstance(expr, BinaryExpression):
                operators.extend([op.source for op in expr.operators])
                operands.extend([elem.source for elem in expr.elements])
            elif isinstance(expr, UnaryExpression):
                operators.append(expr.ts_node.type)
                operands.append(expr.argument.source)
            elif isinstance(expr, ComparisonExpression):
                operators.extend([op.source for op in expr.operators])
                operands.extend([elem.source for elem in expr.elements])

    return operators, operands


def calculate_halstead_volume(operators, operands):
    """
    Calculate Halstead volume metrics.

    Args:
        operators: List of operators
        operands: List of operands

    Returns:
        A tuple of (volume, N1, N2, n1, n2)
    """
    n1 = len(set(operators))
    n2 = len(set(operands))

    N1 = len(operators)
    N2 = len(operands)

    N = N1 + N2
    n = n1 + n2

    if n > 0:
        volume = N * math.log2(n)
        return volume, N1, N2, n1, n2
    return 0, N1, N2, n1, n2


def count_lines(source: str):
    """
    Count different types of lines in source code.

    Args:
        source: The source code as a string

    Returns:
        A tuple of (loc, lloc, sloc, comments)
    """
    if not source.strip():
        return 0, 0, 0, 0

    lines = [line.strip() for line in source.splitlines()]
    loc = len(lines)
    sloc = len([line for line in lines if line])

    in_multiline = False
    comments = 0
    code_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]
        code_part = line
        if not in_multiline and "#" in line:
            comment_start = line.find("#")
            if not re.search(r"[\"\\\']\s*#\s*[\"\\\']\s*", line[:comment_start]):
                code_part = line[:comment_start].strip()
                if line[comment_start:].strip():
                    comments += 1

        if ('"""' in line or "'''" in line) and not (
            line.count('"""') % 2 == 0 or line.count("'''") % 2 == 0
        ):
            if in_multiline:
                in_multiline = False
                comments += 1
            else:
                in_multiline = True
                comments += 1
                if line.strip().startswith('"""') or line.strip().startswith("'''"):
                    code_part = ""
        elif in_multiline or line.strip().startswith("#"):
            comments += 1
            code_part = ""

        if code_part.strip():
            code_lines.append(code_part)

        i += 1

    lloc = 0
    continued_line = False
    for line in code_lines:
        if continued_line:
            if not any(line.rstrip().endswith(c) for c in ("\\", ",", "{", "[", "(")):
                continued_line = False
            continue

        lloc += len([stmt for stmt in line.split(";") if stmt.strip()])

        if any(line.rstrip().endswith(c) for c in ("\\", ",", "{", "[", "(")):
            continued_line = True

    return loc, lloc, sloc, comments


def calculate_maintainability_index(
    halstead_volume: float, cyclomatic_complexity: float, loc: int
) -> int:
    """
    Calculate the normalized maintainability index for a given function.

    Args:
        halstead_volume: The Halstead volume
        cyclomatic_complexity: The cyclomatic complexity
        loc: Lines of code

    Returns:
        The maintainability index score (0-100)
    """
    if loc <= 0:
        return 100

    try:
        raw_mi = (
            171
            - 5.2 * math.log(max(1, halstead_volume))
            - 0.23 * cyclomatic_complexity
            - 16.2 * math.log(max(1, loc))
        )
        normalized_mi = max(0, min(100, raw_mi * 100 / 171))
        return int(normalized_mi)
    except (ValueError, TypeError):
        return 0


def get_maintainability_rank(mi_score: float) -> str:
    """
    Convert maintainability index score to a letter grade.

    Args:
        mi_score: The maintainability index score

    Returns:
        A letter grade from A to F
    """
    if mi_score >= 85:
        return "A"
    elif mi_score >= 65:
        return "B"
    elif mi_score >= 45:
        return "C"
    elif mi_score >= 25:
        return "D"
    else:
        return "F"


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


# Define API models
class RepoAnalysisRequest(BaseModel):
    repo_url: str


class CommitAnalysisRequest(BaseModel):
    repo_url: str
    commit_hash: str


class LocalCommitAnalysisRequest(BaseModel):
    original_path: str
    commit_path: str


# API endpoints
@app.post("/analyze_repo")
async def analyze_repo(request: RepoAnalysisRequest):
    """
    Analyze a repository.
    """
    try:
        codebase = Codebase.from_repo(request.repo_url)
        analyzer = CodeAnalyzer(codebase)

        return {
            "repo_url": request.repo_url,
            "summary": analyzer.get_codebase_summary(),
            "complexity": analyzer.analyze_complexity(),
            "imports": analyzer.analyze_imports(),
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/analyze_commit")
async def analyze_commit(request: CommitAnalysisRequest):
    """
    Analyze a commit in a repository.
    """
    try:
        result = CodeAnalyzer.analyze_commit_from_repo_and_commit(
            repo_url=request.repo_url, commit_hash=request.commit_hash
        )

        return {
            "repo_url": request.repo_url,
            "commit_hash": request.commit_hash,
            "is_properly_implemented": result.is_properly_implemented,
            "summary": result.get_summary(),
            "issues": [issue.to_dict() for issue in result.issues],
            "metrics_diff": result.metrics_diff,
            "files_added": result.files_added,
            "files_modified": result.files_modified,
            "files_removed": result.files_removed,
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/analyze_local_commit")
async def analyze_local_commit(request: LocalCommitAnalysisRequest):
    """
    Analyze a commit by comparing two local repository paths.
    """
    try:
        result = CodeAnalyzer.analyze_commit_from_paths(
            original_path=request.original_path, commit_path=request.commit_path
        )

        return {
            "original_path": request.original_path,
            "commit_path": request.commit_path,
            "is_properly_implemented": result.is_properly_implemented,
            "summary": result.get_summary(),
            "issues": [issue.to_dict() for issue in result.issues],
            "metrics_diff": result.metrics_diff,
            "files_added": result.files_added,
            "files_modified": result.files_modified,
            "files_removed": result.files_removed,
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Run the FastAPI app locally with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
