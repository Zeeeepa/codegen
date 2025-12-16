import { cn } from '@/utils/cn';
import { WorkflowStatus, SandboxStatus } from '@/api/types';

interface StatusBadgeProps {
  status: WorkflowStatus | SandboxStatus | string;
  size?: 'sm' | 'md' | 'lg';
}

export function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const sizeStyles = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  };

  const statusStyles: Record<string, string> = {
    enabled: 'bg-success/10 text-success',
    disabled: 'bg-gray-200 text-gray-600',
    running: 'bg-accent/20 text-accent-dark',
    error: 'bg-error/10 text-error',
    pending: 'bg-warning/20 text-warning',
    completed: 'bg-success/10 text-success',
    failed: 'bg-error/10 text-error',
    terminated: 'bg-gray-300 text-gray-700',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full font-medium',
        sizeStyles[size],
        statusStyles[status.toLowerCase()] || 'bg-gray-200 text-gray-700'
      )}
    >
      <span
        className={cn(
          'w-2 h-2 rounded-full mr-1.5',
          status.toLowerCase() === 'enabled' && 'bg-success',
          status.toLowerCase() === 'disabled' && 'bg-gray-400',
          status.toLowerCase() === 'running' && 'bg-accent animate-pulse',
          status.toLowerCase() === 'error' && 'bg-error',
          status.toLowerCase() === 'pending' && 'bg-warning',
          status.toLowerCase() === 'completed' && 'bg-success',
          status.toLowerCase() === 'failed' && 'bg-error',
          status.toLowerCase() === 'terminated' && 'bg-gray-500'
        )}
      />
      {status}
    </span>
  );
}

