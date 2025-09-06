"""
Example of migrating TUI from static data to database-backed data.

This demonstrates how to replace all static data sources in the TUI with 
database queries using the UIDataService.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .ui_data_service import get_ui_data_service
from .events import get_websocket_manager

logger = logging.getLogger(__name__)


class DatabaseBackedTUI:
    """
    Example TUI class showing migration from static data to database.
    
    BEFORE: TUI made direct API calls and stored data in memory
    AFTER: TUI uses UIDataService to get data from database with real-time updates
    """
    
    def __init__(self, user_id: str, organization_id: str):
        self.user_id = user_id
        self.organization_id = organization_id
        self.ui_data_service = get_ui_data_service()
        self.websocket_manager = get_websocket_manager()
        
        # UI state (now backed by database)
        self.current_user = None
        self.organizations = []
        self.current_organization = None
        self.agent_runs = []
        self.repositories = []
        self.stats = {}
        
        # Real-time update callbacks
        self.update_callbacks = []
    
    async def initialize(self) -> None:
        """Initialize TUI with database data."""
        logger.info("Initializing TUI with database-backed data")
        
        # Load initial data from database
        await self.load_user_data()
        await self.load_organization_data()
        await self.load_agent_runs()
        await self.load_repositories()
        await self.load_statistics()
        
        # Subscribe to real-time updates
        self.subscribe_to_updates()
        
        logger.info("TUI initialization complete")
    
    # BEFORE: Direct API calls
    # def get_organizations(self):
    #     response = requests.get(f"{API_ENDPOINT}/v1/organizations", headers=headers)
    #     return response.json()
    
    # AFTER: Database-backed with real-time updates
    async def load_user_data(self) -> None:
        """Load current user data from database."""
        self.current_user = self.ui_data_service.get_current_user(self.user_id)
        if self.current_user:
            logger.info(f"Loaded user: {self.current_user['display_name']}")
    
    async def load_organization_data(self) -> None:
        """Load organization data from database."""
        # Get user's organizations
        self.organizations = self.ui_data_service.get_user_organizations(self.user_id)
        
        # Get current organization details
        if self.organization_id:
            self.current_organization = self.ui_data_service.get_organization_details(
                self.organization_id
            )
        
        logger.info(f"Loaded {len(self.organizations)} organizations")
    
    # BEFORE: API call with pagination handling
    # def get_agent_runs(self, page=1, limit=50):
    #     response = requests.get(
    #         f"{API_ENDPOINT}/v1/organizations/{org_id}/agent/runs",
    #         params={"skip": (page-1)*limit, "limit": limit},
    #         headers=headers
    #     )
    #     return response.json()
    
    # AFTER: Database query with filtering and real-time updates
    async def load_agent_runs(
        self, 
        limit: int = 50, 
        offset: int = 0,
        status_filter: Optional[str] = None
    ) -> None:
        """Load agent runs from database."""
        if not self.organization_id:
            return
        
        runs, total_count = self.ui_data_service.get_agent_runs(
            org_id=self.organization_id,
            limit=limit,
            offset=offset,
            status_filter=status_filter
        )
        
        self.agent_runs = runs
        logger.info(f"Loaded {len(runs)} agent runs (total: {total_count})")
    
    async def load_repositories(self) -> None:
        """Load repositories from database."""
        if not self.organization_id:
            return
        
        self.repositories = self.ui_data_service.get_organization_repositories(
            self.organization_id
        )
        logger.info(f"Loaded {len(self.repositories)} repositories")
    
    async def load_statistics(self) -> None:
        """Load organization statistics from database."""
        if not self.organization_id:
            return
        
        self.stats = self.ui_data_service.get_organization_stats(self.organization_id)
        logger.info(f"Loaded stats: {self.stats['total_runs']} total runs")
    
    # BEFORE: Manual refresh by re-calling APIs
    # def refresh_data(self):
    #     self.agent_runs = self.get_agent_runs()
    #     self.render_agent_runs()
    
    # AFTER: Real-time updates via WebSocket events
    def subscribe_to_updates(self) -> None:
        """Subscribe to real-time database updates."""
        def handle_update(event_data):
            event_type = event_data.get('event_type', '')
            
            if event_type.startswith('agentrun.'):
                # Agent run updated - refresh the list
                asyncio.create_task(self.load_agent_runs())
                self.notify_ui_update('agent_runs')
            
            elif event_type.startswith('organization.'):
                # Organization updated - refresh org data
                asyncio.create_task(self.load_organization_data())
                asyncio.create_task(self.load_statistics())
                self.notify_ui_update('organization')
            
            elif event_type.startswith('repository.'):
                # Repository updated - refresh repo list
                asyncio.create_task(self.load_repositories())
                self.notify_ui_update('repositories')
        
        # Subscribe to updates for this organization
        self.ui_data_service.subscribe_to_updates(
            user_id=self.user_id,
            org_id=self.organization_id,
            callback=handle_update
        )
    
    def notify_ui_update(self, component: str) -> None:
        """Notify UI components of data updates."""
        for callback in self.update_callbacks:
            try:
                callback(component)
            except Exception as e:
                logger.error(f"Error in UI update callback: {e}")
    
    def add_update_callback(self, callback: callable) -> None:
        """Add callback for UI updates."""
        self.update_callbacks.append(callback)
    
    # BEFORE: Static data display
    # def render_dashboard(self):
    #     print(f"Organization: {self.current_org_name}")
    #     print(f"Agent Runs: {len(self.agent_runs)}")
    #     for run in self.agent_runs[:10]:
    #         print(f"  - {run['id']}: {run['status']}")
    
    # AFTER: Dynamic data display with real-time updates
    def render_dashboard(self) -> str:
        """Render dashboard with database-backed data."""
        if not self.current_organization:
            return "No organization selected"
        
        org = self.current_organization
        stats = self.stats
        
        dashboard = f"""
╭─ Codegen Dashboard ─────────────────────────────────────────╮
│ Organization: {org['display_name'] or org['name']}
│ Plan: {org['plan_type'].title()} | Members: {org['member_count']}
│ 
│ Agent Runs: {stats['total_runs']} total
│   ├─ Running: {stats['running_runs']}
│   ├─ Completed: {stats['completed_runs']} 
│   ├─ Failed: {stats['failed_runs']}
│   └─ Success Rate: {stats['success_rate']:.1f}%
│
│ Recent Activity: {stats['recent_activity']} runs (24h)
│ Repositories: {len(self.repositories)}
╰─────────────────────────────────────────────────────────────╯

Recent Agent Runs:
"""
        
        for i, run in enumerate(self.agent_runs[:5]):
            status_icon = {
                'completed': '✅',
                'running': '🔄',
                'pending': '⏳',
                'failed': '❌',
                'cancelled': '⏹️'
            }.get(run['execution_status'], '❓')
            
            created_by = run['created_by']['display_name'] if run['created_by'] else 'Unknown'
            
            dashboard += f"  {i+1}. {status_icon} {run['prompt'][:50]}...\n"
            dashboard += f"     By: {created_by} | {run['execution_status'].title()}\n"
        
        return dashboard
    
    def render_agent_run_details(self, run_id: str) -> str:
        """Render detailed agent run information."""
        run_details = self.ui_data_service.get_agent_run_details(run_id)
        if not run_details:
            return f"Agent run {run_id} not found"
        
        details = f"""
╭─ Agent Run Details ─────────────────────────────────────────╮
│ ID: {run_details['id']}
│ Status: {run_details['execution_status'].title()}
│ Created: {run_details['created_at']}
│ Duration: {run_details['duration_seconds']}s
│ 
│ Prompt: {run_details['prompt'][:100]}...
│ 
│ Resources:
│   ├─ Tokens: {run_details['tokens_used']}
│   ├─ API Calls: {run_details['api_calls_made']}
│   └─ Memory: {run_details['memory_peak_mb']}MB
╰─────────────────────────────────────────────────────────────╯

Logs ({len(run_details['logs'])} entries):
"""
        
        for log in run_details['logs'][-10:]:  # Show last 10 logs
            level_icon = {
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '❌',
                'debug': '🐛'
            }.get(log['level'], '📝')
            
            details += f"  {level_icon} [{log['level'].upper()}] {log['message'][:80]}...\n"
        
        return details
    
    # BEFORE: Manual data filtering
    # def filter_runs_by_status(self, status):
    #     return [run for run in self.agent_runs if run['status'] == status]
    
    # AFTER: Database-level filtering with efficient queries
    async def filter_runs_by_status(self, status: str) -> None:
        """Filter agent runs by status using database query."""
        await self.load_agent_runs(status_filter=status)
        self.notify_ui_update('agent_runs')
    
    async def search_runs_by_prompt(self, search_term: str) -> List[Dict[str, Any]]:
        """Search agent runs by prompt text."""
        # This would use database full-text search in a real implementation
        matching_runs = []
        for run in self.agent_runs:
            if search_term.lower() in run['full_prompt'].lower():
                matching_runs.append(run)
        return matching_runs
    
    # Real-time status updates
    def get_live_running_runs(self) -> List[Dict[str, Any]]:
        """Get currently running agent runs with live updates."""
        return self.ui_data_service.get_running_agent_runs(self.organization_id)


# Example usage showing the migration
async def example_tui_migration():
    """Example showing how to migrate TUI to database-backed data."""
    
    # Initialize database-backed TUI
    tui = DatabaseBackedTUI(
        user_id="user-123",
        organization_id="org-456"
    )
    
    # Initialize with database data
    await tui.initialize()
    
    # Add UI update callback
    def on_ui_update(component: str):
        print(f"🔄 UI component '{component}' updated with fresh data from database")
    
    tui.add_update_callback(on_ui_update)
    
    # Display dashboard (now with database data)
    print(tui.render_dashboard())
    
    # Filter runs by status (database query)
    await tui.filter_runs_by_status('running')
    
    # Get live running runs
    running_runs = tui.get_live_running_runs()
    print(f"\n🔄 Currently running: {len(running_runs)} agent runs")
    
    # Show detailed run information
    if tui.agent_runs:
        first_run_id = tui.agent_runs[0]['id']
        print(tui.render_agent_run_details(first_run_id))


if __name__ == "__main__":
    # Run the example
    asyncio.run(example_tui_migration())
