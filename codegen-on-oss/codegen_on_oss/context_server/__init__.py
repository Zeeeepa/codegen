"""
Context server module for providing a REST API to access codebase analysis and context functionality.
"""

from codegen_on_oss.context_server.server import app, create_app

__all__ = ["app", "create_app"]
