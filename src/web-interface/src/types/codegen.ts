/**
 * TypeScript definitions for Codegen API and domain models
 * Based on existing Codegen API structure and CLI models
 */

// Core API Response Types
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// Authentication Types
export interface AuthToken {
  token: string;
  expires_at?: string;
  user_id?: string;
  organization_id?: string;
}

export interface User {
  id: string;
  email: string;
  name?: string;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
}

// Agent Run Types
export type AgentRunStatus = 
  | 'PENDING'
  | 'RUNNING' 
  | 'COMPLETE'
  | 'FAILED'
  | 'STOPPED'
  | 'CANCELLED';

export type AgentRunSourceType = 'API' | 'SLACK' | 'GITHUB' | 'LINEAR' | 'CLI';

export interface AgentRun {
  id: string;
  organization_id: string;
  user_id: string;
  status: AgentRunStatus;
  source_type: AgentRunSourceType;
  prompt: string;
  summary?: string;
  result?: string;
  model?: string;
  repo_id?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  web_url?: string;
  github_pull_requests?: GitHubPullRequest[];
  error_message?: string;
  progress_percentage?: number;
}

export interface CreateAgentRunInput {
  prompt: string;
  model?: string;
  repo_id?: string;
  organization_id?: string;
}

// Agent Run Logs Types
export type LogMessageType = 
  | 'ACTION'
  | 'PLAN_EVALUATION'
  | 'FINAL_ANSWER'
  | 'ERROR'
  | 'USER_MESSAGE'
  | 'USER_GITHUB_ISSUE_COMMENT'
  | 'INITIAL_PR_GENERATION'
  | 'DETECT_PR_ERRORS'
  | 'FIX_PR_ERRORS'
  | 'PR_CREATION_FAILED'
  | 'PR_EVALUATION'
  | 'COMMIT_EVALUATION'
  | 'AGENT_RUN_LINK';

export interface AgentRunLog {
  agent_run_id: string;
  created_at: string;
  message_type: LogMessageType;
  thought?: string;
  tool_name?: string;
  tool_input?: Record<string, any>;
  tool_output?: Record<string, any>;
  observation?: Record<string, any> | string;
}

export interface AgentRunWithLogs extends AgentRun {
  logs: AgentRunLog[];
  total_logs: number;
  page: number;
  size: number;
  pages: number;
}

// Repository Types
export interface Repository {
  id: string;
  name: string;
  full_name: string;
  description?: string;
  private: boolean;
  html_url: string;
  clone_url: string;
  default_branch: string;
  language?: string;
  created_at: string;
  updated_at: string;
  organization_id: string;
}

export interface CheckSuiteSettings {
  repository_id: string;
  enabled: boolean;
  auto_fix_enabled: boolean;
  pr_review_enabled: boolean;
  created_at: string;
  updated_at: string;
}

// Pull Request Types
export interface GitHubPullRequest {
  id: string;
  number: number;
  title: string;
  body?: string;
  state: 'open' | 'closed' | 'merged';
  url: string;
  html_url: string;
  head_branch_name: string;
  base_branch_name: string;
  created_at: string;
  updated_at: string;
  merged_at?: string;
  author?: {
    login: string;
    avatar_url?: string;
  };
}

// Integration Types
export interface Integration {
  id: string;
  name: string;
  type: 'github' | 'slack' | 'linear' | 'jira' | 'clickup' | 'monday' | 'sentry' | 'circleci';
  enabled: boolean;
  configuration: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// Project Types (for visual workflow management)
export interface Project {
  id: string;
  name: string;
  description?: string;
  organization_id: string;
  repository_ids: string[];
  workflow_template_id?: string;
  status: 'active' | 'paused' | 'completed' | 'archived';
  created_at: string;
  updated_at: string;
  starred: boolean;
  tags: string[];
}

// Workflow Types (for visual pipeline representation)
export interface WorkflowNode {
  id: string;
  type: 'agent' | 'condition' | 'integration' | 'manual';
  position: { x: number; y: number };
  data: {
    label: string;
    description?: string;
    config: Record<string, any>;
  };
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  type?: 'default' | 'conditional';
  data?: {
    condition?: string;
    label?: string;
  };
}

export interface Workflow {
  id: string;
  name: string;
  description?: string;
  project_id: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  status: 'draft' | 'active' | 'paused' | 'completed';
  created_at: string;
  updated_at: string;
  version: number;
}

// Real-time Event Types
export interface RealTimeEvent {
  type: 'agent_run_status_change' | 'agent_run_log' | 'pr_update' | 'workflow_update';
  data: any;
  timestamp: string;
  organization_id: string;
}

// Error Types
export interface CodegenError {
  code: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
}

// State Management Types
export interface AppState {
  auth: {
    user: User | null;
    token: string | null;
    organization: Organization | null;
    isAuthenticated: boolean;
    isLoading: boolean;
  };
  agents: {
    runs: AgentRun[];
    currentRun: AgentRun | null;
    isLoading: boolean;
    error: string | null;
  };
  projects: {
    list: Project[];
    current: Project | null;
    starred: Project[];
    isLoading: boolean;
    error: string | null;
  };
  workflows: {
    list: Workflow[];
    current: Workflow | null;
    isEditing: boolean;
    isLoading: boolean;
    error: string | null;
  };
  ui: {
    sidebarOpen: boolean;
    theme: 'light' | 'dark';
    notifications: Notification[];
    activeView: 'dashboard' | 'agents' | 'projects' | 'workflows' | 'settings';
  };
}

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  actions?: Array<{
    label: string;
    action: () => void;
  }>;
}
