"""
Intelligent Proxy Rotation Manager

This module provides intelligent proxy rotation for Z.AI and other services
that require proxy support, with health monitoring, load balancing, and
automatic failover capabilities.
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import random
import time

from codegen.orchestration.config.unified_config import UnifiedConfig

logger = logging.getLogger(__name__)

class ProxyStatus(Enum):
    """Proxy status enumeration."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    TESTING = "testing"
    DISABLED = "disabled"

class RotationStrategy(Enum):
    """Proxy rotation strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_USED = "least_used"
    FASTEST_RESPONSE = "fastest_response"
    RANDOM = "random"
    WEIGHTED = "weighted"

@dataclass
class ProxyInfo:
    """Proxy information and metrics."""
    proxy_id: str
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"  # http, https, socks5
    
    # Status and metrics
    status: ProxyStatus = ProxyStatus.HEALTHY
    last_used: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    
    # Performance metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    current_connections: int = 0
    max_connections: int = 10
    
    # Health metrics
    consecutive_failures: int = 0
    max_consecutive_failures: int = 5
    health_check_failures: int = 0
    
    # Weight for weighted rotation
    weight: float = 1.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def is_available(self) -> bool:
        """Check if proxy is available for use."""
        return (
            self.status == ProxyStatus.HEALTHY and
            self.current_connections < self.max_connections and
            self.consecutive_failures < self.max_consecutive_failures
        )
    
    @property
    def proxy_url(self) -> str:
        """Get proxy URL."""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    def record_request(self, success: bool, response_time: float) -> None:
        """Record a request for metrics tracking."""
        self.total_requests += 1
        self.last_used = datetime.utcnow()
        
        if success:
            self.successful_requests += 1
            self.consecutive_failures = 0
        else:
            self.failed_requests += 1
            self.consecutive_failures += 1
        
        # Update average response time (exponential moving average)
        alpha = 0.1  # Smoothing factor
        self.average_response_time = (
            alpha * response_time + (1 - alpha) * self.average_response_time
        )

class IntelligentProxyManager:
    """
    Intelligent Proxy Rotation Manager.
    
    This manager provides:
    - Multiple rotation strategies
    - Health monitoring and automatic failover
    - Load balancing across proxy pool
    - Performance metrics and optimization
    - Automatic proxy discovery and validation
    """
    
    def __init__(self, config: UnifiedConfig):
        """Initialize proxy manager."""
        self.config = config
        self._initialized = False
        
        # Configuration
        proxy_config = config.get_proxy_config()
        self.pool_size = proxy_config.pool_size
        self.health_check_interval = proxy_config.health_check_interval
        self.rotation_strategy = RotationStrategy(proxy_config.rotation_strategy)
        self.proxy_configs = proxy_config.proxies
        
        # Proxy pool
        self._proxy_pool: Dict[str, ProxyInfo] = {}
        self._rotation_index = 0
        
        # Health checking
        self._health_check_session: Optional[aiohttp.ClientSession] = None
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        # Metrics
        self.total_proxy_requests = 0
        self.total_proxy_failures = 0
        self.pool_health_score = 100.0
        
        logger.info("IntelligentProxyManager initialized")
    
    async def initialize(self) -> None:
        """Initialize proxy manager."""
        if self._initialized:
            return
        
        logger.info("Initializing intelligent proxy manager...")
        
        # Create health check session
        self._health_check_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            connector=aiohttp.TCPConnector(limit=20)
        )
        
        # Load proxy configurations
        await self._load_proxy_configurations()
        
        # Perform initial health checks
        await self._perform_initial_health_checks()
        
        # Start background tasks
        await self._start_background_tasks()
        
        self._initialized = True
        logger.info(f"Proxy manager initialized with {len(self._proxy_pool)} proxies")
    
    async def shutdown(self) -> None:
        """Shutdown proxy manager."""
        logger.info("Shutting down proxy manager...")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel background tasks
        if self._background_tasks:
            for task in self._background_tasks:
                task.cancel()
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Close health check session
        if self._health_check_session:
            await self._health_check_session.close()
        
        self._initialized = False
        logger.info("Proxy manager shutdown complete")
    
    async def get_proxy(self, exclude_proxies: Optional[List[str]] = None) -> Optional[ProxyInfo]:
        """
        Get a proxy using the configured rotation strategy.
        
        Args:
            exclude_proxies: List of proxy IDs to exclude
            
        Returns:
            ProxyInfo if available, None if no proxies available
        """
        if not self._initialized:
            await self.initialize()
        
        # Get available proxies
        available_proxies = [
            proxy for proxy in self._proxy_pool.values()
            if proxy.is_available and (not exclude_proxies or proxy.proxy_id not in exclude_proxies)
        ]
        
        if not available_proxies:
            logger.warning("No available proxies in pool")
            return None
        
        # Select proxy based on strategy
        selected_proxy = self._select_proxy_by_strategy(available_proxies)
        
        if selected_proxy:
            selected_proxy.current_connections += 1
            self.total_proxy_requests += 1
            logger.debug(f"Selected proxy: {selected_proxy.proxy_id}")
        
        return selected_proxy
    
    async def release_proxy(self, proxy: ProxyInfo, success: bool, response_time: float) -> None:
        """
        Release a proxy and record metrics.
        
        Args:
            proxy: Proxy to release
            success: Whether the request was successful
            response_time: Response time in seconds
        """
        proxy.current_connections = max(0, proxy.current_connections - 1)
        proxy.record_request(success, response_time)
        
        if not success:
            self.total_proxy_failures += 1
            
            # Disable proxy if too many consecutive failures
            if proxy.consecutive_failures >= proxy.max_consecutive_failures:
                proxy.status = ProxyStatus.UNHEALTHY
                logger.warning(f"Proxy {proxy.proxy_id} marked as unhealthy due to consecutive failures")
        
        logger.debug(f"Released proxy: {proxy.proxy_id} (success: {success})")
    
    async def add_proxy(self, proxy_config: Dict[str, Any]) -> str:
        """
        Add a new proxy to the pool.
        
        Args:
            proxy_config: Proxy configuration
            
        Returns:
            Proxy ID
        """
        proxy_info = ProxyInfo(
            proxy_id=f"proxy_{len(self._proxy_pool) + 1}",
            host=proxy_config["host"],
            port=proxy_config["port"],
            username=proxy_config.get("username"),
            password=proxy_config.get("password"),
            protocol=proxy_config.get("protocol", "http"),
            max_connections=proxy_config.get("max_connections", 10),
            weight=proxy_config.get("weight", 1.0)
        )
        
        # Test proxy health
        if await self._test_proxy_health(proxy_info):
            self._proxy_pool[proxy_info.proxy_id] = proxy_info
            logger.info(f"Added proxy: {proxy_info.proxy_id}")
            return proxy_info.proxy_id
        else:
            logger.warning(f"Failed to add proxy {proxy_info.host}:{proxy_info.port} - health check failed")
            raise ValueError("Proxy health check failed")
    
    async def remove_proxy(self, proxy_id: str) -> bool:
        """
        Remove a proxy from the pool.
        
        Args:
            proxy_id: Proxy ID to remove
            
        Returns:
            True if removed successfully, False if not found
        """
        if proxy_id in self._proxy_pool:
            del self._proxy_pool[proxy_id]
            logger.info(f"Removed proxy: {proxy_id}")
            return True
        return False
    
    async def get_pool_status(self) -> Dict[str, Any]:
        """Get comprehensive pool status."""
        healthy_proxies = len([p for p in self._proxy_pool.values() if p.status == ProxyStatus.HEALTHY])
        available_proxies = len([p for p in self._proxy_pool.values() if p.is_available])
        
        # Calculate pool health score
        if self._proxy_pool:
            total_success_rate = sum(p.success_rate for p in self._proxy_pool.values())
            self.pool_health_score = total_success_rate / len(self._proxy_pool)
        
        return {
            "total_proxies": len(self._proxy_pool),
            "healthy_proxies": healthy_proxies,
            "available_proxies": available_proxies,
            "pool_health_score": self.pool_health_score,
            "rotation_strategy": self.rotation_strategy.value,
            "total_requests": self.total_proxy_requests,
            "total_failures": self.total_proxy_failures,
            "failure_rate": (self.total_proxy_failures / max(self.total_proxy_requests, 1)) * 100,
            "proxy_details": [
                {
                    "proxy_id": proxy.proxy_id,
                    "host": proxy.host,
                    "port": proxy.port,
                    "status": proxy.status.value,
                    "success_rate": proxy.success_rate,
                    "average_response_time": proxy.average_response_time,
                    "current_connections": proxy.current_connections,
                    "total_requests": proxy.total_requests
                }
                for proxy in self._proxy_pool.values()
            ]
        }
    
    async def health_check_all_proxies(self) -> Dict[str, bool]:
        """Perform health check on all proxies."""
        results = {}
        
        for proxy_id, proxy in self._proxy_pool.items():
            is_healthy = await self._test_proxy_health(proxy)
            results[proxy_id] = is_healthy
            
            if is_healthy:
                proxy.status = ProxyStatus.HEALTHY
                proxy.health_check_failures = 0
            else:
                proxy.health_check_failures += 1
                if proxy.health_check_failures >= 3:
                    proxy.status = ProxyStatus.UNHEALTHY
        
        return results
    
    # Private methods
    
    async def _load_proxy_configurations(self) -> None:
        """Load proxy configurations from config."""
        for i, proxy_config in enumerate(self.proxy_configs):
            try:
                proxy_info = ProxyInfo(
                    proxy_id=f"proxy_{i + 1}",
                    host=proxy_config["host"],
                    port=proxy_config["port"],
                    username=proxy_config.get("username"),
                    password=proxy_config.get("password"),
                    protocol=proxy_config.get("protocol", "http"),
                    max_connections=proxy_config.get("max_connections", 10),
                    weight=proxy_config.get("weight", 1.0)
                )
                
                self._proxy_pool[proxy_info.proxy_id] = proxy_info
                
            except Exception as e:
                logger.error(f"Failed to load proxy config {i}: {e}")
    
    async def _perform_initial_health_checks(self) -> None:
        """Perform initial health checks on all proxies."""
        logger.info("Performing initial proxy health checks...")
        
        health_results = await self.health_check_all_proxies()
        healthy_count = sum(1 for is_healthy in health_results.values() if is_healthy)
        
        logger.info(f"Initial health check complete: {healthy_count}/{len(self._proxy_pool)} proxies healthy")
    
    def _select_proxy_by_strategy(self, available_proxies: List[ProxyInfo]) -> Optional[ProxyInfo]:
        """Select proxy based on rotation strategy."""
        if not available_proxies:
            return None
        
        if self.rotation_strategy == RotationStrategy.ROUND_ROBIN:
            selected = available_proxies[self._rotation_index % len(available_proxies)]
            self._rotation_index += 1
            return selected
        
        elif self.rotation_strategy == RotationStrategy.LEAST_USED:
            return min(available_proxies, key=lambda p: p.current_connections)
        
        elif self.rotation_strategy == RotationStrategy.FASTEST_RESPONSE:
            # Filter out proxies with no recorded response time
            proxies_with_times = [p for p in available_proxies if p.average_response_time > 0]
            if proxies_with_times:
                return min(proxies_with_times, key=lambda p: p.average_response_time)
            return available_proxies[0]  # Fallback
        
        elif self.rotation_strategy == RotationStrategy.RANDOM:
            return random.choice(available_proxies)
        
        elif self.rotation_strategy == RotationStrategy.WEIGHTED:
            # Weighted random selection
            total_weight = sum(p.weight for p in available_proxies)
            if total_weight == 0:
                return random.choice(available_proxies)
            
            random_weight = random.uniform(0, total_weight)
            current_weight = 0
            
            for proxy in available_proxies:
                current_weight += proxy.weight
                if current_weight >= random_weight:
                    return proxy
            
            return available_proxies[-1]  # Fallback
        
        # Default fallback
        return available_proxies[0]
    
    async def _test_proxy_health(self, proxy: ProxyInfo) -> bool:
        """Test proxy health by making a test request."""
        try:
            proxy.status = ProxyStatus.TESTING
            proxy.last_health_check = datetime.utcnow()
            
            # Test URL - use a reliable service
            test_url = "http://httpbin.org/ip"
            
            # Configure proxy for test request
            connector = aiohttp.TCPConnector()
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                
                start_time = time.time()
                
                async with session.get(
                    test_url,
                    proxy=proxy.proxy_url
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        # Update response time if this is a real test
                        if proxy.average_response_time == 0:
                            proxy.average_response_time = response_time
                        else:
                            alpha = 0.1
                            proxy.average_response_time = (
                                alpha * response_time + (1 - alpha) * proxy.average_response_time
                            )
                        
                        return True
                    else:
                        logger.warning(f"Proxy {proxy.proxy_id} health check failed: HTTP {response.status}")
                        return False
        
        except Exception as e:
            logger.warning(f"Proxy {proxy.proxy_id} health check failed: {e}")
            return False
        
        finally:
            if proxy.status == ProxyStatus.TESTING:
                proxy.status = ProxyStatus.UNHEALTHY  # Will be set to healthy if test passed
    
    async def _start_background_tasks(self) -> None:
        """Start background monitoring tasks."""
        # Health monitoring task
        self._background_tasks.append(
            asyncio.create_task(self._health_monitoring_loop())
        )
        
        # Pool optimization task
        self._background_tasks.append(
            asyncio.create_task(self._pool_optimization_loop())
        )
    
    async def _health_monitoring_loop(self) -> None:
        """Background task for continuous health monitoring."""
        while not self._shutdown_event.is_set():
            try:
                await self.health_check_all_proxies()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def _pool_optimization_loop(self) -> None:
        """Background task for pool optimization."""
        while not self._shutdown_event.is_set():
            try:
                # Reset connection counts periodically to prevent stale data
                for proxy in self._proxy_pool.values():
                    if proxy.current_connections > 0:
                        proxy.current_connections = max(0, proxy.current_connections - 1)
                
                # Re-enable proxies that have been unhealthy for a while
                cutoff_time = datetime.utcnow() - timedelta(minutes=10)
                for proxy in self._proxy_pool.values():
                    if (proxy.status == ProxyStatus.UNHEALTHY and
                        proxy.last_health_check and
                        proxy.last_health_check < cutoff_time):
                        
                        # Reset failure count and test again
                        proxy.consecutive_failures = 0
                        proxy.health_check_failures = 0
                        
                        if await self._test_proxy_health(proxy):
                            proxy.status = ProxyStatus.HEALTHY
                            logger.info(f"Re-enabled proxy: {proxy.proxy_id}")
                
                await asyncio.sleep(300)  # Optimize every 5 minutes
            except Exception as e:
                logger.error(f"Pool optimization error: {e}")
                await asyncio.sleep(300)

