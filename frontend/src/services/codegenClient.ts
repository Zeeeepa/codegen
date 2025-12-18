/**
 * Codegen API Client
 * Real API integration for workflows and runs management
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

// API Configuration
// Use proxy in development to avoid CORS issues
const API_BASE_URL = import.meta.env.DEV ? '/api/v1' : 'https://api.codegen.com/v1';

// Types for API responses
export interface Workflow {
  id: string;
  name: string;
  description?: string;
  enabled: boolean;
  status: 'idle' | 'running' | 'paused' | 'stopped';
  last_run?: string;
  created_at: string;
  updated_at: string;
}

export interface ExecutionRun {
  id: string;
  workflow_id: string;
  workflow_name: string;
  status: 'pending' | 'running' | 'success' | 'failure';
  started_at: string;
  completed_at?: string;
  duration?: number;
  logs?: string[];
  context?: Record<string, any>;
}

export interface RunFilters {
  status?: 'all' | 'success' | 'failure' | 'running' | 'pending';
  workflow_id?: string;
  limit?: number;
  offset?: number;
}

export class CodegenAPIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public response?: any
  ) {
    super(message);
    this.name = 'CodegenAPIError';
  }
}

export class CodegenClient {
  private client: AxiosInstance;
  private token: string;
  private orgId: string;

  constructor(token: string, orgId: string) {
    this.token = token;
    this.orgId = orgId;

    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response) {
          throw new CodegenAPIError(
            error.response.data?.message || error.message,
            error.response.status,
            error.response.data
          );
        } else if (error.request) {
          throw new CodegenAPIError('No response from server', undefined, error.request);
        } else {
          throw new CodegenAPIError(error.message);
        }
      }
    );
  }

  /**
   * Fetch all workflows for the organization
   */
  async fetchWorkflows(): Promise<Workflow[]> {
    try {
      const response = await this.client.get(
        `/organizations/${this.orgId}/workflows`
      );
      return response.data.workflows || response.data || [];
    } catch (error) {
      console.error('Error fetching workflows:', error);
      throw error;
    }
  }

  /**
   * Execute a workflow
   */
  async executeWorkflow(workflowId: string): Promise<{ run_id: string }> {
    try {
      const response = await this.client.post(
        `/workflows/${workflowId}/execute`,
        { org_id: this.orgId }
      );
      return response.data;
    } catch (error) {
      console.error(`Error executing workflow ${workflowId}:`, error);
      throw error;
    }
  }

  /**
   * Pause a running workflow
   */
  async pauseWorkflow(workflowId: string): Promise<void> {
    try {
      await this.client.post(`/workflows/${workflowId}/pause`, {
        org_id: this.orgId,
      });
    } catch (error) {
      console.error(`Error pausing workflow ${workflowId}:`, error);
      throw error;
    }
  }

  /**
   * Resume a paused workflow
   */
  async resumeWorkflow(workflowId: string): Promise<void> {
    try {
      await this.client.post(`/workflows/${workflowId}/resume`, {
        org_id: this.orgId,
      });
    } catch (error) {
      console.error(`Error resuming workflow ${workflowId}:`, error);
      throw error;
    }
  }

  /**
   * Stop a workflow
   */
  async stopWorkflow(workflowId: string): Promise<void> {
    try {
      await this.client.post(`/workflows/${workflowId}/stop`, {
        org_id: this.orgId,
      });
    } catch (error) {
      console.error(`Error stopping workflow ${workflowId}:`, error);
      throw error;
    }
  }

  /**
   * Toggle workflow enabled/disabled state
   */
  async toggleWorkflowEnabled(workflowId: string, enabled: boolean): Promise<void> {
    try {
      await this.client.put(`/workflows/${workflowId}/toggle`, {
        org_id: this.orgId,
        enabled,
      });
    } catch (error) {
      console.error(`Error toggling workflow ${workflowId}:`, error);
      throw error;
    }
  }

  /**
   * Fetch all runs with optional filters
   */
  async fetchRuns(filters?: RunFilters): Promise<ExecutionRun[]> {
    try {
      const params: any = {
        org_id: this.orgId,
        ...filters,
      };

      const response = await this.client.get(
        `/organizations/${this.orgId}/runs`,
        { params }
      );
      return response.data.runs || response.data.agent_runs || response.data || [];
    } catch (error) {
      console.error('Error fetching runs:', error);
      throw error;
    }
  }

  /**
   * Get a specific run by ID
   */
  async getRun(runId: string): Promise<ExecutionRun> {
    try {
      const response = await this.client.get(
        `/organizations/${this.orgId}/runs/${runId}`
      );
      return response.data;
    } catch (error) {
      console.error(`Error fetching run ${runId}:`, error);
      throw error;
    }
  }

  /**
   * Get logs for a specific run
   */
  async getRunLogs(runId: string): Promise<string[]> {
    try {
      const response = await this.client.get(
        `/organizations/${this.orgId}/runs/${runId}/logs`
      );
      return response.data.logs || [];
    } catch (error) {
      console.error(`Error fetching logs for run ${runId}:`, error);
      throw error;
    }
  }

  /**
   * Get context/metadata for a specific run
   */
  async getRunContext(runId: string): Promise<Record<string, any>> {
    try {
      const response = await this.client.get(
        `/organizations/${this.orgId}/runs/${runId}/context`
      );
      return response.data.context || response.data || {};
    } catch (error) {
      console.error(`Error fetching context for run ${runId}:`, error);
      throw error;
    }
  }

  /**
   * Retry a failed run
   */
  async retryRun(runId: string): Promise<{ run_id: string }> {
    try {
      const response = await this.client.post(
        `/organizations/${this.orgId}/runs/${runId}/retry`
      );
      return response.data;
    } catch (error) {
      console.error(`Error retrying run ${runId}:`, error);
      throw error;
    }
  }
}

// Singleton instance with environment variables
let clientInstance: CodegenClient | null = null;

export function getCodegenClient(token?: string, orgId?: string): CodegenClient {
  if (!clientInstance || token || orgId) {
    const finalToken = token || import.meta.env.VITE_CODEGEN_TOKEN || '';
    const finalOrgId = orgId || import.meta.env.VITE_CODEGEN_ORG_ID || '';

    if (!finalToken || !finalOrgId) {
      throw new Error('Codegen API credentials not configured');
    }

    clientInstance = new CodegenClient(finalToken, finalOrgId);
  }

  return clientInstance;
}

export default CodegenClient;
