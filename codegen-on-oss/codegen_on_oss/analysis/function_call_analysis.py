"""
Function Call Analysis Module for Codegen-on-OSS

This module provides detailed analysis of function calls, including call graphs,
call-in and call-out points, and parameter validation.
"""

import networkx as nx
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from codegen import Codebase
from codegen.sdk.core.function import Function
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.enums import EdgeType, SymbolType

from codegen_on_oss.analysis.codebase_context import CodebaseContext
from codegen_on_oss.analysis.document_functions import hop_through_imports


class FunctionCallGraph:
    """Builds and analyzes a graph of function calls in a codebase."""
    
    def __init__(self, codebase: Codebase, context: Optional[CodebaseContext] = None):
        """Initialize the function call graph.
        
        Args:
            codebase: The Codebase object to analyze
            context: Optional CodebaseContext for additional analysis capabilities
        """
        self.codebase = codebase
        self.context = context
        self.graph = nx.DiGraph()
        self._build_graph()
    
    def _build_graph(self) -> None:
        """Build the function call graph from the codebase."""
        # Add all functions as nodes
        for function in self.codebase.functions:
            self.graph.add_node(function.name, function=function)
        
        # Add edges for function calls
        for function in self.codebase.functions:
            if not hasattr(function, "code_block") or not function.code_block:
                continue
                
            for statement in function.code_block.statements:
                if not hasattr(statement, "function_calls"):
                    continue
                    
                for call in statement.function_calls:
                    # Try to resolve the called function
                    called_func = self._resolve_function_call(call)
                    if called_func:
                        self.graph.add_edge(
                            function.name, 
                            called_func.name,
                            call=call,
                            line_number=call.line_number if hasattr(call, "line_number") else None
                        )
    
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
    
    def get_callers(self, function_name: str) -> List[Function]:
        """Get all functions that call the specified function.
        
        Args:
            function_name: The name of the function
            
        Returns:
            A list of Function objects that call the specified function
        """
        callers = []
        
        for predecessor in self.graph.predecessors(function_name):
            node_data = self.graph.nodes[predecessor]
            if "function" in node_data:
                callers.append(node_data["function"])
        
        return callers
    
    def get_callees(self, function_name: str) -> List[Function]:
        """Get all functions called by the specified function.
        
        Args:
            function_name: The name of the function
            
        Returns:
            A list of Function objects called by the specified function
        """
        callees = []
        
        for successor in self.graph.successors(function_name):
            node_data = self.graph.nodes[successor]
            if "function" in node_data:
                callees.append(node_data["function"])
        
        return callees
    
    def find_cycles(self) -> List[List[str]]:
        """Find cycles in the call graph.
        
        Returns:
            A list of cycles, where each cycle is a list of function names
        """
        cycles = list(nx.simple_cycles(self.graph))
        return cycles
    
    def get_call_chain(self, source: str, target: str) -> List[List[str]]:
        """Find all paths from source function to target function.
        
        Args:
            source: The name of the source function
            target: The name of the target function
            
        Returns:
            A list of paths, where each path is a list of function names
        """
        if not nx.has_path(self.graph, source, target):
            return []
            
        return list(nx.all_simple_paths(self.graph, source, target))
    
    def get_entry_points(self) -> List[Function]:
        """Get all functions that are not called by any other function.
        
        Returns:
            A list of Function objects that are entry points
        """
        entry_points = []
        
        for node in self.graph.nodes:
            if self.graph.in_degree(node) == 0:
                node_data = self.graph.nodes[node]
                if "function" in node_data:
                    entry_points.append(node_data["function"])
        
        return entry_points
    
    def get_leaf_functions(self) -> List[Function]:
        """Get all functions that don't call any other function.
        
        Returns:
            A list of Function objects that are leaf functions
        """
        leaf_functions = []
        
        for node in self.graph.nodes:
            if self.graph.out_degree(node) == 0:
                node_data = self.graph.nodes[node]
                if "function" in node_data:
                    leaf_functions.append(node_data["function"])
        
        return leaf_functions
    
    def get_call_depth(self, function_name: str) -> int:
        """Get the maximum depth of the call tree starting from the specified function.
        
        Args:
            function_name: The name of the function
            
        Returns:
            The maximum depth of the call tree
        """
        if function_name not in self.graph:
            return 0
            
        # Use BFS to find the maximum depth
        visited = set([function_name])
        queue = [(function_name, 0)]
        max_depth = 0
        
        while queue:
            node, depth = queue.pop(0)
            max_depth = max(max_depth, depth)
            
            for successor in self.graph.successors(node):
                if successor not in visited:
                    visited.add(successor)
                    queue.append((successor, depth + 1))
        
        return max_depth
    
    def get_most_called_functions(self, limit: int = 10) -> List[Tuple[Function, int]]:
        """Get the most frequently called functions.
        
        Args:
            limit: The maximum number of functions to return
            
        Returns:
            A list of (Function, call_count) tuples, sorted by call count
        """
        in_degrees = {}
        
        for node in self.graph.nodes:
            in_degree = self.graph.in_degree(node)
            if in_degree > 0:
                node_data = self.graph.nodes[node]
                if "function" in node_data:
                    in_degrees[node_data["function"]] = in_degree
        
        # Sort by in-degree (call count) in descending order
        sorted_functions = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_functions[:limit]
    
    def get_most_calling_functions(self, limit: int = 10) -> List[Tuple[Function, int]]:
        """Get the functions that call the most other functions.
        
        Args:
            limit: The maximum number of functions to return
            
        Returns:
            A list of (Function, called_count) tuples, sorted by called count
        """
        out_degrees = {}
        
        for node in self.graph.nodes:
            out_degree = self.graph.out_degree(node)
            if out_degree > 0:
                node_data = self.graph.nodes[node]
                if "function" in node_data:
                    out_degrees[node_data["function"]] = out_degree
        
        # Sort by out-degree (called count) in descending order
        sorted_functions = sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_functions[:limit]
    
    def get_call_graph_stats(self) -> Dict[str, Any]:
        """Get statistics about the call graph.
        
        Returns:
            A dictionary of statistics
        """
        return {
            "total_functions": len(self.graph.nodes),
            "total_calls": len(self.graph.edges),
            "entry_points": len(self.get_entry_points()),
            "leaf_functions": len(self.get_leaf_functions()),
            "cycles": len(self.find_cycles()),
            "connected_components": nx.number_weakly_connected_components(self.graph),
            "average_calls_per_function": len(self.graph.edges) / len(self.graph.nodes) if len(self.graph.nodes) > 0 else 0,
            "max_call_depth": max(self.get_call_depth(node) for node in self.graph.nodes) if self.graph.nodes else 0,
        }


class ParameterAnalysis:
    """Analyzes function parameters and their usage."""
    
    def __init__(self, codebase: Codebase, context: Optional[CodebaseContext] = None):
        """Initialize the parameter analyzer.
        
        Args:
            codebase: The Codebase object to analyze
            context: Optional CodebaseContext for additional analysis capabilities
        """
        self.codebase = codebase
        self.context = context
    
    def analyze_parameter_usage(self, function: Function) -> Dict[str, Any]:
        """Analyze how parameters are used in a function.
        
        Args:
            function: The function to analyze
            
        Returns:
            A dictionary with parameter usage information
        """
        # Get all parameters
        parameters = {param.name: {"used": False, "usage_count": 0, "has_default": param.has_default_value} 
                     for param in function.parameters}
        
        # Check usage in code block
        if hasattr(function, "code_block") and function.code_block:
            for statement in function.code_block.statements:
                self._analyze_statement_for_parameters(statement, parameters)
        
        # Compute statistics
        unused_params = [name for name, info in parameters.items() if not info["used"] and not name.startswith("_")]
        used_params = [name for name, info in parameters.items() if info["used"]]
        optional_params = [name for name, info in parameters.items() if info["has_default"]]
        required_params = [name for name, info in parameters.items() if not info["has_default"]]
        
        return {
            "total_parameters": len(parameters),
            "unused_parameters": unused_params,
            "used_parameters": used_params,
            "optional_parameters": optional_params,
            "required_parameters": required_params,
            "parameter_details": parameters
        }
    
    def _analyze_statement_for_parameters(self, statement: Any, parameters: Dict[str, Dict[str, Any]]) -> None:
        """Analyze a statement for parameter usage.
        
        Args:
            statement: The statement to analyze
            parameters: Dictionary of parameter information to update
        """
        # Extract from expressions
        if hasattr(statement, "expressions"):
            for expr in statement.expressions:
                self._analyze_expression_for_parameters(expr, parameters)
        
        # Extract from function calls
        if hasattr(statement, "function_calls"):
            for call in statement.function_calls:
                for arg in call.args:
                    if hasattr(arg, "name") and arg.name in parameters:
                        parameters[arg.name]["used"] = True
                        parameters[arg.name]["usage_count"] += 1
        
        # Extract from nested statements
        if hasattr(statement, "statements"):
            for nested_stmt in statement.statements:
                self._analyze_statement_for_parameters(nested_stmt, parameters)
        
        # Handle specific statement types
        if hasattr(statement, "type"):
            if statement.type == "if_statement" and hasattr(statement, "blocks"):
                for block in statement.blocks:
                    for nested_stmt in block.statements:
                        self._analyze_statement_for_parameters(nested_stmt, parameters)
            elif statement.type == "for_statement" and hasattr(statement, "body"):
                for nested_stmt in statement.body.statements:
                    self._analyze_statement_for_parameters(nested_stmt, parameters)
            elif statement.type == "while_statement" and hasattr(statement, "body"):
                for nested_stmt in statement.body.statements:
                    self._analyze_statement_for_parameters(nested_stmt, parameters)
            elif statement.type == "try_statement":
                if hasattr(statement, "try_block"):
                    for nested_stmt in statement.try_block.statements:
                        self._analyze_statement_for_parameters(nested_stmt, parameters)
                if hasattr(statement, "catch_blocks"):
                    for catch_block in statement.catch_blocks:
                        for nested_stmt in catch_block.statements:
                            self._analyze_statement_for_parameters(nested_stmt, parameters)
                if hasattr(statement, "finally_block"):
                    for nested_stmt in statement.finally_block.statements:
                        self._analyze_statement_for_parameters(nested_stmt, parameters)
    
    def _analyze_expression_for_parameters(self, expr: Any, parameters: Dict[str, Dict[str, Any]]) -> None:
        """Analyze an expression for parameter usage.
        
        Args:
            expr: The expression to analyze
            parameters: Dictionary of parameter information to update
        """
        if hasattr(expr, "elements"):
            for elem in expr.elements:
                if hasattr(elem, "name") and elem.name in parameters:
                    parameters[elem.name]["used"] = True
                    parameters[elem.name]["usage_count"] += 1
        elif hasattr(expr, "argument") and hasattr(expr.argument, "name") and expr.argument.name in parameters:
            parameters[expr.argument.name]["used"] = True
            parameters[expr.argument.name]["usage_count"] += 1
    
    def analyze_all_functions(self) -> Dict[str, Dict[str, Any]]:
        """Analyze parameter usage for all functions in the codebase.
        
        Returns:
            A dictionary mapping function names to parameter usage information
        """
        results = {}
        
        for function in self.codebase.functions:
            results[function.name] = self.analyze_parameter_usage(function)
        
        return results
    
    def get_functions_with_unused_parameters(self) -> List[Tuple[Function, List[str]]]:
        """Get all functions with unused parameters.
        
        Returns:
            A list of (Function, unused_parameters) tuples
        """
        functions_with_unused = []
        
        for function in self.codebase.functions:
            analysis = self.analyze_parameter_usage(function)
            if analysis["unused_parameters"]:
                functions_with_unused.append((function, analysis["unused_parameters"]))
        
        return functions_with_unused
    
    def get_parameter_usage_stats(self) -> Dict[str, Any]:
        """Get statistics about parameter usage across the codebase.
        
        Returns:
            A dictionary of statistics
        """
        total_params = 0
        unused_params = 0
        optional_params = 0
        required_params = 0
        
        for function in self.codebase.functions:
            analysis = self.analyze_parameter_usage(function)
            total_params += analysis["total_parameters"]
            unused_params += len(analysis["unused_parameters"])
            optional_params += len(analysis["optional_parameters"])
            required_params += len(analysis["required_parameters"])
        
        return {
            "total_parameters": total_params,
            "unused_parameters": unused_params,
            "optional_parameters": optional_params,
            "required_parameters": required_params,
            "usage_ratio": (total_params - unused_params) / total_params if total_params > 0 else 0,
            "optional_ratio": optional_params / total_params if total_params > 0 else 0,
        }


def analyze_function_calls(codebase: Codebase, context: Optional[CodebaseContext] = None) -> Dict[str, Any]:
    """Analyze function calls in a codebase and return comprehensive results.
    
    Args:
        codebase: The Codebase object to analyze
        context: Optional CodebaseContext for additional analysis capabilities
        
    Returns:
        A dictionary containing function call analysis results
    """
    # Create analyzers
    call_graph = FunctionCallGraph(codebase, context)
    param_analysis = ParameterAnalysis(codebase, context)
    
    # Get call graph statistics
    call_graph_stats = call_graph.get_call_graph_stats()
    
    # Get parameter usage statistics
    param_stats = param_analysis.get_parameter_usage_stats()
    
    # Get most called functions
    most_called = [(func.name, count) for func, count in call_graph.get_most_called_functions()]
    
    # Get most calling functions
    most_calling = [(func.name, count) for func, count in call_graph.get_most_calling_functions()]
    
    # Get cycles
    cycles = call_graph.find_cycles()
    
    # Get entry points
    entry_points = [func.name for func in call_graph.get_entry_points()]
    
    # Get leaf functions
    leaf_functions = [func.name for func in call_graph.get_leaf_functions()]
    
    # Get functions with unused parameters
    unused_params = [(func.name, params) for func, params in param_analysis.get_functions_with_unused_parameters()]
    
    # Return the complete analysis
    return {
        "call_graph_stats": call_graph_stats,
        "parameter_stats": param_stats,
        "most_called_functions": most_called,
        "most_calling_functions": most_calling,
        "cycles": cycles,
        "entry_points": entry_points,
        "leaf_functions": leaf_functions,
        "functions_with_unused_parameters": unused_params
    }

