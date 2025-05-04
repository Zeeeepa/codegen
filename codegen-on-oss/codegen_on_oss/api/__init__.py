"""
API module for codegen-on-oss.

This module provides a unified API for interacting with the codegen-on-oss package,
making it easier to use the various components for code analysis, snapshot management,
and code integrity validation.
"""

from codegen_on_oss.api.unified_api import (
    UnifiedAPI,
    analyze_repository,
    analyze_commit,
    analyze_pull_request,
    compare_branches,
    create_snapshot,
    compare_snapshots,
    analyze_code_integrity,
    batch_analyze_repositories,
)

__all__ = [
    "UnifiedAPI",
    "analyze_repository",
    "analyze_commit",
    "analyze_pull_request",
    "compare_branches",
    "create_snapshot",
    "compare_snapshots",
    "analyze_code_integrity",
    "batch_analyze_repositories",
]

