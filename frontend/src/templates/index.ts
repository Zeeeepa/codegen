/**
 * Template System for Claude Code Profiles
 * Provides pre-built profile templates for common developer roles
 */

import { ProfileTemplate } from '../schemas/claude-config';
import frontendDeveloper from './frontend-developer.json';
import backendDeveloper from './backend-developer.json';
import mcpExpert from './mcp-expert.json';

// Export chain templates
export { chainTemplates } from './chainTemplates';
export * from './productionTemplates';

// Template registry
export const TEMPLATES: ProfileTemplate[] = [
  frontendDeveloper as ProfileTemplate,
  backendDeveloper as ProfileTemplate,
  mcpExpert as ProfileTemplate
];

/**
 * Get all available templates
 */
export function getAllTemplates(): ProfileTemplate[] {
  return TEMPLATES;
}

/**
 * Get template by ID
 */
export function getTemplateById(id: string): ProfileTemplate | undefined {
  return TEMPLATES.find(t => t.id === id);
}

/**
 * Get templates by category
 */
export function getTemplatesByCategory(category: string): ProfileTemplate[] {
  return TEMPLATES.filter(t => t.category === category);
}

/**
 * Search templates by name or description
 */
export function searchTemplates(query: string): ProfileTemplate[] {
  const lowerQuery = query.toLowerCase();
  return TEMPLATES.filter(t => 
    t.name.toLowerCase().includes(lowerQuery) ||
    t.description.toLowerCase().includes(lowerQuery) ||
    t.profile.tags?.some(tag => tag.toLowerCase().includes(lowerQuery))
  );
}

/**
 * Get template categories
 */
export function getTemplateCategories(): string[] {
  return Array.from(new Set(TEMPLATES.map(t => t.category)));
}

/**
 * Clone template profile (deep copy)
 */
export function cloneTemplateProfile(template: ProfileTemplate) {
  return JSON.parse(JSON.stringify(template.profile));
}

/**
 * Apply template to create new profile
 */
export function applyTemplate(
  templateId: string,
  overrides?: Partial<ProfileTemplate['profile']>
): ProfileTemplate['profile'] | null {
  const template = getTemplateById(templateId);
  if (!template) {
    return null;
  }

  const baseProfile = cloneTemplateProfile(template);
  
  // Apply overrides
  if (overrides) {
    return {
      ...baseProfile,
      ...overrides,
      // Generate new ID and timestamps
      id: `profile_${Date.now()}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
  }

  return {
    ...baseProfile,
    id: `profile_${Date.now()}`,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };
}

/**
 * Get template preview statistics
 */
export function getTemplatePreview(template: ProfileTemplate) {
  const profile = template.profile;
  
  return {
    commandsCount: profile.commands?.length || 0,
    hooksCount: Object.values(profile.hooks || {}).flat().length || 0,
    mcpsCount: profile.mcps?.length || 0,
    skillsCount: profile.skills?.length || 0,
    pluginsCount: profile.plugins?.length || 0,
    hasAgent: !!profile.agent,
    hasSettings: !!profile.settings,
    model: profile.settings?.model || profile.agent?.model || 'sonnet',
    tools: profile.agent?.tools || []
  };
}

/**
 * Export template categories enum
 */
export enum TemplateCategory {
  FRONTEND = 'frontend',
  BACKEND = 'backend',
  FULLSTACK = 'fullstack',
  DEVOPS = 'devops',
  TESTING = 'testing',
  OTHER = 'other'
}

/**
 * Template metadata
 */
export interface TemplateMetadata {
  id: string;
  name: string;
  description: string;
  category: string;
  author?: string;
  version: string;
  tags: string[];
  preview: ReturnType<typeof getTemplatePreview>;
}

/**
 * Get template metadata without full profile
 */
export function getTemplateMetadata(templateId: string): TemplateMetadata | null {
  const template = getTemplateById(templateId);
  if (!template) {
    return null;
  }

  return {
    id: template.id,
    name: template.name,
    description: template.description,
    category: template.category,
    author: template.author,
    version: template.version,
    tags: template.profile.tags || [],
    preview: getTemplatePreview(template)
  };
}

/**
 * Get all templates metadata
 */
export function getAllTemplatesMetadata(): TemplateMetadata[] {
  return TEMPLATES.map(t => ({
    id: t.id,
    name: t.name,
    description: t.description,
    category: t.category,
    author: t.author,
    version: t.version,
    tags: t.profile.tags || [],
    preview: getTemplatePreview(t)
  }));
}

// Default export
export default {
  getAllTemplates,
  getTemplateById,
  getTemplatesByCategory,
  searchTemplates,
  getTemplateCategories,
  applyTemplate,
  getTemplatePreview,
  getTemplateMetadata,
  getAllTemplatesMetadata
};
