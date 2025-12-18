import React, { useState, useEffect } from 'react';
import { Play, Pause, Square, RefreshCw, Settings, Clock, CheckCircle, XCircle } from 'lucide-react';

interface Workflow {
  id: string;
  name: string;
  description: string;
  status: 'running' | 'paused' | 'stopped' | 'idle';
  enabled: boolean;
  lastRun?: string;
  nextRun?: string;
}

interface WorkflowControlProps {
  workflows?: Workflow[];
  onToggleWorkflow?: (id: string, enabled: boolean) => void;
  onExecuteWorkflow?: (id: string) => void;
  onPauseWorkflow?: (id: string) => void;
  onResumeWorkflow?: (id: string) => void;
  onStopWorkflow?: (id: string) => void;
}

const WorkflowControl: React.FC<WorkflowControlProps> = ({
  workflows = [],
  onToggleWorkflow,
  onExecuteWorkflow,
  onPauseWorkflow,
  onResumeWorkflow,
  onStopWorkflow
}) => {
  const [localWorkflows, setLocalWorkflows] = useState<Workflow[]>(workflows);

  useEffect(() => {
    if (workflows.length > 0) {
      setLocalWorkflows(workflows);
    } else {
      // Mock data for testing
      setLocalWorkflows([
        {
          id: '1',
          name: 'Data Processing Pipeline',
          description: 'Process and transform incoming data',
          status: 'idle',
          enabled: true,
          lastRun: '2025-12-17 14:30:00',
          nextRun: '2025-12-18 14:30:00'
        },
        {
          id: '2',
          name: 'Code Review Automation',
          description: 'Automated code review and analysis',
          status: 'running',
          enabled: true,
          lastRun: '2025-12-18 00:15:00'
        },
        {
          id: '3',
          name: 'Report Generation',
          description: 'Generate daily reports and metrics',
          status: 'paused',
          enabled: true,
          lastRun: '2025-12-17 22:00:00'
        }
      ]);
    }
  }, [workflows]);

  const handleToggle = (id: string, enabled: boolean) => {
    setLocalWorkflows(prev =>
      prev.map(wf => wf.id === id ? { ...wf, enabled } : wf)
    );
    onToggleWorkflow?.(id, enabled);
  };

  const handleExecute = (id: string) => {
    setLocalWorkflows(prev =>
      prev.map(wf => wf.id === id ? { ...wf, status: 'running' } : wf)
    );
    onExecuteWorkflow?.(id);
  };

  const handlePause = (id: string) => {
    setLocalWorkflows(prev =>
      prev.map(wf => wf.id === id ? { ...wf, status: 'paused' } : wf)
    );
    onPauseWorkflow?.(id);
  };

  const handleResume = (id: string) => {
    setLocalWorkflows(prev =>
      prev.map(wf => wf.id === id ? { ...wf, status: 'running' } : wf)
    );
    onResumeWorkflow?.(id);
  };

  const handleStop = (id: string) => {
    setLocalWorkflows(prev =>
      prev.map(wf => wf.id === id ? { ...wf, status: 'stopped' } : wf)
    );
    onStopWorkflow?.(id);
  };

  const getStatusIcon = (status: Workflow['status']) => {
    switch (status) {
      case 'running':
        return <Play className="w-4 h-4 text-green-500" />;
      case 'paused':
        return <Pause className="w-4 h-4 text-yellow-500" />;
      case 'stopped':
        return <Square className="w-4 h-4 text-red-500" />;
      default:
        return <CheckCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: Workflow['status']) => {
    const badges = {
      running: 'bg-green-100 text-green-800',
      paused: 'bg-yellow-100 text-yellow-800',
      stopped: 'bg-red-100 text-red-800',
      idle: 'bg-gray-100 text-gray-800'
    };
    return badges[status];
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Workflow Control</h2>
        <p className="text-gray-600">Enable/disable workflows and trigger execution</p>
      </div>

      <div className="space-y-4">
        {localWorkflows.map((workflow) => (
          <div
            key={workflow.id}
            className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  {getStatusIcon(workflow.status)}
                  <h3 className="text-lg font-semibold text-gray-900">{workflow.name}</h3>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadge(workflow.status)}`}>
                    {workflow.status.toUpperCase()}
                  </span>
                </div>
                <p className="text-sm text-gray-600 ml-7">{workflow.description}</p>
              </div>

              {/* Enable/Disable Toggle */}
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={workflow.enabled}
                  onChange={(e) => handleToggle(workflow.id, e.target.checked)}
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            {/* Workflow Info */}
            <div className="flex items-center space-x-6 text-sm text-gray-600 mb-4 ml-7">
              {workflow.lastRun && (
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4" />
                  <span>Last run: {workflow.lastRun}</span>
                </div>
              )}
              {workflow.nextRun && (
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4" />
                  <span>Next run: {workflow.nextRun}</span>
                </div>
              )}
            </div>

            {/* Control Buttons */}
            <div className="flex items-center space-x-2 ml-7">
              {workflow.status === 'idle' && (
                <button
                  onClick={() => handleExecute(workflow.id)}
                  disabled={!workflow.enabled}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center space-x-2 transition-colors"
                >
                  <Play className="w-4 h-4" />
                  <span>Execute</span>
                </button>
              )}

              {workflow.status === 'running' && (
                <>
                  <button
                    onClick={() => handlePause(workflow.id)}
                    className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 flex items-center space-x-2 transition-colors"
                  >
                    <Pause className="w-4 h-4" />
                    <span>Pause</span>
                  </button>
                  <button
                    onClick={() => handleStop(workflow.id)}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center space-x-2 transition-colors"
                  >
                    <Square className="w-4 h-4" />
                    <span>Stop</span>
                  </button>
                </>
              )}

              {workflow.status === 'paused' && (
                <>
                  <button
                    onClick={() => handleResume(workflow.id)}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center space-x-2 transition-colors"
                  >
                    <RefreshCw className="w-4 h-4" />
                    <span>Resume</span>
                  </button>
                  <button
                    onClick={() => handleStop(workflow.id)}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center space-x-2 transition-colors"
                  >
                    <Square className="w-4 h-4" />
                    <span>Stop</span>
                  </button>
                </>
              )}

              {workflow.status === 'stopped' && (
                <button
                  onClick={() => handleExecute(workflow.id)}
                  disabled={!workflow.enabled}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center space-x-2 transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>Restart</span>
                </button>
              )}

              <button
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center space-x-2 transition-colors"
              >
                <Settings className="w-4 h-4" />
                <span>Configure</span>
              </button>
            </div>
          </div>
        ))}
      </div>

      {localWorkflows.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <Settings className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-2">No workflows configured</p>
          <p className="text-sm text-gray-500">Create a workflow to get started</p>
        </div>
      )}
    </div>
  );
};

export default WorkflowControl;

