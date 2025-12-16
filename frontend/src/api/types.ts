// API Type Definitions for Controller Dashboard

export interface Workflow {
  id: string;
  name: string;
  description: string;
  status: WorkflowStatus;
  enabled: boolean;
  created_at: string;
  updated_at: string;
  schedule?: string;
  parallel_execution: boolean;
  max_instances: number;
  tags: string[];
  dependencies: string[];
  retry_policy?: RetryPolicy;
  active_executions?: number;
}

export enum WorkflowStatus {
  ENABLED = 'enabled',
  DISABLED = 'disabled',
  RUNNING = 'running',
  ERROR = 'error',
}

export interface RetryPolicy {
  max_retries: number;
  backoff_multiplier: number;
  initial_delay_seconds?: number;
  max_delay_seconds?: number;
}

export interface Sandbox {
  id: string;
  workflow_id: string;
  status: SandboxStatus;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  metrics?: SandboxMetrics;
  resource_usage?: ResourceUsage;
  logs?: string[];
}

export enum SandboxStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  TERMINATED = 'terminated',
}

export interface SandboxMetrics {
  token_usage: number;
  api_calls: number;
  success_rate: number;
  execution_time_ms: number;
  cost_estimate?: number;
}

export interface ResourceUsage {
  cpu_percent: number;
  memory_mb: number;
  network_mbps: number;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  created_at: string;
  workflows: string[];
  team_members: string[];
}

export interface PRD {
  id: string;
  project_id: string;
  title: string;
  content: string;
  version: number;
  created_at: string;
  updated_at: string;
  requirements: Requirement[];
}

export interface Requirement {
  id: string;
  description: string;
  status: 'pending' | 'in-progress' | 'implemented' | 'verified';
  priority: 'low' | 'medium' | 'high' | 'critical';
}

export interface MetricsHistory {
  sandbox_id: string;
  timestamp: string;
  metrics: SandboxMetrics;
  resource_usage: ResourceUsage;
}

export interface DashboardSummary {
  total_workflows: number;
  enabled_workflows: number;
  disabled_workflows: number;
  running_workflows: number;
  active_sandboxes: number;
  total_sandboxes: number;
}

