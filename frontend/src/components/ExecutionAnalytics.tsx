/**
 * ExecutionAnalytics Component
 * Dashboard for execution history and performance analytics
 */

import { useState, useEffect } from 'react';
import {
  Calendar,
  Clock,
  CheckCircle2,
  XCircle,
  Activity,
  TrendingUp,
  Download,
  Filter,
  RefreshCw,
  BarChart3,
  PieChart,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { databaseApi } from '@/services/databaseApi';
import type { Execution, ExecutionStatus, ExecutionFilters } from '@/types/database';

// ============================================================================
// Types
// ============================================================================

interface AnalyticsStats {
  total: number;
  completed: number;
  failed: number;
  running: number;
  avgDuration: number;
  successRate: number;
}

// ============================================================================
// Helper Functions
// ============================================================================

function getStatusColor(status: ExecutionStatus): string {
  const colors: Record<ExecutionStatus, string> = {
    IDLE: 'bg-gray-100 text-gray-700',
    GENERATING: 'bg-blue-100 text-blue-700',
    EVALUATING: 'bg-purple-100 text-purple-700',
    PRUNING: 'bg-yellow-100 text-yellow-700',
    EXECUTING: 'bg-orange-100 text-orange-700',
    COMPLETED: 'bg-green-100 text-green-700',
    FAILED: 'bg-red-100 text-red-700',
  };
  return colors[status] || 'bg-gray-100 text-gray-700';
}

function getStatusIcon(status: ExecutionStatus) {
  if (status === 'COMPLETED') return <CheckCircle2 className="w-4 h-4" />;
  if (status === 'FAILED') return <XCircle className="w-4 h-4" />;
  return <Activity className="w-4 h-4 animate-spin" />;
}

function calculateDuration(createdAt: string, completedAt?: string): string {
  const start = new Date(createdAt).getTime();
  const end = completedAt ? new Date(completedAt).getTime() : Date.now();
  const durationMs = end - start;
  
  const seconds = Math.floor(durationMs / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  
  if (hours > 0) return `${hours}h ${minutes % 60}m`;
  if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
  return `${seconds}s`;
}

// ============================================================================
// Stats Card Component
// ============================================================================

function StatsCard({
  title,
  value,
  icon: Icon,
  trend,
  color = 'blue',
}: {
  title: string;
  value: string | number;
  icon: any;
  trend?: string;
  color?: 'blue' | 'green' | 'red' | 'yellow';
}) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    red: 'bg-red-100 text-red-600',
    yellow: 'bg-yellow-100 text-yellow-600',
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {trend && (
            <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              {trend}
            </p>
          )}
        </div>
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Execution Row Component
// ============================================================================

function ExecutionRow({ execution }: { execution: Execution }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-white border border-gray-200 rounded-lg">
      <div
        className="p-4 cursor-pointer hover:bg-gray-50"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 flex-1">
            {getStatusIcon(execution.status)}
            <div>
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-900">
                  Execution {execution.id.substring(0, 8)}
                </span>
                <span
                  className={`px-2 py-0.5 text-xs rounded ${getStatusColor(
                    execution.status
                  )}`}
                >
                  {execution.status}
                </span>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                Workflow: {execution.workflow_id.substring(0, 8)}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6 text-sm text-gray-600">
            <div className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              {calculateDuration(execution.created_at, execution.completed_at)}
            </div>
            <div className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              {new Date(execution.created_at).toLocaleString()}
            </div>
          </div>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-gray-200 p-4 bg-gray-50">
          {/* Context */}
          {execution.context && (
            <div className="mb-4">
              <h4 className="font-semibold text-gray-900 mb-2">Context</h4>
              <pre className="text-sm bg-white border border-gray-200 rounded p-3 overflow-x-auto">
                {JSON.stringify(execution.context, null, 2)}
              </pre>
            </div>
          )}

          {/* Results */}
          {execution.results && (
            <div className="mb-4">
              <h4 className="font-semibold text-gray-900 mb-2">Results</h4>
              <pre className="text-sm bg-white border border-gray-200 rounded p-3 overflow-x-auto">
                {JSON.stringify(execution.results, null, 2)}
              </pre>
            </div>
          )}

          {/* Logs */}
          {execution.logs && execution.logs.length > 0 && (
            <div className="mb-4">
              <h4 className="font-semibold text-gray-900 mb-2">Logs</h4>
              <div className="bg-white border border-gray-200 rounded p-3 space-y-1 max-h-64 overflow-y-auto">
                {execution.logs.map((log, i) => (
                  <div key={i} className="text-sm font-mono text-gray-700">
                    {log}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error */}
          {execution.error_message && (
            <div className="bg-red-50 border border-red-200 rounded p-3">
              <h4 className="font-semibold text-red-900 mb-1">Error</h4>
              <p className="text-sm text-red-700">{execution.error_message}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export default function ExecutionAnalytics() {
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [stats, setStats] = useState<AnalyticsStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<ExecutionStatus | ''>('');
  const [dateRange, setDateRange] = useState<'24h' | '7d' | '30d' | 'all'>('7d');

  useEffect(() => {
    loadExecutions();
  }, [statusFilter, dateRange]);

  async function loadExecutions() {
    try {
      setLoading(true);

      // Calculate date range
      let createdAfter: string | undefined;
      if (dateRange !== 'all') {
        const hours = dateRange === '24h' ? 24 : dateRange === '7d' ? 168 : 720;
        const date = new Date();
        date.setHours(date.getHours() - hours);
        createdAfter = date.toISOString();
      }

      const filters: ExecutionFilters = {
        page: 1,
        limit: 100,
        sort_by: 'created_at',
        sort_order: 'desc',
        status: statusFilter || undefined,
        created_after: createdAfter,
      };

      const response = await databaseApi.executions.list(filters);
      setExecutions(response.data);

      // Calculate stats
      const total = response.data.length;
      const completed = response.data.filter((e) => e.status === 'COMPLETED').length;
      const failed = response.data.filter((e) => e.status === 'FAILED').length;
      const running = response.data.filter(
        (e) => !['COMPLETED', 'FAILED'].includes(e.status)
      ).length;

      const durations = response.data
        .filter((e) => e.completed_at)
        .map((e) => {
          const start = new Date(e.created_at).getTime();
          const end = new Date(e.completed_at!).getTime();
          return end - start;
        });

      const avgDuration =
        durations.length > 0
          ? durations.reduce((a, b) => a + b, 0) / durations.length
          : 0;

      setStats({
        total,
        completed,
        failed,
        running,
        avgDuration: Math.floor(avgDuration / 1000), // Convert to seconds
        successRate: total > 0 ? (completed / total) * 100 : 0,
      });
    } catch (error: any) {
      console.error('Failed to load executions:', error);
      toast.error('Failed to load execution data');
    } finally {
      setLoading(false);
    }
  }

  async function exportData() {
    try {
      const csv = [
        ['ID', 'Status', 'Created', 'Completed', 'Duration', 'Error'].join(','),
        ...executions.map((e) =>
          [
            e.id,
            e.status,
            e.created_at,
            e.completed_at || '',
            calculateDuration(e.created_at, e.completed_at),
            e.error_message || '',
          ].join(',')
        ),
      ].join('\n');

      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `executions-${Date.now()}.csv`;
      a.click();
      URL.revokeObjectURL(url);

      toast.success('Exported execution data');
    } catch (error) {
      toast.error('Failed to export data');
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Execution Analytics</h2>
          <p className="text-sm text-gray-600">
            Monitor workflow execution history and performance
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadExecutions}
            className="flex items-center gap-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            onClick={exportData}
            className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatsCard
            title="Total Executions"
            value={stats.total}
            icon={BarChart3}
            color="blue"
          />
          <StatsCard
            title="Success Rate"
            value={`${stats.successRate.toFixed(1)}%`}
            icon={CheckCircle2}
            color="green"
            trend={`${stats.completed}/${stats.total} completed`}
          />
          <StatsCard
            title="Failed"
            value={stats.failed}
            icon={XCircle}
            color="red"
          />
          <StatsCard
            title="Avg Duration"
            value={`${stats.avgDuration}s`}
            icon={Clock}
            color="yellow"
          />
        </div>
      )}

      {/* Filters */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center gap-4">
          <Filter className="w-4 h-4 text-gray-500" />

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as ExecutionStatus | '')}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="COMPLETED">Completed</option>
            <option value="FAILED">Failed</option>
            <option value="EXECUTING">Running</option>
            <option value="IDLE">Idle</option>
          </select>

          {/* Date Range */}
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="all">All Time</option>
          </select>
        </div>
      </div>

      {/* Executions List */}
      {loading ? (
        <div className="text-center py-12 text-gray-500">
          Loading executions...
        </div>
      ) : executions.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <Activity className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600">No executions found</p>
          <p className="text-sm text-gray-500 mt-1">
            Try adjusting your filters
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {executions.map((execution) => (
            <ExecutionRow key={execution.id} execution={execution} />
          ))}
        </div>
      )}
    </div>
  );
}

