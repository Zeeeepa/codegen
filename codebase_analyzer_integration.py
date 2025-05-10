    def get_call_chain_analysis(self) -> Dict[str, Any]:
        """
        Analyze call chains between functions.
        
        This function traces and analyzes function call chains in the codebase,
        identifying the longest chains, most called functions, and complex call patterns.
        
        Returns:
            Dict containing call chain analysis results
        """
        if not self.codebase:
            return {"error": "Codebase not initialized"}
            
        return get_call_chain_analysis(self.codebase)
        
    def get_dead_code_detection_with_filtering(self, exclude_patterns: List[str] = None) -> Dict[str, Any]:
        """
        Detect dead code in the codebase with filtering options.
        
        This function identifies functions, classes, and methods that are defined but never used
        in the codebase, with the ability to exclude certain patterns from analysis.
        
        Args:
            exclude_patterns: List of regex patterns to exclude from dead code detection
            
        Returns:
            Dict containing dead code analysis results with filtering
        """
        if not self.codebase:
            return {"error": "Codebase not initialized"}
            
        return get_dead_code_detection_with_filtering(self.codebase, exclude_patterns)
        
    def get_path_finding_in_call_graphs(self, source_function: str = None, target_function: str = None, max_depth: int = 10) -> Dict[str, Any]:
        """
        Find paths between functions in the call graph.
        
        This function identifies all possible paths between a source function and a target function
        in the call graph, with options to limit the search depth.
        
        Args:
            source_function: Name of the source function (if None, all entry points are considered)
            target_function: Name of the target function (if None, all functions are considered)
            max_depth: Maximum depth of the search
            
        Returns:
            Dict containing path finding results
        """
        if not self.codebase:
            return {"error": "Codebase not initialized"}
            
        return get_path_finding_in_call_graphs(self.codebase, source_function, target_function, max_depth)
        
    def get_dead_symbol_detection(self) -> Dict[str, Any]:
        """
        Detect dead symbols in the codebase.
        
        This function identifies symbols (functions, classes, variables) that are defined
        but never used in the codebase.
        
        Returns:
            Dict containing dead symbol analysis results
        """
        if not self.codebase:
            return {"error": "Codebase not initialized"}
            
        return get_dead_symbol_detection(self.codebase)
        
    def get_symbol_import_analysis(self) -> Dict[str, Any]:
        """
        Analyze symbol imports in the codebase.
        
        This function analyzes how symbols are imported and used across the codebase,
        identifying patterns, potential issues, and optimization opportunities.
        
        Returns:
            Dict containing symbol import analysis results
        """
        if not self.codebase:
            return {"error": "Codebase not initialized"}
            
        return get_symbol_import_analysis(self.codebase)
