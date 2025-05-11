#!/usr/bin/env python3
"""
Comprehensive Codebase and PR Analyzer

This module leverages the Codegen SDK to provide detailed analysis of codebases
and pull requests, including comparison between base and PR versions to identify
issues, errors, and quality problems.
"""

import os
import sys
import json
import time
import logging
import argparse
import tempfile
import networkx as nx
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional, Union, TypeVar, cast
from dataclasses import dataclass
from enum import Enum

try:
    from codegen.sdk.core.codebase import Codebase
    from codegen.configs.models.codebase import CodebaseConfig
    from codegen.configs.models.secrets import SecretsConfig
    from codegen.sdk.codebase.config import ProjectConfig
    from codegen.git.schemas.repo_config import RepoConfig
    from codegen.git.repo_operator.repo_operator import RepoOperator
    from codegen.shared.enums.programming_language import ProgrammingLanguage
    from codegen.sdk.codebase.codebase_analysis import get_codebase_summary, get_file_summary
    from codegen.sdk.core.file import SourceFile
    from codegen.sdk.enums import EdgeType, SymbolType
    from codegen.sdk.core.symbol import Symbol
    from codegen.sdk.core.function import Function
    from codegen.sdk.core.class_definition import Class
    from codegen.git.utils.pr_review import CodegenPR

    # Import our custom CodebaseContext
    from codegen_on_oss.context_codebase import CodebaseContext, get_node_classes, GLOBAL_FILE_IGNORE_LIST
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

class AnalysisType(str, Enum):
    """Types of analysis that can be performed."""
    CODEBASE = "codebase"
    PR = "pr"
    COMPARISON = "comparison"

class IssueSeverity(str, Enum):
    """Severity levels for issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class Issue:
    """Represents an issue found during analysis."""
    file: str
    line: Optional[int]
    message: str
    severity: IssueSeverity
    symbol: Optional[str] = None
    code: Optional[str] = None
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file,
            "line": self.line,
            "message": self.message,
            "severity": self.severity,
            "symbol": self.symbol,
            "code": self.code,
            "suggestion": self.suggestion
        }

class CodebaseAnalyzer:
    """
    Advanced analyzer for codebases and PRs using the Codegen SDK.

    This analyzer provides detailed analysis of:
    1. Single codebase analysis to find issues
    2. PR analysis to check changes and identify problems
    3. Comparison between base branch and PR to verify correctness

    The analyzer uses the CodebaseContext to build a graph representation of the codebase
    and perform advanced analysis on the codebase structure.
    """

    def __init__(
        self,
        repo_url: Optional[str] = None,
        repo_path: Optional[str] = None,
        base_branch: str = "main",
        pr_number: Optional[int] = None,
        language: Optional[str] = None,
        file_ignore_list: Optional[List[str]] = None
    ):
        """Initialize the CodebaseAnalyzer.

        Args:
            repo_url: URL of the repository to analyze
            repo_path: Local path to the repository to analyze
            base_branch: Base branch for comparison
            pr_number: PR number to analyze
            language: Programming language of the codebase (auto-detected if not provided)
            file_ignore_list: List of file patterns to ignore during analysis
        """
        self.repo_url = repo_url
        self.repo_path = repo_path
        self.base_branch = base_branch
        self.pr_number = pr_number
        self.language = language

        # Use custom ignore list or default global list
        self.file_ignore_list = file_ignore_list or GLOBAL_FILE_IGNORE_LIST

        self.base_codebase = None
        self.pr_codebase = None

        # Context objects for advanced graph analysis
        self.base_context = None
        self.pr_context = None

        self.issues = []
        self.pr_diff = None
        self.commit_shas = None
        self.modified_symbols = None
        self.pr_branch = None

        # Initialize codebase(s) based on provided parameters
        if repo_url:
            self._init_from_url(repo_url, language)
        elif repo_path:
            self._init_from_path(repo_path, language)

        # If PR number is provided, initialize PR-specific data
        if self.pr_number is not None and self.base_codebase is not None:
            self._init_pr_data(self.pr_number)

        # Initialize CodebaseContext objects
        if self.base_codebase:
            self.base_context = CodebaseContext(
                codebase=self.base_codebase,
                base_path=self.repo_path,
                pr_branch=None,
                base_branch=self.base_branch
            )

        if self.pr_codebase:
            self.pr_context = CodebaseContext(
                codebase=self.pr_codebase,
                base_path=self.repo_path,
                pr_branch=self.pr_branch,
                base_branch=self.base_branch
            )
    
    def _init_from_url(self, repo_url: str, language: Optional[str] = None):
        """Initialize base codebase from a repository URL."""
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
            logger.info(f"Initializing codebase from {repo_url}...")
            
            prog_lang = None
            if language:
                prog_lang = ProgrammingLanguage(language.upper())
            
            # Initialize base codebase
            self.base_codebase = Codebase.from_github(
                repo_full_name=repo_full_name,
                tmp_dir=tmp_dir,
                language=prog_lang,
                config=config,
                secrets=secrets
            )
            
            logger.info(f"Successfully initialized codebase from {repo_url}")
            
            # If PR number is specified, also initialize PR codebase
            if self.pr_number:
                self._init_pr_codebase()
            
        except Exception as e:
            logger.error(f"Error initializing codebase from URL: {e}")
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
            logger.info(f"Initializing codebase from {repo_path}...")
            
            # Set up programming language
            prog_lang = None
            if language:
                prog_lang = ProgrammingLanguage(language.upper())
            
            # Create repo config and repo operator
            repo_config = RepoConfig.from_repo_path(repo_path)
            repo_config.respect_gitignore = False
            repo_operator = RepoOperator(repo_config=repo_config, bot_commit=False)
            
            # Configure project with repo operator and language
            project_config = ProjectConfig(
                repo_operator=repo_operator,
                programming_language=prog_lang if prog_lang else None
            )
            
            # Initialize codebase with proper project configuration
            self.base_codebase = Codebase(
                projects=[project_config],
                config=config,
                secrets=secrets
            )
            
            logger.info(f"Successfully initialized codebase from {repo_path}")
            
            # If PR number is specified, also initialize PR codebase
            if self.pr_number:
                self._init_pr_codebase()
                
        except Exception as e:
            logger.error(f"Error initializing codebase from path: {e}")
            raise
    
    def _init_pr_data(self, pr_number: int):
        """Initialize PR-specific data."""
        try:
            logger.info(f"Fetching PR #{pr_number} data...")
            result = self.base_codebase.get_modified_symbols_in_pr(pr_number)
            
            # Unpack the result tuple
            if len(result) >= 3:
                self.pr_diff, self.commit_shas, self.modified_symbols = result[:3]
                if len(result) >= 4:
                    self.pr_branch = result[3]
                
            logger.info(f"Found {len(self.modified_symbols)} modified symbols in PR")
            
        except Exception as e:
            logger.error(f"Error initializing PR data: {e}")
            raise
    
    def _init_pr_codebase(self):
        """Initialize PR codebase by checking out the PR branch."""
        if not self.base_codebase or not self.pr_number:
            logger.error("Base codebase or PR number not initialized")
            return
            
        try:
            # Get PR data if not already fetched
            if not self.pr_branch:
                self._init_pr_data(self.pr_number)
                
            if not self.pr_branch:
                logger.error("Failed to get PR branch")
                return
                
            # Clone the base codebase
            self.pr_codebase = self.base_codebase
                
            # Checkout PR branch
            logger.info(f"Checking out PR branch: {self.pr_branch}")
            self.pr_codebase.checkout(self.pr_branch)
            
            logger.info("Successfully initialized PR codebase")
                
        except Exception as e:
            logger.error(f"Error initializing PR codebase: {e}")
            raise
    
    def analyze(self, analysis_type: AnalysisType = AnalysisType.CODEBASE) -> Dict[str, Any]:
        """
        Perform a comprehensive analysis of the codebase or PR.
        
        Args:
            analysis_type: Type of analysis to perform (codebase, pr, or comparison)
            
        Returns:
            Dict containing the analysis results
        """
        if not self.base_codebase:
            raise ValueError("Codebase not initialized")
            
        result = {
            "metadata": {
                "analysis_time": datetime.now().isoformat(),
                "analysis_type": analysis_type,
                "repo_name": self.base_codebase.ctx.repo_name,
                "language": str(self.base_codebase.ctx.programming_language),
            },
            "summary": get_codebase_summary(self.base_codebase),
        }
        
        # Reset issues list
        self.issues = []
        
        if analysis_type == AnalysisType.CODEBASE:
            # Perform static analysis on base codebase
            logger.info("Performing static analysis on codebase...")
            result["static_analysis"] = self._perform_static_analysis(self.base_codebase)
            
        elif analysis_type == AnalysisType.PR:
            # Analyze PR changes
            if not self.pr_number:
                raise ValueError("PR number not provided")
                
            logger.info(f"Analyzing PR #{self.pr_number}...")
            result["pr_analysis"] = self._analyze_pr()
            
        elif analysis_type == AnalysisType.COMPARISON:
            # Compare base codebase with PR
            if not self.pr_codebase:
                raise ValueError("PR codebase not initialized")
                
            logger.info("Comparing base codebase with PR...")
            result["comparison"] = self._compare_codebases()
        
        # Add issues to the result
        result["issues"] = [issue.to_dict() for issue in self.issues]
        result["issue_counts"] = {
            "total": len(self.issues),
            "by_severity": {
                "error": sum(1 for issue in self.issues if issue.severity == IssueSeverity.ERROR),
                "warning": sum(1 for issue in self.issues if issue.severity == IssueSeverity.WARNING),
                "info": sum(1 for issue in self.issues if issue.severity == IssueSeverity.INFO),
            }
        }
        
        return result
    
    def _perform_static_analysis(self, codebase: Codebase) -> Dict[str, Any]:
        """
        Perform static analysis on a codebase using the CodebaseContext
        for deep graph-based analysis.

        This method analyzes various aspects of the codebase including:
        - Dead code detection
        - Parameter and function signature issues
        - Error handling patterns
        - Call site compatibility
        - Import dependencies
        - Inheritance hierarchies
        - Code complexity metrics
        - Graph-based dependency analysis
        """
        analysis_result = {}

        # Use the context for more advanced analysis if available
        context = self.base_context if codebase == self.base_codebase else None

        # Check for unused symbols (dead code)
        analysis_result["dead_code"] = self._find_dead_code(codebase)

        # Check for parameter issues
        analysis_result["parameter_issues"] = self._check_function_parameters(codebase)

        # Check for error handling issues
        analysis_result["error_handling"] = self._check_error_handling(codebase)

        # Check for call site issues
        analysis_result["call_site_issues"] = self._check_call_sites(codebase)

        # Check for import issues
        analysis_result["import_issues"] = self._check_imports(codebase)

        # Check for inheritance issues
        analysis_result["inheritance_issues"] = self._check_inheritance(codebase)

        # Analyze code complexity
        analysis_result["code_complexity"] = self._analyze_code_complexity(codebase)

        # Add graph-based analysis if context is available
        if context:
            # Analyze dependency chains
            analysis_result["dependency_chains"] = self._analyze_dependency_chains(context)

            # Analyze circular dependencies
            analysis_result["circular_dependencies"] = self._find_circular_dependencies(context)

            # Analyze module coupling
            analysis_result["module_coupling"] = self._analyze_module_coupling(context)

            # Analyze call hierarchy
            analysis_result["call_hierarchy"] = self._analyze_call_hierarchy(context)

        return analysis_result

    def _analyze_dependency_chains(self, context: CodebaseContext) -> Dict[str, Any]:
        """Analyze dependency chains in the codebase."""
        result = {
            "long_chains": [],
            "critical_paths": []
        }

        # Find long dependency chains
        for node in context.nodes:
            if not hasattr(node, 'name'):
                continue

            # Skip non-symbol nodes
            if not isinstance(node, Symbol):
                continue

            # Use NetworkX to find longest paths from this node
            try:
                # Create a subgraph containing only symbol nodes
                symbol_nodes = [n for n in context.nodes if isinstance(n, Symbol)]
                subgraph = context.build_subgraph(symbol_nodes)

                # Find paths
                paths = []
                for target in symbol_nodes:
                    if node != target and hasattr(target, 'name'):
                        try:
                            path = nx.shortest_path(subgraph, node, target)
                            if len(path) > 3:  # Only track paths with at least 3 edges
                                paths.append(path)
                        except (nx.NetworkXNoPath, nx.NodeNotFound):
                            pass

                # Sort by path length and take longest
                paths.sort(key=len, reverse=True)
                if paths and len(paths[0]) > 3:
                    path_info = {
                        "source": node.name,
                        "targets": [paths[0][-1].name if hasattr(paths[0][-1], 'name') else str(paths[0][-1])],
                        "length": len(paths[0]),
                        "path": [n.name if hasattr(n, 'name') else str(n) for n in paths[0]]
                    }
                    result["long_chains"].append(path_info)
            except Exception as e:
                # Skip errors in graph analysis
                pass

        # Sort by chain length and limit to top 10
        result["long_chains"].sort(key=lambda x: x["length"], reverse=True)
        result["long_chains"] = result["long_chains"][:10]

        return result

    def _find_circular_dependencies(self, context: CodebaseContext) -> Dict[str, Any]:
        """Find circular dependencies in the codebase."""
        result = {
            "circular_imports": [],
            "circular_function_calls": []
        }

        # Find circular dependencies in the context graph
        try:
            cycles = list(nx.simple_cycles(context._graph))

            # Filter and categorize cycles
            for cycle in cycles:
                # Check if it's an import cycle
                if all(hasattr(node, 'symbol_type') and hasattr(node, 'name') for node in cycle):
                    cycle_type = "unknown"

                    # Check if all nodes in the cycle are files
                    if all(isinstance(node, SourceFile) for node in cycle):
                        cycle_type = "import"
                        result["circular_imports"].append({
                            "files": [node.path if hasattr(node, 'path') else str(node) for node in cycle],
                            "length": len(cycle)
                        })

                    # Check if all nodes in the cycle are functions
                    elif all(isinstance(node, Function) for node in cycle):
                        cycle_type = "function_call"
                        result["circular_function_calls"].append({
                            "functions": [node.name if hasattr(node, 'name') else str(node) for node in cycle],
                            "length": len(cycle)
                        })

                        # Add as an issue
                        if len(cycle) > 0 and hasattr(cycle[0], 'file') and hasattr(cycle[0].file, 'file_path'):
                            self.issues.append(Issue(
                                file=cycle[0].file.file_path,
                                line=cycle[0].line if hasattr(cycle[0], 'line') else None,
                                message=f"Circular function call dependency detected",
                                severity=IssueSeverity.ERROR,
                                symbol=cycle[0].name if hasattr(cycle[0], 'name') else str(cycle[0]),
                                suggestion="Refactor the code to eliminate circular dependencies"
                            ))
        except Exception as e:
            # Skip errors in cycle detection
            pass

        return result

    def _analyze_module_coupling(self, context: CodebaseContext) -> Dict[str, Any]:
        """Analyze module coupling in the codebase."""
        result = {
            "high_coupling": [],
            "low_cohesion": []
        }

        # Create a mapping of files to their dependencies
        file_dependencies = {}

        # Iterate over all files
        for file_node in [node for node in context.nodes if isinstance(node, SourceFile)]:
            if not hasattr(file_node, 'path'):
                continue

            file_path = str(file_node.path)

            # Get all outgoing dependencies
            dependencies = []
            for succ in context.successors(file_node):
                if isinstance(succ, SourceFile) and hasattr(succ, 'path'):
                    dependencies.append(str(succ.path))

            # Get all symbols in the file
            file_symbols = [node for node in context.nodes if isinstance(node, Symbol) and
                           hasattr(node, 'file') and hasattr(node.file, 'path') and
                           str(node.file.path) == file_path]

            # Calculate coupling metrics
            file_dependencies[file_path] = {
                "dependencies": dependencies,
                "dependency_count": len(dependencies),
                "symbol_count": len(file_symbols),
                "coupling_ratio": len(dependencies) / max(1, len(file_symbols))
            }

        # Identify files with high coupling (many dependencies)
        high_coupling_files = sorted(
            file_dependencies.items(),
            key=lambda x: x[1]["dependency_count"],
            reverse=True
        )[:10]

        result["high_coupling"] = [
            {
                "file": file_path,
                "dependency_count": data["dependency_count"],
                "dependencies": data["dependencies"][:5]  # Limit to first 5 for brevity
            }
            for file_path, data in high_coupling_files
            if data["dependency_count"] > 5  # Only include if it has more than 5 dependencies
        ]

        return result

    def _analyze_call_hierarchy(self, context: CodebaseContext) -> Dict[str, Any]:
        """Analyze function call hierarchy in the codebase."""
        result = {
            "entry_points": [],
            "leaf_functions": [],
            "deep_call_chains": []
        }

        # Find potential entry points (functions not called by others)
        entry_points = []
        for node in context.nodes:
            if isinstance(node, Function) and hasattr(node, 'name'):
                # Check if this function has no incoming CALLS edges
                has_callers = False
                for pred, _, data in context.in_edges(node, data=True):
                    if 'type' in data and data['type'] == EdgeType.CALLS:
                        has_callers = True
                        break

                if not has_callers:
                    entry_points.append(node)

        # Find leaf functions (those that don't call other functions)
        leaf_functions = []
        for node in context.nodes:
            if isinstance(node, Function) and hasattr(node, 'name'):
                # Check if this function has no outgoing CALLS edges
                has_callees = False
                for _, succ, data in context.out_edges(node, data=True):
                    if 'type' in data and data['type'] == EdgeType.CALLS:
                        has_callees = True
                        break

                if not has_callees:
                    leaf_functions.append(node)

        # Record entry points
        result["entry_points"] = [
            {
                "name": func.name,
                "file": func.file.file_path if hasattr(func, 'file') and hasattr(func.file, 'file_path') else "unknown"
            }
            for func in entry_points[:20]  # Limit to 20 for brevity
        ]

        # Record leaf functions
        result["leaf_functions"] = [
            {
                "name": func.name,
                "file": func.file.file_path if hasattr(func, 'file') and hasattr(func.file, 'file_path') else "unknown"
            }
            for func in leaf_functions[:20]  # Limit to 20 for brevity
        ]

        # Find deep call chains
        for entry_point in entry_points:
            try:
                # Create a subgraph containing only Function nodes
                func_nodes = [n for n in context.nodes if isinstance(n, Function)]
                subgraph = context.build_subgraph(func_nodes)

                # Find longest paths from this entry point
                longest_path = []
                for leaf in leaf_functions:
                    try:
                        path = nx.shortest_path(subgraph, entry_point, leaf)
                        if len(path) > len(longest_path):
                            longest_path = path
                    except (nx.NetworkXNoPath, nx.NodeNotFound):
                        pass

                if len(longest_path) > 3:  # Only record if path length > 3
                    call_chain = {
                        "entry_point": entry_point.name,
                        "length": len(longest_path),
                        "calls": [func.name for func in longest_path if hasattr(func, 'name')]
                    }
                    result["deep_call_chains"].append(call_chain)
            except Exception as e:
                # Skip errors in path finding
                pass

        # Sort by chain length and limit to top 10
        result["deep_call_chains"].sort(key=lambda x: x["length"], reverse=True)
        result["deep_call_chains"] = result["deep_call_chains"][:10]

        return result
    
    def _analyze_pr(self) -> Dict[str, Any]:
        """Analyze a PR and find issues."""
        if not self.pr_codebase or not self.pr_diff or not self.commit_shas:
            raise ValueError("PR data not initialized")
            
        pr_analysis = {}
        
        # Get modified symbols and files
        modified_files = set(self.commit_shas.keys())
        pr_analysis["modified_files_count"] = len(modified_files)
        pr_analysis["modified_symbols_count"] = len(self.modified_symbols)
        
        # Analyze modified files
        file_issues = []
        for file_path in modified_files:
            file = self.pr_codebase.get_file(file_path)
            if file:
                # Check file issues
                self._check_file_issues(file)
                
                # Add file summary
                file_issues.append({
                    "file": file_path,
                    "issues": [issue.to_dict() for issue in self.issues if issue.file == file_path]
                })
        
        pr_analysis["file_issues"] = file_issues
        
        # Perform targeted static analysis on modified symbols
        new_func_count = 0
        modified_func_count = 0
        
        for symbol_name in self.modified_symbols:
            symbol = self.pr_codebase.get_symbol(symbol_name)
            if not symbol:
                continue
                
            # Check if function is new or modified
            if symbol.symbol_type == SymbolType.Function:
                # Try to find in base codebase
                try:
                    base_symbol = self.base_codebase.get_symbol(symbol_name)
                    if not base_symbol:
                        new_func_count += 1
                    else:
                        modified_func_count += 1
                except:
                    new_func_count += 1
                    
                # Check function for issues
                func = cast(Function, symbol)
                self._check_function_for_issues(func)
        
        pr_analysis["new_functions"] = new_func_count
        pr_analysis["modified_functions"] = modified_func_count
        
        return pr_analysis
    
    def _compare_codebases(self) -> Dict[str, Any]:
        """
        Compare base codebase with PR codebase using advanced CodebaseContext.

        This method uses the graph representation of both codebases to perform
        a detailed comparison of the structure and relationships between them.
        """
        if not self.base_codebase or not self.pr_codebase:
            raise ValueError("Both base and PR codebases must be initialized")

        if not self.base_context or not self.pr_context:
            raise ValueError("Both base and PR CodebaseContext objects must be initialized")

        comparison = {
            "graph_analysis": {},
            "structure_changes": {},
            "dependency_changes": {},
            "api_changes": {}
        }

        # Compare graph structures using CodebaseContext
        base_nodes = self.base_context.nodes
        pr_nodes = self.pr_context.nodes

        # Analyze nodes that exist in both, only in base, or only in PR
        common_nodes = []
        base_only_nodes = []
        pr_only_nodes = []

        for base_node in base_nodes:
            if hasattr(base_node, 'name'):
                node_name = base_node.name
                # Look for matching node in PR
                pr_node = next((n for n in pr_nodes if hasattr(n, 'name') and n.name == node_name), None)

                if pr_node:
                    common_nodes.append((base_node, pr_node))
                else:
                    base_only_nodes.append(base_node)

        # Find PR-only nodes
        for pr_node in pr_nodes:
            if hasattr(pr_node, 'name'):
                node_name = pr_node.name
                # Check if it already exists in base
                if not any(hasattr(n, 'name') and n.name == node_name for n in base_nodes):
                    pr_only_nodes.append(pr_node)

        # Add graph analysis results
        comparison["graph_analysis"] = {
            "common_node_count": len(common_nodes),
            "base_only_node_count": len(base_only_nodes),
            "pr_only_node_count": len(pr_only_nodes)
        }

        # Compare dependencies using graph edges
        base_edges = list(self.base_context.edges(data=True))
        pr_edges = list(self.pr_context.edges(data=True))

        # Analyze dependency changes
        removed_dependencies = []
        added_dependencies = []

        # Process existing modified symbols
        if self.modified_symbols:
            detailed_comparison = []

            for symbol_name in self.modified_symbols:
                # Check if symbol exists in both codebases using context
                base_symbol = self.base_context.get_node(symbol_name)
                pr_symbol = self.pr_context.get_node(symbol_name)

                if not base_symbol and not pr_symbol:
                    continue

                # Compare symbols
                symbol_comparison = {
                    "name": symbol_name,
                    "in_base": base_symbol is not None,
                    "in_pr": pr_symbol is not None,
                }

                # For functions, compare parameters
                if (base_symbol and hasattr(base_symbol, 'symbol_type') and base_symbol.symbol_type == SymbolType.Function and
                    pr_symbol and hasattr(pr_symbol, 'symbol_type') and pr_symbol.symbol_type == SymbolType.Function):

                    base_func = cast(Function, base_symbol)
                    pr_func = cast(Function, pr_symbol)

                    # Get function dependencies from context
                    base_dependencies = self.base_context.successors(base_func)
                    pr_dependencies = self.pr_context.successors(pr_func)

                    # Analyze dependency changes for this function
                    for dep in base_dependencies:
                        if hasattr(dep, 'name') and not any(hasattr(d, 'name') and d.name == dep.name for d in pr_dependencies):
                            removed_dependencies.append((base_func.name, dep.name))

                    for dep in pr_dependencies:
                        if hasattr(dep, 'name') and not any(hasattr(d, 'name') and d.name == dep.name for d in base_dependencies):
                            added_dependencies.append((pr_func.name, dep.name))
                    
                    # Compare parameter counts
                    base_params = list(base_func.parameters)
                    pr_params = list(pr_func.parameters)
                    
                    param_changes = []
                    removed_params = []
                    added_params = []
                    
                    # Find removed parameters
                    for base_param in base_params:
                        if not any(pr_param.name == base_param.name for pr_param in pr_params if hasattr(pr_param, 'name')):
                            removed_params.append(base_param.name if hasattr(base_param, 'name') else str(base_param))
                    
                    # Find added parameters
                    for pr_param in pr_params:
                        if not any(base_param.name == pr_param.name for base_param in base_params if hasattr(base_param, 'name')):
                            added_params.append(pr_param.name if hasattr(pr_param, 'name') else str(pr_param))
                    
                    symbol_comparison["parameter_changes"] = {
                        "removed": removed_params,
                        "added": added_params
                    }
                    
                    # Check for parameter type changes
                    for base_param in base_params:
                        for pr_param in pr_params:
                            if (hasattr(base_param, 'name') and hasattr(pr_param, 'name') and 
                                base_param.name == pr_param.name):
                                
                                base_type = str(base_param.type) if hasattr(base_param, 'type') and base_param.type else None
                                pr_type = str(pr_param.type) if hasattr(pr_param, 'type') and pr_param.type else None
                                
                                if base_type != pr_type:
                                    param_changes.append({
                                        "param": base_param.name,
                                        "old_type": base_type,
                                        "new_type": pr_type
                                    })
                    
                    if param_changes:
                        symbol_comparison["type_changes"] = param_changes
                    
                    # Check if return type changed
                    base_return_type = str(base_func.return_type) if hasattr(base_func, 'return_type') and base_func.return_type else None
                    pr_return_type = str(pr_func.return_type) if hasattr(pr_func, 'return_type') and pr_func.return_type else None
                    
                    if base_return_type != pr_return_type:
                        symbol_comparison["return_type_change"] = {
                            "old": base_return_type,
                            "new": pr_return_type
                        }
                    
                    # Check call site compatibility
                    if hasattr(base_func, 'call_sites') and hasattr(pr_func, 'call_sites'):
                        base_call_sites = list(base_func.call_sites)
                        call_site_issues = []
                        
                        # For each call site in base, check if it's still compatible with PR function
                        for call_site in base_call_sites:
                            if len(removed_params) > 0 and not all(param.has_default for param in base_params if hasattr(param, 'name') and param.name in removed_params):
                                # Required parameter was removed
                                file_path = call_site.file.file_path if hasattr(call_site, 'file') and hasattr(call_site.file, 'file_path') else "unknown"
                                line = call_site.line if hasattr(call_site, 'line') else None
                                
                                call_site_issues.append({
                                    "file": file_path,
                                    "line": line,
                                    "issue": "Required parameter was removed, call site may be broken"
                                })
                                
                                # Add issue
                                self.issues.append(Issue(
                                    file=file_path,
                                    line=line,
                                    message=f"Call to {symbol_name} may be broken due to signature change",
                                    severity=IssueSeverity.ERROR,
                                    symbol=symbol_name,
                                    suggestion="Update call site to match new function signature"
                                ))
                        
                        if call_site_issues:
                            symbol_comparison["call_site_issues"] = call_site_issues
                
                detailed_comparison.append(symbol_comparison)
            
            comparison["symbol_comparison"] = detailed_comparison
        
        # Compare overall codebase stats
        base_stats = {
            "files": len(list(self.base_codebase.files)),
            "functions": len(list(self.base_codebase.functions)) if hasattr(self.base_codebase, 'functions') else 0,
            "classes": len(list(self.base_codebase.classes)) if hasattr(self.base_codebase, 'classes') else 0,
            "imports": len(list(self.base_codebase.imports)) if hasattr(self.base_codebase, 'imports') else 0,
        }
        
        pr_stats = {
            "files": len(list(self.pr_codebase.files)),
            "functions": len(list(self.pr_codebase.functions)) if hasattr(self.pr_codebase, 'functions') else 0,
            "classes": len(list(self.pr_codebase.classes)) if hasattr(self.pr_codebase, 'classes') else 0,
            "imports": len(list(self.pr_codebase.imports)) if hasattr(self.pr_codebase, 'imports') else 0,
        }
        
        comparison["stats_comparison"] = {
            "base": base_stats,
            "pr": pr_stats,
            "diff": {
                "files": pr_stats["files"] - base_stats["files"],
                "functions": pr_stats["functions"] - base_stats["functions"],
                "classes": pr_stats["classes"] - base_stats["classes"],
                "imports": pr_stats["imports"] - base_stats["imports"],
            }
        }
        
        return comparison
    
    def _find_dead_code(self, codebase: Codebase) -> Dict[str, Any]:
        """Find unused code (dead code) in the codebase."""
        dead_code = {
            "unused_functions": [],
            "unused_classes": [],
            "unused_variables": [],
            "unused_imports": []
        }
        
        # Find unused functions (no call sites)
        if hasattr(codebase, 'functions'):
            for func in codebase.functions:
                if not hasattr(func, 'call_sites'):
                    continue
                    
                if len(func.call_sites) == 0:
                    # Skip magic methods and main functions
                    if (hasattr(func, 'is_magic') and func.is_magic) or (hasattr(func, 'name') and func.name in ['main', '__main__']):
                        continue
                        
                    # Get file and name safely
                    file_path = func.file.file_path if hasattr(func, 'file') and hasattr(func.file, 'file_path') else "unknown"
                    func_name = func.name if hasattr(func, 'name') else str(func)
                    
                    # Add to dead code list and issues
                    dead_code["unused_functions"].append({
                        "name": func_name,
                        "file": file_path,
                        "line": func.line if hasattr(func, 'line') else None
                    })
                    
                    self.issues.append(Issue(
                        file=file_path,
                        line=func.line if hasattr(func, 'line') else None,
                        message=f"Unused function: {func_name}",
                        severity=IssueSeverity.WARNING,
                        symbol=func_name,
                        suggestion="Consider removing or using this function"
                    ))
        
        # Find unused classes (no symbol usages)
        if hasattr(codebase, 'classes'):
            for cls in codebase.classes:
                if not hasattr(cls, 'symbol_usages'):
                    continue
                    
                if len(cls.symbol_usages) == 0:
                    # Get file and name safely
                    file_path = cls.file.file_path if hasattr(cls, 'file') and hasattr(cls.file, 'file_path') else "unknown"
                    cls_name = cls.name if hasattr(cls, 'name') else str(cls)
                    
                    # Add to dead code list and issues
                    dead_code["unused_classes"].append({
                        "name": cls_name,
                        "file": file_path,
                        "line": cls.line if hasattr(cls, 'line') else None
                    })
                    
                    self.issues.append(Issue(
                        file=file_path,
                        line=cls.line if hasattr(cls, 'line') else None,
                        message=f"Unused class: {cls_name}",
                        severity=IssueSeverity.WARNING,
                        symbol=cls_name,
                        suggestion="Consider removing or using this class"
                    ))
        
        # Find unused variables
        if hasattr(codebase, 'global_vars'):
            for var in codebase.global_vars:
                if not hasattr(var, 'symbol_usages'):
                    continue
                    
                if len(var.symbol_usages) == 0:
                    # Get file and name safely
                    file_path = var.file.file_path if hasattr(var, 'file') and hasattr(var.file, 'file_path') else "unknown"
                    var_name = var.name if hasattr(var, 'name') else str(var)
                    
                    # Add to dead code list and issues
                    dead_code["unused_variables"].append({
                        "name": var_name,
                        "file": file_path,
                        "line": var.line if hasattr(var, 'line') else None
                    })
                    
                    self.issues.append(Issue(
                        file=file_path,
                        line=var.line if hasattr(var, 'line') else None,
                        message=f"Unused variable: {var_name}",
                        severity=IssueSeverity.INFO,
                        symbol=var_name,
                        suggestion="Consider removing this unused variable"
                    ))
        
        # Find unused imports
        for file in codebase.files:
            if hasattr(file, 'is_binary') and file.is_binary:
                continue
                
            if not hasattr(file, 'imports'):
                continue
                
            file_path = file.file_path if hasattr(file, 'file_path') else str(file)
            
            for imp in file.imports:
                if not hasattr(imp, 'usages'):
                    continue
                    
                if len(imp.usages) == 0:
                    # Get import source safely
                    import_source = imp.source if hasattr(imp, 'source') else str(imp)
                    
                    # Add to dead code list and issues
                    dead_code["unused_imports"].append({
                        "import": import_source,
                        "file": file_path,
                        "line": imp.line if hasattr(imp, 'line') else None
                    })
                    
                    self.issues.append(Issue(
                        file=file_path,
                        line=imp.line if hasattr(imp, 'line') else None,
                        message=f"Unused import: {import_source}",
                        severity=IssueSeverity.INFO,
                        code=import_source,
                        suggestion="Remove this unused import"
                    ))
        
        # Add total counts
        dead_code["counts"] = {
            "unused_functions": len(dead_code["unused_functions"]),
            "unused_classes": len(dead_code["unused_classes"]),
            "unused_variables": len(dead_code["unused_variables"]),
            "unused_imports": len(dead_code["unused_imports"]),
            "total": len(dead_code["unused_functions"]) + len(dead_code["unused_classes"]) + 
                     len(dead_code["unused_variables"]) + len(dead_code["unused_imports"]),
        }
        
        return dead_code
    
    def _check_function_parameters(self, codebase: Codebase) -> Dict[str, Any]:
        """Check function parameters for issues."""
        parameter_issues = {
            "missing_types": [],
            "inconsistent_types": [],
            "unused_parameters": []
        }
        
        if not hasattr(codebase, 'functions'):
            return parameter_issues
            
        for func in codebase.functions:
            if not hasattr(func, 'parameters'):
                continue
                
            file_path = func.file.file_path if hasattr(func, 'file') and hasattr(func.file, 'file_path') else "unknown"
            func_name = func.name if hasattr(func, 'name') else str(func)
            
            # Check for missing type annotations
            missing_types = []
            for param in func.parameters:
                if not hasattr(param, 'name'):
                    continue
                    
                if not hasattr(param, 'type') or not param.type:
                    missing_types.append(param.name)
                    
            if missing_types:
                parameter_issues["missing_types"].append({
                    "function": func_name,
                    "file": file_path,
                    "line": func.line if hasattr(func, 'line') else None,
                    "parameters": missing_types
                })
                
                self.issues.append(Issue(
                    file=file_path,
                    line=func.line if hasattr(func, 'line') else None,
                    message=f"Function {func_name} has parameters without type annotations: {', '.join(missing_types)}",
                    severity=IssueSeverity.WARNING,
                    symbol=func_name,
                    suggestion="Add type annotations to all parameters"
                ))
            
            # Check for unused parameters
            if hasattr(func, 'source'):
                # This is a simple check that looks for parameter names in the function body
                # A more sophisticated check would analyze the AST
                unused_params = []
                for param in func.parameters:
                    if not hasattr(param, 'name'):
                        continue
                        
                    # Skip self/cls parameter in methods
                    if param.name in ['self', 'cls'] and hasattr(func, 'parent') and func.parent:
                        continue
                    
                    # Check if parameter name appears in function body
                    # This is a simple heuristic and may produce false positives
                    param_regex = r'\b' + re.escape(param.name) + r'\b'
                    body_lines = func.source.split('\n')[1:] if func.source.count('\n') > 0 else []
                    body_text = '\n'.join(body_lines)
                    
                    if not re.search(param_regex, body_text):
                        unused_params.append(param.name)
                
                if unused_params:
                    parameter_issues["unused_parameters"].append({
                        "function": func_name,
                        "file": file_path,
                        "line": func.line if hasattr(func, 'line') else None,
                        "parameters": unused_params
                    })
                    
                    self.issues.append(Issue(
                        file=file_path,
                        line=func.line if hasattr(func, 'line') else None,
                        message=f"Function {func_name} has potentially unused parameters: {', '.join(unused_params)}",
                        severity=IssueSeverity.INFO,
                        symbol=func_name,
                        suggestion="Check if these parameters are actually used"
                    ))
            
            # Check for consistent parameter types across overloaded functions
            if hasattr(codebase, 'functions'):
                # Find functions with the same name
                overloads = [f for f in codebase.functions if hasattr(f, 'name') and f.name == func_name and f != func]
                
                if overloads:
                    for overload in overloads:
                        # Check if the same parameter name has different types
                        if not hasattr(overload, 'parameters'):
                            continue
                            
                        inconsistent_types = []
                        for param in func.parameters:
                            if not hasattr(param, 'name') or not hasattr(param, 'type'):
                                continue
                                
                            # Find matching parameter in overload
                            matching_params = [p for p in overload.parameters if hasattr(p, 'name') and p.name == param.name]
                            
                            for matching_param in matching_params:
                                if (hasattr(matching_param, 'type') and matching_param.type and 
                                    str(matching_param.type) != str(param.type)):
                                    
                                    inconsistent_types.append({
                                        "parameter": param.name,
                                        "type1": str(param.type),
                                        "type2": str(matching_param.type),
                                        "function1": f"{func_name} at {file_path}:{func.line if hasattr(func, 'line') else '?'}",
                                        "function2": f"{overload.name} at {overload.file.file_path if hasattr(overload, 'file') and hasattr(overload.file, 'file_path') else 'unknown'}:{overload.line if hasattr(overload, 'line') else '?'}"
                                    })
                        
                        if inconsistent_types:
                            parameter_issues["inconsistent_types"].extend(inconsistent_types)
                            
                            for issue in inconsistent_types:
                                self.issues.append(Issue(
                                    file=file_path,
                                    line=func.line if hasattr(func, 'line') else None,
                                    message=f"Inconsistent parameter types for {issue['parameter']}: {issue['type1']} vs {issue['type2']}",
                                    severity=IssueSeverity.ERROR,
                                    symbol=func_name,
                                    suggestion="Use consistent parameter types across function overloads"
                                ))
        
        # Add total counts
        parameter_issues["counts"] = {
            "missing_types": len(parameter_issues["missing_types"]),
            "inconsistent_types": len(parameter_issues["inconsistent_types"]),
            "unused_parameters": len(parameter_issues["unused_parameters"]),
            "total": len(parameter_issues["missing_types"]) + len(parameter_issues["inconsistent_types"]) + 
                     len(parameter_issues["unused_parameters"]),
        }
        
        return parameter_issues
    
    def _check_error_handling(self, codebase: Codebase) -> Dict[str, Any]:
        """Check for error handling issues."""
        error_handling = {
            "bare_excepts": [],
            "pass_in_except": [],
            "errors_not_raised": []
        }
        
        if not hasattr(codebase, 'functions'):
            return error_handling
            
        for func in codebase.functions:
            if not hasattr(func, 'source'):
                continue
                
            file_path = func.file.file_path if hasattr(func, 'file') and hasattr(func.file, 'file_path') else "unknown"
            func_name = func.name if hasattr(func, 'name') else str(func)
            
            # Check for bare except clauses
            if re.search(r'except\s*:', func.source):
                error_handling["bare_excepts"].append({
                    "function": func_name,
                    "file": file_path,
                    "line": func.line if hasattr(func, 'line') else None,
                })
                
                self.issues.append(Issue(
                    file=file_path,
                    line=func.line if hasattr(func, 'line') else None,
                    message=f"Function {func_name} uses bare 'except:' clause",
                    severity=IssueSeverity.WARNING,
                    symbol=func_name,
                    suggestion="Specify exception types to catch"
                ))
            
            # Check for 'pass' in except blocks
            if re.search(r'except[^:]*:.*\bpass\b', func.source, re.DOTALL):
                error_handling["pass_in_except"].append({
                    "function": func_name,
                    "file": file_path,
                    "line": func.line if hasattr(func, 'line') else None,
                })
                
                self.issues.append(Issue(
                    file=file_path,
                    line=func.line if hasattr(func, 'line') else None,
                    message=f"Function {func_name} silently ignores exceptions with 'pass'",
                    severity=IssueSeverity.WARNING,
                    symbol=func_name,
                    suggestion="Add proper error handling or logging"
                ))
            
            # Check for error classes that aren't raised
            if hasattr(func, 'symbol_type') and func.symbol_type == SymbolType.Class:
                # Check if class name contains 'Error' or 'Exception'
                if hasattr(func, 'name') and ('Error' in func.name or 'Exception' in func.name):
                    cls = cast(Class, func)
                    
                    # Check if class extends Exception
                    is_exception = False
                    if hasattr(cls, 'superclasses'):
                        superclass_names = [sc.name for sc in cls.superclasses if hasattr(sc, 'name')]
                        if any(name in ['Exception', 'BaseException'] for name in superclass_names):
                            is_exception = True
                    
                    if is_exception and hasattr(cls, 'symbol_usages') and not any('raise' in str(usage) for usage in cls.symbol_usages):
                        error_handling["errors_not_raised"].append({
                            "class": cls.name,
                            "file": file_path,
                            "line": cls.line if hasattr(cls, 'line') else None,
                        })
                        
                        self.issues.append(Issue(
                            file=file_path,
                            line=cls.line if hasattr(cls, 'line') else None,
                            message=f"Exception class {cls.name} is defined but never raised",
                            severity=IssueSeverity.INFO,
                            symbol=cls.name,
                            suggestion="Either use this exception or remove it"
                        ))
        
        # Add total counts
        error_handling["counts"] = {
            "bare_excepts": len(error_handling["bare_excepts"]),
            "pass_in_except": len(error_handling["pass_in_except"]),
            "errors_not_raised": len(error_handling["errors_not_raised"]),
            "total": len(error_handling["bare_excepts"]) + len(error_handling["pass_in_except"]) + 
                     len(error_handling["errors_not_raised"]),
        }
        
        return error_handling
    
    def _check_call_sites(self, codebase: Codebase) -> Dict[str, Any]:
        """Check for issues with function call sites."""
        call_site_issues = {
            "wrong_parameter_count": [],
            "wrong_return_type_usage": []
        }
        
        if not hasattr(codebase, 'functions'):
            return call_site_issues
            
        for func in codebase.functions:
            if not hasattr(func, 'call_sites'):
                continue
                
            file_path = func.file.file_path if hasattr(func, 'file') and hasattr(func.file, 'file_path') else "unknown"
            func_name = func.name if hasattr(func, 'name') else str(func)
            
            # Get required parameter count (excluding those with defaults)
            required_count = 0
            if hasattr(func, 'parameters'):
                required_count = sum(1 for p in func.parameters if not hasattr(p, 'has_default') or not p.has_default)
            
            # Check each call site
            for call_site in func.call_sites:
                if not hasattr(call_site, 'args'):
                    continue
                    
                # Get call site file info
                call_file = call_site.file.file_path if hasattr(call_site, 'file') and hasattr(call_site.file, 'file_path') else "unknown"
                call_line = call_site.line if hasattr(call_site, 'line') else None
                
                # Check parameter count
                arg_count = len(call_site.args)
                if arg_count < required_count:
                    call_site_issues["wrong_parameter_count"].append({
                        "function": func_name,
                        "caller_file": call_file,
                        "caller_line": call_line,
                        "required_count": required_count,
                        "provided_count": arg_count
                    })
                    
                    self.issues.append(Issue(
                        file=call_file,
                        line=call_line,
                        message=f"Call to {func_name} has too few arguments ({arg_count} provided, {required_count} required)",
                        severity=IssueSeverity.ERROR,
                        symbol=func_name,
                        suggestion=f"Provide all required arguments to {func_name}"
                    ))
        
        # Add total counts
        call_site_issues["counts"] = {
            "wrong_parameter_count": len(call_site_issues["wrong_parameter_count"]),
            "wrong_return_type_usage": len(call_site_issues["wrong_return_type_usage"]),
            "total": len(call_site_issues["wrong_parameter_count"]) + len(call_site_issues["wrong_return_type_usage"]),
        }
        
        return call_site_issues
    
    def _check_imports(self, codebase: Codebase) -> Dict[str, Any]:
        """Check for import issues."""
        import_issues = {
            "circular_imports": [],
            "wildcard_imports": []
        }
        
        # Check for circular imports
        try:
            # Build dependency graph
            dependency_map = {}
            
            for file in codebase.files:
                if hasattr(file, 'is_binary') and file.is_binary:
                    continue
                    
                if not hasattr(file, 'imports'):
                    continue
                    
                file_path = file.file_path if hasattr(file, 'file_path') else str(file)
                imports = []
                
                for imp in file.imports:
                    if hasattr(imp, "imported_symbol") and imp.imported_symbol:
                        imported_symbol = imp.imported_symbol
                        if hasattr(imported_symbol, "file") and imported_symbol.file:
                            imported_file_path = imported_symbol.file.file_path if hasattr(imported_symbol.file, 'file_path') else str(imported_symbol.file)
                            imports.append(imported_file_path)
                
                dependency_map[file_path] = imports
            
            # Create a directed graph
            import networkx as nx
            G = nx.DiGraph()
            
            # Add nodes and edges
            for file_path, imports in dependency_map.items():
                G.add_node(file_path)
                for imp in imports:
                    if imp in dependency_map:  # Only add edges for files that exist in our dependency map
                        G.add_edge(file_path, imp)
            
            # Find cycles
            try:
                cycles = list(nx.simple_cycles(G))
                
                for cycle in cycles:
                    import_issues["circular_imports"].append({
                        "cycle": cycle,
                        "length": len(cycle)
                    })
                    
                    # Create an issue for each file in the cycle
                    for file_path in cycle:
                        self.issues.append(Issue(
                            file=file_path,
                            line=None,
                            message=f"Circular import detected: {' -> '.join(cycle)}",
                            severity=IssueSeverity.ERROR,
                            suggestion="Refactor imports to break circular dependency"
                        ))
            except nx.NetworkXNoCycle:
                pass  # No cycles found
                
        except Exception as e:
            logger.error(f"Error detecting circular imports: {e}")
        
        # Check for wildcard imports
        for file in codebase.files:
            if hasattr(file, 'is_binary') and file.is_binary:
                continue
                
            if not hasattr(file, 'imports'):
                continue
                
            file_path = file.file_path if hasattr(file, 'file_path') else str(file)
            
            for imp in file.imports:
                if not hasattr(imp, 'source'):
                    continue
                    
                # Check for wildcard imports (from module import *)
                if re.search(r'from\s+[\w.]+\s+import\s+\*', imp.source):
                    import_issues["wildcard_imports"].append({
                        "file": file_path,
                        "line": imp.line if hasattr(imp, 'line') else None,
                        "import": imp.source
                    })
                    
                    self.issues.append(Issue(
                        file=file_path,
                        line=imp.line if hasattr(imp, 'line') else None,
                        message=f"Wildcard import: {imp.source}",
                        severity=IssueSeverity.WARNING,
                        code=imp.source,
                        suggestion="Import specific symbols instead of using wildcard imports"
                    ))
        
        # Add total counts
        import_issues["counts"] = {
            "circular_imports": len(import_issues["circular_imports"]),
            "wildcard_imports": len(import_issues["wildcard_imports"]),
            "total": len(import_issues["circular_imports"]) + len(import_issues["wildcard_imports"]),
        }
        
        return import_issues
    
    def _check_inheritance(self, codebase: Codebase) -> Dict[str, Any]:
        """Check for inheritance issues."""
        inheritance_issues = {
            "deep_inheritance": [],
            "multiple_inheritance": [],
            "inconsistent_interfaces": []
        }
        
        if not hasattr(codebase, 'classes'):
            return inheritance_issues
            
        for cls in codebase.classes:
            if not hasattr(cls, 'superclasses'):
                continue
                
            file_path = cls.file.file_path if hasattr(cls, 'file') and hasattr(cls.file, 'file_path') else "unknown"
            cls_name = cls.name if hasattr(cls, 'name') else str(cls)
            
            # Check inheritance depth
            inheritance_depth = len(cls.superclasses)
            if inheritance_depth > 3:  # Arbitrary threshold for deep inheritance
                inheritance_issues["deep_inheritance"].append({
                    "class": cls_name,
                    "file": file_path,
                    "line": cls.line if hasattr(cls, 'line') else None,
                    "depth": inheritance_depth,
                    "hierarchy": [sc.name if hasattr(sc, 'name') else str(sc) for sc in cls.superclasses]
                })
                
                self.issues.append(Issue(
                    file=file_path,
                    line=cls.line if hasattr(cls, 'line') else None,
                    message=f"Deep inheritance detected for class {cls_name} (depth: {inheritance_depth})",
                    severity=IssueSeverity.WARNING,
                    symbol=cls_name,
                    suggestion="Consider composition over inheritance or flattening the hierarchy"
                ))
            
            # Check multiple inheritance
            if inheritance_depth > 1:
                inheritance_issues["multiple_inheritance"].append({
                    "class": cls_name,
                    "file": file_path,
                    "line": cls.line if hasattr(cls, 'line') else None,
                    "superclasses": [sc.name if hasattr(sc, 'name') else str(sc) for sc in cls.superclasses]
                })
                
                # We don't create an issue for this by default, as multiple inheritance is not always bad
        
        # Add total counts
        inheritance_issues["counts"] = {
            "deep_inheritance": len(inheritance_issues["deep_inheritance"]),
            "multiple_inheritance": len(inheritance_issues["multiple_inheritance"]),
            "inconsistent_interfaces": len(inheritance_issues["inconsistent_interfaces"]),
            "total": len(inheritance_issues["deep_inheritance"]) + len(inheritance_issues["multiple_inheritance"]) + 
                     len(inheritance_issues["inconsistent_interfaces"]),
        }
        
        return inheritance_issues
    
    def _analyze_code_complexity(self, codebase: Codebase) -> Dict[str, Any]:
        """Analyze code complexity."""
        complexity = {
            "complex_functions": [],
            "long_functions": [],
            "deeply_nested_code": []
        }
        
        if not hasattr(codebase, 'functions'):
            return complexity
            
        for func in codebase.functions:
            if not hasattr(func, 'source'):
                continue
                
            file_path = func.file.file_path if hasattr(func, 'file') and hasattr(func.file, 'file_path') else "unknown"
            func_name = func.name if hasattr(func, 'name') else str(func)
            
            # Check function length
            func_lines = func.source.count('\n') + 1
            if func_lines > 50:  # Arbitrary threshold for long functions
                complexity["long_functions"].append({
                    "function": func_name,
                    "file": file_path,
                    "line": func.line if hasattr(func, 'line') else None,
                    "length": func_lines
                })
                
                self.issues.append(Issue(
                    file=file_path,
                    line=func.line if hasattr(func, 'line') else None,
                    message=f"Function {func_name} is too long ({func_lines} lines)",
                    severity=IssueSeverity.WARNING,
                    symbol=func_name,
                    suggestion="Consider breaking this function into smaller functions"
                ))
            
            # Check cyclomatic complexity (approximate)
            # Count branch points (if, for, while, case, etc.)
            branch_points = (
                func.source.count('if ') + 
                func.source.count('elif ') + 
                func.source.count('for ') + 
                func.source.count('while ') + 
                func.source.count('case ') + 
                func.source.count('except ') + 
                func.source.count(' and ') + 
                func.source.count(' or ')
            )
            
            if branch_points > 10:  # Arbitrary threshold for complex functions
                complexity["complex_functions"].append({
                    "function": func_name,
                    "file": file_path,
                    "line": func.line if hasattr(func, 'line') else None,
                    "branch_points": branch_points
                })
                
                self.issues.append(Issue(
                    file=file_path,
                    line=func.line if hasattr(func, 'line') else None,
                    message=f"Function {func_name} is complex (branch points: {branch_points})",
                    severity=IssueSeverity.WARNING,
                    symbol=func_name,
                    suggestion="Refactor to reduce complexity"
                ))
            
            # Check nesting depth
            lines = func.source.split('\n')
            max_indent = 0
            for line in lines:
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent)
            
            # Estimate nesting depth (rough approximation)
            est_nesting_depth = max_indent // 4  # Assuming 4 spaces per indent level
            
            if est_nesting_depth > 4:  # Arbitrary threshold for deeply nested code
                complexity["deeply_nested_code"].append({
                    "function": func_name,
                    "file": file_path,
                    "line": func.line if hasattr(func, 'line') else None,
                    "estimated_nesting_depth": est_nesting_depth
                })
                
                self.issues.append(Issue(
                    file=file_path,
                    line=func.line if hasattr(func, 'line') else None,
                    message=f"Function {func_name} has deeply nested code (est. depth: {est_nesting_depth})",
                    severity=IssueSeverity.WARNING,
                    symbol=func_name,
                    suggestion="Refactor to reduce nesting by extracting methods or using early returns"
                ))
        
        # Add total counts
        complexity["counts"] = {
            "complex_functions": len(complexity["complex_functions"]),
            "long_functions": len(complexity["long_functions"]),
            "deeply_nested_code": len(complexity["deeply_nested_code"]),
            "total": len(complexity["complex_functions"]) + len(complexity["long_functions"]) + 
                     len(complexity["deeply_nested_code"]),
        }
        
        return complexity
    
    def _check_file_issues(self, file: SourceFile) -> None:
        """Check a file for issues."""
        # Skip binary files
        if hasattr(file, 'is_binary') and file.is_binary:
            return
            
        file_path = file.file_path if hasattr(file, 'file_path') else str(file)
        
        # Check file size
        if hasattr(file, 'content'):
            file_size = len(file.content)
            if file_size > 500 * 1024:  # 500 KB
                self.issues.append(Issue(
                    file=file_path,
                    line=None,
                    message=f"File is very large ({file_size / 1024:.1f} KB)",
                    severity=IssueSeverity.WARNING,
                    suggestion="Consider breaking this file into smaller modules"
                ))
        
        # Check for too many imports
        if hasattr(file, 'imports') and len(file.imports) > 30:  # Arbitrary threshold
            self.issues.append(Issue(
                file=file_path,
                line=None,
                message=f"File has too many imports ({len(file.imports)})",
                severity=IssueSeverity.WARNING,
                suggestion="Consider refactoring to reduce the number of imports"
            ))
        
        # Check for file-level issues in symbol definitions
        if hasattr(file, 'symbols'):
            # Check for mixing class and function definitions at the top level
            toplevel_classes = [s for s in file.symbols if hasattr(s, 'symbol_type') and s.symbol_type == SymbolType.Class]
            toplevel_functions = [s for s in file.symbols if hasattr(s, 'symbol_type') and s.symbol_type == SymbolType.Function]
            
            if len(toplevel_classes) > 0 and len(toplevel_functions) > 5:
                self.issues.append(Issue(
                    file=file_path,
                    line=None,
                    message=f"File mixes classes and many functions at the top level",
                    severity=IssueSeverity.INFO,
                    suggestion="Consider separating classes and functions into different modules"
                ))
    
    def _check_function_for_issues(self, func: Function) -> None:
        """Check a function for issues."""
        file_path = func.file.file_path if hasattr(func, 'file') and hasattr(func.file, 'file_path') else "unknown"
        func_name = func.name if hasattr(func, 'name') else str(func)
        
        # Check for return type
        if not hasattr(func, 'return_type') or not func.return_type:
            self.issues.append(Issue(
                file=file_path,
                line=func.line if hasattr(func, 'line') else None,
                message=f"Function {func_name} lacks a return type annotation",
                severity=IssueSeverity.WARNING,
                symbol=func_name,
                suggestion="Add a return type annotation"
            ))
        
        # Check parameters for types
        if hasattr(func, 'parameters'):
            missing_types = [p.name for p in func.parameters if hasattr(p, 'name') and (not hasattr(p, 'type') or not p.type)]
            if missing_types:
                self.issues.append(Issue(
                    file=file_path,
                    line=func.line if hasattr(func, 'line') else None,
                    message=f"Function {func_name} has parameters without type annotations: {', '.join(missing_types)}",
                    severity=IssueSeverity.WARNING,
                    symbol=func_name,
                    suggestion="Add type annotations to all parameters"
                ))
        
        # Check for docstring
        if hasattr(func, 'source'):
            lines = func.source.split('\n')
            if len(lines) > 1:
                # Check if second line starts a docstring
                if not any(line.strip().startswith('"""') or line.strip().startswith("'''") for line in lines[:3]):
                    self.issues.append(Issue(
                        file=file_path,
                        line=func.line if hasattr(func, 'line') else None,
                        message=f"Function {func_name} lacks a docstring",
                        severity=IssueSeverity.INFO,
                        symbol=func_name,
                        suggestion="Add a docstring describing the function's purpose, parameters, and return value"
                    ))
        
        # Check for error handling in async functions
        if hasattr(func, 'is_async') and func.is_async and hasattr(func, 'source'):
            if 'await' in func.source and 'try' not in func.source:
                self.issues.append(Issue(
                    file=file_path,
                    line=func.line if hasattr(func, 'line') else None,
                    message=f"Async function {func_name} has awaits without try/except",
                    severity=IssueSeverity.WARNING,
                    symbol=func_name,
                    suggestion="Add error handling for await expressions"
                ))

def main():
    """Main entry point for the codebase analyzer."""
    parser = argparse.ArgumentParser(description="Comprehensive Codebase and PR Analyzer")
    
    # Repository source options
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--repo-url", help="URL of the repository to analyze")
    source_group.add_argument("--repo-path", help="Local path to the repository to analyze")
    
    # Analysis options
    parser.add_argument("--analysis-type", choices=["codebase", "pr", "comparison"], default="codebase",
                        help="Type of analysis to perform (default: codebase)")
    parser.add_argument("--language", choices=["python", "typescript"], help="Programming language (auto-detected if not provided)")
    parser.add_argument("--base-branch", default="main", help="Base branch for PR comparison (default: main)")
    parser.add_argument("--pr-number", type=int, help="PR number to analyze")
    
    # Output options
    parser.add_argument("--output-format", choices=["json", "html", "console"], default="json", help="Output format")
    parser.add_argument("--output-file", help="Path to the output file")
    
    args = parser.parse_args()
    
    try:
        # Initialize the analyzer
        analyzer = CodebaseAnalyzer(
            repo_url=args.repo_url,
            repo_path=args.repo_path,
            base_branch=args.base_branch,
            pr_number=args.pr_number,
            language=args.language
        )
        
        # Perform the analysis
        analysis_type = AnalysisType(args.analysis_type)
        results = analyzer.analyze(analysis_type)
        
        # Output the results
        if args.output_format == "json":
            if args.output_file:
                with open(args.output_file, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"Analysis results saved to {args.output_file}")
            else:
                print(json.dumps(results, indent=2))
        elif args.output_format == "html":
            # Create a simple HTML report
            if not args.output_file:
                args.output_file = "codebase_analysis_report.html"
                
            with open(args.output_file, 'w') as f:
                f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Codebase Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        .error {{ color: red; }}
        .warning {{ color: orange; }}
        .info {{ color: blue; }}
        .section {{ margin-bottom: 30px; }}
        pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>Codebase Analysis Report</h1>
    <div class="section">
        <h2>Summary</h2>
        <p>Repository: {results["metadata"]["repo_name"]}</p>
        <p>Language: {results["metadata"]["language"]}</p>
        <p>Analysis Type: {results["metadata"]["analysis_type"]}</p>
        <p>Analysis Time: {results["metadata"]["analysis_time"]}</p>
        <p>Total Issues: {results["issue_counts"]["total"]}</p>
        <ul>
            <li class="error">Errors: {results["issue_counts"]["by_severity"]["error"]}</li>
            <li class="warning">Warnings: {results["issue_counts"]["by_severity"]["warning"]}</li>
            <li class="info">Info: {results["issue_counts"]["by_severity"]["info"]}</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>Issues</h2>
        <ul>
""")
                
                # Add issues
                for issue in results["issues"]:
                    severity_class = issue["severity"]
                    location = f"{issue['file']}:{issue['line']}" if issue['line'] else issue['file']
                    
                    f.write(f"""
            <li class="{severity_class}">
                <strong>{location}</strong>: {issue['message']}
                {f"<br><em>Symbol: {issue['symbol']}</em>" if issue['symbol'] else ""}
                {f"<br><em>Suggestion: {issue['suggestion']}</em>" if issue['suggestion'] else ""}
            </li>
""")
                
                f.write("""
        </ul>
    </div>
    
    <div class="section">
        <h2>Detailed Analysis</h2>
        <pre>""")
                
                # Add detailed analysis as formatted JSON
                f.write(json.dumps(results, indent=2))
                
                f.write("""
        </pre>
    </div>
</body>
</html>
""")
                
                print(f"HTML report saved to {args.output_file}")
                
        elif args.output_format == "console":
            print(f"===== Codebase Analysis Report =====")
            print(f"Repository: {results['metadata']['repo_name']}")
            print(f"Language: {results['metadata']['language']}")
            print(f"Analysis Type: {results['metadata']['analysis_type']}")
            print(f"Analysis Time: {results['metadata']['analysis_time']}")
            print(f"Total Issues: {results['issue_counts']['total']}")
            print(f"  Errors: {results['issue_counts']['by_severity']['error']}")
            print(f"  Warnings: {results['issue_counts']['by_severity']['warning']}")
            print(f"  Info: {results['issue_counts']['by_severity']['info']}")
            
            print("\n===== Issues =====")
            for issue in results["issues"]:
                severity = issue["severity"].upper()
                location = f"{issue['file']}:{issue['line']}" if issue['line'] else issue['file']
                print(f"[{severity}] {location}: {issue['message']}")
                if issue['symbol']:
                    print(f"  Symbol: {issue['symbol']}")
                if issue['suggestion']:
                    print(f"  Suggestion: {issue['suggestion']}")
                print()
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()