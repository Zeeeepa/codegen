import { z } from 'zod';

// Profile schemas
export const ProfileRoleSchema = z.enum([
  'researcher',
  'developer',
  'analyst',
  'qa-engineer',
  'devops',
  'security',
  'api-manager',
  'custom'
]);

export const CreateProfileSchema = z.object({
  name: z.string().min(1).max(255),
  role: ProfileRoleSchema,
  description: z.string().optional()
});

export const UpdateProfileSchema = z.object({
  name: z.string().min(1).max(255).optional(),
  role: ProfileRoleSchema.optional(),
  description: z.string().optional(),
  isActive: z.boolean().optional()
});

// Template schemas
export const CreateTemplateSchema = z.object({
  name: z.string().min(1).max(255),
  category: z.string().optional(),
  description: z.string().optional(),
  systemPrompt: z.string().optional(),
  userPrompt: z.string().optional(),
  variables: z.array(z.string()).default([]),
  tags: z.array(z.string()).default([]),
  isPublic: z.boolean().default(true)
});

export const UpdateTemplateSchema = CreateTemplateSchema.partial();

// MCP Tool schemas
export const CreateMcpToolSchema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().optional(),
  repoUrl: z.string().url().optional(),
  docsUrl: z.string().url().optional(),
  installCommands: z.array(z.string()).default([]),
  runCommands: z.array(z.string()).default([]),
  envVarsSchema: z.record(z.any()).optional(),
  healthcheck: z.string().optional(),
  instructions: z.string().optional(),
  version: z.string().optional()
});

export const UpdateMcpToolSchema = CreateMcpToolSchema.partial();

// Task Template schemas
export const CreateTaskTemplateSchema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().optional(),
  steps: z.array(z.any()).default([]),
  config: z.record(z.any()).optional()
});

export const UpdateTaskTemplateSchema = CreateTaskTemplateSchema.partial();

// Sandbox schemas
export const CreateSandboxSchema = z.object({
  profileId: z.string().uuid(),
  name: z.string().min(1).max(255),
  setupCommands: z.array(z.string()).default([]),
  env: z.record(z.string()).default({})
});

export const UpdateSandboxSchema = z.object({
  name: z.string().min(1).max(255).optional(),
  setupCommands: z.array(z.string()).optional(),
  env: z.record(z.string()).optional(),
  status: z.enum(['pending', 'ready', 'error']).optional()
});

// Context application schemas
export const ContextApplicationSchema = z.object({
  profileId: z.string().uuid(),
  templateId: z.string().uuid().optional(),
  variables: z.record(z.any()).default({}),
  preview: z.boolean().default(false)
});

// Export types
export type ProfileRole = z.infer<typeof ProfileRoleSchema>;
export type CreateProfileInput = z.infer<typeof CreateProfileSchema>;
export type UpdateProfileInput = z.infer<typeof UpdateProfileSchema>;
export type CreateTemplateInput = z.infer<typeof CreateTemplateSchema>;
export type UpdateTemplateInput = z.infer<typeof UpdateTemplateSchema>;
export type CreateMcpToolInput = z.infer<typeof CreateMcpToolSchema>;
export type UpdateMcpToolInput = z.infer<typeof UpdateMcpToolSchema>;
export type CreateTaskTemplateInput = z.infer<typeof CreateTaskTemplateSchema>;
export type UpdateTaskTemplateInput = z.infer<typeof UpdateTaskTemplateSchema>;
export type CreateSandboxInput = z.infer<typeof CreateSandboxSchema>;
export type UpdateSandboxInput = z.infer<typeof UpdateSandboxSchema>;
export type ContextApplicationInput = z.infer<typeof ContextApplicationSchema>;

