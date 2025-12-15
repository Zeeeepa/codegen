/**
 * Claude Import Utility
 * Imports profiles from .claude directory format or JSON
 */

import JSZip from 'jszip';
import { ProfileAdvanced, ClaudeExport, validateClaudeExport, ClaudeAgent, ClaudeCommand } from '../schemas/claude-config';

/**
 * Parse agent markdown file
 */
function parseAgentMarkdown(content: string): Partial<ClaudeAgent> | null {
  try {
    // Extract frontmatter
    const frontmatterMatch = content.match(/---\n([\s\S]*?)\n---/);
    if (!frontmatterMatch) {
      return null;
    }

    const frontmatter = frontmatterMatch[1];
    const body = content.substring(frontmatterMatch[0].length).trim();

    // Parse frontmatter
    const agent: Partial<ClaudeAgent> = {
      focusAreas: [],
      approach: [],
      outputGuidelines: []
    };

    frontmatter.split('\n').forEach(line => {
      const [key, value] = line.split(':').map(s => s.trim());
      if (key === 'name') agent.name = value;
      if (key === 'description') agent.description = value;
      if (key === 'tools') agent.tools = value.split(',').map(t => t.trim()) as any;
      if (key === 'model') agent.model = value as any;
    });

    // Parse body sections
    const systemPromptMatch = body.match(/^([\s\S]*?)##/);
    if (systemPromptMatch) {
      agent.systemPrompt = systemPromptMatch[1].trim();
    }

    const focusAreasMatch = body.match(/## Focus Areas\n([\s\S]*?)##/);
    if (focusAreasMatch) {
      agent.focusAreas = focusAreasMatch[1]
        .split('\n')
        .filter(line => line.trim().startsWith('-'))
        .map(line => line.replace(/^-\s*/, '').trim());
    }

    const approachMatch = body.match(/## Approach\n([\s\S]*?)##/);
    if (approachMatch) {
      agent.approach = approachMatch[1]
        .split('\n')
        .filter(line => line.match(/^\d+\./))
        .map(line => line.replace(/^\d+\.\s*/, '').trim());
    }

    const outputMatch = body.match(/## Output\n([\s\S]*?)(?:##|$)/);
    if (outputMatch) {
      agent.outputGuidelines = outputMatch[1]
        .split('\n')
        .filter(line => line.trim().startsWith('-'))
        .map(line => line.replace(/^-\s*/, '').trim());
    }

    return agent;
  } catch (error) {
    console.error('Error parsing agent markdown:', error);
    return null;
  }
}

/**
 * Parse command markdown file
 */
function parseCommandMarkdown(content: string, filename: string): Partial<ClaudeCommand> | null {
  try {
    const lines = content.split('\n');
    const name = filename.replace('.md', '');
    
    let description = '';
    let commandContent = '';
    
    // Find first heading (command name)
    const nameMatch = content.match(/^# (.+)$/m);
    if (nameMatch) {
      // Description is the content before ## Purpose
      const descMatch = content.match(/^# .+\n\n([\s\S]*?)(?:##|$)/);
      if (descMatch) {
        description = descMatch[1].trim();
      }
    }

    // Extract content (everything between ## Purpose and ## Examples or end)
    const contentMatch = content.match(/## Purpose\n\n([\s\S]*?)(?:##|$)/);
    if (contentMatch) {
      commandContent = contentMatch[1].trim();
    }

    return {
      name,
      description: description || undefined,
      content: commandContent || content
    };
  } catch (error) {
    console.error('Error parsing command markdown:', error);
    return null;
  }
}

/**
 * Import from ZIP file
 */
export async function importFromZip(file: File): Promise<ProfileAdvanced> {
  const zip = await JSZip.loadAsync(file);
  
  const profile: Partial<ProfileAdvanced> = {
    type: 'advanced',
    commands: [],
    hooks: {
      PreToolUse: [],
      PostToolUse: [],
      PreCommand: [],
      PostCommand: []
    },
    mcps: [],
    skills: [],
    plugins: [],
    tags: [],
    version: '1.0.0'
  };

  // Parse settings.local.json
  const settingsFile = zip.file('.claude/settings.local.json');
  if (settingsFile) {
    const settingsContent = await settingsFile.async('string');
    const settings = JSON.parse(settingsContent);
    profile.settings = {
      permissions: settings.permissions,
      preferences: settings.preferences,
      model: settings.model || 'sonnet'
    };
    profile.hooks = settings.hooks || profile.hooks;
  }

  // Parse .mcp.json
  const mcpFile = zip.file('.mcp.json');
  if (mcpFile) {
    const mcpContent = await mcpFile.async('string');
    const mcpConfig = JSON.parse(mcpContent);
    
    if (mcpConfig.mcpServers) {
      profile.mcps = Object.entries(mcpConfig.mcpServers).map(([name, config]: [string, any]) => ({
        name,
        command: config.command,
        args: config.args || [],
        env: config.env || {}
      }));
    }
  }

  // Parse agents
  const agentsFolder = zip.folder('.claude/agents');
  if (agentsFolder) {
    const agentFiles = Object.keys(zip.files).filter(name => name.startsWith('.claude/agents/') && name.endsWith('.md'));
    
    if (agentFiles.length > 0) {
      const agentFile = zip.file(agentFiles[0]);
      if (agentFile) {
        const agentContent = await agentFile.async('string');
        const agentData = parseAgentMarkdown(agentContent);
        if (agentData) {
          profile.agent = agentData as ClaudeAgent;
        }
      }
    }
  }

  // Parse commands
  const commandsFolder = zip.folder('.claude/commands');
  if (commandsFolder) {
    const commandFiles = Object.keys(zip.files).filter(name => name.startsWith('.claude/commands/') && name.endsWith('.md'));
    
    for (const commandPath of commandFiles) {
      const commandFile = zip.file(commandPath);
      if (commandFile) {
        const commandContent = await commandFile.async('string');
        const filename = commandPath.split('/').pop() || '';
        const commandData = parseCommandMarkdown(commandContent, filename);
        if (commandData) {
          profile.commands!.push(commandData as ClaudeCommand);
        }
      }
    }
  }

  // Generate profile metadata
  profile.name = profile.agent?.name || 'Imported Profile';
  profile.description = profile.agent?.description || 'Imported from .claude directory';
  profile.role = 'custom';
  profile.createdAt = new Date().toISOString();
  profile.updatedAt = new Date().toISOString();

  return profile as ProfileAdvanced;
}

/**
 * Import from JSON file
 */
export async function importFromJson(file: File): Promise<ProfileAdvanced> {
  const content = await file.text();
  const data = JSON.parse(content);

  // Check if it's a full profile or Claude export format
  if (data.type && (data.type === 'basic' || data.type === 'advanced')) {
    // It's a full profile
    return data as ProfileAdvanced;
  }

  // It's Claude export format - convert to profile
  const claudeExport = validateClaudeExport(data);
  
  const profile: ProfileAdvanced = {
    name: claudeExport.agents?.[0]?.name || 'Imported Profile',
    description: claudeExport.agents?.[0]?.description || 'Imported from Claude export',
    role: 'custom',
    type: 'advanced',
    commands: claudeExport.commands || [],
    hooks: claudeExport.hooks,
    mcps: claudeExport.mcps ? Object.entries(claudeExport.mcps).map(([name, config]: [string, any]) => ({
      name,
      command: config.command,
      args: config.args || [],
      env: config.env || {}
    })) : [],
    skills: [],
    plugins: [],
    settings: claudeExport.settings,
    agent: claudeExport.agents?.[0],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    version: '1.0.0',
    tags: []
  };

  return profile;
}

/**
 * Import from file (auto-detect format)
 */
export async function importFromFile(file: File): Promise<ProfileAdvanced> {
  const extension = file.name.split('.').pop()?.toLowerCase();

  if (extension === 'zip') {
    return await importFromZip(file);
  } else if (extension === 'json') {
    return await importFromJson(file);
  } else {
    throw new Error('Unsupported file format. Please use .zip or .json');
  }
}

/**
 * Validate imported profile
 */
export function validateImportedProfile(profile: ProfileAdvanced): {
  isValid: boolean;
  errors: string[];
  warnings: string[];
} {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Check required fields
  if (!profile.name) {
    errors.push('Profile name is required');
  }

  if (!profile.type) {
    warnings.push('Profile type not specified, defaulting to "advanced"');
  }

  // Validate commands
  if (profile.commands) {
    profile.commands.forEach((cmd, index) => {
      if (!cmd.name) {
        errors.push(`Command at index ${index} is missing a name`);
      }
      if (!cmd.content) {
        errors.push(`Command "${cmd.name}" is missing content`);
      }
    });
  }

  // Validate MCPs
  if (profile.mcps) {
    profile.mcps.forEach((mcp, index) => {
      if (!mcp.name) {
        errors.push(`MCP at index ${index} is missing a name`);
      }
      if (!mcp.command) {
        errors.push(`MCP "${mcp.name}" is missing command`);
      }
    });
  }

  // Validate hooks
  if (profile.hooks) {
    Object.entries(profile.hooks).forEach(([type, hooks]) => {
      hooks.forEach((hook, index) => {
        if (!hook.matcher) {
          warnings.push(`Hook ${type}[${index}] is missing matcher`);
        }
        if (!hook.command) {
          errors.push(`Hook ${type}[${index}] is missing command`);
        }
      });
    });
  }

  // Check for security concerns
  if (profile.settings?.permissions?.allow?.includes('*')) {
    warnings.push('Profile allows all permissions (*) - consider restricting for security');
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
}

/**
 * Merge imported profile with existing profile
 */
export function mergeProfiles(
  existing: ProfileAdvanced,
  imported: ProfileAdvanced,
  strategy: 'replace' | 'merge' | 'append' = 'merge'
): ProfileAdvanced {
  if (strategy === 'replace') {
    return { ...imported, id: existing.id, createdAt: existing.createdAt };
  }

  if (strategy === 'append') {
    return {
      ...existing,
      commands: [...(existing.commands || []), ...(imported.commands || [])],
      mcps: [...(existing.mcps || []), ...(imported.mcps || [])],
      skills: [...(existing.skills || []), ...(imported.skills || [])],
      plugins: [...(existing.plugins || []), ...(imported.plugins || [])],
      updatedAt: new Date().toISOString()
    };
  }

  // Merge strategy
  return {
    ...existing,
    ...imported,
    id: existing.id,
    createdAt: existing.createdAt,
    updatedAt: new Date().toISOString(),
    commands: [...(existing.commands || []), ...(imported.commands || [])],
    mcps: [...(existing.mcps || []), ...(imported.mcps || [])],
    skills: [...(existing.skills || []), ...(imported.skills || [])],
    plugins: [...(existing.plugins || []), ...(imported.plugins || [])],
    tags: Array.from(new Set([...(existing.tags || []), ...(imported.tags || [])]))
  };
}

