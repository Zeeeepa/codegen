"""
Database package for Codegen - Persistent storage and event-driven architecture.

This package provides:
- SQLAlchemy models for all data entities
- Database middleware for operations
- Event emission system with webhooks
- Real-time synchronization capabilities
"""

from .connection import DatabaseManager, get_db_session
from .middleware import DatabaseMiddleware
from .events import EventEmitter, WebhookManager
from .models import *

__all__ = [
    "DatabaseManager",
    "get_db_session", 
    "DatabaseMiddleware",
    "EventEmitter",
    "WebhookManager",
]
