import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface WorkflowRun {
  id: string;
  workflowId?: string;
  workflowName?: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  startTime: string;
  endTime?: string;
  result?: string;
  summary?: string;
  error?: string;
  githubPullRequests?: Array<{
    number: number;
    url: string;
    title: string;
  }>;
  metadata?: Record<string, any>;
}

export interface SavedWorkflow {
  id: string;
  name: string;
  description?: string;
  nodes: any[];
  edges: any[];
  createdAt: string;
  updatedAt: string;
  lastRunId?: string;
  runCount: number;
}

interface StoreState {
  // API Configuration
  apiToken: string | null;
  organizationId: string | null;
  setApiToken: (token: string) => void;
  setOrganizationId: (orgId: string) => void;
  clearCredentials: () => void;

  // Workflows
  savedWorkflows: SavedWorkflow[];
  currentWorkflow: SavedWorkflow | null;
  saveWorkflow: (workflow: Omit<SavedWorkflow, 'id' | 'createdAt' | 'updatedAt' | 'runCount'>) => string;
  updateWorkflow: (id: string, updates: Partial<SavedWorkflow>) => void;
  deleteWorkflow: (id: string) => void;
  loadWorkflow: (id: string) => SavedWorkflow | null;
  setCurrentWorkflow: (workflow: SavedWorkflow | null) => void;

  // Run History
  runHistory: WorkflowRun[];
  addRun: (run: WorkflowRun) => void;
  updateRun: (id: string, updates: Partial<WorkflowRun>) => void;
  getRun: (id: string) => WorkflowRun | undefined;
  getRunsByWorkflow: (workflowId: string) => WorkflowRun[];
  clearOldRuns: () => void;

  // UI State
  isSettingsOpen: boolean;
  setSettingsOpen: (open: boolean) => void;
  activeRunId: string | null;
  setActiveRunId: (id: string | null) => void;
}

export const useStore = create<StoreState>()(
  persist(
    (set, get) => ({
      // API Configuration
      apiToken: null,
      organizationId: null,
      setApiToken: (token) => set({ apiToken: token }),
      setOrganizationId: (orgId) => set({ organizationId: orgId }),
      clearCredentials: () => set({ apiToken: null, organizationId: null }),

      // Workflows
      savedWorkflows: [],
      currentWorkflow: null,
      
      saveWorkflow: (workflow) => {
        const id = `wf-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const now = new Date().toISOString();
        
        const newWorkflow: SavedWorkflow = {
          ...workflow,
          id,
          createdAt: now,
          updatedAt: now,
          runCount: 0,
        };

        set((state) => ({
          savedWorkflows: [...state.savedWorkflows, newWorkflow],
          currentWorkflow: newWorkflow,
        }));

        return id;
      },

      updateWorkflow: (id, updates) => {
        set((state) => ({
          savedWorkflows: state.savedWorkflows.map((wf) =>
            wf.id === id
              ? { ...wf, ...updates, updatedAt: new Date().toISOString() }
              : wf
          ),
          currentWorkflow:
            state.currentWorkflow?.id === id
              ? { ...state.currentWorkflow, ...updates, updatedAt: new Date().toISOString() }
              : state.currentWorkflow,
        }));
      },

      deleteWorkflow: (id) => {
        set((state) => ({
          savedWorkflows: state.savedWorkflows.filter((wf) => wf.id !== id),
          currentWorkflow: state.currentWorkflow?.id === id ? null : state.currentWorkflow,
        }));
      },

      loadWorkflow: (id) => {
        const workflow = get().savedWorkflows.find((wf) => wf.id === id);
        if (workflow) {
          set({ currentWorkflow: workflow });
          return workflow;
        }
        return null;
      },

      setCurrentWorkflow: (workflow) => set({ currentWorkflow: workflow }),

      // Run History
      runHistory: [],

      addRun: (run) => {
        set((state) => {
          // Keep only last 100 runs to prevent storage bloat
          const updatedHistory = [run, ...state.runHistory].slice(0, 100);
          
          // Update workflow run count if applicable
          if (run.workflowId) {
            const updatedWorkflows = state.savedWorkflows.map((wf) =>
              wf.id === run.workflowId
                ? { ...wf, runCount: wf.runCount + 1, lastRunId: run.id }
                : wf
            );
            return {
              runHistory: updatedHistory,
              savedWorkflows: updatedWorkflows,
            };
          }

          return { runHistory: updatedHistory };
        });
      },

      updateRun: (id, updates) => {
        set((state) => ({
          runHistory: state.runHistory.map((run) =>
            run.id === id ? { ...run, ...updates } : run
          ),
        }));
      },

      getRun: (id) => {
        return get().runHistory.find((run) => run.id === id);
      },

      getRunsByWorkflow: (workflowId) => {
        return get().runHistory.filter((run) => run.workflowId === workflowId);
      },

      clearOldRuns: () => {
        set((state) => ({
          runHistory: state.runHistory.slice(0, 50), // Keep only last 50 runs
        }));
      },

      // UI State
      isSettingsOpen: false,
      setSettingsOpen: (open) => set({ isSettingsOpen: open }),
      activeRunId: null,
      setActiveRunId: (id) => set({ activeRunId: id }),
    }),
    {
      name: 'codegen-orchestration-store',
      // Only persist certain fields
      partialize: (state) => ({
        apiToken: state.apiToken,
        organizationId: state.organizationId,
        savedWorkflows: state.savedWorkflows,
        runHistory: state.runHistory,
        currentWorkflow: state.currentWorkflow,
      }),
    }
  )
);

// Selectors for common queries
export const selectHasCredentials = (state: StoreState) => 
  !!(state.apiToken && state.organizationId);

export const selectRecentRuns = (state: StoreState, limit = 10) =>
  state.runHistory.slice(0, limit);

export const selectRunningWorkflows = (state: StoreState) =>
  state.runHistory.filter((run) => run.status === 'running' || run.status === 'pending');

