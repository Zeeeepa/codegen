"""
Error detection module for code analysis.

This module provides classes and functions for detecting errors in code,
including parameter validation, call validation, and return validation.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from codegen import Codebase

from codegen_on_oss.analysis.codebase_context import CodebaseContext


class ErrorSeverity(Enum):
    """Severity levels for detected errors."""

    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class ErrorCategory(Enum):
    """Categories of errors that can be detected."""

    PARAMETER_ERROR = auto()
    CALL_ERROR = auto()
    RETURN_ERROR = auto()
    CODE_QUALITY = auto()
    SECURITY = auto()
    PERFORMANCE = auto()


@dataclass
class DetectedError:
    """
    Represents an error detected in the code.

    Attributes:
        category: The category of the error
        severity: The severity of the error
        message: A descriptive message about the error
        file_path: Path to the file containing the error
        line_number: Line number where the error occurs (optional)
        function_name: Name of the function containing the error (optional)
        code_snippet: Snippet of code containing the error (optional)
    """

    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    file_path: str
    line_number: int | None = None
    function_name: str | None = None
    code_snippet: str | None = None


class ErrorDetector:
    """
    Base class for error detectors.

    This class provides common functionality for detecting errors in code.
    Subclasses should implement the detect_errors method.
    """

    def __init__(
        self, codebase: Codebase, context: CodebaseContext | None = None
    ):
        """
        Initialize the error detector.

        Args:
            codebase: The codebase to analyze
            context: Optional context for the analysis
        """
        self.codebase = codebase
        self.context = context
        self.errors: list[DetectedError] = []

    def detect_errors(self) -> list[DetectedError]:
        """
        Detect errors in the codebase.

        Returns:
            A list of detected errors
        """
        raise NotImplementedError(
            "Subclasses must implement detect_errors method"
        )


class ParameterValidator(ErrorDetector):
    """
    Validates function parameters.

    This class detects errors related to function parameters, such as unused
    parameters, parameter count mismatches, and missing required parameters.
    """

    def detect_errors(self) -> list[DetectedError]:
        """
        Detect parameter-related errors in the codebase.

        Returns:
            A list of detected errors
        """
        self.errors = []

        # Check for unused parameters
        self._check_unused_parameters()

        # Check for parameter count mismatches
        self._check_parameter_count_mismatches()

        # Check for missing required parameters
        self._check_missing_required_parameters()

        return self.errors

    def _check_unused_parameters(self) -> None:
        """Check for unused parameters in functions."""
        for function in self.codebase.functions:
            if not hasattr(function, "parameters") or not function.parameters:
                continue

            # Get parameter names
            param_names = {param.name for param in function.parameters}

            # Get used variable names
            used_names = set()
            if hasattr(function, "code_block") and hasattr(
                function.code_block, "variable_references"
            ):
                used_names = {
                    ref.name for ref in function.code_block.variable_references
                }

            # Find unused parameters
            unused = param_names - used_names
            for param_name in unused:
                self.errors.append(
                    DetectedError(
                        category=ErrorCategory.PARAMETER_ERROR,
                        severity=ErrorSeverity.WARNING,
                        message=(
                            f"Unused parameter '{param_name}' in function "
                            f"'{function.name}'"
                        ),
                        file_path=function.filepath,
                        function_name=function.name,
                    )
                )

    def _check_parameter_count_mismatches(self) -> None:
        """Check for parameter count mismatches in function calls."""
        for function in self.codebase.functions:
            if not hasattr(function, "code_block"):
                continue

            for call in function.code_block.function_calls:
                # Find the called function
                called_function = None
                for f in self.codebase.functions:
                    if f.name == call.name:
                        called_function = f
                        break

                if not called_function or not hasattr(
                    called_function, "parameters"
                ):
                    continue

                # Check parameter count
                if hasattr(call, "arguments") and len(call.arguments) != len(
                    called_function.parameters
                ):
                    self.errors.append(
                        DetectedError(
                            category=ErrorCategory.CALL_ERROR,
                            severity=ErrorSeverity.ERROR,
                            message=(
                                f"Function '{call.name}' called with "
                                f"{len(call.arguments)} arguments but "
                                f"expects {len(called_function.parameters)}"
                            ),
                            file_path=function.filepath,
                            function_name=function.name,
                        )
                    )

    def _check_missing_required_parameters(self) -> None:
        """Check for missing required parameters in function calls."""
        for function in self.codebase.functions:
            if not hasattr(function, "code_block"):
                continue

            for call in function.code_block.function_calls:
                # Find the called function
                called_function = None
                for f in self.codebase.functions:
                    if f.name == call.name:
                        called_function = f
                        break

                if (
                    not called_function
                    or not hasattr(called_function, "parameters")
                    or not hasattr(call, "arguments")
                ):
                    continue

                # Get required parameter names
                required_params = {
                    param.name
                    for param in called_function.parameters
                    if not hasattr(param, "default_value")
                    or param.default_value is None
                }

                # Get provided argument names
                provided_args = {arg.name for arg in call.arguments}

                # Find missing required parameters
                missing = required_params - provided_args
                if missing:
                    self.errors.append(
                        DetectedError(
                            category=ErrorCategory.CALL_ERROR,
                            severity=ErrorSeverity.ERROR,
                            message=(
                                f"Call to function '{call.name}' is missing "
                                f"required parameters: {', '.join(missing)}"
                            ),
                            file_path=function.filepath,
                            function_name=function.name,
                        )
                    )


class CallValidator(ErrorDetector):
    """
    Validates function calls.

    This class detects errors related to function calls, such as circular
    dependencies and potential exceptions.
    """

    def detect_errors(self) -> list[DetectedError]:
        """
        Detect call-related errors in the codebase.

        Returns:
            A list of detected errors
        """
        self.errors = []

        # Check for circular dependencies
        self._check_circular_dependencies()

        # Check for potential exceptions
        self._check_potential_exceptions()

        return self.errors

    def _check_circular_dependencies(self) -> None:
        """Check for circular dependencies between functions."""
        # Build call graph
        call_graph = {}
        for function in self.codebase.functions:
            call_graph[function.name] = set()
            if hasattr(function, "code_block"):
                for call in function.code_block.function_calls:
                    call_graph[function.name].add(call.name)

        # Check for cycles
        for function_name in call_graph:
            visited = set()
            path = []

            def dfs(node: str) -> bool:
                if node in path:
                    cycle = path[path.index(node):] + [node]
                    self.errors.append(
                        DetectedError(
                            category=ErrorCategory.CALL_ERROR,
                            severity=ErrorSeverity.WARNING,
                            message=(
                                "Circular dependency detected: "
                                f"{' -> '.join(cycle)}"
                            ),
                            file_path="",  # No specific file
                            function_name=node,
                        )
                    )
                    return True

                if node in visited:
                    return False

                visited.add(node)
                path.append(node)

                for callee in call_graph.get(node, set()):
                    if callee in call_graph and dfs(callee):
                        return True

                path.pop()
                return False

            dfs(function_name)

    def _check_potential_exceptions(self) -> None:
        """Check for potential exceptions in function calls."""
        # This is a simplified implementation
        # In a real implementation, we would check for common error patterns
        for function in self.codebase.functions:
            if not hasattr(function, "code_block"):
                continue

            for call in function.code_block.function_calls:
                # Check for division by zero
                if (
                    call.name == "divide"
                    and hasattr(call, "arguments")
                    and len(call.arguments) >= 2
                    and hasattr(call.arguments[1], "value")
                    and call.arguments[1].value == 0
                ):
                    self.errors.append(
                        DetectedError(
                            category=ErrorCategory.CALL_ERROR,
                            severity=ErrorSeverity.ERROR,
                            message="Potential division by zero",
                            file_path=function.filepath,
                            function_name=function.name,
                        )
                    )


class ReturnValidator(ErrorDetector):
    """
    Validates function returns.

    This class detects errors related to function returns, such as inconsistent
    return types and values.
    """

    def detect_errors(self) -> list[DetectedError]:
        """
        Detect return-related errors in the codebase.

        Returns:
            A list of detected errors
        """
        self.errors = []

        # Check for inconsistent return types
        self._check_inconsistent_return_types()

        # Check for missing return statements
        self._check_missing_return_statements()

        return self.errors

    def _check_inconsistent_return_types(self) -> None:
        """Check for inconsistent return types in functions."""
        for function in self.codebase.functions:
            if not hasattr(function, "code_block") or not hasattr(
                function, "return_type"
            ):
                continue

            return_types = set()
            for stmt in function.code_block.statements:
                if (
                    hasattr(stmt, "type")
                    and stmt.type == "return_statement"
                    and hasattr(stmt, "value")
                    and hasattr(stmt.value, "type")
                ):
                    return_types.add(stmt.value.type)

            if len(return_types) > 1:
                self.errors.append(
                    DetectedError(
                        category=ErrorCategory.RETURN_ERROR,
                        severity=ErrorSeverity.ERROR,
                        message=(
                            f"Function '{function.name}' has inconsistent "
                            f"return types: {', '.join(return_types)}"
                        ),
                        file_path=function.filepath,
                        function_name=function.name,
                    )
                )

    def _check_missing_return_statements(self) -> None:
        """Check for missing return statements in functions."""
        for function in self.codebase.functions:
            if (
                not hasattr(function, "code_block")
                or not hasattr(function, "return_type")
                or function.return_type == "None"
                or function.return_type == "void"
            ):
                continue

            has_return = False
            for stmt in function.code_block.statements:
                if (
                    hasattr(stmt, "type")
                    and stmt.type == "return_statement"
                ):
                    has_return = True
                    break

            if not has_return:
                self.errors.append(
                    DetectedError(
                        category=ErrorCategory.RETURN_ERROR,
                        severity=ErrorSeverity.ERROR,
                        message=(
                            f"Function '{function.name}' has return type "
                            f"'{function.return_type}' but no return statement"
                        ),
                        file_path=function.filepath,
                        function_name=function.name,
                    )
                )


class CodeQualityChecker(ErrorDetector):
    """
    Checks code quality.

    This class detects code quality issues, such as unreachable code and
    overly complex functions.
    """

    def detect_errors(self) -> list[DetectedError]:
        """
        Detect code quality issues in the codebase.

        Returns:
            A list of detected errors
        """
        self.errors = []

        # Check for unreachable code
        self._check_unreachable_code()

        # Check for overly complex functions
        self._check_complex_functions()

        return self.errors

    def _check_unreachable_code(self) -> None:
        """Check for unreachable code in functions."""
        for function in self.codebase.functions:
            if not hasattr(function, "code_block"):
                continue

            has_return = False
            for i, stmt in enumerate(function.code_block.statements):
                if has_return and i < len(function.code_block.statements) - 1:
                    self.errors.append(
                        DetectedError(
                            category=ErrorCategory.CODE_QUALITY,
                            severity=ErrorSeverity.WARNING,
                            message=(
                                f"Unreachable code detected in function "
                                f"'{function.name}'"
                            ),
                            file_path=function.filepath,
                            function_name=function.name,
                        )
                    )
                    break

                if (
                    hasattr(stmt, "type")
                    and stmt.type == "return_statement"
                ):
                    has_return = True

    def _check_complex_functions(self) -> None:
        """Check for overly complex functions."""
        for function in self.codebase.functions:
            if not hasattr(function, "code_block"):
                continue

            # Calculate cyclomatic complexity (simplified)
            complexity = 1  # Base complexity
            for stmt in function.code_block.statements:
                if hasattr(stmt, "type"):
                    if stmt.type in ["if_statement", "while_statement"]:
                        complexity += 1
                    elif stmt.type == "for_statement":
                        complexity += 1

            if complexity > 10:
                self.errors.append(
                    DetectedError(
                        category=ErrorCategory.CODE_QUALITY,
                        severity=ErrorSeverity.WARNING,
                        message=(
                            f"Function '{function.name}' has high cyclomatic "
                            f"complexity ({complexity})"
                        ),
                        file_path=function.filepath,
                        function_name=function.name,
                    )
                )


def detect_errors(
    codebase: Codebase, context: CodebaseContext | None = None
) -> dict[str, Any]:
    """
    Detect errors in the codebase.

    Args:
        codebase: The codebase to analyze
        context: Optional context for the analysis

    Returns:
        A dictionary containing error detection results
    """
    detectors = [
        ParameterValidator(codebase, context),
        CallValidator(codebase, context),
        ReturnValidator(codebase, context),
        CodeQualityChecker(codebase, context),
    ]

    all_errors = []
    for detector in detectors:
        all_errors.extend(detector.detect_errors())

    # Group errors by category
    errors_by_category = {}
    for error in all_errors:
        category = error.category.name
        if category not in errors_by_category:
            errors_by_category[category] = []

        errors_by_category[category].append(
            {
                "severity": error.severity.name,
                "message": error.message,
                "file_path": error.file_path,
                "function_name": error.function_name,
                "line_number": error.line_number,
            }
        )

    # Group errors by severity
    errors_by_severity = {}
    for error in all_errors:
        severity = error.severity.name
        if severity not in errors_by_severity:
            errors_by_severity[severity] = []

        errors_by_severity[severity].append(
            {
                "category": error.category.name,
                "message": error.message,
                "file_path": error.file_path,
                "function_name": error.function_name,
                "line_number": error.line_number,
            }
        )

    # Group errors by file
    errors_by_file = {}
    for error in all_errors:
        file_path = error.file_path
        if file_path not in errors_by_file:
            errors_by_file[file_path] = []

        errors_by_file[file_path].append(
            {
                "category": error.category.name,
                "severity": error.severity.name,
                "message": error.message,
                "function_name": error.function_name,
                "line_number": error.line_number,
            }
        )

    return {
        "total_errors": len(all_errors),
        "errors_by_category": errors_by_category,
        "errors_by_severity": errors_by_severity,
        "errors_by_file": errors_by_file,
    }
