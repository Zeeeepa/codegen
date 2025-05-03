"""
Function call analysis module for code analysis.

This module provides classes and functions for analyzing function calls,
including call graphs, parameter usage, and call chains.
"""

from typing import Dict, List, Optional, Set, Tuple, Union, Any
import networkx as nx

from codegen import Codebase
from codegen.sdk.core.function import Function


class FunctionCallGraph:
    """Represents a graph of function calls in a codebase."""
    
    def __init__(self, codebase: Codebase):
        """
        Initialize the function call graph.
        
        Args:
            codebase: The codebase to analyze
        """
        self.codebase = codebase
        self.graph = self._build_graph()
        self.nx_graph = self._build_networkx_graph()
    
    def _build_graph(self) -> Dict[str, Set[str]]:
        """
        Build a dictionary-based graph of function calls.
        
        Returns:
            A dictionary mapping function names to sets of called function names
        """
        graph = {}
        
        for func in self.codebase.functions:
            caller = func.name
            if caller not in graph:
                graph[caller] = set()
                
            if hasattr(func, "function_calls"):
                for call in func.function_calls:
                    if hasattr(call, "target") and hasattr(call.target, "name"):
                        callee = call.target.name
                        graph[caller].add(callee)
                        
                        # Ensure callee is in the graph
                        if callee not in graph:
                            graph[callee] = set()
        
        return graph
    
    def _build_networkx_graph(self) -> nx.DiGraph:
        """
        Build a NetworkX directed graph of function calls.
        
        Returns:
            A NetworkX DiGraph representing the call graph
        """
        G = nx.DiGraph()
        
        # Add nodes
        for func_name in self.graph:
            G.add_node(func_name)
        
        # Add edges
        for caller, callees in self.graph.items():
            for callee in callees:
                G.add_edge(caller, callee)
        
        return G
    
    def get_callers(self, function_name: str) -> List[str]:
        """
        Get all functions that call the specified function.
        
        Args:
            function_name: Name of the function to find callers for
            
        Returns:
            A list of function names that call the specified function
        """
        callers = []
        
        for caller, callees in self.graph.items():
            if function_name in callees:
                callers.append(caller)
        
        return callers
    
    def get_callees(self, function_name: str) -> List[str]:
        """
        Get all functions called by the specified function.
        
        Args:
            function_name: Name of the function to find callees for
            
        Returns:
            A list of function names called by the specified function
        """
        return list(self.graph.get(function_name, set()))
    
    def get_call_chain(self, start: str, end: str) -> List[List[str]]:
        """
        Get all call chains from start function to end function.
        
        Args:
            start: Name of the starting function
            end: Name of the ending function
            
        Returns:
            A list of call chains (each chain is a list of function names)
        """
        if start not in self.graph or end not in self.graph:
            return []
            
        try:
            # Find all simple paths from start to end
            paths = list(nx.all_simple_paths(self.nx_graph, start, end))
            return paths
        except nx.NetworkXNoPath:
            return []
    
    def get_entry_points(self) -> List[str]:
        """
        Get all entry point functions (functions that are not called by any other function).
        
        Returns:
            A list of entry point function names
        """
        entry_points = []
        
        for func_name in self.graph:
            if not self.get_callers(func_name):
                entry_points.append(func_name)
        
        return entry_points
    
    def get_leaf_functions(self) -> List[str]:
        """
        Get all leaf functions (functions that don't call any other function).
        
        Returns:
            A list of leaf function names
        """
        leaf_functions = []
        
        for func_name, callees in self.graph.items():
            if not callees:
                leaf_functions.append(func_name)
        
        return leaf_functions
    
    def get_call_depth(self, function_name: str) -> int:
        """
        Get the maximum call depth of a function.
        
        Args:
            function_name: Name of the function to find call depth for
            
        Returns:
            The maximum call depth (0 for leaf functions)
        """
        if function_name not in self.graph:
            return 0
            
        callees = self.graph[function_name]
        if not callees:
            return 0
            
        return 1 + max(self.get_call_depth(callee) for callee in callees)
    
    def get_most_called_functions(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get the most frequently called functions.
        
        Args:
            limit: Maximum number of functions to return
            
        Returns:
            A list of (function_name, call_count) tuples, sorted by call count
        """
        call_counts = {}
        
        for func_name in self.graph:
            call_counts[func_name] = len(self.get_callers(func_name))
        
        # Sort by call count (descending)
        sorted_counts = sorted(call_counts.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_counts[:limit]
    
    def get_most_complex_functions(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get the most complex functions based on the number of function calls they make.
        
        Args:
            limit: Maximum number of functions to return
            
        Returns:
            A list of (function_name, complexity) tuples, sorted by complexity
        """
        complexity = {}
        
        for func_name, callees in self.graph.items():
            complexity[func_name] = len(callees)
        
        # Sort by complexity (descending)
        sorted_complexity = sorted(complexity.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_complexity[:limit]
    
    def get_circular_dependencies(self) -> List[List[str]]:
        """
        Get all circular dependencies in the call graph.
        
        Returns:
            A list of circular dependency chains
        """
        try:
            # Find all simple cycles in the graph
            cycles = list(nx.simple_cycles(self.nx_graph))
            return cycles
        except:
            # Fallback to manual cycle detection if NetworkX fails
            return self._find_cycles_manually()
    
    def _find_cycles_manually(self) -> List[List[str]]:
        """
        Find cycles in the call graph manually.
        
        Returns:
            A list of circular dependency chains
        """
        cycles = []
        visited = set()
        path = []
        
        def dfs(node):
            if node in path:
                # Found a cycle
                cycle = path[path.index(node):] + [node]
                cycles.append(cycle)
                return
                
            if node in visited:
                return
                
            visited.add(node)
            path.append(node)
            
            for neighbor in self.graph.get(node, set()):
                dfs(neighbor)
                
            path.pop()
        
        for node in self.graph:
            visited = set()
            path = []
            dfs(node)
        
        return cycles
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the call graph to a dictionary.
        
        Returns:
            A dictionary representation of the call graph
        """
        return {
            "nodes": list(self.graph.keys()),
            "edges": [(caller, callee) for caller, callees in self.graph.items() for callee in callees],
            "entry_points": self.get_entry_points(),
            "leaf_functions": self.get_leaf_functions(),
            "most_called": self.get_most_called_functions(),
            "most_complex": self.get_most_complex_functions(),
            "circular_dependencies": self.get_circular_dependencies()
        }


class ParameterUsageAnalysis:
    """Analyzes how parameters are used within functions."""
    
    def __init__(self, codebase: Codebase):
        """
        Initialize the parameter usage analyzer.
        
        Args:
            codebase: The codebase to analyze
        """
        self.codebase = codebase
    
    def analyze_parameter_usage(self, function_name: str) -> Dict[str, Any]:
        """
        Analyze how parameters are used in a specific function.
        
        Args:
            function_name: Name of the function to analyze
            
        Returns:
            A dictionary with parameter usage information
        """
        # Find the function
        func = None
        for f in self.codebase.functions:
            if f.name == function_name:
                func = f
                break
        
        if not func or not hasattr(func, "parameters") or not hasattr(func, "code_block"):
            return {"error": f"Function {function_name} not found or has no parameters"}
        
        result = {
            "function_name": function_name,
            "parameters": []
        }
        
        for param in func.parameters:
            param_info = {
                "name": param.name,
                "type": param.type_annotation if hasattr(param, "type_annotation") else None,
                "has_default": param.has_default_value if hasattr(param, "has_default_value") else False,
                "is_used": False,
                "usage_count": 0,
                "usage_contexts": []
            }
            
            # Check if parameter is used in the function body
            if hasattr(func, "code_block") and func.code_block and hasattr(func.code_block, "source"):
                source = func.code_block.source
                source_lines = source.splitlines()
                
                # Count occurrences of the parameter name
                param_info["usage_count"] = source.count(param.name)
                
                # If the parameter appears more than once (beyond its declaration), it's used
                if param_info["usage_count"] > 1 or (param.name + "=" not in source and param_info["usage_count"] > 0):
                    param_info["is_used"] = True
                
                # Find usage contexts
                for i, line in enumerate(source_lines):
                    if param.name in line and not line.strip().startswith("def "):
                        param_info["usage_contexts"].append({
                            "line_number": i + 1,  # +1 because line numbers are 1-based
                            "line": line.strip()
                        })
            
            result["parameters"].append(param_info)
        
        return result
    
    def analyze_all_parameters(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze parameter usage for all functions in the codebase.
        
        Returns:
            A dictionary mapping function names to parameter usage information
        """
        result = {}
        
        for func in self.codebase.functions:
            if hasattr(func, "name"):
                result[func.name] = self.analyze_parameter_usage(func.name)
        
        return result
    
    def get_unused_parameters(self) -> Dict[str, List[str]]:
        """
        Get all unused parameters in the codebase.
        
        Returns:
            A dictionary mapping function names to lists of unused parameter names
        """
        result = {}
        
        for func_name, analysis in self.analyze_all_parameters().items():
            if "parameters" in analysis:
                unused = [p["name"] for p in analysis["parameters"] if not p["is_used"] and p["name"] != "self"]
                if unused:
                    result[func_name] = unused
        
        return result
    
    def get_parameter_type_coverage(self) -> Dict[str, float]:
        """
        Get the percentage of parameters with type annotations for each function.
        
        Returns:
            A dictionary mapping function names to type coverage percentages
        """
        result = {}
        
        for func_name, analysis in self.analyze_all_parameters().items():
            if "parameters" in analysis and analysis["parameters"]:
                typed_params = [p for p in analysis["parameters"] if p["type"] is not None]
                coverage = len(typed_params) / len(analysis["parameters"]) * 100
                result[func_name] = coverage
        
        return result


class FunctionCallAnalysis:
    """Main class for function call analysis."""
    
    def __init__(self, codebase: Codebase):
        """
        Initialize the function call analyzer.
        
        Args:
            codebase: The codebase to analyze
        """
        self.codebase = codebase
        self.call_graph = FunctionCallGraph(codebase)
        self.parameter_usage = ParameterUsageAnalysis(codebase)
    
    def analyze_call_graph(self) -> Dict[str, Any]:
        """
        Analyze the function call graph.
        
        Returns:
            A dictionary with call graph analysis results
        """
        return self.call_graph.to_dict()
    
    def analyze_parameter_usage(self, function_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze parameter usage.
        
        Args:
            function_name: Name of the function to analyze (optional)
            
        Returns:
            A dictionary with parameter usage analysis results
        """
        if function_name:
            return self.parameter_usage.analyze_parameter_usage(function_name)
        else:
            return {
                "all_parameters": self.parameter_usage.analyze_all_parameters(),
                "unused_parameters": self.parameter_usage.get_unused_parameters(),
                "type_coverage": self.parameter_usage.get_parameter_type_coverage()
            }
    
    def analyze_function_dependencies(self, function_name: str) -> Dict[str, Any]:
        """
        Analyze dependencies for a specific function.
        
        Args:
            function_name: Name of the function to analyze
            
        Returns:
            A dictionary with function dependency analysis results
        """
        if function_name not in self.call_graph.graph:
            return {"error": f"Function {function_name} not found"}
        
        return {
            "function_name": function_name,
            "calls": list(self.call_graph.get_callees(function_name)),
            "called_by": self.call_graph.get_callers(function_name),
            "call_depth": self.call_graph.get_call_depth(function_name),
            "circular_dependencies": [cycle for cycle in self.call_graph.get_circular_dependencies() if function_name in cycle]
        }
    
    def analyze_all(self) -> Dict[str, Any]:
        """
        Perform comprehensive function call analysis.
        
        Returns:
            A dictionary with all analysis results
        """
        return {
            "call_graph": self.analyze_call_graph(),
            "parameter_usage": self.analyze_parameter_usage(),
            "entry_points": self.call_graph.get_entry_points(),
            "leaf_functions": self.call_graph.get_leaf_functions(),
            "most_called_functions": self.call_graph.get_most_called_functions(),
            "most_complex_functions": self.call_graph.get_most_complex_functions(),
            "circular_dependencies": self.call_graph.get_circular_dependencies(),
            "type_coverage": self.parameter_usage.get_parameter_type_coverage()
        }

