"""
Research extension for agentgen.

This module provides tools for research, including context understanding,
information retrieval, and analysis.
"""

from .context_understanding import (
    ContextItem,
    ContextCollection,
    ContextAnalyzer,
    ContextManager,
)

__all__ = [
    "ContextItem",
    "ContextCollection",
    "ContextAnalyzer",
    "ContextManager",
]
