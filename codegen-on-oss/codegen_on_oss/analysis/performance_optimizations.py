#!/usr/bin/env python3
"""
Performance optimizations for the codebase analyzer.

This module provides performance optimizations for the codebase analyzer
to handle large codebases efficiently.
"""

import functools
import os
import pickle
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, cast

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')


class AnalysisCache:
    """
    Cache for analysis results to avoid redundant calculations.
    
    This class provides a simple caching mechanism for analysis results
    to avoid redundant calculations when analyzing large codebases.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the analysis cache.
        
        Args:
            cache_dir: Directory to store cache files
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "codegen-on-oss" / "analysis"
        
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.memory_cache: Dict[str, Any] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        # Check memory cache first
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        # Check disk cache
        cache_file = self.cache_dir / f"{key}.pickle"
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    value = pickle.load(f)
                
                # Store in memory cache for faster access
                self.memory_cache[key] = value
                
                return value
            except Exception:
                # If there's an error loading the cache, ignore it
                return None
        
        return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        # Store in memory cache
        self.memory_cache[key] = value
        
        # Store in disk cache
        cache_file = self.cache_dir / f"{key}.pickle"
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(value, f)
        except Exception:
            # If there's an error saving the cache, ignore it
            pass
    
    def clear(self) -> None:
        """Clear the cache."""
        # Clear memory cache
        self.memory_cache.clear()
        
        # Clear disk cache
        for cache_file in self.cache_dir.glob("*.pickle"):
            try:
                os.remove(cache_file)
            except Exception:
                # If there's an error removing the cache file, ignore it
                pass


def cached_analysis(func: Callable[..., R]) -> Callable[..., R]:
    """
    Decorator to cache analysis results.
    
    This decorator caches the results of analysis functions to avoid
    redundant calculations when analyzing large codebases.
    
    Args:
        func: Function to cache
        
    Returns:
        Cached function
    """
    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> R:
        # Get the cache
        if not hasattr(self, "_analysis_cache"):
            self._analysis_cache = AnalysisCache()
        
        # Generate a cache key
        key = f"{func.__name__}_{hash(str(args))}_{hash(str(kwargs))}"
        
        # Check if the result is already cached
        cached_result = self._analysis_cache.get(key)
        if cached_result is not None:
            return cast(R, cached_result)
        
        # Call the function
        result = func(self, *args, **kwargs)
        
        # Cache the result
        self._analysis_cache.set(key, result)
        
        return result
    
    return wrapper


def parallel_analysis(func: Callable[..., R]) -> Callable[..., R]:
    """
    Decorator to parallelize analysis functions.
    
    This decorator parallelizes analysis functions to improve performance
    when analyzing large codebases.
    
    Args:
        func: Function to parallelize
        
    Returns:
        Parallelized function
    """
    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> R:
        # Check if parallelization is enabled
        if not getattr(self, "_enable_parallel", True):
            return func(self, *args, **kwargs)
        
        # Import multiprocessing here to avoid issues with pickle
        import multiprocessing
        
        # Get the number of processes
        num_processes = min(multiprocessing.cpu_count(), 4)
        
        # Define a helper function to run the analysis in a separate process
        def run_analysis() -> R:
            return func(self, *args, **kwargs)
        
        # Create a process pool
        with multiprocessing.Pool(processes=num_processes) as pool:
            # Run the analysis in a separate process
            result = pool.apply(run_analysis)
        
        return result
    
    return wrapper


def memory_optimized(func: Callable[..., R]) -> Callable[..., R]:
    """
    Decorator to optimize memory usage.
    
    This decorator optimizes memory usage when analyzing large codebases
    by clearing unnecessary data after the analysis is complete.
    
    Args:
        func: Function to optimize
        
    Returns:
        Memory-optimized function
    """
    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> R:
        # Call the function
        result = func(self, *args, **kwargs)
        
        # Clear any temporary data
        if hasattr(self, "_temp_data"):
            self._temp_data.clear()
        
        # Force garbage collection
        import gc
        gc.collect()
        
        return result
    
    return wrapper


def timed_analysis(func: Callable[..., R]) -> Callable[..., R]:
    """
    Decorator to time analysis functions.
    
    This decorator times analysis functions to help identify performance
    bottlenecks when analyzing large codebases.
    
    Args:
        func: Function to time
        
    Returns:
        Timed function
    """
    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> R:
        # Get the logger
        import logging
        logger = logging.getLogger(__name__)
        
        # Start timing
        start_time = time.time()
        
        # Call the function
        result = func(self, *args, **kwargs)
        
        # End timing
        end_time = time.time()
        duration = end_time - start_time
        
        # Log the duration
        logger.info(f"{func.__name__} took {duration:.2f} seconds")
        
        return result
    
    return wrapper


def incremental_analysis(func: Callable[..., R]) -> Callable[..., R]:
    """
    Decorator for incremental analysis.
    
    This decorator enables incremental analysis to only analyze changes
    since the last analysis, which can significantly improve performance
    when analyzing large codebases.
    
    Args:
        func: Function to make incremental
        
    Returns:
        Incremental function
    """
    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> R:
        # Check if incremental analysis is enabled
        if not getattr(self, "_enable_incremental", True):
            return func(self, *args, **kwargs)
        
        # Get the cache
        if not hasattr(self, "_analysis_cache"):
            self._analysis_cache = AnalysisCache()
        
        # Generate a cache key
        key = f"{func.__name__}_incremental_{hash(str(args))}_{hash(str(kwargs))}"
        
        # Get the last analysis time
        last_analysis_time = self._analysis_cache.get(f"{key}_time")
        
        # Check if we have a previous result
        previous_result = self._analysis_cache.get(key)
        
        # Check if the codebase has changed since the last analysis
        if last_analysis_time is not None and previous_result is not None:
            # Get the last modification time of the codebase
            if hasattr(self, "repo_path") and self.repo_path:
                repo_path = Path(self.repo_path)
                last_modified = max(
                    os.path.getmtime(os.path.join(root, file))
                    for root, _, files in os.walk(repo_path)
                    for file in files
                )
                
                # If the codebase hasn't changed, return the previous result
                if last_modified < last_analysis_time:
                    return cast(R, previous_result)
        
        # Call the function
        result = func(self, *args, **kwargs)
        
        # Cache the result and the current time
        self._analysis_cache.set(key, result)
        self._analysis_cache.set(f"{key}_time", time.time())
        
        return result
    
    return wrapper


# Apply all optimizations
def optimized_analysis(func: Callable[..., R]) -> Callable[..., R]:
    """
    Apply all optimizations to an analysis function.
    
    This decorator applies all optimizations to an analysis function:
    - Caching
    - Parallelization
    - Memory optimization
    - Timing
    - Incremental analysis
    
    Args:
        func: Function to optimize
        
    Returns:
        Optimized function
    """
    return cached_analysis(
        parallel_analysis(
            memory_optimized(
                timed_analysis(
                    incremental_analysis(func)
                )
            )
        )
    )

