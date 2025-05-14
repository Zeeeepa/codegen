"""Call graph visualization utilities."""

from typing import Optional, Union

import networkx as nx

from codegen_on_oss.analyzers.context.graph.class_definition import Class
from codegen_on_oss.analyzers.context.graph.function import Function
from codegen_on_oss.analyzers.context.graph.function_call import FunctionCall
from codegen_on_oss.visualizers.codebase_visualizer import CodebaseVisualizer


class CallGraphFromNode(CodebaseVisualizer):
    """Creates a directed call graph for a given function.
    
    Starting from the specified function, it recursively iterates through its function calls
    and the functions called by them, building a graph of the call paths to a maximum depth.
    The root of the directed graph is the starting function, each node represents a function call,
    and edge from node A to node B indicates that function A calls function B.
    """

    def __init__(
        self,
        function_name: str,
        max_depth: int = 5,
        graph_external_modules: bool = False,
    ):
        """Initialize the call graph visualizer.
        
        Args:
            function_name: Name of the function to trace
            max_depth: Maximum depth of the call graph
            graph_external_modules: Whether to include external module calls
        """
        self.function_name = function_name
        self.max_depth = max_depth
        self.graph_external_modules = graph_external_modules
        self.G: nx.DiGraph = nx.DiGraph()

    def visualize(self, codebase) -> nx.DiGraph:
        """Create a call graph visualization starting from the specified function.
        
        Args:
            codebase: The codebase to analyze
            
        Returns:
            A directed graph representing the call paths
        """
        # Get the function to trace
        function_to_trace = codebase.get_function(self.function_name)
        
        # Set starting node
        self.G.add_node(function_to_trace, color="yellow")
        
        # Add all the children (and sub-children) to the graph
        self._create_downstream_call_trace(function_to_trace)
        
        return self.G
    
    def _create_downstream_call_trace(
        self, 
        parent: Optional[Union[FunctionCall, Function]] = None, 
        depth: int = 0
    ):
        """Creates call graph for parent.
        
        This function recurses through the call graph of a function and creates a visualization.
        
        Args:
            parent: The function for which a call graph will be created
            depth: The current depth of the recursive stack
        """
        # If the maximum recursive depth has been exceeded, return
        if self.max_depth <= depth:
            return
            
        if isinstance(parent, FunctionCall):
            src_call, src_func = parent, parent.function_definition
        else:
            src_call, src_func = parent, parent
            
        # Iterate over all call paths of the symbol
        for call in src_func.function_calls:
            # The symbol being called
            func = call.function_definition
            
            # Ignore direct recursive calls
            if func.name == src_func.name:
                continue
                
            # If the function being called is not from an external module
            if not isinstance(func, str):  # External modules are represented as strings
                # Add `call` to the graph and an edge from `src_call` to `call`
                self.G.add_node(call)
                self.G.add_edge(src_call, call)
                
                # Recursive call to function call
                self._create_downstream_call_trace(call, depth + 1)
            elif self.graph_external_modules:
                # Add `call` to the graph and an edge from `src_call` to `call`
                self.G.add_node(call)
                self.G.add_edge(src_call, call)


class CallGraphFilter(CodebaseVisualizer):
    """Creates a filtered call graph visualization.
    
    This visualizer shows a call graph from a given function or symbol,
    filtering out test files and class declarations and including only methods
    with specific names (by default: post, get, patch, delete).
    """

    def __init__(
        self,
        function_name: str,
        class_name: str,
        method_names: Optional[list[str]] = None,
        max_depth: int = 5,
        skip_class_declarations: bool = True,
    ):
        """Initialize the filtered call graph visualizer.
        
        Args:
            function_name: Name of the function to trace
            class_name: Name of the class to filter methods from
            method_names: List of method names to include (defaults to HTTP methods)
            max_depth: Maximum depth of the call graph
            skip_class_declarations: Whether to skip class declarations in the graph
        """
        self.function_name = function_name
        self.class_name = class_name
        self.method_names = method_names or ["post", "get", "patch", "delete"]
        self.max_depth = max_depth
        self.skip_class_declarations = skip_class_declarations
        self.G: nx.DiGraph = nx.DiGraph()

    def visualize(self, codebase) -> nx.DiGraph:
        """Create a filtered call graph visualization.
        
        Args:
            codebase: The codebase to analyze
            
        Returns:
            A directed graph representing the filtered call paths
        """
        # Get the function to trace
        func_to_trace = codebase.get_function(self.function_name)
        
        # Get the class to filter methods from
        cls = codebase.get_class(self.class_name)
        
        # Add the main symbol as a node
        self.G.add_node(func_to_trace, color="red")
        
        # Start the recursive traversal
        self._create_filtered_downstream_call_trace(func_to_trace, 1, cls)
        
        return self.G
    
    def _create_filtered_downstream_call_trace(
        self, 
        parent: Union[FunctionCall, Function], 
        current_depth: int,
        cls: Class
    ):
        """Creates a filtered call graph.
        
        Args:
            parent: The function or call to trace from
            current_depth: Current depth in the call graph
            cls: The class to filter methods from
        """
        if current_depth > self.max_depth:
            return
            
        # If parent is of type Function
        if isinstance(parent, Function):
            # Set both src_call, src_func to parent
            src_call, src_func = parent, parent
        else:
            # Get the first callable of parent
            src_call, src_func = parent, parent.function_definition
            
        # Iterate over all call paths of the symbol
        for call in src_func.function_calls:
            # The symbol being called
            func = call.function_definition
            
            if self.skip_class_declarations and isinstance(func, Class):
                continue
                
            # If the function being called is not from an external module and is not defined in a test file
            if not isinstance(func, str) and not getattr(func, 'file', {}).get('filepath', '').startswith("test"):
                # Add `call` to the graph and an edge from `src_call` to `call`
                metadata = {}
                if isinstance(func, Function) and getattr(func, 'is_method', False) and func.name in self.method_names:
                    name = f"{func.parent_class.name}.{func.name}"
                    metadata = {"color": "yellow", "name": name}
                self.G.add_node(call, **metadata)
                self.G.add_edge(src_call, call, symbol=cls)  # Add edge from current to successor
                
                # Recursively add successors of the current symbol
                self._create_filtered_downstream_call_trace(call, current_depth + 1, cls)


class CallPathsBetweenNodes(CodebaseVisualizer):
    """Visualizes call paths between two specified functions.
    
    This visualizer generates and visualizes a call graph between two specified functions.
    It starts from a given function and iteratively traverses through its function calls,
    building a directed graph of the call paths. The visualizer then identifies all simple
    paths between the start and end functions, creating a subgraph that includes only the
    nodes in these paths.
    """

    def __init__(
        self,
        start_function_name: str,
        end_function_name: str,
        max_depth: int = 5,
    ):
        """Initialize the call paths visualizer.
        
        Args:
            start_function_name: Name of the starting function
            end_function_name: Name of the ending function
            max_depth: Maximum depth of the call graph
        """
        self.start_function_name = start_function_name
        self.end_function_name = end_function_name
        self.max_depth = max_depth
        self.G: nx.DiGraph = nx.DiGraph()

    def visualize(self, codebase) -> nx.DiGraph:
        """Create a visualization of call paths between two functions.
        
        Args:
            codebase: The codebase to analyze
            
        Returns:
            A directed graph representing the call paths
        """
        # Get the start and end functions
        start = codebase.get_function(self.start_function_name)
        end = codebase.get_function(self.end_function_name)
        
        # Set starting node as blue
        self.G.add_node(start, color="blue")
        # Set ending node as red
        self.G.add_node(end, color="red")
        
        # Start the recursive traversal
        self._create_downstream_call_trace(start, end, 1)
        
        # Find all the simple paths between start and end
        try:
            all_paths = list(nx.all_simple_paths(self.G, source=start, target=end))
            
            # Collect all nodes that are part of these paths
            nodes_in_paths = set()
            for path in all_paths:
                nodes_in_paths.update(path)
                
            # Create a new subgraph with only the nodes in the paths
            self.G = self.G.subgraph(nodes_in_paths)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            # If no path exists, return the original graph
            pass
            
        return self.G
    
    def _create_downstream_call_trace(
        self, 
        parent: Union[FunctionCall, Function], 
        end: Function, 
        current_depth: int
    ):
        """Creates a call graph between two functions.
        
        Args:
            parent: The current function or call in the traversal
            end: The target end function
            current_depth: Current depth in the call graph
        """
        if current_depth > self.max_depth:
            return
            
        # If parent is of type Function
        if isinstance(parent, Function):
            # Set both src_call, src_func to parent
            src_call, src_func = parent, parent
        else:
            # Get the first callable of parent
            src_call, src_func = parent, parent.function_definition
            
        # Iterate over all call paths of the symbol
        for call in src_func.function_calls:
            # The symbol being called
            func = call.function_definition
            
            # Ignore direct recursive calls
            if func.name == src_func.name:
                continue
                
            # If the function being called is not from an external module
            if not isinstance(func, str):
                # Add `call` to the graph and an edge from `src_call` to `call`
                self.G.add_node(call)
                self.G.add_edge(src_call, call)
                
                if func == end:
                    self.G.add_edge(call, end)
                    return
                # Recursive call to function call
                self._create_downstream_call_trace(call, end, current_depth + 1)

