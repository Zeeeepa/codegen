/**
 * DataService - Handles API communication with caching and offline support
 * Integrates with WebSocket for real-time updates
 * Supports event-driven data synchronization
 */

import { WebSocketService } from './WebSocketService';

export interface CacheEntry<T = any> {
  data: T;
  timestamp: number;
}

export interface FetchOptions extends RequestInit {
  cacheDuration?: number;
  skipCache?: boolean;
}

export type DataEventHandler = (type: string, data: any) => void;

export class DataService {
  private cache: Map<string, CacheEntry> = new Map();
  private eventListeners: Set<DataEventHandler> = new Set();
  private baseURL: string = '/api';
  private lastFetch: Record<string, number> = {};
  private webSocketService: WebSocketService | null = null;
  private realTimeEnabled: boolean = false;

  constructor(webSocketService?: WebSocketService) {
    if (webSocketService) {
      this.webSocketService = webSocketService;
      this.setupWebSocketIntegration();
    }
  }

  /**
   * Setup WebSocket integration for real-time updates
   */
  private setupWebSocketIntegration(): void {
    if (!this.webSocketService) return;

    this.webSocketService.on('data_refresh', (data) => {
      this.handleDataRefresh(data);
    });

    this.webSocketService.on('connected', () => {
      this.realTimeEnabled = true;
      this.notifyListeners('ws_connected', { realTimeEnabled: true });
    });

    this.webSocketService.on('disconnected', () => {
      this.realTimeEnabled = false;
      this.notifyListeners('ws_disconnected', { realTimeEnabled: false });
    });
  }

  /**
   * Handle data refresh from WebSocket
   */
  private handleDataRefresh(data: { type: string; payload: any }): void {
    // Invalidate cache for this data type
    const cacheKeys = Array.from(this.cache.keys()).filter(key => 
      key.includes(data.type)
    );
    
    cacheKeys.forEach(key => this.cache.delete(key));
    
    // Notify listeners
    this.notifyListeners(data.type, data.payload);
  }

  /**
   * Add event listener for data changes
   */
  addEventListener(callback: DataEventHandler): () => void {
    this.eventListeners.add(callback);
    
    // Return unsubscribe function
    return () => {
      this.eventListeners.delete(callback);
    };
  }

  /**
   * Remove event listener
   */
  removeEventListener(callback: DataEventHandler): void {
    this.eventListeners.delete(callback);
  }

  /**
   * Notify all listeners of data changes
   */
  private notifyListeners(type: string, data: any): void {
    this.eventListeners.forEach(callback => {
      try {
        callback(type, data);
      } catch (error) {
        console.error('Error in DataService listener:', error);
      }
    });
  }

  /**
   * Generic fetch with caching support
   */
  async cachedFetch<T = any>(endpoint: string, options: FetchOptions = {}): Promise<T> {
    const cacheKey = `${endpoint}_${JSON.stringify(options)}`;
    const now = Date.now();
    const cacheDuration = options.cacheDuration ?? 30000; // 30 seconds default

    // Check if we have cached data that's still valid
    if (!options.skipCache && this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey)!;
      if (now - cached.timestamp < cacheDuration) {
        console.log(`📦 Cache hit for ${endpoint}`);
        return cached.data as T;
      }
    }

    try {
      const response = await fetch(this.baseURL + endpoint, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Cache the response
      this.cache.set(cacheKey, {
        data,
        timestamp: now
      });

      this.lastFetch[endpoint] = now;
      return data as T;
    } catch (error) {
      console.warn(`Server not available for ${endpoint}:`, (error as Error).message);
      
      // Return cached data if available, even if stale
      if (this.cache.has(cacheKey)) {
        console.log(`📦 Using stale cache for ${endpoint}`);
        return this.cache.get(cacheKey)!.data as T;
      }
      
      throw error;
    }
  }

  /**
   * GET request
   */
  async get<T = any>(endpoint: string, options: FetchOptions = {}): Promise<T> {
    return this.cachedFetch<T>(endpoint, { ...options, method: 'GET' });
  }

  /**
   * POST request
   */
  async post<T = any>(endpoint: string, data: any, options: RequestInit = {}): Promise<T> {
    const response = await fetch(this.baseURL + endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      body: JSON.stringify(data),
      ...options
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // Invalidate related cache entries
    this.invalidateCache(endpoint);
    
    const result = await response.json();
    this.notifyListeners('post_success', { endpoint, data: result });
    
    return result as T;
  }

  /**
   * PUT request
   */
  async put<T = any>(endpoint: string, data: any, options: RequestInit = {}): Promise<T> {
    const response = await fetch(this.baseURL + endpoint, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      body: JSON.stringify(data),
      ...options
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // Invalidate related cache entries
    this.invalidateCache(endpoint);
    
    const result = await response.json();
    this.notifyListeners('put_success', { endpoint, data: result });
    
    return result as T;
  }

  /**
   * PATCH request
   */
  async patch<T = any>(endpoint: string, data: any, options: RequestInit = {}): Promise<T> {
    const response = await fetch(this.baseURL + endpoint, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      body: JSON.stringify(data),
      ...options
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // Invalidate related cache entries
    this.invalidateCache(endpoint);
    
    const result = await response.json();
    this.notifyListeners('patch_success', { endpoint, data: result });
    
    return result as T;
  }

  /**
   * DELETE request
   */
  async delete<T = any>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(this.baseURL + endpoint, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // Invalidate related cache entries
    this.invalidateCache(endpoint);
    
    const result = await response.json();
    this.notifyListeners('delete_success', { endpoint, data: result });
    
    return result as T;
  }

  /**
   * Invalidate cache entries related to an endpoint
   */
  private invalidateCache(endpoint: string): void {
    const endpointBase = endpoint.split('?')[0].split('/')[1]; // Get base resource
    const keysToDelete = Array.from(this.cache.keys()).filter(key => 
      key.includes(endpointBase)
    );
    
    keysToDelete.forEach(key => this.cache.delete(key));
  }

  /**
   * Clear all cache
   */
  clearCache(): void {
    this.cache.clear();
    console.log('🗑️ Cache cleared');
  }

  /**
   * Clear cache for specific endpoint
   */
  clearCacheForEndpoint(endpoint: string): void {
    const keysToDelete = Array.from(this.cache.keys()).filter(key => 
      key.includes(endpoint)
    );
    
    keysToDelete.forEach(key => this.cache.delete(key));
    console.log(`🗑️ Cache cleared for ${endpoint}`);
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): {
    size: number;
    entries: { key: string; age: number }[];
  } {
    const now = Date.now();
    const entries = Array.from(this.cache.entries()).map(([key, entry]) => ({
      key,
      age: now - entry.timestamp
    }));

    return {
      size: this.cache.size,
      entries
    };
  }

  /**
   * Set base URL for API requests
   */
  setBaseURL(url: string): void {
    this.baseURL = url;
  }

  /**
   * Get base URL
   */
  getBaseURL(): string {
    return this.baseURL;
  }

  /**
   * Check if real-time updates are enabled
   */
  isRealTimeEnabled(): boolean {
    return this.realTimeEnabled;
  }

  /**
   * Subscribe to real-time channel
   */
  subscribeToChannel(channel: string): void {
    if (this.webSocketService) {
      this.webSocketService.subscribe(channel);
    }
  }

  /**
   * Unsubscribe from real-time channel
   */
  unsubscribeFromChannel(channel: string): void {
    if (this.webSocketService) {
      this.webSocketService.unsubscribe(channel);
    }
  }
}

// Export singleton instance
export const dataService = new DataService();

