import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { createCredentialsSlice, type CredentialsSlice } from './credentialsSlice';
import { createWorkflowSlice, type WorkflowSlice } from './workflowSlice';
import { createExecutionSlice, type ExecutionSlice } from './executionSlice';
import { createRunHistorySlice, type RunHistorySlice } from './runHistorySlice';
import { createUISlice, type UISlice } from './uiSlice';

/**
 * Combined Store Type
 * Merges all slices into a single store interface
 */
export type AppStore = CredentialsSlice &
  WorkflowSlice &
  ExecutionSlice &
  RunHistorySlice &
  UISlice;

/**
 * Main Application Store
 * 
 * Architecture:
 * - Credentials Slice: API token, org ID, validation state
 * - Workflow Slice: Saved workflows, chains, templates
 * - Execution Slice: Active execution contexts with detailed step tracking
 * - Run History Slice: Historical runs with status tracking
 * - UI Slice: Modal states, selections, view preferences (NOT persisted)
 * 
 * Persistence Strategy:
 * - Credentials: localStorage (security warning in UI)
 * - Workflows: localStorage (with metadata)
 * - Executions: Memory only (too large for localStorage)
 * - Runs: localStorage (last 100 runs)
 * - UI: Memory only (session state)
 */
export const useAppStore = create<AppStore>()(
  persist(
    (...args) => ({
      ...createCredentialsSlice(...args),
      ...createWorkflowSlice(...args),
      ...createExecutionSlice(...args),
      ...createRunHistorySlice(...args),
      ...createUISlice(...args),
    }),
    {
      name: 'codegen-app-store',
      storage: createJSONStorage(() => localStorage),
      
      // Partition: Only persist specific slices
      partialize: (state) => ({
        // Persist credentials
        apiToken: state.apiToken,
        organizationId: state.organizationId,
        isValidated: state.isValidated,
        validationResult: state.validationResult,
        
        // Persist workflows
        savedWorkflows: state.savedWorkflows,
        chains: state.chains,
        
        // Persist run history (but NOT active executions - too large)
        runs: state.runs,
        
        // DO NOT persist:
        // - activeExecutions (too large, runtime only)
        // - executionHistory (too large, runtime only)
        // - currentExecution (runtime only)
        // - currentWorkflow (runtime only)
        // - activeRuns (runtime only)
        // - UI state (session only)
      }),
    }
  )
);

/**
 * Typed Selectors for Common Queries
 */
export const selectCredentials = (state: AppStore) => ({
  apiToken: state.apiToken,
  organizationId: state.organizationId,
  isValidated: state.isValidated,
});

export const selectHasValidCredentials = (state: AppStore) =>
  state.isValidated &&
  state.apiToken.length > 0 &&
  state.organizationId.length > 0;

export const selectActiveExecutionCount = (state: AppStore) =>
  state.activeExecutions.size;

export const selectActiveRunCount = (state: AppStore) =>
  state.activeRuns.size;

export const selectCurrentExecutionProgress = (state: AppStore) => {
  if (!state.currentExecution) return null;
  
  return {
    current: state.currentExecution.currentStepIndex,
    total: state.currentExecution.totalSteps,
    percentage: Math.round(
      (state.currentExecution.currentStepIndex / state.currentExecution.totalSteps) * 100
    ),
  };
};

export const selectRecentRuns = (state: AppStore, limit = 10) =>
  state.runs.slice(0, limit);

export const selectWorkflowByName = (state: AppStore, name: string) =>
  state.savedWorkflows.find((w) => w.name === name);

export const selectChainByName = (state: AppStore, name: string) =>
  state.chains.find((c) => c.name === name);

/**
 * Export individual slices for testing
 */
export { createCredentialsSlice } from './credentialsSlice';
export { createWorkflowSlice } from './workflowSlice';
export { createExecutionSlice } from './executionSlice';
export { createRunHistorySlice } from './runHistorySlice';
export { createUISlice } from './uiSlice';

export type {
  CredentialsSlice,
  WorkflowSlice,
  ExecutionSlice,
  RunHistorySlice,
  UISlice,
};

