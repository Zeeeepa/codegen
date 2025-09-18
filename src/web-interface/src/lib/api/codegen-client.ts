/**
 * Codegen API Client
 * Integrates with existing Codegen API while respecting rate limits and providing caching
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { 
  AgentRun, 
  AgentRunWithLogs, 
  CreateAgentRunInput, 
  Organization, 
  User, 
  Repository,
  PaginatedResponse,
  ApiResponse,
  Integration
} from '@/types/codegen';

// Rate limiting configuration based on Codegen API limits
const RATE_LIMITS = {
  standard: { requests: 60, window: 30000 }, // 60 requests per 30 seconds
  agentCreation: { requests: 10, window: 60000 }, // 10 requests per minute
  setupCommands: { requests: 5, window: 60000 }, // 5 requests per minute
  logAnalysis: { requests: 5, window: 60000 }, // 5 requests per minute
};

interface RateLimitTracker {
  requests: number;
  windowStart: number;
}

class CodegenAPIClient {
  private client: AxiosInstance;
  private rateLimitTrackers: Map<string, RateLimitTracker> = new Map();
  private cache: Map<string, { data: any; expires: number }> = new Map();
  private readonly cacheTimeout = 30000; // 30 seconds default cache

  constructor(baseURL?: string, token?: string) {
    this.client = axios.create({
      baseURL: baseURL || process.env.CODEGEN_API_URL || 'https://codegen-sh--rest-api.modal.run',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Set up request interceptor for authentication
    this.client.interceptors.request.use((config) => {
      const authToken = token || this.getStoredToken();
      if (authToken) {
        config.headers.Authorization = `Bearer ${authToken}`;
      }
      return config;
    });

    // Set up response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle authentication errors
          this.clearStoredToken();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  private getStoredToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('codegen_token');
    }
    return null;
  }

  private setStoredToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('codegen_token', token);
    }
  }

  private clearStoredToken(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('codegen_token');
    }
  }

  private checkRateLimit(endpoint: string, limit: { requests: number; window: number }): boolean {
    const now = Date.now();
    const tracker = this.rateLimitTrackers.get(endpoint);

    if (!tracker || now - tracker.windowStart > limit.window) {
      // New window or first request
      this.rateLimitTrackers.set(endpoint, { requests: 1, windowStart: now });
      return true;
    }

    if (tracker.requests >= limit.requests) {
      return false; // Rate limit exceeded
    }

    tracker.requests++;
    return true;
  }

  private getCacheKey(url: string, params?: any): string {
    return `${url}${params ? JSON.stringify(params) : ''}`;
  }

  private getFromCache<T>(key: string): T | null {
    const cached = this.cache.get(key);
    if (cached && Date.now() < cached.expires) {
      return cached.data;
    }
    this.cache.delete(key);
    return null;
  }

  private setCache<T>(key: string, data: T, ttl: number = this.cacheTimeout): void {
    this.cache.set(key, { data, expires: Date.now() + ttl });
  }

  private async request<T>(
    config: AxiosRequestConfig,
    rateLimitKey: string = 'standard',
    useCache: boolean = true,
    cacheTTL?: number
  ): Promise<T> {
    // Check rate limit
    const limit = RATE_LIMITS[rateLimitKey as keyof typeof RATE_LIMITS] || RATE_LIMITS.standard;
    if (!this.checkRateLimit(rateLimitKey, limit)) {
      throw new Error(`Rate limit exceeded for ${rateLimitKey}. Please wait before making more requests.`);
    }

    // Check cache for GET requests
    if (useCache && config.method === 'GET') {
      const cacheKey = this.getCacheKey(config.url!, config.params);
      const cached = this.getFromCache<T>(cacheKey);
      if (cached) {
        return cached;
      }
    }

    try {
      const response: AxiosResponse<T> = await this.client.request(config);
      
      // Cache successful GET responses
      if (useCache && config.method === 'GET' && response.status === 200) {
        const cacheKey = this.getCacheKey(config.url!, config.params);
        this.setCache(cacheKey, response.data, cacheTTL);
      }

      return response.data;
    } catch (error) {
      console.error(`API request failed:`, error);
      throw error;
    }
  }

  // Authentication methods
  async authenticate(token: string): Promise<User> {
    this.setStoredToken(token);
    const user = await this.getCurrentUser();
    return user;
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>({
      method: 'GET',
      url: '/v1/users/me',
    });
  }

  async getOrganizations(): Promise<Organization[]> {
    return this.request<Organization[]>({
      method: 'GET',
      url: '/v1/organizations',
    });
  }

  // Agent Run methods
  async createAgentRun(orgId: string, input: CreateAgentRunInput): Promise<AgentRun> {
    return this.request<AgentRun>(
      {
        method: 'POST',
        url: `/v1/organizations/${orgId}/agent/run`,
        data: input,
      },
      'agentCreation',
      false // Don't cache POST requests
    );
  }

  async getAgentRun(orgId: string, runId: string): Promise<AgentRun> {
    return this.request<AgentRun>({
      method: 'GET',
      url: `/v1/organizations/${orgId}/agent/run/${runId}`,
    });
  }

  async listAgentRuns(
    orgId: string, 
    params?: {
      page?: number;
      page_size?: number;
      source_type?: string;
      user_id?: string;
      status?: string;
    }
  ): Promise<PaginatedResponse<AgentRun>> {
    return this.request<PaginatedResponse<AgentRun>>({
      method: 'GET',
      url: `/v1/organizations/${orgId}/agent/runs`,
      params,
    });
  }

  async getAgentRunLogs(
    orgId: string, 
    runId: string,
    params?: {
      skip?: number;
      limit?: number;
    }
  ): Promise<AgentRunWithLogs> {
    return this.request<AgentRunWithLogs>(
      {
        method: 'GET',
        url: `/v1/organizations/${orgId}/agent/run/${runId}/logs`,
        params,
      },
      'logAnalysis'
    );
  }

  async resumeAgentRun(orgId: string, runId: string): Promise<AgentRun> {
    return this.request<AgentRun>(
      {
        method: 'POST',
        url: `/v1/organizations/${orgId}/agent/run/resume`,
        data: { agent_run_id: runId },
      },
      'agentCreation',
      false
    );
  }

  // Repository methods
  async getRepositories(orgId: string): Promise<Repository[]> {
    return this.request<Repository[]>({
      method: 'GET',
      url: `/v1/organizations/${orgId}/repositories`,
    });
  }

  // Integration methods
  async getIntegrations(orgId: string): Promise<Integration[]> {
    return this.request<Integration[]>({
      method: 'GET',
      url: `/v1/organizations/${orgId}/integrations`,
    });
  }

  // Utility methods
  clearCache(): void {
    this.cache.clear();
  }

  getRateLimitStatus(): Record<string, RateLimitTracker> {
    const status: Record<string, RateLimitTracker> = {};
    this.rateLimitTrackers.forEach((tracker, key) => {
      status[key] = { ...tracker };
    });
    return status;
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    try {
      const response = await this.client.get('/health');
      return {
        status: 'healthy',
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
      };
    }
  }
}

// Create singleton instance
let apiClient: CodegenAPIClient | null = null;

export const getCodegenClient = (baseURL?: string, token?: string): CodegenAPIClient => {
  if (!apiClient) {
    apiClient = new CodegenAPIClient(baseURL, token);
  }
  return apiClient;
};

export default CodegenAPIClient;
