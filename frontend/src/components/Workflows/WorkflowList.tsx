import { useWorkflows, useToggleWorkflow, useExecuteWorkflow } from '@/hooks/useWorkflows';
import { Card } from '@/components/Common/Card';
import { Button } from '@/components/Common/Button';
import { StatusBadge } from '@/components/Common/StatusBadge';
import { Play, Power, Settings } from 'lucide-react';
import { formatRelativeTime } from '@/utils/formatters';

export function WorkflowList() {
  const { data: workflows, isLoading, error } = useWorkflows();
  const toggleMutation = useToggleWorkflow();
  const executeMutation = useExecuteWorkflow();

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
          <p className="text-error">Failed to load workflows</p>
          <p className="text-sm text-gray-600 mt-2">{error.message}</p>
        </div>
      </Card>
    );
  }

  if (!workflows || workflows.length === 0) {
    return (
      <Card>
        <div className="text-center py-12">
          <p className="text-gray-600">No workflows found</p>
          <Button className="mt-4" size="sm">
            Create Workflow
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {workflows.map((workflow) => (
        <Card key={workflow.id} className="hover:shadow-lg transition-shadow">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h3 className="text-lg font-semibold text-gray-900">
                  {workflow.name}
                </h3>
                <StatusBadge status={workflow.status} size="sm" />
                {workflow.active_executions && workflow.active_executions > 0 && (
                  <span className="text-sm text-accent font-medium">
                    {workflow.active_executions} running
                  </span>
                )}
              </div>
              
              <p className="text-gray-600 text-sm mb-3">{workflow.description}</p>
              
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span>Updated {formatRelativeTime(workflow.updated_at)}</span>
                {workflow.schedule && (
                  <span className="flex items-center gap-1">
                    <Settings className="w-3 h-3" />
                    {workflow.schedule}
                  </span>
                )}
                {workflow.tags && workflow.tags.length > 0 && (
                  <div className="flex gap-1">
                    {workflow.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-2 py-0.5 bg-gray-100 rounded text-xs"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
            
            <div className="flex items-center gap-2 ml-4">
              <Button
                size="sm"
                variant="ghost"
                onClick={() => toggleMutation.mutate(workflow.id)}
                disabled={toggleMutation.isPending}
                title={workflow.enabled ? 'Disable workflow' : 'Enable workflow'}
              >
                <Power
                  className={`w-4 h-4 ${
                    workflow.enabled ? 'text-success' : 'text-gray-400'
                  }`}
                />
              </Button>
              
              <Button
                size="sm"
                variant="primary"
                onClick={() => executeMutation.mutate(workflow.id)}
                disabled={!workflow.enabled || executeMutation.isPending}
                title="Execute workflow"
              >
                <Play className="w-4 h-4" />
                Run
              </Button>
            </div>
          </div>
          
          {workflow.parallel_execution && (
            <div className="mt-3 pt-3 border-t border-gray-100">
              <span className="text-xs text-gray-600">
                Parallel execution enabled (max {workflow.max_instances} instances)
              </span>
            </div>
          )}
        </Card>
      ))}
    </div>
  );
}

