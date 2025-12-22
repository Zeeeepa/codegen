/**
 * Single View Dashboard - Unified Management Interface
 * 
 * Requirements:
 * - Single tab view (NO multi-tab navigation)
 * - Header showing "Active Agent Runs: <Number>" with hover dropdown
 * - Pinned runs always visible at top
 * - Active runs below pinned section
 * - Dialogs for: Past Runs, Chainings, Task Templates, Workflows
 * - Visual PRD → CICD flow management
 * - Real API execution with provided credentials
 */

import React, { useState, useEffect } from 'react';
import {
  Play,
  Pause,
  CheckCircle,
  XCircle,
  Clock,
  Pin,
  PinOff,
  ChevronDown,
  History,
  Link2,
  FileText,
  Workflow as WorkflowIcon,
  Settings,
  RefreshCw,
  ExternalLink,
  Maximize2
} from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../store';
import { CodegenClient } from '../services/codegenClient';

// Dialog Components (will be imported after creation)
import PastRunsDialog from './dialogs/PastRunsDialog';
import ChainingsDialog from './dialogs/ChainingsDialog';
import TaskTemplatesDialog from './dialogs/TaskTemplatesDialog';
import WorkflowsDialog from './dialogs/WorkflowsDialog';
import PRDFlowDialog from './dialogs/PRDFlowDialog';

// Types
export interface AgentRun {
  id: string;
  workflow_id?: string;
  workflow_name?: string;
  status: 'pending' | 'running' | 'success' | 'failure' | 'paused';
  started_at: string;
  completed_at?: string;
  duration?: number;
  progress?: number;
  current_step?: string;
  logs?: string[];
  context?: Record<string, any>;
  isPinned?: boolean;
}

interface SingleViewDashboardProps {
  apiKey: string;
  orgId: string;
}

const SingleViewDashboard: React.FC<SingleViewDashboardProps> = ({ apiKey, orgId }) => {
  // State Management
  const [activeRuns, setActiveRuns] = useState<AgentRun[]>([]);
  const [pinnedRuns, setPinnedRuns] = useState<AgentRun[]>([]);
  const [allRuns, setAllRuns] = useState<AgentRun[]>([]);
  const [isHeaderDropdownOpen, setIsHeaderDropdownOpen] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Dialog States
  const [isPastRunsOpen, setIsPastRunsOpen] = useState(false);
  const [isChainingsOpen, setIsChainingsOpen] = useState(false);
  const [isTemplatesOpen, setIsTemplatesOpen] = useState(false);
  const [isWorkflowsOpen, setIsWorkflowsOpen] = useState(false);
  const [isPRDFlowOpen, setIsPRDFlowOpen] = useState(false);

  // API Client
  const [apiClient] = useState(() => new CodegenClient(apiKey, orgId));

  // Load pinned runs from localStorage on mount
  useEffect(() => {
    const savedPinnedIds = localStorage.getItem('pinnedRunIds');
    if (savedPinnedIds) {
      try {
        const pinnedIds: string[] = JSON.parse(savedPinnedIds);
        // Filter pinned runs from all runs
        const pinned = allRuns.filter(run => pinnedIds.includes(run.id));
        setPinnedRuns(pinned);
      } catch (error) {
        console.error('Failed to parse pinned run IDs:', error);
      }
    }
  }, [allRuns]);

  // Fetch runs on mount and set up polling
  useEffect(() => {
    fetchRuns();
    
    // Poll every 5 seconds for active runs
    const pollInterval = setInterval(() => {
      fetchRuns(true); // Silent refresh
    }, 5000);

    return () => clearInterval(pollInterval);
  }, []);

  const fetchRuns = async (silent = false) => {
    if (!silent) setRefreshing(true);
    
    try {
      // Fetch all runs from API
      const runs = await apiClient.fetchRuns({ limit: 100 });
      
      setAllRuns(runs);
      
      // Filter active runs (pending, running, paused)
      const active = runs.filter(run => 
        ['pending', 'running', 'paused'].includes(run.status)
      );
      setActiveRuns(active);
      
      // Update pinned runs with latest data
      const pinnedIds = JSON.parse(localStorage.getItem('pinnedRunIds') || '[]');
      const pinned = runs.filter(run => pinnedIds.includes(run.id));
      setPinnedRuns(pinned);
    } catch (error) {
      console.error('Failed to fetch runs:', error);
    } finally {
      if (!silent) setRefreshing(false);
    }
  };

  const togglePinRun = (runId: string) => {
    const pinnedIds = JSON.parse(localStorage.getItem('pinnedRunIds') || '[]');
    const isPinned = pinnedIds.includes(runId);
    
    let newPinnedIds: string[];
    if (isPinned) {
      // Unpin
      newPinnedIds = pinnedIds.filter((id: string) => id !== runId);
    } else {
      // Pin (max 10 pinned runs)
      if (pinnedIds.length >= 10) {
        alert('Maximum 10 pinned runs allowed. Unpin one first.');
        return;
      }
      newPinnedIds = [...pinnedIds, runId];
    }
    
    localStorage.setItem('pinnedRunIds', JSON.stringify(newPinnedIds));
    
    // Update pinned runs state
    const pinned = allRuns.filter(run => newPinnedIds.includes(run.id));
    setPinnedRuns(pinned);
  };

  const getStatusColor = (status: AgentRun['status']) => {
    switch (status) {
      case 'success':
        return 'text-green-600 bg-green-50';
      case 'failure':
        return 'text-red-600 bg-red-50';
      case 'running':
        return 'text-blue-600 bg-blue-50';
      case 'pending':
        return 'text-yellow-600 bg-yellow-50';
      case 'paused':
        return 'text-gray-600 bg-gray-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusIcon = (status: AgentRun['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-5 h-5" />;
      case 'failure':
        return <XCircle className="w-5 h-5" />;
      case 'running':
        return <Play className="w-5 h-5 animate-pulse" />;
      case 'pending':
        return <Clock className="w-5 h-5" />;
      case 'paused':
        return <Pause className="w-5 h-5" />;
      default:
        return <Clock className="w-5 h-5" />;
    }
  };

  const formatDuration = (duration?: number) => {
    if (!duration) return '-';
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    return `${minutes}m ${seconds}s`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Left: Title */}
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <WorkflowIcon className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">CodeGen Manager</h1>
                <p className="text-xs text-gray-500">Autonomous Workflow Orchestration</p>
              </div>
            </div>

            {/* Center: Active Runs Counter */}
            <div className="relative">
              <button
                onMouseEnter={() => setIsHeaderDropdownOpen(true)}
                onMouseLeave={() => setIsHeaderDropdownOpen(false)}
                onClick={() => setIsHeaderDropdownOpen(!isHeaderDropdownOpen)}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
              >
                <span className="text-sm font-medium text-blue-900">
                  Active Agent Runs:
                </span>
                <span className="text-lg font-bold text-blue-600">
                  {activeRuns.length}
                </span>
                <ChevronDown className={`w-4 h-4 text-blue-600 transition-transform ${
                  isHeaderDropdownOpen ? 'rotate-180' : ''
                }`} />
              </button>

              {/* Dropdown on Hover */}
              {isHeaderDropdownOpen && activeRuns.length > 0 && (
                <div 
                  className="absolute top-full mt-2 right-0 w-96 bg-white rounded-lg shadow-xl border border-gray-200 max-h-96 overflow-y-auto z-50"
                  onMouseEnter={() => setIsHeaderDropdownOpen(true)}
                  onMouseLeave={() => setIsHeaderDropdownOpen(false)}
                >
                  <div className="p-3 border-b border-gray-200">
                    <h3 className="font-semibold text-gray-900">Active Runs</h3>
                  </div>
                  <div className="divide-y divide-gray-100">
                    {activeRuns.map((run) => (
                      <div
                        key={run.id}
                        className="p-3 hover:bg-gray-50 cursor-pointer transition-colors"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <div className={`${getStatusColor(run.status)} p-1 rounded`}>
                                {getStatusIcon(run.status)}
                              </div>
                              <span className="font-medium text-gray-900 text-sm">
                                {run.workflow_name || 'Unnamed Workflow'}
                              </span>
                            </div>
                            {run.current_step && (
                              <p className="text-xs text-gray-600 mt-1 ml-7">
                                Current: {run.current_step}
                              </p>
                            )}
                            {run.progress !== undefined && (
                              <div className="mt-2 ml-7">
                                <div className="w-full bg-gray-200 rounded-full h-1.5">
                                  <div
                                    className="bg-blue-600 h-1.5 rounded-full transition-all"
                                    style={{ width: `${run.progress}%` }}
                                  />
                                </div>
                              </div>
                            )}
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              // Navigate to run details
                            }}
                            className="ml-2 p-1 hover:bg-gray-200 rounded"
                          >
                            <ExternalLink className="w-4 h-4 text-gray-400" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Right: Action Buttons */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => fetchRuns()}
                disabled={refreshing}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title="Refresh"
              >
                <RefreshCw className={`w-5 h-5 text-gray-600 ${refreshing ? 'animate-spin' : ''}`} />
              </button>
              <button
                onClick={() => setIsPRDFlowOpen(true)}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors"
              >
                PRD Flow
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Action Buttons Row */}
        <div className="mb-8 flex flex-wrap gap-3">
          <button
            onClick={() => setIsPastRunsOpen(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-white hover:bg-gray-50 border border-gray-300 rounded-lg transition-colors"
          >
            <History className="w-5 h-5 text-gray-600" />
            <span className="font-medium text-gray-700">Past Agent Runs</span>
          </button>
          
          <button
            onClick={() => setIsChainingsOpen(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-white hover:bg-gray-50 border border-gray-300 rounded-lg transition-colors"
          >
            <Link2 className="w-5 h-5 text-gray-600" />
            <span className="font-medium text-gray-700">Chainings</span>
          </button>
          
          <button
            onClick={() => setIsTemplatesOpen(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-white hover:bg-gray-50 border border-gray-300 rounded-lg transition-colors"
          >
            <FileText className="w-5 h-5 text-gray-600" />
            <span className="font-medium text-gray-700">Task Templates</span>
          </button>
          
          <button
            onClick={() => setIsWorkflowsOpen(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-white hover:bg-gray-50 border border-gray-300 rounded-lg transition-colors"
          >
            <WorkflowIcon className="w-5 h-5 text-gray-600" />
            <span className="font-medium text-gray-700">Workflows</span>
          </button>
        </div>

        {/* Pinned Runs Section */}
        {pinnedRuns.length > 0 && (
          <section className="mb-8">
            <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
              <Pin className="w-5 h-5 mr-2 text-blue-600" />
              Pinned Agent Runs
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {pinnedRuns.map((run) => (
                <RunCard
                  key={run.id}
                  run={run}
                  isPinned={true}
                  onTogglePin={togglePinRun}
                  getStatusColor={getStatusColor}
                  getStatusIcon={getStatusIcon}
                  formatDuration={formatDuration}
                />
              ))}
            </div>
          </section>
        )}

        {/* Active Runs Section */}
        <section>
          <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
            <Play className="w-5 h-5 mr-2 text-green-600" />
            Active Agent Runs
            {activeRuns.length > 0 && (
              <span className="ml-2 px-2 py-0.5 text-xs font-medium bg-green-100 text-green-700 rounded-full">
                {activeRuns.length}
              </span>
            )}
          </h2>
          
          {activeRuns.length === 0 ? (
            <div className="bg-white rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
              <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Runs</h3>
              <p className="text-gray-600 mb-4">Start a new workflow or chain to see active runs here</p>
              <button
                onClick={() => setIsWorkflowsOpen(true)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
              >
                Create Workflow
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {activeRuns.map((run) => (
                <RunCard
                  key={run.id}
                  run={run}
                  isPinned={pinnedRuns.some(p => p.id === run.id)}
                  onTogglePin={togglePinRun}
                  getStatusColor={getStatusColor}
                  getStatusIcon={getStatusIcon}
                  formatDuration={formatDuration}
                />
              ))}
            </div>
          )}
        </section>
      </main>

      {/* Dialogs */}
      <PastRunsDialog
        isOpen={isPastRunsOpen}
        onClose={() => setIsPastRunsOpen(false)}
        runs={allRuns}
        pinnedRunIds={pinnedRuns.map(r => r.id)}
        onTogglePin={togglePinRun}
      />
      
      <ChainingsDialog
        isOpen={isChainingsOpen}
        onClose={() => setIsChainingsOpen(false)}
      />
      
      <TaskTemplatesDialog
        isOpen={isTemplatesOpen}
        onClose={() => setIsTemplatesOpen(false)}
      />
      
      <WorkflowsDialog
        isOpen={isWorkflowsOpen}
        onClose={() => setIsWorkflowsOpen(false)}
      />
      
      <PRDFlowDialog
        isOpen={isPRDFlowOpen}
        onClose={() => setIsPRDFlowOpen(false)}
      />
    </div>
  );
};

// Run Card Component
interface RunCardProps {
  run: AgentRun;
  isPinned: boolean;
  onTogglePin: (id: string) => void;
  getStatusColor: (status: AgentRun['status']) => string;
  getStatusIcon: (status: AgentRun['status']) => JSX.Element;
  formatDuration: (duration?: number) => string;
}

const RunCard: React.FC<RunCardProps> = ({
  run,
  isPinned,
  onTogglePin,
  getStatusColor,
  getStatusIcon,
  formatDuration
}) => {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 text-sm mb-1">
            {run.workflow_name || 'Unnamed Workflow'}
          </h3>
          <p className="text-xs text-gray-500">ID: {run.id.slice(0, 8)}</p>
        </div>
        <button
          onClick={() => onTogglePin(run.id)}
          className="p-1 hover:bg-gray-100 rounded transition-colors"
          title={isPinned ? 'Unpin' : 'Pin'}
        >
          {isPinned ? (
            <PinOff className="w-4 h-4 text-blue-600" />
          ) : (
            <Pin className="w-4 h-4 text-gray-400" />
          )}
        </button>
      </div>

      {/* Status Badge */}
      <div className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium mb-3 ${getStatusColor(run.status)}`}>
        {getStatusIcon(run.status)}
        <span className="capitalize">{run.status}</span>
      </div>

      {/* Progress Bar */}
      {run.progress !== undefined && run.status === 'running' && (
        <div className="mb-3">
          <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
            <span>Progress</span>
            <span>{run.progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ width: `${run.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Current Step */}
      {run.current_step && (
        <div className="mb-3 text-sm">
          <span className="text-gray-500">Current:</span>
          <span className="ml-1 text-gray-900">{run.current_step}</span>
        </div>
      )}

      {/* Metadata */}
      <div className="space-y-1 text-xs text-gray-500">
        <div className="flex items-center justify-between">
          <span>Started:</span>
          <span>{new Date(run.started_at).toLocaleString()}</span>
        </div>
        {run.completed_at && (
          <div className="flex items-center justify-between">
            <span>Duration:</span>
            <span>{formatDuration(run.duration)}</span>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="mt-4 flex items-center space-x-2">
        <button className="flex-1 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded text-xs font-medium transition-colors">
          View Details
        </button>
        {run.status === 'running' && (
          <button className="p-1.5 bg-yellow-100 hover:bg-yellow-200 text-yellow-700 rounded transition-colors">
            <Pause className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

export default SingleViewDashboard;

