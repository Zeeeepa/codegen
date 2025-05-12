#!/usr/bin/env python3
"""
Unified Codebase Analyzer Module

This module consolidates various analyzer functionalities into a cohesive architecture,
reducing code duplication and providing a standard interface for all types of codebase analysis.
It enables comprehensive analysis of codebases including code quality, dependencies,
structural patterns, and issue detection.
"""

import json
import logging
import sys
import tempfile
from datetime import datetime
from typing import Any

import networkx as nx

try:
    from codegen.configs.models.codebase import CodebaseConfig
    from codegen.configs.models.secrets import SecretsConfig
    from codegen.git.repo_operator.repo_operator import RepoOperator
    from codegen.git.schemas.repo_config import RepoConfig
    from codegen.sdk.codebase.codebase_analysis import (
        get_codebase_summary,
        get_file_summary,
    )
    from codegen.sdk.codebase.config import ProjectConfig
    from codegen.sdk.core.class_definition import Class
    from codegen.sdk.core.codebase import Codebase
    from codegen.sdk.core.file import SourceFile
    from codegen.sdk.core.function import Function
    from codegen.sdk.core.symbol import Symbol
    from codegen.sdk.enums import EdgeType, SymbolType
    from codegen.shared.enums.programming_language import ProgrammingLanguage

    from codegen_on_oss.analyzers.issue_types import (
        AnalysisType,
        Issue,
        IssueCategory,
        IssueSeverity,
    )

    # Import from our own modules
    from codegen_on_oss.context_codebase import (
        GLOBAL_FILE_IGNORE_LIST,
        CodebaseContext,
        get_node_classes,
    )
    from codegen_on_oss.current_code_codebase import get_selected_codebase
except ImportError:
    print("Codegen SDK or required modules not found.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class AnalyzerRegistry:
    """
    Registry of analyzer plugins.

    This singleton maintains a registry of all analyzer plugins and their
    associated analysis types.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._analyzers = {}
        return cls._instance

    def register(
        self, analysis_type: AnalysisType, analyzer_class: type["AnalyzerPlugin"]
    ):
        """
        Register an analyzer plugin for a specific analysis type.

        Args:
            analysis_type: Type of analysis the plugin handles
            analyzer_class: Class of the analyzer plugin
        """
        self._analyzers[analysis_type] = analyzer_class

    def get_analyzer(
        self, analysis_type: AnalysisType
    ) -> type["AnalyzerPlugin"] | None:
        """
        Get the analyzer plugin for a specific analysis type.

        Args:
            analysis_type: Type of analysis to get plugin for

        Returns:
            The analyzer plugin class, or None if not found
        """
        return self._analyzers.get(analysis_type)

    def list_analyzers(self) -> dict[AnalysisType, type["AnalyzerPlugin"]]:
        """
        Get all registered analyzers.

        Returns:
            Dictionary mapping analysis types to analyzer plugin classes
        """
        return self._analyzers.copy()


class AnalyzerPlugin:
    """
    Base class for analyzer plugins.

    Analyzer plugins implement specific analysis functionality for different
    types of codebase analysis.
    """

    def __init__(self, analyzer: "UnifiedCodeAnalyzer"):
        """
        Initialize the analyzer plugin.

        Args:
            analyzer: Parent analyzer that owns this plugin
        """
        self.analyzer = analyzer
        self.issues = []

    def analyze(self) -> dict[str, Any]:
        """
        Perform analysis using this plugin.

        Returns:
            Dictionary containing analysis results
        """
        raise NotImplementedError("Analyzer plugins must implement analyze()")

    def add_issue(self, issue: Issue):
        """
        Add an issue to the list.

        Args:
            issue: Issue to add
        """
        self.analyzer.add_issue(issue)
        self.issues.append(issue)


class CodeQualityAnalyzerPlugin(AnalyzerPlugin):
    """
    Plugin for code quality analysis.

    This plugin detects issues related to code quality, including
    dead code, complexity, style, and maintainability.
    """

    def analyze(self) -> dict[str, Any]:
        """
        Perform code quality analysis.

        Returns:
            Dictionary containing code quality analysis results
        """
        result = {}

        # Perform code quality checks
        result["dead_code"] = self._find_dead_code()
        result["complexity"] = self._analyze_code_complexity()
        result["style_issues"] = self._check_style_issues()
        result["maintainability"] = self._calculate_maintainability()

        return result

    def _find_dead_code(self) -> dict[str, Any]:
        """Find unused code (dead code) in the codebase."""
        codebase = self.analyzer.base_codebase

        dead_code = {
            "unused_functions": [],
            "unused_classes": [],
            "unused_variables": [],
            "unused_imports": [],
        }

        # Find unused functions
        if hasattr(codebase, "functions"):
            for func in codebase.functions:
                # Skip if function should be excluded
                if self.analyzer.should_skip_symbol(func):
                    continue

                # Skip decorated functions (as they might be used indirectly)
                if hasattr(func, "decorators") and func.decorators:
                    continue

                # Check if function has no call sites or usages
                has_call_sites = (
                    hasattr(func, "call_sites") and len(func.call_sites) > 0
                )
                has_usages = hasattr(func, "usages") and len(func.usages) > 0

                if not has_call_sites and not has_usages:
                    # Get file path and name safely
                    file_path = (
                        func.file.file_path
                        if hasattr(func, "file") and hasattr(func.file, "file_path")
                        else "unknown"
                    )
                    func_name = func.name if hasattr(func, "name") else str(func)

                    # Skip main entry points
                    if func_name in ["main", "__main__"]:
                        continue

                    # Add to dead code list
                    dead_code["unused_functions"].append({
                        "name": func_name,
                        "file": file_path,
                        "line": func.line if hasattr(func, "line") else None,
                    })

                    # Add issue
                    self.add_issue(
                        Issue(
                            file=file_path,
                            line=func.line if hasattr(func, "line") else None,
                            message=f"Unused function: {func_name}",
                            severity=IssueSeverity.WARNING,
                            category=IssueCategory.DEAD_CODE,
                            symbol=func_name,
                            suggestion="Consider removing this unused function or documenting why it's needed",
                        )
                    )

        # Find unused classes
        if hasattr(codebase, "classes"):
            for cls in codebase.classes:
                # Skip if class should be excluded
                if self.analyzer.should_skip_symbol(cls):
                    continue

                # Check if class has no usages
                has_usages = hasattr(cls, "usages") and len(cls.usages) > 0

                if not has_usages:
                    # Get file path and name safely
                    file_path = (
                        cls.file.file_path
                        if hasattr(cls, "file") and hasattr(cls.file, "file_path")
                        else "unknown"
                    )
                    cls_name = cls.name if hasattr(cls, "name") else str(cls)

                    # Add to dead code list
                    dead_code["unused_classes"].append({
                        "name": cls_name,
                        "file": file_path,
                        "line": cls.line if hasattr(cls, "line") else None,
                    })

                    # Add issue
                    self.add_issue(
                        Issue(
                            file=file_path,
                            line=cls.line if hasattr(cls, "line") else None,
                            message=f"Unused class: {cls_name}",
                            severity=IssueSeverity.WARNING,
                            category=IssueCategory.DEAD_CODE,
                            symbol=cls_name,
                            suggestion="Consider removing this unused class or documenting why it's needed",
                        )
                    )

        # Summarize findings
        dead_code["summary"] = {
            "unused_functions_count": len(dead_code["unused_functions"]),
            "unused_classes_count": len(dead_code["unused_classes"]),
            "unused_variables_count": len(dead_code["unused_variables"]),
            "unused_imports_count": len(dead_code["unused_imports"]),
            "total_dead_code_count": (
                len(dead_code["unused_functions"])
                + len(dead_code["unused_classes"])
                + len(dead_code["unused_variables"])
                + len(dead_code["unused_imports"])
            ),
        }

        return dead_code

    def _analyze_code_complexity(self) -> dict[str, Any]:
        """Analyze code complexity."""
        codebase = self.analyzer.base_codebase

        complexity_result = {
            "function_complexity": [],
            "high_complexity_functions": [],
            "average_complexity": 0.0,
            "complexity_distribution": {
                "low": 0,
                "medium": 0,
                "high": 0,
                "very_high": 0,
            },
        }

        # Process all functions to calculate complexity
        total_complexity = 0
        function_count = 0

        if hasattr(codebase, "functions"):
            for func in codebase.functions:
                # Skip if function should be excluded
                if self.analyzer.should_skip_symbol(func):
                    continue

                # Skip if no code block
                if not hasattr(func, "code_block"):
                    continue

                # Calculate cyclomatic complexity
                complexity = self._calculate_cyclomatic_complexity(func)

                # Get file path and name safely
                file_path = (
                    func.file.file_path
                    if hasattr(func, "file") and hasattr(func.file, "file_path")
                    else "unknown"
                )
                func_name = func.name if hasattr(func, "name") else str(func)

                # Add to complexity list
                complexity_result["function_complexity"].append({
                    "name": func_name,
                    "file": file_path,
                    "line": func.line if hasattr(func, "line") else None,
                    "complexity": complexity,
                })

                # Track total complexity
                total_complexity += complexity
                function_count += 1

                # Categorize complexity
                if complexity <= 5:
                    complexity_result["complexity_distribution"]["low"] += 1
                elif complexity <= 10:
                    complexity_result["complexity_distribution"]["medium"] += 1
                elif complexity <= 15:
                    complexity_result["complexity_distribution"]["high"] += 1
                else:
                    complexity_result["complexity_distribution"]["very_high"] += 1

                # Flag high complexity functions
                if complexity > 10:
                    complexity_result["high_complexity_functions"].append({
                        "name": func_name,
                        "file": file_path,
                        "line": func.line if hasattr(func, "line") else None,
                        "complexity": complexity,
                    })

                    # Add issue
                    severity = (
                        IssueSeverity.WARNING
                        if complexity <= 15
                        else IssueSeverity.ERROR
                    )
                    self.add_issue(
                        Issue(
                            file=file_path,
                            line=func.line if hasattr(func, "line") else None,
                            message=f"High cyclomatic complexity: {complexity}",
                            severity=severity,
                            category=IssueCategory.COMPLEXITY,
                            symbol=func_name,
                            suggestion="Consider refactoring this function to reduce complexity",
                        )
                    )

        # Calculate average complexity
        complexity_result["average_complexity"] = (
            total_complexity / function_count if function_count > 0 else 0.0
        )

        # Sort high complexity functions by complexity
        complexity_result["high_complexity_functions"].sort(
            key=lambda x: x["complexity"], reverse=True
        )

        return complexity_result

    def _calculate_cyclomatic_complexity(self, function) -> int:
        """Calculate cyclomatic complexity for a function."""
        complexity = 1  # Base complexity

        def analyze_statement(statement):
            nonlocal complexity

            # Check for if statements (including elif branches)
            if hasattr(statement, "if_clause"):
                complexity += 1

            # Count elif branches
            if hasattr(statement, "elif_statements"):
                complexity += len(statement.elif_statements)

            # Count else branches
            if hasattr(statement, "else_clause") and statement.else_clause:
                complexity += 1

            # Count for loops
            if hasattr(statement, "is_for_loop") and statement.is_for_loop:
                complexity += 1

            # Count while loops
            if hasattr(statement, "is_while_loop") and statement.is_while_loop:
                complexity += 1

            # Count try/except blocks (each except adds a path)
            if hasattr(statement, "is_try_block") and statement.is_try_block:
                if hasattr(statement, "except_clauses"):
                    complexity += len(statement.except_clauses)

            # Recursively process nested statements
            if hasattr(statement, "statements"):
                for nested_stmt in statement.statements:
                    analyze_statement(nested_stmt)

        # Process all statements in the function's code block
        if hasattr(function, "code_block") and hasattr(
            function.code_block, "statements"
        ):
            for statement in function.code_block.statements:
                analyze_statement(statement)

        return complexity

    def _check_style_issues(self) -> dict[str, Any]:
        """Check for code style issues."""
        codebase = self.analyzer.base_codebase

        style_result = {
            "long_functions": [],
            "long_lines": [],
            "inconsistent_naming": [],
            "summary": {
                "long_functions_count": 0,
                "long_lines_count": 0,
                "inconsistent_naming_count": 0,
            },
        }

        # Check for long functions (too many lines)
        if hasattr(codebase, "functions"):
            for func in codebase.functions:
                # Skip if function should be excluded
                if self.analyzer.should_skip_symbol(func):
                    continue

                # Get function code
                if hasattr(func, "source"):
                    code = func.source
                    lines = code.split("\n")

                    # Check function length
                    if len(lines) > 50:  # Threshold for "too long"
                        # Get file path and name safely
                        file_path = (
                            func.file.file_path
                            if hasattr(func, "file") and hasattr(func.file, "file_path")
                            else "unknown"
                        )
                        func_name = func.name if hasattr(func, "name") else str(func)

                        # Add to long functions list
                        style_result["long_functions"].append({
                            "name": func_name,
                            "file": file_path,
                            "line": func.line if hasattr(func, "line") else None,
                            "line_count": len(lines),
                        })

                        # Add issue
                        self.add_issue(
                            Issue(
                                file=file_path,
                                line=func.line if hasattr(func, "line") else None,
                                message=f"Long function: {len(lines)} lines",
                                severity=IssueSeverity.INFO,
                                category=IssueCategory.STYLE_ISSUE,
                                symbol=func_name,
                                suggestion="Consider breaking this function into smaller, more focused functions",
                            )
                        )

        # Update summary
        style_result["summary"]["long_functions_count"] = len(
            style_result["long_functions"]
        )
        style_result["summary"]["long_lines_count"] = len(style_result["long_lines"])
        style_result["summary"]["inconsistent_naming_count"] = len(
            style_result["inconsistent_naming"]
        )

        return style_result

    def _calculate_maintainability(self) -> dict[str, Any]:
        """Calculate maintainability metrics."""
        import math

        codebase = self.analyzer.base_codebase

        maintainability_result = {
            "function_maintainability": [],
            "low_maintainability_functions": [],
            "average_maintainability": 0.0,
            "maintainability_distribution": {"high": 0, "medium": 0, "low": 0},
        }

        # Process all functions to calculate maintainability
        total_maintainability = 0
        function_count = 0

        if hasattr(codebase, "functions"):
            for func in codebase.functions:
                # Skip if function should be excluded
                if self.analyzer.should_skip_symbol(func):
                    continue

                # Skip if no code block
                if not hasattr(func, "code_block"):
                    continue

                # Calculate metrics
                complexity = self._calculate_cyclomatic_complexity(func)

                # Calculate Halstead volume (approximation)
                operators = 0
                operands = 0

                if hasattr(func, "source"):
                    code = func.source
                    # Simple approximation of operators and operands
                    operators = len([c for c in code if c in "+-*/=<>!&|^~%"])
                    # Counting words as potential operands
                    import re

                    operands = len(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", code))

                halstead_volume = (
                    operators * operands * math.log2(operators + operands)
                    if operators + operands > 0
                    else 0
                )

                # Count lines of code
                loc = len(func.source.split("\n")) if hasattr(func, "source") else 0

                # Calculate maintainability index
                # Formula: 171 - 5.2 * ln(Halstead Volume) - 0.23 * (Cyclomatic Complexity) - 16.2 * ln(LOC)
                halstead_term = (
                    5.2 * math.log(max(1, halstead_volume))
                    if halstead_volume > 0
                    else 0
                )
                complexity_term = 0.23 * complexity
                loc_term = 16.2 * math.log(max(1, loc)) if loc > 0 else 0

                maintainability = 171 - halstead_term - complexity_term - loc_term

                # Normalize to 0-100 scale
                maintainability = max(0, min(100, maintainability * 100 / 171))

                # Get file path and name safely
                file_path = (
                    func.file.file_path
                    if hasattr(func, "file") and hasattr(func.file, "file_path")
                    else "unknown"
                )
                func_name = func.name if hasattr(func, "name") else str(func)

                # Add to maintainability list
                maintainability_result["function_maintainability"].append({
                    "name": func_name,
                    "file": file_path,
                    "line": func.line if hasattr(func, "line") else None,
                    "maintainability": maintainability,
                    "complexity": complexity,
                    "halstead_volume": halstead_volume,
                    "loc": loc,
                })

                # Track total maintainability
                total_maintainability += maintainability
                function_count += 1

                # Categorize maintainability
                if maintainability >= 70:
                    maintainability_result["maintainability_distribution"]["high"] += 1
                elif maintainability >= 50:
                    maintainability_result["maintainability_distribution"][
                        "medium"
                    ] += 1
                else:
                    maintainability_result["maintainability_distribution"]["low"] += 1

                    # Flag low maintainability functions
                    maintainability_result["low_maintainability_functions"].append({
                        "name": func_name,
                        "file": file_path,
                        "line": func.line if hasattr(func, "line") else None,
                        "maintainability": maintainability,
                        "complexity": complexity,
                        "halstead_volume": halstead_volume,
                        "loc": loc,
                    })

                    # Add issue
                    self.add_issue(
                        Issue(
                            file=file_path,
                            line=func.line if hasattr(func, "line") else None,
                            message=f"Low maintainability index: {maintainability:.1f}",
                            severity=IssueSeverity.WARNING,
                            category=IssueCategory.COMPLEXITY,
                            symbol=func_name,
                            suggestion="Consider refactoring this function to improve maintainability",
                        )
                    )

        # Calculate average maintainability
        maintainability_result["average_maintainability"] = (
            total_maintainability / function_count if function_count > 0 else 0.0
        )

        # Sort low maintainability functions
        maintainability_result["low_maintainability_functions"].sort(
            key=lambda x: x["maintainability"]
        )

        return maintainability_result


class DependencyAnalyzerPlugin(AnalyzerPlugin):
    """
    Plugin for dependency analysis.

    This plugin detects issues related to dependencies, including
    import relationships, circular dependencies, and module coupling.
    """

    def analyze(self) -> dict[str, Any]:
        """
        Perform dependency analysis.

        Returns:
            Dictionary containing dependency analysis results
        """
        result = {}

        # Perform dependency checks
        result["import_dependencies"] = self._analyze_import_dependencies()
        result["circular_dependencies"] = self._find_circular_dependencies()
        result["module_coupling"] = self._analyze_module_coupling()
        result["external_dependencies"] = self._analyze_external_dependencies()

        return result

    def _analyze_import_dependencies(self) -> dict[str, Any]:
        """Analyze import dependencies in the codebase."""
        codebase = self.analyzer.base_codebase

        import_deps = {
            "module_dependencies": [],
            "file_dependencies": [],
            "most_imported_modules": [],
            "most_importing_modules": [],
            "dependency_stats": {
                "total_imports": 0,
                "internal_imports": 0,
                "external_imports": 0,
                "relative_imports": 0,
            },
        }

        # Create a directed graph for module dependencies
        G = nx.DiGraph()

        # Track import counts
        module_imports = {}  # modules importing others
        module_imported = {}  # modules being imported

        # Process all files to extract import information
        for file in codebase.files:
            # Skip if no imports
            if not hasattr(file, "imports") or not file.imports:
                continue

            # Skip if file should be excluded
            if self.analyzer.should_skip_file(file):
                continue

            # Get file path
            file_path = (
                file.file_path
                if hasattr(file, "file_path")
                else str(file.path)
                if hasattr(file, "path")
                else str(file)
            )

            # Extract module name from file path
            file_parts = file_path.split("/")
            module_name = (
                "/".join(file_parts[:-1]) if len(file_parts) > 1 else file_parts[0]
            )

            # Initialize import counts
            if module_name not in module_imports:
                module_imports[module_name] = 0

            # Process imports
            for imp in file.imports:
                import_deps["dependency_stats"]["total_imports"] += 1

                # Get imported module information
                imported_file = None
                imported_module = "unknown"
                is_external = False

                if hasattr(imp, "resolved_file"):
                    imported_file = imp.resolved_file
                elif hasattr(imp, "resolved_symbol") and hasattr(
                    imp.resolved_symbol, "file"
                ):
                    imported_file = imp.resolved_symbol.file

                if imported_file:
                    # Get imported file path
                    imported_path = (
                        imported_file.file_path
                        if hasattr(imported_file, "file_path")
                        else str(imported_file.path)
                        if hasattr(imported_file, "path")
                        else str(imported_file)
                    )

                    # Extract imported module name
                    imported_parts = imported_path.split("/")
                    imported_module = (
                        "/".join(imported_parts[:-1])
                        if len(imported_parts) > 1
                        else imported_parts[0]
                    )

                    # Check if external
                    is_external = (
                        hasattr(imported_file, "is_external")
                        and imported_file.is_external
                    )
                else:
                    # If we couldn't resolve the import, use the import name
                    imported_module = imp.name if hasattr(imp, "name") else "unknown"

                    # Assume external if we couldn't resolve
                    is_external = True

                # Update import type counts
                if is_external:
                    import_deps["dependency_stats"]["external_imports"] += 1
                else:
                    import_deps["dependency_stats"]["internal_imports"] += 1

                    # Check if relative import
                    if hasattr(imp, "is_relative") and imp.is_relative:
                        import_deps["dependency_stats"]["relative_imports"] += 1

                # Update module import counts
                module_imports[module_name] += 1

                if imported_module not in module_imported:
                    module_imported[imported_module] = 0
                module_imported[imported_module] += 1

                # Add to dependency graph
                if module_name != imported_module:  # Skip self-imports
                    G.add_edge(module_name, imported_module)

                    # Add to file dependencies list
                    import_deps["file_dependencies"].append({
                        "source_file": file_path,
                        "target_file": imported_path if imported_file else "unknown",
                        "import_name": imp.name if hasattr(imp, "name") else "unknown",
                        "is_external": is_external,
                    })

        # Extract module dependencies from graph
        for source, target in G.edges():
            import_deps["module_dependencies"].append({
                "source_module": source,
                "target_module": target,
            })

        # Find most imported modules
        most_imported = sorted(
            module_imported.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        for module, count in most_imported[:10]:  # Top 10
            import_deps["most_imported_modules"].append({
                "module": module,
                "import_count": count,
            })

        # Find modules that import the most
        most_importing = sorted(
            module_imports.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        for module, count in most_importing[:10]:  # Top 10
            import_deps["most_importing_modules"].append({
                "module": module,
                "import_count": count,
            })

        return import_deps

    def _find_circular_dependencies(self) -> dict[str, Any]:
        """Find circular dependencies in the codebase."""
        codebase = self.analyzer.base_codebase

        circular_deps = {
            "circular_imports": [],
            "circular_dependencies_count": 0,
            "affected_modules": set(),
        }

        # Create dependency graph if not already available
        G = nx.DiGraph()

        # Process all files to build dependency graph
        for file in codebase.files:
            # Skip if no imports
            if not hasattr(file, "imports") or not file.imports:
                continue

            # Skip if file should be excluded
            if self.analyzer.should_skip_file(file):
                continue

            # Get file path
            file_path = (
                file.file_path
                if hasattr(file, "file_path")
                else str(file.path)
                if hasattr(file, "path")
                else str(file)
            )

            # Process imports
            for imp in file.imports:
                # Get imported file
                imported_file = None

                if hasattr(imp, "resolved_file"):
                    imported_file = imp.resolved_file
                elif hasattr(imp, "resolved_symbol") and hasattr(
                    imp.resolved_symbol, "file"
                ):
                    imported_file = imp.resolved_symbol.file

                if imported_file:
                    # Get imported file path
                    imported_path = (
                        imported_file.file_path
                        if hasattr(imported_file, "file_path")
                        else str(imported_file.path)
                        if hasattr(imported_file, "path")
                        else str(imported_file)
                    )

                    # Add edge to graph
                    G.add_edge(file_path, imported_path)

        # Find cycles in the graph
        try:
            cycles = list(nx.simple_cycles(G))

            for cycle in cycles:
                circular_deps["circular_imports"].append({
                    "files": cycle,
                    "length": len(cycle),
                })

                # Add affected modules to set
                for file_path in cycle:
                    module_path = "/".join(file_path.split("/")[:-1])
                    circular_deps["affected_modules"].add(module_path)

                # Add issue
                if len(cycle) >= 2:
                    self.add_issue(
                        Issue(
                            file=cycle[0],
                            line=None,
                            message=f"Circular dependency detected between {len(cycle)} files",
                            severity=IssueSeverity.ERROR,
                            category=IssueCategory.DEPENDENCY_CYCLE,
                            suggestion="Break the circular dependency by refactoring the code",
                        )
                    )

        except Exception as e:
            logger.exception(f"Error finding circular dependencies: {e}")

        # Update cycle count
        circular_deps["circular_dependencies_count"] = len(
            circular_deps["circular_imports"]
        )
        circular_deps["affected_modules"] = list(circular_deps["affected_modules"])

        return circular_deps

    def _analyze_module_coupling(self) -> dict[str, Any]:
        """Analyze module coupling in the codebase."""
        codebase = self.analyzer.base_codebase

        coupling = {
            "high_coupling_modules": [],
            "low_coupling_modules": [],
            "coupling_metrics": {},
            "average_coupling": 0.0,
        }

        # Create module dependency graphs
        modules = {}  # Module name -> set of imported modules
        module_files = {}  # Module name -> list of files

        # Process all files to extract module information
        for file in codebase.files:
            # Skip if file should be excluded
            if self.analyzer.should_skip_file(file):
                continue

            # Get file path
            file_path = (
                file.file_path
                if hasattr(file, "file_path")
                else str(file.path)
                if hasattr(file, "path")
                else str(file)
            )

            # Extract module name from file path
            module_parts = file_path.split("/")
            module_name = (
                "/".join(module_parts[:-1])
                if len(module_parts) > 1
                else module_parts[0]
            )

            # Initialize module structures
            if module_name not in modules:
                modules[module_name] = set()
                module_files[module_name] = []

            module_files[module_name].append(file_path)

            # Skip if no imports
            if not hasattr(file, "imports") or not file.imports:
                continue

            # Process imports
            for imp in file.imports:
                # Get imported file
                imported_file = None

                if hasattr(imp, "resolved_file"):
                    imported_file = imp.resolved_file
                elif hasattr(imp, "resolved_symbol") and hasattr(
                    imp.resolved_symbol, "file"
                ):
                    imported_file = imp.resolved_symbol.file

                if imported_file:
                    # Get imported file path
                    imported_path = (
                        imported_file.file_path
                        if hasattr(imported_file, "file_path")
                        else str(imported_file.path)
                        if hasattr(imported_file, "path")
                        else str(imported_file)
                    )

                    # Extract imported module name
                    imported_parts = imported_path.split("/")
                    imported_module = (
                        "/".join(imported_parts[:-1])
                        if len(imported_parts) > 1
                        else imported_parts[0]
                    )

                    # Skip self-imports
                    if imported_module != module_name:
                        modules[module_name].add(imported_module)

        # Calculate coupling metrics for each module
        total_coupling = 0.0
        module_count = 0

        for module_name, imported_modules in modules.items():
            # Calculate metrics
            file_count = len(module_files[module_name])
            import_count = len(imported_modules)

            # Calculate coupling ratio (imports per file)
            coupling_ratio = import_count / file_count if file_count > 0 else 0

            # Add to metrics
            coupling["coupling_metrics"][module_name] = {
                "files": file_count,
                "imported_modules": list(imported_modules),
                "import_count": import_count,
                "coupling_ratio": coupling_ratio,
            }

            # Track total for average
            total_coupling += coupling_ratio
            module_count += 1

            # Categorize coupling
            if coupling_ratio > 3:  # Threshold for "high coupling"
                coupling["high_coupling_modules"].append({
                    "module": module_name,
                    "coupling_ratio": coupling_ratio,
                    "import_count": import_count,
                    "file_count": file_count,
                })

                # Add issue
                self.add_issue(
                    Issue(
                        file=module_files[module_name][0]
                        if module_files[module_name]
                        else module_name,
                        line=None,
                        message=f"High module coupling: {coupling_ratio:.2f} imports per file",
                        severity=IssueSeverity.WARNING,
                        category=IssueCategory.DEPENDENCY_CYCLE,
                        suggestion="Consider refactoring to reduce coupling between modules",
                    )
                )
            elif (
                coupling_ratio < 0.5 and file_count > 1
            ):  # Threshold for "low coupling"
                coupling["low_coupling_modules"].append({
                    "module": module_name,
                    "coupling_ratio": coupling_ratio,
                    "import_count": import_count,
                    "file_count": file_count,
                })

        # Calculate average coupling
        coupling["average_coupling"] = (
            total_coupling / module_count if module_count > 0 else 0.0
        )

        # Sort coupling lists
        coupling["high_coupling_modules"].sort(
            key=lambda x: x["coupling_ratio"], reverse=True
        )
        coupling["low_coupling_modules"].sort(key=lambda x: x["coupling_ratio"])

        return coupling

    def _analyze_external_dependencies(self) -> dict[str, Any]:
        """Analyze external dependencies in the codebase."""
        codebase = self.analyzer.base_codebase

        external_deps = {
            "external_modules": [],
            "external_module_usage": {},
            "most_used_external_modules": [],
        }

        # Track external module usage
        external_usage = {}  # Module name -> usage count

        # Process all imports to find external dependencies
        for file in codebase.files:
            # Skip if no imports
            if not hasattr(file, "imports") or not file.imports:
                continue

            # Skip if file should be excluded
            if self.analyzer.should_skip_file(file):
                continue

            # Process imports
            for imp in file.imports:
                # Check if external import
                is_external = False
                external_name = None

                if hasattr(imp, "module_name"):
                    external_name = imp.module_name

                    # Check if this is an external module
                    if hasattr(imp, "is_external"):
                        is_external = imp.is_external
                    elif (
                        external_name
                        and "." not in external_name
                        and "/" not in external_name
                    ):
                        # Simple heuristic: single-word module names without dots or slashes
                        # are likely external modules
                        is_external = True

                if is_external and external_name:
                    # Add to external modules list if not already there
                    if external_name not in external_usage:
                        external_usage[external_name] = 0
                        external_deps["external_modules"].append(external_name)

                    external_usage[external_name] += 1

        # Add usage counts
        for module, count in external_usage.items():
            external_deps["external_module_usage"][module] = count

        # Find most used external modules
        most_used = sorted(
            external_usage.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        for module, count in most_used[:10]:  # Top 10
            external_deps["most_used_external_modules"].append({
                "module": module,
                "usage_count": count,
            })

        return external_deps


class UnifiedCodeAnalyzer:
    """
    Unified Codebase Analyzer.

    This class provides a comprehensive framework for analyzing codebases,
    with support for pluggable analyzers for different types of analysis.
    """

    def __init__(
        self,
        repo_url: str | None = None,
        repo_path: str | None = None,
        base_branch: str = "main",
        pr_number: int | None = None,
        language: str | None = None,
        file_ignore_list: list[str] | None = None,
        config: dict[str, Any] | None = None,
    ):
        """
        Initialize the unified analyzer.

        Args:
            repo_url: URL of the repository to analyze
            repo_path: Local path to the repository to analyze
            base_branch: Base branch for comparison
            pr_number: PR number to analyze
            language: Programming language of the codebase
            file_ignore_list: List of file patterns to ignore
            config: Additional configuration options
        """
        self.repo_url = repo_url
        self.repo_path = repo_path
        self.base_branch = base_branch
        self.pr_number = pr_number
        self.language = language

        # Use custom ignore list or default global list
        self.file_ignore_list = file_ignore_list or GLOBAL_FILE_IGNORE_LIST

        # Configuration options
        self.config = config or {}

        # Codebase and context objects
        self.base_codebase = None
        self.pr_codebase = None
        self.base_context = None
        self.pr_context = None

        # Analysis results
        self.issues = []
        self.results = {}

        # PR comparison data
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

        # Initialize contexts
        self._init_contexts()

        # Initialize analyzers
        self._init_analyzers()

    def _init_from_url(self, repo_url: str, language: str | None = None):
        """
        Initialize codebase from a repository URL.

        Args:
            repo_url: URL of the repository
            language: Programming language of the codebase
        """
        try:
            # Extract repository information
            if repo_url.endswith(".git"):
                repo_url = repo_url[:-4]

            parts = repo_url.rstrip("/").split("/")
            repo_name = parts[-1]
            owner = parts[-2]
            repo_full_name = f"{owner}/{repo_name}"

            # Create temporary directory for cloning
            tmp_dir = tempfile.mkdtemp(prefix="analyzer_")

            # Set up configuration
            config = CodebaseConfig(
                debug=False,
                allow_external=True,
                py_resolve_syspath=True,
            )

            secrets = SecretsConfig()

            # Determine programming language
            prog_lang = None
            if language:
                prog_lang = ProgrammingLanguage(language.upper())

            # Initialize the codebase
            logger.info(f"Initializing codebase from {repo_url}")

            self.base_codebase = Codebase.from_github(
                repo_full_name=repo_full_name,
                tmp_dir=tmp_dir,
                language=prog_lang,
                config=config,
                secrets=secrets,
            )

            logger.info(f"Successfully initialized codebase from {repo_url}")

        except Exception as e:
            logger.exception(f"Error initializing codebase from URL: {e}")
            raise

    def _init_from_path(self, repo_path: str, language: str | None = None):
        """
        Initialize codebase from a local repository path.

        Args:
            repo_path: Path to the repository
            language: Programming language of the codebase
        """
        try:
            # Set up configuration
            config = CodebaseConfig(
                debug=False,
                allow_external=True,
                py_resolve_syspath=True,
            )

            secrets = SecretsConfig()

            # Initialize the codebase
            logger.info(f"Initializing codebase from {repo_path}")

            # Determine programming language
            prog_lang = None
            if language:
                prog_lang = ProgrammingLanguage(language.upper())

            # Set up repository configuration
            repo_config = RepoConfig.from_repo_path(repo_path)
            repo_config.respect_gitignore = False
            repo_operator = RepoOperator(repo_config=repo_config, bot_commit=False)

            # Create project configuration
            project_config = ProjectConfig(
                repo_operator=repo_operator,
                programming_language=prog_lang if prog_lang else None,
            )

            # Initialize codebase
            self.base_codebase = Codebase(
                projects=[project_config], config=config, secrets=secrets
            )

            logger.info(f"Successfully initialized codebase from {repo_path}")

        except Exception as e:
            logger.exception(f"Error initializing codebase from path: {e}")
            raise

    def _init_pr_data(self, pr_number: int):
        """
        Initialize PR-specific data.

        Args:
            pr_number: PR number to analyze
        """
        try:
            logger.info(f"Fetching PR #{pr_number} data")
            result = self.base_codebase.get_modified_symbols_in_pr(pr_number)

            # Unpack the result tuple
            if len(result) >= 3:
                self.pr_diff, self.commit_shas, self.modified_symbols = result[:3]
                if len(result) >= 4:
                    self.pr_branch = result[3]

            logger.info(f"Found {len(self.modified_symbols)} modified symbols in PR")

            # Initialize PR codebase
            self._init_pr_codebase()

        except Exception as e:
            logger.exception(f"Error initializing PR data: {e}")
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
            logger.exception(f"Error initializing PR codebase: {e}")
            raise

    def _init_contexts(self):
        """Initialize CodebaseContext objects for both base and PR codebases."""
        if self.base_codebase:
            try:
                self.base_context = CodebaseContext(
                    codebase=self.base_codebase,
                    base_path=self.repo_path,
                    pr_branch=None,
                    base_branch=self.base_branch,
                )
                logger.info("Successfully initialized base context")
            except Exception as e:
                logger.exception(f"Error initializing base context: {e}")

        if self.pr_codebase:
            try:
                self.pr_context = CodebaseContext(
                    codebase=self.pr_codebase,
                    base_path=self.repo_path,
                    pr_branch=self.pr_branch,
                    base_branch=self.base_branch,
                )
                logger.info("Successfully initialized PR context")
            except Exception as e:
                logger.exception(f"Error initializing PR context: {e}")

    def _init_analyzers(self):
        """Initialize analyzer plugins."""
        # Register default analyzers
        registry = AnalyzerRegistry()
        registry.register(AnalysisType.CODE_QUALITY, CodeQualityAnalyzerPlugin)
        registry.register(AnalysisType.DEPENDENCY, DependencyAnalyzerPlugin)

    def add_issue(self, issue: Issue):
        """
        Add an issue to the list of detected issues.

        Args:
            issue: Issue to add
        """
        # Check if issue should be skipped
        if self.should_skip_issue(issue):
            return

        self.issues.append(issue)

    def should_skip_issue(self, issue: Issue) -> bool:
        """
        Check if an issue should be skipped based on file patterns.

        Args:
            issue: Issue to check

        Returns:
            True if the issue should be skipped, False otherwise
        """
        # Skip issues in ignored files
        file_path = issue.file

        # Check against ignore list
        for pattern in self.file_ignore_list:
            if pattern in file_path:
                return True

        # Check if the file is a test file
        if "test" in file_path.lower() or "tests" in file_path.lower():
            # Skip low-severity issues in test files
            if issue.severity in [IssueSeverity.INFO, IssueSeverity.WARNING]:
                return True

        return False

    def should_skip_file(self, file) -> bool:
        """
        Check if a file should be skipped during analysis.

        Args:
            file: File to check

        Returns:
            True if the file should be skipped, False otherwise
        """
        # Skip binary files
        if hasattr(file, "is_binary") and file.is_binary:
            return True

        # Get file path
        file_path = (
            file.file_path
            if hasattr(file, "file_path")
            else str(file.path)
            if hasattr(file, "path")
            else str(file)
        )

        # Check against ignore list
        return any(pattern in file_path for pattern in self.file_ignore_list)

    def should_skip_symbol(self, symbol) -> bool:
        """
        Check if a symbol should be skipped during analysis.

        Args:
            symbol: Symbol to check

        Returns:
            True if the symbol should be skipped, False otherwise
        """
        # Skip symbols without a file
        if not hasattr(symbol, "file"):
            return True

        # Skip symbols in skipped files
        return self.should_skip_file(symbol.file)

    def get_issues(
        self,
        severity: IssueSeverity | None = None,
        category: IssueCategory | None = None,
    ) -> list[Issue]:
        """
        Get all issues matching the specified criteria.

        Args:
            severity: Optional severity level to filter by
            category: Optional category to filter by

        Returns:
            List of matching issues
        """
        filtered_issues = self.issues

        if severity:
            filtered_issues = [i for i in filtered_issues if i.severity == severity]

        if category:
            filtered_issues = [i for i in filtered_issues if i.category == category]

        return filtered_issues

    def analyze(
        self, analysis_types: list[AnalysisType] | None = None
    ) -> dict[str, Any]:
        """
        Perform analysis on the codebase.

        Args:
            analysis_types: List of analysis types to perform. If None, performs CODE_QUALITY and DEPENDENCY analysis.

        Returns:
            Dictionary containing analysis results
        """
        if not self.base_codebase:
            raise ValueError("Codebase not initialized")

        # Default to code quality and dependency analysis
        if analysis_types is None:
            analysis_types = [AnalysisType.CODE_QUALITY, AnalysisType.DEPENDENCY]

        # Initialize results
        self.results = {
            "metadata": {
                "analysis_time": datetime.now().isoformat(),
                "analysis_types": [t.value for t in analysis_types],
                "repo_name": getattr(self.base_codebase.ctx, "repo_name", None),
                "language": str(
                    getattr(self.base_codebase.ctx, "programming_language", None)
                ),
            },
            "summary": get_codebase_summary(self.base_codebase),
            "results": {},
        }

        # Clear issues
        self.issues = []

        # Run each analyzer
        registry = AnalyzerRegistry()

        for analysis_type in analysis_types:
            analyzer_class = registry.get_analyzer(analysis_type)

            if analyzer_class:
                logger.info(f"Running {analysis_type.value} analysis")
                analyzer = analyzer_class(self)
                analysis_result = analyzer.analyze()

                # Add results to unified results
                self.results["results"][analysis_type.value] = analysis_result
            else:
                logger.warning(f"No analyzer found for {analysis_type.value}")

        # Add issues to results
        self.results["issues"] = [issue.to_dict() for issue in self.issues]

        # Add issue statistics
        self.results["issue_stats"] = {
            "total": len(self.issues),
            "by_severity": {
                "critical": sum(
                    1
                    for issue in self.issues
                    if issue.severity == IssueSeverity.CRITICAL
                ),
                "error": sum(
                    1 for issue in self.issues if issue.severity == IssueSeverity.ERROR
                ),
                "warning": sum(
                    1
                    for issue in self.issues
                    if issue.severity == IssueSeverity.WARNING
                ),
                "info": sum(
                    1 for issue in self.issues if issue.severity == IssueSeverity.INFO
                ),
            },
            "by_category": {
                category.value: sum(
                    1 for issue in self.issues if issue.category == category
                )
                for category in IssueCategory
                if any(issue.category == category for issue in self.issues)
            },
        }

        return self.results

    def save_results(self, output_file: str, format: str = "json"):
        """
        Save analysis results to a file.

        Args:
            output_file: Path to the output file
            format: Output format (json, html, or console)
        """
        if format == "json":
            with open(output_file, "w") as f:
                json.dump(self.results, f, indent=2)
        elif format == "html":
            self._generate_html_report(output_file)
        else:
            # Default to JSON
            with open(output_file, "w") as f:
                json.dump(self.results, f, indent=2)

        logger.info(f"Results saved to {output_file}")

    def _generate_html_report(self, output_file: str):
        """
        Generate an HTML report of the analysis results.

        Args:
            output_file: Path to the output file
        """
        html_content = f"""
        <!DOCTYPE html>
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
                .issue {{ margin-bottom: 10px; padding: 10px; border-radius: 5px; }}
                .critical {{ background-color: #ffcdd2; }}
                .error {{ background-color: #ffebee; }}
                .warning {{ background-color: #fff8e1; }}
                .info {{ background-color: #e8f5e9; }}
            </style>
        </head>
        <body>
            <h1>Codebase Analysis Report</h1>
            <div class="section">
                <h2>Summary</h2>
                <p>Repository: {self.results["metadata"].get("repo_name", "Unknown")}</p>
                <p>Language: {self.results["metadata"].get("language", "Unknown")}</p>
                <p>Analysis Time: {self.results["metadata"].get("analysis_time", "Unknown")}</p>
                <p>Analysis Types: {", ".join(self.results["metadata"].get("analysis_types", []))}</p>
                <p>Total Issues: {len(self.issues)}</p>
                <ul>
                    <li class="critical">Critical: {self.results["issue_stats"]["by_severity"].get("critical", 0)}</li>
                    <li class="error">Errors: {self.results["issue_stats"]["by_severity"].get("error", 0)}</li>
                    <li class="warning">Warnings: {self.results["issue_stats"]["by_severity"].get("warning", 0)}</li>
                    <li class="info">Info: {self.results["issue_stats"]["by_severity"].get("info", 0)}</li>
                </ul>
            </div>

            <div class="section">
                <h2>Issues</h2>
        """

        # Add issues grouped by severity
        for severity in [
            IssueSeverity.CRITICAL,
            IssueSeverity.ERROR,
            IssueSeverity.WARNING,
            IssueSeverity.INFO,
        ]:
            severity_issues = [
                issue for issue in self.issues if issue.severity == severity
            ]

            if severity_issues:
                html_content += f"""
                <h3>{severity.value.upper()} Issues ({len(severity_issues)})</h3>
                <div class="issues">
                """

                for issue in severity_issues:
                    location = (
                        f"{issue.file}:{issue.line}" if issue.line else issue.file
                    )
                    category = f"[{issue.category.value}]" if issue.category else ""

                    html_content += f"""
                    <div class="issue {severity.value}">
                        <p><strong>{location}</strong> {category} {issue.message}</p>
                        <p>{issue.suggestion}</p>
                    </div>
                    """

                html_content += """
                </div>
                """

        # Add detailed analysis sections
        html_content += """
            <div class="section">
                <h2>Detailed Analysis</h2>
        """

        for analysis_type, results in self.results.get("results", {}).items():
            html_content += f"""
            <h3>{analysis_type}</h3>
            <pre>{json.dumps(results, indent=2)}</pre>
            """

        html_content += """
            </div>
        </body>
        </html>
        """

        with open(output_file, "w") as f:
            f.write(html_content)


def main():
    """Command-line entry point for the unified analyzer."""
    import argparse

    parser = argparse.ArgumentParser(description="Unified Codebase Analyzer")

    # Repository source options
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--repo-url", help="URL of the repository to analyze")
    source_group.add_argument(
        "--repo-path", help="Local path to the repository to analyze"
    )

    # Analysis options
    parser.add_argument(
        "--analysis-types",
        nargs="+",
        choices=[at.value for at in AnalysisType],
        default=["code_quality", "dependency"],
        help="Types of analysis to perform",
    )
    parser.add_argument(
        "--language",
        choices=["python", "typescript"],
        help="Programming language (auto-detected if not provided)",
    )
    parser.add_argument(
        "--base-branch",
        default="main",
        help="Base branch for PR comparison (default: main)",
    )
    parser.add_argument("--pr-number", type=int, help="PR number to analyze")

    # Output options
    parser.add_argument(
        "--output-format",
        choices=["json", "html", "console"],
        default="json",
        help="Output format",
    )
    parser.add_argument("--output-file", help="Path to the output file")

    args = parser.parse_args()

    try:
        # Initialize the analyzer
        analyzer = UnifiedCodeAnalyzer(
            repo_url=args.repo_url,
            repo_path=args.repo_path,
            base_branch=args.base_branch,
            pr_number=args.pr_number,
            language=args.language,
        )

        # Perform the analysis
        analysis_types = [AnalysisType(at) for at in args.analysis_types]
        results = analyzer.analyze(analysis_types)

        # Output the results
        if args.output_format == "json":
            if args.output_file:
                analyzer.save_results(args.output_file, "json")
            else:
                print(json.dumps(results, indent=2))
        elif args.output_format == "html":
            output_file = args.output_file or "codebase_analysis_report.html"
            analyzer.save_results(output_file, "html")
        elif args.output_format == "console":
            # Print summary to console
            print("\n===== Codebase Analysis Report =====")
            print(f"Repository: {results['metadata'].get('repo_name', 'Unknown')}")
            print(f"Language: {results['metadata'].get('language', 'Unknown')}")
            print(
                f"Analysis Time: {results['metadata'].get('analysis_time', 'Unknown')}"
            )
            print(
                f"Analysis Types: {', '.join(results['metadata'].get('analysis_types', []))}"
            )

            print("\n===== Issues Summary =====")
            print(f"Total: {results['issue_stats']['total']}")
            print(
                f"Critical: {results['issue_stats']['by_severity'].get('critical', 0)}"
            )
            print(f"Errors: {results['issue_stats']['by_severity'].get('error', 0)}")
            print(
                f"Warnings: {results['issue_stats']['by_severity'].get('warning', 0)}"
            )
            print(f"Info: {results['issue_stats']['by_severity'].get('info', 0)}")

            print("\n===== Top Issues =====")
            for i, issue in enumerate(analyzer.issues[:10]):
                severity = issue.severity.value.upper()
                location = f"{issue.file}:{issue.line}" if issue.line else issue.file
                category = f"[{issue.category.value}]" if issue.category else ""
                print(f"{i + 1}. [{severity}] {location} {category} {issue.message}")
                print(f"   Suggestion: {issue.suggestion}")
                print()

    except Exception as e:
        import traceback

        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
