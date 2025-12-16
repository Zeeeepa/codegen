import axios, { AxiosInstance } from 'axios';
import type {
  Workflow,
  Sandbox,
  Project,
  PRD,
  DashboardSummary,
  MetricsHistory,
} from './types';

class ControllerAPIClient {
  private client: AxiosInstance;

  constructor(baseURL?: string, authToken?: string) {
    this.client = axios.create({
      baseURL: baseURL || import.meta.env.VITE_API_URL || '/api',
      headers: {
        'Content-Type': 'application/json',
        ...(authToken && { Authorization: `Bearer ${authToken}` }),
      },
    });
  }

  // Authentication
  setAuthToken(token: string) {
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  // Workflows
  async getWorkflows(): Promise<Workflow[]> {
    const { data } = await this.client.get('/workflows');
    return data;
  }

  async getWorkflow(workflowId: string): Promise<Workflow> {
    const { data } = await this.client.get(`/workflows/${workflowId}`);
    return data;
  }

  async createWorkflow(workflow: Partial<Workflow>): Promise<Workflow> {
    const { data } = await this.client.post('/workflows', workflow);
    return data;
  }

  async updateWorkflow(
    workflowId: string,
    updates: Partial<Workflow>
  ): Promise<Workflow> {
    const { data } = await this.client.patch(`/workflows/${workflowId}`, updates);
    return data;
  }

  async toggleWorkflow(workflowId: string): Promise<Workflow> {
    const { data } = await this.client.post(`/workflows/${workflowId}/toggle`);
    return data;
  }

  async executeWorkflow(workflowId: string): Promise<Sandbox> {
    const { data } = await this.client.post(`/workflows/${workflowId}/execute`);
    return data;
  }

  async getWorkflowMetrics(workflowId: string): Promise<MetricsHistory[]> {
    const { data } = await this.client.get(`/workflows/${workflowId}/metrics`);
    return data;
  }

  // Sandboxes
  async getSandboxes(): Promise<Sandbox[]> {
    const { data } = await this.client.get('/sandboxes');
    return data;
  }

  async getSandboxStatus(sandboxId: string): Promise<Sandbox> {
    const { data } = await this.client.get(`/sandboxes/${sandboxId}/status`);
    return data;
  }

  async terminateSandbox(sandboxId: string): Promise<void> {
    await this.client.post(`/sandboxes/${sandboxId}/terminate`);
  }

  async getSandboxLogs(sandboxId: string): Promise<string[]> {
    const { data } = await this.client.get(`/sandboxes/${sandboxId}/logs`);
    return data;
  }

  // Projects
  async getProjects(): Promise<Project[]> {
    const { data } = await this.client.get('/projects');
    return data;
  }

  async getProject(projectId: string): Promise<Project> {
    const { data } = await this.client.get(`/projects/${projectId}`);
    return data;
  }

  async createProject(project: Partial<Project>): Promise<Project> {
    const { data } = await this.client.post('/projects', project);
    return data;
  }

  async updateProject(
    projectId: string,
    updates: Partial<Project>
  ): Promise<Project> {
    const { data } = await this.client.patch(`/projects/${projectId}`, updates);
    return data;
  }

  // PRDs
  async getPRDs(): Promise<PRD[]> {
    const { data } = await this.client.get('/prds');
    return data;
  }

  async getPRD(prdId: string): Promise<PRD> {
    const { data } = await this.client.get(`/prds/${prdId}`);
    return data;
  }

  async createPRD(prd: Partial<PRD>): Promise<PRD> {
    const { data } = await this.client.post('/prds', prd);
    return data;
  }

  async updatePRD(prdId: string, updates: Partial<PRD>): Promise<PRD> {
    const { data} = await this.client.patch(`/prds/${prdId}`, updates);
    return data;
  }

  // Dashboard
  async getDashboardSummary(): Promise<DashboardSummary> {
    const { data } = await this.client.get('/dashboard/summary');
    return data;
  }
}

export const apiClient = new ControllerAPIClient();
export default ControllerAPIClient;

