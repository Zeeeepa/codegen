"""Dashboard API endpoints configuration and rate limiting."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional
import os

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.api.modal import get_modal_prefix


class RateLimit(Enum):
    """Rate limit categories for API endpoints."""
    STANDARD = "60_per_30s"  # 60 requests per 30 seconds
    AGENT_CREATION = "10_per_min"  # 10 requests per minute
    SETUP_COMMANDS = "5_per_min"  # 5 requests per minute
    LOG_ANALYSIS = "5_per_min"  # 5 requests per minute


@dataclass
class EndpointConfig:
    """Configuration for a single API endpoint."""
    path: str
    method: str
    rate_limit: RateLimit
    description: str
    cli_command: Optional[str] = None
    requires_org_id: bool = True
    cache_ttl_seconds: Optional[int] = None


class DashboardAPIEndpoints:
    """Centralized configuration for all dashboard API endpoints."""
    
    def __init__(self):
        self.base_url = API_ENDPOINT.rstrip('/')
        self.modal_prefix = get_modal_prefix()
        
    # Agent Management Endpoints
    AGENT_ENDPOINTS = {
        "create_agent_run": EndpointConfig(
            path="/v1/organizations/{org_id}/agent/run",
            method="POST",
            rate_limit=RateLimit.AGENT_CREATION,
            description="Creates a new agent run with specified prompt",
            cli_command="codegen agent create",
            cache_ttl_seconds=None
        ),
        "get_agent_run": EndpointConfig(
            path="/v1/organizations/{org_id}/agent/run/{agent_run_id}",
            method="GET",
            rate_limit=RateLimit.STANDARD,
            description="Retrieves detailed information about a specific agent run",
            cli_command="codegen agent get",
            cache_ttl_seconds=30
        ),
        "list_agent_runs": EndpointConfig(
            path="/v1/organizations/{org_id}/agent/runs",
            method="GET",
            rate_limit=RateLimit.STANDARD,
            description="Lists agent runs with pagination and filtering",
            cli_command="codegen agents list",
            cache_ttl_seconds=30
        ),
        "resume_agent_run": EndpointConfig(
            path="/v1/organizations/{org_id}/agent/run/resume",
            method="POST",
            rate_limit=RateLimit.AGENT_CREATION,
            description="Resumes an agent run with follow-up queries",
            cache_ttl_seconds=None
        )
    }
    
    # Claude Code Integration Endpoints
    CLAUDE_ENDPOINTS = {
        "create_claude_session": EndpointConfig(
            path="/v1/organizations/{org_id}/claude_code/session",
            method="POST",
            rate_limit=RateLimit.STANDARD,
            description="Creates a new Claude Code session for tracking",
            cli_command="codegen claude",
            cache_ttl_seconds=None
        ),
        "get_session_status": EndpointConfig(
            path="/v1/organizations/{org_id}/claude_code/session/{session_id}/status",
            method="GET",
            rate_limit=RateLimit.STANDARD,
            description="Retrieves current status of a Claude session",
            cache_ttl_seconds=10
        ),
        "get_session_logs": EndpointConfig(
            path="/v1/organizations/{org_id}/claude_code/session/{session_id}/log",
            method="GET",
            rate_limit=RateLimit.LOG_ANALYSIS,
            description="Retrieves logs from a Claude session",
            cache_ttl_seconds=5
        )
    }
    
    # User & Organization Management Endpoints
    USER_ORG_ENDPOINTS = {
        "get_current_user": EndpointConfig(
            path="/v1/users/me",
            method="GET",
            rate_limit=RateLimit.STANDARD,
            description="Retrieves current user information",
            cli_command="codegen profile",
            requires_org_id=False,
            cache_ttl_seconds=600  # 10 minutes
        ),
        "list_organizations": EndpointConfig(
            path="/v1/organizations",
            method="GET",
            rate_limit=RateLimit.STANDARD,
            description="Lists organizations accessible to the user",
            cli_command="codegen org list",
            requires_org_id=False,
            cache_ttl_seconds=300  # 5 minutes
        ),
        "list_integrations": EndpointConfig(
            path="/v1/organizations/{org_id}/integrations",
            method="GET",
            rate_limit=RateLimit.STANDARD,
            description="Lists available integrations for an organization",
            cli_command="codegen integrations list",
            cache_ttl_seconds=900  # 15 minutes
        ),
        "list_tools": EndpointConfig(
            path="/v1/organizations/{org_id}/tools",
            method="GET",
            rate_limit=RateLimit.STANDARD,
            description="Lists available tools for an organization",
            cli_command="codegen tools list",
            cache_ttl_seconds=900  # 15 minutes
        ),
        "execute_tool": EndpointConfig(
            path="/v1/organizations/{org_id}/tools/execute",
            method="POST",
            rate_limit=RateLimit.STANDARD,
            description="Executes a tool via the API",
            cache_ttl_seconds=None
        )
    }
    
    # Repository Management Endpoints
    REPO_ENDPOINTS = {
        "list_repositories": EndpointConfig(
            path="/v1/organizations/{org_id}/repositories",
            method="GET",
            rate_limit=RateLimit.STANDARD,
            description="Lists repositories accessible to the organization",
            cache_ttl_seconds=300  # 5 minutes
        )
    }
    
    @classmethod
    def get_all_endpoints(cls) -> Dict[str, EndpointConfig]:
        """Get all configured endpoints."""
        endpoints = {}
        endpoints.update(cls.AGENT_ENDPOINTS)
        endpoints.update(cls.CLAUDE_ENDPOINTS)
        endpoints.update(cls.USER_ORG_ENDPOINTS)
        endpoints.update(cls.REPO_ENDPOINTS)
        return endpoints
    
    @classmethod
    def get_endpoint_url(cls, endpoint_name: str, **path_params) -> str:
        """Get the full URL for an endpoint with path parameters."""
        endpoints = cls.get_all_endpoints()
        if endpoint_name not in endpoints:
            raise ValueError(f"Unknown endpoint: {endpoint_name}")
        
        config = endpoints[endpoint_name]
        base_url = API_ENDPOINT.rstrip('/')
        path = config.path.format(**path_params)
        return f"{base_url}{path}"
    
    @classmethod
    def get_rate_limit_info(cls, endpoint_name: str) -> Dict[str, str]:
        """Get rate limit information for an endpoint."""
        endpoints = cls.get_all_endpoints()
        if endpoint_name not in endpoints:
            raise ValueError(f"Unknown endpoint: {endpoint_name}")
        
        config = endpoints[endpoint_name]
        rate_limit_map = {
            RateLimit.STANDARD: {"limit": "60", "window": "30s", "description": "Standard operations"},
            RateLimit.AGENT_CREATION: {"limit": "10", "window": "1min", "description": "Agent creation"},
            RateLimit.SETUP_COMMANDS: {"limit": "5", "window": "1min", "description": "Setup operations"},
            RateLimit.LOG_ANALYSIS: {"limit": "5", "window": "1min", "description": "Log analysis"}
        }
        
        return rate_limit_map[config.rate_limit]
    
    @classmethod
    def get_cache_ttl(cls, endpoint_name: str) -> Optional[int]:
        """Get cache TTL for an endpoint."""
        endpoints = cls.get_all_endpoints()
        if endpoint_name not in endpoints:
            return None
        return endpoints[endpoint_name].cache_ttl_seconds


# Legacy Modal Endpoints Configuration
class LegacyModalEndpoints:
    """Configuration for legacy Modal service endpoints."""
    
    @staticmethod
    def get_modal_endpoint(service_name: str) -> str:
        """Get Modal endpoint URL for a service."""
        modal_prefix = get_modal_prefix()
        endpoints = {
            "run": f"https://{modal_prefix}--cli-run.modal.run",
            "docs": f"https://{modal_prefix}--cli-docs.modal.run",
            "expert": f"https://{modal_prefix}--cli-ask-expert.modal.run",
            "identify": f"https://{modal_prefix}--cli-identify.modal.run",
            "create": f"https://{modal_prefix}--cli-create.modal.run",
            "deploy": f"https://{modal_prefix}--cli-deploy.modal.run",
            "lookup": f"https://{modal_prefix}--cli-lookup.modal.run",
            "run_on_pr": f"https://{modal_prefix}--cli-run-on-pull-request.modal.run",
            "pr_lookup": f"https://{modal_prefix}--cli-pr-lookup.modal.run",
            "improve": f"https://{modal_prefix}--cli-improve.modal.run",
            "mcp_server": f"https://{modal_prefix}--codegen-mcp-server.modal.run/mcp"
        }
        
        if service_name not in endpoints:
            raise ValueError(f"Unknown Modal service: {service_name}")
        
        return endpoints[service_name]


# Dashboard-specific endpoint configurations
DASHBOARD_SPECIFIC_ENDPOINTS = {
    "websocket": {
        "path": "/ws",
        "description": "WebSocket endpoint for real-time updates"
    },
    "health": {
        "path": "/health",
        "description": "Health check endpoint"
    },
    "metrics": {
        "path": "/metrics",
        "description": "Prometheus metrics endpoint"
    }
}


def get_dashboard_config() -> Dict:
    """Get complete dashboard configuration."""
    return {
        "api_endpoints": DashboardAPIEndpoints.get_all_endpoints(),
        "legacy_endpoints": LegacyModalEndpoints,
        "dashboard_endpoints": DASHBOARD_SPECIFIC_ENDPOINTS,
        "base_url": API_ENDPOINT,
        "modal_prefix": get_modal_prefix()
    }
