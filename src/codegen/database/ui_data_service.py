"""
UI Data Service for Codegen TUI.

Provides database-backed data for the TUI interface, replacing static data sources.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from .middleware import get_database_middleware
from .models.organizations import Organization, OrganizationMember
from .models.users import User, UserSession
from .models.agents import AgentRun, AgentRunLog, AgentTask
from .models.repositories import Repository
from .connection import db_session_scope

logger = logging.getLogger(__name__)


class UIDataService:
    """
    Service for providing UI data from database instead of static sources.
    
    This service replaces all static data access in the TUI with database queries,
    enabling real-time updates and persistent state management.
    """
    
    def __init__(self):
        self.middleware = get_database_middleware()
    
    # Organization Data
    
    def get_user_organizations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all organizations for a user (replaces static org list)."""
        try:
            with db_session_scope() as session:
                # Get user with organization memberships
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    return []
                
                organizations = []
                for membership in user.organization_memberships:
                    if membership.is_active and not membership.organization.is_deleted:
                        org_data = {
                            'id': str(membership.organization.id),
                            'name': membership.organization.name,
                            'display_name': membership.organization.display_name,
                            'slug': membership.organization.slug,
                            'avatar_url': membership.organization.avatar_url,
                            'role': membership.role,
                            'permissions': membership.permissions,
                            'plan_type': membership.organization.plan_type,
                            'agent_runs_used': membership.organization.agent_runs_used,
                            'agent_run_limit': membership.organization.agent_run_limit,
                            'can_create_runs': membership.organization.can_create_agent_run(),
                        }
                        organizations.append(org_data)
                
                return sorted(organizations, key=lambda x: x['name'])
                
        except Exception as e:
            logger.error(f"Failed to get user organizations: {e}")
            return []
    
    def get_organization_details(self, org_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed organization information."""
        try:
            org = self.middleware.get_by_id(Organization, org_id, relationships=['settings', 'members'])
            if not org:
                return None
            
            return {
                'id': str(org.id),
                'name': org.name,
                'display_name': org.display_name,
                'description': org.description,
                'slug': org.slug,
                'avatar_url': org.avatar_url,
                'website_url': org.website_url,
                'plan_type': org.plan_type,
                'agent_runs_used': org.agent_runs_used,
                'agent_run_limit': org.agent_run_limit,
                'features_enabled': org.features_enabled,
                'status': org.status,
                'created_at': org.created_at.isoformat() if org.created_at else None,
                'member_count': len([m for m in org.members if m.is_active]),
                'settings': org.settings.to_dict() if org.settings else {},
            }
            
        except Exception as e:
            logger.error(f"Failed to get organization details: {e}")
            return None
    
    # Agent Run Data
    
    def get_agent_runs(
        self, 
        org_id: str, 
        limit: int = 50, 
        offset: int = 0,
        status_filter: Optional[str] = None,
        user_filter: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get agent runs for organization (replaces API calls in TUI)."""
        try:
            filters = {'organization_id': org_id}
            
            if status_filter:
                filters['execution_status'] = status_filter
            
            if user_filter:
                filters['created_by_user_id'] = user_filter
            
            # Get runs with relationships
            runs = self.middleware.list_with_filters(
                AgentRun,
                filters=filters,
                order_by='created_at',
                order_desc=True,
                limit=limit,
                offset=offset,
                relationships=['created_by_user', 'repository']
            )
            
            # Get total count
            total_count = self.middleware.count_with_filters(AgentRun, filters)
            
            # Format for UI
            formatted_runs = []
            for run in runs:
                run_data = {
                    'id': str(run.id),
                    'external_id': run.external_id,
                    'run_number': run.run_number,
                    'prompt': run.prompt[:200] + '...' if len(run.prompt) > 200 else run.prompt,
                    'full_prompt': run.prompt,
                    'execution_status': run.execution_status,
                    'source_type': run.source_type,
                    'agent_type': run.agent_type,
                    'created_at': run.created_at.isoformat() if run.created_at else None,
                    'started_at': run.started_at,
                    'completed_at': run.completed_at,
                    'duration_seconds': run.duration_seconds,
                    'error_message': run.error_message,
                    'result_summary': run.result_summary,
                    'tokens_used': run.tokens_used,
                    'api_calls_made': run.api_calls_made,
                    'is_running': run.is_running(),
                    'is_completed': run.is_completed(),
                    'is_successful': run.is_successful(),
                    'can_retry': run.can_retry(),
                    'created_by': {
                        'id': str(run.created_by_user.id),
                        'email': run.created_by_user.email,
                        'display_name': run.created_by_user.display_name or run.created_by_user.email,
                    } if run.created_by_user else None,
                    'repository': {
                        'id': str(run.repository.id),
                        'name': run.repository.name,
                        'full_name': run.repository.full_name,
                    } if run.repository else None,
                }
                formatted_runs.append(run_data)
            
            return formatted_runs, total_count
            
        except Exception as e:
            logger.error(f"Failed to get agent runs: {e}")
            return [], 0
    
    def get_agent_run_details(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed agent run information with logs."""
        try:
            run = self.middleware.get_by_id(
                AgentRun, 
                run_id, 
                relationships=['created_by_user', 'repository', 'logs', 'tasks']
            )
            if not run:
                return None
            
            # Format logs
            logs = []
            for log in run.logs:
                log_data = {
                    'id': str(log.id),
                    'message': log.message,
                    'level': log.level,
                    'tool_name': log.tool_name,
                    'message_type': log.message_type,
                    'thought': log.thought,
                    'timestamp': log.timestamp,
                    'created_at': log.created_at.isoformat() if log.created_at else None,
                }
                logs.append(log_data)
            
            # Format tasks
            tasks = []
            for task in run.tasks:
                task_data = {
                    'id': str(task.id),
                    'task_name': task.task_name,
                    'task_type': task.task_type,
                    'execution_status': task.execution_status,
                    'progress_percentage': task.progress_percentage,
                    'started_at': task.started_at,
                    'completed_at': task.completed_at,
                    'duration_seconds': task.duration_seconds,
                    'error_message': task.error_message,
                }
                tasks.append(task_data)
            
            return {
                'id': str(run.id),
                'external_id': run.external_id,
                'run_number': run.run_number,
                'prompt': run.prompt,
                'images': run.images,
                'execution_status': run.execution_status,
                'source_type': run.source_type,
                'source_metadata': run.source_metadata,
                'agent_type': run.agent_type,
                'agent_version': run.agent_version,
                'created_at': run.created_at.isoformat() if run.created_at else None,
                'started_at': run.started_at,
                'completed_at': run.completed_at,
                'duration_seconds': run.duration_seconds,
                'error_message': run.error_message,
                'error_code': run.error_code,
                'result_summary': run.result_summary,
                'output_files': run.output_files,
                'artifacts': run.artifacts,
                'tokens_used': run.tokens_used,
                'api_calls_made': run.api_calls_made,
                'memory_peak_mb': run.memory_peak_mb,
                'cpu_time_seconds': run.cpu_time_seconds,
                'is_test_run': run.is_test_run,
                'is_debug_mode': run.is_debug_mode,
                'is_priority': run.is_priority,
                'retry_count': run.retry_count,
                'max_retries': run.max_retries,
                'logs': logs,
                'tasks': tasks,
                'created_by': {
                    'id': str(run.created_by_user.id),
                    'email': run.created_by_user.email,
                    'display_name': run.created_by_user.display_name or run.created_by_user.email,
                } if run.created_by_user else None,
                'repository': {
                    'id': str(run.repository.id),
                    'name': run.repository.name,
                    'full_name': run.repository.full_name,
                } if run.repository else None,
            }
            
        except Exception as e:
            logger.error(f"Failed to get agent run details: {e}")
            return None
    
    def get_running_agent_runs(self, org_id: str) -> List[Dict[str, Any]]:
        """Get currently running agent runs."""
        try:
            filters = {
                'organization_id': org_id,
                'execution_status': ['pending', 'running']
            }
            
            runs = self.middleware.list_with_filters(
                AgentRun,
                filters=filters,
                order_by='created_at',
                order_desc=True,
                relationships=['created_by_user']
            )
            
            formatted_runs = []
            for run in runs:
                run_data = {
                    'id': str(run.id),
                    'run_number': run.run_number,
                    'prompt': run.prompt[:100] + '...' if len(run.prompt) > 100 else run.prompt,
                    'execution_status': run.execution_status,
                    'started_at': run.started_at,
                    'duration_seconds': run.duration_seconds,
                    'created_by': run.created_by_user.display_name if run.created_by_user else 'Unknown',
                }
                formatted_runs.append(run_data)
            
            return formatted_runs
            
        except Exception as e:
            logger.error(f"Failed to get running agent runs: {e}")
            return []
    
    # Repository Data
    
    def get_organization_repositories(self, org_id: str) -> List[Dict[str, Any]]:
        """Get repositories for organization."""
        try:
            repos = self.middleware.list_with_filters(
                Repository,
                filters={'organization_id': org_id},
                order_by='name'
            )
            
            formatted_repos = []
            for repo in repos:
                repo_data = {
                    'id': str(repo.id),
                    'name': repo.name,
                    'full_name': repo.full_name,
                    'description': repo.description,
                    'is_private': repo.is_private,
                    'default_branch': repo.default_branch,
                    'language': repo.primary_language,
                    'stars_count': repo.stars_count,
                    'forks_count': repo.forks_count,
                    'last_activity_at': repo.last_activity_at,
                    'is_active': repo.is_active,
                }
                formatted_repos.append(repo_data)
            
            return formatted_repos
            
        except Exception as e:
            logger.error(f"Failed to get organization repositories: {e}")
            return []
    
    # User Data
    
    def get_current_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current user information."""
        try:
            user = self.middleware.get_by_id(User, user_id)
            if not user:
                return None
            
            return {
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'full_name': user.full_name,
                'display_name': user.display_name or user.full_name or user.email,
                'avatar_url': user.avatar_url,
                'github_username': user.github_username,
                'timezone': user.timezone,
                'language': user.language,
                'theme': user.theme,
                'is_active': user.is_active,
                'last_login_at': user.last_login_at,
                'login_count': user.login_count,
                'onboarding_completed': user.onboarding_completed,
            }
            
        except Exception as e:
            logger.error(f"Failed to get current user: {e}")
            return None
    
    # Statistics and Metrics
    
    def get_organization_stats(self, org_id: str) -> Dict[str, Any]:
        """Get organization statistics for dashboard."""
        try:
            with db_session_scope() as session:
                # Get basic counts
                total_runs = session.query(AgentRun).filter(
                    AgentRun.organization_id == org_id
                ).count()
                
                running_runs = session.query(AgentRun).filter(
                    AgentRun.organization_id == org_id,
                    AgentRun.execution_status.in_(['pending', 'running'])
                ).count()
                
                completed_runs = session.query(AgentRun).filter(
                    AgentRun.organization_id == org_id,
                    AgentRun.execution_status == 'completed'
                ).count()
                
                failed_runs = session.query(AgentRun).filter(
                    AgentRun.organization_id == org_id,
                    AgentRun.execution_status == 'failed'
                ).count()
                
                # Get recent activity (last 24 hours)
                yesterday = datetime.utcnow() - timedelta(days=1)
                recent_runs = session.query(AgentRun).filter(
                    AgentRun.organization_id == org_id,
                    AgentRun.created_at >= yesterday
                ).count()
                
                return {
                    'total_runs': total_runs,
                    'running_runs': running_runs,
                    'completed_runs': completed_runs,
                    'failed_runs': failed_runs,
                    'success_rate': (completed_runs / total_runs * 100) if total_runs > 0 else 0,
                    'recent_activity': recent_runs,
                }
                
        except Exception as e:
            logger.error(f"Failed to get organization stats: {e}")
            return {
                'total_runs': 0,
                'running_runs': 0,
                'completed_runs': 0,
                'failed_runs': 0,
                'success_rate': 0,
                'recent_activity': 0,
            }
    
    # Real-time Updates
    
    def subscribe_to_updates(self, user_id: str, org_id: str, callback: callable) -> None:
        """Subscribe to real-time updates for UI."""
        from .events import get_event_emitter
        
        event_emitter = get_event_emitter()
        
        def handle_event(event):
            # Filter events for this organization
            if event.organization_id == org_id:
                callback(event.to_dict())
        
        # Subscribe to relevant events
        event_emitter.on('agentrun.created', handle_event)
        event_emitter.on('agentrun.updated', handle_event)
        event_emitter.on('agentrun.deleted', handle_event)
        event_emitter.on('organization.updated', handle_event)


# Global service instance
_ui_data_service: Optional[UIDataService] = None


def get_ui_data_service() -> UIDataService:
    """Get the global UI data service instance."""
    global _ui_data_service
    if _ui_data_service is None:
        _ui_data_service = UIDataService()
    return _ui_data_service
