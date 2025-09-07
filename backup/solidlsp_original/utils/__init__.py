"""
SolidLSP Utilities

Extracted utilities and compatibility layers for SolidLSP integration.
"""

from .text_utils import MatchedConsecutiveLines, TextLine, LineType
from .file_system import match_path
from .sensai_compat import ToStringMixin, LogTime

__all__ = [
    'MatchedConsecutiveLines',
    'TextLine', 
    'LineType',
    'match_path',
    'ToStringMixin',
    'LogTime'
]
