"""
Analysis context for PR analysis.

This module provides the AnalysisContext class, which holds all the necessary
context information for analyzing a pull request, including repository information,
PR data, and analysis configuration.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from codegen_on_oss.analysis.pr_analysis.git.models import PullRequest, Repository


@dataclass
class AnalysisContext:
    """
    Context object for PR analysis.
    
    This class holds all the necessary context information for analyzing a pull request,
    including repository information, PR data, and analysis configuration.
    
    Attributes:
        repository: Repository information
        pull_request: Pull request data
        config: Analysis configuration
        cache: Cache for analysis results
        metadata: Additional metadata for analysis
    """
    
    repository: Repository
    pull_request: PullRequest
    config: Dict[str, Any] = field(default_factory=dict)
    cache: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
    
    def set_config(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
    
    def cache_result(self, key: str, value: Any) -> None:
        """
        Cache an analysis result.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self.cache[key] = value
    
    def get_cached_result(self, key: str, default: Any = None) -> Any:
        """
        Get a cached analysis result.
        
        Args:
            key: Cache key
            default: Default value if key is not found
            
        Returns:
            Cached value or default
        """
        return self.cache.get(key, default)
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata for analysis.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata for analysis.
        
        Args:
            key: Metadata key
            default: Default value if key is not found
            
        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)

