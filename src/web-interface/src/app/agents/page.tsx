'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import useAppStore from '@/store/app-store';
import DashboardLayout from '@/components/layout/DashboardLayout';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { AgentRun } from '@/types/codegen';
import { 
  Plus, 
  Search, 
  Filter, 
  ExternalLink, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  MoreHorizontal,
  RefreshCw
} from 'lucide-react';
import { clsx } from 'clsx';
import { format } from 'date-fns';

export default function AgentRunsPage() {
  const router = useRouter();
  const { agents, auth, fetchAgentRuns, selectAgentRun } = useAppStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  useEffect(() => {
    if (auth.isAuthenticated && auth.organization) {
      fetchAgentRuns();
    }
  }, [auth.isAuthenticated, auth.organization, fetchAgentRuns]);

  const filteredRuns = agents.runs.filter(run => {
    const matchesSearch = run.prompt.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         run.summary?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || run.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'RUNNING':
        return <LoadingSpinner size="sm" className="w-4 h-4" />;
      case 'COMPLETE':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'FAILED':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'CANCELLED':
        return <XCircle className="w-4 h-4 text-gray-500" />;
      default:
        return <Clock className="w-4 h-4 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'RUNNING':
        return 'bg-blue-100 text-blue-800';
      case 'COMPLETE':
        return 'bg-green-100 text-green-800';
      case 'FAILED':
        return 'bg-red-100 text-red-800';
      case 'CANCELLED':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  const handleCreateRun = () => {
    router.push('/agents/create');
  };

  const handleRunClick = (run: AgentRun) => {
    selectAgentRun(run);
    router.push(`/agents/${run.id}`);
  };

  return (
    <DashboardLayout>
      <div className="p-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Agent Runs</h1>
              <p className="text-gray-600 mt-1">
                Manage and monitor your AI agent executions
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={fetchAgentRuns}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </button>
              <button
                onClick={handleCreateRun}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create Agent Run
              </button>
            </div>
          </div>
        </div>

        {/* Filters and Search */}
        <div className="mb-6 flex flex-col sm:flex-row sm:items-center space-y-3 sm:space-y-0 sm:space-x-4">
          <div className="flex-1">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search agent runs..."
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Filter className="h-5 w-5 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Status</option>
              <option value="RUNNING">Running</option>
              <option value="COMPLETE">Complete</option>
              <option value="FAILED">Failed</option>
              <option value="PENDING">Pending</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>
        </div>

        {/* Agent Runs List */}
        {agents.isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <LoadingSpinner size="lg" />
              <p className="mt-4 text-gray-600">Loading agent runs...</p>
            </div>
          </div>
        ) : agents.error ? (
          <div className="rounded-md bg-red-50 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <AlertCircle className="h-5 w-5 text-red-400" />
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{agents.error}</p>
                </div>
              </div>
            </div>
          </div>
        ) : filteredRuns.length === 0 ? (
          <div className="text-center py-12">
            <div className="mx-auto h-12 w-12 text-gray-400">
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No agent runs</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by creating a new agent run.
            </p>
            <div className="mt-6">
              <button
                onClick={handleCreateRun}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create Agent Run
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
              {filteredRuns.map((run) => (
                <li key={run.id}>
                  <button
                    onClick={() => handleRunClick(run)}
                    className="block w-full text-left hover:bg-gray-50 px-6 py-4 transition-colors duration-150"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3 mb-2">
                          {getStatusIcon(run.status)}
                          <span className={clsx(
                            'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                            getStatusColor(run.status)
                          )}>
                            {run.status}
                          </span>
                          <span className="text-sm text-gray-500">
                            {format(new Date(run.created_at), 'MMM d, yyyy h:mm a')}
                          </span>
                        </div>
                        <div className="mb-2">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {run.prompt}
                          </p>
                          {run.summary && (
                            <p className="text-sm text-gray-500 truncate">
                              {run.summary}
                            </p>
                          )}
                        </div>
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          {run.model && (
                            <span>Model: {run.model}</span>
                          )}
                          {run.progress_percentage !== undefined && (
                            <span>Progress: {run.progress_percentage}%</span>
                          )}
                          {run.github_pull_requests && run.github_pull_requests.length > 0 && (
                            <span className="flex items-center">
                              <ExternalLink className="w-3 h-3 mr-1" />
                              {run.github_pull_requests.length} PR{run.github_pull_requests.length !== 1 ? 's' : ''}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center">
                        <MoreHorizontal className="w-5 h-5 text-gray-400" />
                      </div>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}