import { WorkflowList } from '@/components/Workflows/WorkflowList';
import { Button } from '@/components/Common/Button';
import { Plus } from 'lucide-react';

export function WorkflowsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Workflows</h1>
          <p className="text-gray-600">
            Manage and execute your automated workflows
          </p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          Create Workflow
        </Button>
      </div>

      <WorkflowList />
    </div>
  );
}

