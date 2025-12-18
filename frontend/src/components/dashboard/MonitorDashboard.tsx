import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle, XCircle, AlertCircle, Eye, Download, Filter, Search, RefreshCw } from 'lucide-react';

interface ExecutionRun {
  id: string;
  workflowName: string;
  status: 'success' | 'failure' | 'running' | 'pending';
  startTime: string;
  endTime?: string;
  duration?: string;
  logs?: string[];
  context?: Record<string, any>;
}

interface MonitorDashboardProps {
  runs?: ExecutionRun[];
  onViewLogs?: (runId: string) => void;
  onRetryRun?: (runId: string) => void;
  onRefresh?: () => void;
}

const MonitorDashboard: React.FC<MonitorDashboardProps> = ({
  runs = [],
  onViewLogs,
  onRetryRun,
  onRefresh
}) => {
  const [localRuns, setLocalRuns] = useState<ExecutionRun[]>(runs);
  const [selectedRun, setSelectedRun] = useState<ExecutionRun | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showLogs, setShowLogs] = useState(false);

  useEffect(() => {
    if (runs.length > 0) {
      setLocalRuns(runs);
    } else {
      // Mock data for testing
      setLocalRuns([
        {
          id: '1',
          workflowName: 'Data Processing Pipeline',
          status: 'success',
          startTime: '2025-12-18 00:30:00',
          endTime: '2025-12-18 00:35:23',
          duration: '5m 23s',
          logs: [
            '[00:30:00] Starting workflow execution...',
            '[00:30:15] Fetching input data from repository',
            '[00:31:30] Processing 1,250 records',
            '[00:34:45] Validation passed: 100% success rate',
            '[00:35:23] Workflow completed successfully'
          ],
          context: {
            recordsProcessed: 1250,
            successRate: '100%',
            repository: 'Zeeeepa/codegen'
          }
        },
        {
          id: '2',
          workflowName: 'Code Review Automation',
          status: 'running',
          startTime: '2025-12-18 00:40:12',
          logs: [
            '[00:40:12] Workflow started',
            '[00:40:30] Analyzing pull request #195',
            '[00:42:15] Running linting checks...',
            '[00:43:00] Executing unit tests (in progress)'
          ],
          context: {
            pullRequest: '#195',
            branch: 'Frontend2',
            filesChanged: 12
          }
        },
        {
          id: '3',
          workflowName: 'Report Generation',
          status: 'failure',
          startTime: '2025-12-17 22:00:00',
          endTime: '2025-12-17 22:02:15',
          duration: '2m 15s',
          logs: [
            '[22:00:00] Starting report generation',
            '[22:01:00] Fetching analytics data',
            '[22:01:45] Error: Database connection timeout',
            '[22:02:00] Attempting retry...',
            '[22:02:15] Fatal: Maximum retries exceeded'
          ],
          context: {
            error: 'Database connection timeout',
            retries: 3
          }
        },
        {
          id: '4',
          workflowName: 'Data Processing Pipeline',
          status: 'success',
          startTime: '2025-12-17 14:30:00',
          endTime: '2025-12-17 14:34:50',
          duration: '4m 50s',
          logs: [
            '[14:30:00] Starting workflow execution...',
            '[14:32:00] Processing complete'
          ],
          context: {
            recordsProcessed: 980,
            successRate: '98.5%'
          }
        },
        {
          id: '5',
          workflowName: 'Code Review Automation',
          status: 'pending',
          startTime: '2025-12-18 01:00:00',
          logs: ['[01:00:00] Workflow queued, waiting for available resources...'],
          context: {
            queuePosition: 2
          }
        }
      ]);
    }
  }, [runs]);

  const getStatusIcon = (status: ExecutionRun['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failure':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'running':
        return <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'pending':
        return <Clock className="w-5 h-5 text-yellow-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: ExecutionRun['status']) => {
    const badges = {
      success: 'bg-green-100 text-green-800',
      failure: 'bg-red-100 text-red-800',
      running: 'bg-blue-100 text-blue-800',
      pending: 'bg-yellow-100 text-yellow-800'
    };
    return badges[status];
  };

  const handleViewLogs = (run: ExecutionRun) => {
    setSelectedRun(run);
    setShowLogs(true);
    onViewLogs?.(run.id);
  };

  const handleRetry = (runId: string) => {
    onRetryRun?.(runId);
  };

  const filteredRuns = localRuns.filter(run => {
    const matchesStatus = statusFilter === 'all' || run.status === statusFilter;
    const matchesSearch = run.workflowName.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         run.id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const statusCounts = {
    all: localRuns.length,
    success: localRuns.filter(r => r.status === 'success').length,
    failure: localRuns.filter(r => r.status === 'failure').length,
    running: localRuns.filter(r => r.status === 'running').length,
    pending: localRuns.filter(r => r.status === 'pending').length
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Monitor Dashboard</h2>
            <p className="text-gray-600">Real-time execution monitoring and logs</p>
          </div>
          <button
            onClick={onRefresh}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>

        {/* Status Summary */}
        <div className="grid grid-cols-5 gap-4 mb-6">
          {[
            { key: 'all', label: 'All', count: statusCounts.all, color: 'bg-gray-100 text-gray-800' },
            { key: 'success', label: 'Success', count: statusCounts.success, color: 'bg-green-100 text-green-800' },
            { key: 'failure', label: 'Failed', count: statusCounts.failure, color: 'bg-red-100 text-red-800' },
            { key: 'running', label: 'Running', count: statusCounts.running, color: 'bg-blue-100 text-blue-800' },
            { key: 'pending', label: 'Pending', count: statusCounts.pending, color: 'bg-yellow-100 text-yellow-800' }
          ].map(({ key, label, count, color }) => (
            <button
              key={key}
              onClick={() => setStatusFilter(key)}
              className={`p-4 rounded-lg border-2 transition-all ${
                statusFilter === key
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 bg-white hover:border-gray-300'
              }`}
            >
              <div className={`text-sm font-medium mb-1 ${color} inline-block px-2 py-1 rounded-full`}>
                {label}
              </div>
              <div className="text-2xl font-bold text-gray-900">{count}</div>
            </button>
          ))}
        </div>

        {/* Search and Filter */}
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by workflow name or run ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center space-x-2 transition-colors">
            <Filter className="w-4 h-4" />
            <span>Filters</span>
          </button>
        </div>
      </div>

      {/* Runs Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Workflow
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Run ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Start Time
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Duration
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredRuns.map((run) => (
              <tr key={run.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(run.status)}
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadge(run.status)}`}>
                      {run.status.toUpperCase()}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{run.workflowName}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-600 font-mono">{run.id}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-600">{run.startTime}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-600">{run.duration || '-'}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button
                    onClick={() => handleViewLogs(run)}
                    className="text-blue-600 hover:text-blue-900 mr-4"
                  >
                    <Eye className="w-5 h-5 inline" />
                  </button>
                  {run.status === 'failure' && (
                    <button
                      onClick={() => handleRetry(run.id)}
                      className="text-green-600 hover:text-green-900"
                    >
                      <RefreshCw className="w-5 h-5 inline" />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredRuns.length === 0 && (
          <div className="text-center py-12">
            <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 mb-2">No runs found</p>
            <p className="text-sm text-gray-500">Try adjusting your filters or search query</p>
          </div>
        )}
      </div>

      {/* Logs Modal */}
      {showLogs && selectedRun && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] flex flex-col">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-gray-900">{selectedRun.workflowName}</h3>
                  <p className="text-sm text-gray-600">Run ID: {selectedRun.id}</p>
                </div>
                <button
                  onClick={() => setShowLogs(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {/* Context */}
              {selectedRun.context && (
                <div className="mb-6">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Context</h4>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <pre className="text-xs text-gray-800 font-mono">
                      {JSON.stringify(selectedRun.context, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {/* Logs */}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Execution Logs</h4>
                <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm">
                  {selectedRun.logs?.map((log, index) => (
                    <div key={index} className="text-green-400 mb-1">
                      {log}
                    </div>
                  ))}
                  {!selectedRun.logs?.length && (
                    <div className="text-gray-500">No logs available</div>
                  )}
                </div>
              </div>
            </div>

            <div className="p-6 border-t border-gray-200 flex justify-end space-x-2">
              <button
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center space-x-2"
              >
                <Download className="w-4 h-4" />
                <span>Export Logs</span>
              </button>
              <button
                onClick={() => setShowLogs(false)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
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

