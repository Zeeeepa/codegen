import axios, { AxiosInstance } from 'axios';
import { Repository, AgentRun } from '@/types';

const API_BASE = 'https://api.codegen.com/v1';

class CodeGenAPI {
  private static instance: CodeGenAPI;
  private client: AxiosInstance;

  private constructor() {
    this.client = axios.create({
      baseURL: API_BASE,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  static getInstance(): CodeGenAPI {
    if (!CodeGenAPI.instance) {
      CodeGenAPI.instance = new CodeGenAPI();
    }
    return CodeGenAPI.instance;
  }

  private getHeaders(apiKey: string) {
    return {
      Authorization: `Bearer ${apiKey}`,
    };
  }

  async fetchRepos(orgId: string, apiKey: string): Promise<Repository[]> {
    const response = await this.client.get(
      `/organizations/${orgId}/repositories`,
      { headers: this.getHeaders(apiKey) }
    );
    return response.data.repositories || [];
  }

  async fetchAllRuns(orgId: string, apiKey: string): Promise<AgentRun[]> {
    const response = await this.client.get(
      `/organizations/${orgId}/agent/runs`,
      { headers: this.getHeaders(apiKey) }
    );
    return response.data.agent_runs || [];
  }

  async getRunDetails(orgId: string, apiKey: string, runId: string): Promise<AgentRun> {
    const response = await this.client.get(
      `/organizations/${orgId}/agent/run/${runId}`,
      { headers: this.getHeaders(apiKey) }
    );
    return response.data;
  }

  async createRun(
    orgId: string,
    apiKey: string,
    prompt: string,
    model: string,
    repoId?: string
  ): Promise<AgentRun> {
    const payload: any = {
      prompt,
      model,
      agent_type: 'codegen',
    };

    if (repoId) {
      payload.repo_id = parseInt(repoId);
    }

    const response = await this.client.post(
      `/organizations/${orgId}/agent/run`,
      payload,
      { headers: this.getHeaders(apiKey) }
    );

    return response.data;
  }

  async resumeRun(
    orgId: string,
    apiKey: string,
    runId: string,
    prompt: string
  ): Promise<void> {
    await this.client.post(
      `/organizations/${orgId}/agent/run/resume`,
      {
        agent_run_id: runId,
        prompt,
      },
      { headers: this.getHeaders(apiKey) }
    );
  }
}

export const codegenApi = CodeGenAPI.getInstance();

