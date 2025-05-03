# Enhanced Caching System

This module provides a comprehensive caching system for the codegen-on-oss project. It includes:

- Multiple cache backends (in-memory, Redis, file-based)
- Decorator for caching function results
- Automatic cache invalidation

## Architecture

The caching system follows a layered architecture:

```
┌─────────────────────────┐
│ Cache Manager           │
│ (Unified Interface)     │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│ Cache Backend           │
│ (Implementation)        │
└─────────────────────────┘
            ▲
            │
┌───────────┴─────────────┐
│ Backend Implementations │
├─────────────────────────┤
│ - In-Memory Cache       │
│ - Redis Cache           │
│ - File Cache            │
└─────────────────────────┘
```

## Cache Backends

The caching system supports the following backends:

- `InMemoryCache`: In-memory cache using a dictionary
- `RedisCache`: Distributed cache using Redis
- `FileCache`: File-based cache using the local filesystem

## Features

- **TTL Support**: All cache backends support time-to-live (TTL) for cached items
- **Serialization**: Redis and file cache backends support custom serialization/deserialization
- **Decorator**: The `cached` decorator simplifies caching function results
- **Automatic Cleanup**: Expired items are automatically removed from the cache

## Usage

### Initializing the Cache

```python
from codegen_on_oss.cache.manager import initialize_cache

# Initialize with in-memory cache (default)
cache_manager = initialize_cache('memory')

# Initialize with Redis cache
cache_manager = initialize_cache('redis', host='localhost', port=6379, db=0)

# Initialize with file cache
cache_manager = initialize_cache('file', cache_dir='/path/to/cache')
```

### Basic Cache Operations

```python
from codegen_on_oss.cache.manager import get_cache_manager

cache_manager = get_cache_manager()

# Set a value in the cache
cache_manager.set('key', 'value')

# Set a value with TTL (in seconds)
cache_manager.set('key', 'value', ttl=3600)  # Expires after 1 hour

# Get a value from the cache
value = cache_manager.get('key')  # Returns None if not found or expired

# Check if a key exists in the cache
exists = cache_manager.exists('key')

# Delete a value from the cache
cache_manager.delete('key')

# Clear the entire cache
cache_manager.clear()
```

### Caching Function Results

```python
from codegen_on_oss.cache.manager import get_cache_manager

cache_manager = get_cache_manager()

# Decorate a function to cache its results
@cache_manager.cached('my_function', ttl=3600)
def expensive_function(arg1, arg2):
    # Expensive computation
    return result

# Call the function - result will be cached
result1 = expensive_function('a', 'b')

# Call again with the same arguments - result will be retrieved from cache
result2 = expensive_function('a', 'b')

# Call with different arguments - new computation will be performed
result3 = expensive_function('c', 'd')
```

## Configuration

The cache can be configured using environment variables:

- `CODEGEN_CACHE_BACKEND`: Cache backend to use ('memory', 'redis', or 'file')
- `CODEGEN_CACHE_REDIS_HOST`: Redis host (default: 'localhost')
- `CODEGEN_CACHE_REDIS_PORT`: Redis port (default: 6379)
- `CODEGEN_CACHE_REDIS_DB`: Redis database number (default: 0)
- `CODEGEN_CACHE_REDIS_PASSWORD`: Redis password (default: None)
- `CODEGEN_CACHE_FILE_DIR`: Directory for file cache (default: platform-specific user cache dir)

