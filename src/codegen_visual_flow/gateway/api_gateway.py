"""
API Gateway Layer
================

Unified API gateway for the Codegen Visual Flow interface, providing centralized
routing, authentication, rate limiting, and integration with existing Codegen APIs.

Features:
- Request routing and load balancing
- Authentication and authorization
- Rate limiting and throttling
- Request/response transformation
- Integration with existing Codegen API endpoints
- Real-time WebSocket proxy
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import aiohttp
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Request, Response, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from codegen.cli.api.client import RestAPI
from ..core.event_system import Event, EventType, event_system
from ..auth.auth_manager import AuthManager
from ..cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class RouteType(str, Enum):
    """Types of routes handled by the gateway."""
    
    CODEGEN_API = "codegen_api"
    VISUAL_FLOW = "visual_flow"
    WEBSOCKET = "websocket"
    STATIC = "static"


@dataclass
class RouteConfig:
    """Configuration for a route."""
    
    path: str
    route_type: RouteType
    target_url: Optional[str] = None
    auth_required: bool = True
    rate_limit: Optional[int] = None  # requests per minute
    cache_ttl: Optional[int] = None  # seconds
    transform_request: bool = False
    transform_response: bool = False


class RateLimiter:
    """Rate limiting implementation using Redis."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
    
    async def is_allowed(
        self,
        key: str,
        limit: int,
        window: int = 60
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed based on rate limit.
        
        Args:
            key: Unique identifier for rate limiting (e.g., user_id, ip)
            limit: Maximum requests allowed
            window: Time window in seconds
            
        Returns:
            Tuple of (allowed, metadata)
        """
        try:
            current_time = int(time.time())
            window_start = current_time - window
            
            # Use sliding window rate limiting
            pipe = self.redis_client.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(f"rate_limit:{key}", 0, window_start)
            
            # Count current requests
            pipe.zcard(f"rate_limit:{key}")
            
            # Add current request
            pipe.zadd(f"rate_limit:{key}", {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(f"rate_limit:{key}", window)
            
            results = await pipe.execute()
            current_requests = results[1]
            
            allowed = current_requests < limit
            
            metadata = {
                "limit": limit,
                "remaining": max(0, limit - current_requests - 1),
                "reset_time": current_time + window,
                "window": window
            }
            
            return allowed, metadata
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Allow request on error (fail open)
            return True, {"limit": limit, "remaining": limit - 1}


class RequestTransformer:
    """Transform requests between different API formats."""
    
    @staticmethod
    def transform_codegen_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform request for Codegen API compatibility."""
        # Add any necessary transformations here
        return request_data
    
    @staticmethod
    def transform_visual_flow_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform request for Visual Flow API."""
        # Add visual flow specific transformations
        return request_data


class ResponseTransformer:
    """Transform responses between different API formats."""
    
    @staticmethod
    def transform_codegen_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Codegen API response for visual flow compatibility."""
        # Add response transformations here
        return response_data
    
    @staticmethod
    def enhance_with_metadata(
        response_data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance response with additional metadata."""
        return {
            **response_data,
            "_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "gateway_version": "1.0.0",
                **metadata
            }
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""
    
    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for certain paths
        if request.url.path.startswith("/health") or request.url.path.startswith("/metrics"):
            return await call_next(request)
        
        # Get rate limit key (user ID or IP)
        rate_limit_key = self._get_rate_limit_key(request)
        
        # Check rate limit (default: 1000 requests per minute)
        allowed, metadata = await self.rate_limiter.is_allowed(
            rate_limit_key, 
            limit=1000, 
            window=60
        )
        
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "limit": metadata["limit"],
                    "reset_time": metadata["reset_time"]
                },
                headers={
                    "X-RateLimit-Limit": str(metadata["limit"]),
                    "X-RateLimit-Remaining": str(metadata["remaining"]),
                    "X-RateLimit-Reset": str(metadata["reset_time"]),
                    "Retry-After": str(metadata["window"])
                }
            )
        
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(metadata["limit"])
        response.headers["X-RateLimit-Remaining"] = str(metadata["remaining"])
        response.headers["X-RateLimit-Reset"] = str(metadata["reset_time"])
        
        return response
    
    def _get_rate_limit_key(self, request: Request) -> str:
        """Get rate limiting key from request."""
        # Try to get user ID from auth header
        auth_header = request.headers.get("Authorization")
        if auth_header:
            # Extract user ID from token (simplified)
            return f"user:{auth_header[-10:]}"  # Use last 10 chars as identifier
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"


class APIGateway:
    """
    Main API Gateway class for routing and managing requests.
    
    Provides:
    - Centralized request routing
    - Authentication and authorization
    - Rate limiting and caching
    - Request/response transformation
    - Integration with existing Codegen APIs
    """
    
    def __init__(
        self,
        codegen_api_base_url: str = "https://api.codegen.com",
        redis_url: str = "redis://localhost:6379"
    ):
        self.app = FastAPI(
            title="Codegen Visual Flow API Gateway",
            description="Unified API gateway for the Codegen Visual Flow interface",
            version="1.0.0"
        )
        
        self.codegen_api_base_url = codegen_api_base_url
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        
        # Initialize components
        self.auth_manager = AuthManager()
        self.cache_manager = CacheManager()
        self.rate_limiter: Optional[RateLimiter] = None
        self.request_transformer = RequestTransformer()
        self.response_transformer = ResponseTransformer()
        
        # Route configurations
        self.routes: List[RouteConfig] = []
        
        # HTTP client for proxying requests
        self.http_client: Optional[aiohttp.ClientSession] = None
        
        self._setup_middleware()
        self._setup_routes()
    
    async def initialize(self) -> None:
        """Initialize the API gateway."""
        try:
            # Initialize Redis
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            
            # Initialize rate limiter
            self.rate_limiter = RateLimiter(self.redis_client)
            
            # Initialize HTTP client
            self.http_client = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            # Initialize other components
            await self.auth_manager.initialize()
            await self.cache_manager.initialize()
            
            logger.info("API Gateway initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize API Gateway: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the API gateway."""
        try:
            if self.http_client:
                await self.http_client.close()
            
            if self.redis_client:
                await self.redis_client.close()
            
            await self.auth_manager.shutdown()
            await self.cache_manager.shutdown()
            
            logger.info("API Gateway shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during API Gateway shutdown: {e}")
    
    def _setup_middleware(self) -> None:
        """Setup middleware for the FastAPI app."""
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Gzip compression
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)
        
        # Rate limiting middleware will be added after initialization
    
    def _setup_routes(self) -> None:
        """Setup API routes."""
        
        # Health check endpoint
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            }
        
        # Metrics endpoint
        @self.app.get("/metrics")
        async def metrics():
            return {
                "requests_total": 0,  # TODO: Implement metrics collection
                "active_connections": 0,
                "cache_hit_rate": await self.cache_manager.get_hit_rate() if self.cache_manager else 0
            }
        
        # Codegen API proxy routes
        @self.app.api_route(
            "/api/codegen/{path:path}",
            methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
        )
        async def proxy_codegen_api(
            request: Request,
            path: str,
            credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
        ):
            return await self._proxy_request(
                request,
                f"{self.codegen_api_base_url}/{path}",
                RouteType.CODEGEN_API,
                credentials
            )
        
        # Visual Flow API routes
        @self.app.api_route(
            "/api/visual-flow/{path:path}",
            methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
        )
        async def visual_flow_api(
            request: Request,
            path: str,
            credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
        ):
            return await self._handle_visual_flow_request(request, path, credentials)
        
        # WebSocket proxy
        @self.app.websocket("/ws/{path:path}")
        async def websocket_proxy(websocket: WebSocket, path: str):
            await self._handle_websocket(websocket, path)
    
    async def _proxy_request(
        self,
        request: Request,
        target_url: str,
        route_type: RouteType,
        credentials: HTTPAuthorizationCredentials
    ) -> Response:
        """Proxy request to target URL."""
        try:
            # Authenticate request
            user_info = await self.auth_manager.verify_token(credentials.credentials)
            if not user_info:
                raise HTTPException(status_code=401, detail="Invalid authentication")
            
            # Check cache first
            cache_key = f"{request.method}:{target_url}:{hash(str(request.query_params))}"
            cached_response = await self.cache_manager.get(cache_key)
            
            if cached_response and request.method == "GET":
                return JSONResponse(content=cached_response)
            
            # Get request body
            body = await request.body()
            
            # Transform request if needed
            if body and route_type == RouteType.CODEGEN_API:
                try:
                    request_data = json.loads(body)
                    request_data = self.request_transformer.transform_codegen_request(request_data)
                    body = json.dumps(request_data).encode()
                except json.JSONDecodeError:
                    pass  # Keep original body if not JSON
            
            # Prepare headers
            headers = dict(request.headers)
            headers["Authorization"] = f"Bearer {credentials.credentials}"
            
            # Remove hop-by-hop headers
            hop_by_hop_headers = [
                "connection", "keep-alive", "proxy-authenticate",
                "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade"
            ]
            for header in hop_by_hop_headers:
                headers.pop(header, None)
            
            # Make request to target
            async with self.http_client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=request.query_params,
                data=body
            ) as response:
                response_data = await response.json()
                
                # Transform response if needed
                if route_type == RouteType.CODEGEN_API:
                    response_data = self.response_transformer.transform_codegen_response(response_data)
                
                # Add metadata
                response_data = self.response_transformer.enhance_with_metadata(
                    response_data,
                    {
                        "route_type": route_type.value,
                        "user_id": user_info.get("user_id"),
                        "cached": False
                    }
                )
                
                # Cache GET responses
                if request.method == "GET" and response.status == 200:
                    await self.cache_manager.set(cache_key, response_data, ttl=300)  # 5 minutes
                
                # Publish API usage event
                await self._publish_api_event(request, user_info, response.status)
                
                return JSONResponse(
                    content=response_data,
                    status_code=response.status,
                    headers=dict(response.headers)
                )
        
        except aiohttp.ClientError as e:
            logger.error(f"Proxy request failed: {e}")
            raise HTTPException(status_code=502, detail="Bad Gateway")
        
        except Exception as e:
            logger.error(f"Unexpected error in proxy request: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
    
    async def _handle_visual_flow_request(
        self,
        request: Request,
        path: str,
        credentials: HTTPAuthorizationCredentials
    ) -> Response:
        """Handle Visual Flow API requests."""
        try:
            # Authenticate request
            user_info = await self.auth_manager.verify_token(credentials.credentials)
            if not user_info:
                raise HTTPException(status_code=401, detail="Invalid authentication")
            
            # Route to appropriate handler based on path
            if path.startswith("workflows"):
                return await self._handle_workflow_request(request, path, user_info)
            elif path.startswith("agents"):
                return await self._handle_agent_request(request, path, user_info)
            elif path.startswith("traces"):
                return await self._handle_trace_request(request, path, user_info)
            elif path.startswith("chat"):
                return await self._handle_chat_request(request, path, user_info)
            else:
                raise HTTPException(status_code=404, detail="Endpoint not found")
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error handling visual flow request: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
    
    async def _handle_websocket(self, websocket: WebSocket, path: str) -> None:
        """Handle WebSocket connections."""
        await websocket.accept()
        
        try:
            # TODO: Implement WebSocket authentication
            # TODO: Route WebSocket messages based on path
            # TODO: Integrate with event system for real-time updates
            
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Echo for now (implement proper handling)
                await websocket.send_text(json.dumps({
                    "type": "echo",
                    "data": message,
                    "timestamp": datetime.utcnow().isoformat()
                }))
        
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            await websocket.close()
    
    async def _handle_workflow_request(
        self,
        request: Request,
        path: str,
        user_info: Dict[str, Any]
    ) -> Response:
        """Handle workflow-related requests."""
        # TODO: Implement workflow management endpoints
        return JSONResponse(content={"message": "Workflow endpoint - TODO"})
    
    async def _handle_agent_request(
        self,
        request: Request,
        path: str,
        user_info: Dict[str, Any]
    ) -> Response:
        """Handle agent-related requests."""
        # TODO: Implement agent management endpoints
        return JSONResponse(content={"message": "Agent endpoint - TODO"})
    
    async def _handle_trace_request(
        self,
        request: Request,
        path: str,
        user_info: Dict[str, Any]
    ) -> Response:
        """Handle trace analysis requests."""
        # TODO: Implement trace analysis endpoints
        return JSONResponse(content={"message": "Trace endpoint - TODO"})
    
    async def _handle_chat_request(
        self,
        request: Request,
        path: str,
        user_info: Dict[str, Any]
    ) -> Response:
        """Handle AI chat requests."""
        # TODO: Implement AI chat endpoints
        return JSONResponse(content={"message": "Chat endpoint - TODO"})
    
    async def _publish_api_event(
        self,
        request: Request,
        user_info: Dict[str, Any],
        status_code: int
    ) -> None:
        """Publish API usage event."""
        event = Event(
            type=EventType.USER_ACTION,
            source="api_gateway",
            data={
                "method": request.method,
                "path": str(request.url.path),
                "status_code": status_code,
                "user_id": user_info.get("user_id"),
                "organization_id": user_info.get("organization_id")
            },
            user_id=user_info.get("user_id"),
            organization_id=user_info.get("organization_id")
        )
        await event_system.publish(event)
    
    def add_rate_limit_middleware(self) -> None:
        """Add rate limiting middleware after initialization."""
        if self.rate_limiter:
            self.app.add_middleware(RateLimitMiddleware, rate_limiter=self.rate_limiter)


# Global API gateway instance
api_gateway = APIGateway()
