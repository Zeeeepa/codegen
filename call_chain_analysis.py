    def get_call_chain_analysis(self) -> Dict[str, Any]:
        """
        Analyze call chains between functions.
        
        This function traces and analyzes function call chains in the codebase,
        identifying the longest chains, most called functions, and complex call patterns.
        
        Returns:
            Dict containing call chain analysis results
        """
        call_chain_analysis = {
            "longest_chains": [],
            "most_called_functions": [],
            "complex_call_patterns": [],
            "average_chain_length": 0,
            "max_chain_length": 0,
            "total_chains": 0
        }
        
        try:
            # Create a directed graph of function calls
            G = nx.DiGraph()
            
            # Map to store function objects by their qualified name
            function_map = {}
            
            # Add nodes and edges to the graph
            for function in self.codebase.functions:
                function_name = f"{function.file.file_path}::{function.name}"
                G.add_node(function_name)
                function_map[function_name] = function
                
                # Add edges for each function call
                for call in function.function_calls:
                    if hasattr(call, "function_definition") and call.function_definition:
                        called_func = call.function_definition
                        called_name = f"{called_func.file.file_path if hasattr(called_func, 'file') else 'external'}::{called_func.name}"
                        G.add_node(called_name)
                        G.add_edge(function_name, called_name)
            
            # Find all simple paths in the graph
            all_paths = []
            entry_points = [node for node in G.nodes() if G.in_degree(node) == 0]
            
            for entry in entry_points:
                for node in G.nodes():
                    if entry != node:
                        try:
                            paths = list(nx.all_simple_paths(G, entry, node, cutoff=10))  # Limit path length to avoid exponential explosion
                            all_paths.extend(paths)
                        except (nx.NetworkXNoPath, nx.NodeNotFound):
                            continue
            
            # Calculate statistics
            if all_paths:
                path_lengths = [len(path) for path in all_paths]
                call_chain_analysis["average_chain_length"] = sum(path_lengths) / len(path_lengths)
                call_chain_analysis["max_chain_length"] = max(path_lengths)
                call_chain_analysis["total_chains"] = len(all_paths)
                
                # Get the longest chains
                longest_paths = sorted(all_paths, key=len, reverse=True)[:10]  # Top 10 longest paths
                call_chain_analysis["longest_chains"] = [
                    {
                        "path": [node.split("::")[-1] for node in path],  # Just function names for readability
                        "length": len(path),
                        "files": [node.split("::")[0] for node in path]
                    }
                    for path in longest_paths
                ]
                
                # Get the most called functions
                in_degrees = dict(G.in_degree())
                most_called = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:10]  # Top 10 most called
                call_chain_analysis["most_called_functions"] = [
                    {
                        "function": node.split("::")[-1],
                        "file": node.split("::")[0],
                        "call_count": count
                    }
                    for node, count in most_called if count > 0
                ]
                
                # Identify complex call patterns (e.g., cycles)
                try:
                    cycles = list(nx.simple_cycles(G))
                    call_chain_analysis["complex_call_patterns"] = [
                        {
                            "type": "cycle",
                            "functions": [node.split("::")[-1] for node in cycle],
                            "files": [node.split("::")[0] for node in cycle]
                        }
                        for cycle in cycles[:10]  # Top 10 cycles
                    ]
                except:
                    # Simple cycles might not be available for all graph types
                    call_chain_analysis["complex_call_patterns"] = []
            
            return call_chain_analysis
        except Exception as e:
            logger.error(f"Error in call chain analysis: {e}")
            return {"error": str(e)}
