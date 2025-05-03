"""
Type validation module for code analysis.

This module provides classes and functions for validating types in code,
including type annotation validation, type compatibility checks, and type inference.
"""

from enum import Enum, auto
from typing import Dict, List, Set, Any, Optional, Union, Tuple
from dataclasses import dataclass

from codegen import Codebase
from codegen.sdk.core.function import Function
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.core.variable import Variable
from codegen_on_oss.analysis.codebase_context import CodebaseContext


class TypeIssue(Enum):
    """Types of type validation issues."""
    MISSING_ANNOTATION = auto()
    TYPE_MISMATCH = auto()
    INCOMPATIBLE_TYPES = auto()
    INCONSISTENT_RETURN_TYPE = auto()
    INVALID_TYPE_ANNOTATION = auto()


@dataclass
class TypeValidationError:
    """
    Represents a type validation error.
    
    Attributes:
        issue: The type of issue
        message: A descriptive message about the error
        file_path: Path to the file containing the error
        line_number: Line number where the error occurs (optional)
        function_name: Name of the function containing the error (optional)
        symbol_name: Name of the symbol related to the error (optional)
    """
    issue: TypeIssue
    message: str
    file_path: str
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    symbol_name: Optional[str] = None


class TypeValidator:
    """
    Validates types in code.
    
    This class provides methods for validating type annotations, checking type
    compatibility, and identifying type-related issues.
    """
    
    def __init__(self, codebase: Codebase, context: Optional[CodebaseContext] = None):
        """
        Initialize the type validator.
        
        Args:
            codebase: The codebase to analyze
            context: Optional context for the analysis
        """
        self.codebase = codebase
        self.context = context
        self.errors: List[TypeValidationError] = []
    
    def validate_types(self) -> List[TypeValidationError]:
        """
        Validate types in the codebase.
        
        Returns:
            A list of type validation errors
        """
        self.errors = []
        
        # Validate function parameter and return types
        self._validate_function_types()
        
        # Validate variable types
        self._validate_variable_types()
        
        return self.errors
    
    def _validate_function_types(self) -> None:
        """Validate function parameter and return types."""
        for function in self.codebase.functions:
            # Check for missing return type annotation
            if not hasattr(function, "return_type") or not function.return_type:
                self.errors.append(TypeValidationError(
                    issue=TypeIssue.MISSING_ANNOTATION,
                    message=f"Function '{function.name}' is missing a return type annotation",
                    file_path=function.filepath,
                    function_name=function.name
                ))
            
            # Check parameter type annotations
            if hasattr(function, "parameters"):
                for param in function.parameters:
                    if not hasattr(param, "type_annotation") or not param.type_annotation:
                        self.errors.append(TypeValidationError(
                            issue=TypeIssue.MISSING_ANNOTATION,
                            message=f"Parameter '{param.name}' in function '{function.name}' is missing a type annotation",
                            file_path=function.filepath,
                            function_name=function.name
                        ))
            
            # Check for inconsistent return types
            if hasattr(function, "code_block") and hasattr(function, "return_type"):
                return_types = set()
                for stmt in function.code_block.statements:
                    if hasattr(stmt, "type") and stmt.type == "return_statement" and hasattr(stmt, "value") and hasattr(stmt.value, "type"):
                        return_types.add(stmt.value.type)
                
                if len(return_types) > 1:
                    self.errors.append(TypeValidationError(
                        issue=TypeIssue.INCONSISTENT_RETURN_TYPE,
                        message=f"Function '{function.name}' has inconsistent return types: {', '.join(return_types)}",
                        file_path=function.filepath,
                        function_name=function.name
                    ))
    
    def _validate_variable_types(self) -> None:
        """Validate variable types."""
        for function in self.codebase.functions:
            if not hasattr(function, "code_block"):
                continue
                
            # Check variable declarations
            for var in function.code_block.variable_declarations:
                # Check for missing type annotation
                if not hasattr(var, "type_annotation") or not var.type_annotation:
                    self.errors.append(TypeValidationError(
                        issue=TypeIssue.MISSING_ANNOTATION,
                        message=f"Variable '{var.name}' in function '{function.name}' is missing a type annotation",
                        file_path=function.filepath,
                        function_name=function.name
                    ))
                
                # Check for type mismatches
                if hasattr(var, "type_annotation") and hasattr(var, "initializer") and hasattr(var.initializer, "type"):
                    if var.type_annotation != var.initializer.type:
                        self.errors.append(TypeValidationError(
                            issue=TypeIssue.TYPE_MISMATCH,
                            message=f"Type mismatch for variable '{var.name}' in function '{function.name}': declared as '{var.type_annotation}', initialized with '{var.initializer.type}'",
                            file_path=function.filepath,
                            function_name=function.name
                        ))
    
    def get_errors_by_issue(self, issue: TypeIssue) -> List[TypeValidationError]:
        """
        Get errors of a specific issue type.
        
        Args:
            issue: The type of issue to filter by
            
        Returns:
            A list of errors of the specified issue type
        """
        return [error for error in self.errors if error.issue == issue]
    
    def get_errors_by_file(self, file_path: str) -> List[TypeValidationError]:
        """
        Get errors in a specific file.
        
        Args:
            file_path: The path to the file
            
        Returns:
            A list of errors in the specified file
        """
        return [error for error in self.errors if error.file_path == file_path]
    
    def get_errors_by_function(self, function_name: str) -> List[TypeValidationError]:
        """
        Get errors in a specific function.
        
        Args:
            function_name: The name of the function
            
        Returns:
            A list of errors in the specified function
        """
        return [error for error in self.errors if error.function_name == function_name]


class TypeInferenceEngine:
    """
    Infers types for variables and expressions.
    
    This class provides methods for inferring types based on usage patterns
    and context.
    """
    
    def __init__(self, codebase: Codebase, context: Optional[CodebaseContext] = None):
        """
        Initialize the type inference engine.
        
        Args:
            codebase: The codebase to analyze
            context: Optional context for the analysis
        """
        self.codebase = codebase
        self.context = context
        self.inferred_types: Dict[str, Dict[str, str]] = {}  # function_name -> {variable_name: type}
    
    def infer_types(self) -> Dict[str, Dict[str, str]]:
        """
        Infer types for variables in the codebase.
        
        Returns:
            A dictionary mapping function names to dictionaries mapping variable names to inferred types
        """
        self.inferred_types = {}
        
        for function in self.codebase.functions:
            if not hasattr(function, "code_block"):
                continue
                
            self.inferred_types[function.name] = {}
            
            # Infer types from variable declarations with initializers
            for var in function.code_block.variable_declarations:
                if hasattr(var, "initializer") and hasattr(var.initializer, "type"):
                    self.inferred_types[function.name][var.name] = var.initializer.type
            
            # Infer types from assignments
            for stmt in function.code_block.statements:
                if hasattr(stmt, "type") and stmt.type == "assignment" and hasattr(stmt, "left") and hasattr(stmt, "right"):
                    if hasattr(stmt.left, "name") and hasattr(stmt.right, "type"):
                        self.inferred_types[function.name][stmt.left.name] = stmt.right.type
            
            # Infer types from function calls
            for call in function.code_block.function_calls:
                if hasattr(call, "target") and hasattr(call, "name"):
                    # Find the called function
                    called_function = None
                    for f in self.codebase.functions:
                        if f.name == call.name:
                            called_function = f
                            break
                    
                    if called_function and hasattr(called_function, "return_type"):
                        self.inferred_types[function.name][call.target] = called_function.return_type
        
        return self.inferred_types
    
    def get_inferred_type(self, function_name: str, variable_name: str) -> Optional[str]:
        """
        Get the inferred type for a variable in a function.
        
        Args:
            function_name: The name of the function
            variable_name: The name of the variable
            
        Returns:
            The inferred type, or None if the type could not be inferred
        """
        if not self.inferred_types:
            self.infer_types()
            
        return self.inferred_types.get(function_name, {}).get(variable_name)
    
    def get_inferred_types_for_function(self, function_name: str) -> Dict[str, str]:
        """
        Get all inferred types for variables in a function.
        
        Args:
            function_name: The name of the function
            
        Returns:
            A dictionary mapping variable names to inferred types
        """
        if not self.inferred_types:
            self.infer_types()
            
        return self.inferred_types.get(function_name, {})


def analyze_types(codebase: Codebase, context: Optional[CodebaseContext] = None) -> Dict[str, Any]:
    """
    Analyze types in the codebase.
    
    Args:
        codebase: The codebase to analyze
        context: Optional context for the analysis
        
    Returns:
        A dictionary containing type analysis results
    """
    validator = TypeValidator(codebase, context)
    inference_engine = TypeInferenceEngine(codebase, context)
    
    # Validate types
    errors = validator.validate_types()
    
    # Infer types
    inferred_types = inference_engine.infer_types()
    
    # Group errors by issue type
    errors_by_issue: Dict[str, List[Dict[str, Any]]] = {}
    for error in errors:
        issue = error.issue.name
        if issue not in errors_by_issue:
            errors_by_issue[issue] = []
            
        errors_by_issue[issue].append({
            "message": error.message,
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
            "issue": error.issue.name,
            "function_name": error.function_name,
            "line_number": error.line_number
        })
    
    # Collect type statistics
    type_stats = {
        "functions_with_return_type": 0,
        "functions_without_return_type": 0,
        "parameters_with_type": 0,
        "parameters_without_type": 0,
        "variables_with_type": 0,
        "variables_without_type": 0
    }
    
    for function in codebase.functions:
        if hasattr(function, "return_type") and function.return_type:
            type_stats["functions_with_return_type"] += 1
        else:
            type_stats["functions_without_return_type"] += 1
            
        if hasattr(function, "parameters"):
            for param in function.parameters:
                if hasattr(param, "type_annotation") and param.type_annotation:
                    type_stats["parameters_with_type"] += 1
                else:
                    type_stats["parameters_without_type"] += 1
                    
        if hasattr(function, "code_block"):
            for var in function.code_block.variable_declarations:
                if hasattr(var, "type_annotation") and var.type_annotation:
                    type_stats["variables_with_type"] += 1
                else:
                    type_stats["variables_without_type"] += 1
    
    return {
        "validation": {
            "total_errors": len(errors),
            "errors_by_issue": errors_by_issue,
            "errors_by_file": errors_by_file
        },
        "inference": {
            "inferred_types": inferred_types
        },
        "statistics": type_stats
    }

