"""
Complexity Analysis Module for Codegen-on-OSS

This module provides functions for analyzing the complexity of code in a codebase,
including cyclomatic complexity, maintainability index, and other metrics.
"""

from typing import Dict, List, Optional, Tuple, Union

from codegen import Codebase
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.expressions.binary_expression import BinaryExpression
from codegen.sdk.core.expressions.comparison_expression import ComparisonExpression
from codegen.sdk.core.expressions.unary_expression import UnaryExpression
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.statements.for_loop_statement import ForLoopStatement
from codegen.sdk.core.statements.if_block_statement import IfBlockStatement
from codegen.sdk.core.statements.try_catch_statement import TryCatchStatement
from codegen.sdk.core.statements.while_statement import WhileStatement
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)

from functools import lru_cache

@lru_cache(maxsize=1024)
def calculate_cyclomatic_complexity(func: Function) -> int:
    """
    Calculate the cyclomatic complexity of a function.

    Args:
        func: The function to analyze

    Returns:
        The cyclomatic complexity score
    """
    # Start with complexity of 1 (one path through the function)
    complexity = 1

    # Count if statements
    if_statements = func.code_block.find_all(IfBlockStatement)
    for if_stmt in if_statements:
        # Add 1 for the if and 1 for each elif
        complexity += 1 + len(if_stmt.elif_blocks)

    # Count loops
    for_loops = func.code_block.find_all(ForLoopStatement)
    complexity += len(for_loops)

    while_loops = func.code_block.find_all(WhileStatement)
    complexity += len(while_loops)

    # Count try-except blocks
    try_blocks = func.code_block.find_all(TryCatchStatement)
    for try_block in try_blocks:
        # Add 1 for each except clause
        complexity += len(try_block.catch_blocks)

    # Count logical operators in binary expressions
    binary_expressions = func.code_block.find_all(BinaryExpression)
    for expr in binary_expressions:
        if hasattr(expr, "operators"):
            for op in expr.operators:
                if op.source in ["&&", "||", "and", "or"]:
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


def get_complexity_rank(complexity: int) -> str:
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


def analyze_file_complexity(file: SourceFile) -> Dict[str, Union[int, Dict[str, int]]]:
    """
    Analyze the complexity of a file.

    Args:
        file: The file to analyze

    Returns:
        A dictionary with complexity metrics for the file
    """
    # Initialize metrics
    metrics = {
        "cyclomatic_complexity": 0,
        "functions": {},
        "classes": {},
        "total_lines": len(file.content.splitlines()),
        "function_count": len(file.functions),
        "class_count": len(file.classes),
    }

    # Calculate complexity for each function
    max_complexity = 0
    for func in file.functions:
        complexity = calculate_cyclomatic_complexity(func)
        metrics["functions"][func.name] = complexity
        max_complexity = max(max_complexity, complexity)

    # Calculate complexity for each class
    for cls in file.classes:
        class_complexity = 0
        for method in cls.methods:
            complexity = calculate_cyclomatic_complexity(method)
            class_complexity += complexity
            metrics["functions"][f"{cls.name}.{method.name}"] = complexity
            max_complexity = max(max_complexity, complexity)
        metrics["classes"][cls.name] = class_complexity

    # Set the overall complexity to the maximum function complexity
    metrics["cyclomatic_complexity"] = max_complexity

    return metrics


def analyze_codebase_complexity(
    codebase: Codebase, file_patterns: Optional[List[str]] = None
) -> Dict[str, Union[Dict[str, Dict[str, int]], int, float]]:
    """
    Analyze the complexity of a codebase.

    Args:
        codebase: The codebase to analyze
        file_patterns: Optional list of file patterns to include

    Returns:
        A dictionary with complexity metrics for the codebase
    """
    # Initialize metrics
COMPLEXITY_RANKS = {
    'A': {'range': (1, 5), 'description': 'Excellent'},
    'B': {'range': (6, 10), 'description': 'Good'},
    'C': {'range': (11, 20), 'description': 'Moderate'},
    'D': {'range': (21, 30), 'description': 'Complex'},
    'E': {'range': (31, 40), 'description': 'Very Complex'},
    'F': {'range': (41, float('inf')), 'description': 'Unmaintainable'}
}

metrics = {
    'complexity_distribution': {rank: 0 for rank in COMPLEXITY_RANKS}
}
            "D": 0,  # 21-30
            "E": 0,  # 31-40
            "F": 0,  # 41+
        },
    }

    # Filter files if patterns are provided
    files = codebase.files
    if file_patterns:
        import re
        files = [
            file for file in files
            if any(re.search(pattern, str(file.path)) for pattern in file_patterns)
        ]

    # Analyze each file
    total_complexity = 0
    function_complexities = []

    for file in files:
        file_metrics = analyze_file_complexity(file)
        metrics["files"][str(file.path)] = file_metrics
        metrics["function_count"] += file_metrics["function_count"]
        metrics["class_count"] += file_metrics["class_count"]
        metrics["total_lines"] += file_metrics["total_lines"]

        # Track function complexities for distribution
        for func_name, complexity in file_metrics["functions"].items():
            function_complexities.append(complexity)
            rank = get_complexity_rank(complexity)
            metrics["complexity_distribution"][rank] += 1

        # Update overall complexity (maximum of all files)
        metrics["overall_complexity"] = max(
            metrics["overall_complexity"], file_metrics["cyclomatic_complexity"]
        )
        total_complexity += file_metrics["cyclomatic_complexity"]

    # Calculate average complexity
    if len(files) > 0:
        metrics["average_complexity"] = round(total_complexity / len(files), 2)

    # Calculate percentages for complexity distribution
    total_functions = len(function_complexities)
    if total_functions > 0:
        for rank in metrics["complexity_distribution"]:
            count = metrics["complexity_distribution"][rank]
            metrics["complexity_distribution"][rank] = {
                "count": count,
                "percentage": round((count / total_functions) * 100, 2),
            }

    return metrics


def identify_complex_hotspots(
    codebase: Codebase, threshold: int = 15
) -> List[Dict[str, Union[str, int]]]:
    """
    Identify complex hotspots in the codebase that may need refactoring.

    Args:
        codebase: The codebase to analyze
        threshold: Complexity threshold for identifying hotspots (default: 15)

    Returns:
        A list of hotspots with their locations and complexity scores
    """
    hotspots = []

    for file in codebase.files:
        for func in file.functions:
            complexity = calculate_cyclomatic_complexity(func)
            if complexity >= threshold:
                hotspots.append({
                    "type": "function",
                    "name": func.name,
                    "file": str(file.path),
                    "line": func.start_line,
                    "complexity": complexity,
                    "rank": get_complexity_rank(complexity),
                })

        for cls in file.classes:
            for method in cls.methods:
                complexity = calculate_cyclomatic_complexity(method)
                if complexity >= threshold:
                    hotspots.append({
                        "type": "method",
                        "name": f"{cls.name}.{method.name}",
                        "file": str(file.path),
                        "line": method.start_line,
                        "complexity": complexity,
                        "rank": get_complexity_rank(complexity),
                    })

    # Sort hotspots by complexity (descending)
    hotspots.sort(key=lambda x: x["complexity"], reverse=True)
    return hotspots
"""

