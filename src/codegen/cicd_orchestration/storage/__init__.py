"""
Unified Storage Management

Simple storage coordination for the CI/CD orchestration system following
KISS principles. Provides basic storage capabilities without unnecessary complexity.

For now, implements simple in-memory storage with plans for future expansion
to SQLite, Redis, and other storage backends as needed.
"""

from .unified_storage_manager import UnifiedStorageManager

__all__ = [
    "UnifiedStorageManager",
]
