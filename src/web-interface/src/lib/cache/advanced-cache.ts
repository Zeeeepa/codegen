/**
 * Advanced Caching System
 * Multi-tier caching with intelligent invalidation
 */

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
  tags: string[];
  dependencies: string[];
  accessCount: number;
  lastAccessed: number;
}

interface CacheConfig {
  defaultTTL: number;
  maxSize: number;
  enableCompression: boolean;
  enablePersistence: boolean;
  storageKey: string;
}

class AdvancedCache {
  private cache = new Map<string, CacheEntry<any>>();
  private config: CacheConfig;
  private cleanupInterval: NodeJS.Timeout | null = null;
  private compressionEnabled: boolean;

  constructor(config: Partial<CacheConfig> = {}) {
    this.config = {
      defaultTTL: 300000, // 5 minutes
      maxSize: 1000,
      enableCompression: false,
      enablePersistence: true,
      storageKey: 'codegen_advanced_cache',
      ...config,
    };

    this.compressionEnabled = this.config.enableCompression && typeof window !== 'undefined';
    
    // Load persisted cache
    if (this.config.enablePersistence) {
      this.loadFromStorage();
    }

    // Start cleanup interval
    this.startCleanup();
  }

  /**
   * Set cache entry with advanced options
   */
  set<T>(
    key: string,
    data: T,
    options: {
      ttl?: number;
      tags?: string[];
      dependencies?: string[];
      compress?: boolean;
    } = {}
  ): void {
    const now = Date.now();
    const ttl = options.ttl || this.config.defaultTTL;
    
    // Check cache size limit
    if (this.cache.size >= this.config.maxSize) {
      this.evictLeastRecentlyUsed();
    }

    // Compress data if enabled
    let processedData = data;
    if (options.compress && this.compressionEnabled) {
      processedData = this.compress(data);
    }

    const entry: CacheEntry<T> = {
      data: processedData,
      timestamp: now,
      ttl,
      tags: options.tags || [],
      dependencies: options.dependencies || [],
      accessCount: 0,
      lastAccessed: now,
    };

    this.cache.set(key, entry);

    // Persist to storage if enabled
    if (this.config.enablePersistence) {
      this.persistToStorage();
    }
  }

  /**
   * Get cache entry with access tracking
   */
  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    
    if (!entry) {
      return null;
    }

    const now = Date.now();
    
    // Check if entry has expired
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    // Update access statistics
    entry.accessCount++;
    entry.lastAccessed = now;

    // Decompress data if needed
    let data = entry.data;
    if (this.compressionEnabled && this.isCompressed(data)) {
      data = this.decompress(data);
    }

    return data;
  }

  /**
   * Check if key exists and is valid
   */
  has(key: string): boolean {
    const entry = this.cache.get(key);
    
    if (!entry) {
      return false;
    }

    const now = Date.now();
    
    // Check if entry has expired
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return false;
    }

    return true;
  }

  /**
   * Delete specific cache entry
   */
  delete(key: string): boolean {
    const deleted = this.cache.delete(key);
    
    if (deleted && this.config.enablePersistence) {
      this.persistToStorage();
    }
    
    return deleted;
  }

  /**
   * Invalidate cache entries by tags
   */
  invalidateByTags(tags: string[]): number {
    let invalidated = 0;
    
    for (const [key, entry] of this.cache.entries()) {
      if (entry.tags.some(tag => tags.includes(tag))) {
        this.cache.delete(key);
        invalidated++;
      }
    }

    if (invalidated > 0 && this.config.enablePersistence) {
      this.persistToStorage();
    }

    return invalidated;
  }

  /**
   * Invalidate cache entries by dependencies
   */
  invalidateByDependencies(dependencies: string[]): number {
    let invalidated = 0;
    
    for (const [key, entry] of this.cache.entries()) {
      if (entry.dependencies.some(dep => dependencies.includes(dep))) {
        this.cache.delete(key);
        invalidated++;
      }
    }

    if (invalidated > 0 && this.config.enablePersistence) {
      this.persistToStorage();
    }

    return invalidated;
  }

  /**
   * Get cache statistics
   */
  getStats(): {
    size: number;
    maxSize: number;
    hitRate: number;
    memoryUsage: number;
    oldestEntry: number;
    newestEntry: number;
  } {
    const now = Date.now();
    let totalAccess = 0;
    let totalHits = 0;
    let oldestTimestamp = now;
    let newestTimestamp = 0;
    let memoryUsage = 0;

    for (const [key, entry] of this.cache.entries()) {
      totalAccess += entry.accessCount;
      if (entry.accessCount > 0) {
        totalHits++;
      }
      
      if (entry.timestamp < oldestTimestamp) {
        oldestTimestamp = entry.timestamp;
      }
      
      if (entry.timestamp > newestTimestamp) {
        newestTimestamp = entry.timestamp;
      }

      // Estimate memory usage
      memoryUsage += this.estimateSize(key) + this.estimateSize(entry);
    }

    return {
      size: this.cache.size,
      maxSize: this.config.maxSize,
      hitRate: totalAccess > 0 ? totalHits / totalAccess : 0,
      memoryUsage,
      oldestEntry: oldestTimestamp,
      newestEntry: newestTimestamp,
    };
  }

  /**
   * Clear all cache entries
   */
  clear(): void {
    this.cache.clear();
    
    if (this.config.enablePersistence) {
      this.clearStorage();
    }
  }

  /**
   * Get all cache keys with optional filtering
   */
  keys(filter?: {
    tags?: string[];
    dependencies?: string[];
    expired?: boolean;
  }): string[] {
    const now = Date.now();
    const keys: string[] = [];

    for (const [key, entry] of this.cache.entries()) {
      // Check expiration filter
      const isExpired = now - entry.timestamp > entry.ttl;
      if (filter?.expired !== undefined && filter.expired !== isExpired) {
        continue;
      }

      // Check tags filter
      if (filter?.tags && !filter.tags.some(tag => entry.tags.includes(tag))) {
        continue;
      }

      // Check dependencies filter
      if (filter?.dependencies && !filter.dependencies.some(dep => entry.dependencies.includes(dep))) {
        continue;
      }

      keys.push(key);
    }

    return keys;
  }

  /**
   * Batch operations
   */
  batch(): CacheBatch {
    return new CacheBatch(this);
  }

  /**
   * Evict least recently used entries
   */
  private evictLeastRecentlyUsed(): void {
    let lruKey: string | null = null;
    let lruTime = Date.now();

    for (const [key, entry] of this.cache.entries()) {
      if (entry.lastAccessed < lruTime) {
        lruTime = entry.lastAccessed;
        lruKey = key;
      }
    }

    if (lruKey) {
      this.cache.delete(lruKey);
    }
  }

  /**
   * Start cleanup interval
   */
  private startCleanup(): void {
    this.cleanupInterval = setInterval(() => {
      this.cleanup();
    }, 60000); // Run every minute
  }

  /**
   * Cleanup expired entries
   */
  private cleanup(): void {
    const now = Date.now();
    const expiredKeys: string[] = [];

    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > entry.ttl) {
        expiredKeys.push(key);
      }
    }

    expiredKeys.forEach(key => this.cache.delete(key));

    if (expiredKeys.length > 0 && this.config.enablePersistence) {
      this.persistToStorage();
    }
  }

  /**
   * Persist cache to storage
   */
  private persistToStorage(): void {
    if (typeof window === 'undefined') return;

    try {
      const serialized = JSON.stringify(Array.from(this.cache.entries()));
      localStorage.setItem(this.config.storageKey, serialized);
    } catch (error) {
      console.warn('Failed to persist cache to storage:', error);
    }
  }

  /**
   * Load cache from storage
   */
  private loadFromStorage(): void {
    if (typeof window === 'undefined') return;

    try {
      const stored = localStorage.getItem(this.config.storageKey);
      if (stored) {
        const entries = JSON.parse(stored);
        this.cache = new Map(entries);
        
        // Clean up expired entries
        this.cleanup();
      }
    } catch (error) {
      console.warn('Failed to load cache from storage:', error);
    }
  }

  /**
   * Clear storage
   */
  private clearStorage(): void {
    if (typeof window === 'undefined') return;

    try {
      localStorage.removeItem(this.config.storageKey);
    } catch (error) {
      console.warn('Failed to clear cache storage:', error);
    }
  }

  /**
   * Compress data (placeholder - would use actual compression library)
   */
  private compress<T>(data: T): any {
    // In a real implementation, you would use a compression library like lz-string
    return { __compressed: true, data: JSON.stringify(data) };
  }

  /**
   * Decompress data
   */
  private decompress<T>(data: any): T {
    if (this.isCompressed(data)) {
      return JSON.parse(data.data);
    }
    return data;
  }

  /**
   * Check if data is compressed
   */
  private isCompressed(data: any): boolean {
    return data && typeof data === 'object' && data.__compressed === true;
  }

  /**
   * Estimate memory usage of an object
   */
  private estimateSize(obj: any): number {
    const str = JSON.stringify(obj);
    return str.length * 2; // Rough estimate (UTF-16)
  }

  /**
   * Destroy cache and cleanup
   */
  destroy(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
    
    this.clear();
  }
}

/**
 * Batch operations for cache
 */
class CacheBatch {
  private operations: Array<() => void> = [];

  constructor(private cache: AdvancedCache) {}

  set<T>(key: string, data: T, options?: any): CacheBatch {
    this.operations.push(() => this.cache.set(key, data, options));
    return this;
  }

  delete(key: string): CacheBatch {
    this.operations.push(() => this.cache.delete(key));
    return this;
  }

  invalidateByTags(tags: string[]): CacheBatch {
    this.operations.push(() => this.cache.invalidateByTags(tags));
    return this;
  }

  execute(): void {
    this.operations.forEach(op => op());
    this.operations = [];
  }
}

// Create singleton instances for different cache tiers
export const memoryCache = new AdvancedCache({
  defaultTTL: 300000, // 5 minutes
  maxSize: 500,
  enablePersistence: false,
  storageKey: 'codegen_memory_cache',
});

export const persistentCache = new AdvancedCache({
  defaultTTL: 1800000, // 30 minutes
  maxSize: 1000,
  enablePersistence: true,
  storageKey: 'codegen_persistent_cache',
});

export const longTermCache = new AdvancedCache({
  defaultTTL: 86400000, // 24 hours
  maxSize: 200,
  enablePersistence: true,
  enableCompression: true,
  storageKey: 'codegen_longterm_cache',
});

export default AdvancedCache;
