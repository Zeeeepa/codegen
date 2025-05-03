"""
Error detection module for code analysis.

This module provides classes and functions for detecting various types of errors in code,
including parameter validation, call validation, and return validation.
"""

from enum import Enum, auto
from typing import List, Dict, Any, Optional, Set, Union
from dataclasses import dataclass

from codegen import Codebase
from codegen.sdk.core.function import Function
from codegen.sdk.core.symbol import Symbol
from codegen_on_oss.analysis.codebase_context import CodebaseContext


class ErrorSeverity(Enum):
    """Severity levels for code errors."""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class ErrorCategory(Enum):
    """Categories of code errors."""
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
    """
    Represents an error detected in the code.
    
    Attributes:
        category: The category of the error
        severity: The severity level of the error
        message: A descriptive message about the error
        file_path: Path to the file containing the error
        line_number: Line number where the error occurs (optional)
        function_name: Name of the function containing the error (optional)
        symbol_name: Name of the symbol related to the error (optional)
        additional_info: Any additional information about the error (optional)
    """
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    file_path: str
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    symbol_name: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None


class ErrorDetector:
    """
    Base class for error detectors.
    
    This class provides common functionality for detecting errors in code.
    Subclasses should implement the detect_errors method.
    """
    
    def __init__(self, codebase: Codebase, context: Optional[CodebaseContext] = None):
        """
        Initialize the error detector.
        
        Args:
            codebase: The codebase to analyze
            context: Optional context for the analysis
        """
        self.codebase = codebase
        self.context = context
        self.errors: List[CodeError] = []
    
    def detect_errors(self) -> List[CodeError]:
        """
        Detect errors in the codebase.
        
        Returns:
            A list of detected errors
        """
        raise NotImplementedError("Subclasses must implement detect_errors")
    
    def clear_errors(self) -> None:
        """Clear the list of detected errors."""
        self.errors = []


class ParameterValidator(ErrorDetector):
    """
    Validates function parameters.
    
    This class detects issues related to function parameters, such as unused parameters,
    parameter count mismatches, and missing required parameters.
    """
    
    def detect_errors(self) -> List[CodeError]:
        """
        Detect parameter-related errors in the codebase.
        
        Returns:
            A list of detected errors
        """
        self.clear_errors()
        
        for function in self.codebase.functions:
            # Skip functions without code blocks
            if not hasattr(function, "code_block"):
                continue
                
            # Check for unused parameters
            self._check_unused_parameters(function)
            
            # Check for parameter type mismatches
            self._check_parameter_types(function)
        
        return self.errors
    
    def _check_unused_parameters(self, function: Function) -> None:
        """
        Check for unused parameters in a function.
        
        Args:
            function: The function to check
        """
        if not hasattr(function, "parameters") or not function.parameters:
            return
            
        # Get all parameter names
        param_names = {param.name for param in function.parameters}
        
        # Get all variable references in the function body
        used_names = set()
        if hasattr(function, "code_block") and hasattr(function.code_block, "variable_references"):
            used_names = {ref.name for ref in function.code_block.variable_references}
        
        # Find unused parameters
        unused_params = param_names - used_names
        for param_name in unused_params:
            self.errors.append(CodeError(
                category=ErrorCategory.UNUSED_PARAMETER,
                severity=ErrorSeverity.WARNING,
                message=f"Parameter '{param_name}' is never used in function '{function.name}'",
                file_path=function.filepath,
                function_name=function.name
            ))
    
    def _check_parameter_types(self, function: Function) -> None:
        """
        Check for parameter type mismatches in a function.
        
        Args:
            function: The function to check
        """
        if not hasattr(function, "parameters") or not function.parameters:
            return
            
        # Check for parameters with type annotations
        for param in function.parameters:
            if not hasattr(param, "type_annotation") or not param.type_annotation:
                continue
                
            # Check for calls to this function
            for caller in self.codebase.functions:
                if not hasattr(caller, "code_block"):
                    continue
                    
                for call in caller.code_block.function_calls:
                    if call.name != function.name:
                        continue
                        
                    # Check if the argument types match the parameter types
                    for i, arg in enumerate(call.args):
                        if i >= len(function.parameters):
                            break
                            
                        param = function.parameters[i]
                        if not hasattr(arg, "type") or not arg.type:
                            continue
                            
                        if arg.type != param.type_annotation:
                            self.errors.append(CodeError(
                                category=ErrorCategory.PARAMETER_TYPE_MISMATCH,
                                severity=ErrorSeverity.ERROR,
                                message=f"Type mismatch for parameter '{param.name}' in call to '{function.name}': expected '{param.type_annotation}', got '{arg.type}'",
                                file_path=caller.filepath,
                                function_name=caller.name
                            ))


class CallValidator(ErrorDetector):
    """
    Validates function calls.
    
    This class detects issues related to function calls, such as circular dependencies
    and potential exceptions.
    """
    
    def detect_errors(self) -> List[CodeError]:
        """
        Detect call-related errors in the codebase.
        
        Returns:
            A list of detected errors
        """
        self.clear_errors()
        
        # Build a call graph
        call_graph: Dict[str, Set[str]] = {}
        for function in self.codebase.functions:
            if not hasattr(function, "code_block"):
                continue
                
            call_graph[function.name] = set()
            for call in function.code_block.function_calls:
                call_graph[function.name].add(call.name)
        
        # Check for circular dependencies
        self._check_circular_dependencies(call_graph)
        
        # Check for potential exceptions
        self._check_potential_exceptions()
        
        return self.errors
    
    def _check_circular_dependencies(self, call_graph: Dict[str, Set[str]]) -> None:
        """
        Check for circular dependencies in the call graph.
        
        Args:
            call_graph: A dictionary mapping function names to sets of called function names
        """
        visited = set()
        path = []
        
        def dfs(node: str) -> None:
            if node in path:
                # Found a cycle
                cycle = path[path.index(node):] + [node]
                cycle_str = " -> ".join(cycle)
                
                # Find the function object for the file path
                function = None
                for f in self.codebase.functions:
                    if f.name == node:
                        function = f
                        break
                
                if function:
                    self.errors.append(CodeError(
                        category=ErrorCategory.CIRCULAR_DEPENDENCY,
                        severity=ErrorSeverity.WARNING,
                        message=f"Circular dependency detected: {cycle_str}",
                        file_path=function.filepath,
                        function_name=node
                    ))
                return
            
            if node in visited or node not in call_graph:
                return
                
            visited.add(node)
            path.append(node)
            
            for called in call_graph[node]:
                dfs(called)
                
            path.pop()
        
        for node in call_graph:
            dfs(node)
    
    def _check_potential_exceptions(self) -> None:
        """Check for potential exceptions in function calls."""
        for function in self.codebase.functions:
            if not hasattr(function, "code_block"):
                continue
                
            # Check for try-except blocks
            has_try_except = any(
                hasattr(stmt, "type") and stmt.type == "try_statement"
                for stmt in function.code_block.statements
            )
            
            # Check for potentially risky operations
            for call in function.code_block.function_calls:
                risky_functions = ["open", "read", "write", "div", "divide", "parse", "json.loads"]
                if any(risk in call.name for risk in risky_functions) and not has_try_except:
                    self.errors.append(CodeError(
                        category=ErrorCategory.POTENTIAL_EXCEPTION,
                        severity=ErrorSeverity.WARNING,
                        message=f"Potentially risky function '{call.name}' called without exception handling",
                        file_path=function.filepath,
                        function_name=function.name
                    ))


class ReturnValidator(ErrorDetector):
    """
    Validates function returns.
    
    This class detects issues related to function returns, such as inconsistent return types
    and values.
    """
    
    def detect_errors(self) -> List[CodeError]:
        """
        Detect return-related errors in the codebase.
        
        Returns:
            A list of detected errors
        """
        self.clear_errors()
        
        for function in self.codebase.functions:
            # Skip functions without code blocks
            if not hasattr(function, "code_block"):
                continue
                
            # Check for inconsistent return types
            self._check_return_types(function)
            
            # Check for inconsistent return values
            self._check_return_values(function)
        
        return self.errors
    
    def _check_return_types(self, function: Function) -> None:
        """
        Check for inconsistent return types in a function.
        
        Args:
            function: The function to check
        """
        if not hasattr(function, "return_type") or not function.return_type:
            return
            
        # Get all return statements
        return_stmts = []
        for stmt in function.code_block.statements:
            if hasattr(stmt, "type") and stmt.type == "return_statement":
                return_stmts.append(stmt)
        
        # Check if return types match the declared return type
        for ret_stmt in return_stmts:
            if not hasattr(ret_stmt, "value") or not hasattr(ret_stmt.value, "type"):
                continue
                
            if ret_stmt.value.type != function.return_type:
                self.errors.append(CodeError(
                    category=ErrorCategory.RETURN_TYPE_MISMATCH,
                    severity=ErrorSeverity.ERROR,
                    message=f"Return type mismatch in function '{function.name}': expected '{function.return_type}', got '{ret_stmt.value.type}'",
                    file_path=function.filepath,
                    function_name=function.name
                ))
    
    def _check_return_values(self, function: Function) -> None:
        """
        Check for inconsistent return values in a function.
        
        Args:
            function: The function to check
        """
        # Get all return statements
        return_stmts = []
        for stmt in function.code_block.statements:
            if hasattr(stmt, "type") and stmt.type == "return_statement":
                return_stmts.append(stmt)
        
        # Check if some return statements have values and others don't
        has_value = [hasattr(ret_stmt, "value") and ret_stmt.value is not None for ret_stmt in return_stmts]
        if has_value and any(has_value) and not all(has_value):
            self.errors.append(CodeError(
                category=ErrorCategory.INCONSISTENT_RETURN,
                severity=ErrorSeverity.WARNING,
                message=f"Inconsistent return values in function '{function.name}': some return statements have values, others don't",
                file_path=function.filepath,
                function_name=function.name
            ))


class CodeAnalysisError:
    """
    Main class for detecting errors in code.
    
    This class combines multiple error detectors to provide comprehensive error detection.
    """
    
    def __init__(self, codebase: Codebase, context: Optional[CodebaseContext] = None):
        """
        Initialize the error detector.
        
        Args:
            codebase: The codebase to analyze
            context: Optional context for the analysis
        """
        self.codebase = codebase
        self.context = context
        self.parameter_validator = ParameterValidator(codebase, context)
        self.call_validator = CallValidator(codebase, context)
        self.return_validator = ReturnValidator(codebase, context)
    
    def detect_errors(self) -> List[CodeError]:
        """
        Detect all errors in the codebase.
        
        Returns:
            A list of all detected errors
        """
        errors = []
        errors.extend(self.parameter_validator.detect_errors())
        errors.extend(self.call_validator.detect_errors())
        errors.extend(self.return_validator.detect_errors())
        return errors
    
    def get_errors_by_category(self, category: ErrorCategory) -> List[CodeError]:
        """
        Get errors of a specific category.
        
        Args:
            category: The category of errors to get
            
        Returns:
            A list of errors of the specified category
        """
        return [error for error in self.detect_errors() if error.category == category]
    
    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[CodeError]:
        """
        Get errors of a specific severity.
        
        Args:
            severity: The severity of errors to get
            
        Returns:
            A list of errors of the specified severity
        """
        return [error for error in self.detect_errors() if error.severity == severity]
    
    def get_errors_by_file(self, file_path: str) -> List[CodeError]:
        """
        Get errors in a specific file.
        
        Args:
            file_path: The path to the file
            
        Returns:
            A list of errors in the specified file
        """
        return [error for error in self.detect_errors() if error.file_path == file_path]
    
    def get_errors_by_function(self, function_name: str) -> List[CodeError]:
        """
        Get errors in a specific function.
        
        Args:
            function_name: The name of the function
            
        Returns:
            A list of errors in the specified function
        """
        return [error for error in self.detect_errors() if error.function_name == function_name]


def analyze_errors(codebase: Codebase, context: Optional[CodebaseContext] = None) -> Dict[str, Any]:
    """
    Analyze the codebase for errors.
    
    Args:
        codebase: The codebase to analyze
        context: Optional context for the analysis
        
    Returns:
        A dictionary containing error analysis results
    """
    analyzer = CodeAnalysisError(codebase, context)
    errors = analyzer.detect_errors()
    
    # Group errors by category
    errors_by_category: Dict[str, List[Dict[str, Any]]] = {}
    for error in errors:
        category = error.category.name
        if category not in errors_by_category:
            errors_by_category[category] = []
            
        errors_by_category[category].append({
            "message": error.message,
            "severity": error.severity.name,
            "file_path": error.file_path,
            "function_name": error.function_name,
            "line_number": error.line_number
        })
    
    # Group errors by severity
    errors_by_severity: Dict[str, List[Dict[str, Any]]] = {}
    for error in errors:
        severity = error.severity.name
        if severity not in errors_by_severity:
            errors_by_severity[severity] = []
            
        errors_by_severity[severity].append({
            "message": error.message,
            "category": error.category.name,
            "file_path": error.file_path,
            "function_name": error.function_name,
            "line_number": error.line_number
        })
    
    # Group errors by file
    errors_by_file: Dict[str, List[Dict[str, Any]]] = {}
    for error in errors:
        file_path = error.file_path
        if file_path not in errors_by_file:
            errors_by_file[file_path] = []
            
        errors_by_file[file_path].append({
            "message": error.message,
            "category": error.category.name,
            "severity": error.severity.name,
            "function_name": error.function_name,
            "line_number": error.line_number
        })
    
    return {
        "total_errors": len(errors),
        "errors_by_category": errors_by_category,
        "errors_by_severity": errors_by_severity,
        "errors_by_file": errors_by_file,
        "summary": {
            "critical": len([e for e in errors if e.severity == ErrorSeverity.CRITICAL]),
            "error": len([e for e in errors if e.severity == ErrorSeverity.ERROR]),
            "warning": len([e for e in errors if e.severity == ErrorSeverity.WARNING]),
            "info": len([e for e in errors if e.severity == ErrorSeverity.INFO])
        }
    }

