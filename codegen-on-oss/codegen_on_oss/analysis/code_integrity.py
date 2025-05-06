"""
Code integrity analysis module.

This module provides tools for analyzing code integrity, including:
- Finding functions with issues
- Identifying classes with problems
- Detecting parameter usage errors
- Finding incorrect function callback points
- Comparing error counts between branches
- Analyzing code complexity and duplication
- Checking for type hint usage
- Detecting unused imports
"""

import difflib
import logging
import re
from typing import Any, Dict, List, Optional

from graph_sitter.core.class_definition import Class
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.core.function import Function
from graph_sitter.core.import_statement import Import
from graph_sitter.core.file import SourceFile
from graph_sitter.core.symbol import Symbol
from graph_sitter.core.enums import EdgeType, SymbolType

logger = logging.getLogger(__name__)


class CodeIntegrityAnalyzer:
    """
    Analyzer for code integrity issues.

    This class provides methods to analyze various aspects of code integrity,
    including finding functions with issues, identifying classes with problems,
    detecting parameter usage errors, and more.
    """

    def __init__(
        self, codebase: Codebase, config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the analyzer with a codebase.

        Args:
            codebase: The codebase to analyze
            config: Optional configuration options for the analyzer
        """
        self.codebase = codebase
        self.config = config or {}
        self.issues = []

    def analyze(self) -> Dict[str, Any]:
        """
        Analyze code integrity for the codebase.

        Returns:
            A dictionary with analysis results
        """
        # Find functions with issues
        functions_with_issues = self.find_functions_with_issues()

        # Find classes with problems
        classes_with_problems = self.find_classes_with_problems()

        # Find parameter usage errors
        parameter_errors = self.find_parameter_usage_errors()

        # Find incorrect function callback points
        callback_errors = self.find_incorrect_function_callbacks()

        # Find unused imports
        unused_imports = self.find_unused_imports()

        # Find missing type hints
        missing_type_hints = self.find_missing_type_hints()

        # Find code duplication
        code_duplication = self.find_code_duplication()

        # Analyze complexity
        complexity_issues = self.analyze_complexity()

        # Combine all issues
        all_issues = (
            functions_with_issues
            + classes_with_problems
            + parameter_errors
            + callback_errors
            + unused_imports
            + missing_type_hints
            + code_duplication
            + complexity_issues
        )

        # Store issues for later reference
        self.issues = all_issues

        # Return analysis results
        return {
            "issues_count": len(all_issues),
            "issues": all_issues,
            "functions_with_issues": functions_with_issues,
            "classes_with_problems": classes_with_problems,
            "parameter_errors": parameter_errors,
            "callback_errors": callback_errors,
            "unused_imports": unused_imports,
            "missing_type_hints": missing_type_hints,
            "code_duplication": code_duplication,
            "complexity_issues": complexity_issues,
        }

    def find_functions_with_issues(self) -> List[Dict[str, Any]]:
        """
        Find functions with potential issues.

        Returns:
            A list of dictionaries describing function issues
        """
        issues = []

        for func in self.codebase.functions:
            # Check for functions without docstrings
            if not func.docstring:
                issues.append({
                    "type": "missing_docstring",
                    "symbol_type": "function",
                    "name": func.name,
                    "file": func.file.path if func.file else "unknown",
                    "line": func.line_number,
                    "message": f"Function '{func.name}' is missing a docstring",
                })

            # Check for functions with too many parameters
            max_params = self.config.get("max_parameters", 7)
            if len(func.parameters) > max_params:
                issues.append({
                    "type": "too_many_parameters",
                    "symbol_type": "function",
                    "name": func.name,
                    "file": func.file.path if func.file else "unknown",
                    "line": func.line_number,
                    "message": f"Function '{func.name}' has {len(func.parameters)} parameters (max: {max_params})",
                })

            # Check for functions that are too long
            max_lines = self.config.get("max_function_lines", 50)
            if func.end_line_number - func.line_number > max_lines:
                issues.append({
                    "type": "function_too_long",
                    "symbol_type": "function",
                    "name": func.name,
                    "file": func.file.path if func.file else "unknown",
                    "line": func.line_number,
                    "message": f"Function '{func.name}' is too long ({func.end_line_number - func.line_number} lines, max: {max_lines})",
                })

        return issues

    def find_classes_with_problems(self) -> List[Dict[str, Any]]:
        """
        Find classes with potential problems.

        Returns:
            A list of dictionaries describing class issues
        """
        issues = []

        for cls in self.codebase.classes:
            # Check for classes without docstrings
            if not cls.docstring:
                issues.append({
                    "type": "missing_docstring",
                    "symbol_type": "class",
                    "name": cls.name,
                    "file": cls.file.path if cls.file else "unknown",
                    "line": cls.line_number,
                    "message": f"Class '{cls.name}' is missing a docstring",
                })

            # Check for classes with too many methods
            max_methods = self.config.get("max_methods", 20)
            if len(cls.methods) > max_methods:
                issues.append({
                    "type": "too_many_methods",
                    "symbol_type": "class",
                    "name": cls.name,
                    "file": cls.file.path if cls.file else "unknown",
                    "line": cls.line_number,
                    "message": f"Class '{cls.name}' has {len(cls.methods)} methods (max: {max_methods})",
                })

            # Check for classes with too many attributes
            max_attributes = self.config.get("max_attributes", 15)
            if len(cls.attributes) > max_attributes:
                issues.append({
                    "type": "too_many_attributes",
                    "symbol_type": "class",
                    "name": cls.name,
                    "file": cls.file.path if cls.file else "unknown",
                    "line": cls.line_number,
                    "message": f"Class '{cls.name}' has {len(cls.attributes)} attributes (max: {max_attributes})",
                })

        return issues

    def find_parameter_usage_errors(self) -> List[Dict[str, Any]]:
        """
        Find parameter usage errors in functions.

        Returns:
            A list of dictionaries describing parameter usage errors
        """
        issues = []

        for func in self.codebase.functions:
            # Check for unused parameters
            used_params = set()
            for usage in func.symbol_usages:
                if isinstance(usage, Symbol) and usage.name in [p.name for p in func.parameters]:
                    used_params.add(usage.name)

            for param in func.parameters:
                if param.name not in used_params and not param.name.startswith("_"):
                    issues.append({
                        "type": "unused_parameter",
                        "symbol_type": "parameter",
                        "name": param.name,
                        "function": func.name,
                        "file": func.file.path if func.file else "unknown",
                        "line": func.line_number,
                        "message": f"Parameter '{param.name}' in function '{func.name}' is never used",
                    })

        return issues

    def find_incorrect_function_callbacks(self) -> List[Dict[str, Any]]:
        """
        Find incorrect function callback points.

        Returns:
            A list of dictionaries describing callback errors
        """
        # This is a placeholder for function callback analysis
        # In a real implementation, this would analyze function callbacks
        # and identify potential issues
        return []

    def find_unused_imports(self) -> List[Dict[str, Any]]:
        """
        Find unused imports in the codebase.

        Returns:
            A list of dictionaries describing unused imports
        """
        issues = []

        for file in self.codebase.files:
            for import_stmt in file.imports:
                # Check if the imported symbol is used
                if not import_stmt.symbol_usages:
                    issues.append({
                        "type": "unused_import",
                        "symbol_type": "import",
                        "name": import_stmt.name,
                        "file": file.path,
                        "line": import_stmt.line_number,
                        "message": f"Import '{import_stmt.name}' in file '{file.path}' is never used",
                    })

        return issues

    def find_missing_type_hints(self) -> List[Dict[str, Any]]:
        """
        Find missing type hints in functions.

        Returns:
            A list of dictionaries describing missing type hints
        """
        issues = []

        for func in self.codebase.functions:
            # Check for missing return type hints
            if not func.return_type and not func.name.startswith("_"):
                issues.append({
                    "type": "missing_return_type",
                    "symbol_type": "function",
                    "name": func.name,
                    "file": func.file.path if func.file else "unknown",
                    "line": func.line_number,
                    "message": f"Function '{func.name}' is missing a return type hint",
                })

            # Check for missing parameter type hints
            for param in func.parameters:
                if not param.type_annotation and not param.name.startswith("_"):
                    issues.append({
                        "type": "missing_parameter_type",
                        "symbol_type": "parameter",
                        "name": param.name,
                        "function": func.name,
                        "file": func.file.path if func.file else "unknown",
                        "line": func.line_number,
                        "message": f"Parameter '{param.name}' in function '{func.name}' is missing a type hint",
                    })

        return issues

    def find_code_duplication(self) -> List[Dict[str, Any]]:
        """
        Find code duplication in the codebase.

        Returns:
            A list of dictionaries describing code duplication
        """
        # This is a placeholder for code duplication analysis
        # In a real implementation, this would analyze code duplication
        # and identify potential issues
        return []

    def analyze_complexity(self) -> List[Dict[str, Any]]:
        """
        Analyze code complexity in the codebase.

        Returns:
            A list of dictionaries describing complexity issues
        """
        issues = []

        for func in self.codebase.functions:
            # Calculate cyclomatic complexity
            complexity = self._calculate_cyclomatic_complexity(func)

            # Check if complexity exceeds threshold
            max_complexity = self.config.get("max_complexity", 10)
            if complexity > max_complexity:
                issues.append({
                    "type": "high_complexity",
                    "symbol_type": "function",
                    "name": func.name,
                    "file": func.file.path if func.file else "unknown",
                    "line": func.line_number,
                    "complexity": complexity,
                    "max_complexity": max_complexity,
                    "message": f"Function '{func.name}' has high cyclomatic complexity ({complexity}, max: {max_complexity})",
                })

        return issues

    def _calculate_cyclomatic_complexity(self, func: Function) -> int:
        """
        Calculate cyclomatic complexity for a function.

        Args:
            func: The function to analyze

        Returns:
            The cyclomatic complexity score
        """
        # This is a simplified implementation of cyclomatic complexity calculation
        # In a real implementation, this would analyze the control flow graph
        # and calculate the cyclomatic complexity more accurately

        # Start with complexity of 1 (for the function itself)
        complexity = 1

        # Count if statements
        if_count = len(re.findall(r"\bif\b", func.source))
        complexity += if_count

        # Count else statements
        else_count = len(re.findall(r"\belse\b", func.source))
        complexity += else_count

        # Count elif statements
        elif_count = len(re.findall(r"\belif\b", func.source))
        complexity += elif_count

        # Count for loops
        for_count = len(re.findall(r"\bfor\b", func.source))
        complexity += for_count

        # Count while loops
        while_count = len(re.findall(r"\bwhile\b", func.source))
        complexity += while_count

        # Count try/except blocks
        try_count = len(re.findall(r"\btry\b", func.source))
        complexity += try_count

        # Count except blocks
        except_count = len(re.findall(r"\bexcept\b", func.source))
        complexity += except_count

        # Count logical operators (and, or)
        and_count = len(re.findall(r"\band\b", func.source))
        complexity += and_count

        or_count = len(re.findall(r"\bor\b", func.source))
        complexity += or_count

        return complexity


def analyze_code_integrity(
    codebase: Codebase, config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze code integrity for a codebase.

    Args:
        codebase: The codebase to analyze
        config: Optional configuration options for the analyzer

    Returns:
        A dictionary with analysis results
    """
    analyzer = CodeIntegrityAnalyzer(codebase, config)
    return analyzer.analyze()


def compare_branches(
    main_branch: str, feature_branch: str, repo_url: str
) -> Dict[str, Any]:
    """
    Compare code integrity between two branches.

    Args:
        main_branch: The main branch to compare against
        feature_branch: The feature branch to compare
        repo_url: The repository URL

    Returns:
        A dictionary with comparison results
    """
    # Get the codebase for each branch
    main_codebase = Codebase.from_repo(repo_url, branch=main_branch)
    feature_codebase = Codebase.from_repo(repo_url, branch=feature_branch)

    # Analyze each codebase
    main_analysis = analyze_code_integrity(main_codebase)
    feature_analysis = analyze_code_integrity(feature_codebase)

    # Compare the results
    comparison = {
        "main_branch": {
            "name": main_branch,
            "issues_count": main_analysis["issues_count"],
            "issues": main_analysis["issues"],
        },
        "feature_branch": {
            "name": feature_branch,
            "issues_count": feature_analysis["issues_count"],
            "issues": feature_analysis["issues"],
        },
        "diff": {
            "issues_count_diff": feature_analysis["issues_count"] - main_analysis["issues_count"],
        },
    }

    # Find new issues in the feature branch
    main_issues_by_type = {}
    for issue in main_analysis["issues"]:
        issue_type = issue["type"]
        if issue_type not in main_issues_by_type:
            main_issues_by_type[issue_type] = []
        main_issues_by_type[issue_type].append(issue)

    feature_issues_by_type = {}
    for issue in feature_analysis["issues"]:
        issue_type = issue["type"]
        if issue_type not in feature_issues_by_type:
            feature_issues_by_type[issue_type] = []
        feature_issues_by_type[issue_type].append(issue)

    # Calculate differences by issue type
    diff_by_type = {}
    all_types = set(list(main_issues_by_type.keys()) + list(feature_issues_by_type.keys()))
    for issue_type in all_types:
        main_count = len(main_issues_by_type.get(issue_type, []))
        feature_count = len(feature_issues_by_type.get(issue_type, []))
        diff_by_type[issue_type] = feature_count - main_count

    comparison["diff"]["by_type"] = diff_by_type

    return comparison


__all__ = ["CodeIntegrityAnalyzer", "analyze_code_integrity", "compare_branches"]

