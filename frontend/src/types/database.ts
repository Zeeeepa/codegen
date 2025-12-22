/**
 * Database Types - Matching PostgreSQL Schema
 * These types align with database/schema.sql
 */

// ============================================================================
// Core Database Types
// ============================================================================

export type UUID = string;

export interface DatabaseTimestamps {
  created_at: string;
  updated_at?: string;
}

// ============================================================================
// Workflows Table
// ============================================================================

export interface Workflow extends DatabaseTimestamps {
  id: UUID;
  organization_id: number;
  name: string;
  description?: string;
  definition: WorkflowDefinition; // JSONB
  context?: Record<string, any>; // JSONB
  created_by?: number;
  is_template: boolean;
}

export interface WorkflowDefinition {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface WorkflowNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: Record<string, any>;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  type?: string;
}

export interface CreateWorkflowRequest {
  name: string;
  description?: string;
  definition: WorkflowDefinition;
  context?: Record<string, any>;
  is_template?: boolean;
}

export interface UpdateWorkflowRequest {
  name?: string;
  description?: string;
  definition?: WorkflowDefinition;
  context?: Record<string, any>;
  is_template?: boolean;
}

// ============================================================================
// Executions Table
// ============================================================================

export type ExecutionStatus = 
  | 'IDLE' 
  | 'GENERATING' 
  | 'EVALUATING' 
  | 'PRUNING' 
  | 'EXECUTING' 
  | 'COMPLETED' 
  | 'FAILED';

export interface Execution extends DatabaseTimestamps {
  id: UUID;
  workflow_id: UUID;
  status: ExecutionStatus;
  context?: Record<string, any>; // JSONB
  results?: Record<string, any>; // JSONB
  logs?: string[];
  completed_at?: string;
  error_message?: string;
}

export interface CreateExecutionRequest {
  workflow_id: UUID;
  status?: ExecutionStatus;
  context?: Record<string, any>;
}

export interface UpdateExecutionRequest {
  status?: ExecutionStatus;
  context?: Record<string, any>;
  results?: Record<string, any>;
  logs?: string[];
  error_message?: string;
}

// ============================================================================
// Templates Table
// ============================================================================

export interface Template extends DatabaseTimestamps {
  id: UUID;
  name: string;
  category?: string;
  description?: string;
  definition: WorkflowDefinition; // JSONB
  downloads: number;
  rating: number;
}

export interface CreateTemplateRequest {
  name: string;
  category?: string;
  description?: string;
  definition: WorkflowDefinition;
}

export interface UpdateTemplateRequest {
  name?: string;
  category?: string;
  description?: string;
  definition?: WorkflowDefinition;
}

// ============================================================================
// Profiles Table
// ============================================================================

export type ProfileType = 'agent' | 'workflow' | 'node';

export interface Profile extends DatabaseTimestamps {
  id: UUID;
  name: string;
  type: ProfileType;
  config: Record<string, any>; // JSONB
  rules?: string;
  instructions?: string;
}

export interface CreateProfileRequest {
  name: string;
  type: ProfileType;
  config: Record<string, any>;
  rules?: string;
  instructions?: string;
}

export interface UpdateProfileRequest {
  name?: string;
  type?: ProfileType;
  config?: Record<string, any>;
  rules?: string;
  instructions?: string;
}

// ============================================================================
// Workflow States Table
// ============================================================================

export interface WorkflowState extends DatabaseTimestamps {
  id: UUID;
  workflow_id: UUID;
  execution_id: UUID;
  node_id?: string;
  state: Record<string, any>; // JSONB
}

export interface CreateWorkflowStateRequest {
  workflow_id: UUID;
  execution_id: UUID;
  node_id?: string;
  state: Record<string, any>;
}

// ============================================================================
// Webhooks Table
// ============================================================================

export type WebhookEvent = 
  | 'workflow:created'
  | 'workflow:updated'
  | 'workflow:deleted'
  | 'execution:started'
  | 'execution:completed'
  | 'execution:failed'
  | 'execution:updated';

export interface Webhook extends DatabaseTimestamps {
  id: UUID;
  workflow_id?: UUID;
  url: string;
  events: WebhookEvent[];
  headers?: Record<string, string>; // JSONB
  is_active: boolean;
}

export interface CreateWebhookRequest {
  workflow_id?: UUID;
  url: string;
  events: WebhookEvent[];
  headers?: Record<string, string>;
  is_active?: boolean;
}

export interface UpdateWebhookRequest {
  url?: string;
  events?: WebhookEvent[];
  headers?: Record<string, string>;
  is_active?: boolean;
}

// ============================================================================
// API Keys Table
// ============================================================================

export type ApiKeyScope = 
  | 'workflows:read'
  | 'workflows:write'
  | 'executions:read'
  | 'executions:write'
  | 'templates:read'
  | 'templates:write'
  | 'profiles:read'
  | 'profiles:write'
  | 'webhooks:read'
  | 'webhooks:write'
  | 'admin';

export interface ApiKey extends DatabaseTimestamps {
  id: UUID;
  user_id: number;
  organization_id: number;
  name: string;
  key_hash: string;
  scopes: ApiKeyScope[];
  last_used_at?: string;
  expires_at?: string;
  is_active: boolean;
}

export interface CreateApiKeyRequest {
  name: string;
  scopes: ApiKeyScope[];
  expires_at?: string;
}

export interface CreateApiKeyResponse {
  key: ApiKey;
  plaintext_key: string; // Only returned on creation
}

export interface UpdateApiKeyRequest {
  name?: string;
  scopes?: ApiKeyScope[];
  expires_at?: string;
  is_active?: boolean;
}

// ============================================================================
// Pagination
// ============================================================================

export interface PaginationParams {
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
}

// ============================================================================
// Query Filters
// ============================================================================

export interface WorkflowFilters extends PaginationParams {
  organization_id?: number;
  is_template?: boolean;
  name_contains?: string;
  created_after?: string;
  created_before?: string;
}

export interface ExecutionFilters extends PaginationParams {
  workflow_id?: UUID;
  status?: ExecutionStatus;
  created_after?: string;
  created_before?: string;
}

export interface TemplateFilters extends PaginationParams {
  category?: string;
  name_contains?: string;
  min_rating?: number;
}

export interface ProfileFilters extends PaginationParams {
  type?: ProfileType;
  name_contains?: string;
}

export interface WebhookFilters extends PaginationParams {
  workflow_id?: UUID;
  is_active?: boolean;
}

export interface ApiKeyFilters extends PaginationParams {
  organization_id?: number;
  is_active?: boolean;
  expires_before?: string;
}

