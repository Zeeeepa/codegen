"""
Organization-related database models.

Models for organizations, their settings, and membership relationships.
"""

from typing import List, Optional
from sqlalchemy import Column, String, Text, Boolean, Integer, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped

from .base import BaseModel, SoftDeleteMixin, AuditMixin, StatusMixin


class Organization(BaseModel, SoftDeleteMixin, AuditMixin, StatusMixin):
    """
    Organization model representing a Codegen organization.
    
    Maps to the API endpoint: GET /v1/organizations
    UI Data Flow: Organization selector, dashboard header, settings pages
    """
    
    # Basic organization information
    name = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Organization identifiers
    slug = Column(String(100), unique=True, nullable=False, index=True)
    external_id = Column(String(255), nullable=True, index=True)  # GitHub org ID, etc.
    
    # Organization configuration
    avatar_url = Column(String(500), nullable=True)
    website_url = Column(String(500), nullable=True)
    
    # Billing and limits
    plan_type = Column(String(50), default='free', nullable=False)
    agent_run_limit = Column(Integer, default=100, nullable=False)
    agent_runs_used = Column(Integer, default=0, nullable=False)
    
    # Feature flags
    features_enabled = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    members: Mapped[List["OrganizationMember"]] = relationship(
        "OrganizationMember", 
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    
    settings: Mapped[Optional["OrganizationSettings"]] = relationship(
        "OrganizationSettings", 
        back_populates="organization",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    repositories: Mapped[List["Repository"]] = relationship(
        "Repository", 
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    
    agent_runs: Mapped[List["AgentRun"]] = relationship(
        "AgentRun", 
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    
    def can_create_agent_run(self) -> bool:
        """Check if organization can create a new agent run."""
        return self.agent_runs_used < self.agent_run_limit
    
    def increment_agent_runs(self) -> None:
        """Increment the agent runs counter."""
        self.agent_runs_used += 1
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled for this organization."""
        return self.features_enabled.get(feature, False)


class OrganizationSettings(BaseModel, AuditMixin):
    """
    Organization settings and preferences.
    
    UI Data Flow: Settings pages, configuration forms, feature toggles
    """
    
    organization_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("organization.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    
    # GitHub integration settings
    github_installation_id = Column(String(255), nullable=True)
    github_app_id = Column(String(255), nullable=True)
    github_webhook_secret = Column(String(255), nullable=True)
    
    # Linear integration settings
    linear_api_key = Column(String(255), nullable=True)
    linear_webhook_secret = Column(String(255), nullable=True)
    linear_team_id = Column(String(255), nullable=True)
    
    # Slack integration settings
    slack_bot_token = Column(String(255), nullable=True)
    slack_webhook_url = Column(String(500), nullable=True)
    slack_channel_id = Column(String(255), nullable=True)
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True, nullable=False)
    slack_notifications = Column(Boolean, default=False, nullable=False)
    webhook_notifications = Column(Boolean, default=False, nullable=False)
    
    # Agent run preferences
    default_agent_timeout = Column(Integer, default=3600, nullable=False)  # 1 hour
    auto_retry_failed_runs = Column(Boolean, default=True, nullable=False)
    max_concurrent_runs = Column(Integer, default=5, nullable=False)
    
    # PRD management settings
    prd_auto_generation = Column(Boolean, default=False, nullable=False)
    prd_pro_mode_enabled = Column(Boolean, default=False, nullable=False)
    prd_default_generations = Column(Integer, default=3, nullable=False)
    prd_default_temperature = Column(Integer, default=7, nullable=False)  # 0.7 * 10
    
    # Security settings
    require_2fa = Column(Boolean, default=False, nullable=False)
    allowed_ip_ranges = Column(JSON, default=list, nullable=False)
    api_rate_limit = Column(Integer, default=1000, nullable=False)  # requests per hour
    
    # Custom settings (JSON for flexibility)
    custom_settings = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", 
        back_populates="settings"
    )


class OrganizationMember(BaseModel, AuditMixin, StatusMixin):
    """
    Organization membership model.
    
    UI Data Flow: Member lists, permission management, user profiles
    """
    
    organization_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Role and permissions
    role = Column(String(50), default='member', nullable=False, index=True)
    permissions = Column(JSON, default=list, nullable=False)
    
    # Membership details
    invited_by_id = Column(UUID(as_uuid=True), nullable=True)
    invited_at = Column(String(255), nullable=True)  # ISO datetime string
    joined_at = Column(String(255), nullable=True)   # ISO datetime string
    
    # Access control
    is_active = Column(Boolean, default=True, nullable=False)
    last_active_at = Column(String(255), nullable=True)
    
    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", 
        back_populates="members"
    )
    
    user: Mapped["User"] = relationship(
        "User", 
        back_populates="organization_memberships"
    )
    
    def has_permission(self, permission: str) -> bool:
        """Check if member has a specific permission."""
        return permission in self.permissions
    
    def add_permission(self, permission: str) -> None:
        """Add a permission to the member."""
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def remove_permission(self, permission: str) -> None:
        """Remove a permission from the member."""
        if permission in self.permissions:
            self.permissions.remove(permission)
    
    def is_admin(self) -> bool:
        """Check if member is an admin."""
        return self.role in ['admin', 'owner']
    
    def can_manage_members(self) -> bool:
        """Check if member can manage other members."""
        return self.is_admin() or self.has_permission('manage_members')
