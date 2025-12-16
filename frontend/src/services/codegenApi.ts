/**
 * Codegen REST API Service - Environment-Based Configuration
 * 
 * Configuration via environment variables:
 * - VITE_CODEGEN_API_BASE: API base URL (default: https://api.codegen.com/v1)
 * - VITE_CODEGEN_ORG_ID: Organization ID (required)
 * - VITE_CODEGEN_API_TOKEN: API authentication token (required)
 */

const CODEGEN_API_BASE = import.meta.env.VITE_CODEGEN_API_BASE || 'https://api.codegen.com/v1';
const ORG_ID = import.meta.env.VITE_CODEGEN_ORG_ID;
const API_TOKEN = import.meta.env.VITE_CODEGEN_API_TOKEN;

// Validate required environment variables at module load time
if (!ORG_ID) {
  throw new Error(
    'VITE_CODEGEN_ORG_ID environment variable is required. ' +
    'Please set it in your .env.local file.'
  );
}

if (!API_TOKEN) {
  throw new Error(
    'VITE_CODEGEN_API_TOKEN environment variable is required. ' +
    'Please set it in your .env.local file.'
  );
}

// ============================================================================
// Types
// ============================================================================

export interface Repository {
  id: number;
  name: string;
  full_name: string;
  description?: string;
  github_id?: string;
  organization_id: number;
  visibility?: string;
  archived: boolean;
  setup_status?: string;
  language?: string;
}

export interface RepositoriesResponse {
  items: Repository[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface CreateAgentRunRequest {
  task: string;
  context?: Record<string, any>;
  metadata?: Record<string, any>;
  repo_id?: number;  // Updated to number to match API
  model?: string;
}

export interface CreateAgentRunResponse {
  agentRunId: string;
  status: string;
  createdAt: number;
}

export interface AgentRunStatusResponse {
  agentRunId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: string;
  error?: string;
  progress?: number;
  updatedAt: number;
}

export interface ResumeAgentRunRequest {
  task: string;
  context?: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface ResumeAgentRunResponse {
  agentRunId: string;
  status: string;
  updatedAt: number;
}

// ============================================================================
// API Functions - REAL IMPLEMENTATION
// ============================================================================

/**
 * Create a new agent run - REAL API CALL
 * 
 * POST /organizations/{orgId}/agent/run
 */
export async function createAgentRun(
  orgId: string = ORG_ID,
  token: string = API_TOKEN,
  request: CreateAgentRunRequest
): Promise<CreateAgentRunResponse> {
  console.log('[CodegenAPI] Creating agent run:', {
    orgId,
    task: request.task.substring(0, 100) + '...',
    model: request.model || 'default'
  });

  const response = await fetch(`${CODEGEN_API_BASE}/organizations/${orgId}/agent/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'X-Organization-Id': orgId,
    },
    body: JSON.stringify({
      prompt: request.task,
      model: request.model || 'Sonnet 4.5',
      agent_type: 'codegen',
      repo_id: request.repo_id || request.metadata?.repository,
      context: request.context,
      metadata: request.metadata
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('[CodegenAPI] Create run failed:', {
      status: response.status,
      statusText: response.statusText,
      body: errorText
    });
    throw new Error(`Failed to create agent run: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  console.log('[CodegenAPI] Agent run created:', data);

  return {
    agentRunId: data.id || data.agent_run_id || data.runId,
    status: data.status || 'pending',
    createdAt: Date.now()
  };
}

/**
 * Get agent run status - REAL API CALL
 * 
 * GET /organizations/{orgId}/agent/run/{runId}
 */
export async function getAgentRunStatus(
  orgId: string = ORG_ID,
  token: string = API_TOKEN,
  agentRunId: string
): Promise<AgentRunStatusResponse> {
  console.log('[CodegenAPI] Polling status:', { orgId, agentRunId });

  const response = await fetch(
    `${CODEGEN_API_BASE}/organizations/${orgId}/agent/run/${agentRunId}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Organization-Id': orgId,
      },
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    console.error('[CodegenAPI] Status check failed:', {
      status: response.status,
      statusText: response.statusText,
      body: errorText
    });
    throw new Error(`Failed to get agent run status: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  console.log('[CodegenAPI] Status received:', {
    agentRunId,
    status: data.status,
    hasResult: !!data.result
  });

  return {
    agentRunId: data.id || data.agent_run_id || agentRunId,
    status: data.status || 'pending',
    result: data.result || data.output,
    error: data.error || data.error_message,
    progress: data.progress,
    updatedAt: Date.now()
  };
}

/**
 * Resume agent run with next task - REAL API CALL
 * 
 * POST /organizations/{orgId}/agent/run/resume
 * 
 * THE CORE PATTERN: After polling shows "completed", resume with next task
 */
export async function resumeAgentRun(
  orgId: string = ORG_ID,
  token: string = API_TOKEN,
  agentRunId: string,
  request: ResumeAgentRunRequest
): Promise<ResumeAgentRunResponse> {
  console.log('[CodegenAPI] Resuming agent run:', {
    orgId,
    agentRunId,
    task: request.task.substring(0, 100) + '...'
  });

  const response = await fetch(
    `${CODEGEN_API_BASE}/organizations/${orgId}/agent/run/resume`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'X-Organization-Id': orgId,
      },
      body: JSON.stringify({
        agent_run_id: agentRunId,
        prompt: request.task,
        context: request.context,
        metadata: request.metadata
      }),
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    console.error('[CodegenAPI] Resume failed:', {
      status: response.status,
      statusText: response.statusText,
      body: errorText
    });
    throw new Error(`Failed to resume agent run: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  console.log('[CodegenAPI] Agent run resumed:', data);

  return {
    agentRunId: data.id || data.agent_run_id || agentRunId,
    status: data.status || 'running',
    updatedAt: Date.now()
  };
}

/**
 * Cancel agent run - REAL API CALL
 * 
 * POST /organizations/{orgId}/agent/run/{runId}/cancel
 */
export async function cancelAgentRun(
  orgId: string = ORG_ID,
  token: string = API_TOKEN,
  agentRunId: string
): Promise<void> {
  console.log('[CodegenAPI] Cancelling agent run:', { orgId, agentRunId });

  const response = await fetch(
    `${CODEGEN_API_BASE}/organizations/${orgId}/agent/run/${agentRunId}/cancel`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Organization-Id': orgId,
      },
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    console.error('[CodegenAPI] Cancel failed:', {
      status: response.status,
      statusText: response.statusText,
      body: errorText
    });
    throw new Error(`Failed to cancel agent run: ${response.status} ${errorText}`);
  }

  console.log('[CodegenAPI] Agent run cancelled');
}

/**
 * List repositories - REAL API CALL
 * 
 * GET /v1/organizations/{orgId}/repos
 */
export async function listRepositories(
  orgId: string = ORG_ID,
  token: string = API_TOKEN,
  skip: number = 0,
  limit: number = 100
): Promise<RepositoriesResponse> {
  console.log('[CodegenAPI] Fetching repositories:', { orgId, skip, limit });

  const response = await fetch(
    `${CODEGEN_API_BASE}/organizations/${orgId}/repos?skip=${skip}&limit=${limit}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Organization-Id': orgId,
      },
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    console.error('[CodegenAPI] List repos failed:', {
      status: response.status,
      statusText: response.statusText,
      body: errorText
    });
    throw new Error(`Failed to list repositories: ${response.status} ${errorText}`);
  }

  const data: RepositoriesResponse = await response.json();
  console.log('[CodegenAPI] Repositories loaded:', data.total, 'total,', data.items.length, 'in page');

  return data;
}

/**
 * Test API connection - REAL API CALL
 */
export async function testConnection(
  orgId: string = ORG_ID,
  token: string = API_TOKEN
): Promise<{ success: boolean; message: string }> {
  try {
    console.log('[CodegenAPI] Testing connection...', { orgId });
    
    const repos = await listRepositories(orgId, token);
    
    return {
      success: true,
      message: `Connected successfully! Found ${repos.length} repositories.`
    };
  } catch (error: any) {
    console.error('[CodegenAPI] Connection test failed:', error);
    return {
      success: false,
      message: error.message || 'Connection failed'
    };
  }
}

// ============================================================================
// Export configured instances
// ============================================================================

export const codegenApi = {
  createAgentRun: (request: CreateAgentRunRequest) => 
    createAgentRun(ORG_ID, API_TOKEN, request),
  
  getAgentRunStatus: (agentRunId: string) => 
    getAgentRunStatus(ORG_ID, API_TOKEN, agentRunId),
  
  resumeAgentRun: (agentRunId: string, request: ResumeAgentRunRequest) => 
    resumeAgentRun(ORG_ID, API_TOKEN, agentRunId, request),
  
  cancelAgentRun: (agentRunId: string) => 
    cancelAgentRun(ORG_ID, API_TOKEN, agentRunId),
  
  listRepositories: () => 
    listRepositories(ORG_ID, API_TOKEN),
  
  testConnection: () => 
    testConnection(ORG_ID, API_TOKEN)
};
