"""
FastAPI gateway for AutoQA testing system.

Provides REST API for test execution, results, and management.
"""

from autoqa.api.main import create_app, run_server

__all__ = [
    "create_app",
    "run_server",
]
