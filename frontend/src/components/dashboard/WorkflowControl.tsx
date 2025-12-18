import React, { useState, useEffect } from 'react';
import {
  Play,
  Pause,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Clock,
  Loader,
  XCircle,
  Search,
  Filter
} from 'lucide-react';
import { codegenApi } from '@/services/api';
import { AgentRun, RunStatus } from '@/types';
import toast from 'react-hot-toast';

const WorkflowControl: React.FC = () => {
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [filteredRuns, setFilteredRuns] = useState<AgentRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<RunStatus | 'all'>('all');
  const [isResumeModalOpen, setIsResumeModalOpen] = useState(false);
  const [selectedRun, setSelectedRun] = useState<AgentRun | null>(null);
  const [resumePrompt, setResumePrompt] = useState('');
  const [resuming, setResuming] = useState(false);

  const orgId = 'default-org'; // TODO: Get from auth context
  const apiKey = import.meta.env.VITE_API_KEY || 'demo-key';

  useEffect(() => {
    fetchRuns();
    // Auto-refresh every 5 seconds
    const interval = setInterval(fetchRuns, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Apply filters
    let filtered = runs;

    if (statusFilter !== 'all') {
      filtered = filtered.filter(run => run.status === statusFilter);
    }

    if (searchTerm) {
      filtered = filtered.filter(
        run =>
          run.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
          run.prompt?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredRuns(filtered);
  }, [runs, statusFilter, searchTerm]);

  const fetchRuns = async () => {
    try {
      setLoading(true);
      const fetchedRuns = await codegenApi.fetchAllRuns(orgId, apiKey);
      setRuns(fetchedRuns);
    } catch (err: any) {
      console.error('[WorkflowControl] Error fetching runs:', err);
      toast.error('Failed to fetch runs');
    } finally {
      setLoading(false);
    }
  };

  const handleResumeClick = (run: AgentRun) => {
    setSelectedRun(run);
    setResumePrompt('');
    setIsResumeModalOpen(true);
  };

  const handleResumeSubmit = async () => {
    if (!selectedRun || !resumePrompt.trim()) {
      toast.error('Please provide instructions for resuming the run');
      return;
    }

    try {
      setResuming(true);
      await codegenApi.resumeRun(orgId, apiKey, selectedRun.id, resumePrompt);
      toast.success('Run resumed successfully!');
      setIsResumeModalOpen(false);
      setSelectedRun(null);
      setResumePrompt('');
      // Refresh runs list
      setTimeout(fetchRuns, 1000);
    } catch (err: any) {
      console.error('[WorkflowControl] Error resuming run:', err);
      toast.error(err.message || 'Failed to resume run');
    } finally {
      setResuming(false);
    }
  };

  const getStatusIcon = (status: RunStatus) => {
    switch (status) {
      case 'running':
        return <Loader className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: RunStatus) => {
    switch (status) {
      case 'running':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'completed':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'failed':
        return 'bg-red-100 text-red-700 border-red-200';
      case 'pending':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  if (loading && !runs.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Loader className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading workflow controls...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Workflow Control</h2>
        <p className="text-gray-600 text-sm mt-1">
          Manage and control agent run executions
        </p>
      </div>

      {/* Filters and Search */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by ID or prompt..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Status Filter */}
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as RunStatus | 'all')}
              className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="running">Running</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
          </div>

          {/* Refresh Button */}
          <button
            onClick={fetchRuns}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>

        {/* Filter Stats */}
        <div className="mt-4 flex items-center space-x-4 text-sm text-gray-600">
          <span>Total: {runs.length}</span>
          <span>•</span>
          <span>Filtered: {filteredRuns.length}</span>
        </div>
      </div>

      {/* Runs List */}
      {filteredRuns.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 font-medium mb-2">No runs found</p>
          <p className="text-gray-500 text-sm">
            {runs.length === 0
              ? 'Create your first agent run to get started'
              : 'Try adjusting your filters'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredRuns.map((run) => (
            <div
              key={run.id}
              className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(run.status)}
                  <div>
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="font-mono text-sm text-gray-900">
                        {run.id.substring(0, 12)}...
                      </span>
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${getStatusColor(run.status)}`}>
                        {run.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">
                      {run.model || 'No model specified'}
                    </p>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-2">
                  {(run.status === 'failed' || run.status === 'completed') && (
                    <button
                      onClick={() => handleResumeClick(run)}
                      className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-1"
                    >
                      <Play className="w-3 h-3" />
                      <span>Resume</span>
                    </button>
                  )}
                  {run.status === 'running' && (
                    <button
                      className="px-3 py-1.5 bg-gray-200 text-gray-700 text-sm rounded-lg cursor-not-allowed flex items-center space-x-1"
                      disabled
                    >
                      <Pause className="w-3 h-3" />
                      <span>Running</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Prompt */}
              <div className="bg-gray-50 rounded-lg p-3 mb-3 border border-gray-200">
                <p className="text-sm text-gray-700 font-medium mb-1">Prompt:</p>
                <p className="text-sm text-gray-900">{run.prompt}</p>
              </div>

              {/* Result/Error */}
              {run.result && (
                <div className="bg-green-50 rounded-lg p-3 mb-3 border border-green-200">
                  <p className="text-sm text-green-700 font-medium mb-1">Result:</p>
                  <p className="text-sm text-green-900">{run.result}</p>
                </div>
              )}

              {run.error && (
                <div className="bg-red-50 rounded-lg p-3 mb-3 border border-red-200">
                  <p className="text-sm text-red-700 font-medium mb-1">Error:</p>
                  <p className="text-sm text-red-900">{run.error}</p>
                </div>
              )}

              {/* Timestamps */}
              <div className="flex items-center space-x-4 text-xs text-gray-500">
                <span>Created: {new Date(run.created_at || '').toLocaleString()}</span>
                {run.updated_at && (
                  <>
                    <span>•</span>
                    <span>Updated: {new Date(run.updated_at).toLocaleString()}</span>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Resume Modal */}
      {isResumeModalOpen && selectedRun && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6">
            <div className="flex items-start justify-between mb-6">
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Resume Run</h3>
                <p className="text-sm text-gray-600">
                  Provide additional instructions to continue this run
                </p>
              </div>
              <button
                onClick={() => setIsResumeModalOpen(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            {/* Original Run Info */}
            <div className="bg-gray-50 rounded-lg p-4 mb-4 border border-gray-200">
              <p className="text-sm text-gray-700 font-medium mb-2">Original Prompt:</p>
              <p className="text-sm text-gray-900">{selectedRun.prompt}</p>
              <div className="mt-3 flex items-center space-x-2">
                <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${getStatusColor(selectedRun.status)}`}>
                  {selectedRun.status}
                </span>
                <span className="text-xs text-gray-500">
                  ID: {selectedRun.id.substring(0, 12)}...
                </span>
              </div>
            </div>

            {/* Resume Instructions */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Resume Instructions
              </label>
              <textarea
                value={resumePrompt}
                onChange={(e) => setResumePrompt(e.target.value)}
                placeholder="Enter instructions for continuing this run..."
                rows={6}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              />
              <p className="text-xs text-gray-500 mt-2">
                Provide context and instructions for what the agent should do next
              </p>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end space-x-3">
              <button
                onClick={() => setIsResumeModalOpen(false)}
                disabled={resuming}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleResumeSubmit}
                disabled={resuming || !resumePrompt.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center space-x-2"
              >
                {resuming ? (
                  <>
                    <Loader className="w-4 h-4 animate-spin" />
                    <span>Resuming...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    <span>Resume Run</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowControl;

