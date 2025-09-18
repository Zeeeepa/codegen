"""
Enhanced API Client - Step 3 Implementation

Intelligent API client with caching, rate limiting, and batch operations
that respects Codegen's API constraints while providing optimal performance.
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import hashlib

import aiohttp
import redis.asyncio as redis
from tenacity import retry, stop_after_attempt, wait_exponential

from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.utils.org import resolve_org_id
from codegen.cli.api.endpoints import API_ENDPOINT

logger = logging.getLogger(__name__)


class RequestPriority(Enum):
    """Request priority levels for intelligent queuing"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class APIEndpointConfig:
    """Configuration for API endpoints with rate limiting"""
    endpoint: str
    rate_limit: int  # requests per window
    window_seconds: int
    cache_ttl: int = 300  # 5 minutes default
    priority: RequestPriority = RequestPriority.NORMAL


class CodegenAPIEndpoints:
    """Codegen API endpoint configurations with rate limits"""
    
    ENDPOINTS = {
        # Agent Management (10 req/min for creation, 60 req/30s for others)
        "create_agent_run": APIEndpointConfig(
            "/v1/organizations/{org_id}/agent/run",
            rate_limit=10, window_seconds=60, cache_ttl=0,
            priority=RequestPriority.HIGH
        ),
        "get_agent_run": APIEndpointConfig(
            "/v1/organizations/{org_id}/agent/run/{agent_run_id}",
            rate_limit=60, window_seconds=30, cache_ttl=30
        ),
        "list_agent_runs": APIEndpointConfig(
            "/v1/organizations/{org_id}/agent/runs",
            rate_limit=60, window_seconds=30, cache_ttl=60
        ),
        "resume_agent_run": APIEndpointConfig(
            "/v1/organizations/{org_id}/agent/run/resume",
            rate_limit=10, window_seconds=60, cache_ttl=0,
            priority=RequestPriority.HIGH
        ),
        "get_agent_logs": APIEndpointConfig(
            "/v1/organizations/{org_id}/agent/run/{agent_run_id}/logs",
            rate_limit=5, window_seconds=60, cache_ttl=10
        ),
        
        # Organization Management (60 req/30s)
        "get_current_user": APIEndpointConfig(
            "/v1/users/me",
            rate_limit=60, window_seconds=30, cache_ttl=300
        ),
        "list_organizations": APIEndpointConfig(
            "/v1/organizations",
            rate_limit=60, window_seconds=30, cache_ttl=300
        ),
        "list_repositories": APIEndpointConfig(
            "/v1/organizations/{org_id}/repositories",
            rate_limit=60, window_seconds=30, cache_ttl=180
        ),
        "list_integrations": APIEndpointConfig(
            "/v1/organizations/{org_id}/integrations",
            rate_limit=60, window_seconds=30, cache_ttl=300
        ),
        "list_tools": APIEndpointConfig(
            "/v1/organizations/{org_id}/tools",
            rate_limit=60, window_seconds=30, cache_ttl=300
        ),
        
        # Setup & Analysis (5 req/min)
        "generate_setup_commands": APIEndpointConfig(
            "/v1/organizations/{org_id}/setup",
            rate_limit=5, window_seconds=60, cache_ttl=0,
            priority=RequestPriority.LOW
        ),
        "analyze_sandbox_logs": APIEndpointConfig(
            "/v1/organizations/{org_id}/sandbox/analyze",
            rate_limit=5, window_seconds=60, cache_ttl=0,
            priority=RequestPriority.LOW
        ),
    }


class RateLimiter:
    """Intelligent rate limiter with priority queuing"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.local_limits = {}  # Fallback for when Redis is unavailable
        
    async def check_rate_limit(self, endpoint_name: str, token_hash: str) -> bool:
        """Check if request is within rate limits"""
        config = CodegenAPIEndpoints.ENDPOINTS.get(endpoint_name)
        if not config:
            return True
            
        key = f"rate_limit:{endpoint_name}:{token_hash}"
        
        if self.redis:
            try:
                current = await self.redis.get(key)
                if current is None:
                    await self.redis.setex(key, config.window_seconds, 1)
                    return True
                elif int(current) < config.rate_limit:
                    await self.redis.incr(key)
                    return True
                else:
                    return False
            except Exception as e:
                logger.warning(f"Redis rate limiting failed: {e}")
                
        # Fallback to local rate limiting
        now = time.time()
        if key not in self.local_limits:
            self.local_limits[key] = {"count": 1, "window_start": now}
            return True
            
        limit_data = self.local_limits[key]
        if now - limit_data["window_start"] > config.window_seconds:
            self.local_limits[key] = {"count": 1, "window_start": now}
            return True
        elif limit_data["count"] < config.rate_limit:
            limit_data["count"] += 1
            return True
        else:
            return False


class CacheManager:
    """Intelligent caching with multiple backends"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.local_cache = {}  # In-memory fallback cache
        
    def _generate_cache_key(self, endpoint: str, params: Dict = None) -> str:
        """Generate cache key for request"""
        key_data = {"endpoint": endpoint, "params": params or {}}
        key_string = json.dumps(key_data, sort_keys=True)
        return f"cache:{hashlib.md5(key_string.encode()).hexdigest()}"
        
    async def get(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Get cached response"""
        cache_key = self._generate_cache_key(endpoint, params)
        
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Redis cache get failed: {e}")
                
        # Fallback to local cache
        return self.local_cache.get(cache_key)
        
    async def set(self, endpoint: str, params: Dict, data: Dict, ttl: int):
        """Set cached response"""
        cache_key = self._generate_cache_key(endpoint, params)
        
        if self.redis:
            try:
                await self.redis.setex(cache_key, ttl, json.dumps(data))
            except Exception as e:
                logger.warning(f"Redis cache set failed: {e}")
                
        # Always set in local cache as fallback
        self.local_cache[cache_key] = data
        
        # Simple TTL for local cache
        asyncio.create_task(self._expire_local_cache(cache_key, ttl))
        
    async def _expire_local_cache(self, key: str, ttl: int):
        """Expire local cache entry after TTL"""
        await asyncio.sleep(ttl)
        self.local_cache.pop(key, None)


class BatchProcessor:
    """Batch operations for efficiency"""
    
    def __init__(self, max_batch_size: int = 10, batch_timeout: float = 1.0):
        self.max_batch_size = max_batch_size
        self.batch_timeout = batch_timeout
        self.pending_requests = []
        self.batch_timer = None
        
    async def add_request(self, request_func: Callable, *args, **kwargs) -> Any:
        """Add request to batch processing queue"""
        future = asyncio.Future()
        self.pending_requests.append((request_func, args, kwargs, future))
        
        if len(self.pending_requests) >= self.max_batch_size:
            await self._process_batch()
        elif self.batch_timer is None:
            self.batch_timer = asyncio.create_task(self._batch_timeout())
            
        return await future
        
    async def _batch_timeout(self):
        """Process batch after timeout"""
        await asyncio.sleep(self.batch_timeout)
        await self._process_batch()
        
    async def _process_batch(self):
        """Process all pending requests in batch"""
        if not self.pending_requests:
            return
            
        batch = self.pending_requests.copy()
        self.pending_requests.clear()
        self.batch_timer = None
        
        # Group requests by function for potential optimization
        grouped_requests = {}
        for request_func, args, kwargs, future in batch:
            func_name = request_func.__name__
            if func_name not in grouped_requests:
                grouped_requests[func_name] = []
            grouped_requests[func_name].append((request_func, args, kwargs, future))
            
        # Execute all requests concurrently
        tasks = []
        for group in grouped_requests.values():
            for request_func, args, kwargs, future in group:
                task = asyncio.create_task(self._execute_request(request_func, args, kwargs, future))
                tasks.append(task)
                
        await asyncio.gather(*tasks, return_exceptions=True)
        
    async def _execute_request(self, request_func: Callable, args: tuple, kwargs: dict, future: asyncio.Future):
        """Execute individual request and set result"""
        try:
            result = await request_func(*args, **kwargs)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)


class EnhancedAPIClient:
    """
    Enhanced API client with intelligent caching, rate limiting, and batch operations
    """
    
    def __init__(
        self,
        token: Optional[str] = None,
        org_id: Optional[int] = None,
        redis_url: Optional[str] = None,
        enable_caching: bool = True,
        enable_rate_limiting: bool = True,
        enable_batching: bool = True
    ):
        """Initialize enhanced API client"""
        self.token = token or get_current_token()
        self.org_id = org_id or resolve_org_id()
        self.base_url = API_ENDPOINT.rstrip('/')
        
        if not self.token:
            raise ValueError("Authentication token is required")
            
        # Initialize components
        self.redis_client = None
        if redis_url and (enable_caching or enable_rate_limiting):
            try:
                self.redis_client = redis.from_url(redis_url)
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
                
        self.rate_limiter = RateLimiter(self.redis_client) if enable_rate_limiting else None
        self.cache_manager = CacheManager(self.redis_client) if enable_caching else None
        self.batch_processor = BatchProcessor() if enable_batching else None
        
        # HTTP session configuration
        self.session = None
        self.token_hash = hashlib.md5(self.token.encode()).hexdigest()[:8]
        
        logger.info("Enhanced API client initialized", extra={
            "caching": enable_caching,
            "rate_limiting": enable_rate_limiting,
            "batching": enable_batching,
            "redis": self.redis_client is not None
        })
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "User-Agent": "Codegen-CICD-Interface/1.0"
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        if self.redis_client:
            await self.redis_client.close()
            
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _make_request(
        self,
        method: str,
        endpoint_name: str,
        path_params: Optional[Dict] = None,
        query_params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Make HTTP request with intelligent caching and rate limiting"""
        
        # Get endpoint configuration
        config = CodegenAPIEndpoints.ENDPOINTS.get(endpoint_name)
        if not config:
            raise ValueError(f"Unknown endpoint: {endpoint_name}")
            
        # Check rate limits
        if self.rate_limiter:
            if not await self.rate_limiter.check_rate_limit(endpoint_name, self.token_hash):
                raise Exception(f"Rate limit exceeded for {endpoint_name}")
                
        # Build URL
        url = self.base_url + config.endpoint.format(**(path_params or {}))
        
        # Check cache for GET requests
        if method.upper() == "GET" and use_cache and self.cache_manager and config.cache_ttl > 0:
            cached_response = await self.cache_manager.get(url, query_params)
            if cached_response:
                logger.debug(f"Cache hit for {endpoint_name}")
                return cached_response
                
        # Make HTTP request
        logger.info(f"Making {method} request to {endpoint_name}")
        
        async with self.session.request(
            method=method,
            url=url,
            params=query_params,
            json=json_data
        ) as response:
            response.raise_for_status()
            response_data = await response.json()
            
            # Cache GET responses
            if (method.upper() == "GET" and self.cache_manager and 
                config.cache_ttl > 0 and response.status == 200):
                await self.cache_manager.set(url, query_params, response_data, config.cache_ttl)
                
            return response_data
            
    # Agent Management Methods
    async def create_agent_run(
        self,
        prompt: str,
        model: Optional[str] = None,
        repo_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new agent run"""
        json_data = {"prompt": prompt}
        if model:
            json_data["model"] = model
        if repo_id:
            json_data["repo_id"] = repo_id
            
        if self.batch_processor:
            return await self.batch_processor.add_request(
                self._make_request,
                "POST", "create_agent_run",
                {"org_id": self.org_id},
                None, json_data, False
            )
        else:
            return await self._make_request(
                "POST", "create_agent_run",
                {"org_id": self.org_id},
                None, json_data, False
            )
            
    async def get_agent_run(self, agent_run_id: int) -> Dict[str, Any]:
        """Get agent run details"""
        return await self._make_request(
            "GET", "get_agent_run",
            {"org_id": self.org_id, "agent_run_id": agent_run_id}
        )
        
    async def list_agent_runs(
        self,
        source_type: Optional[str] = None,
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """List agent runs with filtering"""
        query_params = {"page": page, "page_size": page_size}
        if source_type:
            query_params["source_type"] = source_type
        if user_id:
            query_params["user_id"] = user_id
            
        return await self._make_request(
            "GET", "list_agent_runs",
            {"org_id": self.org_id},
            query_params
        )
        
    async def resume_agent_run(self, agent_run_id: int, follow_up_prompt: str) -> Dict[str, Any]:
        """Resume an agent run with follow-up"""
        return await self._make_request(
            "POST", "resume_agent_run",
            {"org_id": self.org_id},
            None,
            {"agent_run_id": agent_run_id, "follow_up_prompt": follow_up_prompt},
            False
        )
        
    async def get_agent_logs(self, agent_run_id: int, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get agent run logs"""
        return await self._make_request(
            "GET", "get_agent_logs",
            {"org_id": self.org_id, "agent_run_id": agent_run_id},
            {"skip": skip, "limit": limit}
        )
        
    # Organization & User Methods
    async def get_current_user(self) -> Dict[str, Any]:
        """Get current user information"""
        return await self._make_request("GET", "get_current_user")
        
    async def list_organizations(self) -> Dict[str, Any]:
        """List user organizations"""
        return await self._make_request("GET", "list_organizations")
        
    async def list_repositories(self, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """List organization repositories"""
        return await self._make_request(
            "GET", "list_repositories",
            {"org_id": self.org_id},
            {"page": page, "page_size": page_size}
        )
        
    async def list_integrations(self) -> Dict[str, Any]:
        """List organization integrations"""
        return await self._make_request(
            "GET", "list_integrations",
            {"org_id": self.org_id}
        )
        
    async def list_tools(self) -> Dict[str, Any]:
        """List organization tools"""
        return await self._make_request(
            "GET", "list_tools",
            {"org_id": self.org_id}
        )
        
    # Batch Operations
    async def batch_get_agent_runs(self, agent_run_ids: List[int]) -> List[Dict[str, Any]]:
        """Get multiple agent runs in batch"""
        if self.batch_processor:
            tasks = [
                self.batch_processor.add_request(
                    self._make_request,
                    "GET", "get_agent_run",
                    {"org_id": self.org_id, "agent_run_id": agent_run_id}
                )
                for agent_run_id in agent_run_ids
            ]
        else:
            tasks = [
                self._make_request(
                    "GET", "get_agent_run",
                    {"org_id": self.org_id, "agent_run_id": agent_run_id}
                )
                for agent_run_id in agent_run_ids
            ]
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return successful results
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Batch get agent run failed for ID {agent_run_ids[i]}: {result}")
            else:
                successful_results.append(result)
                
        return successful_results
        
    # Health & Monitoring
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on API and dependencies"""
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
            logger.error(f"API health check failed: {e}")
            
        # Test cache connectivity
        if self.cache_manager and self.redis_client:
            try:
                await self.redis_client.ping()
                health_status["cache"] = True
            except Exception as e:
                logger.error(f"Cache health check failed: {e}")
        else:
            health_status["cache"] = "disabled"
            
        # Test rate limiter
        if self.rate_limiter:
            health_status["rate_limiter"] = True
        else:
            health_status["rate_limiter"] = "disabled"
            
        return health_status
        
    async def get_metrics(self) -> Dict[str, Any]:
        """Get client performance metrics"""
        metrics = {
            "requests_made": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "rate_limit_hits": 0,
            "batch_requests": 0
        }
        
        # TODO: Implement metrics collection
        return metrics


# Global client instance for convenience
_global_client: Optional[EnhancedAPIClient] = None


async def get_client(
    token: Optional[str] = None,
    org_id: Optional[int] = None,
    redis_url: Optional[str] = None
) -> EnhancedAPIClient:
    """Get global enhanced API client instance"""
    global _global_client
    
    if _global_client is None:
        _global_client = EnhancedAPIClient(
            token=token,
            org_id=org_id,
            redis_url=redis_url
        )
        
    return _global_client


async def close_client():
    """Close global client instance"""
    global _global_client
    
    if _global_client:
        await _global_client.__aexit__(None, None, None)
        _global_client = None
