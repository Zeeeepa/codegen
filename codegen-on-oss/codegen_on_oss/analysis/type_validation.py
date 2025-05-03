"""
Type Validation Module for Codegen-on-OSS

This module provides type checking and validation capabilities for Python codebases,
focusing on type annotations, type inference, and type compatibility.
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


class TypeValidationError(Enum):
    """Types of type validation errors."""
    INCOMPATIBLE_TYPES = auto()
    MISSING_TYPE_ANNOTATION = auto()
    INCONSISTENT_RETURN_TYPE = auto()
    INVALID_TYPE_ANNOTATION = auto()
    UNUSED_TYPE_IMPORT = auto()
    INCORRECT_GENERIC_USAGE = auto()
    TYPE_NARROWING_ISSUE = auto()


@dataclass
class TypeIssue:
    """Represents a type-related issue in the code."""
    error_type: TypeValidationError
    message: str
    file_path: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    code_snippet: Optional[str] = None
    suggested_fix: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the issue to a dictionary representation."""
        return {
            "error_type": self.error_type.name,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "function_name": self.function_name,
            "class_name": self.class_name,
            "code_snippet": self.code_snippet,
            "suggested_fix": self.suggested_fix
        }
    
    def __str__(self) -> str:
        """String representation of the issue."""
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
        
        return f"[{self.error_type.name}] {self.message} at {location}{context}"


class TypeValidator:
    """Validates type annotations and type compatibility in a codebase."""
    
    def __init__(self, codebase: Codebase, context: Optional[CodebaseContext] = None):
        """Initialize the type validator.
        
        Args:
            codebase: The Codebase object to analyze
            context: Optional CodebaseContext for additional analysis capabilities
        """
        self.codebase = codebase
        self.context = context
        self.issues: List[TypeIssue] = []
        
        # Common Python types
        self.builtin_types = {
            "str", "int", "float", "bool", "list", "dict", "tuple", "set", "frozenset",
            "bytes", "bytearray", "memoryview", "complex", "None", "Any", "Optional",
            "Union", "List", "Dict", "Tuple", "Set", "FrozenSet", "Callable", "Type",
            "Sequence", "Mapping", "Iterable", "Iterator", "Generator", "Coroutine",
            "AsyncIterable", "AsyncIterator", "ContextManager", "AsyncContextManager"
        }
    
    def validate_types(self) -> List[TypeIssue]:
        """Validate type annotations and compatibility in the codebase.
        
        Returns:
            A list of type issues
        """
        self.issues = []
        
        # Validate function parameter and return types
        for function in self.codebase.functions:
            self._validate_function_types(function)
        
        # Validate class attribute types
        for cls in self.codebase.classes:
            self._validate_class_types(cls)
        
        return self.issues
    
    def _validate_function_types(self, function: Function) -> None:
        """Validate type annotations in a function.
        
        Args:
            function: The function to validate
        """
        # Check for missing return type annotation
        if not hasattr(function, "return_type") or not function.return_type:
            # Skip if it's a special method like __init__
            if not function.name.startswith("__") or function.name == "__call__":
                self.issues.append(TypeIssue(
                    error_type=TypeValidationError.MISSING_TYPE_ANNOTATION,
                    message=f"Function '{function.name}' is missing a return type annotation",
                    file_path=function.filepath,
                    line_number=function.line_number,
                    function_name=function.name,
                    class_name=function.class_name if hasattr(function, "class_name") else None
                ))
        
        # Check parameter type annotations
        for param in function.parameters:
            if not param.type_annotation and not param.name.startswith("_"):
                self.issues.append(TypeIssue(
                    error_type=TypeValidationError.MISSING_TYPE_ANNOTATION,
                    message=f"Parameter '{param.name}' in function '{function.name}' is missing a type annotation",
                    file_path=function.filepath,
                    line_number=function.line_number,
                    function_name=function.name,
                    class_name=function.class_name if hasattr(function, "class_name") else None
                ))
            elif param.type_annotation:
                self._validate_type_annotation(param.type_annotation, function)
        
        # Check return type annotation if present
        if hasattr(function, "return_type") and function.return_type:
            self._validate_type_annotation(function.return_type, function)
        
        # Check for inconsistent return types
        if hasattr(function, "return_statements") and function.return_statements:
            self._check_return_type_consistency(function)
    
    def _validate_class_types(self, cls: Class) -> None:
        """Validate type annotations in a class.
        
        Args:
            cls: The class to validate
        """
        # Check attribute type annotations
        for attr in cls.attributes:
            if not attr.type_annotation and not attr.name.startswith("_"):
                self.issues.append(TypeIssue(
                    error_type=TypeValidationError.MISSING_TYPE_ANNOTATION,
                    message=f"Attribute '{attr.name}' in class '{cls.name}' is missing a type annotation",
                    file_path=cls.filepath,
                    line_number=attr.line_number if hasattr(attr, "line_number") else cls.line_number,
                    class_name=cls.name
                ))
            elif attr.type_annotation:
                self._validate_type_annotation(attr.type_annotation, cls)
    
    def _validate_type_annotation(self, type_annotation: str, context_symbol: Union[Function, Class]) -> None:
        """Validate a type annotation string.
        
        Args:
            type_annotation: The type annotation string to validate
            context_symbol: The function or class containing the annotation
        """
        # Check for invalid type annotations
        if type_annotation not in self.builtin_types:
            # Check if it's a valid user-defined type
            if not self._is_valid_user_type(type_annotation):
                self.issues.append(TypeIssue(
                    error_type=TypeValidationError.INVALID_TYPE_ANNOTATION,
                    message=f"Type annotation '{type_annotation}' may not be a valid type",
                    file_path=context_symbol.filepath,
                    line_number=context_symbol.line_number,
                    function_name=context_symbol.name if isinstance(context_symbol, Function) else None,
                    class_name=context_symbol.name if isinstance(context_symbol, Class) else getattr(context_symbol, "class_name", None)
                ))
        
        # Check for incorrect generic usage
        if self._has_incorrect_generic_usage(type_annotation):
            self.issues.append(TypeIssue(
                error_type=TypeValidationError.INCORRECT_GENERIC_USAGE,
                message=f"Incorrect generic usage in type annotation '{type_annotation}'",
                file_path=context_symbol.filepath,
                line_number=context_symbol.line_number,
                function_name=context_symbol.name if isinstance(context_symbol, Function) else None,
                class_name=context_symbol.name if isinstance(context_symbol, Class) else getattr(context_symbol, "class_name", None)
            ))
    
    def _is_valid_user_type(self, type_name: str) -> bool:
        """Check if a type name refers to a valid user-defined type.
        
        Args:
            type_name: The type name to check
            
        Returns:
            True if the type is valid, False otherwise
        """
        # Remove generic parameters if present
        base_type = type_name.split("[")[0].split(".")[-1]
        
        # Check if it's a class in the codebase
        for cls in self.codebase.classes:
            if cls.name == base_type:
                return True
        
        # Check if it's imported
        for imp in self.codebase.imports:
            if imp.imported_name == base_type:
                return True
        
        # It might be a valid type that we can't verify
        return True
    
    def _has_incorrect_generic_usage(self, type_annotation: str) -> bool:
        """Check if a type annotation has incorrect generic usage.
        
        Args:
            type_annotation: The type annotation to check
            
        Returns:
            True if the generic usage is incorrect, False otherwise
        """
        # Check for unbalanced brackets
        if type_annotation.count("[") != type_annotation.count("]"):
            return True
        
        # Check for common generic types
        generic_types = ["List", "Dict", "Tuple", "Set", "FrozenSet", "Optional", "Union", "Callable"]
        for generic in generic_types:
            if type_annotation.startswith(f"{generic}[") and type_annotation.endswith("]"):
                # Check specific rules for each generic type
                if generic == "Dict" and "," not in type_annotation:
                    return True
                if generic == "Tuple" and not ("," in type_annotation or "..." in type_annotation):
                    return True
                if generic == "Callable" and "[" in type_annotation and "]" in type_annotation:
                    # Callable[[arg1, arg2], return_type]
                    if type_annotation.count("[") < 2 or type_annotation.count("]") < 2:
                        return True
        
        return False
    
    def _check_return_type_consistency(self, function: Function) -> None:
        """Check if return statements are consistent with the declared return type.
        
        Args:
            function: The function to check
        """
        if not hasattr(function, "return_type") or not function.return_type:
            return
        
        # Skip if return type is Any or similar
        if function.return_type in ["Any", "Optional", "Union"]:
            return
        
        # Check each return statement
        for stmt in function.return_statements:
            if not hasattr(stmt, "value") or not stmt.value:
                # Return None
                if function.return_type not in ["None", "Optional", "Any"]:
                    self.issues.append(TypeIssue(
                        error_type=TypeValidationError.INCONSISTENT_RETURN_TYPE,
                        message=f"Return statement without value is inconsistent with declared return type '{function.return_type}'",
                        file_path=function.filepath,
                        line_number=stmt.line_number if hasattr(stmt, "line_number") else function.line_number,
                        function_name=function.name,
                        class_name=function.class_name if hasattr(function, "class_name") else None
                    ))
            elif hasattr(stmt.value, "type"):
                # Check if return value type matches declared type
                value_type = stmt.value.type
                if value_type and value_type != function.return_type:
                    self.issues.append(TypeIssue(
                        error_type=TypeValidationError.INCONSISTENT_RETURN_TYPE,
                        message=f"Return value of type '{value_type}' is inconsistent with declared return type '{function.return_type}'",
                        file_path=function.filepath,
                        line_number=stmt.line_number if hasattr(stmt, "line_number") else function.line_number,
                        function_name=function.name,
                        class_name=function.class_name if hasattr(function, "class_name") else None
                    ))


class TypeInferenceEngine:
    """Infers types for variables and expressions in a codebase."""
    
    def __init__(self, codebase: Codebase, context: Optional[CodebaseContext] = None):
        """Initialize the type inference engine.
        
        Args:
            codebase: The Codebase object to analyze
            context: Optional CodebaseContext for additional analysis capabilities
        """
        self.codebase = codebase
        self.context = context
        self.type_map: Dict[str, Dict[str, str]] = {}  # file_path -> {symbol_name -> type}
    
    def infer_types(self) -> Dict[str, Dict[str, str]]:
        """Infer types for variables and expressions in the codebase.
        
        Returns:
            A dictionary mapping file paths to dictionaries mapping symbol names to inferred types
        """
        self.type_map = {}
        
        # Process all functions
        for function in self.codebase.functions:
            file_path = function.filepath
            if file_path not in self.type_map:
                self.type_map[file_path] = {}
            
            # Add function return type
            if hasattr(function, "return_type") and function.return_type:
                self.type_map[file_path][function.name] = function.return_type
            
            # Add parameter types
            for param in function.parameters:
                if param.type_annotation:
                    param_key = f"{function.name}.{param.name}"
                    self.type_map[file_path][param_key] = param.type_annotation
            
            # Infer types in function body
            if hasattr(function, "code_block") and function.code_block:
                self._infer_types_in_block(function.code_block, function, file_path)
        
        # Process all classes
        for cls in self.codebase.classes:
            file_path = cls.filepath
            if file_path not in self.type_map:
                self.type_map[file_path] = {}
            
            # Add class type
            self.type_map[file_path][cls.name] = "Type"
            
            # Add attribute types
            for attr in cls.attributes:
                if attr.type_annotation:
                    attr_key = f"{cls.name}.{attr.name}"
                    self.type_map[file_path][attr_key] = attr.type_annotation
        
        return self.type_map
    
    def _infer_types_in_block(self, block: Any, function: Function, file_path: str) -> None:
        """Infer types for variables in a code block.
        
        Args:
            block: The code block to analyze
            function: The function containing the block
            file_path: The file path for context
        """
        if not hasattr(block, "statements"):
            return
        
        for stmt in block.statements:
            # Handle assignments
            if hasattr(stmt, "type") and stmt.type == "assignment":
                if hasattr(stmt, "left") and hasattr(stmt, "right"):
                    # Infer type from right side
                    right_type = self._infer_expression_type(stmt.right, file_path)
                    if right_type and hasattr(stmt.left, "name"):
                        var_key = f"{function.name}.{stmt.left.name}"
                        self.type_map[file_path][var_key] = right_type
            
            # Handle nested blocks
            if isinstance(stmt, IfBlockStatement):
                for block in stmt.blocks:
                    self._infer_types_in_block(block, function, file_path)
            elif isinstance(stmt, ForLoopStatement) and hasattr(stmt, "body"):
                self._infer_types_in_block(stmt.body, function, file_path)
            elif isinstance(stmt, WhileStatement) and hasattr(stmt, "body"):
                self._infer_types_in_block(stmt.body, function, file_path)
            elif isinstance(stmt, TryCatchStatement):
                if hasattr(stmt, "try_block"):
                    self._infer_types_in_block(stmt.try_block, function, file_path)
                if hasattr(stmt, "catch_blocks"):
                    for catch_block in stmt.catch_blocks:
                        self._infer_types_in_block(catch_block, function, file_path)
                if hasattr(stmt, "finally_block"):
                    self._infer_types_in_block(stmt.finally_block, function, file_path)
    
    def _infer_expression_type(self, expr: Any, file_path: str) -> Optional[str]:
        """Infer the type of an expression.
        
        Args:
            expr: The expression to analyze
            file_path: The file path for context
            
        Returns:
            The inferred type as a string, or None if the type cannot be inferred
        """
        # Handle literals
        if hasattr(expr, "type"):
            if expr.type == "string_literal":
                return "str"
            elif expr.type == "number_literal":
                # Check if it's an integer or float
                if hasattr(expr, "value"):
                    try:
                        int(expr.value)
                        return "int"
                    except ValueError:
                        try:
                            float(expr.value)
                            return "float"
                        except ValueError:
                            pass
            elif expr.type == "boolean_literal":
                return "bool"
            elif expr.type == "null_literal":
                return "None"
            elif expr.type == "array_literal":
                return "List"
            elif expr.type == "object_literal":
                return "Dict"
        
        # Handle variables
        if hasattr(expr, "name"):
            # Check if it's a known variable
            for key, type_str in self.type_map.get(file_path, {}).items():
                if key.endswith(f".{expr.name}"):
                    return type_str
            
            # Check if it's a function
            for function in self.codebase.functions:
                if function.name == expr.name:
                    return function.return_type if hasattr(function, "return_type") else None
            
            # Check if it's a class
            for cls in self.codebase.classes:
                if cls.name == expr.name:
                    return "Type"
        
        # Handle function calls
        if hasattr(expr, "type") and expr.type == "call_expression":
            if hasattr(expr, "callee") and hasattr(expr.callee, "name"):
                # Try to find the function
                for function in self.codebase.functions:
                    if function.name == expr.callee.name:
                        return function.return_type if hasattr(function, "return_type") else None
        
        # Handle binary expressions
        if isinstance(expr, BinaryExpression):
            # Infer based on operator and operands
            if hasattr(expr, "operators") and expr.operators:
                op = expr.operators[0].source if hasattr(expr.operators[0], "source") else None
                if op in ["+", "-", "*", "/", "%", "**"]:
                    # Numeric operations
                    return "float"
                elif op in ["==", "!=", "<", ">", "<=", ">=", "and", "or", "not"]:
                    # Boolean operations
                    return "bool"
        
        return None


def analyze_types(codebase: Codebase, context: Optional[CodebaseContext] = None) -> Dict[str, Any]:
    """Analyze types in a codebase and return comprehensive results.
    
    Args:
        codebase: The Codebase object to analyze
        context: Optional CodebaseContext for additional analysis capabilities
        
    Returns:
        A dictionary containing type analysis results
    """
    # Create analyzers
    validator = TypeValidator(codebase, context)
    inference = TypeInferenceEngine(codebase, context)
    
    # Validate types
    issues = validator.validate_types()
    
    # Infer types
    inferred_types = inference.infer_types()
    
    # Group issues by type
    issues_by_type = {}
    for issue in issues:
        error_type = issue.error_type.name
        if error_type not in issues_by_type:
            issues_by_type[error_type] = []
        issues_by_type[error_type].append(issue.to_dict())
    
    # Group issues by file
    issues_by_file = {}
    for issue in issues:
        file_path = issue.file_path
        if file_path not in issues_by_file:
            issues_by_file[file_path] = []
        issues_by_file[file_path].append(issue.to_dict())
    
    # Compute summary statistics
    summary = {
        "total_issues": len(issues),
        "issues_by_type": {error_type: len(issues) for error_type, issues in issues_by_type.items()},
        "files_with_issues": len(issues_by_file),
    }
    
    # Return the complete analysis
    return {
        "summary": summary,
        "issues_by_type": issues_by_type,
        "issues_by_file": issues_by_file,
        "all_issues": [issue.to_dict() for issue in issues],
        "inferred_types": inferred_types
    }

