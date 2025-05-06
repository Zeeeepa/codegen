"""
Enums module for graph-sitter.
"""

from enum import Enum, auto


class SymbolType(Enum):
    """Symbol types."""
    Function = auto()
    Class = auto()
    GlobalVar = auto()
    Interface = auto()


class EdgeType(Enum):
    """Edge types."""
    SYMBOL_USAGE = auto()
    IMPORT_SYMBOL_RESOLUTION = auto()
    EXPORT = auto()

