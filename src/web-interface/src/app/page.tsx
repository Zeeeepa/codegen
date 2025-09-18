/**
 * Home Page Component
 * Main dashboard entry point for the Codegen Visual Interface
 */

'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import useAppStore from '@/store/app-store';
import DashboardLayout from '@/components/layout/DashboardLayout';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export default function HomePage() {
  const router = useRouter();
  const { auth, fetchAgentRuns, fetchProjects } = useAppStore();

  useEffect(() => {
    // Check authentication status
    if (!auth.isAuthenticated && !auth.isLoading) {
      router.push('/login');
      return;
    }

    // Fetch initial data if authenticated
    if (auth.isAuthenticated && auth.organization) {
      fetchAgentRuns();
      fetchProjects();
    }
  }, [auth.isAuthenticated, auth.isLoading, auth.organization, router, fetchAgentRuns, fetchProjects]);

  // Show loading spinner while checking authentication
  if (auth.isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-gray-600">Loading Codegen Visual Interface...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!auth.isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-gray-600">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return (
    <DashboardLayout>
      <div className="p-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome to Codegen Visual Interface
          </h1>
          <p className="text-gray-600">
            Manage your CICD workflows, agent runs, and projects with AI-powered orchestration.
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <QuickStatCard
            title="Active Agents"
            value="3"
            change="+2 from yesterday"
            changeType="positive"
            icon="🤖"
          />
          <QuickStatCard
            title="Workflows"
            value="12"
            change="+1 this week"
            changeType="positive"
            icon="⚡"
          />
          <QuickStatCard
            title="Projects"
            value="8"
            change="No change"
            changeType="neutral"
            icon="📁"
          />
          <QuickStatCard
            title="Success Rate"
            value="94%"
            change="+2% this month"
            changeType="positive"
            icon="✅"
          />
        </div>

        {/* Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Agent Runs</h2>
            <div className="space-y-3">
              <ActivityItem
                title="Fix authentication bug"
                status="running"
                time="2 minutes ago"
                type="agent"
              />
              <ActivityItem
                title="Update documentation"
                status="complete"
                time="1 hour ago"
                type="agent"
              />
              <ActivityItem
                title="Refactor user service"
                status="failed"
                time="3 hours ago"
                type="agent"
              />
            </div>
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Workflow Status</h2>
            <div className="space-y-3">
              <ActivityItem
                title="Production Deployment"
                status="running"
                time="Active"
                type="workflow"
              />
              <ActivityItem
                title="Code Review Process"
                status="complete"
                time="Completed"
                type="workflow"
              />
              <ActivityItem
                title="Testing Pipeline"
                status="pending"
                time="Queued"
                type="workflow"
              />
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <QuickActionCard
              title="Create Agent Run"
              description="Start a new AI agent task"
              icon="🚀"
              onClick={() => router.push('/agents/create')}
            />
            <QuickActionCard
              title="New Workflow"
              description="Design a CICD workflow"
              icon="⚙️"
              onClick={() => router.push('/workflows/create')}
            />
            <QuickActionCard
              title="View Projects"
              description="Manage your projects"
              icon="📊"
              onClick={() => router.push('/projects')}
            />
            <QuickActionCard
              title="AI Chat"
              description="Chat with AI assistant"
              icon="💬"
              onClick={() => router.push('/chat')}
            />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

// Quick stat card component
interface QuickStatCardProps {
  title: string;
  value: string;
  change: string;
  changeType: 'positive' | 'negative' | 'neutral';
  icon: string;
}

function QuickStatCard({ title, value, change, changeType, icon }: QuickStatCardProps) {
  const changeColor = {
    positive: 'text-green-600',
    negative: 'text-red-600',
    neutral: 'text-gray-600',
  }[changeType];

  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          <p className={`text-xs ${changeColor}`}>{change}</p>
        </div>
        <div className="text-2xl">{icon}</div>
      </div>
    </div>
  );
}

// Activity item component
interface ActivityItemProps {
  title: string;
  status: 'running' | 'complete' | 'failed' | 'pending';
  time: string;
  type: 'agent' | 'workflow';
}

function ActivityItem({ title, status, time, type }: ActivityItemProps) {
  const statusClasses = {
    running: 'status-running',
    complete: 'status-complete',
    failed: 'status-failed',
    pending: 'status-pending',
  };

  const typeIcon = type === 'agent' ? '🤖' : '⚡';

  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
      <div className="flex items-center space-x-3">
        <span className="text-lg">{typeIcon}</span>
        <div>
          <p className="text-sm font-medium text-gray-900">{title}</p>
          <p className="text-xs text-gray-500">{time}</p>
        </div>
      </div>
      <span className={statusClasses[status]}>{status}</span>
    </div>
  );
}

// Quick action card component
interface QuickActionCardProps {
  title: string;
  description: string;
  icon: string;
  onClick: () => void;
}

function QuickActionCard({ title, description, icon, onClick }: QuickActionCardProps) {
  return (
    <button
      onClick={onClick}
      className="card-hover text-left p-4 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
    >
      <div className="flex items-center space-x-3 mb-2">
        <span className="text-xl">{icon}</span>
        <h3 className="font-medium text-gray-900">{title}</h3>
      </div>
      <p className="text-sm text-gray-600">{description}</p>
    </button>
  );
}
