"""
Unified Analysis Module for Codegen-on-OSS

This module serves as a central hub for all code analysis functionality, integrating
various specialized analysis components into a cohesive system.
"""

import difflib
import math
import os
import re
import subprocess
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
import uvicorn
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.class_definition import Class
from graph_sitter.core.expressions.binary_expression import BinaryExpression
from graph_sitter.core.expressions.comparison_expression import ComparisonExpression
from graph_sitter.core.expressions.unary_expression import UnaryExpression
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.core.file import SourceFile
from graph_sitter.core.function import Function
from graph_sitter.core.statements.for_loop_statement import ForLoopStatement
from graph_sitter.core.statements.if_block_statement import IfBlockStatement
from graph_sitter.core.statements.try_catch_statement import TryCatchStatement
from graph_sitter.core.statements.while_statement import WhileStatement
from graph_sitter.core.symbol import Symbol
from fastapi import FastAPI
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
        This is called automatically when needed but can be called explicitly for eager
        initialization.
        """
        if self._initialized:
            return

        # Initialize context if not already done
        if self._context is None:
            self._context = self._create_context()

        self._initialized = True

    def _create_context(self):
        """
        Create a context for the current codebase.

        Returns:
            A new context instance
        """
        # This is a placeholder for actual context creation
        return {"codebase": self.codebase}

    @property
    def context(self):
        """
        Get the context for the current codebase.

        Returns:
            A context object for the codebase
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

    def get_monthly_commit_activity(self) -> Dict[str, Any]:
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


def get_monthly_commits(repo_path: str) -> Dict[str, Any]:
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
    Get the operators and operands from a function's source code.

    Args:
        function: The function to analyze

    Returns:
        A tuple of (operators, operands)
    """
    # This is a simplified implementation
    # In a real implementation, you would parse the source code and extract operators and operands
    if not function.source:
        return [], []

    # Define operators
    operators = [
        "+", "-", "*", "/", "%", "=", "==", "!=", "<", ">", "<=", ">=",
        "&&", "||", "!", "++", "--", "+=", "-=", "*=", "/=", "%=",
        ".", "->", "::", "?", ":", "<<", ">>", "&", "|", "^", "~",
        "if", "else", "for", "while", "do", "switch", "case", "break",
        "continue", "return", "throw", "try", "catch", "finally"
    ]

    # Count operators
    operator_counts = {}
    for op in operators:
        count = function.source.count(op)
        if count > 0:
            operator_counts[op] = count

    # Extract identifiers and literals as operands
    # This is a simplified approach
    words = re.findall(r'\b[a-zA-Z_]\w*\b', function.source)
    operand_counts = {}
    for word in words:
        if word not in operators:
            operand_counts[word] = operand_counts.get(word, 0) + 1

    return operator_counts, operand_counts


def calculate_halstead_metrics(function):
    """
    Calculate Halstead complexity metrics for a function.

    Args:
        function: The function to analyze

    Returns:
        A dictionary with Halstead metrics
    """
    operator_counts, operand_counts = get_operators_and_operands(function)

    # Count unique operators and operands
    n1 = len(operator_counts)  # Number of unique operators
    n2 = len(operand_counts)   # Number of unique operands

    # Count total operators and operands
    N1 = sum(operator_counts.values())  # Total number of operators
    N2 = sum(operand_counts.values())   # Total number of operands

    # Calculate Halstead metrics
    if n1 > 0 and n2 > 0:
        vocabulary = n1 + n2
        length = N1 + N2
        volume = length * math.log2(vocabulary) if vocabulary > 0 else 0
        difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
        effort = difficulty * volume
        time = effort / 18  # Time in seconds (18 is a constant from Halstead's research)
        bugs = volume / 3000  # Estimated number of bugs (3000 is a constant from Halstead's research)

        return {
            "vocabulary": vocabulary,
            "length": length,
            "volume": volume,
            "difficulty": difficulty,
            "effort": effort,
            "time": time,
            "bugs": bugs,
        }
    else:
        return {
            "vocabulary": 0,
            "length": 0,
            "volume": 0,
            "difficulty": 0,
            "effort": 0,
            "time": 0,
            "bugs": 0,
        }
