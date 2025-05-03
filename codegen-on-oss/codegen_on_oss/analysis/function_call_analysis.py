"""
Function call analysis module for code analysis.

This module provides classes and functions for analyzing function calls in code,
including call graphs, parameter usage analysis, and call statistics.
"""

from collections import Counter, defaultdict
from typing import Any

from codegen import Codebase

from codegen_on_oss.analysis.codebase_context import CodebaseContext


class FunctionCallGraph:
    """
    Represents a graph of function calls in a codebase.

    This class provides methods for analyzing function call relationships,
    including finding callers and callees, calculating call depths, and
    identifying entry points and leaf functions.
    """

    def __init__(
        self, codebase: Codebase, context: CodebaseContext | None = None
    ):
        """
        Initialize the function call graph.

        Args:
            codebase: The codebase to analyze
            context: Optional context for the analysis
        """
        self.codebase = codebase
        self.context = context
        self.callers: dict[str, set[str]] = defaultdict(
            set
        )  # function -> set of functions that call it
        self.callees: dict[str, set[str]] = defaultdict(
            set
        )  # function -> set of functions it calls
        self._build_graph()

    def _build_graph(self) -> None:
        """Build the function call graph."""
        # Initialize all functions as nodes in the graph
        for function in self.codebase.functions:
            self.callers[function.name] = set()
            self.callees[function.name] = set()

        # Add edges for function calls
        for function in self.codebase.functions:
            if not hasattr(function, "code_block"):
                continue

            for call in function.code_block.function_calls:
                # Skip calls to functions not in the codebase
                if call.name not in self.callees:
                    continue

                self.callees[function.name].add(call.name)
                self.callers[call.name].add(function.name)

    def get_callers(self, function_name: str) -> set[str]:
        """
        Get all functions that call the specified function.

        Args:
            function_name: The name of the function

        Returns:
            A set of function names that call the specified function
        """
        return self.callers.get(function_name, set())

    def get_callees(self, function_name: str) -> set[str]:
        """
        Get all functions called by the specified function.

        Args:
            function_name: The name of the function

        Returns:
            A set of function names called by the specified function
        """
        return self.callees.get(function_name, set())

    def get_entry_points(self) -> set[str]:
        """
        Get all entry point functions (functions not called by any other function).

        Returns:
            A set of function names that are entry points
        """
        return {name for name, callers in self.callers.items() if not callers}

    def get_leaf_functions(self) -> set[str]:
        """
        Get all leaf functions (functions that don't call any other function).

        Returns:
            A set of function names that are leaf functions
        """
        return {name for name, callees in self.callees.items() if not callees}

    def get_call_depth(self, function_name: str) -> int:
        """
        Get the maximum call depth of a function.

        Args:
            function_name: The name of the function

        Returns:
            The maximum call depth of the function
        """
        visited = set()

        def dfs(node: str, depth: int) -> int:
            if node in visited:
                return 0

            visited.add(node)

            if not self.callees.get(node, set()):
                return depth

            return max(dfs(callee, depth + 1) for callee in self.callees[node])

        return dfs(function_name, 0)

    def find_path(self, from_function: str, to_function: str) -> list[str]:
        """
        Find a path from one function to another in the call graph.

        Args:
            from_function: The starting function
            to_function: The target function

        Returns:
            A list of function names representing the path, or an empty list if no path exists
        """
        if from_function == to_function:
            return [from_function]

        visited = set()
        path = []

        def dfs(node: str) -> bool:
            if node == to_function:
                path.append(node)
                return True

            if node in visited:
                return False

            visited.add(node)
            path.append(node)

            for callee in self.callees.get(node, set()):
                if dfs(callee):
                    return True

            path.pop()
            return False

        if dfs(from_function):
            return path
        else:
            return []

    def get_most_called_functions(
        self, limit: int = 10
    ) -> list[tuple[str, int]]:
        """
        Get the most frequently called functions.

        Args:
            limit: Maximum number of functions to return

        Returns:
            A list of (function_name, call_count) tuples, sorted by call count
        """
        call_counts = [
            (name, len(callers)) for name, callers in self.callers.items()
        ]
        return sorted(call_counts, key=lambda x: x[1], reverse=True)[:limit]

    def get_functions_with_highest_call_depth(
        self, limit: int = 10
    ) -> list[tuple[str, int]]:
        """
        Get functions with the highest call depth.

        Args:
            limit: Maximum number of functions to return

        Returns:
            A list of (function_name, call_depth) tuples, sorted by call depth
        """
        depths = [(name, self.get_call_depth(name)) for name in self.callees]
        return sorted(depths, key=lambda x: x[1], reverse=True)[:limit]


class ParameterAnalysis:
    """
    Analyzes parameter usage in functions.

    This class provides methods for analyzing how parameters are used in functions,
    including parameter usage patterns and parameter type statistics.
    """

    def __init__(
        self, codebase: Codebase, context: CodebaseContext | None = None
    ):
        """
        Initialize the parameter analyzer.

        Args:
            codebase: The codebase to analyze
            context: Optional context for the analysis
        """
        self.codebase = codebase
        self.context = context

    def get_parameter_usage(self, function_name: str) -> dict[str, int]:
        """
        Get usage statistics for parameters of a function.

        Args:
            function_name: The name of the function

        Returns:
            A dictionary mapping parameter names to usage counts
        """
        # Find the function
        function = None
        for f in self.codebase.functions:
            if f.name == function_name:
                function = f
                break

        if (
            not function
            or not hasattr(function, "parameters")
            or not function.parameters
        ):
            return {}

        # Get parameter names
        param_names = {param.name for param in function.parameters}

        # Count variable references
        usage_counts = Counter()
        if hasattr(function, "code_block") and hasattr(
            function.code_block, "variable_references"
        ):
            for ref in function.code_block.variable_references:
                if ref.name in param_names:
                    usage_counts[ref.name] += 1

        return dict(usage_counts)

    def get_parameter_type_statistics(self) -> dict[str, int]:
        """
        Get statistics on parameter types across the codebase.

        Returns:
            A dictionary mapping parameter types to counts
        """
        type_counts = Counter()

        for function in self.codebase.functions:
            if not hasattr(function, "parameters") or not function.parameters:
                continue

            for param in function.parameters:
                if hasattr(param, "type_annotation") and param.type_annotation:
                    type_counts[param.type_annotation] += 1

        return dict(type_counts)

    def get_functions_with_most_parameters(
        self, limit: int = 10
    ) -> list[tuple[str, int]]:
        """
        Get functions with the most parameters.

        Args:
            limit: Maximum number of functions to return

        Returns:
            A list of (function_name, parameter_count) tuples, sorted by parameter count
        """
        param_counts = []

        for function in self.codebase.functions:
            if hasattr(function, "parameters"):
                param_counts.append((function.name, len(function.parameters)))

        return sorted(param_counts, key=lambda x: x[1], reverse=True)[:limit]

    def get_unused_parameters(self) -> dict[str, list[str]]:
        """
        Get unused parameters for each function.

        Returns:
            A dictionary mapping function names to lists of unused parameter names
        """
        unused_params = {}

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
            if unused:
                unused_params[function.name] = list(unused)

        return unused_params


def analyze_function_calls(
    codebase: Codebase, context: CodebaseContext | None = None
) -> dict[str, Any]:
    """
    Analyze function calls in the codebase.

    Args:
        codebase: The codebase to analyze
        context: Optional context for the analysis

    Returns:
        A dictionary containing function call analysis results
    """
    call_graph = FunctionCallGraph(codebase, context)
    param_analyzer = ParameterAnalysis(codebase, context)

    # Get call statistics
    most_called = call_graph.get_most_called_functions(limit=10)
    highest_depth = call_graph.get_functions_with_highest_call_depth(limit=10)
    entry_points = call_graph.get_entry_points()
    leaf_functions = call_graph.get_leaf_functions()

    # Get parameter statistics
    most_params = param_analyzer.get_functions_with_most_parameters(limit=10)
    param_types = param_analyzer.get_parameter_type_statistics()
    unused_params = param_analyzer.get_unused_parameters()

    return {
        "call_statistics": {
            "most_called_functions": most_called,
            "functions_with_highest_call_depth": highest_depth,
            "entry_points": list(entry_points),
            "leaf_functions": list(leaf_functions),
            "total_functions": len(codebase.functions),
        },
        "parameter_statistics": {
            "functions_with_most_parameters": most_params,
            "parameter_types": param_types,
            "functions_with_unused_parameters": unused_params,
        },
    }
