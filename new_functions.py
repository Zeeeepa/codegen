    def find_max_call_chain(self, function_name: str) -> Dict[str, Any]:
        """Find the longest call chain starting from a specific function.
        
        This function builds a directed graph of function calls starting from the specified
        function and finds the longest path in the resulting graph.
        
        Args:
            function_name: Name of the function to start the call chain analysis from
            
        Returns:
            Dict containing the longest call chain information, including:
                - chain_length: Length of the longest call chain
                - call_chain: List of function names in the call chain
                - visualization_data: Data for visualizing the call chain
        """
        # Find the starting function
        start_function = None
        for func in self.codebase.functions:
            if func.name == function_name:
                start_function = func
                break
                
        if not start_function:
            return {
                "error": f"Function '{function_name}' not found in the codebase",
                "chain_length": 0,
                "call_chain": [],
                "visualization_data": {}
            }
            
        # Create a directed graph
        G = nx.DiGraph()
        
        # Track visited functions to avoid infinite recursion
        visited = set()
        
        def build_graph(func, depth=0, max_depth=10):
            """Recursively build the call graph."""
            if depth > max_depth or func in visited:
                return
                
            visited.add(func)
            
            # Add the current function as a node
            G.add_node(func.name, file=func.file.file_path if hasattr(func, "file") else "Unknown")
            
            # Process all function calls
            for call in func.function_calls:
                called_func = call.function_definition
                
                # Skip if the called function is external or the same as the caller
                if not hasattr(called_func, "name") or called_func.name == func.name:
                    continue
                    
                # Add the called function as a node
                G.add_node(called_func.name, file=called_func.file.file_path if hasattr(called_func, "file") else "Unknown")
                
                # Add an edge from the current function to the called function
                G.add_edge(func.name, called_func.name)
                
                # Recursively process the called function
                build_graph(called_func, depth + 1, max_depth)
        
        # Build the graph starting from the specified function
        build_graph(start_function)
        
        # Find the longest path in the graph
        longest_path = []
        try:
            # If the graph is a DAG (no cycles), use dag_longest_path
            longest_path = nx.dag_longest_path(G)
        except nx.NetworkXError:
            # If the graph has cycles, find the longest simple path
            longest_paths = []
            for node in G.nodes():
                for target in G.nodes():
                    if node != target:
                        try:
                            paths = list(nx.all_simple_paths(G, node, target))
                            if paths:
                                longest_paths.extend(paths)
                        except nx.NetworkXNoPath:
                            continue
            
            if longest_paths:
                longest_path = max(longest_paths, key=len)
        
        # Prepare the result
        result = {
            "chain_length": len(longest_path),
            "call_chain": longest_path,
            "visualization_data": {
                "nodes": [{"id": node, "file": G.nodes[node]["file"]} for node in G.nodes()],
                "edges": [{"source": u, "target": v} for u, v in G.edges()]
            }
        }
        
        return result
    
    def detect_dead_code(self) -> List[Dict[str, Any]]:
        """Detect unused (dead) functions in the codebase.
        
        This function identifies functions that are never called by any other function
        in the codebase and are not entry points or exported functions.
        
        Returns:
            List of dictionaries containing information about unused functions:
                - name: Name of the unused function
                - file: File path where the function is defined
                - line: Line number where the function is defined
                - is_public: Whether the function is public (not prefixed with _)
                - is_test: Whether the function appears to be a test function
        """
        # Get all functions in the codebase
        all_functions = list(self.codebase.functions)
        
        # Create a set of all called functions
        called_functions = set()
        for func in all_functions:
            for call in func.function_calls:
                called_func = call.function_definition
                if hasattr(called_func, "name"):
                    called_functions.add(called_func.name)
        
        # Find functions that are never called
        dead_functions = []
        for func in all_functions:
            # Skip if the function is called by another function
            if func.name in called_functions:
                continue
                
            # Check if the function might be an entry point or test
            is_test = False
            if func.name.startswith("test_") or "test" in func.name.lower():
                is_test = True
                
            # Check if the function is public (not prefixed with _)
            is_public = not func.name.startswith("_")
            
            # Get the file and line number
            file_path = func.file.file_path if hasattr(func, "file") else "Unknown"
            line_number = func.span.start.line if hasattr(func, "span") else 0
            
            # Add to the list of dead functions
            dead_functions.append({
                "name": func.name,
                "file": file_path,
                "line": line_number,
                "is_public": is_public,
                "is_test": is_test
            })
        
        # Sort by file path and line number
        dead_functions.sort(key=lambda x: (x["file"], x["line"]))
        
        return dead_functions
    
    def find_paths_between_functions(self, start_function: str, end_function: str) -> Dict[str, Any]:
        """Find all paths between two functions in the call graph.
        
        This function builds a directed graph of function calls and finds all possible
        paths between the specified start and end functions.
        
        Args:
            start_function: Name of the starting function
            end_function: Name of the target function
            
        Returns:
            Dict containing information about the paths:
                - paths_count: Number of paths found
                - paths: List of paths, each represented as a list of function names
                - visualization_data: Data for visualizing the paths
        """
        # Find the start and end functions
        start_func = None
        end_func = None
        
        for func in self.codebase.functions:
            if func.name == start_function:
                start_func = func
            if func.name == end_function:
                end_func = func
                
        if not start_func or not end_func:
            missing = []
            if not start_func:
                missing.append(f"Start function '{start_function}'")
            if not end_func:
                missing.append(f"End function '{end_function}'")
                
            return {
                "error": f"Function(s) not found: {', '.join(missing)}",
                "paths_count": 0,
                "paths": [],
                "visualization_data": {}
            }
            
        # Create a directed graph
        G = nx.DiGraph()
        
        # Build the complete call graph
        for func in self.codebase.functions:
            # Add the current function as a node
            G.add_node(func.name, file=func.file.file_path if hasattr(func, "file") else "Unknown")
            
            # Process all function calls
            for call in func.function_calls:
                called_func = call.function_definition
                
                # Skip if the called function is external
                if not hasattr(called_func, "name"):
                    continue
                    
                # Add the called function as a node
                G.add_node(called_func.name, file=called_func.file.file_path if hasattr(called_func, "file") else "Unknown")
                
                # Add an edge from the current function to the called function
                G.add_edge(func.name, called_func.name)
        
        # Find all simple paths between the start and end functions
        paths = []
        try:
            paths = list(nx.all_simple_paths(G, start_function, end_function, cutoff=10))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            # No path exists or node not found
            pass
        
        # Prepare the result
        result = {
            "paths_count": len(paths),
            "paths": paths,
            "visualization_data": {
                "nodes": [{"id": node, "file": G.nodes[node]["file"]} for node in G.nodes()],
                "edges": [{"source": u, "target": v} for u, v in G.edges()],
                "highlighted_paths": paths
            }
        }
        
        return result

