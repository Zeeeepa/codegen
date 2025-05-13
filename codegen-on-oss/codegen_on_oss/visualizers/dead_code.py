"""Dead code visualization utilities."""

import networkx as nx

from codegen_on_oss.analyzers.context.graph.function import Function
from codegen_on_oss.analyzers.context.graph.import_resolution import Import
from codegen_on_oss.analyzers.context.graph.symbol import Symbol
from codegen_on_oss.visualizers.codebase_visualizer import CodebaseVisualizer


class DeadCodeVisualizer(CodebaseVisualizer):
    """Visualizes dead code in the codebase.
    
    This visualizer identifies functions that have no usages and are not in test files
    or decorated. These functions are considered 'dead code' and are added to a directed
    graph. The visualizer then explores the dependencies of these dead code functions,
    adding them to the graph as well. This process helps to identify not only directly
    unused code but also code that might only be used by other dead code (second-order
    dead code).
    """

    def __init__(self, exclude_test_files: bool = True, exclude_decorated: bool = True):
        """Initialize the dead code visualizer.
        
        Args:
            exclude_test_files: Whether to exclude test files from analysis
            exclude_decorated: Whether to exclude decorated functions from analysis
        """
        self.exclude_test_files = exclude_test_files
        self.exclude_decorated = exclude_decorated

    def visualize(self, codebase) -> nx.DiGraph:
        """Create a visualization of dead code in the codebase.
        
        Args:
            codebase: The codebase to analyze
            
        Returns:
            A directed graph representing the dead code and its dependencies
        """
        # Create a directed graph to visualize dead and second-order dead code
        G: nx.DiGraph = nx.DiGraph()
        
        # First, identify all dead code
        dead_code: list[Function] = []
        
        # Iterate through all functions in the codebase
        for function in codebase.functions:
            # Filter down functions
            if self.exclude_test_files and "test" in function.file.filepath:
                continue
                
            if self.exclude_decorated and function.decorators:
                continue
                
            # Check if the function has no usages
            if not function.symbol_usages:
                # Add the function to the dead code list
                dead_code.append(function)
                # Add the function to the graph as dead code
                G.add_node(function, color="red")
                
        # Now, find second-order dead code
        for symbol in dead_code:
            # Get all usages of the dead code symbol
            for dep in symbol.dependencies:
                if isinstance(dep, Import):
                    dep = dep.imported_symbol
                if isinstance(dep, Symbol):
                    if not (self.exclude_test_files and "test" in getattr(dep, 'name', '')):
                        G.add_node(dep)
                        G.add_edge(symbol, dep, color="red")
                        for usage_symbol in dep.symbol_usages:
                            if isinstance(usage_symbol, Function):
                                if not (self.exclude_test_files and "test" in usage_symbol.name):
                                    G.add_edge(usage_symbol, dep)
                                    
        return G

