"""Redis client for dashboard caching operations."""

import os
import asyncio
from typing import Optional, Any, List, Dict, Union
import json

try:
    import redis.asyncio as redis
    from redis.asyncio import Redis
except ImportError:
    # Graceful fallback if redis is not installed
    redis = None
    Redis = None

from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Async Redis client for dashboard caching."""
    
    def __init__(self, url: Optional[str] = None, **kwargs):
        """Initialize Redis client.
        
        Args:
            url: Redis URL (defaults to REDIS_URL env var)
            **kwargs: Additional Redis connection parameters
        """
        if redis is None:
            raise ImportError("redis is required for caching operations. Install with: pip install redis")
        
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.connection_kwargs = kwargs
        
        # Parse connection parameters from URL or use defaults
        self.client: Optional[Redis] = None
        self._connected = False
        
        logger.info("Redis client initialized", extra={"url": self.url})
    
    async def connect(self) -> None:
        """Connect to Redis."""
        if self._connected:
            return
        
        try:
            self.client = redis.from_url(self.url, **self.connection_kwargs)
            await self.client.ping()
            self._connected = True
            logger.info("Redis client connected successfully")
        except Exception as e:
            logger.error("Failed to connect to Redis", extra={"error": str(e)})
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.client and self._connected:
            await self.client.close()
            self._connected = False
            logger.info("Redis client disconnected")
    
    async def _ensure_connected(self) -> None:
        """Ensure Redis connection is active."""
        if not self._connected:
            await self.connect()
    
    # Basic Operations
    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        await self._ensure_connected()
        try:
            value = await self.client.get(key)
            return value.decode('utf-8') if value else None
        except Exception as e:
            logger.error("Redis GET failed", extra={"key": key, "error": str(e)})
            return None
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set key-value pair with optional expiration."""
        await self._ensure_connected()
        try:
            result = await self.client.set(key, value, ex=ex)
            return bool(result)
        except Exception as e:
            logger.error("Redis SET failed", extra={"key": key, "error": str(e)})
            return False
    
    async def setex(self, key: str, time: int, value: str) -> bool:
        """Set key-value pair with expiration time."""
        await self._ensure_connected()
        try:
            result = await self.client.setex(key, time, value)
            return bool(result)
        except Exception as e:
            logger.error("Redis SETEX failed", extra={"key": key, "error": str(e)})
            return False
    
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        await self._ensure_connected()
        try:
            return await self.client.delete(*keys)
        except Exception as e:
            logger.error("Redis DELETE failed", extra={"keys": keys, "error": str(e)})
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        await self._ensure_connected()
        try:
            result = await self.client.exists(key)
            return bool(result)
        except Exception as e:
            logger.error("Redis EXISTS failed", extra={"key": key, "error": str(e)})
            return False
    
    async def expire(self, key: str, time: int) -> bool:
        """Set expiration time for key."""
        await self._ensure_connected()
        try:
            result = await self.client.expire(key, time)
            return bool(result)
        except Exception as e:
            logger.error("Redis EXPIRE failed", extra={"key": key, "error": str(e)})
            return False
    
    async def ttl(self, key: str) -> int:
        """Get time to live for key."""
        await self._ensure_connected()
        try:
            return await self.client.ttl(key)
        except Exception as e:
            logger.error("Redis TTL failed", extra={"key": key, "error": str(e)})
            return -1
    
    # Advanced Operations
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern."""
        await self._ensure_connected()
        try:
            keys = await self.client.keys(pattern)
            return [key.decode('utf-8') for key in keys]
        except Exception as e:
            logger.error("Redis KEYS failed", extra={"pattern": pattern, "error": str(e)})
            return []
    
    async def mget(self, keys: List[str]) -> List[Optional[str]]:
        """Get multiple values by keys."""
        await self._ensure_connected()
        try:
            values = await self.client.mget(keys)
            return [value.decode('utf-8') if value else None for value in values]
        except Exception as e:
            logger.error("Redis MGET failed", extra={"keys": keys, "error": str(e)})
            return [None] * len(keys)
    
    async def mset(self, mapping: Dict[str, str]) -> bool:
        """Set multiple key-value pairs."""
        await self._ensure_connected()
        try:
            result = await self.client.mset(mapping)
            return bool(result)
        except Exception as e:
            logger.error("Redis MSET failed", extra={"mapping": mapping, "error": str(e)})
            return False
    
    # JSON Operations
    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value by key."""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.error("JSON decode failed", extra={"key": key, "error": str(e)})
        return None
    
    async def set_json(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set JSON value with optional expiration."""
        try:
            json_value = json.dumps(value)
            return await self.set(key, json_value, ex=ex)
        except (TypeError, ValueError) as e:
            logger.error("JSON encode failed", extra={"key": key, "error": str(e)})
            return False
    
    # Hash Operations
    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field value."""
        await self._ensure_connected()
        try:
            value = await self.client.hget(name, key)
            return value.decode('utf-8') if value else None
        except Exception as e:
            logger.error("Redis HGET failed", extra={"name": name, "key": key, "error": str(e)})
            return None
    
    async def hset(self, name: str, key: str, value: str) -> bool:
        """Set hash field value."""
        await self._ensure_connected()
        try:
            result = await self.client.hset(name, key, value)
            return bool(result)
        except Exception as e:
            logger.error("Redis HSET failed", extra={"name": name, "key": key, "error": str(e)})
            return False
    
    async def hgetall(self, name: str) -> Dict[str, str]:
        """Get all hash fields and values."""
        await self._ensure_connected()
        try:
            result = await self.client.hgetall(name)
            return {k.decode('utf-8'): v.decode('utf-8') for k, v in result.items()}
        except Exception as e:
            logger.error("Redis HGETALL failed", extra={"name": name, "error": str(e)})
            return {}
    
    async def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields."""
        await self._ensure_connected()
        try:
            return await self.client.hdel(name, *keys)
        except Exception as e:
            logger.error("Redis HDEL failed", extra={"name": name, "keys": keys, "error": str(e)})
            return 0
    
    # List Operations
    async def lpush(self, name: str, *values: str) -> int:
        """Push values to left of list."""
        await self._ensure_connected()
        try:
            return await self.client.lpush(name, *values)
        except Exception as e:
            logger.error("Redis LPUSH failed", extra={"name": name, "error": str(e)})
            return 0
    
    async def rpush(self, name: str, *values: str) -> int:
        """Push values to right of list."""
        await self._ensure_connected()
        try:
            return await self.client.rpush(name, *values)
        except Exception as e:
            logger.error("Redis RPUSH failed", extra={"name": name, "error": str(e)})
            return 0
    
    async def lpop(self, name: str) -> Optional[str]:
        """Pop value from left of list."""
        await self._ensure_connected()
        try:
            value = await self.client.lpop(name)
            return value.decode('utf-8') if value else None
        except Exception as e:
            logger.error("Redis LPOP failed", extra={"name": name, "error": str(e)})
            return None
    
    async def lrange(self, name: str, start: int, end: int) -> List[str]:
        """Get list range."""
        await self._ensure_connected()
        try:
            values = await self.client.lrange(name, start, end)
            return [value.decode('utf-8') for value in values]
        except Exception as e:
            logger.error("Redis LRANGE failed", extra={"name": name, "error": str(e)})
            return []
    
    # Set Operations
    async def sadd(self, name: str, *values: str) -> int:
        """Add values to set."""
        await self._ensure_connected()
        try:
            return await self.client.sadd(name, *values)
        except Exception as e:
            logger.error("Redis SADD failed", extra={"name": name, "error": str(e)})
            return 0
    
    async def srem(self, name: str, *values: str) -> int:
        """Remove values from set."""
        await self._ensure_connected()
        try:
            return await self.client.srem(name, *values)
        except Exception as e:
            logger.error("Redis SREM failed", extra={"name": name, "error": str(e)})
            return 0
    
    async def smembers(self, name: str) -> set:
        """Get all set members."""
        await self._ensure_connected()
        try:
            members = await self.client.smembers(name)
            return {member.decode('utf-8') for member in members}
        except Exception as e:
            logger.error("Redis SMEMBERS failed", extra={"name": name, "error": str(e)})
            return set()
    
    async def sismember(self, name: str, value: str) -> bool:
        """Check if value is in set."""
        await self._ensure_connected()
        try:
            result = await self.client.sismember(name, value)
            return bool(result)
        except Exception as e:
            logger.error("Redis SISMEMBER failed", extra={"name": name, "value": value, "error": str(e)})
            return False
    
    # Utility Operations
    async def ping(self) -> bool:
        """Ping Redis server."""
        await self._ensure_connected()
        try:
            result = await self.client.ping()
            return result
        except Exception as e:
            logger.error("Redis PING failed", extra={"error": str(e)})
            return False
    
    async def info(self, section: Optional[str] = None) -> Dict[str, Any]:
        """Get Redis server info."""
        await self._ensure_connected()
        try:
            return await self.client.info(section)
        except Exception as e:
            logger.error("Redis INFO failed", extra={"error": str(e)})
            return {}
    
    async def flushdb(self) -> bool:
        """Flush current database."""
        await self._ensure_connected()
        try:
            result = await self.client.flushdb()
            return bool(result)
        except Exception as e:
            logger.error("Redis FLUSHDB failed", extra={"error": str(e)})
            return False
    
    async def dbsize(self) -> int:
        """Get database size."""
        await self._ensure_connected()
        try:
            return await self.client.dbsize()
        except Exception as e:
            logger.error("Redis DBSIZE failed", extra={"error": str(e)})
            return 0
    
    # Context Manager Support
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


# Global Redis client instance
_redis_client: Optional[RedisClient] = None


def get_redis_client(url: Optional[str] = None) -> RedisClient:
    """Get the global Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient(url)
    return _redis_client


def init_redis_client(url: str, **kwargs) -> RedisClient:
    """Initialize the global Redis client with custom settings."""
    global _redis_client
    _redis_client = RedisClient(url, **kwargs)
    return _redis_client


# Utility functions for common caching patterns
async def cache_with_ttl(key: str, value: Any, ttl_seconds: int, client: Optional[RedisClient] = None) -> bool:
    """Cache a value with TTL."""
    redis_client = client or get_redis_client()
    return await redis_client.set_json(key, value, ex=ttl_seconds)


async def get_cached_or_compute(key: str, compute_func, ttl_seconds: int = 300, 
                               client: Optional[RedisClient] = None) -> Any:
    """Get cached value or compute and cache it."""
    redis_client = client or get_redis_client()
    
    # Try to get from cache first
    cached_value = await redis_client.get_json(key)
    if cached_value is not None:
        return cached_value
    
    # Compute value
    if asyncio.iscoroutinefunction(compute_func):
        computed_value = await compute_func()
    else:
        computed_value = compute_func()
    
    # Cache the computed value
    await redis_client.set_json(key, computed_value, ex=ttl_seconds)
    
    return computed_value


async def invalidate_cache_pattern(pattern: str, client: Optional[RedisClient] = None) -> int:
    """Invalidate all cache keys matching a pattern."""
    redis_client = client or get_redis_client()
    keys = await redis_client.keys(pattern)
    if keys:
        return await redis_client.delete(*keys)
    return 0
