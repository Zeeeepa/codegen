-- =====================================================
-- CACHE SCHEMA - Query Optimization and Result Caching
-- =====================================================

-- Cache configurations
CREATE TABLE cache_configurations (
    id BIGSERIAL PRIMARY KEY,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    ttl_seconds INTEGER NOT NULL DEFAULT 3600,
    invalidation_pattern VARCHAR(500),
    max_size_mb INTEGER DEFAULT 100,
    compression_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cached query results
CREATE TABLE cached_results (
    id BIGSERIAL PRIMARY KEY,
    cache_key VARCHAR(255) NOT NULL,
    query_hash VARCHAR(64) NOT NULL,
    result_data JSONB NOT NULL,
    result_size_bytes INTEGER,
    hit_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX(cache_key, query_hash),
    INDEX(expires_at),
    INDEX(last_accessed_at)
);

-- Cache statistics
CREATE TABLE cache_statistics (
    id BIGSERIAL PRIMARY KEY,
    cache_key VARCHAR(255) NOT NULL,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    hit_count INTEGER DEFAULT 0,
    miss_count INTEGER DEFAULT 0,
    eviction_count INTEGER DEFAULT 0,
    avg_response_time_ms DECIMAL(10,2),
    total_size_mb DECIMAL(10,2),
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(cache_key, date)
);

COMMENT ON TABLE cache_configurations IS 'Configuration settings for different cache types and keys';
COMMENT ON TABLE cached_results IS 'Stored cache results with expiration and access tracking';
COMMENT ON TABLE cache_statistics IS 'Daily cache performance statistics for monitoring and optimization';
