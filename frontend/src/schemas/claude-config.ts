/**
 * Claude Code Configuration Schemas
 * Complete type definitions and validators for Claude Code profiles
 * Based on .claude/ directory structure
 */

import { z } from 'zod';

// ===== Command Schema =====
export const ClaudeCommandSchema = z.object({
  name: z.string().min(1, 'Command name is required'),
  description: z.string().optional(),
  content: z.string().min(1, 'Command content is required'),
  parameters: z.array(z.object({
    name: z.string(),
    description: z.string().optional(),
    required: z.boolean().default(false),
    type: z.enum(['string', 'number', 'boolean', 'array', 'object']).default('string')
  })).optional(),
  examples: z.array(z.string()).optional()
});

export type ClaudeCommand = z.infer<typeof ClaudeCommandSchema>;

// ===== Hook Schema =====
export const ClaudeHookSchema = z.object({
  type: z.enum(['PreToolUse', 'PostToolUse', 'PreCommand', 'PostCommand']),
  matcher: z.string().min(1, 'Hook matcher is required'),
  command: z.string().min(1, 'Hook command is required'),
  timeout: z.number().default(5),
  continueOnError: z.boolean().default(false)
});

export type ClaudeHook = z.infer<typeof ClaudeHookSchema>;

// ===== MCP (Model Context Protocol) Schema =====
export const ClaudeMCPSchema = z.object({
  name: z.string().min(1, 'MCP name is required'),
  command: z.string().min(1, 'MCP command is required'),
  args: z.array(z.string()).default([]),
  env: z.record(z.string()).optional(),
  disabled: z.boolean().default(false)
});

export type ClaudeMCP = z.infer<typeof ClaudeMCPSchema>;

// ===== Plugin Schema =====
export const ClaudePluginSchema = z.object({
  name: z.string().min(1, 'Plugin name is required'),
  version: z.string().optional(),
  enabled: z.boolean().default(true),
  config: z.record(z.any()).optional()
});

export type ClaudePlugin = z.infer<typeof ClaudePluginSchema>;

// ===== Skill Schema =====
export const ClaudeSkillSchema = z.object({
  name: z.string().min(1, 'Skill name is required'),
  description: z.string().optional(),
  implementation: z.string().min(1, 'Skill implementation is required'),
  dependencies: z.array(z.string()).default([]),
  examples: z.array(z.string()).optional()
});

export type ClaudeSkill = z.infer<typeof ClaudeSkillSchema>;

// ===== Settings Schema =====
export const ClaudeSettingsSchema = z.object({
  permissions: z.object({
    allow: z.array(z.string()).default([]),
    deny: z.array(z.string()).default([])
  }).optional(),
  preferences: z.record(z.any()).optional(),
  model: z.enum(['sonnet', 'opus', 'haiku', 'claude-3-sonnet', 'claude-3-opus', 'claude-3-haiku']).default('sonnet'),
  temperature: z.number().min(0).max(1).optional(),
  maxTokens: z.number().positive().optional()
});

export type ClaudeSettings = z.infer<typeof ClaudeSettingsSchema>;

// ===== Agent Schema =====
export const ClaudeAgentSchema = z.object({
  name: z.string().min(1, 'Agent name is required'),
  description: z.string().optional(),
  tools: z.array(z.enum(['Read', 'Write', 'Edit', 'Bash', 'WebSearch', 'WebFetch'])).default(['Read', 'Write']),
  model: z.enum(['sonnet', 'opus', 'haiku']).default('sonnet'),
  systemPrompt: z.string().optional(),
  focusAreas: z.array(z.string()).default([]),
  approach: z.array(z.string()).default([]),
  outputGuidelines: z.array(z.string()).default([])
});

export type ClaudeAgent = z.infer<typeof ClaudeAgentSchema>;

// ===== Advanced Profile Schema =====
export const ProfileAdvancedSchema = z.object({
  // Basic Info (from Feature 1)
  id: z.string().optional(),
  name: z.string().min(1, 'Profile name is required'),
  description: z.string().optional(),
  role: z.enum([
    'custom',
    'frontend',
    'backend',
    'fullstack',
    'devops',
    'testing',
    'security',
    'data',
    'ml',
    'mobile'
  ]).default('custom'),
  
  // Advanced Configuration
  type: z.enum(['basic', 'advanced']).default('basic'),
  
  // Commands
  commands: z.array(ClaudeCommandSchema).default([]),
  
  // Hooks
  hooks: z.object({
    PreToolUse: z.array(ClaudeHookSchema).default([]),
    PostToolUse: z.array(ClaudeHookSchema).default([]),
    PreCommand: z.array(ClaudeHookSchema).default([]),
    PostCommand: z.array(ClaudeHookSchema).default([])
  }).optional(),
  
  // MCPs
  mcps: z.array(ClaudeMCPSchema).default([]),
  
  // Plugins
  plugins: z.array(ClaudePluginSchema).default([]),
  
  // Skills
  skills: z.array(ClaudeSkillSchema).default([]),
  
  // Settings
  settings: ClaudeSettingsSchema.optional(),
  
  // Agent Configuration
  agent: ClaudeAgentSchema.optional(),
  
  // Metadata
  createdAt: z.string().optional(),
  updatedAt: z.string().optional(),
  author: z.string().optional(),
  version: z.string().default('1.0.0'),
  tags: z.array(z.string()).default([]),
  
  // CI/CD Integration
  cicd: z.object({
    enabled: z.boolean().default(false),
    autoSync: z.boolean().default(false),
    syncOnChange: z.boolean().default(false),
    lastSync: z.string().optional()
  }).optional()
});

export type ProfileAdvanced = z.infer<typeof ProfileAdvancedSchema>;

// ===== Template Schema =====
export const ProfileTemplateSchema = z.object({
  id: z.string(),
  name: z.string().min(1),
  description: z.string(),
  category: z.enum(['frontend', 'backend', 'fullstack', 'devops', 'testing', 'other']),
  author: z.string().optional(),
  version: z.string().default('1.0.0'),
  profile: ProfileAdvancedSchema,
  preview: z.object({
    commandsCount: z.number(),
    hooksCount: z.number(),
    mcpsCount: z.number(),
    skillsCount: z.number()
  }).optional()
});

export type ProfileTemplate = z.infer<typeof ProfileTemplateSchema>;

// ===== Export Format Schema (.claude directory) =====
export const ClaudeExportSchema = z.object({
  settings: ClaudeSettingsSchema,
  agents: z.array(ClaudeAgentSchema).default([]),
  commands: z.array(ClaudeCommandSchema).default([]),
  mcps: z.record(ClaudeMCPSchema).optional(),
  hooks: z.object({
    PreToolUse: z.array(ClaudeHookSchema).default([]),
    PostToolUse: z.array(ClaudeHookSchema).default([]),
    PreCommand: z.array(ClaudeHookSchema).default([]),
    PostCommand: z.array(ClaudeHookSchema).default([])
  }).optional()
});

export type ClaudeExport = z.infer<typeof ClaudeExportSchema>;

// ===== Validation Helpers =====

export function validateCommand(data: unknown): ClaudeCommand {
  return ClaudeCommandSchema.parse(data);
}

export function validateHook(data: unknown): ClaudeHook {
  return ClaudeHookSchema.parse(data);
}

export function validateMCP(data: unknown): ClaudeMCP {
  return ClaudeMCPSchema.parse(data);
}

export function validatePlugin(data: unknown): ClaudePlugin {
  return ClaudePluginSchema.parse(data);
}

export function validateSkill(data: unknown): ClaudeSkill {
  return ClaudeSkillSchema.parse(data);
}

export function validateSettings(data: unknown): ClaudeSettings {
  return ClaudeSettingsSchema.parse(data);
}

export function validateAgent(data: unknown): ClaudeAgent {
  return ClaudeAgentSchema.parse(data);
}

export function validateProfileAdvanced(data: unknown): ProfileAdvanced {
  return ProfileAdvancedSchema.parse(data);
}

export function validateTemplate(data: unknown): ProfileTemplate {
  return ProfileTemplateSchema.parse(data);
}

export function validateClaudeExport(data: unknown): ClaudeExport {
  return ClaudeExportSchema.parse(data);
}

// ===== Type Guards =====

export function isAdvancedProfile(profile: any): profile is ProfileAdvanced {
  return profile.type === 'advanced' || 
         profile.commands || 
         profile.hooks || 
         profile.mcps || 
         profile.skills;
}

export function hasCommands(profile: ProfileAdvanced): boolean {
  return profile.commands && profile.commands.length > 0;
}

export function hasHooks(profile: ProfileAdvanced): boolean {
  return !!profile.hooks && (
    (profile.hooks.PreToolUse && profile.hooks.PreToolUse.length > 0) ||
    (profile.hooks.PostToolUse && profile.hooks.PostToolUse.length > 0) ||
    (profile.hooks.PreCommand && profile.hooks.PreCommand.length > 0) ||
    (profile.hooks.PostCommand && profile.hooks.PostCommand.length > 0)
  );
}

export function hasMCPs(profile: ProfileAdvanced): boolean {
  return profile.mcps && profile.mcps.length > 0;
}

export function hasSkills(profile: ProfileAdvanced): boolean {
  return profile.skills && profile.skills.length > 0;
}

// ===== Default Values =====

export const DEFAULT_PROFILE_ADVANCED: Partial<ProfileAdvanced> = {
  type: 'advanced',
  commands: [],
  hooks: {
    PreToolUse: [],
    PostToolUse: [],
    PreCommand: [],
    PostCommand: []
  },
  mcps: [],
  plugins: [],
  skills: [],
  settings: {
    permissions: {
      allow: ['Read', 'Write', 'Edit', 'Bash'],
      deny: []
    },
    model: 'sonnet'
  },
  version: '1.0.0',
  tags: [],
  cicd: {
    enabled: false,
    autoSync: false,
    syncOnChange: false
  }
};

