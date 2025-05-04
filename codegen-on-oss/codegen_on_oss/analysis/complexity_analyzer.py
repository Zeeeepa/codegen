"""
Complexity Analyzer Module

This module provides functions for analyzing the complexity of code.
"""

from typing import Any, Dict, List, Optional, Tuple

from codegen import Codebase
from codegen.sdk.core.function import Function
from codegen.sdk.core.class_def import Class
from codegen.sdk.core.source_file import SourceFile
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


def calculate_cyclomatic_complexity(function: Function) -> int:
    """
    Calculate the cyclomatic complexity of a function.
    
    Cyclomatic complexity is a measure of the number of linearly independent paths
    through a program's source code. It is calculated as:
    
    M = E - N + 2P
    
    Where:
    - E is the number of edges in the control flow graph
    - N is the number of nodes in the control flow graph
    - P is the number of connected components
    
    For a simple function, this can be approximated by counting the number of
    decision points (if, while, for, etc.) and adding 1.
    
    Args:
        function: The function to analyze
        
    Returns:
        The cyclomatic complexity of the function
    """
    complexity = 1  # Base complexity
    
    # Count decision points in the function
    for statement in function.code_block.statements:
        # Check for if statements
        if statement.type == "if_statement":
            complexity += 1
            # Add complexity for elif and else branches
            if hasattr(statement, "elif_branches"):
                complexity += len(statement.elif_branches)
        
        # Check for loops
        elif statement.type in ["for_statement", "while_statement"]:
            complexity += 1
        
        # Check for exception handling
        elif statement.type == "try_catch_statement":
            complexity += len(statement.catch_blocks)
        
        # Check for logical operators in expressions
        elif statement.type == "expression_statement":
            # This is a simplification; a more accurate approach would parse the expression
            if hasattr(statement, "expression") and hasattr(statement.expression, "value"):
                expr = statement.expression.value
                if isinstance(expr, str):
                    complexity += expr.count(" and ") + expr.count(" or ")
    
    return complexity


def calculate_cognitive_complexity(function: Function) -> int:
    """
    Calculate the cognitive complexity of a function.
    
    Cognitive complexity is a measure of how difficult a function is to understand.
    It is based on the following principles:
    
    1. Increment for each break in the linear flow
    2. Increment when flow-breaking structures are nested
    3. Ignore structures that allow multiple statements to be readably shorthanded
    
    Args:
        function: The function to analyze
        
    Returns:
        The cognitive complexity of the function
    """
    complexity = 0
    nesting_level = 0
    
    def process_statements(statements, current_nesting):
        nonlocal complexity
        
        for statement in statements:
            # Increment for control flow structures
            if statement.type in ["if_statement", "for_statement", "while_statement", "try_catch_statement"]:
                complexity += 1 + current_nesting  # Base + nesting level
                
                # Process nested statements with increased nesting level
                if statement.type == "if_statement":
                    if hasattr(statement, "body") and statement.body:
                        process_statements(statement.body.statements, current_nesting + 1)
                    if hasattr(statement, "else_body") and statement.else_body:
                        process_statements(statement.else_body.statements, current_nesting + 1)
                    if hasattr(statement, "elif_branches"):
                        for branch in statement.elif_branches:
                            if hasattr(branch, "body") and branch.body:
                                process_statements(branch.body.statements, current_nesting + 1)
                
                elif statement.type in ["for_statement", "while_statement"]:
                    if hasattr(statement, "body") and statement.body:
                        process_statements(statement.body.statements, current_nesting + 1)
                
                elif statement.type == "try_catch_statement":
                    if hasattr(statement, "try_block") and statement.try_block:
                        process_statements(statement.try_block.statements, current_nesting + 1)
                    if hasattr(statement, "catch_blocks"):
                        for block in statement.catch_blocks:
                            if hasattr(block, "body") and block.body:
                                process_statements(block.body.statements, current_nesting + 1)
                    if hasattr(statement, "finally_block") and statement.finally_block:
                        process_statements(statement.finally_block.statements, current_nesting + 1)
    
    # Start processing from the function's code block
    process_statements(function.code_block.statements, nesting_level)
    
    return complexity


def analyze_function_complexity(function: Function) -> Dict[str, Any]:
    """
    Analyze the complexity of a function.
    
    Args:
        function: The function to analyze
        
    Returns:
        A dictionary with complexity metrics
    """
    return {
        "name": function.name,
        "file": function.file.path if hasattr(function, "file") else None,
        "start_line": function.start_line,
        "end_line": function.end_line,
        "lines_of_code": function.end_line - function.start_line + 1,
        "cyclomatic_complexity": calculate_cyclomatic_complexity(function),
        "cognitive_complexity": calculate_cognitive_complexity(function),
        "parameter_count": len(function.parameters),
    }


def analyze_class_complexity(cls: Class) -> Dict[str, Any]:
    """
    Analyze the complexity of a class.
    
    Args:
        cls: The class to analyze
        
    Returns:
        A dictionary with complexity metrics
    """
    method_complexities = []
    total_cyclomatic = 0
    total_cognitive = 0
    
    for method in cls.methods:
        method_complexity = analyze_function_complexity(method)
        method_complexities.append(method_complexity)
        total_cyclomatic += method_complexity["cyclomatic_complexity"]
        total_cognitive += method_complexity["cognitive_complexity"]
    
    return {
        "name": cls.name,
        "file": cls.file.path if hasattr(cls, "file") else None,
        "start_line": cls.start_line,
        "end_line": cls.end_line,
        "lines_of_code": cls.end_line - cls.start_line + 1,
        "method_count": len(cls.methods),
        "property_count": len(cls.properties),
        "methods": method_complexities,
        "total_cyclomatic_complexity": total_cyclomatic,
        "total_cognitive_complexity": total_cognitive,
        "average_cyclomatic_complexity": total_cyclomatic / len(cls.methods) if cls.methods else 0,
        "average_cognitive_complexity": total_cognitive / len(cls.methods) if cls.methods else 0,
    }


def analyze_file_complexity(file: SourceFile) -> Dict[str, Any]:
    """
    Analyze the complexity of a file.
    
    Args:
        file: The file to analyze
        
    Returns:
        A dictionary with complexity metrics
    """
    function_complexities = []
    class_complexities = []
    
    for function in file.functions:
        function_complexities.append(analyze_function_complexity(function))
    
    for cls in file.classes:
        class_complexities.append(analyze_class_complexity(cls))
    
    return {
        "path": file.path,
        "lines_of_code": file.end_line - file.start_line + 1,
        "function_count": len(file.functions),
        "class_count": len(file.classes),
        "functions": function_complexities,
        "classes": class_complexities,
    }


def analyze_codebase_complexity(codebase: Codebase) -> Dict[str, Any]:
    """
    Analyze the complexity of a codebase.
    
    Args:
        codebase: The codebase to analyze
        
    Returns:
        A dictionary with complexity metrics
    """
    file_complexities = []
    function_complexities = []
    class_complexities = []
    
    total_files = len(codebase.files)
    total_functions = len(codebase.functions)
    total_classes = len(codebase.classes)
    total_lines = 0
    
    # Analyze files
    for file in codebase.files:
        file_complexity = analyze_file_complexity(file)
        file_complexities.append(file_complexity)
        total_lines += file_complexity["lines_of_code"]
    
    # Analyze functions
    for function in codebase.functions:
        function_complexities.append(analyze_function_complexity(function))
    
    # Analyze classes
    for cls in codebase.classes:
        class_complexities.append(analyze_class_complexity(cls))
    
    # Calculate average complexities
    avg_cyclomatic = sum(f["cyclomatic_complexity"] for f in function_complexities) / total_functions if total_functions else 0
    avg_cognitive = sum(f["cognitive_complexity"] for f in function_complexities) / total_functions if total_functions else 0
    
    # Find the most complex functions
    most_complex_functions = sorted(
        function_complexities,
        key=lambda f: f["cyclomatic_complexity"],
        reverse=True
    )[:10]
    
    return {
        "summary": {
            "total_files": total_files,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "total_lines_of_code": total_lines,
            "average_cyclomatic_complexity": avg_cyclomatic,
            "average_cognitive_complexity": avg_cognitive,
        },
        "most_complex_functions": most_complex_functions,
        "files": file_complexities,
        "functions": function_complexities,
        "classes": class_complexities,
    }

