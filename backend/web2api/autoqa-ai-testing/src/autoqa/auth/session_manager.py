"""
Session lifecycle management for service authentication.

Manages browser sessions with cookie persistence, session validation,
and automatic refresh for efficient service access.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from autoqa.adapters.owl import OwlBrowserAdapter
from autoqa.auth.credential_store import CredentialStore
from autoqa.storage.database import (
    DatabaseManager,
    ServiceModel,
    ServiceSessionModel,
)

logger = structlog.get_logger(__name__)


class SessionManager:
    """
    Manages authenticated browser sessions for web services.

    Features:
    - Session creation with automatic login
    - Cookie persistence for session reuse
    - Session validation and health checks
    - Automatic session refresh on expiry
    - Multi-tab support per session

    Usage:
        manager = SessionManager(db_manager, credential_store, browser_adapter)

        # Create or restore session
        session = await manager.create_session(service_id="k2think", credentials_ref="...")

        # Validate session
        is_valid = await manager.validate_session(session_id)

        # Use session
        await manager.execute_in_session(session_id, lambda page: page.navigate(...))
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        credential_store: CredentialStore,
        browser_adapter: OwlBrowserAdapter,
        session_ttl_hours: int = 24
    ):
        """
        Initialize session manager.

        Args:
            db_manager: Database manager for persistence
            credential_store: Encrypted credential store
            browser_adapter: Owl-Browser adapter instance
            session_ttl_hours: Default session TTL in hours
        """
        self._db = db_manager
        self._credentials = credential_store
        self._browser = browser_adapter
        self._session_ttl = timedelta(hours=session_ttl_hours)

        self._log = logger.bind(component="session_manager")

        # Active sessions cache (in-memory)
        self._active_sessions: Dict[str, Dict[str, Any]] = {}

    async def create_session(
        self,
        service_id: str,
        credentials_ref: str,
        auto_login: bool = True
    ) -> str:
        """
        Create a new authenticated session for a service.

        Args:
            service_id: Service identifier
            credentials_ref: Encrypted credentials reference
            auto_login: Automatically perform login flow

        Returns:
            Session ID

        Raises:
            AuthError: If login fails
        """
        session_id = uuid.uuid4()

        # Get service info
        async with self._db.session() as session:
            result = await session.execute(
                select(ServiceModel).where(ServiceModel.id == uuid.UUID(service_id))
            )
            service = result.scalar_one_or_none()

            if not service:
                raise AuthError(f"Service not found: {service_id}")

        # Create browser session
        try:
            # Auto-login if requested
            cookies = None
            login_success = False

            if auto_login:
                # Perform login flow
                credentials = self._credentials.get_credentials(credentials_ref)

                login_success = await self._perform_login(
                    service.base_url,
                    credentials["data"]
                )

                if login_success:
                    # Capture cookies after successful login
                    cookies = self._browser.get_cookies()

            # Calculate expiry
            expires_at = datetime.utcnow() + self._session_ttl

            # Save session to database
            async with self._db.session() as session:
                db_session = ServiceSessionModel(
                    id=session_id,
                    service_id=uuid.UUID(service_id),
                    owl_session_id=str(uuid.uuid4()),
                    tabs=[],
                    cookies_ref=credentials_ref if cookies else None,
                    state="active",
                    expires_at=expires_at,
                )
                session.add(db_session)

            # Cache in memory
            self._active_sessions[str(session_id)] = {
                "service_id": service_id,
                "created_at": datetime.utcnow(),
                "expires_at": expires_at,
                "cookies": cookies,
            }

            self._log.info(
                "Session created",
                session_id=str(session_id),
                service_id=service_id,
                auto_login=auto_login,
                login_success=login_success
            )

            return str(session_id)

        except Exception as e:
            self._log.error("Failed to create session", service_id=service_id, error=str(e))
            raise

    async def restore_session(self, session_id: str) -> bool:
        """
        Restore a session from persisted cookies.

        Args:
            session_id: Session ID

        Returns:
            True if session restored successfully
        """
        try:
            # Get session from database
            async with self._db.session() as session:
                result = await session.execute(
                    select(ServiceSessionModel).where(
                        ServiceSessionModel.id == uuid.UUID(session_id)
                    )
                )
                db_session = result.scalar_one_or_none()

                if not db_session:
                    return False

                # Check if session is expired
                if db_session.expires_at and datetime.utcnow() > db_session.expires_at:
                    await self.expire_session(session_id)
                    return False

                # Get stored cookies
                if db_session.cookies_ref:
                    credentials = self._credentials.get_credentials(db_session.cookies_ref)
                    cookies = credentials.get("cookies", [])

                    # Restore cookies in browser
                    for cookie in cookies:
                        self._browser.set_cookie(
                            url=cookie.get("url", ""),
                            name=cookie["name"],
                            value=cookie["value"],
                            domain=cookie.get("domain"),
                            path=cookie.get("path", "/"),
                            secure=cookie.get("secure", False),
                            http_only=cookie.get("http_only", False)
                        )

                # Cache in memory
                self._active_sessions[session_id] = {
                    "service_id": str(db_session.service_id),
                    "created_at": db_session.created_at,
                    "expires_at": db_session.expires_at,
                }

                self._log.info("Session restored", session_id=session_id)
                return True

        except Exception as e:
            self._log.error("Failed to restore session", session_id=session_id, error=str(e))
            return False

    async def validate_session(self, session_id: str) -> bool:
        """
        Validate if session is active and not expired.

        Args:
            session_id: Session ID

        Returns:
            True if session is valid
        """
        try:
            # Check cache first
            if session_id in self._active_sessions:
                cached = self._active_sessions[session_id]
                if datetime.utcnow() < cached["expires_at"]:
                    return True
                else:
                    # Session expired, remove from cache
                    del self._active_sessions[session_id]
                    return False

            # Check database
            async with self._db.session() as session:
                result = await session.execute(
                    select(ServiceSessionModel).where(
                        ServiceSessionModel.id == uuid.UUID(session_id)
                    )
                )
                db_session = result.scalar_one_or_none()

                if not db_session or db_session.state != "active":
                    return False

                # Check expiry
                if db_session.expires_at and datetime.utcnow() > db_session.expires_at:
                    await self.expire_session(session_id)
                    return False

                # Add to cache
                self._active_sessions[session_id] = {
                    "service_id": str(db_session.service_id),
                    "created_at": db_session.created_at,
                    "expires_at": db_session.expires_at,
                }

                return True

        except Exception as e:
            self._log.error("Failed to validate session", session_id=session_id, error=str(e))
            return False

    async def expire_session(self, session_id: str) -> bool:
        """
        Mark session as expired.

        Args:
            session_id: Session ID

        Returns:
            True if session expired successfully
        """
        try:
            # Remove from cache
            if session_id in self._active_sessions:
                del self._active_sessions[session_id]

            # Update database
            async with self._db.session() as session:
                result = await session.execute(
                    select(ServiceSessionModel).where(
                        ServiceSessionModel.id == uuid.UUID(session_id)
                    )
                )
                db_session = result.scalar_one_or_none()

                if db_session:
                    db_session.state = "expired"

            self._log.info("Session expired", session_id=session_id)
            return True

        except Exception as e:
            self._log.error("Failed to expire session", session_id=session_id, error=str(e))
            return False

    async def refresh_session(self, session_id: str) -> bool:
        """
        Refresh session expiry time.

        Args:
            session_id: Session ID

        Returns:
            True if session refreshed successfully
        """
        try:
            new_expiry = datetime.utcnow() + self._session_ttl

            # Update cache
            if session_id in self._active_sessions:
                self._active_sessions[session_id]["expires_at"] = new_expiry

            # Update database
            async with self._db.session() as session:
                result = await session.execute(
                    select(ServiceSessionModel).where(
                        ServiceSessionModel.id == uuid.UUID(session_id)
                    )
                )
                db_session = result.scalar_one_or_none()

                if db_session:
                    db_session.expires_at = new_expiry

            self._log.info("Session refreshed", session_id=session_id)
            return True

        except Exception as e:
            self._log.error("Failed to refresh session", session_id=session_id, error=str(e))
            return False

    async def _perform_login(
        self,
        base_url: str,
        credentials: Dict[str, Any]
    ) -> bool:
        """
        Perform automated login flow.

        Args:
            base_url: Service base URL
            credentials: Credential data (email, password, etc.)

        Returns:
            True if login successful

        TODO: Integrate with auto-discovery auth_detector and form_filler
        """
        try:
            # Navigate to login page
            login_url = f"{base_url.rstrip('/')}/login"
            self._browser.navigate(login_url)

            # Simple login flow (will be replaced by auth_detector)
            email = credentials.get("email")
            password = credentials.get("password")

            if not (email and password):
                self._log.warning("Missing email/password in credentials")
                return False

            # Try common selectors
            email_selectors = [
                "#email",
                "input[type='email']",
                "input[name='email']",
                "input[placeholder*='email']",
                "input[placeholder*='Email']",
            ]

            password_selectors = [
                "#password",
                "input[type='password']",
                "input[name='password']",
            ]

            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('Login')",
                "button:contains('Sign In')",
            ]

            # Fill email
            email_filled = False
            for selector in email_selectors:
                try:
                    if self._browser.is_visible(selector):
                        self._browser.type(selector, email)
                        email_filled = True
                        break
                except:
                    continue

            if not email_filled:
                self._log.warning("Could not find email input field")
                return False

            # Fill password
            password_filled = False
            for selector in password_selectors:
                try:
                    if self._browser.is_visible(selector):
                        self._browser.type(selector, password)
                        password_filled = True
                        break
                except:
                    continue

            if not password_filled:
                self._log.warning("Could not find password input field")
                return False

            # Submit form
            submitted = False
            for selector in submit_selectors:
                try:
                    if self._browser.is_visible(selector):
                        self._browser.click(selector)
                        submitted = True
                        break
                except:
                    continue

            if not submitted:
                self._log.warning("Could not find submit button")
                return False

            # Wait for navigation
            import time
            time.sleep(3)

            # Verify login success
            current_url = self._browser.get_url()
            success = "login" not in current_url.lower()

            self._log.info(
                "Login attempt completed",
                success=success,
                current_url=current_url
            )

            return success

        except Exception as e:
            self._log.error("Login failed", error=str(e))
            return False

    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions in database.

        Returns:
            Number of sessions cleaned up
        """
        try:
            async with self._db.session() as session:
                result = await session.execute(
                    select(ServiceSessionModel).where(
                        ServiceSessionModel.state == "active",
                        ServiceSessionModel.expires_at < datetime.utcnow()
                    )
                )
                expired = result.scalars().all()

                count = 0
                for db_session in expired:
                    db_session.state = "expired"
                    count += 1

                    # Remove from cache
                    session_id = str(db_session.id)
                    if session_id in self._active_sessions:
                        del self._active_sessions[session_id]

            self._log.info("Cleaned up expired sessions", count=count)
            return count

        except Exception as e:
            self._log.error("Failed to cleanup sessions", error=str(e))
            return 0
