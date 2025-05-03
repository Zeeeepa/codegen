"""
Cache manager for codegen-on-oss.

This module provides a cache manager that supports multiple cache backends,
including in-memory, Redis, and file-based caching.
"""

import os
import json
import pickle
import logging
import hashlib
import time
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Generic
from functools import wraps
from pathlib import Path
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from contextlib import contextmanager

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from platformdirs import user_cache_dir

logger = logging.getLogger(__name__)

# Type variable for generic cache
T = TypeVar('T')

class CacheBackend(ABC, Generic[T]):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[T]:
        """Get a value from the cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """Set a value in the cache with an optional TTL in seconds."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete a value from the cache."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all values from the cache."""
        pass


class InMemoryCache(CacheBackend[T]):
    """In-memory cache backend."""
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize the in-memory cache.
        
        Args:
            max_size: Maximum number of items to store in the cache.
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
    
    def get(self, key: str) -> Optional[T]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key.
            
        Returns:
            Cached value if found and not expired, None otherwise.
        """
        if key not in self.cache:
            return None
        
        item = self.cache[key]
        
        # Check if the item has expired
        if 'expires_at' in item and item['expires_at'] is not None:
            if datetime.now() > item['expires_at']:
                self.delete(key)
                return None
        
        return item['value']
    
    def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache with an optional TTL in seconds.
        
        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time to live in seconds.
        """
        # If the cache is full, remove the oldest item
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['created_at'])
            self.delete(oldest_key)
        
        expires_at = None
        if ttl is not None:
            expires_at = datetime.now() + timedelta(seconds=ttl)
        
        self.cache[key] = {
            'value': value,
            'created_at': datetime.now(),
            'expires_at': expires_at
        }
    
    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key.
        """
        if key in self.cache:
            del self.cache[key]
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache and is not expired.
        
        Args:
            key: Cache key.
            
        Returns:
            True if the key exists and is not expired, False otherwise.
        """
        if key not in self.cache:
            return False
        
        item = self.cache[key]
        
        # Check if the item has expired
        if 'expires_at' in item and item['expires_at'] is not None:
            if datetime.now() > item['expires_at']:
                self.delete(key)
                return False
        
        return True
    
    def clear(self) -> None:
        """Clear all values from the cache."""
        self.cache.clear()


class RedisCache(CacheBackend[T]):
    """Redis cache backend."""
    
    def __init__(
        self, 
        host: str = 'localhost', 
        port: int = 6379, 
        db: int = 0,
        password: Optional[str] = None,
        prefix: str = 'codegen:',
        serializer: Callable[[T], bytes] = pickle.dumps,
        deserializer: Callable[[bytes], T] = pickle.loads
    ):
        """
        Initialize the Redis cache.
        
        Args:
            host: Redis host.
            port: Redis port.
            db: Redis database number.
            password: Redis password.
            prefix: Key prefix for all cache keys.
            serializer: Function to serialize values to bytes.
            deserializer: Function to deserialize bytes to values.
        """
        if not REDIS_AVAILABLE:
            raise ImportError("Redis is not available. Install it with 'pip install redis'.")
        
        self.redis_params = {
            'host': host,
            'port': port,
            'db': db,
            'password': password
        }
        self._redis = None
        self.prefix = prefix
        self.serializer = serializer
        self.deserializer = deserializer
    
    @property
    def redis(self):
        """Lazy initialization of Redis connection."""
        if self._redis is None:
            self._redis = redis.Redis(**self.redis_params)
        return self._redis
    
    def close(self):
        """Close the Redis connection."""
        if self._redis is not None:
            self._redis.close()
            self._redis = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def _prefixed_key(self, key: str) -> str:
        """Add the prefix to a key."""
        return f"{self.prefix}{key}"
    
    def get(self, key: str) -> Optional[T]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key.
            
        Returns:
            Cached value if found, None otherwise.
        """
        prefixed_key = self._prefixed_key(key)
        value = self.redis.get(prefixed_key)
        
        if value is None:
            return None
        
        try:
            return self.deserializer(value)
        except Exception as e:
            logger.error(f"Error deserializing cache value for key {key}: {e}")
            return None
    
    def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache with an optional TTL in seconds.
        
        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time to live in seconds.
        """
        prefixed_key = self._prefixed_key(key)
        
        try:
            serialized_value = self.serializer(value)
            if ttl is not None:
                self.redis.setex(prefixed_key, ttl, serialized_value)
            else:
                self.redis.set(prefixed_key, serialized_value)
        except Exception as e:
            logger.error(f"Error serializing cache value for key {key}: {e}")
    
    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key.
        """
        prefixed_key = self._prefixed_key(key)
        self.redis.delete(prefixed_key)
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: Cache key.
            
        Returns:
            True if the key exists, False otherwise.
        """
        prefixed_key = self._prefixed_key(key)
        return bool(self.redis.exists(prefixed_key))
    
    def clear(self) -> None:
        """Clear all values from the cache with the configured prefix."""
        for key in self.redis.keys(f"{self.prefix}*"):
            self.redis.delete(key)


class FileCache(CacheBackend[T]):
    """File-based cache backend."""
    
    def __init__(
        self, 
        cache_dir: Optional[str] = None,
        serializer: Callable[[T], bytes] = pickle.dumps,
        deserializer: Callable[[bytes], T] = pickle.loads
    ):
        """
        Initialize the file cache.
        
        Args:
            cache_dir: Directory to store cache files. If None, uses platformdirs.
            serializer: Function to serialize values to bytes.
            deserializer: Function to deserialize bytes to values.
        """
        if cache_dir is None:
            cache_dir = user_cache_dir("codegen-on-oss", "codegen")
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.serializer = serializer
        self.deserializer = deserializer
        
        # Create a metadata file to track TTLs
        self.metadata_file = self.cache_dir / "metadata.json"
        if not self.metadata_file.exists():
            self._save_metadata({})
    
    def _get_cache_path(self, key: str) -> Path:
        """Get the file path for a cache key."""
        # Use a hash of the key as the filename to avoid invalid characters
        hashed_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / hashed_key
    
    def _load_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Load the metadata file."""
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading cache metadata: {e}")
            return {}
    
    def _save_metadata(self, metadata: Dict[str, Dict[str, Any]]) -> None:
        """Save the metadata file."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f)
        except Exception as e:
            logger.error(f"Error saving cache metadata: {e}")
    
    def _update_metadata(self, key: str, expires_at: Optional[datetime] = None) -> None:
        """Update the metadata for a key."""
        metadata = self._load_metadata()
        
        if expires_at is None:
            metadata[key] = {'created_at': datetime.now().isoformat()}
        else:
            metadata[key] = {
                'created_at': datetime.now().isoformat(),
                'expires_at': expires_at.isoformat()
            }
        
        self._save_metadata(metadata)
    
    def _remove_metadata(self, key: str) -> None:
        """Remove the metadata for a key."""
        metadata = self._load_metadata()
        
        if key in metadata:
            del metadata[key]
            self._save_metadata(metadata)
    
    def _is_expired(self, key: str) -> bool:
        """Check if a key has expired."""
        metadata = self._load_metadata()
        
        if key not in metadata:
            return True
        
        if 'expires_at' not in metadata[key]:
            return False
        
        expires_at = datetime.fromisoformat(metadata[key]['expires_at'])
        return datetime.now() > expires_at
    
    def get(self, key: str) -> Optional[T]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key.
            
        Returns:
            Cached value if found and not expired, None otherwise.
        """
        if self._is_expired(key):
            self.delete(key)
            return None
        
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                return self.deserializer(f.read())
        except Exception as e:
            logger.error(f"Error reading cache file for key {key}: {e}")
            return None
    
    def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache with an optional TTL in seconds.
        
        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time to live in seconds.
        """
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, 'wb') as f:
                f.write(self.serializer(value))
            
            expires_at = None
            if ttl is not None:
                expires_at = datetime.now() + timedelta(seconds=ttl)
            
            self._update_metadata(key, expires_at)
        except Exception as e:
            logger.error(f"Error writing cache file for key {key}: {e}")
    
    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key.
        """
        cache_path = self._get_cache_path(key)
        
        if cache_path.exists():
            try:
                cache_path.unlink()
            except Exception as e:
                logger.error(f"Error deleting cache file for key {key}: {e}")
        
        self._remove_metadata(key)
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache and is not expired.
        
        Args:
            key: Cache key.
            
        Returns:
            True if the key exists and is not expired, False otherwise.
        """
        if self._is_expired(key):
            self.delete(key)
            return False
        
        cache_path = self._get_cache_path(key)
        return cache_path.exists()
    
    def clear(self) -> None:
        """Clear all values from the cache."""
        for cache_file in self.cache_dir.glob("*"):
            if cache_file != self.metadata_file:
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.error(f"Error deleting cache file {cache_file}: {e}")
        
        self._save_metadata({})


class CacheManager:
    """
    Cache manager that supports multiple cache backends.
    
    This class provides a unified interface for caching with support for
    multiple backends, including in-memory, Redis, and file-based caching.
    """
    
    def __init__(
        self, 
        backend: str = 'memory',
        **backend_kwargs
    ):
        """
        Initialize the cache manager.
        
        Args:
            backend: Cache backend to use ('memory', 'redis', or 'file').
            **backend_kwargs: Additional arguments to pass to the backend.
        """
        self.backend_name = backend
        
        if backend == 'memory':
            self.backend = InMemoryCache(**backend_kwargs)
        elif backend == 'redis':
            if not REDIS_AVAILABLE:
                logger.warning("Redis is not available. Falling back to in-memory cache.")
                self.backend = InMemoryCache()
            else:
                self.backend = RedisCache(**backend_kwargs)
        elif backend == 'file':
            self.backend = FileCache(**backend_kwargs)
        else:
            raise ValueError(f"Unknown cache backend: {backend}")
    
    def get(self, key: str) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key.
            
        Returns:
            Cached value if found, None otherwise.
        """
        return self.backend.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache with an optional TTL in seconds.
        
        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time to live in seconds.
        """
        self.backend.set(key, value, ttl)
    
    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key.
        """
        self.backend.delete(key)
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: Cache key.
            
        Returns:
            True if the key exists, False otherwise.
        """
        return self.backend.exists(key)
    
    def clear(self) -> None:
        """Clear all values from the cache."""
        self.backend.clear()
    
    def cached(self, key_prefix: str, ttl: Optional[int] = None):
        """
        Decorator for caching function results.
        
        Args:
            key_prefix: Prefix for the cache key.
            ttl: Time to live in seconds.
            
        Returns:
            Decorated function.
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Create a cache key from the function name, args, and kwargs
                key_parts = [key_prefix, func.__name__]
                
                # Add args to the key
                for arg in args:
                    key_parts.append(str(arg))
                
                # Add kwargs to the key (sorted for consistency)
                for k, v in sorted(kwargs.items()):
                    key_parts.append(f"{k}={v}")
                
                cache_key = ":".join(key_parts)
                
                # Check if the result is cached
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Call the function and cache the result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        
        return decorator
    
    def close(self):
        """Close the cache backend if it supports closing."""
        if hasattr(self.backend, 'close'):
            self.backend.close()


# Global cache manager instance
cache_manager = CacheManager()

def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    return cache_manager

def initialize_cache(backend: str = 'memory', **backend_kwargs) -> CacheManager:
    """
    Initialize the cache.
    
    Args:
        backend: Cache backend to use ('memory', 'redis', or 'file').
        **backend_kwargs: Additional arguments to pass to the backend.
        
    Returns:
        CacheManager instance.
    """
    global cache_manager
    cache_manager = CacheManager(backend, **backend_kwargs)
    return cache_manager
