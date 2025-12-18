import React, { useState, useEffect } from 'react';
import { 
  RefreshCw, 
  Clock, 
  CheckCircle, 
  XCircle, 
  Loader, 
  ExternalLink,
  FileText,
  GitBranch,
  Calendar
} from 'lucide-react';
import { codegenApi } from '@/services/api';
import { AgentRun, RunStatus } from '@/types';

const MonitorDashboard: React.FC = () => {
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<AgentRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const orgId = 'default-org'; // TODO: Get from auth context
  const apiKey = import.meta.env.VITE_API_KEY || 'demo-key';

  useEffect(() => {
    fetchRuns();
    // Auto-refresh every 5 seconds
    const interval = setInterval(() => {
      fetchRuns(true);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchRuns = async (isBackground = false) => {
    try {
      if (!isBackground) setLoading(true);
      else setRefreshing(true);
      
      const fetchedRuns = await codegenApi.fetchAllRuns(orgId, apiKey);
      setRuns(fetchedRuns);
      setError(null);
      
      // Update selected run if it exists in new data
      if (selectedRun) {
        const updated = fetchedRuns.find(r => r.id === selectedRun.id);
        if (updated) setSelectedRun(updated);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch runs');
      console.error('[MonitorDashboard] Error fetching runs:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
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

  const getStatusBadge = (status: RunStatus) => {
    const colors = {
      running: 'bg-blue-100 text-blue-700',
      completed: 'bg-green-100 text-green-700',
      failed: 'bg-red-100 text-red-700',
      pending: 'bg-yellow-100 text-yellow-700'
    };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[status]}`}>
        {status.toUpperCase()}
      </span>
    );
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  if (loading && !runs.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Loader className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading runs...</p>
        </div>
      </div>
    );
  }

  if (error && !runs.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 font-medium mb-2">Error Loading Runs</p>
          <p className="text-gray-600 text-sm mb-4">{error}</p>
          <button
            onClick={() => fetchRuns()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!runs.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 font-medium mb-2">No Runs Yet</p>
          <p className="text-gray-500 text-sm">Create your first agent run to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Agent Runs Monitor</h2>
          <p className="text-gray-600 text-sm mt-1">
            Real-time monitoring of all agent executions
          </p>
        </div>
        <button
          onClick={() => fetchRuns()}
          disabled={refreshing}
          className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          label="Total Runs"
          value={runs.length}
          icon={FileText}
          color="blue"
        />
        <StatCard
          label="Running"
          value={runs.filter(r => r.status === 'running').length}
          icon={Loader}
          color="blue"
        />
        <StatCard
          label="Completed"
          value={runs.filter(r => r.status === 'completed').length}
          icon={CheckCircle}
          color="green"
        />
        <StatCard
          label="Failed"
          value={runs.filter(r => r.status === 'failed').length}
          icon={XCircle}
          color="red"
        />
      </div>

      {/* Runs Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Run ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Prompt
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Model
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {runs.map((run) => (
                <tr
                  key={run.id}
                  onClick={() => setSelectedRun(run)}
                  className={`hover:bg-gray-50 cursor-pointer transition-colors ${
                    selectedRun?.id === run.id ? 'bg-blue-50' : ''
                  }`}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(run.status)}
                      {getStatusBadge(run.status)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                    {run.id.substring(0, 8)}...
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                    {run.prompt || 'No prompt'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {run.model || 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {formatDate(run.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedRun(run);
                      }}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Selected Run Details */}
      {selectedRun && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Run Details</h3>
              <div className="flex items-center space-x-3">
                {getStatusIcon(selectedRun.status)}
                {getStatusBadge(selectedRun.status)}
                <span className="text-sm text-gray-600 font-mono">
                  ID: {selectedRun.id}
                </span>
              </div>
            </div>
            <button
              onClick={() => setSelectedRun(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Left Column */}
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-2">
                  <Calendar className="w-4 h-4 inline mr-1" />
                  Created
                </label>
                <p className="text-gray-900">{formatDate(selectedRun.created_at)}</p>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-700 block mb-2">
                  <Clock className="w-4 h-4 inline mr-1" />
                  Updated
                </label>
                <p className="text-gray-900">{formatDate(selectedRun.updated_at)}</p>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-700 block mb-2">
                  Model
                </label>
                <p className="text-gray-900">{selectedRun.model || 'Not specified'}</p>
              </div>
            </div>

            {/* Right Column */}
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-2">
                  Prompt
                </label>
                <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-900 border border-gray-200">
                  {selectedRun.prompt}
                </div>
              </div>

              {selectedRun.pr_urls && selectedRun.pr_urls.length > 0 && (
                <div>
                  <label className="text-sm font-medium text-gray-700 block mb-2">
                    <GitBranch className="w-4 h-4 inline mr-1" />
                    Pull Requests
                  </label>
                  <div className="space-y-2">
                    {selectedRun.pr_urls.map((url, idx) => (
                      <a
                        key={idx}
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center space-x-2 text-blue-600 hover:text-blue-800 text-sm"
                      >
                        <ExternalLink className="w-4 h-4" />
                        <span>{url}</span>
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Result/Error Section */}
          {selectedRun.result && (
            <div className="mt-6">
              <label className="text-sm font-medium text-gray-700 block mb-2">
                Result
              </label>
              <div className="bg-green-50 rounded-lg p-4 text-sm text-gray-900 border border-green-200">
                {selectedRun.result}
              </div>
            </div>
          )}

          {selectedRun.error && (
            <div className="mt-6">
              <label className="text-sm font-medium text-gray-700 block mb-2">
                Error
              </label>
              <div className="bg-red-50 rounded-lg p-4 text-sm text-red-900 border border-red-200">
                {selectedRun.error}
              </div>
            </div>
          )}

          {selectedRun.summary && (
            <div className="mt-6">
              <label className="text-sm font-medium text-gray-700 block mb-2">
                Summary
              </label>
              <div className="bg-blue-50 rounded-lg p-4 text-sm text-gray-900 border border-blue-200">
                {selectedRun.summary}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Stat Card Component
interface StatCardProps {
  label: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  color: 'blue' | 'green' | 'red' | 'yellow';
}

const StatCard: React.FC<StatCardProps> = ({ label, value, icon: Icon, color }) => {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    red: 'bg-red-50 text-red-600',
    yellow: 'bg-yellow-50 text-yellow-600'
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">{label}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${colors[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
};

export default MonitorDashboard;

