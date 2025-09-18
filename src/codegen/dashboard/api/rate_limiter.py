"""Rate limiter for API requests with Redis backend."""

import time
import asyncio
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import hashlib

from codegen.dashboard.config.api_endpoints import DashboardAPIEndpoints, RateLimit
from codegen.dashboard.cache.redis_client import get_redis_client, RedisClient
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter with Redis backend for API request throttling."""
    
    def __init__(self, redis_client: Optional[RedisClient] = None, key_prefix: str = "codegen:rate_limit"):
        """Initialize rate limiter.
        
        Args:
            redis_client: Redis client instance (defaults to global client)
            key_prefix: Prefix for Redis keys
        """
        self.redis_client = redis_client or get_redis_client()
        self.key_prefix = key_prefix
        
        # Rate limit configurations
        self.rate_limits = {
            RateLimit.STANDARD: {"requests": 60, "window": 30},  # 60 requests per 30 seconds
            RateLimit.AGENT_CREATION: {"requests": 10, "window": 60},  # 10 requests per minute
            RateLimit.SETUP_COMMANDS: {"requests": 5, "window": 60},  # 5 requests per minute
            RateLimit.LOG_ANALYSIS: {"requests": 5, "window": 60},  # 5 requests per minute
        }
        
        logger.info("Rate limiter initialized", extra={"key_prefix": key_prefix})
    
    def _get_rate_limit_key(self, endpoint_name: str, token: str) -> str:
        """Generate Redis key for rate limiting."""
        token_hash = hashlib.md5(token.encode()).hexdigest()[:8]
        return f"{self.key_prefix}:{endpoint_name}:{token_hash}"
    
    def _get_rate_limit_config(self, endpoint_name: str) -> Dict[str, int]:
        """Get rate limit configuration for an endpoint."""
        endpoints = DashboardAPIEndpoints.get_all_endpoints()
        if endpoint_name not in endpoints:
            # Default to standard rate limit for unknown endpoints
            return self.rate_limits[RateLimit.STANDARD]
        
        config = endpoints[endpoint_name]
        return self.rate_limits[config.rate_limit]
    
    async def check_rate_limit(self, endpoint_name: str, token: str) -> bool:
        """Check if request is within rate limits.
        
        Args:
            endpoint_name: Name of the API endpoint
            token: User authentication token
            
        Returns:
            True if request is allowed, False if rate limited
        """
        try:
            rate_config = self._get_rate_limit_config(endpoint_name)
            key = self._get_rate_limit_key(endpoint_name, token)
            
            # Use sliding window rate limiting with Redis
            current_time = int(time.time())
            window_start = current_time - rate_config["window"]
            
            # Remove old entries outside the window
            await self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in the window
            current_count = await self.redis_client.zcard(key)
            
            if current_count >= rate_config["requests"]:
                logger.warning("Rate limit exceeded", extra={
                    "endpoint": endpoint_name,
                    "current_count": current_count,
                    "limit": rate_config["requests"],
                    "window": rate_config["window"]
                })
                return False
            
            # Add current request to the window
            await self.redis_client.zadd(key, {str(current_time): current_time})
            
            # Set expiration for the key
            await self.redis_client.expire(key, rate_config["window"] + 10)
            
            logger.debug("Rate limit check passed", extra={
                "endpoint": endpoint_name,
                "current_count": current_count + 1,
                "limit": rate_config["requests"]
            })
            
            return True
            
        except Exception as e:
            logger.error("Rate limit check failed", extra={
                "endpoint": endpoint_name,
                "error": str(e)
            })
            # Fail open - allow request if rate limiting fails
            return True
    
    async def get_status(self, endpoint_name: str, token: str) -> Dict:
        """Get current rate limit status for an endpoint.
        
        Args:
            endpoint_name: Name of the API endpoint
            token: User authentication token
            
        Returns:
            Dictionary with rate limit status information
        """
        try:
            rate_config = self._get_rate_limit_config(endpoint_name)
            key = self._get_rate_limit_key(endpoint_name, token)
            
            current_time = int(time.time())
            window_start = current_time - rate_config["window"]
            
            # Remove old entries and count current requests
            await self.redis_client.zremrangebyscore(key, 0, window_start)
            current_count = await self.redis_client.zcard(key)
            
            # Get the oldest request in the current window
            oldest_requests = await self.redis_client.zrange(key, 0, 0, withscores=True)
            reset_time = None
            if oldest_requests:
                oldest_timestamp = int(oldest_requests[0][1])
                reset_time = oldest_timestamp + rate_config["window"]
            
            return {
                "endpoint": endpoint_name,
                "limit": rate_config["requests"],
                "window_seconds": rate_config["window"],
                "current_count": current_count,
                "remaining": max(0, rate_config["requests"] - current_count),
                "reset_time": reset_time,
                "reset_in_seconds": max(0, reset_time - current_time) if reset_time else 0
            }
            
        except Exception as e:
            logger.error("Failed to get rate limit status", extra={
                "endpoint": endpoint_name,
                "error": str(e)
            })
            return {
                "endpoint": endpoint_name,
                "error": str(e)
            }
    
    async def reset_limits(self, token: str, endpoint_name: Optional[str] = None) -> bool:
        """Reset rate limits for a token.
        
        Args:
            token: User authentication token
            endpoint_name: Specific endpoint to reset (None for all endpoints)
            
        Returns:
            True if reset was successful
        """
        try:
            if endpoint_name:
                # Reset specific endpoint
                key = self._get_rate_limit_key(endpoint_name, token)
                await self.redis_client.delete(key)
                logger.info("Rate limit reset for endpoint", extra={
                    "endpoint": endpoint_name
                })
            else:
                # Reset all endpoints for the token
                token_hash = hashlib.md5(token.encode()).hexdigest()[:8]
                pattern = f"{self.key_prefix}:*:{token_hash}"
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
                logger.info("Rate limits reset for all endpoints", extra={
                    "keys_deleted": len(keys)
                })
            
            return True
            
        except Exception as e:
            logger.error("Failed to reset rate limits", extra={
                "endpoint": endpoint_name,
                "error": str(e)
            })
            return False
    
    async def get_all_status(self, token: str) -> Dict[str, Dict]:
        """Get rate limit status for all endpoints.
        
        Args:
            token: User authentication token
            
        Returns:
            Dictionary mapping endpoint names to their status
        """
        endpoints = DashboardAPIEndpoints.get_all_endpoints()
        status_dict = {}
        
        for endpoint_name in endpoints.keys():
            status_dict[endpoint_name] = await self.get_status(endpoint_name, token)
        
        return status_dict
    
    async def health_check(self) -> bool:
        """Perform health check on rate limiter."""
        try:
            # Test Redis connectivity
            await self.redis_client.ping()
            
            # Test basic operations
            test_key = f"{self.key_prefix}:health_check"
            await self.redis_client.set(test_key, "test", ex=10)
            value = await self.redis_client.get(test_key)
            await self.redis_client.delete(test_key)
            
            return value == "test"
            
        except Exception as e:
            logger.error("Rate limiter health check failed", extra={"error": str(e)})
            return False
    
    async def get_statistics(self) -> Dict:
        """Get rate limiter statistics."""
        try:
            # Get all rate limit keys
            pattern = f"{self.key_prefix}:*"
            keys = await self.redis_client.keys(pattern)
            
            stats = {
                "total_keys": len(keys),
                "endpoints": {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Group by endpoint
            endpoint_counts = {}
            for key in keys:
                parts = key.split(":")
                if len(parts) >= 3:
                    endpoint = parts[2]
                    endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1
            
            stats["endpoints"] = endpoint_counts
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get rate limiter statistics", extra={"error": str(e)})
            return {"error": str(e)}
    
    async def cleanup_expired_keys(self) -> int:
        """Clean up expired rate limit keys."""
        try:
            pattern = f"{self.key_prefix}:*"
            keys = await self.redis_client.keys(pattern)
            
            deleted_count = 0
            current_time = int(time.time())
            
            for key in keys:
                # Check if key has any entries
                count = await self.redis_client.zcard(key)
                if count == 0:
                    await self.redis_client.delete(key)
                    deleted_count += 1
                else:
                    # Remove old entries
                    # Assume maximum window of 60 seconds for cleanup
                    window_start = current_time - 60
                    removed = await self.redis_client.zremrangebyscore(key, 0, window_start)
                    
                    # If no entries left after cleanup, delete the key
                    remaining = await self.redis_client.zcard(key)
                    if remaining == 0:
                        await self.redis_client.delete(key)
                        deleted_count += 1
            
            logger.info("Rate limiter cleanup completed", extra={
                "deleted_keys": deleted_count,
                "total_keys": len(keys)
            })
            
            return deleted_count
            
        except Exception as e:
            logger.error("Rate limiter cleanup failed", extra={"error": str(e)})
            return 0


# Utility functions for rate limiting
async def check_endpoint_rate_limit(endpoint_name: str, token: str, 
                                  rate_limiter: Optional[RateLimiter] = None) -> bool:
    """Check rate limit for a specific endpoint."""
    limiter = rate_limiter or RateLimiter()
    return await limiter.check_rate_limit(endpoint_name, token)


async def get_endpoint_rate_status(endpoint_name: str, token: str,
                                 rate_limiter: Optional[RateLimiter] = None) -> Dict:
    """Get rate limit status for a specific endpoint."""
    limiter = rate_limiter or RateLimiter()
    return await limiter.get_status(endpoint_name, token)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, endpoint: str, limit: int, window: int, reset_in: int):
        self.endpoint = endpoint
        self.limit = limit
        self.window = window
        self.reset_in = reset_in
        super().__init__(f"Rate limit exceeded for {endpoint}. Limit: {limit}/{window}s. Reset in: {reset_in}s")


async def enforce_rate_limit(endpoint_name: str, token: str, 
                           rate_limiter: Optional[RateLimiter] = None) -> None:
    """Enforce rate limit for an endpoint, raising exception if exceeded."""
    limiter = rate_limiter or RateLimiter()
    
    if not await limiter.check_rate_limit(endpoint_name, token):
        status = await limiter.get_status(endpoint_name, token)
        raise RateLimitExceeded(
            endpoint=endpoint_name,
            limit=status.get("limit", 0),
            window=status.get("window_seconds", 0),
            reset_in=status.get("reset_in_seconds", 0)
        )
