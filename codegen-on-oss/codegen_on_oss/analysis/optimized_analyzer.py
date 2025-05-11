#!/usr/bin/env python3
"""
Optimized Codebase Analyzer

This module provides an optimized version of the codebase analyzer
that uses performance optimizations to handle large codebases efficiently.
"""

import sys
from typing import Dict, List, Any, Optional

from .codebase_analyzer import CodebaseAnalyzer as BaseCodebaseAnalyzer
from .performance_optimizations import (
    cached_analysis,
    parallel_analysis,
    memory_optimized,
    timed_analysis,
    incremental_analysis,
    optimized_analysis,
)


class OptimizedCodebaseAnalyzer(BaseCodebaseAnalyzer):
    """
    Optimized version of the codebase analyzer.
    
    This class extends the base codebase analyzer with performance optimizations
    to handle large codebases efficiently.
    """
    
    def __init__(self, repo_url: str = None, repo_path: str = None, language: str = None):
        """
        Initialize the OptimizedCodebaseAnalyzer.
        
        Args:
            repo_url: URL of the repository to analyze
            repo_path: Local path to the repository to analyze
            language: Programming language of the codebase (auto-detected if not provided)
        """
        super().__init__(repo_url, repo_path, language)
        self._temp_data = {}
        self._enable_parallel = True
        self._enable_incremental = True
    
    @optimized_analysis
    def analyze(self, categories: List[str] = None, output_format: str = "json", output_file: str = None) -> Dict[str, Any]:
        """
        Perform a comprehensive analysis of the codebase with performance optimizations.
        
        Args:
            categories: List of categories to analyze. If None, all categories are analyzed.
            output_format: Format of the output (json, html, console)
            output_file: Path to the output file
            
        Returns:
            Dict containing the analysis results
        """
        return super().analyze(categories, output_format, output_file)
    
    @optimized_analysis
    def get_file_count(self) -> Dict[str, int]:
        """Get the number of files in the codebase with performance optimizations."""
        return super().get_file_count()
    
    @optimized_analysis
    def get_files_by_language(self) -> Dict[str, int]:
        """Get the number of files by language with performance optimizations."""
        return super().get_files_by_language()
    
    @optimized_analysis
    def get_file_size_distribution(self) -> Dict[str, Any]:
        """Get the distribution of file sizes with performance optimizations."""
        return super().get_file_size_distribution()
    
    @optimized_analysis
    def get_directory_structure(self) -> Dict[str, Any]:
        """Get the directory structure with performance optimizations."""
        return super().get_directory_structure()
    
    @optimized_analysis
    def get_symbol_count(self) -> Dict[str, int]:
        """Get the number of symbols in the codebase with performance optimizations."""
        return super().get_symbol_count()
    
    @optimized_analysis
    def get_symbol_type_distribution(self) -> Dict[str, int]:
        """Get the distribution of symbol types with performance optimizations."""
        return super().get_symbol_type_distribution()
    
    @optimized_analysis
    def get_symbol_hierarchy(self) -> Dict[str, Any]:
        """Get the symbol hierarchy with performance optimizations."""
        return super().get_symbol_hierarchy()
    
    @optimized_analysis
    def get_top_level_vs_nested_symbols(self) -> Dict[str, int]:
        """Get the number of top-level vs. nested symbols with performance optimizations."""
        return super().get_top_level_vs_nested_symbols()
    
    @optimized_analysis
    def get_import_dependency_map(self) -> Dict[str, List[str]]:
        """Get the import dependency map with performance optimizations."""
        return super().get_import_dependency_map()
    
    @optimized_analysis
    def get_external_vs_internal_dependencies(self) -> Dict[str, int]:
        """Get the number of external vs. internal dependencies with performance optimizations."""
        return super().get_external_vs_internal_dependencies()
    
    @optimized_analysis
    def get_circular_imports(self) -> List[List[str]]:
        """Get the circular imports with performance optimizations."""
        return super().get_circular_imports()
    
    @optimized_analysis
    def get_unused_imports(self) -> List[Dict[str, str]]:
        """Get the unused imports with performance optimizations."""
        return super().get_unused_imports()
    
    @optimized_analysis
    def get_module_coupling_metrics(self) -> Dict[str, float]:
        """Get the module coupling metrics with performance optimizations."""
        return super().get_module_coupling_metrics()
    
    @optimized_analysis
    def get_module_cohesion_analysis(self) -> Dict[str, float]:
        """Get the module cohesion analysis with performance optimizations."""
        return super().get_module_cohesion_analysis()
    
    @optimized_analysis
    def get_package_structure(self) -> Dict[str, Any]:
        """Get the package structure with performance optimizations."""
        return super().get_package_structure()
    
    @optimized_analysis
    def get_module_dependency_graph(self) -> Dict[str, Any]:
        """Get the module dependency graph with performance optimizations."""
        return super().get_module_dependency_graph()
    
    # Add optimized versions of all other analysis methods
    # ...
    
    def enable_parallel_processing(self, enable: bool = True) -> None:
        """
        Enable or disable parallel processing.
        
        Args:
            enable: Whether to enable parallel processing
        """
        self._enable_parallel = enable
    
    def enable_incremental_analysis(self, enable: bool = True) -> None:
        """
        Enable or disable incremental analysis.
        
        Args:
            enable: Whether to enable incremental analysis
        """
        self._enable_incremental = enable
    
    def clear_cache(self) -> None:
        """Clear the analysis cache."""
        if hasattr(self, "_analysis_cache"):
            self._analysis_cache.clear()


# Update the CodebaseAnalyzer class to use the optimized version
CodebaseAnalyzer = OptimizedCodebaseAnalyzer

