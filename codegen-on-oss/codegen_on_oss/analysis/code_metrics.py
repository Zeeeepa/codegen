"""
Code Metrics Module for Codegen-on-OSS

This module provides functions for analyzing code metrics in a codebase,
including cyclomatic complexity, maintainability index, Halstead metrics,
and other code quality metrics.
"""

import math
from typing import Dict, List, Optional, Tuple, Union, Any

from codegen import Codebase
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.code_block import CodeBlock
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

# Constants for maintainability index calculation
MI_CONSTANTS = {
    'a': 171,
    'b': 5.2,
    'c': 0.23,
    'd': 16.2,
    'scale': 100 / 171
}

# Complexity rank definitions
COMPLEXITY_RANKS = {
    'A': {'range': (1, 5), 'description': 'Excellent'},
    'B': {'range': (6, 10), 'description': 'Good'},
    'C': {'range': (11, 20), 'description': 'Moderate'},
    'D': {'range': (21, 30), 'description': 'Complex'},
    'E': {'range': (31, 40), 'description': 'Very Complex'},
    'F': {'range': (41, float('inf')), 'description': 'Unmaintainable'}
}

def calculate_cyclomatic_complexity(code_block: CodeBlock) -> int:
    """
    Calculate the cyclomatic complexity of a code block.
    
    Cyclomatic complexity is a software metric used to indicate the complexity of a program.
    It directly measures the number of linearly independent paths through a program's source code.
    
    Args:
        code_block: The code block to analyze (function, method, etc.)
        
    Returns:
        int: The cyclomatic complexity score
    """
    # Start with complexity of 1 (one path through the function)
    complexity = 1
    
    # Count if statements
    if_statements = code_block.find_all(IfBlockStatement)
    for if_stmt in if_statements:
        # Add 1 for the if and 1 for each elif
        complexity += 1 + len(if_stmt.elif_blocks)
        # Add 1 for else if present
        if if_stmt.else_block:
            complexity += 1
    
    # Count loops
    for_loops = code_block.find_all(ForLoopStatement)
    complexity += len(for_loops)
    
    while_loops = code_block.find_all(WhileStatement)
    complexity += len(while_loops)
    
    # Count try-except blocks
    try_blocks = code_block.find_all(TryCatchStatement)
    for try_block in try_blocks:
        # Add 1 for each except clause
        complexity += len(try_block.catch_blocks)
    
    # Count logical operators in binary expressions
    binary_expressions = code_block.find_all(BinaryExpression)
    for expr in binary_expressions:
        if hasattr(expr, "operators"):
            for op in expr.operators:
                if op.source in ["&&", "||", "and", "or"]:
                    complexity += 1
    
    return complexity

def get_complexity_rank(complexity: int) -> str:
    """
    Convert cyclomatic complexity score to a letter grade.
    
    Args:
        complexity: The cyclomatic complexity score
        
    Returns:
        str: A letter grade from A to F
    """
    if complexity < 0:
        raise ValueError("Complexity must be a non-negative value")
    
    for rank, info in COMPLEXITY_RANKS.items():
        low, high = info['range']
        if low <= complexity <= high:
            return rank
    
    return "F"  # Default to F if no range matches (should not happen)

def calculate_halstead_metrics(code_block: CodeBlock) -> Dict[str, float]:
    """
    Calculate Halstead complexity metrics for a code block.
    
    Halstead metrics are software metrics that measure the computational complexity
    of a program based on the number of operators and operands.
    
    Args:
        code_block: The code block to analyze
        
    Returns:
        Dict[str, float]: Dictionary containing Halstead metrics
    """
    # This is a simplified implementation
    # In a real implementation, we would need to parse the code to identify operators and operands
    
    # Extract operators and operands
    operators = set()
    operands = set()
    
    # Find binary expressions for operators
    binary_expressions = code_block.find_all(BinaryExpression)
    for expr in binary_expressions:
        if hasattr(expr, "operators"):
            for op in expr.operators:
                operators.add(op.source)
    
    # Find comparison expressions for operators
    comparison_expressions = code_block.find_all(ComparisonExpression)
    for expr in comparison_expressions:
        if hasattr(expr, "operators"):
            for op in expr.operators:
                operators.add(op.source)
    
    # Find unary expressions for operators
    unary_expressions = code_block.find_all(UnaryExpression)
    for expr in unary_expressions:
        if hasattr(expr, "operator"):
            operators.add(expr.operator)
    
    # Count unique operators and operands
    n1 = len(operators)  # Number of distinct operators
    n2 = len(operands)   # Number of distinct operands
    
    # Estimate total operators and operands based on code length
    # This is a rough approximation
    code_length = len(str(code_block).splitlines())
    N1 = n1 * code_length // 4  # Total operators
    N2 = n2 * code_length // 3  # Total operands
    
    # Ensure we have at least 1 for each to avoid division by zero
    n1 = max(1, n1)
    n2 = max(1, n2)
    N1 = max(1, N1)
    N2 = max(1, N2)
    
    # Calculate Halstead metrics
    N = N1 + N2  # Program length
    n = n1 + n2  # Vocabulary size
    V = N * math.log2(n)  # Program volume
    D = (n1 / 2) * (N2 / n2)  # Difficulty
    E = D * V  # Effort
    T = E / 18  # Time required to program (in seconds)
    B = V / 3000  # Number of bugs
    
    return {
        "vocabulary": n,
        "length": N,
        "volume": V,
        "difficulty": D,
        "effort": E,
        "time": T,
        "bugs": B
    }

def calculate_maintainability_index(
    cyclomatic_complexity: int, 
    halstead_volume: float, 
    line_count: int, 
    comment_percentage: float = 0
) -> float:
    """
    Calculate the maintainability index for a code block.
    
    The maintainability index is a software metric that measures how maintainable
    (easy to support and change) the source code is.
    
    Args:
        cyclomatic_complexity: The cyclomatic complexity score
        halstead_volume: The Halstead volume metric
        line_count: The number of lines of code
        comment_percentage: The percentage of comments in the code (0-100)
        
    Returns:
        float: The maintainability index (0-100)
    """
    # Avoid log of zero
    if halstead_volume <= 0:
        halstead_volume = 1
    if line_count <= 0:
        line_count = 1
    
    # Calculate maintainability index
    mi = (
        MI_CONSTANTS['a'] - 
        MI_CONSTANTS['b'] * math.log(halstead_volume) - 
        MI_CONSTANTS['c'] * cyclomatic_complexity - 
        MI_CONSTANTS['d'] * math.log(line_count)
    )
    
    # Add comment factor if available
    if comment_percentage > 0:
        mi += 50 * math.sin(math.sqrt(2.4 * comment_percentage / 100))
    
    # Scale to 0-100
    mi = max(0, mi * MI_CONSTANTS['scale'])
    
    return round(mi, 2)

def get_function_metrics(func: Function) -> Dict[str, Any]:
    """
    Get comprehensive metrics for a function.
    
    Args:
        func: The function to analyze
        
    Returns:
        Dict[str, Any]: Dictionary containing all metrics for the function
    """
    # Get line count
    line_count = func.end_line - func.start_line + 1
    
    # Calculate cyclomatic complexity
    complexity = calculate_cyclomatic_complexity(func.code_block)
    
    # Calculate Halstead metrics
    halstead = calculate_halstead_metrics(func.code_block)
    
    # Estimate comment percentage (would need actual code parsing for accuracy)
    comment_percentage = 0  # Placeholder
    
    # Calculate maintainability index
    mi = calculate_maintainability_index(
        complexity, 
        halstead["volume"], 
        line_count, 
        comment_percentage
    )
    
    return {
        "name": func.name,
        "filepath": func.filepath,
        "start_line": func.start_line,
        "end_line": func.end_line,
        "line_count": line_count,
        "cyclomatic_complexity": complexity,
        "complexity_rank": get_complexity_rank(complexity),
        "halstead_metrics": halstead,
        "maintainability_index": mi,
        "comment_percentage": comment_percentage
    }

def analyze_file_metrics(file: SourceFile) -> Dict[str, Any]:
    """
    Analyze the metrics of a file.
    
    Args:
        file: The file to analyze
        
    Returns:
        Dict[str, Any]: Dictionary with metrics for the file
    """
    # Initialize metrics
    metrics = {
        "filepath": str(file.path),
        "total_lines": len(file.content.splitlines()),
        "function_count": len(file.functions),
        "class_count": len(file.classes),
        "functions": {},
        "classes": {},
        "overall_complexity": 0,
        "overall_maintainability": 100
    }
    
    # Calculate metrics for each function
    max_complexity = 0
    min_maintainability = 100
    total_complexity = 0
    
    for func in file.functions:
        func_metrics = get_function_metrics(func)
        metrics["functions"][func.name] = func_metrics
        max_complexity = max(max_complexity, func_metrics["cyclomatic_complexity"])
        min_maintainability = min(min_maintainability, func_metrics["maintainability_index"])
        total_complexity += func_metrics["cyclomatic_complexity"]
    
    # Calculate metrics for each class
    for cls in file.classes:
        class_metrics = {
            "name": cls.name,
            "methods": {},
            "total_complexity": 0,
            "average_complexity": 0,
            "method_count": len(cls.methods)
        }
        
        for method in cls.methods:
            method_metrics = get_function_metrics(method)
            class_metrics["methods"][method.name] = method_metrics
            class_metrics["total_complexity"] += method_metrics["cyclomatic_complexity"]
            max_complexity = max(max_complexity, method_metrics["cyclomatic_complexity"])
            min_maintainability = min(min_maintainability, method_metrics["maintainability_index"])
            total_complexity += method_metrics["cyclomatic_complexity"]
        
        if class_metrics["method_count"] > 0:
            class_metrics["average_complexity"] = round(
                class_metrics["total_complexity"] / class_metrics["method_count"], 
                2
            )
        
        metrics["classes"][cls.name] = class_metrics
    
    # Set the overall metrics
    metrics["overall_complexity"] = max_complexity
    metrics["overall_maintainability"] = min_maintainability
    
    # Calculate average complexity
    total_callables = metrics["function_count"] + sum(
        len(cls_metrics["methods"]) for cls_metrics in metrics["classes"].values()
    )
    
    if total_callables > 0:
        metrics["average_complexity"] = round(total_complexity / total_callables, 2)
    else:
        metrics["average_complexity"] = 0
    
    return metrics

def analyze_codebase_metrics(
    codebase: Codebase, 
    file_patterns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Analyze the metrics of a codebase.
    
    Args:
        codebase: The codebase to analyze
        file_patterns: Optional list of file patterns to include
        
    Returns:
        Dict[str, Any]: Dictionary with metrics for the codebase
    """
    # Initialize metrics
    metrics = {
        "files": {},
        "function_count": 0,
        "class_count": 0,
        "total_lines": 0,
        "overall_complexity": 0,
        "average_complexity": 0,
        "complexity_distribution": {rank: 0 for rank in COMPLEXITY_RANKS},
        "maintainability_distribution": {
            "high": 0,    # 85-100
            "medium": 0,  # 65-84
            "low": 0      # 0-64
        },
        "hotspots": []
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
    function_maintainability = []
    
    for file in files:
        file_metrics = analyze_file_metrics(file)
        metrics["files"][str(file.path)] = file_metrics
        metrics["function_count"] += file_metrics["function_count"]
        metrics["class_count"] += file_metrics["class_count"]
        metrics["total_lines"] += file_metrics["total_lines"]
        
        # Track function metrics for distribution
        for func_name, func_metrics in file_metrics["functions"].items():
            complexity = func_metrics["cyclomatic_complexity"]
            maintainability = func_metrics["maintainability_index"]
            
            function_complexities.append(complexity)
            function_maintainability.append(maintainability)
            
            # Update complexity distribution
            rank = get_complexity_rank(complexity)
            metrics["complexity_distribution"][rank] += 1
            
            # Update maintainability distribution
            if maintainability >= 85:
                metrics["maintainability_distribution"]["high"] += 1
            elif maintainability >= 65:
                metrics["maintainability_distribution"]["medium"] += 1
            else:
                metrics["maintainability_distribution"]["low"] += 1
            
            # Add to hotspots if complexity is high
            if complexity > 15:
                metrics["hotspots"].append({
                    "type": "function",
                    "name": func_name,
                    "file": str(file.path),
                    "line": func_metrics["start_line"],
                    "complexity": complexity,
                    "maintainability": maintainability,
                    "rank": rank
                })
        
        # Track class method metrics
        for cls_name, cls_metrics in file_metrics["classes"].items():
            for method_name, method_metrics in cls_metrics["methods"].items():
                complexity = method_metrics["cyclomatic_complexity"]
                maintainability = method_metrics["maintainability_index"]
                
                function_complexities.append(complexity)
                function_maintainability.append(maintainability)
                
                # Update complexity distribution
                rank = get_complexity_rank(complexity)
                metrics["complexity_distribution"][rank] += 1
                
                # Update maintainability distribution
                if maintainability >= 85:
                    metrics["maintainability_distribution"]["high"] += 1
                elif maintainability >= 65:
                    metrics["maintainability_distribution"]["medium"] += 1
                else:
                    metrics["maintainability_distribution"]["low"] += 1
                
                # Add to hotspots if complexity is high
                if complexity > 15:
                    metrics["hotspots"].append({
                        "type": "method",
                        "name": f"{cls_name}.{method_name}",
                        "file": str(file.path),
                        "line": method_metrics["start_line"],
                        "complexity": complexity,
                        "maintainability": maintainability,
                        "rank": rank
                    })
        
        # Update overall complexity (maximum of all files)
        metrics["overall_complexity"] = max(
            metrics["overall_complexity"], file_metrics["overall_complexity"]
        )
        total_complexity += file_metrics["overall_complexity"]
    
    # Calculate average complexity
    if len(files) > 0:
        metrics["average_complexity"] = round(total_complexity / len(files), 2)
    
    # Calculate percentages for distributions
    total_functions = len(function_complexities)
    if total_functions > 0:
        # Complexity distribution percentages
        for rank in metrics["complexity_distribution"]:
            count = metrics["complexity_distribution"][rank]
            metrics["complexity_distribution"][rank] = {
                "count": count,
                "percentage": round((count / total_functions) * 100, 2),
                "description": COMPLEXITY_RANKS[rank]["description"]
            }
        
        # Maintainability distribution percentages
        for level in metrics["maintainability_distribution"]:
            count = metrics["maintainability_distribution"][level]
            metrics["maintainability_distribution"][level] = {
                "count": count,
                "percentage": round((count / total_functions) * 100, 2)
            }
    
    # Sort hotspots by complexity (descending)
    metrics["hotspots"].sort(key=lambda x: x["complexity"], reverse=True)
    
    return metrics

def calculate_line_metrics(file: SourceFile) -> Dict[str, int]:
    """
    Calculate line-based metrics for a file.
    
    Args:
        file: The file to analyze
        
    Returns:
        Dict[str, int]: Dictionary with line metrics
    """
    content = file.content
    lines = content.splitlines()
    
    # Count different types of lines
    total_lines = len(lines)
    blank_lines = sum(1 for line in lines if line.strip() == '')
    
    # Estimate comment lines (this is a simplification)
    # A more accurate implementation would need to parse the code properly
    comment_lines = 0
    in_multiline_comment = False
    
    for line in lines:
        stripped = line.strip()
        
        # Check for single line comments
        if stripped.startswith('#') or stripped.startswith('//'):
            comment_lines += 1
            continue
            
        # Check for multiline comments
        if in_multiline_comment:
            comment_lines += 1
            if '*/' in stripped:
                in_multiline_comment = False
            continue
            
        if stripped.startswith('/*'):
            comment_lines += 1
            if not '*/' in stripped:
                in_multiline_comment = True
            continue
            
        # Check for docstrings in Python
        if stripped.startswith('"""') or stripped.startswith("'''"):
            comment_lines += 1
            if stripped.endswith('"""') or stripped.endswith("'''"):
                # Single line docstring
                continue
            else:
                # Start of multiline docstring
                in_multiline_comment = True
                continue
    
    # Calculate code lines
    code_lines = total_lines - blank_lines - comment_lines
    
    return {
        "total_lines": total_lines,
        "code_lines": code_lines,
        "comment_lines": comment_lines,
        "blank_lines": blank_lines,
        "comment_ratio": round((comment_lines / total_lines * 100), 2) if total_lines > 0 else 0
    }

