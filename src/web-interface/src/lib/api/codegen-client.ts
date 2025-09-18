/**
 * Codegen API Client
 * Integrates with existing Codegen API while respecting rate limits and providing caching
 * Enhanced with authentication management similar to VSCode extension structure
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

// Enhanced interfaces to match VSCode extension structure
export interface AgentRunsResponse {
  items: AgentRun[];
  total: number;
  page: number;
  per_page: number;
}

export interface CreateAgentRunRequest {
  prompt: string;
  model?: string;
  repo_id?: number;
}

// AuthManager-like interface for web
class WebAuthManager {
  private token: string | null = null;
  private orgId: string | null = null;

  constructor() {
    this.loadFromStorage();
  }

  private loadFromStorage(): void {
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('codegen_token');
      this.orgId = localStorage.getItem('codegen_org_id');
    }
  }

  async getToken(): Promise<string | null> {
    return this.token;
  }

  setToken(token: string): void {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('codegen_token', token);
    }
  }

  getOrgId(): string | null {
    return this.orgId;
  }

  setOrgId(orgId: string): void {
    this.orgId = orgId;
    if (typeof window !== 'undefined') {
      localStorage.setItem('codegen_org_id', orgId);
    }
  }

  clearAuth(): void {
    this.token = null;
    this.orgId = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('codegen_token');
      localStorage.removeItem('codegen_org_id');
    }
  }
}

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
  private authManager: WebAuthManager;

  constructor(baseURL?: string, authManager?: WebAuthManager) {
    this.authManager = authManager || new WebAuthManager();
    
    this.client = axios.create({
      baseURL: baseURL || process.env.CODEGEN_API_URL || 'https://api.codegen.com',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Set up request interceptor for authentication
    this.client.interceptors.request.use(async (config) => {
      const token = await this.authManager.getToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Set up response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle authentication errors
          this.authManager.clearAuth();
          if (typeof window !== 'undefined') {
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // Enhanced methods matching VSCode extension API
  async getAgentRuns(page: number = 1, perPage: number = 10): Promise<AgentRunsResponse> {
    const orgId = this.authManager.getOrgId();
    if (!orgId) {
      throw new Error('No organization ID found. Please login again.');
    }

    try {
      const response = await this.client.get(`/v1/organizations/${orgId}/agent/runs`, {
        params: {
          page,
          per_page: perPage,
          source_type: 'API' // Filter to API source type like the CLI does
        }
      });

      return response.data;
    } catch (error: any) {
      console.error('Failed to fetch agent runs:', error);
      throw new Error(`Failed to fetch agent runs: ${error.response?.data?.message || error.message}`);
    }
  }

  async createAgentRun(prompt: string, model?: string, repoId?: number): Promise<AgentRun> {
    const orgId = this.authManager.getOrgId();
    if (!orgId) {
      throw new Error('No organization ID found. Please login again.');
    }

    const requestData: CreateAgentRunRequest = {
      prompt,
      ...(model && { model }),
      ...(repoId && { repo_id: repoId })
    };

    try {
      const response = await this.client.post(`/v1/organizations/${orgId}/agent/run`, requestData);
      return response.data;
    } catch (error: any) {
      console.error('Failed to create agent run:', error);
      throw new Error(`Failed to create agent run: ${error.response?.data?.message || error.message}`);
    }
  }

  async getAgentRun(agentRunId: number): Promise<AgentRun> {
    const orgId = this.authManager.getOrgId();
    if (!orgId) {
      throw new Error('No organization ID found. Please login again.');
    }

    try {
      const response = await this.client.get(`/v1/organizations/${orgId}/agent/run/${agentRunId}`);
      return response.data;
    } catch (error: any) {
      console.error('Failed to fetch agent run:', error);
      throw new Error(`Failed to fetch agent run: ${error.response?.data?.message || error.message}`);
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
    this.authManager.setToken(token);
    const user = await this.getCurrentUser();
    // Set org ID from the user's organizations
    const orgs = await this.getOrganizations();
    if (orgs.length > 0) {
      this.authManager.setOrgId(orgs[0].id);
    }
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

  // Enhanced utility methods
  clearCache(): void {
    this.cache.clear();
  }

  logout(): void {
    this.authManager.clearAuth();
    this.clearCache();
  }

  getAuthManager(): WebAuthManager {
    return this.authManager;
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

// Create singleton instance with auth manager
let apiClient: CodegenAPIClient | null = null;
let authManager: WebAuthManager | null = null;

export const getAuthManager = (): WebAuthManager => {
  if (!authManager) {
    authManager = new WebAuthManager();
  }
  return authManager;
};

export const getCodegenClient = (baseURL?: string): CodegenAPIClient => {
  if (!apiClient) {
    apiClient = new CodegenAPIClient(baseURL, getAuthManager());
  }
  return apiClient;
};

export { WebAuthManager };

export default CodegenAPIClient;
