"""
Authentication and session management for Web2API services.

Provides encrypted credential storage and session lifecycle management.
"""

from autoqa.auth.credential_store import CredentialStore
from autoqa.auth.session_manager import SessionManager

__all__ = ["CredentialStore", "SessionManager"]
