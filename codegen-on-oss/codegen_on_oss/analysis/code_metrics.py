"""
Code Metrics Module for Codegen-on-OSS

This module provides functions for calculating various code metrics,
including cyclomatic complexity, maintainability index, and Halstead metrics.
"""

import ast
import math
import re
from typing import Any, Dict, List, Optional

from radon.complexity import cc_visit
from radon.metrics import h_visit

# Constants for maintainability index calculation
MI_PARAMETERS = (50, 14, 8)  # weight factors for the maintainability index


def calculate_cyclomatic_complexity(code: str) -> int:
    """
    Calculate the cyclomatic complexity of a code snippet.

    Args:
        code: The code to analyze

    Returns:
        The cyclomatic complexity score
    """
    try:
        results = cc_visit(code)
        if not results:
            return 1  # Default complexity for empty code
        # Return the maximum complexity of all functions/classes
        return max(item.complexity for item in results)
    except Exception:
        # If parsing fails, return a default value
        return 1


def calculate_maintainability_index(code: str) -> float:
    """
    Calculate the maintainability index for a code snippet.

    Args:
        code: The code to analyze

    Returns:
        The maintainability index (0-100)
    """
    try:
        # Calculate Halstead volume
        h_stats = h_visit(code)
        if h_stats.total.N == 0:
            return 100  # Default for empty code
        # Calculate cyclomatic complexity
        complexity = calculate_cyclomatic_complexity(code)
        # Calculate lines of code
        loc = len(code.splitlines())
        # Calculate maintainability index using radon's formula
        halstead_volume = h_stats.total.volume
        # Avoid log of zero or negative values
        if halstead_volume <= 0:
            halstead_volume = 1
        if loc <= 0:
            loc = 1
        # Calculate raw maintainability index
        raw_mi = (
            MI_PARAMETERS[0] * math.log(halstead_volume) +
            MI_PARAMETERS[1] * math.log(complexity) +
            MI_PARAMETERS[2] * math.log(loc)
        )
        # Scale to 0-100
        mi = max(0, 100 - raw_mi / 171 * 100)
        return round(mi, 2)
    except Exception:
        # If calculation fails, return a default value
        return 50.0


def calculate_halstead_metrics(code: str) -> Dict[str, float]:
    """
    Calculate Halstead complexity metrics for a code snippet.

    Args:
        code: The code to analyze

    Returns:
        Dictionary containing Halstead metrics
    """
    try:
        h_stats = h_visit(code)
        # Extract metrics from h_stats
        return {
            "h1": h_stats.total.h1,  # Number of distinct operators
            "h2": h_stats.total.h2,  # Number of distinct operands
            "N1": h_stats.total.N1,  # Total operators
            "N2": h_stats.total.N2,  # Total operands
            "vocabulary": h_stats.total.vocabulary,  # Program vocabulary
            "length": h_stats.total.length,  # Program length
            "volume": h_stats.total.volume,  # Program volume
            "difficulty": h_stats.total.difficulty,  # Program difficulty
            "effort": h_stats.total.effort,  # Programming effort
            "time": h_stats.total.time,  # Time to program
            "bugs": h_stats.total.bugs,  # Estimated bugs
        }
    except Exception:
        # If calculation fails, return default values
        return {
            "h1": 0, "h2": 0, "N1": 0, "N2": 0,
            "vocabulary": 0, "length": 0, "volume": 0,
            "difficulty": 0, "effort": 0, "time": 0, "bugs": 0
        }


def calculate_line_metrics(code: str) -> Dict[str, int]:
    """
    Calculate line-based metrics for code.

    Args:
        code: The code to analyze

    Returns:
        Dictionary with line metrics
    """
    lines = code.splitlines()
    # Count different types of lines
    total_lines = len(lines)
    blank_lines = sum(1 for line in lines if not line.strip())
    # Count comment lines
    comment_pattern = re.compile(r'^\s*(#|//|/\*|\*\s|/\*\*|\*/).*$')
    comment_lines = sum(1 for line in lines if comment_pattern.match(line))
    # Calculate code lines
    code_lines = total_lines - blank_lines - comment_lines
    # Calculate comment ratio
    comment_ratio = (
        round((comment_lines / total_lines * 100), 2) if total_lines > 0 else 0
    )
    return {
        "total_lines": total_lines,
        "code_lines": code_lines,
        "comment_lines": comment_lines,
        "blank_lines": blank_lines,
        "comment_ratio": comment_ratio,
    }


def get_function_metrics(code: str) -> Dict[str, Any]:
    """
    Extract and analyze functions from code.

    Args:
        code: The code to analyze

    Returns:
        Dictionary with function metrics
    """
    try:
        # Parse the code
        tree = ast.parse(code)
        # Find all function definitions
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Get function code
                func_lines = code.splitlines()[node.lineno - 1:node.end_lineno]
                func_code = "\n".join(func_lines)
                # Calculate metrics
                complexity = calculate_cyclomatic_complexity(func_code)
                maintainability = calculate_maintainability_index(func_code)
                halstead = calculate_halstead_metrics(func_code)
                line_metrics = calculate_line_metrics(func_code)
                functions.append({
                    "name": node.name,
                    "lineno": node.lineno,
                    "end_lineno": node.end_lineno,
                    "complexity": complexity,
                    "maintainability": maintainability,
                    "halstead": halstead,
                    "line_metrics": line_metrics,
                })
        return {
            "count": len(functions),
            "functions": functions,
            "avg_complexity": (
                sum(f["complexity"] for f in functions) / len(functions)
                if functions else 0
            ),
            "avg_maintainability": (
                sum(f["maintainability"] for f in functions) / len(functions)
                if functions else 0
            ),
        }
    except Exception:
        # If parsing fails, return empty results
        return {
            "count": 0,
            "functions": [],
            "avg_complexity": 0,
            "avg_maintainability": 0,
        }


def analyze_codebase_metrics(
    files: Dict[str, str], file_patterns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Analyze the metrics of a codebase.

    Args:
        files: Dictionary mapping file paths to file content
        file_patterns: Optional list of file patterns to include

    Returns:
        Dictionary with metrics for the codebase
    """
    # Filter files if patterns are provided
    if file_patterns:
        filtered_files = {
            path: content
            for path, content in files.items()
            if any(re.search(pattern, path) for pattern in file_patterns)
        }
    else:
        filtered_files = files
    # Initialize metrics
    metrics = {
        "files": {},
        "total_files": len(filtered_files),
        "total_lines": 0,
        "code_lines": 0,
        "comment_lines": 0,
        "blank_lines": 0,
        "comment_ratio": 0,
        "avg_complexity": 0,
        "avg_maintainability": 0,
        "function_count": 0,
    }
    # Analyze each file
    total_complexity = 0
    total_maintainability = 0
    total_functions = 0
    for path, content in filtered_files.items():
        # Calculate metrics
        complexity = calculate_cyclomatic_complexity(content)
        maintainability = calculate_maintainability_index(content)
        halstead = calculate_halstead_metrics(content)
        line_metrics = calculate_line_metrics(content)
        function_metrics = get_function_metrics(content)
        # Update file metrics
        metrics["files"][path] = {
            "complexity": complexity,
            "maintainability": maintainability,
            "halstead": halstead,
            "line_metrics": line_metrics,
            "function_metrics": function_metrics,
        }
        # Update totals
        metrics["total_lines"] += line_metrics["total_lines"]
        metrics["code_lines"] += line_metrics["code_lines"]
        metrics["comment_lines"] += line_metrics["comment_lines"]
        metrics["blank_lines"] += line_metrics["blank_lines"]
        metrics["function_count"] += function_metrics["count"]
        total_complexity += complexity
        total_maintainability += maintainability
        total_functions += function_metrics["count"]
    # Calculate averages
    if filtered_files:
        metrics["avg_complexity"] = round(
            total_complexity / len(filtered_files), 2
        )
        metrics["avg_maintainability"] = round(
            total_maintainability / len(filtered_files), 2
        )
    # Calculate overall comment ratio
    if metrics["total_lines"] > 0:
        ratio = metrics["comment_lines"] / metrics["total_lines"] * 100
        metrics["comment_ratio"] = round(ratio, 2)
    return metrics

