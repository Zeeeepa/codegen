"""
Project Management Integration for Visual Orchestration System

This module provides comprehensive project management capabilities through API integrations
with various platforms like Linear, GitHub, Jira, and ClickUp via MCP servers.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
from pydantic import BaseModel, Field

from .schemas import PipelineDefinition, ExecutionStatus, AgentTask
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class ProjectPlatform(str, Enum):
    """Supported project management platforms."""
    LINEAR = "linear"
    GITHUB = "github"
    JIRA = "jira"
    CLICKUP = "clickup"
    CUSTOM_API = "custom_api"


class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    """Task status types."""
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    CANCELLED = "cancelled"


@dataclass
class ProjectTask:
    """Represents a project management task."""
    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assignee: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    labels: List[str] = field(default_factory=list)
    platform: ProjectPlatform = ProjectPlatform.CUSTOM_API
    platform_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PipelineIntegrationConfig(BaseModel):
    """Configuration for pipeline integration with project management."""
    platform: ProjectPlatform
    project_id: str
    api_base_url: Optional[str] = None
    auth_token: Optional[str] = None
    webhook_url: Optional[str] = None
    auto_create_tasks: bool = True
    auto_update_status: bool = True
    task_prefix: str = "[Pipeline]"
    assignee_mapping: Dict[str, str] = Field(default_factory=dict)


class MCPServerIntegration:
    """Integration layer for MCP (Model Context Protocol) servers."""
    
    def __init__(self, server_configs: Dict[str, Dict[str, str]]):
        """
        Initialize MCP server integration.
        
        Args:
            server_configs: Map of server names to configuration dicts
                Example: {
                    "linear": {"url": "ws://localhost:8001", "token": "..."},
                    "github": {"url": "ws://localhost:8002", "token": "..."}
                }
        """
        self.server_configs = server_configs
        self.active_connections: Dict[str, Any] = {}
        
    async def connect_to_server(self, server_name: str) -> bool:
        """Connect to an MCP server."""
        if server_name not in self.server_configs:
            logger.error(f"Unknown MCP server: {server_name}")
            return False
            
        try:
            config = self.server_configs[server_name]
            # In a real implementation, this would establish WebSocket connection
            # to the MCP server and handle protocol negotiation
            self.active_connections[server_name] = {
                "connected": True,
                "config": config,
                "last_ping": datetime.now()
            }
            logger.info(f"Connected to MCP server: {server_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server_name}: {e}")
            return False
    
    async def call_tool(
        self, 
        server_name: str, 
        tool_name: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool on an MCP server."""
        if server_name not in self.active_connections:
            await self.connect_to_server(server_name)
            
        if server_name not in self.active_connections:
            raise ConnectionError(f"Cannot connect to MCP server: {server_name}")
        
        # Mock implementation - in reality this would send JSON-RPC requests
        # over WebSocket to the MCP server
        try:
            logger.debug(f"Calling {tool_name} on {server_name} with {parameters}")
            
            # Simulate different tool responses based on server and tool
            if server_name == "linear" and tool_name == "create_issue":
                return {
                    "success": True,
                    "issue_id": f"LIN-{datetime.now().strftime('%m%d')}-001",
                    "url": f"https://linear.app/team/issue/LIN-{datetime.now().strftime('%m%d')}-001"
                }
            elif server_name == "github" and tool_name == "create_issue":
                return {
                    "success": True,
                    "issue_number": 42,
                    "html_url": "https://github.com/org/repo/issues/42"
                }
            elif tool_name == "update_issue":
                return {"success": True, "updated_at": datetime.now().isoformat()}
            else:
                return {"success": True, "data": "Mock response"}
                
        except Exception as e:
            logger.error(f"MCP tool call failed: {e}")
            return {"success": False, "error": str(e)}


class ProjectManagementIntegration:
    """Main project management integration orchestrator."""
    
    def __init__(self, mcp_integration: Optional[MCPServerIntegration] = None):
        self.mcp = mcp_integration
        self.integrations: Dict[str, PipelineIntegrationConfig] = {}
        self.task_cache: Dict[str, List[ProjectTask]] = {}
        
    def add_integration(self, name: str, config: PipelineIntegrationConfig):
        """Add a project management integration."""
        self.integrations[name] = config
        logger.info(f"Added integration: {name} ({config.platform})")
        
    async def create_pipeline_tasks(
        self, 
        pipeline: PipelineDefinition, 
        integration_name: str
    ) -> List[ProjectTask]:
        """Create project management tasks for a pipeline."""
        if integration_name not in self.integrations:
            raise ValueError(f"Unknown integration: {integration_name}")
            
        config = self.integrations[integration_name]
        tasks = []
        
        logger.info(f"Creating tasks for pipeline: {pipeline.name}")
        
        # Create overview task
        overview_task = await self._create_task(
            title=f"{config.task_prefix} {pipeline.name} - Pipeline Execution",
            description=f"Track execution of CI/CD pipeline: {pipeline.name}\n\n"
                       f"Stages: {len(pipeline.stages)}\n"
                       f"Total Tasks: {sum(len(stage.tasks) for stage in pipeline.stages)}",
            integration_name=integration_name,
            priority=TaskPriority.HIGH
        )
        if overview_task:
            tasks.append(overview_task)
        
        # Create tasks for each stage if configured
        if config.auto_create_tasks:
            for stage in pipeline.stages:
                stage_task = await self._create_task(
                    title=f"{config.task_prefix} {pipeline.name} - {stage.name}",
                    description=f"Execute stage: {stage.name}\n\n"
                               f"Tasks in stage: {len(stage.tasks)}\n"
                               f"Dependencies: {', '.join(stage.depends_on) if stage.depends_on else 'None'}",
                    integration_name=integration_name,
                    priority=TaskPriority.MEDIUM,
                    labels=[f"stage:{stage.name}", "pipeline", "automation"]
                )
                if stage_task:
                    tasks.append(stage_task)
        
        # Cache the tasks
        cache_key = f"{integration_name}:{pipeline.name}"
        self.task_cache[cache_key] = tasks
        
        return tasks
    
    async def update_pipeline_progress(
        self, 
        pipeline: PipelineDefinition,
        execution_status: ExecutionStatus,
        integration_name: str,
        stage_name: Optional[str] = None,
        completion_percentage: Optional[float] = None
    ):
        """Update project management tasks based on pipeline progress."""
        if integration_name not in self.integrations:
            logger.warning(f"Unknown integration for update: {integration_name}")
            return
            
        config = self.integrations[integration_name]
        cache_key = f"{integration_name}:{pipeline.name}"
        
        if cache_key not in self.task_cache:
            logger.warning(f"No cached tasks for pipeline: {pipeline.name}")
            return
        
        logger.info(f"Updating progress for {pipeline.name}: {execution_status}")
        
        # Update overview task
        overview_tasks = [t for t in self.task_cache[cache_key] if "Pipeline Execution" in t.title]
        if overview_tasks:
            overview_task = overview_tasks[0]
            new_status = self._map_execution_status_to_task_status(execution_status)
            
            description_update = f"\n\n**Status Update ({datetime.now().strftime('%Y-%m-%d %H:%M')}):**\n"
            description_update += f"- Execution Status: {execution_status.value}\n"
            if completion_percentage:
                description_update += f"- Progress: {completion_percentage:.1f}%\n"
            if stage_name:
                description_update += f"- Current Stage: {stage_name}\n"
            
            await self._update_task(
                task_id=overview_task.id,
                status=new_status,
                description=overview_task.description + description_update,
                integration_name=integration_name
            )
        
        # Update stage-specific task if provided
        if stage_name and config.auto_update_status:
            stage_tasks = [t for t in self.task_cache[cache_key] if stage_name in t.title]
            if stage_tasks:
                stage_task = stage_tasks[0]
                stage_status = TaskStatus.IN_PROGRESS if execution_status == ExecutionStatus.RUNNING else \
                              TaskStatus.DONE if execution_status == ExecutionStatus.COMPLETED else \
                              TaskStatus.TODO
                
                await self._update_task(
                    task_id=stage_task.id,
                    status=stage_status,
                    integration_name=integration_name
                )
    
    async def create_issue_from_failure(
        self, 
        pipeline: PipelineDefinition,
        failed_task: AgentTask,
        error_details: str,
        integration_name: str
    ) -> Optional[ProjectTask]:
        """Create a high-priority issue when a pipeline task fails."""
        if integration_name not in self.integrations:
            return None
            
        config = self.integrations[integration_name]
        
        title = f"🚨 {config.task_prefix} Pipeline Failure: {pipeline.name}"
        description = f"""
**Pipeline Failure Report**

**Pipeline:** {pipeline.name}
**Failed Task:** {failed_task.name}
**Timestamp:** {datetime.now().isoformat()}

**Error Details:**
```
{error_details}
```

**Task Configuration:**
- Agent: {failed_task.agent_type}
- Timeout: {failed_task.timeout}s
- Retry Count: {failed_task.retry_count}

**Recommended Actions:**
1. Review the error logs above
2. Check agent configuration and dependencies
3. Verify input parameters and environment
4. Consider increasing timeout or retry count
5. Test the failing task in isolation

**Pipeline Context:**
Total Stages: {len(pipeline.stages)}
Parallel Execution: {'Yes' if pipeline.parallel_execution else 'No'}
"""
        
        return await self._create_task(
            title=title,
            description=description,
            integration_name=integration_name,
            priority=TaskPriority.URGENT,
            labels=["bug", "pipeline", "failure", "urgent"]
        )
    
    async def sync_tasks_with_platform(self, integration_name: str) -> Dict[str, Any]:
        """Sync local task cache with the external platform."""
        if integration_name not in self.integrations:
            return {"error": "Unknown integration"}
            
        config = self.integrations[integration_name]
        
        try:
            # Use MCP server if available
            if self.mcp and config.platform != ProjectPlatform.CUSTOM_API:
                server_name = config.platform.value
                result = await self.mcp.call_tool(
                    server_name=server_name,
                    tool_name="list_tasks",
                    parameters={"project_id": config.project_id}
                )
                
                if result.get("success"):
                    # Update cache with fresh data
                    logger.info(f"Synced tasks from {config.platform}")
                    return {"synced": True, "count": len(result.get("tasks", []))}
            
            # Fallback to direct API integration
            return await self._direct_api_sync(config)
            
        except Exception as e:
            logger.error(f"Task sync failed for {integration_name}: {e}")
            return {"error": str(e)}
    
    async def get_platform_analytics(self, integration_name: str) -> Dict[str, Any]:
        """Get analytics and insights from the project management platform."""
        if integration_name not in self.integrations:
            return {"error": "Unknown integration"}
            
        config = self.integrations[integration_name]
        
        # Mock analytics data - in reality this would come from platform APIs
        return {
            "platform": config.platform.value,
            "total_tasks": 156,
            "completed_tasks": 89,
            "in_progress_tasks": 23,
            "overdue_tasks": 7,
            "completion_rate": 57.1,
            "average_completion_time": "2.3 days",
            "top_assignees": [
                {"name": "alice", "tasks": 34},
                {"name": "bob", "tasks": 28},
                {"name": "charlie", "tasks": 19}
            ],
            "pipeline_success_rate": 94.2,
            "last_updated": datetime.now().isoformat()
        }
    
    async def _create_task(
        self,
        title: str,
        description: str, 
        integration_name: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        labels: Optional[List[str]] = None
    ) -> Optional[ProjectTask]:
        """Create a task using the configured integration."""
        config = self.integrations[integration_name]
        labels = labels or []
        
        try:
            if self.mcp and config.platform != ProjectPlatform.CUSTOM_API:
                # Use MCP server
                result = await self.mcp.call_tool(
                    server_name=config.platform.value,
                    tool_name="create_issue",
                    parameters={
                        "title": title,
                        "description": description,
                        "priority": priority.value,
                        "labels": labels,
                        "project_id": config.project_id
                    }
                )
                
                if result.get("success"):
                    task_id = result.get("issue_id") or result.get("issue_number", "unknown")
                    return ProjectTask(
                        id=str(task_id),
                        title=title,
                        description=description,
                        status=TaskStatus.TODO,
                        priority=priority,
                        created_at=datetime.now(),
                        labels=labels,
                        platform=config.platform,
                        platform_url=result.get("url") or result.get("html_url")
                    )
            else:
                # Direct API integration fallback
                return await self._direct_api_create(title, description, config, priority, labels)
                
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            return None
    
    async def _update_task(
        self, 
        task_id: str, 
        integration_name: str,
        status: Optional[TaskStatus] = None,
        description: Optional[str] = None,
        assignee: Optional[str] = None
    ):
        """Update a task using the configured integration."""
        config = self.integrations[integration_name]
        
        try:
            if self.mcp and config.platform != ProjectPlatform.CUSTOM_API:
                parameters = {"task_id": task_id}
                if status:
                    parameters["status"] = status.value
                if description:
                    parameters["description"] = description
                if assignee:
                    parameters["assignee"] = assignee
                
                result = await self.mcp.call_tool(
                    server_name=config.platform.value,
                    tool_name="update_issue",
                    parameters=parameters
                )
                
                if result.get("success"):
                    logger.info(f"Updated task {task_id}")
                else:
                    logger.warning(f"Failed to update task {task_id}: {result}")
            else:
                # Direct API integration fallback
                await self._direct_api_update(task_id, config, status, description, assignee)
                
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
    
    async def _direct_api_create(
        self, 
        title: str, 
        description: str, 
        config: PipelineIntegrationConfig, 
        priority: TaskPriority,
        labels: List[str]
    ) -> Optional[ProjectTask]:
        """Direct API integration for task creation."""
        # Mock implementation - would use aiohttp for real API calls
        task_id = f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        logger.info(f"Created task via direct API: {task_id}")
        
        return ProjectTask(
            id=task_id,
            title=title,
            description=description,
            status=TaskStatus.TODO,
            priority=priority,
            created_at=datetime.now(),
            labels=labels,
            platform=config.platform,
            platform_url=f"{config.api_base_url}/task/{task_id}" if config.api_base_url else None
        )
    
    async def _direct_api_update(
        self, 
        task_id: str, 
        config: PipelineIntegrationConfig,
        status: Optional[TaskStatus] = None,
        description: Optional[str] = None,
        assignee: Optional[str] = None
    ):
        """Direct API integration for task updates."""
        # Mock implementation
        logger.info(f"Updated task via direct API: {task_id}")
    
    async def _direct_api_sync(self, config: PipelineIntegrationConfig) -> Dict[str, Any]:
        """Direct API integration for task synchronization."""
        # Mock implementation
        return {"synced": True, "count": 0}
    
    def _map_execution_status_to_task_status(self, execution_status: ExecutionStatus) -> TaskStatus:
        """Map pipeline execution status to project task status."""
        mapping = {
            ExecutionStatus.PENDING: TaskStatus.TODO,
            ExecutionStatus.RUNNING: TaskStatus.IN_PROGRESS,
            ExecutionStatus.COMPLETED: TaskStatus.DONE,
            ExecutionStatus.FAILED: TaskStatus.TODO,  # Reset to TODO for retry
            ExecutionStatus.CANCELLED: TaskStatus.CANCELLED
        }
        return mapping.get(execution_status, TaskStatus.TODO)


# Example usage and configuration factory
class ProjectManagementFactory:
    """Factory for creating project management integrations."""
    
    @staticmethod
    def create_linear_integration(
        project_id: str,
        api_token: str,
        team_id: str,
        webhook_url: Optional[str] = None
    ) -> PipelineIntegrationConfig:
        """Create Linear integration configuration."""
        return PipelineIntegrationConfig(
            platform=ProjectPlatform.LINEAR,
            project_id=project_id,
            auth_token=api_token,
            webhook_url=webhook_url,
            task_prefix="[CI/CD]",
            auto_create_tasks=True,
            auto_update_status=True,
            assignee_mapping={
                "build": team_id,
                "test": team_id,
                "deploy": team_id
            }
        )
    
    @staticmethod 
    def create_github_integration(
        repo_owner: str,
        repo_name: str,
        github_token: str,
        webhook_url: Optional[str] = None
    ) -> PipelineIntegrationConfig:
        """Create GitHub integration configuration."""
        return PipelineIntegrationConfig(
            platform=ProjectPlatform.GITHUB,
            project_id=f"{repo_owner}/{repo_name}",
            api_base_url="https://api.github.com",
            auth_token=github_token,
            webhook_url=webhook_url,
            task_prefix="[Pipeline]",
            auto_create_tasks=True,
            auto_update_status=True
        )
    
    @staticmethod
    def create_mcp_server_integration(servers: Dict[str, Dict[str, str]]) -> MCPServerIntegration:
        """Create MCP server integration with multiple servers."""
        return MCPServerIntegration(servers)


# CLI integration helper
async def setup_project_management_from_config(config_path: Path) -> ProjectManagementIntegration:
    """Set up project management integration from configuration file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path) as f:
        if config_path.suffix.lower() in ['.yaml', '.yml']:
            import yaml
            config_data = yaml.safe_load(f)
        else:
            config_data = json.load(f)
    
    # Initialize MCP integration if configured
    mcp_integration = None
    if "mcp_servers" in config_data:
        mcp_integration = MCPServerIntegration(config_data["mcp_servers"])
        
        # Connect to all configured servers
        for server_name in config_data["mcp_servers"]:
            await mcp_integration.connect_to_server(server_name)
    
    # Create main integration
    pm_integration = ProjectManagementIntegration(mcp_integration)
    
    # Add configured integrations
    for name, integration_config in config_data.get("integrations", {}).items():
        config = PipelineIntegrationConfig(**integration_config)
        pm_integration.add_integration(name, config)
    
    logger.info(f"Project management integration initialized with {len(pm_integration.integrations)} platforms")
    return pm_integration