import { useSandboxes, useTerminateSandbox } from '@/hooks/useSandboxes';
import { Card } from '@/components/Common/Card';
import { Button } from '@/components/Common/Button';
import { StatusBadge } from '@/components/Common/StatusBadge';
import { XCircle, Clock, Activity } from 'lucide-react';
import { formatRelativeTime, formatDuration } from '@/utils/formatters';

export function SandboxList() {
  const { data: sandboxes, isLoading, error } = useSandboxes();
  const terminateMutation = useTerminateSandbox();

  if (isLoading) {
    return (
      <Card>
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <div className="text-center py-12">
          <p className="text-error">Failed to load sandboxes</p>
          <p className="text-sm text-gray-600 mt-2">{error.message}</p>
        </div>
      </Card>
    );
  }

  if (!sandboxes || sandboxes.length === 0) {
    return (
      <Card>
        <div className="text-center py-12">
          <Activity className="w-12 h-12 mx-auto text-gray-400 mb-3" />
          <p className="text-gray-600">No active sandboxes</p>
          <p className="text-sm text-gray-500 mt-1">
            Execute a workflow to create a sandbox
          </p>
        </div>
      </Card>
    );
  }

  const activeSandboxes = sandboxes.filter(
    (s) => s.status === 'running' || s.status === 'pending'
  );
  const completedSandboxes = sandboxes.filter(
    (s) => s.status === 'completed' || s.status === 'failed' || s.status === 'terminated'
  );

  return (
    <div className="space-y-6">
      {activeSandboxes.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            Active Sandboxes ({activeSandboxes.length})
          </h3>
          <div className="space-y-3">
            {activeSandboxes.map((sandbox) => (
              <Card key={sandbox.id} className="border-l-4 border-accent">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="font-mono text-sm text-gray-600">
                        {sandbox.id.slice(0, 8)}...
                      </span>
                      <StatusBadge status={sandbox.status} size="sm" />
                    </div>
                    
                    <div className="flex items-center gap-4 text-xs text-gray-600">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        Started {formatRelativeTime(sandbox.created_at)}
                      </span>
                      
                      {sandbox.metrics && (
                        <>
                          <span>
                            {sandbox.metrics.api_calls} API calls
                          </span>
                          <span>
                            {sandbox.metrics.token_usage.toLocaleString()} tokens
                          </span>
                        </>
                      )}
                    </div>
                    
                    {sandbox.resource_usage && (
                      <div className="mt-2 flex gap-4 text-xs">
                        <div className="flex items-center gap-1">
                          <span className="text-gray-500">CPU:</span>
                          <span className="font-medium">{sandbox.resource_usage.cpu_percent.toFixed(1)}%</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <span className="text-gray-500">Memory:</span>
                          <span className="font-medium">{sandbox.resource_usage.memory_mb}MB</span>
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <Button
                    size="sm"
                    variant="danger"
                    onClick={() => terminateMutation.mutate(sandbox.id)}
                    disabled={terminateMutation.isPending}
                    title="Terminate sandbox"
                  >
                    <XCircle className="w-4 h-4" />
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {completedSandboxes.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            Recent Completed ({completedSandboxes.slice(0, 5).length})
          </h3>
          <div className="space-y-3">
            {completedSandboxes.slice(0, 5).map((sandbox) => (
              <Card key={sandbox.id} className="bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-1">
                      <span className="font-mono text-xs text-gray-500">
                        {sandbox.id.slice(0, 8)}...
                      </span>
                      <StatusBadge status={sandbox.status} size="sm" />
                    </div>
                    
                    <div className="flex items-center gap-4 text-xs text-gray-600">
                      {sandbox.started_at && sandbox.completed_at && (
                        <span>
                          Duration: {formatDuration(
                            new Date(sandbox.completed_at).getTime() -
                            new Date(sandbox.started_at).getTime()
                          )}
                        </span>
                      )}
                      
                      {sandbox.metrics && (
                        <span className="text-success">
                          {(sandbox.metrics.success_rate * 100).toFixed(1)}% success
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

