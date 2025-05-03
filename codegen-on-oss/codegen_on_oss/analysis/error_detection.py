"""
Error Detection Module for Codegen-on-OSS

This module provides comprehensive error detection capabilities for Python codebases,
focusing on function parameter validation, call-in/call-out point validation, and
other common code issues.
"""

import ast
import inspect
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from codegen import Codebase
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.expressions.binary_expression import BinaryExpression
from codegen.sdk.core.expressions.comparison_expression import ComparisonExpression
from codegen.sdk.core.expressions.unary_expression import UnaryExpression
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.statements.for_loop_statement import ForLoopStatement
from codegen.sdk.core.statements.if_block_statement import IfBlockStatement
from codegen.sdk.core.statements.try_catch_statement import TryCatchStatement
from codegen.sdk.core.statements.while_statement import WhileStatement
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.enums import EdgeType, SymbolType

from codegen_on_oss.analysis.codebase_context import CodebaseContext


class ErrorSeverity(Enum):
    """Severity levels for detected errors."""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class ErrorCategory(Enum):
    """Categories of errors that can be detected."""
    PARAMETER_TYPE_MISMATCH = auto()
    PARAMETER_COUNT_MISMATCH = auto()
    UNUSED_PARAMETER = auto()
    UNDEFINED_PARAMETER = auto()
    MISSING_REQUIRED_PARAMETER = auto()
    RETURN_TYPE_MISMATCH = auto()
    UNDEFINED_VARIABLE = auto()
    UNUSED_IMPORT = auto()
    UNUSED_VARIABLE = auto()
    POTENTIAL_EXCEPTION = auto()
    CALL_POINT_ERROR = auto()
    CIRCULAR_DEPENDENCY = auto()
    INCONSISTENT_RETURN = auto()
    UNREACHABLE_CODE = auto()
    COMPLEX_FUNCTION = auto()


@dataclass
class CodeError:
    """Represents a detected error in the code."""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    file_path: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    code_snippet: Optional[str] = None
    suggested_fix: Optional[str] = None
    related_symbols: List[Symbol] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary representation."""
        return {
            "category": self.category.name,
            "severity": self.severity.name,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "function_name": self.function_name,
            "class_name": self.class_name,
            "code_snippet": self.code_snippet,
            "suggested_fix": self.suggested_fix,
            "related_symbols": [symbol.name for symbol in self.related_symbols]
        }
    
    def __str__(self) -> str:
        """String representation of the error."""
        location = f"{self.file_path}"
        if self.line_number:
            location += f":{self.line_number}"
            if self.column:
                location += f":{self.column}"
        
        context = ""
        if self.function_name:
            context += f" in function '{self.function_name}'"
        if self.class_name:
            context += f" of class '{self.class_name}'"
        
        return f"[{self.severity.name}] {self.category.name}: {self.message} at {location}{context}"


class ErrorDetector:
    """Base class for error detectors."""
    
    def __init__(self, codebase: Codebase, context: Optional[CodebaseContext] = None):
        """Initialize the error detector with a codebase.
        
        Args:
            codebase: The Codebase object to analyze
            context: Optional CodebaseContext for additional analysis capabilities
        """
        self.codebase = codebase
        self.context = context
        self.errors: List[CodeError] = []
    
    def detect_errors(self) -> List[CodeError]:
        """Detect errors in the codebase.
        
        Returns:
            A list of detected errors
        """
        raise NotImplementedError("Subclasses must implement detect_errors()")
    
    def clear_errors(self) -> None:
        """Clear all detected errors."""
        self.errors = []


class ParameterValidator(ErrorDetector):
    """Validates function parameters and their usage."""
    
    def detect_errors(self) -> List[CodeError]:
        """Detect parameter-related errors in the codebase.
        
        Returns:
            A list of detected parameter errors
        """
        self.clear_errors()
        
        # Process all functions in the codebase
        for function in self.codebase.functions:
            self._validate_function_parameters(function)
            self._validate_function_calls(function)
        
        return self.errors
    
    def _validate_function_parameters(self, function: Function) -> None:
        """Validate the parameters of a function.
        
        Args:
            function: The function to validate
        """
        # Check for unused parameters
        used_params = set()
        if hasattr(function, "code_block") and function.code_block:
            for statement in function.code_block.statements:
                # Extract parameter usages from the statement
                param_names = self._extract_parameter_usages(statement)
                used_params.update(param_names)
        
        # Compare with declared parameters
        for param in function.parameters:
            if param.name not in used_params and not param.name.startswith('_'):
                self.errors.append(CodeError(
                    category=ErrorCategory.UNUSED_PARAMETER,
                    severity=ErrorSeverity.WARNING,
                    message=f"Parameter '{param.name}' is declared but never used",
                    file_path=function.filepath,
                    line_number=function.line_number,
                    function_name=function.name,
                    class_name=function.class_name if hasattr(function, "class_name") else None,
                    related_symbols=[function]
                ))
    
    def _validate_function_calls(self, function: Function) -> None:
        """Validate calls to other functions.
        
        Args:
            function: The function containing calls to validate
        """
        if not hasattr(function, "code_block") or not function.code_block:
            return
        
        for statement in function.code_block.statements:
            if not hasattr(statement, "function_calls"):
                continue
                
            for call in statement.function_calls:
                # Try to resolve the called function
                called_func = self._resolve_function_call(call)
                if not called_func:
                    continue
                
                # Check parameter count
                if len(call.args) > len(called_func.parameters):
                    self.errors.append(CodeError(
                        category=ErrorCategory.PARAMETER_COUNT_MISMATCH,
                        severity=ErrorSeverity.ERROR,
                        message=f"Too many arguments in call to '{called_func.name}': expected {len(called_func.parameters)}, got {len(call.args)}",
                        file_path=function.filepath,
                        line_number=call.line_number if hasattr(call, "line_number") else function.line_number,
                        function_name=function.name,
                        related_symbols=[function, called_func]
                    ))
                
                # Check for missing required parameters
                required_params = [p for p in called_func.parameters if not p.has_default_value]
                if len(call.args) < len(required_params):
                    self.errors.append(CodeError(
                        category=ErrorCategory.MISSING_REQUIRED_PARAMETER,
                        severity=ErrorSeverity.ERROR,
                        message=f"Missing required parameters in call to '{called_func.name}': expected at least {len(required_params)}, got {len(call.args)}",
                        file_path=function.filepath,
                        line_number=call.line_number if hasattr(call, "line_number") else function.line_number,
                        function_name=function.name,
                        related_symbols=[function, called_func]
                    ))
    
    def _extract_parameter_usages(self, statement: Any) -> Set[str]:
        """Extract parameter names used in a statement.
        
        Args:
            statement: The statement to analyze
            
        Returns:
            A set of parameter names used in the statement
        """
        used_params = set()
        
        # Extract from expressions
        if hasattr(statement, "expressions"):
            for expr in statement.expressions:
                if isinstance(expr, BinaryExpression) or isinstance(expr, ComparisonExpression):
                    for elem in expr.elements:
                        if hasattr(elem, "name"):
                            used_params.add(elem.name)
                elif isinstance(expr, UnaryExpression):
                    if hasattr(expr.argument, "name"):
                        used_params.add(expr.argument.name)
        
        # Extract from function calls
        if hasattr(statement, "function_calls"):
            for call in statement.function_calls:
                for arg in call.args:
                    if hasattr(arg, "name"):
                        used_params.add(arg.name)
        
        # Extract from nested statements
        if isinstance(statement, IfBlockStatement):
            for block in statement.blocks:
                for nested_stmt in block.statements:
                    used_params.update(self._extract_parameter_usages(nested_stmt))
        elif isinstance(statement, ForLoopStatement):
            for nested_stmt in statement.body.statements:
                used_params.update(self._extract_parameter_usages(nested_stmt))
        elif isinstance(statement, WhileStatement):
            for nested_stmt in statement.body.statements:
                used_params.update(self._extract_parameter_usages(nested_stmt))
        elif isinstance(statement, TryCatchStatement):
            for nested_stmt in statement.try_block.statements:
                used_params.update(self._extract_parameter_usages(nested_stmt))
            for catch_block in statement.catch_blocks:
                for nested_stmt in catch_block.statements:
                    used_params.update(self._extract_parameter_usages(nested_stmt))
            if statement.finally_block:
                for nested_stmt in statement.finally_block.statements:
                    used_params.update(self._extract_parameter_usages(nested_stmt))
        
        return used_params
    
    def _resolve_function_call(self, call: Any) -> Optional[Function]:
        """Resolve a function call to its definition.
        
        Args:
            call: The function call to resolve
            
        Returns:
            The Function object if found, None otherwise
        """
        # Try to find the function by name
        for func in self.codebase.functions:
            if func.name == call.name:
                return func
        
        # If not found directly, try to resolve through imports
        # This is a simplified approach and may not work for all cases
        return None


class CallValidator(ErrorDetector):
    """Validates function call-in and call-out points."""
    
    def detect_errors(self) -> List[CodeError]:
        """Detect call-related errors in the codebase.
        
        Returns:
            A list of detected call errors
        """
        self.clear_errors()
        
        # Build a call graph
        call_graph = self._build_call_graph()
        
        # Check for circular dependencies
        circular_deps = self._find_circular_dependencies(call_graph)
        for cycle in circular_deps:
            if len(cycle) > 1:  # Ignore self-recursion
                cycle_str = " -> ".join(cycle)
                self.errors.append(CodeError(
                    category=ErrorCategory.CIRCULAR_DEPENDENCY,
                    severity=ErrorSeverity.WARNING,
                    message=f"Circular dependency detected: {cycle_str}",
                    file_path="",  # This is a multi-file issue
                    related_symbols=[self._get_function_by_name(func_name) for func_name in cycle if self._get_function_by_name(func_name)]
                ))
        
        # Check for potential exceptions in call chains
        for function in self.codebase.functions:
            self._check_exception_handling(function, call_graph)
        
        return self.errors
    
    def _build_call_graph(self) -> Dict[str, List[str]]:
        """Build a graph of function calls.
        
        Returns:
            A dictionary mapping function names to lists of called function names
        """
        call_graph = {}
        
        for function in self.codebase.functions:
            calls = []
            
            if hasattr(function, "code_block") and function.code_block:
                for statement in function.code_block.statements:
                    if hasattr(statement, "function_calls"):
                        for call in statement.function_calls:
                            calls.append(call.name)
            
            call_graph[function.name] = calls
        
        return call_graph
    
    def _find_circular_dependencies(self, call_graph: Dict[str, List[str]]) -> List[List[str]]:
        """Find circular dependencies in the call graph.
        
        Args:
            call_graph: The call graph to analyze
            
        Returns:
            A list of cycles, where each cycle is a list of function names
        """
        cycles = []
        visited = set()
        path = []
        
        def dfs(node):
            if node in path:
                cycle = path[path.index(node):] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            path.append(node)
            
            for neighbor in call_graph.get(node, []):
                if neighbor in call_graph:  # Only consider functions we know about
                    dfs(neighbor)
            
            path.pop()
        
        for node in call_graph:
            dfs(node)
        
        return cycles
    
    def _check_exception_handling(self, function: Function, call_graph: Dict[str, List[str]]) -> None:
        """Check for potential exceptions in function calls.
        
        Args:
            function: The function to check
            call_graph: The call graph for context
        """
        if not hasattr(function, "code_block") or not function.code_block:
            return
        
        # Check if the function has try-catch blocks
        has_try_catch = any(isinstance(stmt, TryCatchStatement) for stmt in function.code_block.statements)
        
        # Check calls that might throw exceptions
        for statement in function.code_block.statements:
            if not hasattr(statement, "function_calls"):
                continue
                
            for call in statement.function_calls:
                # Check if the called function might throw exceptions
                called_func = self._get_function_by_name(call.name)
                if not called_func:
                    continue
                
                if self._might_throw_exception(called_func) and not has_try_catch:
                    self.errors.append(CodeError(
                        category=ErrorCategory.POTENTIAL_EXCEPTION,
                        severity=ErrorSeverity.WARNING,
                        message=f"Call to '{call.name}' might throw an exception but is not wrapped in a try-catch block",
                        file_path=function.filepath,
                        line_number=call.line_number if hasattr(call, "line_number") else function.line_number,
                        function_name=function.name,
                        related_symbols=[function, called_func]
                    ))
    
    def _might_throw_exception(self, function: Function) -> bool:
        """Check if a function might throw an exception.
        
        Args:
            function: The function to check
            
        Returns:
            True if the function might throw an exception, False otherwise
        """
        if not hasattr(function, "code_block") or not function.code_block:
            return False
        
        # Look for raise statements
        for statement in function.code_block.statements:
            if hasattr(statement, "type") and statement.type == "raise_statement":
                return True
        
        # Check for calls to functions that might throw exceptions
        for statement in function.code_block.statements:
            if hasattr(statement, "function_calls"):
                for call in statement.function_calls:
                    # Some common functions that might throw exceptions
                    if call.name in ["open", "read", "write", "json.loads", "requests.get"]:
                        return True
        
        return False
    
    def _get_function_by_name(self, name: str) -> Optional[Function]:
        """Get a function by its name.
        
        Args:
            name: The name of the function
            
        Returns:
            The Function object if found, None otherwise
        """
        for function in self.codebase.functions:
            if function.name == name:
                return function
        return None


class ReturnValidator(ErrorDetector):
    """Validates function return values and types."""
    
    def detect_errors(self) -> List[CodeError]:
        """Detect return-related errors in the codebase.
        
        Returns:
            A list of detected return errors
        """
        self.clear_errors()
        
        for function in self.codebase.functions:
            self._validate_return_consistency(function)
            self._validate_return_type(function)
        
        return self.errors
    
    def _validate_return_consistency(self, function: Function) -> None:
        """Validate that a function's return statements are consistent.
        
        Args:
            function: The function to validate
        """
        if not hasattr(function, "return_statements") or not function.return_statements:
            return
        
        # Check if some return statements have values and others don't
        has_value = any(hasattr(stmt, "value") and stmt.value for stmt in function.return_statements)
        missing_value = any(not hasattr(stmt, "value") or not stmt.value for stmt in function.return_statements)
        
        if has_value and missing_value:
            self.errors.append(CodeError(
                category=ErrorCategory.INCONSISTENT_RETURN,
                severity=ErrorSeverity.ERROR,
                message="Inconsistent return statements: some return values and others don't",
                file_path=function.filepath,
                line_number=function.line_number,
                function_name=function.name,
                class_name=function.class_name if hasattr(function, "class_name") else None,
                related_symbols=[function]
            ))
    
    def _validate_return_type(self, function: Function) -> None:
        """Validate that a function's return type matches its annotations.
        
        Args:
            function: The function to validate
        """
        # Check if the function has a return type annotation
        if not hasattr(function, "return_type") or not function.return_type:
            return
        
        # Skip if return type is Any, None, or similar
        if function.return_type in ["Any", "None", "Optional", "Union"]:
            return
        
        # Check return statements
        for stmt in function.return_statements:
            if not hasattr(stmt, "value") or not stmt.value:
                continue
                
            # This is a simplified check and may not work for all cases
            # A more robust implementation would need type inference
            if hasattr(stmt.value, "type"):
                value_type = stmt.value.type
                if value_type and value_type != function.return_type:
                    self.errors.append(CodeError(
                        category=ErrorCategory.RETURN_TYPE_MISMATCH,
                        severity=ErrorSeverity.WARNING,
                        message=f"Return type mismatch: expected '{function.return_type}', got '{value_type}'",
                        file_path=function.filepath,
                        line_number=stmt.line_number if hasattr(stmt, "line_number") else function.line_number,
                        function_name=function.name,
                        class_name=function.class_name if hasattr(function, "class_name") else None,
                        related_symbols=[function]
                    ))


class CodeAnalysisError(ErrorDetector):
    """Comprehensive error detector that combines multiple specialized detectors."""
    
    def __init__(self, codebase: Codebase, context: Optional[CodebaseContext] = None):
        """Initialize the error detector with a codebase.
        
        Args:
            codebase: The Codebase object to analyze
            context: Optional CodebaseContext for additional analysis capabilities
        """
        super().__init__(codebase, context)
        
        # Initialize specialized detectors
        self.parameter_validator = ParameterValidator(codebase, context)
        self.call_validator = CallValidator(codebase, context)
        self.return_validator = ReturnValidator(codebase, context)
    
    def detect_errors(self) -> List[CodeError]:
        """Detect all types of errors in the codebase.
        
        Returns:
            A list of all detected errors
        """
        self.clear_errors()
        
        # Collect errors from all specialized detectors
        self.errors.extend(self.parameter_validator.detect_errors())
        self.errors.extend(self.call_validator.detect_errors())
        self.errors.extend(self.return_validator.detect_errors())
        
        # Add additional error detection logic here
        self._detect_unreachable_code()
        self._detect_complex_functions()
        
        return self.errors
    
    def _detect_unreachable_code(self) -> None:
        """Detect unreachable code in functions."""
        for function in self.codebase.functions:
            if not hasattr(function, "code_block") or not function.code_block:
                continue
                
            # Check for code after return statements
            has_unreachable = False
            reached_return = False
            
            for stmt in function.code_block.statements:
                if reached_return:
                    has_unreachable = True
                    break
                
                if hasattr(stmt, "type") and stmt.type == "return_statement":
                    reached_return = True
            
            if has_unreachable:
                self.errors.append(CodeError(
                    category=ErrorCategory.UNREACHABLE_CODE,
                    severity=ErrorSeverity.WARNING,
                    message="Function contains unreachable code after return statement",
                    file_path=function.filepath,
                    line_number=function.line_number,
                    function_name=function.name,
                    class_name=function.class_name if hasattr(function, "class_name") else None,
                    related_symbols=[function]
                ))
    
    def _detect_complex_functions(self) -> None:
        """Detect overly complex functions."""
        from codegen_on_oss.analysis.analysis import calculate_cyclomatic_complexity
        
        for function in self.codebase.functions:
            complexity = calculate_cyclomatic_complexity(function)
            
            if complexity > 15:  # Threshold for high complexity
                self.errors.append(CodeError(
                    category=ErrorCategory.COMPLEX_FUNCTION,
                    severity=ErrorSeverity.WARNING,
                    message=f"Function has high cyclomatic complexity ({complexity})",
                    file_path=function.filepath,
                    line_number=function.line_number,
                    function_name=function.name,
                    class_name=function.class_name if hasattr(function, "class_name") else None,
                    related_symbols=[function]
                ))


def analyze_errors(codebase: Codebase, context: Optional[CodebaseContext] = None) -> Dict[str, Any]:
    """Analyze a codebase for errors and return comprehensive results.
    
    Args:
        codebase: The Codebase object to analyze
        context: Optional CodebaseContext for additional analysis capabilities
        
    Returns:
        A dictionary containing error analysis results
    """
    # Create the comprehensive error detector
    detector = CodeAnalysisError(codebase, context)
    
    # Detect all errors
    errors = detector.detect_errors()
    
    # Group errors by category
    errors_by_category = {}
    for error in errors:
        category = error.category.name
        if category not in errors_by_category:
            errors_by_category[category] = []
        errors_by_category[category].append(error.to_dict())
    
    # Group errors by file
    errors_by_file = {}
    for error in errors:
        file_path = error.file_path
        if file_path not in errors_by_file:
            errors_by_file[file_path] = []
        errors_by_file[file_path].append(error.to_dict())
    
    # Group errors by severity
    errors_by_severity = {}
    for error in errors:
        severity = error.severity.name
        if severity not in errors_by_severity:
            errors_by_severity[severity] = []
        errors_by_severity[severity].append(error.to_dict())
    
    # Compute summary statistics
    summary = {
        "total_errors": len(errors),
        "errors_by_severity": {severity: len(errors) for severity, errors in errors_by_severity.items()},
        "errors_by_category": {category: len(errors) for category, errors in errors_by_category.items()},
        "files_with_errors": len(errors_by_file),
    }
    
    # Return the complete analysis
    return {
        "summary": summary,
        "errors_by_category": errors_by_category,
        "errors_by_file": errors_by_file,
        "errors_by_severity": errors_by_severity,
        "all_errors": [error.to_dict() for error in errors]
    }

