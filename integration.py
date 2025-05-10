"""
Integration module for codebase analyzer.

This module provides functions to integrate the codebase analyzer with the SDK modules.
"""

def integrate_codebase_analyzer():
    """
    Integrate the codebase analyzer with the SDK modules.
    
    This function adds the following methods to the CodebaseAnalyzer class:
    - get_call_chain_analysis
    - get_dead_code_detection_with_filtering
    - get_path_finding_in_call_graphs
    - get_dead_symbol_detection
    - get_symbol_import_analysis
    
    Returns:
        None
    """
    # Import the necessary modules
    from call_chain_analysis import get_call_chain_analysis
    from dead_code_detection import get_dead_code_detection_with_filtering
    from dead_symbol_detection import get_dead_symbol_detection
    from path_finding import get_path_finding_in_call_graphs
    from symbol_import_analysis import get_symbol_import_analysis
    
    # Add the methods to the CodebaseAnalyzer class
    from codebase_analyzer import CodebaseAnalyzer
    
    # Add the call chain analysis method
    def get_call_chain_analysis_method(self):
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
    
    # Add the dead code detection method
    def get_dead_code_detection_with_filtering_method(self, exclude_patterns=None):
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
    
    # Add the path finding method
    def get_path_finding_in_call_graphs_method(self, source_function=None, target_function=None, max_depth=10):
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
    
    # Add the dead symbol detection method
    def get_dead_symbol_detection_method(self):
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
    
    # Add the symbol import analysis method
    def get_symbol_import_analysis_method(self):
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
    
    # Add the methods to the CodebaseAnalyzer class
    CodebaseAnalyzer.get_call_chain_analysis = get_call_chain_analysis_method
    CodebaseAnalyzer.get_dead_code_detection_with_filtering = get_dead_code_detection_with_filtering_method
    CodebaseAnalyzer.get_path_finding_in_call_graphs = get_path_finding_in_call_graphs_method
    CodebaseAnalyzer.get_dead_symbol_detection = get_dead_symbol_detection_method
    CodebaseAnalyzer.get_symbol_import_analysis = get_symbol_import_analysis_method

