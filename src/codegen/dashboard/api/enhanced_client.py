"""Enhanced API client with caching and rate limiting for dashboard operations."""

import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
import hashlib

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from codegen.cli.api.client import RestAPI
from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.utils.org import resolve_org_id
from codegen.dashboard.config.api_endpoints import DashboardAPIEndpoints, RateLimit
from codegen.dashboard.cache.redis_client import get_redis_client
from codegen.dashboard.api.rate_limiter import RateLimiter
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class EnhancedAPIClient:
    """Enhanced API client with caching, rate limiting, and dashboard-specific features."""
    
    def __init__(self, token: Optional[str] = None, enable_caching: bool = True, enable_rate_limiting: bool = True):
        """Initialize enhanced API client.
        
        Args:
            token: Authentication token (defaults to current token)
            enable_caching: Whether to enable response caching
            enable_rate_limiting: Whether to enable rate limiting
        """
        self.token = token or get_current_token()
        self.enable_caching = enable_caching
        self.enable_rate_limiting = enable_rate_limiting
        
        if not self.token:
            raise ValueError("Authentication token is required")
        
        # Initialize base client
        self.base_client = RestAPI(self.token)
        
        # Initialize caching
        self.cache_client = get_redis_client() if enable_caching else None
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter() if enable_rate_limiting else None
        
        # Configure requests session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "Codegen-Dashboard/1.0"
        })
        
        logger.info("Enhanced API client initialized", extra={
            "caching_enabled": enable_caching,
            "rate_limiting_enabled": enable_rate_limiting
        })
    
    def _generate_cache_key(self, endpoint: str, params: Optional[Dict] = None, body: Optional[Dict] = None) -> str:
        """Generate cache key for request."""
        key_data = {
            "endpoint": endpoint,
            "params": params or {},
            "body": body or {},
            "token_hash": hashlib.md5(self.token.encode()).hexdigest()[:8]
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return f"codegen:api:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    async def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Get response from cache."""
        if not self.cache_client:
            return None
        
        try:
            cached_data = await self.cache_client.get(cache_key)
            if cached_data:
                logger.debug("Cache hit", extra={"cache_key": cache_key})
                return json.loads(cached_data)
        except Exception as e:
            logger.warning("Cache get failed", extra={"error": str(e), "cache_key": cache_key})
        
        return None
    
    async def _set_cache(self, cache_key: str, data: Dict, ttl_seconds: int) -> None:
        """Set response in cache."""
        if not self.cache_client:
            return
        
        try:
            await self.cache_client.setex(cache_key, ttl_seconds, json.dumps(data))
            logger.debug("Cache set", extra={"cache_key": cache_key, "ttl": ttl_seconds})
        except Exception as e:
            logger.warning("Cache set failed", extra={"error": str(e), "cache_key": cache_key})
    
    async def _check_rate_limit(self, endpoint_name: str) -> bool:
        """Check if request is within rate limits."""
        if not self.rate_limiter:
            return True
        
        return await self.rate_limiter.check_rate_limit(endpoint_name, self.token)
    
    async def _make_request(self, method: str, endpoint_name: str, path_params: Optional[Dict] = None,
                          query_params: Optional[Dict] = None, body: Optional[Dict] = None) -> Dict:
        """Make API request with caching and rate limiting."""
        # Get endpoint configuration
        endpoints = DashboardAPIEndpoints.get_all_endpoints()
        if endpoint_name not in endpoints:
            raise ValueError(f"Unknown endpoint: {endpoint_name}")
        
        config = endpoints[endpoint_name]
        
        # Check rate limits
        if not await self._check_rate_limit(endpoint_name):
            rate_limit_info = DashboardAPIEndpoints.get_rate_limit_info(endpoint_name)
            raise Exception(f"Rate limit exceeded for {endpoint_name}. Limit: {rate_limit_info['limit']}/{rate_limit_info['window']}")
        
        # Build URL
        url = DashboardAPIEndpoints.get_endpoint_url(endpoint_name, **(path_params or {}))
        
        # Generate cache key for GET requests
        cache_key = None
        if method.upper() == "GET" and self.enable_caching:
            cache_key = self._generate_cache_key(url, query_params, body)
            
            # Try to get from cache
            cached_response = await self._get_from_cache(cache_key)
            if cached_response:
                return cached_response
        
        # Make the request
        try:
            logger.info("Making API request", extra={
                "method": method,
                "endpoint": endpoint_name,
                "url": url
            })
            
            response = self.session.request(
                method=method,
                url=url,
                params=query_params,
                json=body,
                timeout=30
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            # Cache GET responses
            if method.upper() == "GET" and cache_key and config.cache_ttl_seconds:
                await self._set_cache(cache_key, response_data, config.cache_ttl_seconds)
            
            logger.info("API request successful", extra={
                "method": method,
                "endpoint": endpoint_name,
                "status_code": response.status_code
            })
            
            return response_data
            
        except requests.RequestException as e:
            logger.error("API request failed", extra={
                "method": method,
                "endpoint": endpoint_name,
                "error": str(e)
            })
            raise
    
    # Agent Management Methods
    async def create_agent_run(self, org_id: int, prompt: str, model: Optional[str] = None, 
                             repo_id: Optional[int] = None) -> Dict:
        """Create a new agent run."""
        body = {"prompt": prompt}
        if model:
            body["model"] = model
        if repo_id:
            body["repo_id"] = repo_id
        
        return await self._make_request(
            method="POST",
            endpoint_name="create_agent_run",
            path_params={"org_id": org_id},
            body=body
        )
    
    async def get_agent_run(self, org_id: int, agent_run_id: int) -> Dict:
        """Get agent run details."""
        return await self._make_request(
            method="GET",
            endpoint_name="get_agent_run",
            path_params={"org_id": org_id, "agent_run_id": agent_run_id}
        )
    
    async def list_agent_runs(self, org_id: int, source_type: Optional[str] = None, 
                            user_id: Optional[str] = None, page: int = 1, page_size: int = 10) -> Dict:
        """List agent runs with filtering."""
        query_params = {"page": page, "page_size": page_size}
        if source_type:
            query_params["source_type"] = source_type
        if user_id:
            query_params["user_id"] = user_id
        
        return await self._make_request(
            method="GET",
            endpoint_name="list_agent_runs",
            path_params={"org_id": org_id},
            query_params=query_params
        )
    
    async def resume_agent_run(self, org_id: int, agent_run_id: int, follow_up_prompt: str) -> Dict:
        """Resume an agent run with follow-up."""
        return await self._make_request(
            method="POST",
            endpoint_name="resume_agent_run",
            path_params={"org_id": org_id},
            body={"agent_run_id": agent_run_id, "follow_up_prompt": follow_up_prompt}
        )
    
    # Claude Code Integration Methods
    async def create_claude_session(self, org_id: int, session_id: str) -> Dict:
        """Create a Claude Code session."""
        return await self._make_request(
            method="POST",
            endpoint_name="create_claude_session",
            path_params={"org_id": org_id},
            body={"session_id": session_id}
        )
    
    async def get_session_status(self, org_id: int, session_id: str) -> Dict:
        """Get Claude session status."""
        return await self._make_request(
            method="GET",
            endpoint_name="get_session_status",
            path_params={"org_id": org_id, "session_id": session_id}
        )
    
    async def get_session_logs(self, org_id: int, session_id: str) -> Dict:
        """Get Claude session logs."""
        return await self._make_request(
            method="GET",
            endpoint_name="get_session_logs",
            path_params={"org_id": org_id, "session_id": session_id}
        )
    
    # User & Organization Methods
    async def get_current_user(self) -> Dict:
        """Get current user information."""
        return await self._make_request(
            method="GET",
            endpoint_name="get_current_user"
        )
    
    async def list_organizations(self) -> Dict:
        """List user organizations."""
        return await self._make_request(
            method="GET",
            endpoint_name="list_organizations"
        )
    
    async def list_integrations(self, org_id: int) -> Dict:
        """List organization integrations."""
        return await self._make_request(
            method="GET",
            endpoint_name="list_integrations",
            path_params={"org_id": org_id}
        )
    
    async def list_tools(self, org_id: int) -> Dict:
        """List organization tools."""
        return await self._make_request(
            method="GET",
            endpoint_name="list_tools",
            path_params={"org_id": org_id}
        )
    
    async def execute_tool(self, org_id: int, tool_name: str, arguments: Dict) -> Dict:
        """Execute a tool via API."""
        return await self._make_request(
            method="POST",
            endpoint_name="execute_tool",
            path_params={"org_id": org_id},
            body={"tool_name": tool_name, "arguments": arguments}
        )
    
    # Repository Methods
    async def list_repositories(self, org_id: int, page: int = 1, page_size: int = 50) -> Dict:
        """List organization repositories."""
        return await self._make_request(
            method="GET",
            endpoint_name="list_repositories",
            path_params={"org_id": org_id},
            query_params={"page": page, "page_size": page_size}
        )
    
    # Batch Operations
    async def batch_get_agent_runs(self, org_id: int, agent_run_ids: List[int]) -> List[Dict]:
        """Get multiple agent runs in batch."""
        tasks = [self.get_agent_run(org_id, agent_run_id) for agent_run_id in agent_run_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return successful results
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning("Batch get agent run failed", extra={
                    "agent_run_id": agent_run_ids[i],
                    "error": str(result)
                })
            else:
                successful_results.append(result)
        
        return successful_results
    
    # Cache Management
    async def invalidate_cache(self, pattern: str = "codegen:api:*") -> int:
        """Invalidate cache entries matching pattern."""
        if not self.cache_client:
            return 0
        
        try:
            keys = await self.cache_client.keys(pattern)
            if keys:
                deleted = await self.cache_client.delete(*keys)
                logger.info("Cache invalidated", extra={"pattern": pattern, "deleted_keys": deleted})
                return deleted
        except Exception as e:
            logger.error("Cache invalidation failed", extra={"error": str(e), "pattern": pattern})
        
        return 0
    
    async def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        if not self.cache_client:
            return {"enabled": False}
        
        try:
            info = await self.cache_client.info()
            return {
                "enabled": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0)
            }
        except Exception as e:
            logger.error("Failed to get cache stats", extra={"error": str(e)})
            return {"enabled": True, "error": str(e)}
    
    # Rate Limit Management
    async def get_rate_limit_status(self, endpoint_name: str) -> Dict:
        """Get rate limit status for an endpoint."""
        if not self.rate_limiter:
            return {"enabled": False}
        
        return await self.rate_limiter.get_status(endpoint_name, self.token)
    
    async def reset_rate_limits(self, endpoint_name: Optional[str] = None) -> bool:
        """Reset rate limits for an endpoint or all endpoints."""
        if not self.rate_limiter:
            return False
        
        return await self.rate_limiter.reset_limits(self.token, endpoint_name)
    
    # Health Check
    async def health_check(self) -> Dict:
        """Perform health check on API and dependencies."""
        health_status = {
            "api": False,
            "cache": False,
            "rate_limiter": False,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Test API connectivity
        try:
            await self.get_current_user()
            health_status["api"] = True
        except Exception as e:
            logger.error("API health check failed", extra={"error": str(e)})
        
        # Test cache connectivity
        if self.cache_client:
            try:
                await self.cache_client.ping()
                health_status["cache"] = True
            except Exception as e:
                logger.error("Cache health check failed", extra={"error": str(e)})
        else:
            health_status["cache"] = "disabled"
        
        # Test rate limiter
        if self.rate_limiter:
            try:
                await self.rate_limiter.health_check()
                health_status["rate_limiter"] = True
            except Exception as e:
                logger.error("Rate limiter health check failed", extra={"error": str(e)})
        else:
            health_status["rate_limiter"] = "disabled"
        
        return health_status


# Global client instance
_enhanced_client: Optional[EnhancedAPIClient] = None


def get_enhanced_client(token: Optional[str] = None) -> EnhancedAPIClient:
    """Get the global enhanced API client instance."""
    global _enhanced_client
    if _enhanced_client is None or (token and _enhanced_client.token != token):
        _enhanced_client = EnhancedAPIClient(token)
    return _enhanced_client


def init_enhanced_client(token: str, enable_caching: bool = True, enable_rate_limiting: bool = True) -> EnhancedAPIClient:
    """Initialize the global enhanced API client with custom settings."""
    global _enhanced_client
    _enhanced_client = EnhancedAPIClient(token, enable_caching, enable_rate_limiting)
    return _enhanced_client
