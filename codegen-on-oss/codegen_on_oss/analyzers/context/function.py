#!/usr/bin/env python3
"""
Function Context Module

This module provides a specialized context for function-level analysis,
including parameters, return types, complexity, and call relationships.
"""

import logging
import sys
from typing import Any

try:
    from codegen.sdk.core.function import Function
    from codegen.sdk.core.symbol import Symbol
    from codegen.sdk.enums import EdgeType
except ImportError:
    print("Codegen SDK not found. Please install it first.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class FunctionContext:
    """
    Context for function-level analysis.

    This class provides specialized analysis capabilities for a single function,
    including parameter analysis, return type analysis, complexity analysis,
    and call relationship analysis.
    """

    def __init__(self, function: Function):
        """
        Initialize the FunctionContext.

        Args:
            function: The function to analyze
        """
        self.function = function
        self.name = function.name if hasattr(function, "name") else str(function)
        self.file = function.file if hasattr(function, "file") else None
        self.file_path = (
            function.file.file_path
            if hasattr(function, "file") and hasattr(function.file, "file_path")
            else "unknown"
        )
        self.line = function.line if hasattr(function, "line") else None
        self.parameters = (
            list(function.parameters) if hasattr(function, "parameters") else []
        )
        self.return_type = (
            function.return_type if hasattr(function, "return_type") else None
        )
        self.is_async = function.is_async if hasattr(function, "is_async") else False
        self.source = function.source if hasattr(function, "source") else ""
        self.call_sites = (
            list(function.call_sites) if hasattr(function, "call_sites") else []
        )
        self.locals = []

        # Extract local variables if available
        if hasattr(function, "code_block") and hasattr(
            function.code_block, "local_var_assignments"
        ):
            self.locals = list(function.code_block.local_var_assignments)

    def get_parameter(self, name: str) -> Any | None:
        """
        Get a parameter by name.

        Args:
            name: Name of the parameter to get

        Returns:
            The parameter, or None if not found
        """
        for param in self.parameters:
            if hasattr(param, "name") and param.name == name:
                return param
        return None

    def get_parameter_types(self) -> dict[str, Any]:
        """
        Get parameter types.

        Returns:
            Dictionary mapping parameter names to types
        """
        result = {}
        for param in self.parameters:
            if hasattr(param, "name"):
                param_type = param.type if hasattr(param, "type") else None
                result[param.name] = str(param_type) if param_type else None
        return result

    def get_called_functions(self) -> list[Any]:
        """
        Get functions called by this function.

        Returns:
            List of called functions
        """
        result = []
        for call_site in self.call_sites:
            if hasattr(call_site, "called_function"):
                result.append(call_site.called_function)
        return result

    def analyze_complexity(self) -> dict[str, Any]:
        """
        Analyze function complexity.

        Returns:
            Dictionary containing complexity metrics
        """
        result = {
            "name": self.name,
            "file": self.file_path,
            "line": self.line,
            "cyclomatic_complexity": self._calculate_cyclomatic_complexity(),
            "line_count": len(self.source.split("\n")) if self.source else 0,
            "parameter_count": len(self.parameters),
            "nesting_depth": self._calculate_nesting_depth(),
        }

        return result

    def _calculate_cyclomatic_complexity(self) -> int:
        """
        Calculate cyclomatic complexity of the function.

        Returns:
            Cyclomatic complexity score
        """
        if not self.source:
            return 1

        complexity = 1  # Base complexity

        # Count branching statements
        complexity += self.source.count("if ")
        complexity += self.source.count("elif ")
        complexity += self.source.count("for ")
        complexity += self.source.count("while ")
        complexity += self.source.count("except:")
        complexity += self.source.count("except ")
        complexity += self.source.count(" and ")
        complexity += self.source.count(" or ")
        complexity += self.source.count("case ")

        return complexity

    def _calculate_nesting_depth(self) -> int:
        """
        Calculate the maximum nesting depth of the function.

        Returns:
            Maximum nesting depth
        """
        if not self.source:
            return 0

        lines = self.source.split("\n")
        max_indent = 0

        for line in lines:
            if line.strip():  # Skip empty lines
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent)

        # Estimate nesting depth (rough approximation)
        est_nesting_depth = max_indent // 4  # Assuming 4 spaces per indent level

        return est_nesting_depth

    def analyze_parameters(self) -> dict[str, Any]:
        """
        Analyze function parameters.

        Returns:
            Dictionary containing parameter analysis
        """
        result = {
            "total_parameters": len(self.parameters),
            "typed_parameters": 0,
            "untyped_parameters": 0,
            "default_parameters": 0,
            "parameter_details": [],
        }

        for param in self.parameters:
            param_info = {
                "name": param.name if hasattr(param, "name") else str(param),
                "type": str(param.type)
                if hasattr(param, "type") and param.type
                else None,
                "has_default": param.has_default
                if hasattr(param, "has_default")
                else False,
                "position": param.position if hasattr(param, "position") else None,
            }

            # Update counts
            if param_info["type"]:
                result["typed_parameters"] += 1
            else:
                result["untyped_parameters"] += 1

            if param_info["has_default"]:
                result["default_parameters"] += 1

            result["parameter_details"].append(param_info)

        return result

    def analyze_return_type(self) -> dict[str, Any]:
        """
        Analyze function return type.

        Returns:
            Dictionary containing return type analysis
        """
        return {
            "has_return_type": self.return_type is not None,
            "return_type": str(self.return_type) if self.return_type else None,
            "return_type_category": self._categorize_return_type(),
        }

    def _categorize_return_type(self) -> str:
        """
        Categorize the return type.

        Returns:
            Category of the return type
        """
        if not self.return_type:
            return "untyped"

        type_str = str(self.return_type).lower()

        if "none" in type_str:
            return "none"
        elif "bool" in type_str:
            return "boolean"
        elif "int" in type_str or "float" in type_str or "number" in type_str:
            return "numeric"
        elif "str" in type_str or "string" in type_str:
            return "string"
        elif "list" in type_str or "array" in type_str:
            return "list"
        elif "dict" in type_str or "map" in type_str:
            return "dictionary"
        elif "tuple" in type_str:
            return "tuple"
        elif "union" in type_str or "|" in type_str:
            return "union"
        elif "callable" in type_str or "function" in type_str:
            return "callable"
        else:
            return "complex"

    def analyze_call_sites(self) -> dict[str, Any]:
        """
        Analyze function call sites.

        Returns:
            Dictionary containing call site analysis
        """
        result = {
            "total_call_sites": len(self.call_sites),
            "calls_by_function": {},
            "calls_by_file": {},
        }

        for call_site in self.call_sites:
            # Get called function
            called_function = None
            if hasattr(call_site, "called_function"):
                called_function = call_site.called_function

            # Skip if no called function
            if not called_function:
                continue

            # Get function name
            func_name = (
                called_function.name
                if hasattr(called_function, "name")
                else str(called_function)
            )

            # Update calls by function
            if func_name not in result["calls_by_function"]:
                result["calls_by_function"][func_name] = 0
            result["calls_by_function"][func_name] += 1

            # Get file
            file_path = "unknown"
            if hasattr(call_site, "file") and hasattr(call_site.file, "file_path"):
                file_path = call_site.file.file_path

            # Update calls by file
            if file_path not in result["calls_by_file"]:
                result["calls_by_file"][file_path] = 0
            result["calls_by_file"][file_path] += 1

        return result

    def analyze_usage_patterns(self) -> dict[str, Any]:
        """
        Analyze function usage patterns.

        Returns:
            Dictionary containing usage pattern analysis
        """
        result = {
            "uses_async_await": self.is_async or "await " in self.source,
            "uses_exceptions": "try:" in self.source
            or "except:" in self.source
            or "except " in self.source,
            "uses_loops": "for " in self.source or "while " in self.source,
            "uses_conditionals": "if " in self.source
            or "elif " in self.source
            or "else:" in self.source,
            "uses_comprehensions": "[" in self.source
            and "for" in self.source
            and "]" in self.source,
            "uses_generators": "yield " in self.source,
            "uses_decorators": hasattr(self.function, "decorators")
            and bool(self.function.decorators),
        }

        return result

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the function context to a dictionary.

        Returns:
            Dictionary representation of the function context
        """
        return {
            "name": self.name,
            "file_path": self.file_path,
            "line": self.line,
            "is_async": self.is_async,
            "parameters": [
                param.name if hasattr(param, "name") else str(param)
                for param in self.parameters
            ],
            "return_type": str(self.return_type) if self.return_type else None,
            "complexity": self._calculate_cyclomatic_complexity(),
            "line_count": len(self.source.split("\n")) if self.source else 0,
            "nesting_depth": self._calculate_nesting_depth(),
            "local_variables": [
                local.name if hasattr(local, "name") else str(local)
                for local in self.locals
            ],
            "call_sites_count": len(self.call_sites),
        }
