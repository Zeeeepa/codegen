import { DashboardSummary } from '@/components/Dashboard/DashboardSummary';
import { WorkflowList } from '@/components/Workflows/WorkflowList';
import { SandboxList } from '@/components/Sandboxes/SandboxList';

export function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Controller Dashboard
        </h1>
        <p className="text-gray-600">
          Manage workflows, monitor sandboxes, and track execution metrics
        </p>
      </div>

      <DashboardSummary />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Workflows
          </h2>
          <WorkflowList />
        </div>

        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Sandboxes
          </h2>
          <SandboxList />
        </div>
      </div>
    </div>
  );
}

