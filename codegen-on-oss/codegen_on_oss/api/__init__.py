"""
API package for the codegen-on-oss system.

This package provides API endpoints for accessing analysis data.
"""

from codegen_on_oss.api.public_api import CodegenOnOSS
from codegen_on_oss.api.rest import router as rest_router
from codegen_on_oss.api.websocket_manager import websocket_manager

# Public API exports
from codegen_on_oss.api.public_api import (
    parse_repository_func as parse_repository,
    analyze_codebase_func as analyze_codebase,
    analyze_code_integrity_func as analyze_code_integrity,
    analyze_commit_func as analyze_commit,
    analyze_diff_func as analyze_diff,
    create_snapshot_func as create_snapshot,
    compare_snapshots_func as compare_snapshots,
)

__all__ = [
    "CodegenOnOSS",
    "rest_router", 
    "websocket_manager",
    "parse_repository",
    "analyze_codebase",
    "analyze_code_integrity",
    "analyze_commit",
    "analyze_diff",
    "create_snapshot",
    "compare_snapshots",
]
