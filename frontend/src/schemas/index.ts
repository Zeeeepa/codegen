import { z } from 'zod';

/**
 * Zod Schemas for Runtime Type Validation
 * Provides compile-time + runtime type safety for all data structures
 */

// ============================================================================
// Base Schemas
// ============================================================================

export const ApiTokenSchema = z
  .string()
  .min(1, 'API token is required')
  .startsWith('sk-', 'API token must start with "sk-"');

export const OrganizationIdSchema = z
  .string()
  .min(1, 'Organization ID is required');

// ============================================================================
// Workflow & Chain Schemas
// ============================================================================

export const RunStatusSchema = z.enum([
  'pending',
  'running',
  'completed',
  'failed',
  'cancelled',
]);

export const ChainStepTypeSchema = z.enum(['sequential', 'parallel']);

export const SequentialStepSchema = z.object({
  type: z.literal('sequential'),
  prompt: z.string(),
  model: z.string(),
  taskType: z.string().optional(),
  waitForPrevious: z.boolean().optional(),
});

export const ParallelStepSchema = z.object({
  type: z.literal('parallel'),
  branches: z.array(
    z.object({
      prompt: z.string(),
      model: z.string(),
      taskType: z.string().optional(),
    })
  ),
});

export const ChainStepSchema = z.union([
  SequentialStepSchema,
  ParallelStepSchema,
]);

export const ContextStrategySchema = z.enum(['full', 'minimal', 'progressive']);

export const ChainConfigSchema = z.object({
  id: z.number().optional(),
  name: z.string().min(1, 'Chain name is required'),
  description: z.string().optional(),
  steps: z.array(ChainStepSchema),
  contextStrategy: ContextStrategySchema.optional(),
});

// ============================================================================
// Agent Execution Context Schemas
// ============================================================================

export const AgentExecutionStepSchema = z.object({
  stepId: z.string(),
  stepIndex: z.number(),
  stepType: ChainStepTypeSchema,
  status: RunStatusSchema,
  startTime: z.string().datetime().optional(),
  endTime: z.string().datetime().optional(),
  prompt: z.string(),
  model: z.string(),
  result: z.string().optional(),
  error: z.string().optional(),
  tokensUsed: z.number().optional(),
  duration: z.number().optional(), // milliseconds
  retryCount: z.number().default(0),
});

export const AgentContextMetadataSchema = z.object({
  userId: z.string().optional(),
  sessionId: z.string(),
  environment: z.enum(['development', 'staging', 'production']).default('development'),
  version: z.string().default('1.0.0'),
  tags: z.array(z.string()).default([]),
});

export const AgentExecutionContextSchema = z.object({
  executionId: z.string(),
  workflowId: z.string(),
  workflowName: z.string(),
  status: RunStatusSchema,
  currentStepIndex: z.number().default(0),
  totalSteps: z.number(),
  steps: z.array(AgentExecutionStepSchema),
  startTime: z.string().datetime(),
  endTime: z.string().datetime().optional(),
  metadata: AgentContextMetadataSchema,
  error: z.string().optional(),
  summary: z.string().optional(),
  githubPullRequests: z.array(z.string()).default([]),
});

// ============================================================================
// Workflow Run Schemas
// ============================================================================

export const WorkflowRunSchema = z.object({
  id: z.string(),
  workflowId: z.string(),
  workflowName: z.string(),
  status: RunStatusSchema,
  startTime: z.string().datetime(),
  endTime: z.string().datetime().optional(),
  result: z.string().optional(),
  summary: z.string().optional(),
  error: z.string().optional(),
  githubPullRequests: z.array(z.string()).default([]),
  metadata: z.record(z.string(), z.unknown()).optional(),
  executionContext: AgentExecutionContextSchema.optional(),
});

// ============================================================================
// Saved Workflow Schemas
// ============================================================================

export const ReactFlowNodeDataSchema = z.object({
  type: z.string(),
  prompt: z.string(),
  model: z.string(),
  taskType: z.string().optional(),
});

export const ReactFlowNodeSchema = z.object({
  id: z.string(),
  type: z.string(),
  position: z.object({
    x: z.number(),
    y: z.number(),
  }),
  data: ReactFlowNodeDataSchema,
});

export const ReactFlowEdgeSchema = z.object({
  id: z.string(),
  source: z.string(),
  target: z.string(),
  type: z.string().optional(),
});

export const SavedWorkflowSchema = z.object({
  id: z.string(),
  name: z.string().min(1, 'Workflow name is required'),
  description: z.string().optional(),
  nodes: z.array(ReactFlowNodeSchema),
  edges: z.array(ReactFlowEdgeSchema),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
  lastRunId: z.string().optional(),
  runCount: z.number().default(0),
  tags: z.array(z.string()).default([]),
});

// ============================================================================
// API Response Schemas
// ============================================================================

export const AgentRunResponseSchema = z.object({
  id: z.string(),
  status: RunStatusSchema,
  created_at: z.string(),
  updated_at: z.string().optional(),
  result: z.string().optional(),
  error: z.string().optional(),
});

export const RepositorySchema = z.object({
  id: z.string(),
  name: z.string(),
  full_name: z.string(),
  owner: z.string(),
  description: z.string().optional(),
  private: z.boolean(),
});

// ============================================================================
// Settings Schemas
// ============================================================================

export const ApiCredentialsSchema = z.object({
  apiToken: ApiTokenSchema,
  organizationId: OrganizationIdSchema,
});

export const ApiValidationResultSchema = z.object({
  valid: z.boolean(),
  message: z.string().optional(),
  timestamp: z.string().datetime(),
});

// ============================================================================
// Type Exports (Inferred from Schemas)
// ============================================================================

export type ApiToken = z.infer<typeof ApiTokenSchema>;
export type OrganizationId = z.infer<typeof OrganizationIdSchema>;
export type RunStatus = z.infer<typeof RunStatusSchema>;
export type ChainStepType = z.infer<typeof ChainStepTypeSchema>;
export type SequentialStep = z.infer<typeof SequentialStepSchema>;
export type ParallelStep = z.infer<typeof ParallelStepSchema>;
export type ChainStep = z.infer<typeof ChainStepSchema>;
export type ContextStrategy = z.infer<typeof ContextStrategySchema>;
export type ChainConfig = z.infer<typeof ChainConfigSchema>;
export type AgentExecutionStep = z.infer<typeof AgentExecutionStepSchema>;
export type AgentContextMetadata = z.infer<typeof AgentContextMetadataSchema>;
export type AgentExecutionContext = z.infer<typeof AgentExecutionContextSchema>;
export type WorkflowRun = z.infer<typeof WorkflowRunSchema>;
export type ReactFlowNodeData = z.infer<typeof ReactFlowNodeDataSchema>;
export type ReactFlowNode = z.infer<typeof ReactFlowNodeSchema>;
export type ReactFlowEdge = z.infer<typeof ReactFlowEdgeSchema>;
export type SavedWorkflow = z.infer<typeof SavedWorkflowSchema>;
export type AgentRunResponse = z.infer<typeof AgentRunResponseSchema>;
export type Repository = z.infer<typeof RepositorySchema>;
export type ApiCredentials = z.infer<typeof ApiCredentialsSchema>;
export type ApiValidationResult = z.infer<typeof ApiValidationResultSchema>;

// ============================================================================
// Validation Helpers
// ============================================================================

/**
 * Safely parse data with Zod schema and return typed result
 */
export function safeParse<T extends z.ZodType>(
  schema: T,
  data: unknown
): { success: true; data: z.infer<T> } | { success: false; error: z.ZodError } {
  const result = schema.safeParse(data);
  return result;
}

/**
 * Parse and throw on validation error
 */
export function parse<T extends z.ZodType>(schema: T, data: unknown): z.infer<T> {
  return schema.parse(data);
}

/**
 * Validate array of items with schema
 */
export function validateArray<T extends z.ZodType>(
  schema: T,
  items: unknown[]
): z.infer<T>[] {
  return items.map((item) => schema.parse(item));
}

/**
 * Check if data matches schema without throwing
 */
export function isValid<T extends z.ZodType>(
  schema: T,
  data: unknown
): data is z.infer<T> {
  return schema.safeParse(data).success;
}
