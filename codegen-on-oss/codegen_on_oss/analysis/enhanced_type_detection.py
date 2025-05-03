"""
Enhanced Type Detection Module for Error Context Analysis

This module provides more robust type detection and analysis capabilities
for the ErrorContextAnalyzer. It uses AST analysis and type inference
to detect potential type errors in code.
"""

import ast
import inspect
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from codegen.sdk.core.function import Function
from codegen_on_oss.analysis.error_context import CodeError, ErrorType, ErrorSeverity


class TypeAnalyzer:
    """
    Analyzes code for type-related errors using AST analysis and type inference.
    """
    
    def __init__(self):
        """Initialize the TypeAnalyzer."""
        # Map of known Python types
        self.python_types = {
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'tuple': tuple,
            'set': set,
            'None': type(None),
        }
        
        # Map of compatible binary operations
        self.compatible_ops = {
            ast.Add: {
                str: [str],
                int: [int, float],
                float: [int, float],
                list: [list],
                tuple: [tuple],
            },
            ast.Sub: {
                int: [int, float],
                float: [int, float],
                set: [set],
            },
            ast.Mult: {
                int: [int, float, str, list, tuple],
                float: [int, float],
                str: [int],
                list: [int],
                tuple: [int],
            },
            ast.Div: {
                int: [int, float],
                float: [int, float],
            },
            # Add more operations as needed
        }
    
    def analyze_function(self, function: Function) -> List[CodeError]:
        """
        Analyze a function for type-related errors.
        
        Args:
            function: The function to analyze
            
        Returns:
            A list of type-related errors
        """
        errors = []
        
        if not hasattr(function, "code_block") or not hasattr(function.code_block, "source"):
            return errors
        
        try:
            # Parse the AST
            tree = ast.parse(function.code_block.source)
            
            # Track variable types based on assignments and annotations
            variable_types = self._collect_variable_types(tree, function)
            
            # Check for type mismatches
            errors.extend(self._check_type_mismatches(tree, variable_types, function))
            
            # Check for parameter type mismatches
            errors.extend(self._check_parameter_types(tree, variable_types, function))
            
            # Check for return type mismatches
            errors.extend(self._check_return_types(tree, variable_types, function))
            
            return errors
        except SyntaxError:
            # If we can't parse the AST, return no errors
            return errors
    
    def _collect_variable_types(self, tree: ast.AST, function: Function) -> Dict[str, Any]:
        """
        Collect variable types from assignments and annotations.
        
        Args:
            tree: The AST to analyze
            function: The function being analyzed
            
        Returns:
            A dictionary mapping variable names to their types
        """
        variable_types = {}
        
        # Add function parameters with type annotations
        if hasattr(function, "parameters"):
            for param in function.parameters:
                if hasattr(param, "type_annotation") and param.type_annotation:
                    variable_types[param.name] = self._parse_type_annotation(param.type_annotation)
        
        # First pass: collect type information from the AST
        for node in ast.walk(tree):
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                # Handle type annotations
                variable_types[node.target.id] = self._get_type_from_annotation(node.annotation)
            elif isinstance(node, ast.Assign):
                # Infer types from assignments where possible
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        inferred_type = self._infer_type_from_value(node.value)
                        if inferred_type:
                            variable_types[target.id] = inferred_type
        
        return variable_types
    
    def _check_type_mismatches(self, tree: ast.AST, variable_types: Dict[str, Any], function: Function) -> List[CodeError]:
        """
        Check for type mismatches in binary operations.
        
        Args:
            tree: The AST to analyze
            variable_types: Dictionary mapping variable names to their types
            function: The function being analyzed
            
        Returns:
            A list of type-related errors
        """
        errors = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp):
                # Check binary operations for type mismatches
                left_type = self._get_expression_type(node.left, variable_types)
                right_type = self._get_expression_type(node.right, variable_types)
                
                if left_type and right_type and not self._are_types_compatible(left_type, right_type, node.op):
                    # Found potential type error
                    line_number = node.lineno
                    errors.append(CodeError(
                        error_type=ErrorType.TYPE_ERROR,
                        message=f"Potential type mismatch: {self._type_name(left_type)} {type(node.op).__name__} {self._type_name(right_type)}",
                        file_path=function.file.name if hasattr(function, "file") else None,
                        line_number=line_number,
                        severity=ErrorSeverity.HIGH,
                        symbol_name=function.name,
                        context_lines=self._get_context_lines(function, line_number),
                        suggested_fix=f"Ensure operands are of compatible types for {type(node.op).__name__} operation"
                    ))
        
        return errors
    
    def _check_parameter_types(self, tree: ast.AST, variable_types: Dict[str, Any], function: Function) -> List[CodeError]:
        """
        Check for parameter type mismatches in function calls.
        
        Args:
            tree: The AST to analyze
            variable_types: Dictionary mapping variable names to their types
            function: The function being analyzed
            
        Returns:
            A list of parameter-related errors
        """
        errors = []
        
        # Get function calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check if we're calling a function we know about
                if isinstance(node.func, ast.Name) and node.func.id in variable_types:
                    # This is a simplification - in a real implementation, we would need to
                    # track function signatures and parameter types
                    pass
        
        return errors
    
    def _check_return_types(self, tree: ast.AST, variable_types: Dict[str, Any], function: Function) -> List[CodeError]:
        """
        Check for return type mismatches.
        
        Args:
            tree: The AST to analyze
            variable_types: Dictionary mapping variable names to their types
            function: The function being analyzed
            
        Returns:
            A list of return-related errors
        """
        errors = []
        
        # Get the declared return type
        declared_return_type = None
        if hasattr(function, "return_type") and function.return_type:
            declared_return_type = self._parse_type_annotation(function.return_type)
        
        if not declared_return_type:
            return errors
        
        # Check return statements
        for node in ast.walk(tree):
            if isinstance(node, ast.Return) and node.value:
                returned_type = self._get_expression_type(node.value, variable_types)
                
                if returned_type and not self._is_return_type_compatible(returned_type, declared_return_type):
                    line_number = node.lineno
                    errors.append(CodeError(
                        error_type=ErrorType.TYPE_ERROR,
                        message=f"Return type mismatch: returning {self._type_name(returned_type)} but function declares {self._type_name(declared_return_type)}",
                        file_path=function.file.name if hasattr(function, "file") else None,
                        line_number=line_number,
                        severity=ErrorSeverity.HIGH,
                        symbol_name=function.name,
                        context_lines=self._get_context_lines(function, line_number),
                        suggested_fix=f"Ensure the return value matches the declared return type {self._type_name(declared_return_type)}"
                    ))
        
        return errors
    
    def _get_expression_type(self, node: ast.AST, variable_types: Dict[str, Any]) -> Optional[Any]:
        """
        Get the type of an expression.
        
        Args:
            node: The AST node representing the expression
            variable_types: Dictionary mapping variable names to their types
            
        Returns:
            The type of the expression, or None if it cannot be determined
        """
        if isinstance(node, ast.Name):
            # Variable reference
            return variable_types.get(node.id)
        elif isinstance(node, ast.Constant):
            # Literal value
            return type(node.value)
        elif isinstance(node, ast.List):
            # List literal
            return list
        elif isinstance(node, ast.Dict):
            # Dict literal
            return dict
        elif isinstance(node, ast.Tuple):
            # Tuple literal
            return tuple
        elif isinstance(node, ast.Set):
            # Set literal
            return set
        elif isinstance(node, ast.BinOp):
            # Binary operation
            left_type = self._get_expression_type(node.left, variable_types)
            right_type = self._get_expression_type(node.right, variable_types)
            
            # Determine result type based on operation and operand types
            # This is a simplification - in a real implementation, we would need more sophisticated type inference
            if isinstance(node.op, ast.Add):
                if left_type == str or right_type == str:
                    return str
                elif left_type in (int, float) and right_type in (int, float):
                    return float if float in (left_type, right_type) else int
                elif left_type == list and right_type == list:
                    return list
                elif left_type == tuple and right_type == tuple:
                    return tuple
            
            # Add more operation type inference as needed
            
        # For other expression types, we can't determine the type
        return None
    
    def _are_types_compatible(self, left_type: Any, right_type: Any, op: ast.operator) -> bool:
        """
        Check if two types are compatible for a binary operation.
        
        Args:
            left_type: The type of the left operand
            right_type: The type of the right operand
            op: The binary operation
            
        Returns:
            True if the types are compatible, False otherwise
        """
        op_type = type(op)
        
        if op_type in self.compatible_ops and left_type in self.compatible_ops[op_type]:
            return right_type in self.compatible_ops[op_type][left_type]
        
        return False
    
    def _is_return_type_compatible(self, actual_type: Any, declared_type: Any) -> bool:
        """
        Check if a return type is compatible with the declared return type.
        
        Args:
            actual_type: The actual return type
            declared_type: The declared return type
            
        Returns:
            True if the types are compatible, False otherwise
        """
        # This is a simplification - in a real implementation, we would need more sophisticated type compatibility checking
        if actual_type == declared_type:
            return True
        
        # Handle numeric types
        if declared_type == float and actual_type == int:
            return True
        
        # Handle None
        if declared_type == type(None) and actual_type == type(None):
            return True
        
        # Handle Union types (simplified)
        if isinstance(declared_type, tuple):
            return actual_type in declared_type
        
        return False
    
    def _get_type_from_annotation(self, annotation: ast.AST) -> Optional[Any]:
        """
        Get a type from an annotation AST node.
        
        Args:
            annotation: The AST node representing the annotation
            
        Returns:
            The type, or None if it cannot be determined
        """
        if isinstance(annotation, ast.Name):
            # Simple type name
            return self.python_types.get(annotation.id)
        elif isinstance(annotation, ast.Subscript):
            # Generic type (e.g., List[int])
            if isinstance(annotation.value, ast.Name):
                if annotation.value.id == 'List':
                    return list
                elif annotation.value.id == 'Dict':
                    return dict
                elif annotation.value.id == 'Tuple':
                    return tuple
                elif annotation.value.id == 'Set':
                    return set
                elif annotation.value.id == 'Optional':
                    # For Optional[T], we return the inner type
                    return self._get_type_from_annotation(annotation.slice)
                elif annotation.value.id == 'Union':
                    # For Union[T1, T2, ...], we return a tuple of types
                    if isinstance(annotation.slice, ast.Tuple):
                        types = [self._get_type_from_annotation(elt) for elt in annotation.slice.elts]
                        return tuple(t for t in types if t is not None)
        
        return None
    
    def _parse_type_annotation(self, type_annotation: str) -> Optional[Any]:
        """
        Parse a type annotation string.
        
        Args:
            type_annotation: The type annotation string
            
        Returns:
            The type, or None if it cannot be parsed
        """
        # This is a simplification - in a real implementation, we would need more sophisticated parsing
        if type_annotation == 'str':
            return str
        elif type_annotation == 'int':
            return int
        elif type_annotation == 'float':
            return float
        elif type_annotation == 'bool':
            return bool
        elif type_annotation == 'list' or type_annotation.startswith('List['):
            return list
        elif type_annotation == 'dict' or type_annotation.startswith('Dict['):
            return dict
        elif type_annotation == 'tuple' or type_annotation.startswith('Tuple['):
            return tuple
        elif type_annotation == 'set' or type_annotation.startswith('Set['):
            return set
        elif type_annotation == 'None':
            return type(None)
        elif type_annotation.startswith('Optional['):
            # Extract the inner type
            inner_type = type_annotation[9:-1]
            return self._parse_type_annotation(inner_type)
        elif type_annotation.startswith('Union['):
            # Extract the union types
            union_types = type_annotation[6:-1].split(', ')
            types = [self._parse_type_annotation(t) for t in union_types]
            return tuple(t for t in types if t is not None)
        
        return None
    
    def _infer_type_from_value(self, node: ast.AST) -> Optional[Any]:
        """
        Infer the type of a value.
        
        Args:
            node: The AST node representing the value
            
        Returns:
            The inferred type, or None if it cannot be determined
        """
        if isinstance(node, ast.Constant):
            return type(node.value)
        elif isinstance(node, ast.List):
            return list
        elif isinstance(node, ast.Dict):
            return dict
        elif isinstance(node, ast.Tuple):
            return tuple
        elif isinstance(node, ast.Set):
            return set
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                # Function call - try to determine the return type
                if node.func.id in self.python_types:
                    return self.python_types[node.func.id]
        
        return None
    
    def _get_context_lines(self, function: Function, line_number: int, context_size: int = 2) -> Dict[int, str]:
        """
        Get context lines around a specific line in a function.
        
        Args:
            function: The function containing the line
            line_number: The line number to get context for
            context_size: Number of lines before and after to include
            
        Returns:
            Dictionary mapping line numbers to line content
        """
        if not hasattr(function, "code_block") or not hasattr(function.code_block, "source"):
            return {}
        
        lines = function.code_block.source.splitlines()
        
        # Adjust line_number to be relative to the function's code block
        if hasattr(function, "line_number"):
            relative_line = line_number - function.line_number
        else:
            relative_line = line_number
        
        start_line = max(0, relative_line - context_size - 1)
        end_line = min(len(lines), relative_line + context_size)
        
        # Map the relative line numbers back to absolute line numbers
        if hasattr(function, "line_number"):
            return {i + function.line_number: lines[i] for i in range(start_line, end_line)}
        else:
            return {i + 1: lines[i] for i in range(start_line, end_line)}
    
    def _type_name(self, type_obj: Any) -> str:
        """
        Get a human-readable name for a type.
        
        Args:
            type_obj: The type object
            
        Returns:
            A string representation of the type
        """
        if type_obj == str:
            return "str"
        elif type_obj == int:
            return "int"
        elif type_obj == float:
            return "float"
        elif type_obj == bool:
            return "bool"
        elif type_obj == list:
            return "list"
        elif type_obj == dict:
            return "dict"
        elif type_obj == tuple:
            return "tuple"
        elif type_obj == set:
            return "set"
        elif type_obj == type(None):
            return "None"
        elif isinstance(type_obj, tuple):
            # Union type
            return f"Union[{', '.join(self._type_name(t) for t in type_obj)}]"
        
        return str(type_obj)


# Example usage
def analyze_function_types(function: Function) -> List[CodeError]:
    """
    Analyze a function for type-related errors.
    
    Args:
        function: The function to analyze
        
    Returns:
        A list of type-related errors
    """
    analyzer = TypeAnalyzer()
    return analyzer.analyze_function(function)

