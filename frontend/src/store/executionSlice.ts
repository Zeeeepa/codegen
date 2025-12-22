import { StateCreator } from 'zustand';
import {
  AgentExecutionContextSchema,
  AgentExecutionStepSchema,
  WorkflowRunSchema,
  type AgentExecutionContext,
  type AgentExecutionStep,
  type WorkflowRun,
  type RunStatus,
  safeParse,
  validateArray,
} from '../schemas';

/**
 * Execution Slice - Manages agent execution context and detailed step tracking
 */
export interface ExecutionSlice {
  // State
  activeExecutions: Map<string, AgentExecutionContext>;
  executionHistory: AgentExecutionContext[];
  currentExecution: AgentExecutionContext | null;
  
  // Actions
  startExecution: (context: AgentExecutionContext) => void;
  updateExecutionStep: (executionId: string, step: AgentExecutionStep) => void;
  updateExecutionStatus: (executionId: string, status: RunStatus) => void;
  completeExecution: (executionId: string, result?: string, error?: string) => void;
  setCurrentExecution: (executionId: string | null) => void;
  getExecutionById: (executionId: string) => AgentExecutionContext | null;
  getExecutionSteps: (executionId: string) => AgentExecutionStep[];
  clearExecutionHistory: () => void;
}

export const createExecutionSlice: StateCreator<ExecutionSlice> = (set, get) => ({
  // Initial state
  activeExecutions: new Map(),
  executionHistory: [],
  currentExecution: null,

  // Start new execution with validation
  startExecution: (context) => {
    const result = safeParse(AgentExecutionContextSchema, context);
    
    if (!result.success) {
      console.error('Invalid execution context:', result.error);
      throw new Error(`Execution validation failed: ${result.error.message}`);
    }

    const validated = result.data;
    
    set((state) => {
      const newActiveExecutions = new Map(state.activeExecutions);
      newActiveExecutions.set(validated.executionId, validated);
      
      return {
        activeExecutions: newActiveExecutions,
        currentExecution: validated,
      };
    });
  },

  // Update execution step
  updateExecutionStep: (executionId, step) => {
    const stepResult = safeParse(AgentExecutionStepSchema, step);
    
    if (!stepResult.success) {
      console.error('Invalid execution step:', stepResult.error);
      return;
    }

    const validatedStep = stepResult.data;
    
    set((state) => {
      const execution = state.activeExecutions.get(executionId);
      if (!execution) return state;

      const stepIndex = execution.steps.findIndex(
        (s) => s.stepId === validatedStep.stepId
      );

      const updatedSteps = [...execution.steps];
      
      if (stepIndex >= 0) {
        updatedSteps[stepIndex] = validatedStep;
      } else {
        updatedSteps.push(validatedStep);
      }

      const updatedExecution: AgentExecutionContext = {
        ...execution,
        steps: updatedSteps,
        currentStepIndex: validatedStep.stepIndex,
      };

      const newActiveExecutions = new Map(state.activeExecutions);
      newActiveExecutions.set(executionId, updatedExecution);

      return {
        activeExecutions: newActiveExecutions,
        currentExecution:
          state.currentExecution?.executionId === executionId
            ? updatedExecution
            : state.currentExecution,
      };
    });
  },

  // Update execution status
  updateExecutionStatus: (executionId, status) => {
    set((state) => {
      const execution = state.activeExecutions.get(executionId);
      if (!execution) return state;

      const updatedExecution: AgentExecutionContext = {
        ...execution,
        status,
      };

      const newActiveExecutions = new Map(state.activeExecutions);
      newActiveExecutions.set(executionId, updatedExecution);

      return {
        activeExecutions: newActiveExecutions,
        currentExecution:
          state.currentExecution?.executionId === executionId
            ? updatedExecution
            : state.currentExecution,
      };
    });
  },

  // Complete execution
  completeExecution: (executionId, result, error) => {
    set((state) => {
      const execution = state.activeExecutions.get(executionId);
      if (!execution) return state;

      const completedExecution: AgentExecutionContext = {
        ...execution,
        status: error ? 'failed' : 'completed',
        endTime: new Date().toISOString(),
        summary: result,
        error,
      };

      const newActiveExecutions = new Map(state.activeExecutions);
      newActiveExecutions.delete(executionId);

      // Add to history (keep last 100)
      const newHistory = [completedExecution, ...state.executionHistory];
      if (newHistory.length > 100) {
        newHistory.pop();
      }

      return {
        activeExecutions: newActiveExecutions,
        executionHistory: newHistory,
        currentExecution:
          state.currentExecution?.executionId === executionId
            ? null
            : state.currentExecution,
      };
    });
  },

  // Set current execution
  setCurrentExecution: (executionId) => {
    if (!executionId) {
      set({ currentExecution: null });
      return;
    }

    const execution = get().activeExecutions.get(executionId);
    if (execution) {
      set({ currentExecution: execution });
    }
  },

  // Get execution by ID
  getExecutionById: (executionId) => {
    const active = get().activeExecutions.get(executionId);
    if (active) return active;

    const historical = get().executionHistory.find(
      (e) => e.executionId === executionId
    );
    return historical || null;
  },

  // Get execution steps
  getExecutionSteps: (executionId) => {
    const execution = get().getExecutionById(executionId);
    if (!execution) return [];

    try {
      return validateArray(AgentExecutionStepSchema, execution.steps);
    } catch (error) {
      console.error('Invalid execution steps:', error);
      return [];
    }
  },

  // Clear execution history
  clearExecutionHistory: () => {
    set({ executionHistory: [] });
  },
});

