"""
API module for Codegen-on-OSS

This module provides API endpoints for accessing analysis results,
snapshots, and other data.
"""

from codegen_on_oss.api.graphql import create_graphql_app
from codegen_on_oss.api.rest import create_rest_app
from codegen_on_oss.api.websocket import WebSocketManager

__all__ = ["create_graphql_app", "create_rest_app", "WebSocketManager"]

