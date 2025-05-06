"""
Utils Package

This package provides utility functions for PR analysis.
"""

from .diff_utils import (
    parse_diff,
    get_changed_lines,
    compute_diff,
    get_line_changes,
    highlight_diff,
)
from .integration import (
    create_codebase_context,
    convert_pull_request_context,
    create_github_client,
    create_diff_analyzer,
    create_code_integrity_analyzer,
)

# Export all utility functions
__all__ = [
    'parse_diff',
    'get_changed_lines',
    'compute_diff',
    'get_line_changes',
    'highlight_diff',
    'create_codebase_context',
    'convert_pull_request_context',
    'create_github_client',
    'create_diff_analyzer',
    'create_code_integrity_analyzer',
]

