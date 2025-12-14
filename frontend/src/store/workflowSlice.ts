import { StateCreator } from 'zustand';
import {
  SavedWorkflowSchema,
  ChainConfigSchema,
  type SavedWorkflow,
  type ChainConfig,
  safeParse,
  validateArray,
} from '../schemas';

/**
 * Workflow Slice - Manages saved workflows and chains
 */
export interface WorkflowSlice {
  // State
  savedWorkflows: SavedWorkflow[];
  currentWorkflow: SavedWorkflow | null;
  chains: ChainConfig[];
  
  // Actions
  saveWorkflow: (workflow: SavedWorkflow) => void;
  loadWorkflow: (id: string) => SavedWorkflow | null;
  updateWorkflow: (id: string, updates: Partial<SavedWorkflow>) => void;
  deleteWorkflow: (id: string) => void;
  setCurrentWorkflow: (workflow: SavedWorkflow | null) => void;
  getAllWorkflows: () => SavedWorkflow[];
  
  // Chain actions
  saveChain: (chain: ChainConfig) => void;
  updateChain: (id: number, updates: Partial<ChainConfig>) => void;
  deleteChain: (id: number) => void;
  getChainById: (id: number) => ChainConfig | null;
}

export const createWorkflowSlice: StateCreator<WorkflowSlice> = (set, get) => ({
  // Initial state
  savedWorkflows: [],
  currentWorkflow: null,
  chains: [],

  // Save workflow with validation
  saveWorkflow: (workflow) => {
    const result = safeParse(SavedWorkflowSchema, workflow);
    
    if (!result.success) {
      console.error('Invalid workflow:', result.error);
      throw new Error(`Workflow validation failed: ${result.error.message}`);
    }

    const validated = result.data;
    
    set((state) => {
      const existing = state.savedWorkflows.findIndex((w) => w.id === validated.id);
      
      if (existing >= 0) {
        const updated = [...state.savedWorkflows];
        updated[existing] = {
          ...validated,
          updatedAt: new Date().toISOString(),
        };
        return { savedWorkflows: updated };
      }
      
      return {
        savedWorkflows: [...state.savedWorkflows, validated],
      };
    });
  },

  // Load workflow by ID
  loadWorkflow: (id) => {
    const workflow = get().savedWorkflows.find((w) => w.id === id);
    return workflow || null;
  },

  // Update workflow
  updateWorkflow: (id, updates) => {
    set((state) => {
      const index = state.savedWorkflows.findIndex((w) => w.id === id);
      if (index === -1) return state;

      const updated = [...state.savedWorkflows];
      const current = updated[index];
      
      updated[index] = {
        ...current,
        ...updates,
        updatedAt: new Date().toISOString(),
      };

      // Validate updated workflow
      const result = safeParse(SavedWorkflowSchema, updated[index]);
      if (!result.success) {
        console.error('Invalid workflow update:', result.error);
        return state;
      }

      return { savedWorkflows: updated };
    });
  },

  // Delete workflow
  deleteWorkflow: (id) => {
    set((state) => ({
      savedWorkflows: state.savedWorkflows.filter((w) => w.id !== id),
      currentWorkflow: state.currentWorkflow?.id === id ? null : state.currentWorkflow,
    }));
  },

  // Set current workflow
  setCurrentWorkflow: (workflow) => {
    if (workflow) {
      const result = safeParse(SavedWorkflowSchema, workflow);
      if (!result.success) {
        console.error('Invalid workflow:', result.error);
        return;
      }
      set({ currentWorkflow: result.data });
    } else {
      set({ currentWorkflow: null });
    }
  },

  // Get all workflows (validated)
  getAllWorkflows: () => {
    const workflows = get().savedWorkflows;
    try {
      return validateArray(SavedWorkflowSchema, workflows);
    } catch (error) {
      console.error('Invalid workflows in store:', error);
      return [];
    }
  },

  // Save chain with validation
  saveChain: (chain) => {
    const result = safeParse(ChainConfigSchema, chain);
    
    if (!result.success) {
      console.error('Invalid chain:', result.error);
      throw new Error(`Chain validation failed: ${result.error.message}`);
    }

    const validated = result.data;
    
    set((state) => {
      if (validated.id !== undefined) {
        const existing = state.chains.findIndex((c) => c.id === validated.id);
        if (existing >= 0) {
          const updated = [...state.chains];
          updated[existing] = validated;
          return { chains: updated };
        }
      }
      
      const newChain = {
        ...validated,
        id: validated.id ?? Date.now(),
      };
      
      return { chains: [...state.chains, newChain] };
    });
  },

  // Update chain
  updateChain: (id, updates) => {
    set((state) => {
      const index = state.chains.findIndex((c) => c.id === id);
      if (index === -1) return state;

      const updated = [...state.chains];
      updated[index] = { ...updated[index], ...updates };

      // Validate updated chain
      const result = safeParse(ChainConfigSchema, updated[index]);
      if (!result.success) {
        console.error('Invalid chain update:', result.error);
        return state;
      }

      return { chains: updated };
    });
  },

  // Delete chain
  deleteChain: (id) => {
    set((state) => ({
      chains: state.chains.filter((c) => c.id !== id),
    }));
  },

  // Get chain by ID
  getChainById: (id) => {
    const chain = get().chains.find((c) => c.id === id);
    return chain || null;
  },
});

