"""
Type validation module for code analysis.

This module provides classes and functions for validating type annotations,
checking type compatibility, and inferring types for variables and expressions.
"""

from typing import Dict, List, Optional, Set, Tuple, Union, Any

from codegen import Codebase
from codegen.sdk.core.function import Function
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.symbol import Symbol


class TypeValidationError:
    """Represents a type validation error."""
    
    def __init__(
        self,
        message: str,
        file_path: str,
        line_number: Optional[int] = None,
        column_number: Optional[int] = None,
        function_name: Optional[str] = None,
        class_name: Optional[str] = None,
        variable_name: Optional[str] = None,
        expected_type: Optional[str] = None,
        actual_type: Optional[str] = None,
        fix_suggestion: Optional[str] = None
    ):
        """
        Initialize a TypeValidationError.
        
        Args:
            message: A descriptive message about the error
            file_path: Path to the file containing the error
            line_number: Line number where the error occurs (optional)
            column_number: Column number where the error occurs (optional)
            function_name: Name of the function containing the error (optional)
            class_name: Name of the class containing the error (optional)
            variable_name: Name of the variable with the type error (optional)
            expected_type: The expected type (optional)
            actual_type: The actual type (optional)
            fix_suggestion: A suggestion for fixing the error (optional)
        """
        self.message = message
        self.file_path = file_path
        self.line_number = line_number
        self.column_number = column_number
        self.function_name = function_name
        self.class_name = class_name
        self.variable_name = variable_name
        self.expected_type = expected_type
        self.actual_type = actual_type
        self.fix_suggestion = fix_suggestion
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary."""
        return {
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "function_name": self.function_name,
            "class_name": self.class_name,
            "variable_name": self.variable_name,
            "expected_type": self.expected_type,
            "actual_type": self.actual_type,
            "fix_suggestion": self.fix_suggestion
        }
    
    def __str__(self) -> str:
        """String representation of the error."""
        location = f"{self.file_path}"
        if self.line_number:
            location += f":{self.line_number}"
            if self.column_number:
                location += f":{self.column_number}"
        
        context = ""
        if self.function_name:
            context += f" in function '{self.function_name}'"
        if self.class_name:
            context += f" in class '{self.class_name}'"
        if self.variable_name:
            context += f" for variable '{self.variable_name}'"
        
        type_info = ""
        if self.expected_type and self.actual_type:
            type_info = f" (expected: {self.expected_type}, actual: {self.actual_type})"
        
        return f"Type Error: {self.message}{type_info} at {location}{context}"


class TypeAnnotationValidator:
    """Validates type annotations in the codebase."""
    
    def __init__(self, codebase: Codebase):
        """
        Initialize the type annotation validator.
        
        Args:
            codebase: The codebase to analyze
        """
        self.codebase = codebase
        self.errors: List[TypeValidationError] = []
    
    def validate_function_annotations(self, func: Function) -> List[TypeValidationError]:
        """
        Validate type annotations in a function.
        
        Args:
            func: The function to validate
            
        Returns:
            A list of type validation errors
        """
        errors = []
        
        # Check return type annotation
        if not hasattr(func, "return_type") or not func.return_type:
            errors.append(TypeValidationError(
                message="Missing return type annotation",
                file_path=func.filepath,
                function_name=func.name,
                fix_suggestion=f"Add a return type annotation to function '{func.name}'"
            ))
        
        # Check parameter type annotations
        if hasattr(func, "parameters"):
            for param in func.parameters:
                if not hasattr(param, "type_annotation") or not param.type_annotation:
                    # Skip self parameter in methods
                    if param.name == "self" and hasattr(func, "parent") and isinstance(func.parent, Class):
                        continue
                        
                    errors.append(TypeValidationError(
                        message=f"Missing type annotation for parameter '{param.name}'",
                        file_path=func.filepath,
                        function_name=func.name,
                        variable_name=param.name,
                        fix_suggestion=f"Add a type annotation to parameter '{param.name}'"
                    ))
        
        return errors
    
    def validate_variable_annotations(self, func: Function) -> List[TypeValidationError]:
        """
        Validate type annotations for variables in a function.
        
        Args:
            func: The function to validate
            
        Returns:
            A list of type validation errors
        """
        errors = []
        
        if hasattr(func, "variables"):
            for var in func.variables:
                if hasattr(var, "name") and not hasattr(var, "type_annotation"):
                    errors.append(TypeValidationError(
                        message=f"Missing type annotation for variable '{var.name}'",
                        file_path=func.filepath,
                        function_name=func.name,
                        variable_name=var.name,
                        fix_suggestion=f"Add a type annotation to variable '{var.name}'"
                    ))
        
        return errors
    
    def validate_class_annotations(self, cls: Class) -> List[TypeValidationError]:
        """
        Validate type annotations in a class.
        
        Args:
            cls: The class to validate
            
        Returns:
            A list of type validation errors
        """
        errors = []
        
        # Check attribute type annotations
        if hasattr(cls, "attributes"):
            for attr in cls.attributes:
                if hasattr(attr, "name") and not hasattr(attr, "type_annotation"):
                    errors.append(TypeValidationError(
                        message=f"Missing type annotation for attribute '{attr.name}'",
                        file_path=cls.filepath,
                        class_name=cls.name,
                        variable_name=attr.name,
                        fix_suggestion=f"Add a type annotation to attribute '{attr.name}'"
                    ))
        
        # Check method annotations
        if hasattr(cls, "methods"):
            for method in cls.methods:
                method_errors = self.validate_function_annotations(method)
                errors.extend(method_errors)
        
        return errors
    
    def validate_all(self) -> List[TypeValidationError]:
        """
        Validate type annotations in the entire codebase.
        
        Returns:
            A list of all type validation errors
        """
        self.errors = []
        
        # Validate functions
        for func in self.codebase.functions:
            self.errors.extend(self.validate_function_annotations(func))
            self.errors.extend(self.validate_variable_annotations(func))
        
        # Validate classes
        for cls in self.codebase.classes:
            self.errors.extend(self.validate_class_annotations(cls))
        
        return self.errors
    
    def get_annotation_coverage(self) -> Dict[str, float]:
        """
        Calculate type annotation coverage for the codebase.
        
        Returns:
            A dictionary with coverage percentages for different elements
        """
        # Count functions with return type annotations
        total_functions = len(list(self.codebase.functions))
        functions_with_return_type = 0
        
        for func in self.codebase.functions:
            if hasattr(func, "return_type") and func.return_type:
                functions_with_return_type += 1
        
        # Count parameters with type annotations
        total_parameters = 0
        parameters_with_type = 0
        
        for func in self.codebase.functions:
            if hasattr(func, "parameters"):
                for param in func.parameters:
                    # Skip self parameter in methods
                    if param.name == "self" and hasattr(func, "parent") and isinstance(func.parent, Class):
                        continue
                        
                    total_parameters += 1
                    if hasattr(param, "type_annotation") and param.type_annotation:
                        parameters_with_type += 1
        
        # Count variables with type annotations
        total_variables = 0
        variables_with_type = 0
        
        for func in self.codebase.functions:
            if hasattr(func, "variables"):
                for var in func.variables:
                    total_variables += 1
                    if hasattr(var, "type_annotation") and var.type_annotation:
                        variables_with_type += 1
        
        # Count class attributes with type annotations
        total_attributes = 0
        attributes_with_type = 0
        
        for cls in self.codebase.classes:
            if hasattr(cls, "attributes"):
                for attr in cls.attributes:
                    total_attributes += 1
                    if hasattr(attr, "type_annotation") and attr.type_annotation:
                        attributes_with_type += 1
        
        # Calculate coverage percentages
        function_coverage = (functions_with_return_type / total_functions * 100) if total_functions > 0 else 0
        parameter_coverage = (parameters_with_type / total_parameters * 100) if total_parameters > 0 else 0
        variable_coverage = (variables_with_type / total_variables * 100) if total_variables > 0 else 0
        attribute_coverage = (attributes_with_type / total_attributes * 100) if total_attributes > 0 else 0
        
        # Calculate overall coverage
        total_elements = total_functions + total_parameters + total_variables + total_attributes
        total_with_type = functions_with_return_type + parameters_with_type + variables_with_type + attributes_with_type
        overall_coverage = (total_with_type / total_elements * 100) if total_elements > 0 else 0
        
        return {
            "overall": overall_coverage,
            "functions": function_coverage,
            "parameters": parameter_coverage,
            "variables": variable_coverage,
            "attributes": attribute_coverage
        }


class TypeCompatibilityChecker:
    """Checks type compatibility in the codebase."""
    
    def __init__(self, codebase: Codebase):
        """
        Initialize the type compatibility checker.
        
        Args:
            codebase: The codebase to analyze
        """
        self.codebase = codebase
        self.errors: List[TypeValidationError] = []
    
    def check_assignment_compatibility(self, func: Function) -> List[TypeValidationError]:
        """
        Check type compatibility in assignments within a function.
        
        Args:
            func: The function to check
            
        Returns:
            A list of type validation errors
        """
        errors = []
        
        # This is a simplified implementation
        # A proper implementation would use AST analysis to check all assignments
        if hasattr(func, "code_block") and hasattr(func.code_block, "source"):
            source_lines = func.code_block.source.splitlines()
            
            for i, line in enumerate(source_lines):
                line = line.strip()
                
                # Check for assignments with type annotations
                if ":" in line and "=" in line and not line.startswith(("#", "\"\"\"", "'''", "def ", "class ")):
                    parts = line.split(":", 1)
                    var_name = parts[0].strip()
                    
                    # Extract type annotation
                    type_parts = parts[1].split("=", 1)
                    type_annotation = type_parts[0].strip()
                    
                    # Extract assigned value
                    if len(type_parts) > 1:
                        value = type_parts[1].strip()
                        
                        # Simple type checking for literals
                        if type_annotation == "int" and (value.startswith("\"") or value.startswith("'")):
                            errors.append(TypeValidationError(
                                message=f"Type mismatch in assignment",
                                file_path=func.filepath,
                                line_number=i + 1,  # +1 because line numbers are 1-based
                                function_name=func.name,
                                variable_name=var_name,
                                expected_type=type_annotation,
                                actual_type="str",
                                fix_suggestion=f"Ensure the assigned value is of type '{type_annotation}'"
                            ))
                        elif type_annotation == "str" and value.isdigit():
                            errors.append(TypeValidationError(
                                message=f"Type mismatch in assignment",
                                file_path=func.filepath,
                                line_number=i + 1,
                                function_name=func.name,
                                variable_name=var_name,
                                expected_type=type_annotation,
                                actual_type="int",
                                fix_suggestion=f"Ensure the assigned value is of type '{type_annotation}'"
                            ))
        
        return errors
    
    def check_return_compatibility(self, func: Function) -> List[TypeValidationError]:
        """
        Check type compatibility in return statements within a function.
        
        Args:
            func: The function to check
            
        Returns:
            A list of type validation errors
        """
        errors = []
        
        if not hasattr(func, "return_type") or not func.return_type or not hasattr(func, "return_statements"):
            return errors
            
        return_type = func.return_type
        
        for ret in func.return_statements:
            if hasattr(ret, "value") and hasattr(ret.value, "type_annotation") and ret.value.type_annotation:
                ret_type = ret.value.type_annotation
                
                # Check if return type matches declared return type
                if ret_type != return_type:
                    errors.append(TypeValidationError(
                        message=f"Return type mismatch",
                        file_path=func.filepath,
                        function_name=func.name,
                        expected_type=return_type,
                        actual_type=ret_type,
                        fix_suggestion=f"Ensure the return value is of type '{return_type}'"
                    ))
        
        return errors
    
    def check_parameter_compatibility(self, func: Function) -> List[TypeValidationError]:
        """
        Check type compatibility in function calls within a function.
        
        Args:
            func: The function to check
            
        Returns:
            A list of type validation errors
        """
        errors = []
        
        if not hasattr(func, "function_calls"):
            return errors
            
        for call in func.function_calls:
            if hasattr(call, "target") and hasattr(call.target, "parameters"):
                for i, arg in enumerate(call.arguments):
                    if i < len(call.target.parameters) and hasattr(arg, "type_annotation") and hasattr(call.target.parameters[i], "type_annotation"):
                        arg_type = arg.type_annotation
                        param_type = call.target.parameters[i].type_annotation
                        
                        if arg_type and param_type and arg_type != param_type:
                            errors.append(TypeValidationError(
                                message=f"Argument type mismatch",
                                file_path=func.filepath,
                                function_name=func.name,
                                variable_name=call.target.parameters[i].name,
                                expected_type=param_type,
                                actual_type=arg_type,
                                fix_suggestion=f"Ensure the argument is of type '{param_type}'"
                            ))
        
        return errors
    
    def check_all(self) -> List[TypeValidationError]:
        """
        Check type compatibility in the entire codebase.
        
        Returns:
            A list of all type validation errors
        """
        self.errors = []
        
        for func in self.codebase.functions:
            self.errors.extend(self.check_assignment_compatibility(func))
            self.errors.extend(self.check_return_compatibility(func))
            self.errors.extend(self.check_parameter_compatibility(func))
        
        return self.errors


class TypeInference:
    """Infers types for variables and expressions in the codebase."""
    
    def __init__(self, codebase: Codebase):
        """
        Initialize the type inference engine.
        
        Args:
            codebase: The codebase to analyze
        """
        self.codebase = codebase
        self.inferred_types: Dict[str, Dict[str, str]] = {}
    
    def infer_variable_types(self, func: Function) -> Dict[str, str]:
        """
        Infer types for variables in a function.
        
        Args:
            func: The function to analyze
            
        Returns:
            A dictionary mapping variable names to inferred types
        """
        inferred = {}
        
        if not hasattr(func, "code_block") or not hasattr(func.code_block, "source"):
            return inferred
            
        source_lines = func.code_block.source.splitlines()
        
        for line in source_lines:
            line = line.strip()
            
            # Infer types from assignments
            if "=" in line and not line.startswith(("#", "\"\"\"", "'''", "def ", "class ", "if ", "for ", "while ")):
                parts = line.split("=", 1)
                var_name = parts[0].strip()
                value = parts[1].strip()
                
                # Infer type from literal values
                if value.isdigit():
                    inferred[var_name] = "int"
                elif value.startswith("\"") or value.startswith("'"):
                    inferred[var_name] = "str"
                elif value in ("True", "False"):
                    inferred[var_name] = "bool"
                elif value.startswith("[") and value.endswith("]"):
                    inferred[var_name] = "list"
                elif value.startswith("{") and value.endswith("}"):
                    if ":" in value:
                        inferred[var_name] = "dict"
                    else:
                        inferred[var_name] = "set"
                elif value.startswith("(") and value.endswith(")"):
                    inferred[var_name] = "tuple"
                elif value == "None":
                    inferred[var_name] = "None"
        
        return inferred
    
    def infer_all_types(self) -> Dict[str, Dict[str, str]]:
        """
        Infer types for variables in all functions.
        
        Returns:
            A dictionary mapping function names to dictionaries of inferred types
        """
        self.inferred_types = {}
        
        for func in self.codebase.functions:
            if hasattr(func, "name"):
                self.inferred_types[func.name] = self.infer_variable_types(func)
        
        return self.inferred_types
    
    def suggest_type_annotations(self) -> Dict[str, Dict[str, str]]:
        """
        Suggest type annotations for variables without annotations.
        
        Returns:
            A dictionary mapping function names to dictionaries of suggested types
        """
        suggestions = {}
        
        # Infer types for all variables
        self.infer_all_types()
        
        for func in self.codebase.functions:
            if not hasattr(func, "name") or not hasattr(func, "variables"):
                continue
                
            func_suggestions = {}
            
            for var in func.variables:
                if hasattr(var, "name") and not hasattr(var, "type_annotation"):
                    var_name = var.name
                    
                    # Check if we have an inferred type for this variable
                    if func.name in self.inferred_types and var_name in self.inferred_types[func.name]:
                        func_suggestions[var_name] = self.inferred_types[func.name][var_name]
            
            if func_suggestions:
                suggestions[func.name] = func_suggestions
        
        return suggestions


class TypeValidation:
    """Main class for type validation."""
    
    def __init__(self, codebase: Codebase):
        """
        Initialize the type validator.
        
        Args:
            codebase: The codebase to analyze
        """
        self.codebase = codebase
        self.annotation_validator = TypeAnnotationValidator(codebase)
        self.compatibility_checker = TypeCompatibilityChecker(codebase)
        self.type_inference = TypeInference(codebase)
    
    def validate_annotations(self) -> List[TypeValidationError]:
        """
        Validate type annotations in the codebase.
        
        Returns:
            A list of type validation errors
        """
        return self.annotation_validator.validate_all()
    
    def check_compatibility(self) -> List[TypeValidationError]:
        """
        Check type compatibility in the codebase.
        
        Returns:
            A list of type validation errors
        """
        return self.compatibility_checker.check_all()
    
    def infer_types(self) -> Dict[str, Dict[str, str]]:
        """
        Infer types for variables in the codebase.
        
        Returns:
            A dictionary of inferred types
        """
        return self.type_inference.infer_all_types()
    
    def suggest_annotations(self) -> Dict[str, Dict[str, str]]:
        """
        Suggest type annotations for variables without annotations.
        
        Returns:
            A dictionary of suggested type annotations
        """
        return self.type_inference.suggest_type_annotations()
    
    def get_annotation_coverage(self) -> Dict[str, float]:
        """
        Get type annotation coverage for the codebase.
        
        Returns:
            A dictionary with coverage percentages
        """
        return self.annotation_validator.get_annotation_coverage()
    
    def validate_all(self) -> Dict[str, Any]:
        """
        Perform comprehensive type validation.
        
        Returns:
            A dictionary with all validation results
        """
        return {
            "annotation_errors": [error.to_dict() for error in self.validate_annotations()],
            "compatibility_errors": [error.to_dict() for error in self.check_compatibility()],
            "inferred_types": self.infer_types(),
            "suggested_annotations": self.suggest_annotations(),
            "annotation_coverage": self.get_annotation_coverage()
        }

