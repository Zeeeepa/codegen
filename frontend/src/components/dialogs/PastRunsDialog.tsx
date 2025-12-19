/**
 * Past Runs Dialog
 * Displays all historical agent runs with search, filter, and pin/unpin actions
 */

import React, { useState, useMemo } from 'react';
import { X, Search, Filter, Pin, PinOff, CheckCircle, XCircle, Clock, Play, Pause, ExternalLink } from 'lucide-react';
import { AgentRun } from '../SingleViewDashboard';

interface PastRunsDialogProps {
  isOpen: boolean;
  onClose: () => void;
  runs: AgentRun[];
  pinnedRunIds: string[];
  onTogglePin: (runId: string) => void;
}

const PastRunsDialog: React.FC<PastRunsDialogProps> = ({
  isOpen,
  onClose,
  runs,
  pinnedRunIds,
  onTogglePin
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'success' | 'failure' | 'running' | 'pending' | 'paused'>('all');
  const [sortBy, setSortBy] = useState<'date' | 'duration' | 'status'>('date');

  // Filter and sort runs
  const filteredRuns = useMemo(() => {
    let filtered = runs;

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(run =>
        run.workflow_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        run.id.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(run => run.status === statusFilter);
    }

    // Sort runs
    filtered = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'date':
          return new Date(b.started_at).getTime() - new Date(a.started_at).getTime();
        case 'duration':
          return (b.duration || 0) - (a.duration || 0);
        case 'status':
          return a.status.localeCompare(b.status);
        default:
          return 0;
      }
    });

    return filtered;
  }, [runs, searchQuery, statusFilter, sortBy]);

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
        return <CheckCircle className="w-4 h-4" />;
      case 'failure':
        return <XCircle className="w-4 h-4" />;
      case 'running':
        return <Play className="w-4 h-4 animate-pulse" />;
      case 'pending':
        return <Clock className="w-4 h-4" />;
      case 'paused':
        return <Pause className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  const formatDuration = (duration?: number) => {
    if (!duration) return '-';
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    return `${minutes}m ${seconds}s`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-6xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Past Agent Runs</h2>
            <p className="text-sm text-gray-600 mt-1">
              View all historical runs, search, filter, and manage pinned items
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-6 h-6 text-gray-600" />
          </button>
        </div>

        {/* Filters and Search */}
        <div className="p-6 border-b border-gray-200 space-y-4">
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by workflow name or run ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-3">
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-600" />
              <span className="text-sm font-medium text-gray-700">Status:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as any)}
                className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All</option>
                <option value="success">Success</option>
                <option value="failure">Failure</option>
                <option value="running">Running</option>
                <option value="pending">Pending</option>
                <option value="paused">Paused</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-700">Sort by:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="date">Date</option>
                <option value="duration">Duration</option>
                <option value="status">Status</option>
              </select>
            </div>

            <div className="ml-auto text-sm text-gray-600">
              Showing {filteredRuns.length} of {runs.length} runs
            </div>
          </div>
        </div>

        {/* Runs Table */}
        <div className="flex-1 overflow-auto">
          {filteredRuns.length === 0 ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <Clock className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600">No runs found</p>
              </div>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 sticky top-0">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Pin
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Workflow
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Started
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredRuns.map((run) => {
                  const isPinned = pinnedRunIds.includes(run.id);
                  return (
                    <tr key={run.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => onTogglePin(run.id)}
                          className="p-1 hover:bg-gray-200 rounded transition-colors"
                          title={isPinned ? 'Unpin' : 'Pin'}
                        >
                          {isPinned ? (
                            <PinOff className="w-4 h-4 text-blue-600" />
                          ) : (
                            <Pin className="w-4 h-4 text-gray-400" />
                          )}
                        </button>
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          <div className="font-medium text-gray-900">
                            {run.workflow_name || 'Unnamed Workflow'}
                          </div>
                          <div className="text-xs text-gray-500">ID: {run.id.slice(0, 12)}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(run.status)}`}>
                          {getStatusIcon(run.status)}
                          <span className="capitalize">{run.status}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {new Date(run.started_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {formatDuration(run.duration)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button className="flex items-center space-x-1 text-blue-600 hover:text-blue-800 transition-colors">
                          <span>View</span>
                          <ExternalLink className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            {pinnedRunIds.length} pinned run{pinnedRunIds.length !== 1 ? 's' : ''}
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default PastRunsDialog;

