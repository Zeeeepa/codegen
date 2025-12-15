/**
 * Database API Service
 * Provides type-safe API access to PostgreSQL database via REST endpoints
 * Handles authentication, error handling, and response validation
 */

import type {
  // Workflows
  Workflow,
  CreateWorkflowRequest,
  UpdateWorkflowRequest,
  WorkflowFilters,
  
  // Executions
  Execution,
  CreateExecutionRequest,
  UpdateExecutionRequest,
  ExecutionFilters,
  
  // Templates
  Template,
  CreateTemplateRequest,
  UpdateTemplateRequest,
  TemplateFilters,
  
  // Profiles
  Profile,
  CreateProfileRequest,
  UpdateProfileRequest,
  ProfileFilters,
  
  // Workflow States
  WorkflowState,
  CreateWorkflowStateRequest,
  
  // Webhooks
  Webhook,
  CreateWebhookRequest,
  UpdateWebhookRequest,
  WebhookFilters,
  
  // API Keys
  ApiKey,
  CreateApiKeyRequest,
  CreateApiKeyResponse,
  UpdateApiKeyRequest,
  ApiKeyFilters,
  
  // Pagination
  PaginatedResponse,
  UUID,
} from '@/types/database';

// ============================================================================
// Configuration
// ============================================================================

const API_BASE = import.meta.env.VITE_DATABASE_API_BASE || 'https://api.codegen.com/v1';
const DEFAULT_ORG_ID = import.meta.env.VITE_CODEGEN_ORG_ID || '323';

// ============================================================================
// Error Handling
// ============================================================================

export class DatabaseApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string,
    public details?: any
  ) {
    super(message);
    this.name = 'DatabaseApiError';
  }
}

// ============================================================================
// HTTP Client
// ============================================================================

interface RequestOptions extends RequestInit {
  params?: Record<string, any>;
}

async function request<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { params, ...fetchOptions } = options;
  
  // Build URL with query params
  let url = `${API_BASE}${endpoint}`;
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      url += `?${queryString}`;
    }
  }
  
  // Get API token from environment or localStorage
  const apiToken = import.meta.env.VITE_CODEGEN_API_TOKEN || 
                   localStorage.getItem('codegen_api_token');
  
  if (!apiToken) {
    throw new DatabaseApiError('API token not configured', 401, 'UNAUTHORIZED');
  }
  
  // Make request
  const response = await fetch(url, {
    ...fetchOptions,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiToken}`,
      'X-Organization-Id': DEFAULT_ORG_ID,
      ...fetchOptions.headers,
    },
  });
  
  // Handle errors
  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    let errorDetails;
    
    try {
      const errorData = await response.json();
      errorMessage = errorData.message || errorMessage;
      errorDetails = errorData;
    } catch {
      // Response not JSON
    }
    
    throw new DatabaseApiError(
      errorMessage,
      response.status,
      response.status === 401 ? 'UNAUTHORIZED' : 
      response.status === 403 ? 'FORBIDDEN' : 
      response.status === 404 ? 'NOT_FOUND' : 
      'REQUEST_FAILED',
      errorDetails
    );
  }
  
  // Parse response
  if (response.status === 204) {
    return undefined as T;
  }
  
  return response.json();
}

// ============================================================================
// Workflows API
// ============================================================================

export const workflowsApi = {
  /**
   * List workflows with optional filtering
   */
  async list(filters?: WorkflowFilters): Promise<PaginatedResponse<Workflow>> {
    return request<PaginatedResponse<Workflow>>('/workflows', {
      params: filters,
    });
  },

  /**
   * Get workflow by ID
   */
  async get(id: UUID): Promise<Workflow> {
    return request<Workflow>(`/workflows/${id}`);
  },

  /**
   * Create new workflow
   */
  async create(data: CreateWorkflowRequest): Promise<Workflow> {
    return request<Workflow>('/workflows', {
      method: 'POST',
      body: JSON.stringify({
        ...data,
        organization_id: parseInt(DEFAULT_ORG_ID),
      }),
    });
  },

  /**
   * Update existing workflow
   */
  async update(id: UUID, data: UpdateWorkflowRequest): Promise<Workflow> {
    return request<Workflow>(`/workflows/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete workflow
   */
  async delete(id: UUID): Promise<void> {
    return request<void>(`/workflows/${id}`, {
      method: 'DELETE',
    });
  },

  /**
   * Duplicate workflow
   */
  async duplicate(id: UUID, newName: string): Promise<Workflow> {
    const workflow = await this.get(id);
    return this.create({
      name: newName,
      description: workflow.description,
      definition: workflow.definition,
      context: workflow.context,
    });
  },
};

// ============================================================================
// Executions API
// ============================================================================

export const executionsApi = {
  /**
   * List executions with optional filtering
   */
  async list(filters?: ExecutionFilters): Promise<PaginatedResponse<Execution>> {
    return request<PaginatedResponse<Execution>>('/executions', {
      params: filters,
    });
  },

  /**
   * Get execution by ID
   */
  async get(id: UUID): Promise<Execution> {
    return request<Execution>(`/executions/${id}`);
  },

  /**
   * Create new execution
   */
  async create(data: CreateExecutionRequest): Promise<Execution> {
    return request<Execution>('/executions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Update execution status and results
   */
  async update(id: UUID, data: UpdateExecutionRequest): Promise<Execution> {
    return request<Execution>(`/executions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get executions for specific workflow
   */
  async getByWorkflow(workflowId: UUID, filters?: ExecutionFilters): Promise<PaginatedResponse<Execution>> {
    return this.list({
      ...filters,
      workflow_id: workflowId,
    });
  },

  /**
   * Add log entry to execution
   */
  async addLog(id: UUID, logEntry: string): Promise<Execution> {
    const execution = await this.get(id);
    const logs = [...(execution.logs || []), logEntry];
    return this.update(id, { logs });
  },
};

// ============================================================================
// Templates API
// ============================================================================

export const templatesApi = {
  /**
   * List templates with optional filtering
   */
  async list(filters?: TemplateFilters): Promise<PaginatedResponse<Template>> {
    return request<PaginatedResponse<Template>>('/templates', {
      params: filters,
    });
  },

  /**
   * Get template by ID
   */
  async get(id: UUID): Promise<Template> {
    return request<Template>(`/templates/${id}`);
  },

  /**
   * Create new template
   */
  async create(data: CreateTemplateRequest): Promise<Template> {
    return request<Template>('/templates', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Update template
   */
  async update(id: UUID, data: UpdateTemplateRequest): Promise<Template> {
    return request<Template>(`/templates/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete template
   */
  async delete(id: UUID): Promise<void> {
    return request<void>(`/templates/${id}`, {
      method: 'DELETE',
    });
  },

  /**
   * Increment download count
   */
  async recordDownload(id: UUID): Promise<Template> {
    return request<Template>(`/templates/${id}/download`, {
      method: 'POST',
    });
  },

  /**
   * Rate template
   */
  async rate(id: UUID, rating: number): Promise<Template> {
    return request<Template>(`/templates/${id}/rate`, {
      method: 'POST',
      body: JSON.stringify({ rating }),
    });
  },

  /**
   * Use template to create workflow
   */
  async useTemplate(id: UUID, workflowName: string): Promise<Workflow> {
    const template = await this.get(id);
    await this.recordDownload(id);
    
    return workflowsApi.create({
      name: workflowName,
      description: template.description || `Created from template: ${template.name}`,
      definition: template.definition,
    });
  },
};

// ============================================================================
// Profiles API
// ============================================================================

export const profilesApi = {
  /**
   * List profiles with optional filtering
   */
  async list(filters?: ProfileFilters): Promise<PaginatedResponse<Profile>> {
    return request<PaginatedResponse<Profile>>('/profiles', {
      params: filters,
    });
  },

  /**
   * Get profile by ID
   */
  async get(id: UUID): Promise<Profile> {
    return request<Profile>(`/profiles/${id}`);
  },

  /**
   * Create new profile
   */
  async create(data: CreateProfileRequest): Promise<Profile> {
    return request<Profile>('/profiles', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Update profile
   */
  async update(id: UUID, data: UpdateProfileRequest): Promise<Profile> {
    return request<Profile>(`/profiles/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete profile
   */
  async delete(id: UUID): Promise<void> {
    return request<void>(`/profiles/${id}`, {
      method: 'DELETE',
    });
  },
};

// ============================================================================
// Workflow States API
// ============================================================================

export const workflowStatesApi = {
  /**
   * Get states for execution
   */
  async getByExecution(executionId: UUID): Promise<WorkflowState[]> {
    const response = await request<{ data: WorkflowState[] }>('/workflow-states', {
      params: { execution_id: executionId },
    });
    return response.data;
  },

  /**
   * Create state snapshot
   */
  async create(data: CreateWorkflowStateRequest): Promise<WorkflowState> {
    return request<WorkflowState>('/workflow-states', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get state by ID
   */
  async get(id: UUID): Promise<WorkflowState> {
    return request<WorkflowState>(`/workflow-states/${id}`);
  },
};

// ============================================================================
// Webhooks API
// ============================================================================

export const webhooksApi = {
  /**
   * List webhooks with optional filtering
   */
  async list(filters?: WebhookFilters): Promise<PaginatedResponse<Webhook>> {
    return request<PaginatedResponse<Webhook>>('/webhooks', {
      params: filters,
    });
  },

  /**
   * Get webhook by ID
   */
  async get(id: UUID): Promise<Webhook> {
    return request<Webhook>(`/webhooks/${id}`);
  },

  /**
   * Create new webhook
   */
  async create(data: CreateWebhookRequest): Promise<Webhook> {
    return request<Webhook>('/webhooks', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Update webhook
   */
  async update(id: UUID, data: UpdateWebhookRequest): Promise<Webhook> {
    return request<Webhook>(`/webhooks/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete webhook
   */
  async delete(id: UUID): Promise<void> {
    return request<void>(`/webhooks/${id}`, {
      method: 'DELETE',
    });
  },

  /**
   * Test webhook
   */
  async test(id: UUID): Promise<{ success: boolean; status?: number; error?: string }> {
    return request(`/webhooks/${id}/test`, {
      method: 'POST',
    });
  },
};

// ============================================================================
// API Keys API
// ============================================================================

export const apiKeysApi = {
  /**
   * List API keys with optional filtering
   */
  async list(filters?: ApiKeyFilters): Promise<PaginatedResponse<ApiKey>> {
    return request<PaginatedResponse<ApiKey>>('/api-keys', {
      params: filters,
    });
  },

  /**
   * Get API key by ID
   */
  async get(id: UUID): Promise<ApiKey> {
    return request<ApiKey>(`/api-keys/${id}`);
  },

  /**
   * Create new API key
   */
  async create(data: CreateApiKeyRequest): Promise<CreateApiKeyResponse> {
    return request<CreateApiKeyResponse>('/api-keys', {
      method: 'POST',
      body: JSON.stringify({
        ...data,
        organization_id: parseInt(DEFAULT_ORG_ID),
      }),
    });
  },

  /**
   * Update API key
   */
  async update(id: UUID, data: UpdateApiKeyRequest): Promise<ApiKey> {
    return request<ApiKey>(`/api-keys/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  /**
   * Revoke API key
   */
  async revoke(id: UUID): Promise<ApiKey> {
    return this.update(id, { is_active: false });
  },

  /**
   * Delete API key
   */
  async delete(id: UUID): Promise<void> {
    return request<void>(`/api-keys/${id}`, {
      method: 'DELETE',
    });
  },
};

// ============================================================================
// Export unified API
// ============================================================================

export const databaseApi = {
  workflows: workflowsApi,
  executions: executionsApi,
  templates: templatesApi,
  profiles: profilesApi,
  workflowStates: workflowStatesApi,
  webhooks: webhooksApi,
  apiKeys: apiKeysApi,
};

export default databaseApi;

