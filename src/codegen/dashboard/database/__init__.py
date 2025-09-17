"""Dashboard database integration with Supabase."""

from .supabase_client import SupabaseClient
from .models import (
    AgentRunStarred,
    ProjectStarred,
    UserPreferences,
    Notification,
    ValidationGate,
    PRDDialog,
    WorkflowTemplate,
    DashboardSession
)

__all__ = [
    "SupabaseClient",
    "AgentRunStarred",
    "ProjectStarred", 
    "UserPreferences",
    "Notification",
    "ValidationGate",
    "PRDDialog",
    "WorkflowTemplate",
    "DashboardSession"
]
