"""
API package for the codegen-on-oss system.

This package provides API endpoints for accessing analysis data.
"""

from codegen_on_oss.api.rest import router as rest_router
from codegen_on_oss.api.websocket_manager import websocket_manager

__all__ = ["rest_router", "websocket_manager"]
