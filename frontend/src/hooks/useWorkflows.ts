import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { useWorkflowStore } from '@/store/workflowStore';
import type { Workflow } from '@/api/types';

export function useWorkflows() {
  const { setWorkflows, setLoading, setError } = useWorkflowStore();

  return useQuery({
    queryKey: ['workflows'],
    queryFn: async () => {
      setLoading(true);
      setError(null);
      try {
        const workflows = await apiClient.getWorkflows();
        setWorkflows(workflows);
        return workflows;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to fetch workflows';
        setError(message);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    refetchInterval: 5000, // Refetch every 5 seconds for real-time updates
  });
}

export function useWorkflow(workflowId: string) {
  return useQuery({
    queryKey: ['workflow', workflowId],
    queryFn: () => apiClient.getWorkflow(workflowId),
    enabled: !!workflowId,
  });
}

export function useToggleWorkflow() {
  const queryClient = useQueryClient();
  const { updateWorkflow } = useWorkflowStore();

  return useMutation({
    mutationFn: (workflowId: string) => apiClient.toggleWorkflow(workflowId),
    onSuccess: (updatedWorkflow) => {
      updateWorkflow(updatedWorkflow.id, updatedWorkflow);
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      queryClient.invalidateQueries({ queryKey: ['workflow', updatedWorkflow.id] });
    },
  });
}

export function useExecuteWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (workflowId: string) => apiClient.executeWorkflow(workflowId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sandboxes'] });
    },
  });
}

export function useCreateWorkflow() {
  const queryClient = useQueryClient();
  const { addWorkflow } = useWorkflowStore();

  return useMutation({
    mutationFn: (workflow: Partial<Workflow>) => apiClient.createWorkflow(workflow),
    onSuccess: (newWorkflow) => {
      addWorkflow(newWorkflow);
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });
}

export function useUpdateWorkflow() {
  const queryClient = useQueryClient();
  const { updateWorkflow } = useWorkflowStore();

  return useMutation({
    mutationFn: ({
      workflowId,
      updates,
    }: {
      workflowId: string;
      updates: Partial<Workflow>;
    }) => apiClient.updateWorkflow(workflowId, updates),
    onSuccess: (updatedWorkflow) => {
      updateWorkflow(updatedWorkflow.id, updatedWorkflow);
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      queryClient.invalidateQueries({ queryKey: ['workflow', updatedWorkflow.id] });
    },
  });
}

export function useWorkflowMetrics(workflowId: string) {
  return useQuery({
    queryKey: ['workflow-metrics', workflowId],
    queryFn: () => apiClient.getWorkflowMetrics(workflowId),
    enabled: !!workflowId,
    refetchInterval: 5000,
  });
}

