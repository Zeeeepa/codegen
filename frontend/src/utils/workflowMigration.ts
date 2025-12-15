/**
 * Workflow Migration Utility
 * Migrates workflows from localStorage to database
 */

import { databaseApi } from '@/services/databaseApi';
import type { SavedWorkflow, ChainConfig } from '@/schemas';
import type { WorkflowDefinition } from '@/types/database';
import toast from 'react-hot-toast';

// ============================================================================
// Migration Functions
// ============================================================================

/**
 * Convert ChainConfig to WorkflowDefinition for database storage
 */
export function chainConfigToWorkflowDefinition(chain: ChainConfig): WorkflowDefinition {
  // Convert chain steps to visual nodes and edges
  const nodes = chain.steps.map((step, index) => ({
    id: `step-${index}`,
    type: step.type,
    position: { x: 100 + (index * 200), y: 100 },
    data: step,
  }));

  const edges = nodes.slice(0, -1).map((node, index) => ({
    id: `edge-${index}`,
    source: node.id,
    target: `step-${index + 1}`,
  }));

  return { nodes, edges };
}

/**
 * Convert WorkflowDefinition to ChainConfig
 */
export function workflowDefinitionToChainConfig(
  definition: WorkflowDefinition,
  name: string,
  description: string
): ChainConfig {
  // Extract steps from nodes
  const steps = definition.nodes
    .sort((a, b) => a.position.x - b.position.x) // Sort by x position
    .map(node => node.data);

  return {
    name,
    description,
    steps,
    contextStrategy: {
      mode: 'accumulate',
      maxTokens: 8000,
      includeErrors: true,
      includeLogs: true,
    },
    errorHandling: {
      autoRetry: true,
      maxGlobalRetries: 3,
      escalateOnFailure: false,
      notifyOnError: true,
    },
  };
}

/**
 * Migrate localStorage workflows to database
 */
export async function migrateLocalStorageToDatabase(): Promise<{
  success: number;
  failed: number;
  errors: string[];
}> {
  const results = {
    success: 0,
    failed: 0,
    errors: [] as string[],
  };

  try {
    // Get localStorage data
    const stored = localStorage.getItem('codegen-app-store');
    if (!stored) {
      console.log('No localStorage data to migrate');
      return results;
    }

    const data = JSON.parse(stored);
    const { savedWorkflows = [], chains = [] } = data;

    // Migrate saved workflows
    for (const workflow of savedWorkflows) {
      try {
        const definition = workflow.definition || chainConfigToWorkflowDefinition(workflow);
        
        await databaseApi.workflows.create({
          name: workflow.name,
          description: workflow.description || '',
          definition,
          context: workflow.metadata || {},
        });
        
        results.success++;
      } catch (error: any) {
        results.failed++;
        results.errors.push(`${workflow.name}: ${error.message}`);
      }
    }

    // Migrate chains
    for (const chain of chains) {
      try {
        const definition = chainConfigToWorkflowDefinition(chain);
        
        await databaseApi.workflows.create({
          name: chain.name,
          description: chain.description,
          definition,
          context: {
            contextStrategy: chain.contextStrategy,
            errorHandling: chain.errorHandling,
          },
        });
        
        results.success++;
      } catch (error: any) {
        results.failed++;
        results.errors.push(`${chain.name}: ${error.message}`);
      }
    }

    // Backup localStorage data
    if (results.success > 0) {
      localStorage.setItem(
        'codegen-app-store-backup',
        localStorage.getItem('codegen-app-store') || ''
      );
    }

  } catch (error: any) {
    results.errors.push(`Migration error: ${error.message}`);
  }

  return results;
}

/**
 * Check if migration is needed
 */
export function needsMigration(): boolean {
  const stored = localStorage.getItem('codegen-app-store');
  if (!stored) return false;

  try {
    const data = JSON.parse(stored);
    const hasWorkflows = (data.savedWorkflows?.length || 0) > 0;
    const hasChains = (data.chains?.length || 0) > 0;
    const notMigrated = !localStorage.getItem('codegen-migrated');
    
    return (hasWorkflows || hasChains) && notMigrated;
  } catch {
    return false;
  }
}

/**
 * Mark migration as complete
 */
export function markMigrationComplete(): void {
  localStorage.setItem('codegen-migrated', new Date().toISOString());
}

/**
 * Run migration with user notification
 */
export async function runMigrationWithToast(): Promise<void> {
  if (!needsMigration()) {
    return;
  }

  const toastId = toast.loading('Migrating workflows to database...');

  try {
    const results = await migrateLocalStorageToDatabase();
    
    if (results.success > 0) {
      toast.success(
        `Successfully migrated ${results.success} workflow(s) to database`,
        { id: toastId }
      );
      markMigrationComplete();
    }
    
    if (results.failed > 0) {
      toast.error(
        `Failed to migrate ${results.failed} workflow(s). Check console for details.`,
        { id: toastId }
      );
      console.error('Migration errors:', results.errors);
    }
    
    if (results.success === 0 && results.failed === 0) {
      toast.dismiss(toastId);
    }
  } catch (error: any) {
    toast.error(`Migration failed: ${error.message}`, { id: toastId });
    console.error('Migration error:', error);
  }
}

