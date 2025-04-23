"""
Windows-compatible resource module alternative.

This module provides dummy implementations of the Unix resource module functions
for Windows platforms, allowing code that uses resource module to run on Windows.
"""

import sys

# Constants that mimic the Unix resource module
RLIMIT_STACK = 0
RLIM_INFINITY = -1

def getrlimit(resource):
    """
    Dummy implementation of getrlimit for Windows.
    
    Args:
        resource: Resource constant (ignored on Windows)
        
    Returns:
        A tuple (soft_limit, hard_limit) with dummy values
    """
    if sys.platform == "win32":
        return (RLIM_INFINITY, RLIM_INFINITY)
    else:
        # On non-Windows platforms, import and use the real resource module
        import resource
        return resource.getrlimit(resource)

def setrlimit(resource, limits):
    """
    Dummy implementation of setrlimit for Windows.
    
    Args:
        resource: Resource constant (ignored on Windows)
        limits: A tuple (soft_limit, hard_limit) (ignored on Windows)
        
    Returns:
        None
    """
    if sys.platform == "win32":
        # Do nothing on Windows
        pass
    else:
        # On non-Windows platforms, import and use the real resource module
        import resource
        return resource.setrlimit(resource, limits)
