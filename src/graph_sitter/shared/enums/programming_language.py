"""
Programming language enum for graph-sitter.
"""

from enum import Enum, auto


class ProgrammingLanguage(Enum):
    """Programming languages."""
    PYTHON = auto()
    TYPESCRIPT = auto()
    JAVASCRIPT = auto()
    UNSUPPORTED = auto()
    OTHER = auto()

