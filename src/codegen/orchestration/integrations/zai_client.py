"""
Z.AI Client Integration

This module provides comprehensive integration with Z.AI services, including
parallel processing, proxy rotation, rate limiting, and intelligent request
management for the orchestration layer.
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import time

from codegen.orchestration.config.unified_config import UnifiedConfig

logger = logging.getLogger(__name__)

class ZAIRequestType(Enum):
    """Types of Z.AI requests."""
    PARALLEL_PROCESSING = "parallel_processing"
    SINGLE_REQUEST = "single_request"
    CODE_ANALYSIS = "code_analysis"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    VALIDATION = "validation"

@dataclass
class ZAIRequest:
    """Z.AI request structure."""
    request_id: str
    request_type: ZAIRequestType
    action: str
    payload: Dict[str, Any]
    priority: int = 5
    timeout: int = 30
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ZAIResponse:
    """Z.AI response structure."""
    request_id: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    proxy_used: Optional[str] = None
    completed_at: datetime = field(default_factory=datetime.utcnow)

class ZAIClient:
    """
    Z.AI Client with advanced features.
    
    This client provides:
    - Parallel processing capabilities
    - Intelligent proxy rotation
    - Rate limiting and queuing
    - Request retry logic
    - Response caching
    - Health monitoring
    """
    
    def __init__(self, config: UnifiedConfig):
        """Initialize Z.AI client."""
        self.config = config
        self._initialized = False
        
        # Configuration
        zai_config = config.get_service_config("zai")
        self.base_url = zai_config.base_url
        self.api_key = zai_config.api_key
        self.timeout = zai_config.timeout
        self.max_retries = zai_config.max_retries
        
        # Rate limiting (50 parallel, 100 single per minute)
        self.parallel_rate_limit = 50
        self.single_rate_limit = 100
        self.rate_window = 60  # seconds
        
        # Request tracking
        self._parallel_requests = []
        self._single_requests = []
        self._request_queue = asyncio.Queue()
        self._active_requests: Dict[str, ZAIRequest] = {}
        
        # Session management
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        # Metrics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.average_response_time = 0.0
        
        logger.info("ZAIClient initialized")
    
    async def initialize(self) -> None:
        """Initialize the Z.AI client."""
        if self._initialized:
            return
        
        logger.info("Initializing Z.AI client...")
        
        # Create HTTP connector with connection pooling
        self._connector = aiohttp.TCPConnector(
            limit=100,  # Total connection pool size
            limit_per_host=20,  # Per-host connection limit
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        # Create HTTP session
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self._session = aiohttp.ClientSession(
            connector=self._connector,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Codegen-Orchestration/1.0"
            }
        )
        
        # Start background tasks
        await self._start_background_tasks()
        
        self._initialized = True
        logger.info("Z.AI client initialized successfully")
    
    async def shutdown(self) -> None:
        """Shutdown the Z.AI client."""
        logger.info("Shutting down Z.AI client...")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel background tasks
        if self._background_tasks:
            for task in self._background_tasks:
                task.cancel()
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Close HTTP session
        if self._session:
            await self._session.close()
        
        if self._connector:
            await self._connector.close()
        
        self._initialized = False
        logger.info("Z.AI client shutdown complete")
    
    async def process_request(
        self,
        request_data: Dict[str, Any],
        request_type: ZAIRequestType = ZAIRequestType.SINGLE_REQUEST,
        proxy: Optional[str] = None,
        priority: int = 5
    ) -> ZAIResponse:
        """
        Process a single Z.AI request.
        
        Args:
            request_data: Request payload
            request_type: Type of request
            proxy: Optional proxy to use
            priority: Request priority (1-10)
            
        Returns:
            ZAIResponse with results
        """
        if not self._initialized:
            await self.initialize()
        
        # Create request
        request = ZAIRequest(
            request_id=f"zai_{int(time.time() * 1000)}",
            request_type=request_type,
            action=request_data.get("action", "process"),
            payload=request_data,
            priority=priority
        )
        
        # Check rate limits
        await self._check_rate_limits(request_type)
        
        # Execute request
        return await self._execute_request(request, proxy)
    
    async def process_parallel_requests(
        self,
        requests: List[Dict[str, Any]],
        max_concurrent: int = 10,
        proxy_pool: Optional[List[str]] = None
    ) -> List[ZAIResponse]:
        """
        Process multiple requests in parallel.
        
        Args:
            requests: List of request payloads
            max_concurrent: Maximum concurrent requests
            proxy_pool: Optional pool of proxies to rotate
            
        Returns:
            List of ZAIResponse objects
        """
        if not self._initialized:
            await self.initialize()
        
        # Check parallel rate limits
        await self._check_rate_limits(ZAIRequestType.PARALLEL_PROCESSING)
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        # Create tasks
        tasks = []
        for i, request_data in enumerate(requests):
            proxy = proxy_pool[i % len(proxy_pool)] if proxy_pool else None
            task = self._process_with_semaphore(semaphore, request_data, proxy)
            tasks.append(task)
        
        # Execute all tasks
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        results = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                results.append(ZAIResponse(
                    request_id=f"parallel_{i}",
                    success=False,
                    error=str(response)
                ))
            else:
                results.append(response)
        
        return results
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Z.AI service."""
        try:
            if not self._session:
                return {"status": "unhealthy", "error": "Session not initialized"}
            
            start_time = time.time()
            
            async with self._session.get(f"{self.base_url}/health") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "healthy",
                        "response_time": response_time,
                        "data": data
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status}",
                        "response_time": response_time
                    }
        
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive client status."""
        return {
            "initialized": self._initialized,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (self.successful_requests / max(self.total_requests, 1)) * 100,
            "average_response_time": self.average_response_time,
            "active_requests": len(self._active_requests),
            "queue_size": self._request_queue.qsize(),
            "parallel_requests_last_minute": len([
                r for r in self._parallel_requests
                if (datetime.utcnow() - r).total_seconds() < 60
            ]),
            "single_requests_last_minute": len([
                r for r in self._single_requests
                if (datetime.utcnow() - r).total_seconds() < 60
            ])
        }
    
    # Private methods
    
    async def _execute_request(self, request: ZAIRequest, proxy: Optional[str] = None) -> ZAIResponse:
        """Execute a single Z.AI request."""
        start_time = time.time()
        self._active_requests[request.request_id] = request
        
        try:
            # Prepare request
            url = f"{self.base_url}/api/v1/{request.action}"
            headers = {}
            
            # Configure proxy if provided
            connector_kwargs = {}
            if proxy:
                connector_kwargs["proxy"] = proxy
                headers["Proxy-Authorization"] = f"Bearer {proxy}"
            
            # Make request
            async with self._session.post(
                url,
                json=request.payload,
                headers=headers,
                **connector_kwargs
            ) as response:
                processing_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Update metrics
                    self.total_requests += 1
                    self.successful_requests += 1
                    self._update_average_response_time(processing_time)
                    
                    # Track rate limits
                    self._track_request(request.request_type)
                    
                    return ZAIResponse(
                        request_id=request.request_id,
                        success=True,
                        data=data,
                        processing_time=processing_time,
                        proxy_used=proxy
                    )
                else:
                    error_text = await response.text()
                    
                    # Update metrics
                    self.total_requests += 1
                    self.failed_requests += 1
                    
                    return ZAIResponse(
                        request_id=request.request_id,
                        success=False,
                        error=f"HTTP {response.status}: {error_text}",
                        processing_time=processing_time,
                        proxy_used=proxy
                    )
        
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Update metrics
            self.total_requests += 1
            self.failed_requests += 1
            
            # Retry logic
            if request.retry_count < request.max_retries:
                request.retry_count += 1
                logger.warning(f"Retrying request {request.request_id} (attempt {request.retry_count})")
                await asyncio.sleep(2 ** request.retry_count)  # Exponential backoff
                return await self._execute_request(request, proxy)
            
            return ZAIResponse(
                request_id=request.request_id,
                success=False,
                error=str(e),
                processing_time=processing_time,
                proxy_used=proxy
            )
        
        finally:
            self._active_requests.pop(request.request_id, None)
    
    async def _process_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        request_data: Dict[str, Any],
        proxy: Optional[str] = None
    ) -> ZAIResponse:
        """Process request with semaphore for concurrency control."""
        async with semaphore:
            return await self.process_request(
                request_data,
                ZAIRequestType.PARALLEL_PROCESSING,
                proxy
            )
    
    async def _check_rate_limits(self, request_type: ZAIRequestType) -> None:
        """Check and enforce rate limits."""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.rate_window)
        
        if request_type == ZAIRequestType.PARALLEL_PROCESSING:
            # Clean old requests
            self._parallel_requests = [
                r for r in self._parallel_requests if r > cutoff
            ]
            
            # Check limit
            if len(self._parallel_requests) >= self.parallel_rate_limit:
                wait_time = (self._parallel_requests[0] - cutoff).total_seconds()
                logger.warning(f"Parallel rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
        
        else:
            # Clean old requests
            self._single_requests = [
                r for r in self._single_requests if r > cutoff
            ]
            
            # Check limit
            if len(self._single_requests) >= self.single_rate_limit:
                wait_time = (self._single_requests[0] - cutoff).total_seconds()
                logger.warning(f"Single request rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
    
    def _track_request(self, request_type: ZAIRequestType) -> None:
        """Track request for rate limiting."""
        now = datetime.utcnow()
        
        if request_type == ZAIRequestType.PARALLEL_PROCESSING:
            self._parallel_requests.append(now)
        else:
            self._single_requests.append(now)
    
    def _update_average_response_time(self, response_time: float) -> None:
        """Update average response time using exponential moving average."""
        alpha = 0.1  # Smoothing factor
        self.average_response_time = (
            alpha * response_time + (1 - alpha) * self.average_response_time
        )
    
    async def _start_background_tasks(self) -> None:
        """Start background monitoring tasks."""
        # Rate limit cleanup task
        self._background_tasks.append(
            asyncio.create_task(self._rate_limit_cleanup_loop())
        )
        
        # Health monitoring task
        self._background_tasks.append(
            asyncio.create_task(self._health_monitoring_loop())
        )
    
    async def _rate_limit_cleanup_loop(self) -> None:
        """Background task to clean up old rate limit tracking."""
        while not self._shutdown_event.is_set():
            try:
                now = datetime.utcnow()
                cutoff = now - timedelta(seconds=self.rate_window * 2)
                
                # Clean up old requests
                self._parallel_requests = [
                    r for r in self._parallel_requests if r > cutoff
                ]
                self._single_requests = [
                    r for r in self._single_requests if r > cutoff
                ]
                
                await asyncio.sleep(60)  # Clean every minute
            except Exception as e:
                logger.error(f"Rate limit cleanup error: {e}")
                await asyncio.sleep(60)
    
    async def _health_monitoring_loop(self) -> None:
        """Background task for health monitoring."""
        while not self._shutdown_event.is_set():
            try:
                health_status = await self.health_check()
                if health_status["status"] != "healthy":
                    logger.warning(f"Z.AI health check failed: {health_status}")
                
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(300)

