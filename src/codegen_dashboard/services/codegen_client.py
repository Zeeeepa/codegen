"""
Codegen API Client Service

Wraps the existing Codegen CLI functionality and API client to provide
a clean interface for the dashboard.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import os
import sys

# Add the codegen module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from codegen.agents.agent import Agent, AgentTask
from codegen.cli.auth.token_manager import TokenManager
from codegen.cli.utils.org import resolve_org_id
from codegen_api_client.api.agents_api import AgentsApi
from codegen_api_client.api.organizations_api import OrganizationsApi
from codegen_api_client.api_client import ApiClient
from codegen_api_client.configuration import Configuration


class CodegenClient:
    """
    Service that wraps existing Codegen CLI functionality for the dashboard.
    
    Provides methods for:
    - Agent run management (create, list, get status, resume)
    - Organization management
    - Authentication handling
    - Rate limit management
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Codegen client."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize authentication
        self.token_manager = TokenManager()
        self.token = self.token_manager.get_token()
        self.org_id = resolve_org_id(None)  # Use default org
        
        if not self.token:
            raise ValueError("No authentication token found. Please run 'codegen login' first.")
        
        # Initialize API client
        api_config = Configuration(
            host=config.get('api_base_url', 'https://api.codegen.com'),
            access_token=self.token
        )
        self.api_client = ApiClient(configuration=api_config)
        self.agents_api = AgentsApi(self.api_client)
        self.organizations_api = OrganizationsApi(self.api_client)
        
        # Initialize Agent wrapper
        self.agent = Agent(token=self.token, org_id=self.org_id)
        
        # Rate limiting tracking
        self.last_agent_creation = None
        self.last_status_check = None
        self.agent_creation_count = 0
        self.status_check_count = 0
        
    async def create_agent_run(self, prompt: str, repo_id: Optional[int] = None) -> AgentTask:
        """
        Create a new agent run.
        
        Rate limit: 10 requests per minute
        """
        try:
            # Check rate limits
            await self._check_agent_creation_rate_limit()
            
            self.logger.info(f"Creating agent run with prompt: {prompt[:100]}...")
            
            # Use the existing Agent class
            task = self.agent.run(prompt)
            
            # Update rate limiting
            self.agent_creation_count += 1
            self.last_agent_creation = datetime.now()
            
            self.logger.info(f"Agent run created successfully: {task.id}")
            return task
            
        except Exception as e:
            self.logger.error(f"Failed to create agent run: {e}")
            raise
    
    async def get_agent_run_status(self, agent_run_id: int) -> Dict[str, Any]:
        """
        Get the status of an agent run.
        
        Rate limit: 60 requests per 30 seconds
        """
        try:
            # Check rate limits
            await self._check_status_rate_limit()
            
            self.logger.debug(f"Getting status for agent run: {agent_run_id}")
            
            # Get agent run details
            agent_run = self.agents_api.get_agent_run_v1_organizations_org_id_agent_run_agent_run_id_get(
                org_id=self.org_id,
                agent_run_id=agent_run_id,
                authorization=f"Bearer {self.token}"
            )
            
            # Update rate limiting
            self.status_check_count += 1
            self.last_status_check = datetime.now()
            
            return {
                'id': agent_run.id,
                'status': agent_run.status,
                'result': agent_run.result,
                'web_url': agent_run.web_url,
                'created_at': agent_run.created_at,
                'organization_id': agent_run.organization_id
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get agent run status: {e}")
            raise
    
    async def list_agent_runs(self, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """
        List agent runs for the current organization.
        
        Rate limit: 60 requests per 30 seconds
        """
        try:
            # Check rate limits
            await self._check_status_rate_limit()
            
            self.logger.debug(f"Listing agent runs (skip={skip}, limit={limit})")
            
            # This would need to be implemented in the API client
            # For now, we'll return a placeholder
            # TODO: Implement actual agent runs listing API call
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to list agent runs: {e}")
            raise
    
    async def resume_agent_run(self, agent_run_id: int, prompt: str) -> AgentTask:
        """
        Resume an agent run with a follow-up prompt.
        
        Rate limit: 10 requests per minute
        """
        try:
            # Check rate limits
            await self._check_agent_creation_rate_limit()
            
            self.logger.info(f"Resuming agent run {agent_run_id} with prompt: {prompt[:100]}...")
            
            # TODO: Implement resume functionality using the API
            # For now, create a new run (this should be replaced with actual resume API)
            task = await self.create_agent_run(f"Resume from run {agent_run_id}: {prompt}")
            
            return task
            
        except Exception as e:
            self.logger.error(f"Failed to resume agent run: {e}")
            raise
    
    async def get_organizations(self) -> List[Dict[str, Any]]:
        """
        Get list of organizations for the current user.
        
        Rate limit: 60 requests per 30 seconds
        """
        try:
            # Check rate limits
            await self._check_status_rate_limit()
            
            self.logger.debug("Getting organizations")
            
            orgs_response = self.organizations_api.get_organizations_v1_organizations_get(
                authorization=f"Bearer {self.token}"
            )
            
            return [
                {
                    'id': org.id,
                    'name': org.name,
                    'created_at': org.created_at
                }
                for org in orgs_response.items
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to get organizations: {e}")
            raise
    
    async def _check_agent_creation_rate_limit(self):
        """Check if we're within the agent creation rate limit (10/minute)."""
        if self.last_agent_creation:
            time_since_last = (datetime.now() - self.last_agent_creation).total_seconds()
            if time_since_last < 60 and self.agent_creation_count >= 10:
                wait_time = 60 - time_since_last
                self.logger.warning(f"Rate limit reached for agent creation. Waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                self.agent_creation_count = 0
    
    async def _check_status_rate_limit(self):
        """Check if we're within the status check rate limit (60/30s)."""
        if self.last_status_check:
            time_since_last = (datetime.now() - self.last_status_check).total_seconds()
            if time_since_last < 30 and self.status_check_count >= 60:
                wait_time = 30 - time_since_last
                self.logger.warning(f"Rate limit reached for status checks. Waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                self.status_check_count = 0
    
    def get_current_org_id(self) -> int:
        """Get the current organization ID."""
        return self.org_id
    
    def get_current_token(self) -> str:
        """Get the current authentication token."""
        return self.token
    
    def is_authenticated(self) -> bool:
        """Check if the client is properly authenticated."""
        return self.token is not None and self.org_id is not None
