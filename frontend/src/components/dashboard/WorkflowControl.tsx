import React, { useState, useEffect } from 'react';
import { Play, Pause, Square, RefreshCw, Settings, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { getCodegenClient, Workflow, CodegenAPIError } from '@/services/codegenClient';

interface WorkflowControlProps {
  workflows?: Workflow[];
  onToggleWorkflow?: (id: string, enabled: boolean) => void;
  onExecuteWorkflow?: (id: string) => void;
  onPauseWorkflow?: (id: string) => void;
  onResumeWorkflow?: (id: string) => void;
  onStopWorkflow?: (id: string) => void;
}

const WorkflowControl: React.FC<WorkflowControlProps> = () => {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Fetch workflows from API on mount
  useEffect(() => {
    fetchWorkflows();
  }, []);

  const fetchWorkflows = async () => {
    try {
      setLoading(true);
      setError(null);
      const client = getCodegenClient();
      const data = await client.fetchWorkflows();
      setWorkflows(data);
    } catch (err) {
      const error = err as CodegenAPIError;
      setError(error.message || 'Failed to fetch workflows');
      console.error('Error fetching workflows:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleWorkflow = async (id: string, enabled: boolean) => {
    try {
      setActionLoading(id);
      const client = getCodegenClient();
      await client.toggleWorkflowEnabled(id, enabled);
      
      // Update local state
      setWorkflows(prev =>
        prev.map(wf => (wf.id === id ? { ...wf, enabled } : wf))
      );
    } catch (err) {
      const error = err as CodegenAPIError;
      alert(`Failed to toggle workflow: ${error.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleExecuteWorkflow = async (id: string) => {
    try {
      setActionLoading(id);
      const client = getCodegenClient();
      await client.executeWorkflow(id);
      
      // Update local state
      setWorkflows(prev =>
        prev.map(wf => (wf.id === id ? { ...wf, status: 'running' } : wf))
      );
      
      // Refresh workflows after a short delay
      setTimeout(() => fetchWorkflows(), 2000);
    } catch (err) {
      const error = err as CodegenAPIError;
      alert(`Failed to execute workflow: ${error.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handlePauseWorkflow = async (id: string) => {
    try {
      setActionLoading(id);
      const client = getCodegenClient();
      await client.pauseWorkflow(id);
      
      // Update local state
      setWorkflows(prev =>
        prev.map(wf => (wf.id === id ? { ...wf, status: 'paused' } : wf))
      );
    } catch (err) {
      const error = err as CodegenAPIError;
      alert(`Failed to pause workflow: ${error.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleResumeWorkflow = async (id: string) => {
    try {
      setActionLoading(id);
      const client = getCodegenClient();
      await client.resumeWorkflow(id);
      
      // Update local state
      setWorkflows(prev =>
        prev.map(wf => (wf.id === id ? { ...wf, status: 'running' } : wf))
      );
    } catch (err) {
      const error = err as CodegenAPIError;
      alert(`Failed to resume workflow: ${error.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleStopWorkflow = async (id: string) => {
    try {
      setActionLoading(id);
      const client = getCodegenClient();
      await client.stopWorkflow(id);
      
      // Update local state
      setWorkflows(prev =>
        prev.map(wf => (wf.id === id ? { ...wf, status: 'stopped' } : wf))
      );
    } catch (err) {
      const error = err as CodegenAPIError;
      alert(`Failed to stop workflow: ${error.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Play className="h-4 w-4 text-green-500" />;
      case 'paused':
        return <Pause className="h-4 w-4 text-yellow-500" />;
      case 'stopped':
        return <Square className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'stopped':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center mb-6">
          <div className="h-8 w-48 bg-gray-200 rounded animate-pulse"></div>
          <div className="h-10 w-32 bg-gray-200 rounded animate-pulse"></div>
        </div>
        {[1, 2, 3].map(i => (
          <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="h-6 w-3/4 bg-gray-200 rounded animate-pulse mb-4"></div>
            <div className="h-4 w-full bg-gray-200 rounded animate-pulse"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-start space-x-3">
          <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-red-800 font-semibold mb-1">Error Loading Workflows</h3>
            <p className="text-red-700 text-sm mb-4">{error}</p>
            <button
              onClick={fetchWorkflows}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2"
            >
              <RefreshCw className="h-4 w-4" />
              <span>Retry</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (workflows.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center">
        <Settings className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-gray-700 font-semibold mb-2">No Workflows Found</h3>
        <p className="text-gray-500 text-sm">
          There are no workflows configured for this organization.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Workflow Control</h2>
        <button
          onClick={fetchWorkflows}
          disabled={loading}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {workflows.map((workflow) => (
        <div
          key={workflow.id}
          className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
        >
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-2">
                <h3 className="text-lg font-semibold text-gray-900">{workflow.name}</h3>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium border flex items-center space-x-1 ${getStatusColor(
                    workflow.status
                  )}`}
                >
                  {getStatusIcon(workflow.status)}
                  <span className="capitalize">{workflow.status}</span>
                </span>
              </div>
              {workflow.description && (
                <p className="text-gray-600 text-sm mb-3">{workflow.description}</p>
              )}
              {workflow.last_run && (
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <Clock className="h-4 w-4" />
                  <span>Last run: {new Date(workflow.last_run).toLocaleString()}</span>
                </div>
              )}
            </div>

            <div className="flex items-center space-x-2">
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={workflow.enabled}
                  onChange={(e) => handleToggleWorkflow(workflow.id, e.target.checked)}
                  disabled={actionLoading === workflow.id}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                <span className="ml-3 text-sm font-medium text-gray-700">
                  {workflow.enabled ? 'Enabled' : 'Disabled'}
                </span>
              </label>
            </div>
          </div>

          <div className="flex items-center space-x-2 pt-4 border-t border-gray-100">
            {workflow.status === 'idle' && (
              <button
                onClick={() => handleExecuteWorkflow(workflow.id)}
                disabled={!workflow.enabled || actionLoading === workflow.id}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Play className="h-4 w-4" />
                <span>Execute</span>
              </button>
            )}

            {workflow.status === 'running' && (
              <>
                <button
                  onClick={() => handlePauseWorkflow(workflow.id)}
                  disabled={actionLoading === workflow.id}
                  className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
                >
                  <Pause className="h-4 w-4" />
                  <span>Pause</span>
                </button>
                <button
                  onClick={() => handleStopWorkflow(workflow.id)}
                  disabled={actionLoading === workflow.id}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
                >
                  <Square className="h-4 w-4" />
                  <span>Stop</span>
                </button>
              </>
            )}

            {workflow.status === 'paused' && (
              <>
                <button
                  onClick={() => handleResumeWorkflow(workflow.id)}
                  disabled={actionLoading === workflow.id}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
                >
                  <Play className="h-4 w-4" />
                  <span>Resume</span>
                </button>
                <button
                  onClick={() => handleStopWorkflow(workflow.id)}
                  disabled={actionLoading === workflow.id}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
                >
                  <Square className="h-4 w-4" />
                  <span>Stop</span>
                </button>
              </>
            )}

            {workflow.status === 'stopped' && (
              <button
                onClick={() => handleExecuteWorkflow(workflow.id)}
                disabled={!workflow.enabled || actionLoading === workflow.id}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Play className="h-4 w-4" />
                <span>Restart</span>
              </button>
            )}

            <button
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center space-x-2 ml-auto"
            >
              <Settings className="h-4 w-4" />
              <span>Configure</span>
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default WorkflowControl;

