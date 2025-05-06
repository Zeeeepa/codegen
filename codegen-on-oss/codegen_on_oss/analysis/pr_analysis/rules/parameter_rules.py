"""
Parameter validation rules for PR static analysis.

This module defines rules for detecting parameter validation issues such as
parameter type mismatches, missing required parameters, and incorrect parameter usage.
"""

import ast
import inspect
import importlib
import os
import sys
from typing import List, Dict, Any, Optional, Set, Tuple, Union, get_type_hints

from .base_rule import BaseRule, AnalysisResult


class ParameterTypeMismatchRule(BaseRule):
    """Rule for detecting parameter type mismatches in function calls."""
    
    def __init__(self):
        """Initialize the parameter type mismatch rule."""
        super().__init__(
            rule_id="PV001",
            name="Parameter Type Mismatch Check",
            description="Checks for parameter type mismatches in function calls."
        )
        
    def apply(self, context) -> List[AnalysisResult]:
        """
        Apply the rule to the context and return results.
        
        Args:
            context: Analysis context containing PR data and utilities
            
        Returns:
            List of analysis results
        """
        results = []
        for file_path, change_type in context.get_file_changes().items():
            if change_type in ["added", "modified"] and file_path.endswith(".py"):
                file_content = context.head_context.get_file_content(file_path)
                type_mismatches = self._check_type_mismatches(file_path, file_content, context)
                results.extend(type_mismatches)
        return results
        
    def _check_type_mismatches(self, file_path: str, content: str, context) -> List[AnalysisResult]:
        """
        Check for parameter type mismatches in function calls.
        
        Args:
            file_path: Path to the file being checked
            content: Content of the file
            context: Analysis context
            
        Returns:
            List of analysis results
        """
        results = []
        try:
            tree = ast.parse(content, filename=file_path)
            visitor = ParameterTypeVisitor(file_path, context)
            visitor.visit(tree)
            
            for call_node, func_name, param_name, expected_type, actual_type in visitor.type_mismatches:
                results.append(AnalysisResult(
                    rule_id=self.rule_id,
                    severity="warning",
                    message=f"Parameter type mismatch in call to '{func_name}': "
                            f"parameter '{param_name}' expected type '{expected_type}', "
                            f"got '{actual_type}'",
                    file=file_path,
                    line=call_node.lineno,
                    column=call_node.col_offset,
                    details={
                        "error_type": "parameter_type_mismatch",
                        "function_name": func_name,
                        "parameter_name": param_name,
                        "expected_type": str(expected_type),
                        "actual_type": str(actual_type)
                    }
                ))
        except SyntaxError:
            # Syntax errors will be caught by the SyntaxErrorRule
            pass
        
        return results


class ParameterTypeVisitor(ast.NodeVisitor):
    """AST visitor for finding parameter type mismatches."""
    
    def __init__(self, file_path: str, context):
        """
        Initialize the visitor.
        
        Args:
            file_path: Path to the file being checked
            context: Analysis context
        """
        self.file_path = file_path
        self.context = context
        self.type_mismatches: List[Tuple[ast.Call, str, str, str, str]] = []
        self.function_defs: Dict[str, Tuple[ast.arguments, Dict[str, str]]] = {}
        
    def visit_FunctionDef(self, node):
        """Visit a FunctionDef node."""
        # Extract type hints from function definition
        type_hints = {}
        for arg in node.args.args:
            if arg.annotation:
                type_hints[arg.arg] = self._annotation_to_type(arg.annotation)
        
        self.function_defs[node.name] = (node.args, type_hints)
        self.generic_visit(node)
        
    def visit_Call(self, node):
        """Visit a Call node."""
        # Check if this is a call to a function we have type hints for
        func_name = self._get_func_name(node.func)
        if func_name in self.function_defs:
            args, type_hints = self.function_defs[func_name]
            
            # Check positional arguments
            for i, arg in enumerate(node.args):
                if i < len(args.args):
                    param_name = args.args[i].arg
                    if param_name in type_hints:
                        expected_type = type_hints[param_name]
                        actual_type = self._infer_type(arg)
                        if actual_type and not self._is_compatible_type(expected_type, actual_type):
                            self.type_mismatches.append((node, func_name, param_name, expected_type, actual_type))
            
            # Check keyword arguments
            for kw in node.keywords:
                if kw.arg in type_hints:
                    expected_type = type_hints[kw.arg]
                    actual_type = self._infer_type(kw.value)
                    if actual_type and not self._is_compatible_type(expected_type, actual_type):
                        self.type_mismatches.append((node, func_name, kw.arg, expected_type, actual_type))
        
        self.generic_visit(node)
        
    def _get_func_name(self, node):
        """Get the name of a function from a node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return None
        
    def _annotation_to_type(self, annotation):
        """Convert an annotation node to a type."""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Attribute):
            return f"{self._get_attribute_full_name(annotation)}"
        elif isinstance(annotation, ast.Subscript):
            return f"{self._annotation_to_type(annotation.value)}[{self._annotation_to_type(annotation.slice)}]"
        return str(annotation)
        
    def _get_attribute_full_name(self, node):
        """Get the full name of an attribute."""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attribute_full_name(node.value)}.{node.attr}"
        return node.attr
        
    def _infer_type(self, node):
        """Infer the type of a node."""
        if isinstance(node, ast.Num):
            return type(node.n).__name__
        elif isinstance(node, ast.Str):
            return "str"
        elif isinstance(node, ast.List):
            return "list"
        elif isinstance(node, ast.Dict):
            return "dict"
        elif isinstance(node, ast.Set):
            return "set"
        elif isinstance(node, ast.Tuple):
            return "tuple"
        elif isinstance(node, ast.NameConstant):
            if node.value is None:
                return "None"
            return type(node.value).__name__
        elif isinstance(node, ast.Name):
            # This is a simplification; in a real implementation, we would need
            # to track variable assignments and their types
            if node.id == "True" or node.id == "False":
                return "bool"
            elif node.id == "None":
                return "None"
        return None
        
    def _is_compatible_type(self, expected_type, actual_type):
        """Check if an actual type is compatible with an expected type."""
        # This is a simplification; in a real implementation, we would need
        # to handle more complex type compatibility checks
        if expected_type == actual_type:
            return True
        if expected_type == "Any" or actual_type == "Any":
            return True
        if expected_type == "Optional" and actual_type == "None":
            return True
        if expected_type.startswith("Optional[") and actual_type == "None":
            return True
        if expected_type == "Union" and actual_type in expected_type:
            return True
        return False


class MissingParameterRule(BaseRule):
    """Rule for detecting missing required parameters in function calls."""
    
    def __init__(self):
        """Initialize the missing parameter rule."""
        super().__init__(
            rule_id="PV002",
            name="Missing Parameter Check",
            description="Checks for missing required parameters in function calls."
        )
        
    def apply(self, context) -> List[AnalysisResult]:
        """
        Apply the rule to the context and return results.
        
        Args:
            context: Analysis context containing PR data and utilities
            
        Returns:
            List of analysis results
        """
        results = []
        for file_path, change_type in context.get_file_changes().items():
            if change_type in ["added", "modified"] and file_path.endswith(".py"):
                file_content = context.head_context.get_file_content(file_path)
                missing_params = self._check_missing_parameters(file_path, file_content, context)
                results.extend(missing_params)
        return results
        
    def _check_missing_parameters(self, file_path: str, content: str, context) -> List[AnalysisResult]:
        """
        Check for missing required parameters in function calls.
        
        Args:
            file_path: Path to the file being checked
            content: Content of the file
            context: Analysis context
            
        Returns:
            List of analysis results
        """
        results = []
        try:
            tree = ast.parse(content, filename=file_path)
            visitor = MissingParameterVisitor(file_path, context)
            visitor.visit(tree)
            
            for call_node, func_name, missing_params in visitor.missing_parameters:
                missing_params_str = ", ".join(missing_params)
                results.append(AnalysisResult(
                    rule_id=self.rule_id,
                    severity="error",
                    message=f"Missing required parameters in call to '{func_name}': {missing_params_str}",
                    file=file_path,
                    line=call_node.lineno,
                    column=call_node.col_offset,
                    details={
                        "error_type": "missing_parameter",
                        "function_name": func_name,
                        "missing_parameters": missing_params
                    }
                ))
        except SyntaxError:
            # Syntax errors will be caught by the SyntaxErrorRule
            pass
        
        return results


class MissingParameterVisitor(ast.NodeVisitor):
    """AST visitor for finding missing required parameters."""
    
    def __init__(self, file_path: str, context):
        """
        Initialize the visitor.
        
        Args:
            file_path: Path to the file being checked
            context: Analysis context
        """
        self.file_path = file_path
        self.context = context
        self.missing_parameters: List[Tuple[ast.Call, str, List[str]]] = []
        self.function_defs: Dict[str, Tuple[List[str], List[ast.expr], List[str], List[ast.expr]]] = {}
        
    def visit_FunctionDef(self, node):
        """Visit a FunctionDef node."""
        # Extract parameter information from function definition
        args = [arg.arg for arg in node.args.args]
        defaults = node.args.defaults
        kwonlyargs = [arg.arg for arg in node.args.kwonlyargs]
        kw_defaults = node.args.kw_defaults
        
        self.function_defs[node.name] = (args, defaults, kwonlyargs, kw_defaults)
        self.generic_visit(node)
        
    def visit_Call(self, node):
        """Visit a Call node."""
        # Check if this is a call to a function we have parameter information for
        func_name = self._get_func_name(node.func)
        if func_name in self.function_defs:
            args, defaults, kwonlyargs, kw_defaults = self.function_defs[func_name]
            
            # Calculate required positional parameters
            num_required_args = len(args) - len(defaults)
            required_args = args[:num_required_args]
            
            # Calculate required keyword-only parameters
            required_kwonlyargs = [
                kwonlyargs[i] for i in range(len(kwonlyargs))
                if i >= len(kw_defaults) or kw_defaults[i] is None
            ]
            
            # Check if all required parameters are provided
            provided_args = len(node.args)
            provided_kwargs = {kw.arg for kw in node.keywords}
            
            missing_required_args = []
            
            # Check positional arguments
            if provided_args < num_required_args:
                missing_required_args.extend(required_args[provided_args:])
            
            # Check keyword-only arguments
            for kwarg in required_kwonlyargs:
                if kwarg not in provided_kwargs:
                    missing_required_args.append(kwarg)
            
            if missing_required_args:
                self.missing_parameters.append((node, func_name, missing_required_args))
        
        self.generic_visit(node)
        
    def _get_func_name(self, node):
        """Get the name of a function from a node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return None


class IncorrectParameterUsageRule(BaseRule):
    """Rule for detecting incorrect parameter usage in function calls."""
    
    def __init__(self):
        """Initialize the incorrect parameter usage rule."""
        super().__init__(
            rule_id="PV003",
            name="Incorrect Parameter Usage Check",
            description="Checks for incorrect parameter usage in function calls."
        )
        
    def apply(self, context) -> List[AnalysisResult]:
        """
        Apply the rule to the context and return results.
        
        Args:
            context: Analysis context containing PR data and utilities
            
        Returns:
            List of analysis results
        """
        results = []
        for file_path, change_type in context.get_file_changes().items():
            if change_type in ["added", "modified"] and file_path.endswith(".py"):
                file_content = context.head_context.get_file_content(file_path)
                incorrect_usages = self._check_incorrect_parameter_usage(file_path, file_content, context)
                results.extend(incorrect_usages)
        return results
        
    def _check_incorrect_parameter_usage(self, file_path: str, content: str, context) -> List[AnalysisResult]:
        """
        Check for incorrect parameter usage in function calls.
        
        Args:
            file_path: Path to the file being checked
            content: Content of the file
            context: Analysis context
            
        Returns:
            List of analysis results
        """
        results = []
        try:
            tree = ast.parse(content, filename=file_path)
            visitor = IncorrectParameterUsageVisitor(file_path, context)
            visitor.visit(tree)
            
            for call_node, func_name, param_name, issue in visitor.incorrect_usages:
                results.append(AnalysisResult(
                    rule_id=self.rule_id,
                    severity="warning",
                    message=f"Incorrect parameter usage in call to '{func_name}': {issue}",
                    file=file_path,
                    line=call_node.lineno,
                    column=call_node.col_offset,
                    details={
                        "error_type": "incorrect_parameter_usage",
                        "function_name": func_name,
                        "parameter_name": param_name,
                        "issue": issue
                    }
                ))
        except SyntaxError:
            # Syntax errors will be caught by the SyntaxErrorRule
            pass
        
        return results


class IncorrectParameterUsageVisitor(ast.NodeVisitor):
    """AST visitor for finding incorrect parameter usage."""
    
    def __init__(self, file_path: str, context):
        """
        Initialize the visitor.
        
        Args:
            file_path: Path to the file being checked
            context: Analysis context
        """
        self.file_path = file_path
        self.context = context
        self.incorrect_usages: List[Tuple[ast.Call, str, Optional[str], str]] = []
        self.function_defs: Dict[str, Tuple[List[str], List[str], Optional[str], Optional[str]]] = {}
        
    def visit_FunctionDef(self, node):
        """Visit a FunctionDef node."""
        # Extract parameter information from function definition
        args = [arg.arg for arg in node.args.args]
        kwonlyargs = [arg.arg for arg in node.args.kwonlyargs]
        vararg = node.args.vararg.arg if node.args.vararg else None
        kwarg = node.args.kwarg.arg if node.args.kwarg else None
        
        self.function_defs[node.name] = (args, kwonlyargs, vararg, kwarg)
        self.generic_visit(node)
        
    def visit_Call(self, node):
        """Visit a Call node."""
        # Check if this is a call to a function we have parameter information for
        func_name = self._get_func_name(node.func)
        if func_name in self.function_defs:
            args, kwonlyargs, vararg, kwarg = self.function_defs[func_name]
            
            # Check for duplicate keyword arguments
            seen_kwargs = set()
            for kw in node.keywords:
                if kw.arg is not None:  # None means **kwargs
                    if kw.arg in seen_kwargs:
                        self.incorrect_usages.append(
                            (node, func_name, kw.arg, f"duplicate keyword argument '{kw.arg}'")
                        )
                    seen_kwargs.add(kw.arg)
            
            # Check for unknown keyword arguments
            all_params = set(args + kwonlyargs)
            for kw in node.keywords:
                if kw.arg is not None and kw.arg not in all_params and kwarg is None:
                    self.incorrect_usages.append(
                        (node, func_name, kw.arg, f"unknown keyword argument '{kw.arg}'")
                    )
            
            # Check for positional arguments after keyword arguments
            if node.keywords and node.args and not all(kw.arg is None for kw in node.keywords):
                # This is a simplification; in a real implementation, we would need
                # to check if the positional arguments after keywords are valid
                pass
            
            # Check for too many positional arguments
            if len(node.args) > len(args) and vararg is None:
                self.incorrect_usages.append(
                    (node, func_name, None, f"too many positional arguments")
                )
        
        self.generic_visit(node)
        
    def _get_func_name(self, node):
        """Get the name of a function from a node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return None
