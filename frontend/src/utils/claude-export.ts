/**
 * Claude Export Utility
 * Converts profiles to .claude directory format for Claude Code compatibility
 */

import { ProfileAdvanced, ClaudeExport } from '../schemas/claude-config';
import JSZip from 'jszip';

/**
 * Convert profile to Claude export format
 */
export function profileToClaudeExport(profile: ProfileAdvanced): ClaudeExport {
  const claudeExport: ClaudeExport = {
    settings: profile.settings || {
      permissions: {
        allow: [],
        deny: []
      },
      model: 'sonnet'
    },
    agents: profile.agent ? [profile.agent] : [],
    commands: profile.commands || [],
    mcps: profile.mcps?.reduce((acc, mcp) => {
      acc[mcp.name] = mcp;
      return acc;
    }, {} as Record<string, any>) || {},
    hooks: profile.hooks
  };

  return claudeExport;
}

/**
 * Generate settings.local.json content
 */
export function generateSettingsJson(profile: ProfileAdvanced): string {
  const settings = {
    permissions: profile.settings?.permissions || {
      allow: [],
      deny: []
    },
    hooks: profile.hooks || {}
  };

  return JSON.stringify(settings, null, 2);
}

/**
 * Generate .mcp.json content
 */
export function generateMcpJson(profile: ProfileAdvanced): string {
  const mcpServers = profile.mcps?.reduce((acc, mcp) => {
    acc[mcp.name] = {
      command: mcp.command,
      args: mcp.args,
      env: mcp.env || {}
    };
    return acc;
  }, {} as Record<string, any>) || {};

  return JSON.stringify({ mcpServers }, null, 2);
}

/**
 * Generate agent markdown file
 */
export function generateAgentMarkdown(profile: ProfileAdvanced): string | null {
  if (!profile.agent) {
    return null;
  }

  const { agent } = profile;
  
  let markdown = `---
name: ${agent.name}
description: ${agent.description || ''}
tools: ${agent.tools.join(', ')}
model: ${agent.model}
---

${agent.systemPrompt || ''}

## Focus Areas
${agent.focusAreas.map(area => `- ${area}`).join('\n')}

## Approach
${agent.approach.map((item, i) => `${i + 1}. ${item}`).join('\n')}

## Output
${agent.outputGuidelines.map(item => `- ${item}`).join('\n')}

Focus on working code over explanations. Include usage examples in comments.
`;

  return markdown;
}

/**
 * Generate command markdown files
 */
export function generateCommandMarkdowns(profile: ProfileAdvanced): Record<string, string> {
  const commands: Record<string, string> = {};

  profile.commands?.forEach(command => {
    const markdown = `# ${command.name}

${command.description || ''}

## Purpose

${command.content}

${command.examples ? `## Examples

${command.examples.map(ex => `\`\`\`\n${ex}\n\`\`\``).join('\n\n')}` : ''}
`;

    commands[`${command.name}.md`] = markdown;
  });

  return commands;
}

/**
 * Export profile as ZIP file (.claude directory structure)
 */
export async function exportAsZip(profile: ProfileAdvanced): Promise<Blob> {
  const zip = new JSZip();

  // Create .claude directory structure
  const claudeDir = zip.folder('.claude')!;

  // Add settings.local.json
  claudeDir.file('settings.local.json', generateSettingsJson(profile));

  // Add .mcp.json at root
  zip.file('.mcp.json', generateMcpJson(profile));

  // Add agents if present
  if (profile.agent) {
    const agentsDir = claudeDir.folder('agents')!;
    const agentMd = generateAgentMarkdown(profile);
    if (agentMd) {
      agentsDir.file(`${profile.agent.name}.md`, agentMd);
    }
  }

  // Add commands
  if (profile.commands && profile.commands.length > 0) {
    const commandsDir = claudeDir.folder('commands')!;
    const commandFiles = generateCommandMarkdowns(profile);
    
    Object.entries(commandFiles).forEach(([filename, content]) => {
      commandsDir.file(filename, content);
    });
  }

  // Generate ZIP
  return await zip.generateAsync({ type: 'blob' });
}

/**
 * Export profile as JSON (single file)
 */
export function exportAsJson(profile: ProfileAdvanced): string {
  const claudeExport = profileToClaudeExport(profile);
  return JSON.stringify(claudeExport, null, 2);
}

/**
 * Download file helper
 */
export function downloadFile(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Export profile as ZIP and trigger download
 */
export async function exportProfileAsZip(profile: ProfileAdvanced): Promise<void> {
  const blob = await exportAsZip(profile);
  const filename = `${profile.name.replace(/\s+/g, '-').toLowerCase()}-claude-config.zip`;
  downloadFile(blob, filename);
}

/**
 * Export profile as JSON and trigger download
 */
export function exportProfileAsJson(profile: ProfileAdvanced): void {
  const json = exportAsJson(profile);
  const blob = new Blob([json], { type: 'application/json' });
  const filename = `${profile.name.replace(/\s+/g, '-').toLowerCase()}-claude-config.json`;
  downloadFile(blob, filename);
}

/**
 * Copy export JSON to clipboard
 */
export async function copyExportToClipboard(profile: ProfileAdvanced): Promise<void> {
  const json = exportAsJson(profile);
  await navigator.clipboard.writeText(json);
}

/**
 * Generate README for exported profile
 */
export function generateReadme(profile: ProfileAdvanced): string {
  return `# ${profile.name}

${profile.description || ''}

## Installation

1. Extract this ZIP file to your project directory
2. The \`.claude\` directory will be created with all configuration files
3. Restart Claude Code to load the new configuration

## What's Included

- **Agent Configuration**: ${profile.agent ? profile.agent.name : 'No agent configured'}
- **Commands**: ${profile.commands?.length || 0} custom commands
- **Hooks**: ${Object.values(profile.hooks || {}).flat().length || 0} event hooks
- **MCPs**: ${profile.mcps?.length || 0} MCP server configurations
- **Skills**: ${profile.skills?.length || 0} reusable skills

## Configuration Files

- \`.claude/settings.local.json\` - Permissions and preferences
- \`.claude/agents/\` - Agent definitions
- \`.claude/commands/\` - Custom commands
- \`.mcp.json\` - MCP server configurations

## Version

${profile.version || '1.0.0'}

## Tags

${profile.tags?.join(', ') || 'No tags'}

---

Generated by Codegen Profile Manager
`;
}

/**
 * Export profile with README as ZIP
 */
export async function exportProfileWithReadme(profile: ProfileAdvanced): Promise<void> {
  const zip = new JSZip();

  // Add README
  zip.file('README.md', generateReadme(profile));

  // Create .claude directory structure
  const claudeDir = zip.folder('.claude')!;

  // Add settings.local.json
  claudeDir.file('settings.local.json', generateSettingsJson(profile));

  // Add .mcp.json at root
  zip.file('.mcp.json', generateMcpJson(profile));

  // Add agents if present
  if (profile.agent) {
    const agentsDir = claudeDir.folder('agents')!;
    const agentMd = generateAgentMarkdown(profile);
    if (agentMd) {
      agentsDir.file(`${profile.agent.name}.md`, agentMd);
    }
  }

  // Add commands
  if (profile.commands && profile.commands.length > 0) {
    const commandsDir = claudeDir.folder('commands')!;
    const commandFiles = generateCommandMarkdowns(profile);
    
    Object.entries(commandFiles).forEach(([filename, content]) => {
      commandsDir.file(filename, content);
    });
  }

  // Generate and download ZIP
  const blob = await zip.generateAsync({ type: 'blob' });
  const filename = `${profile.name.replace(/\s+/g, '-').toLowerCase()}-claude-profile.zip`;
  downloadFile(blob, filename);
}

