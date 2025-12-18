import React, { useState, useEffect } from 'react';
import { Eye, RefreshCw, AlertCircle, Clock, CheckCircle, XCircle, PlayCircle, Filter } from 'lucide-react';
import { getCodegenClient, ExecutionRun, CodegenAPIError, RunFilters } from '@/services/codegenClient';

interface MonitorDashboardProps {
  runs?: ExecutionRun[];
}

const MonitorDashboard: React.FC<MonitorDashboardProps> = () => {
  const [runs, setRuns] = useState<ExecutionRun[]>([]);
  const [filteredRuns, setFilteredRuns] = useState<ExecutionRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<'all' | 'success' | 'failure' | 'running' | 'pending'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showLogs, setShowLogs] = useState(false);
  const [selectedRun, setSelectedRun] = useState<ExecutionRun | null>(null);
  const [selectedRunLogs, setSelectedRunLogs] = useState<string[]>([]);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Fetch runs on mount
  useEffect(() => {
    fetchRuns();
  }, []);

  // Filter runs when status filter or search query changes
  useEffect(() => {
    filterRuns();
  }, [runs, statusFilter, searchQuery]);

  const fetchRuns = async (filters?: RunFilters) => {
    try {
      setLoading(true);
      setError(null);
      const client = getCodegenClient();
      
      const filterParams: RunFilters = filters || {
        status: statusFilter === 'all' ? undefined : statusFilter,
      };
      
      const data = await client.fetchRuns(filterParams);
      setRuns(data);
    } catch (err) {
      const error = err as CodegenAPIError;
      setError(error.message || 'Failed to fetch runs');
      console.error('Error fetching runs:', err);
    } finally {
      setLoading(false);
    }
  };

  const filterRuns = () => {
    let filtered = runs;

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(run => run.status === statusFilter);
    }

    // Apply search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(run =>
        run.workflow_name?.toLowerCase().includes(query) ||
        run.id.toLowerCase().includes(query)
      );
    }

    setFilteredRuns(filtered);
  };

  const handleViewLogs = async (run: ExecutionRun) => {
    try {
      setSelectedRun(run);
      setShowLogs(true);
      setLoadingLogs(true);
      
      const client = getCodegenClient();
      const logs = await client.getRunLogs(run.id);
      setSelectedRunLogs(logs);
    } catch (err) {
      const error = err as CodegenAPIError;
      console.error('Error fetching logs:', err);
      setSelectedRunLogs([`Error loading logs: ${error.message}`]);
    } finally {
      setLoadingLogs(false);
    }
  };

  const handleRetryRun = async (runId: string) => {
    try {
      setActionLoading(runId);
      const client = getCodegenClient();
      const result = await client.retryRun(runId);
      
      // Refresh runs list
      await fetchRuns();
      
      alert(`Run retry initiated. New run ID: ${result.run_id}`);
    } catch (err) {
      const error = err as CodegenAPIError;
      alert(`Failed to retry run: ${error.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failure':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'running':
        return <PlayCircle className="h-4 w-4 text-blue-500 animate-pulse" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'failure':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'running':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatDuration = (started: string, completed?: string) => {
    if (!completed) return 'In progress...';
    
    const start = new Date(started).getTime();
    const end = new Date(completed).getTime();
    const duration = Math.floor((end - start) / 1000);
    
    const hours = Math.floor(duration / 3600);
    const minutes = Math.floor((duration % 3600) / 60);
    const seconds = duration % 60;
    
    if (hours > 0) return `${hours}h ${minutes}m ${seconds}s`;
    if (minutes > 0) return `${minutes}m ${seconds}s`;
    return `${seconds}s`;
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center mb-6">
          <div className="h-8 w-48 bg-gray-200 rounded animate-pulse"></div>
          <div className="h-10 w-32 bg-gray-200 rounded animate-pulse"></div>
        </div>
        
        <div className="flex space-x-2 mb-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-10 w-24 bg-gray-200 rounded animate-pulse"></div>
          ))}
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          {[1, 2, 3].map(i => (
            <div key={i} className="p-6 border-b border-gray-100">
              <div className="h-6 w-3/4 bg-gray-200 rounded animate-pulse mb-4"></div>
              <div className="h-4 w-full bg-gray-200 rounded animate-pulse"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-start space-x-3">
          <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-red-800 font-semibold mb-1">Error Loading Runs</h3>
            <p className="text-red-700 text-sm mb-4">{error}</p>
            <button
              onClick={() => fetchRuns()}
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

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Monitor Dashboard</h2>
        <button
          onClick={() => fetchRuns()}
          disabled={loading}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        {/* Status Filters */}
        <div className="flex flex-wrap gap-2">
          {['all', 'success', 'failure', 'running', 'pending'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status as typeof statusFilter)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                statusFilter === status
                  ? 'bg-purple-600 text-white'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              {status === 'all' ? 'All' : status.charAt(0).toUpperCase() + status.slice(1)}
              {status !== 'all' && (
                <span className="ml-2 px-2 py-0.5 bg-white/20 rounded text-xs">
                  {runs.filter(r => r.status === status).length}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Search */}
        <input
          type="text"
          placeholder="Search by workflow name or ID..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        />
      </div>

      {/* Runs Table */}
      {filteredRuns.length === 0 ? (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center">
          <Filter className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-gray-700 font-semibold mb-2">No Runs Found</h3>
          <p className="text-gray-500 text-sm">
            {searchQuery || statusFilter !== 'all'
              ? 'Try adjusting your filters'
              : 'No execution runs have been created yet'}
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
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
              {filteredRuns.map((run) => (
                <tr key={run.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {run.workflow_name || 'Unknown Workflow'}
                      </div>
                      <div className="text-xs text-gray-500">ID: {run.id}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium border flex items-center space-x-1 w-fit ${getStatusColor(
                        run.status
                      )}`}
                    >
                      {getStatusIcon(run.status)}
                      <span className="capitalize">{run.status}</span>
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(run.started_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {formatDuration(run.started_at, run.completed_at)}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleViewLogs(run)}
                        className="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors flex items-center space-x-1"
                      >
                        <Eye className="h-4 w-4" />
                        <span>Logs</span>
                      </button>
                      {run.status === 'failure' && (
                        <button
                          onClick={() => handleRetryRun(run.id)}
                          disabled={actionLoading === run.id}
                          className="px-3 py-1 bg-orange-100 text-orange-700 rounded hover:bg-orange-200 transition-colors flex items-center space-x-1 disabled:opacity-50"
                        >
                          <RefreshCw className={`h-4 w-4 ${actionLoading === run.id ? 'animate-spin' : ''}`} />
                          <span>Retry</span>
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Logs Modal */}
      {showLogs && selectedRun && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] flex flex-col">
            {/* Modal Header */}
            <div className="flex justify-between items-center p-6 border-b border-gray-200">
              <div>
                <h3 className="text-xl font-bold text-gray-900">Execution Logs</h3>
                <p className="text-sm text-gray-500 mt-1">
                  {selectedRun.workflow_name} - Run ID: {selectedRun.id}
                </p>
              </div>
              <button
                onClick={() => setShowLogs(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-auto p-6">
              {loadingLogs ? (
                <div className="flex items-center justify-center py-12">
                  <RefreshCw className="h-8 w-8 text-purple-600 animate-spin" />
                </div>
              ) : (
                <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm text-green-400 overflow-auto">
                  {selectedRunLogs.length > 0 ? (
                    selectedRunLogs.map((log, index) => (
                      <div key={index} className="mb-1">
                        {log}
                      </div>
                    ))
                  ) : (
                    <div className="text-gray-500">No logs available for this run</div>
                  )}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-6 border-t border-gray-200">
              <button
                onClick={() => setShowLogs(false)}
                className="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MonitorDashboard;

