"""
User-related database models.

Models for users, sessions, and API tokens.
"""

from typing import List, Optional
from sqlalchemy import Column, String, Text, Boolean, Integer, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped

from .base import BaseModel, SoftDeleteMixin, AuditMixin, StatusMixin


class User(BaseModel, SoftDeleteMixin, AuditMixin, StatusMixin):
    """
    User model representing a Codegen user.
    
    Maps to API endpoints: GET /v1/users/me, GET /v1/organizations/{org_id}/users/{user_id}
    UI Data Flow: User profile, authentication, user management
    """
    
    # Basic user information
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    full_name = Column(String(255), nullable=True)
    display_name = Column(String(255), nullable=True)
    
    # Authentication
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth-only users
    is_email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String(255), nullable=True)
    
    # Profile information
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    website_url = Column(String(500), nullable=True)
    
    # GitHub integration
    github_username = Column(String(100), nullable=True, index=True)
    github_user_id = Column(String(50), nullable=True, index=True)
    github_access_token = Column(String(255), nullable=True)
    
    # User preferences
    timezone = Column(String(50), default='UTC', nullable=False)
    language = Column(String(10), default='en', nullable=False)
    theme = Column(String(20), default='light', nullable=False)
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True, nullable=False)
    marketing_emails = Column(Boolean, default=False, nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_staff = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Login tracking
    last_login_at = Column(String(255), nullable=True)  # ISO datetime string
    last_login_ip = Column(String(45), nullable=True)
    login_count = Column(Integer, default=0, nullable=False)
    
    # Two-factor authentication
    is_2fa_enabled = Column(Boolean, default=False, nullable=False)
    totp_secret = Column(String(255), nullable=True)
    backup_codes = Column(JSON, default=list, nullable=False)
    
    # User metadata
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    terms_accepted_at = Column(String(255), nullable=True)
    privacy_policy_accepted_at = Column(String(255), nullable=True)
    
    # Relationships
    organization_memberships: Mapped[List["OrganizationMember"]] = relationship(
        "OrganizationMember", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    sessions: Mapped[List["UserSession"]] = relationship(
        "UserSession", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    api_tokens: Mapped[List["APIToken"]] = relationship(
        "APIToken", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    created_agent_runs: Mapped[List["AgentRun"]] = relationship(
        "AgentRun", 
        back_populates="created_by_user",
        foreign_keys="AgentRun.created_by_user_id"
    )
    
    def get_organizations(self) -> List["Organization"]:
        """Get all organizations this user belongs to."""
        return [membership.organization for membership in self.organization_memberships]
    
    def is_member_of(self, organization_id: str) -> bool:
        """Check if user is a member of the given organization."""
        return any(
            membership.organization_id == organization_id 
            for membership in self.organization_memberships
        )
    
    def get_role_in_organization(self, organization_id: str) -> Optional[str]:
        """Get user's role in a specific organization."""
        for membership in self.organization_memberships:
            if membership.organization_id == organization_id:
                return membership.role
        return None
    
    def has_permission_in_organization(self, organization_id: str, permission: str) -> bool:
        """Check if user has a specific permission in an organization."""
        for membership in self.organization_memberships:
            if membership.organization_id == organization_id:
                return membership.has_permission(permission)
        return False
    
    def increment_login_count(self) -> None:
        """Increment the login counter."""
        self.login_count += 1


class UserSession(BaseModel, StatusMixin):
    """
    User session model for tracking active sessions.
    
    UI Data Flow: Session management, security settings, active sessions list
    """
    
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Session identification
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=True, index=True)
    
    # Session metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(50), nullable=True)  # web, mobile, cli, api
    
    # Session timing
    expires_at = Column(String(255), nullable=False)  # ISO datetime string
    last_activity_at = Column(String(255), nullable=True)
    
    # Session flags
    is_active = Column(Boolean, default=True, nullable=False)
    is_remember_me = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User", 
        back_populates="sessions"
    )
    
    def is_expired(self) -> bool:
        """Check if the session is expired."""
        from datetime import datetime
        try:
            expires_at = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))
            return datetime.utcnow() > expires_at
        except (ValueError, AttributeError):
            return True
    
    def extend_session(self, hours: int = 24) -> None:
        """Extend the session expiration time."""
        from datetime import datetime, timedelta
        new_expiry = datetime.utcnow() + timedelta(hours=hours)
        self.expires_at = new_expiry.isoformat() + 'Z'


class APIToken(BaseModel, SoftDeleteMixin, AuditMixin, StatusMixin):
    """
    API token model for programmatic access.
    
    UI Data Flow: API token management, developer settings, token creation forms
    """
    
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Token identification
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    token_prefix = Column(String(20), nullable=False)  # First few chars for display
    
    # Token permissions and scope
    scopes = Column(JSON, default=list, nullable=False)
    permissions = Column(JSON, default=list, nullable=False)
    
    # Token restrictions
    allowed_ips = Column(JSON, default=list, nullable=False)
    rate_limit = Column(Integer, default=1000, nullable=False)  # requests per hour
    
    # Token timing
    expires_at = Column(String(255), nullable=True)  # ISO datetime string, null = never expires
    last_used_at = Column(String(255), nullable=True)
    
    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)
    last_used_ip = Column(String(45), nullable=True)
    
    # Token flags
    is_active = Column(Boolean, default=True, nullable=False)
    is_read_only = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User", 
        back_populates="api_tokens"
    )
    
    def is_expired(self) -> bool:
        """Check if the token is expired."""
        if not self.expires_at:
            return False
        
        from datetime import datetime
        try:
            expires_at = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))
            return datetime.utcnow() > expires_at
        except (ValueError, AttributeError):
            return True
    
    def has_scope(self, scope: str) -> bool:
        """Check if token has a specific scope."""
        return scope in self.scopes
    
    def has_permission(self, permission: str) -> bool:
        """Check if token has a specific permission."""
        return permission in self.permissions
    
    def increment_usage(self) -> None:
        """Increment the usage counter."""
        self.usage_count += 1
        from datetime import datetime
        self.last_used_at = datetime.utcnow().isoformat() + 'Z'
    
    def is_ip_allowed(self, ip_address: str) -> bool:
        """Check if the IP address is allowed to use this token."""
        if not self.allowed_ips:
            return True
        return ip_address in self.allowed_ips
