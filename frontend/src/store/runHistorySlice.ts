import { StateCreator } from 'zustand';
import {
  WorkflowRunSchema,
  type WorkflowRun,
  type RunStatus,
  safeParse,
  validateArray,
} from '../schemas';

/**
 * Run History Slice - Manages workflow run history and status tracking
 */
export interface RunHistorySlice {
  // State
  runs: WorkflowRun[];
  activeRuns: Map<string, WorkflowRun>;
  
  // Actions
  addRun: (run: WorkflowRun) => void;
  updateRun: (id: string, updates: Partial<WorkflowRun>) => void;
  updateRunStatus: (id: string, status: RunStatus) => void;
  completeRun: (id: string, result?: string, error?: string) => void;
  getRunById: (id: string) => WorkflowRun | null;
  getRunsByWorkflow: (workflowId: string) => WorkflowRun[];
  getRunsByStatus: (status: RunStatus) => WorkflowRun[];
  clearOldRuns: (keepCount?: number) => void;
  getAllRuns: () => WorkflowRun[];
}

const MAX_RUNS = 100;

export const createRunHistorySlice: StateCreator<RunHistorySlice> = (set, get) => ({
  // Initial state
  runs: [],
  activeRuns: new Map(),

  // Add new run with validation
  addRun: (run) => {
    const result = safeParse(WorkflowRunSchema, run);
    
    if (!result.success) {
      console.error('Invalid run:', result.error);
      throw new Error(`Run validation failed: ${result.error.message}`);
    }

    const validated = result.data;
    
    set((state) => {
      const newRuns = [validated, ...state.runs];
      
      // Auto-cleanup old runs
      if (newRuns.length > MAX_RUNS) {
        newRuns.splice(MAX_RUNS);
      }

      const newActiveRuns = new Map(state.activeRuns);
      if (validated.status === 'running' || validated.status === 'pending') {
        newActiveRuns.set(validated.id, validated);
      }

      return {
        runs: newRuns,
        activeRuns: newActiveRuns,
      };
    });
  },

  // Update run
  updateRun: (id, updates) => {
    set((state) => {
      const index = state.runs.findIndex((r) => r.id === id);
      if (index === -1) return state;

      const updatedRuns = [...state.runs];
      const current = updatedRuns[index];
      
      updatedRuns[index] = {
        ...current,
        ...updates,
        endTime: updates.status && 
                 (updates.status === 'completed' || updates.status === 'failed')
          ? new Date().toISOString()
          : current.endTime,
      };

      // Validate updated run
      const result = safeParse(WorkflowRunSchema, updatedRuns[index]);
      if (!result.success) {
        console.error('Invalid run update:', result.error);
        return state;
      }

      const validated = result.data;
      updatedRuns[index] = validated;

      // Update active runs map
      const newActiveRuns = new Map(state.activeRuns);
      if (validated.status === 'running' || validated.status === 'pending') {
        newActiveRuns.set(id, validated);
      } else {
        newActiveRuns.delete(id);
      }

      return {
        runs: updatedRuns,
        activeRuns: newActiveRuns,
      };
    });
  },

  // Update run status
  updateRunStatus: (id, status) => {
    get().updateRun(id, { status });
  },

  // Complete run
  completeRun: (id, result, error) => {
    get().updateRun(id, {
      status: error ? 'failed' : 'completed',
      result,
      error,
      endTime: new Date().toISOString(),
    });
  },

  // Get run by ID
  getRunById: (id) => {
    const run = get().runs.find((r) => r.id === id);
    return run || null;
  },

  // Get runs by workflow ID
  getRunsByWorkflow: (workflowId) => {
    return get().runs.filter((r) => r.workflowId === workflowId);
  },

  // Get runs by status
  getRunsByStatus: (status) => {
    return get().runs.filter((r) => r.status === status);
  },

  // Clear old runs (keep most recent N)
  clearOldRuns: (keepCount = MAX_RUNS) => {
    set((state) => {
      const sortedRuns = [...state.runs].sort((a, b) => {
        return new Date(b.startTime).getTime() - new Date(a.startTime).getTime();
      });

      const runsToKeep = sortedRuns.slice(0, keepCount);

      // Update active runs to only include kept runs
      const keptIds = new Set(runsToKeep.map((r) => r.id));
      const newActiveRuns = new Map(
        Array.from(state.activeRuns.entries()).filter(([id]) => keptIds.has(id))
      );

      return {
        runs: runsToKeep,
        activeRuns: newActiveRuns,
      };
    });
  },

  // Get all runs (validated)
  getAllRuns: () => {
    const runs = get().runs;
    try {
      return validateArray(WorkflowRunSchema, runs);
    } catch (error) {
      console.error('Invalid runs in store:', error);
      return [];
    }
  },
});

