import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { useSandboxStore } from '@/store/sandboxStore';

export function useSandboxes() {
  const { setSandboxes, setLoading, setError } = useSandboxStore();

  return useQuery({
    queryKey: ['sandboxes'],
    queryFn: async () => {
      setLoading(true);
      setError(null);
      try {
        const sandboxes = await apiClient.getSandboxes();
        setSandboxes(sandboxes);
        return sandboxes;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to fetch sandboxes';
        setError(message);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    refetchInterval: 2000, // Refetch every 2 seconds for real-time monitoring
  });
}

export function useSandboxStatus(sandboxId: string) {
  return useQuery({
    queryKey: ['sandbox-status', sandboxId],
    queryFn: () => apiClient.getSandboxStatus(sandboxId),
    enabled: !!sandboxId,
    refetchInterval: 2000,
  });
}

export function useTerminateSandbox() {
  const queryClient = useQueryClient();
  const { removeSandbox } = useSandboxStore();

  return useMutation({
    mutationFn: (sandboxId: string) => apiClient.terminateSandbox(sandboxId),
    onSuccess: (_data, sandboxId) => {
      removeSandbox(sandboxId);
      queryClient.invalidateQueries({ queryKey: ['sandboxes'] });
      queryClient.invalidateQueries({ queryKey: ['sandbox-status', sandboxId] });
    },
  });
}

export function useSandboxLogs(sandboxId: string) {
  return useQuery({
    queryKey: ['sandbox-logs', sandboxId],
    queryFn: () => apiClient.getSandboxLogs(sandboxId),
    enabled: !!sandboxId,
    refetchInterval: 3000,
  });
}

