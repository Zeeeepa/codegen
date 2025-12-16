import { create } from 'zustand';
import type { Workflow } from '@/api/types';

interface WorkflowStore {
  workflows: Workflow[];
  selectedWorkflowId: string | null;
  isLoading: boolean;
  error: string | null;
  
  setWorkflows: (workflows: Workflow[]) => void;
  addWorkflow: (workflow: Workflow) => void;
  updateWorkflow: (workflowId: string, updates: Partial<Workflow>) => void;
  removeWorkflow: (workflowId: string) => void;
  selectWorkflow: (workflowId: string | null) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useWorkflowStore = create<WorkflowStore>((set) => ({
  workflows: [],
  selectedWorkflowId: null,
  isLoading: false,
  error: null,

  setWorkflows: (workflows) => set({ workflows }),
  
  addWorkflow: (workflow) =>
    set((state) => ({ workflows: [...state.workflows, workflow] })),
  
  updateWorkflow: (workflowId, updates) =>
    set((state) => ({
      workflows: state.workflows.map((w) =>
        w.id === workflowId ? { ...w, ...updates } : w
      ),
    })),
  
  removeWorkflow: (workflowId) =>
    set((state) => ({
      workflows: state.workflows.filter((w) => w.id !== workflowId),
    })),
  
  selectWorkflow: (workflowId) => set({ selectedWorkflowId: workflowId }),
  
  setLoading: (isLoading) => set({ isLoading }),
  
  setError: (error) => set({ error }),
}));

