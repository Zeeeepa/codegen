import { SandboxList } from '@/components/Sandboxes/SandboxList';

export function SandboxesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Sandboxes</h1>
        <p className="text-gray-600">
          Monitor active and completed sandbox executions
        </p>
      </div>

      <SandboxList />
    </div>
  );
}

