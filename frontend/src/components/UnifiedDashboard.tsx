import React, { useState, Suspense, lazy } from 'react';
import {
  LayoutDashboard,
  FileText,
  BarChart3,
  Webhook,
  Key,
  User,
  Workflow,
  Settings as SettingsIcon,
  ChevronDown,
  Menu,
  X
} from 'lucide-react';

// Lazy load heavy components for performance
const WorkflowCanvas = lazy(() => import('./WorkflowCanvas'));
const TemplateMarketplace = lazy(() => import('./TemplateMarketplace'));
const ExecutionAnalytics = lazy(() => import('./ExecutionAnalytics'));
const WebhookConfig = lazy(() => import('./WebhookConfig'));
const TokenManagement = lazy(() => import('./TokenManagement'));
const ProfileManagement = lazy(() => import('./ProfileManagement'));
const StateInspector = lazy(() => import('./StateInspector'));

type TabKey =
  | 'dashboard'
  | 'workflows'
  | 'templates'
  | 'analytics'
  | 'webhooks'
  | 'tokens'
  | 'profiles'
  | 'inspector';

interface Tab {
  key: TabKey;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  badge?: string | number;
}

const TABS: Tab[] = [
  {
    key: 'dashboard',
    label: 'Dashboard',
    icon: LayoutDashboard,
    description: 'Overview and quick actions'
  },
  {
    key: 'workflows',
    label: 'Workflows',
    icon: Workflow,
    description: 'Visual workflow editor and execution'
  },
  {
    key: 'templates',
    label: 'Templates',
    icon: FileText,
    description: 'Browse and use workflow templates'
  },
  {
    key: 'analytics',
    label: 'Analytics',
    icon: BarChart3,
    description: 'Execution metrics and insights'
  },
  {
    key: 'webhooks',
    label: 'Webhooks',
    icon: Webhook,
    description: 'Configure event notifications'
  },
  {
    key: 'tokens',
    label: 'API Tokens',
    icon: Key,
    description: 'Manage API keys and access'
  },
  {
    key: 'profiles',
    label: 'Profiles',
    icon: User,
    description: 'Agent profiles and configurations'
  },
  {
    key: 'inspector',
    label: 'Inspector',
    icon: SettingsIcon,
    description: 'Debug and inspect state'
  }
];

interface UnifiedDashboardProps {
  initialTab?: TabKey;
  onTabChange?: (tab: TabKey) => void;
}

const UnifiedDashboard: React.FC<UnifiedDashboardProps> = ({
  initialTab = 'dashboard',
  onTabChange
}) => {
  const [activeTab, setActiveTab] = useState<TabKey>(initialTab);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleTabChange = (tab: TabKey) => {
    setActiveTab(tab);
    setIsMobileMenuOpen(false);
    onTabChange?.(tab);
  };

  const activeTabInfo = TABS.find(t => t.key === activeTab);

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar Navigation */}
      <aside
        className={`
          bg-white border-r border-gray-200 
          transition-all duration-300 ease-in-out
          ${isSidebarOpen ? 'w-64' : 'w-0 lg:w-20'}
          ${isMobileMenuOpen ? 'fixed inset-y-0 left-0 z-50' : 'hidden lg:block'}
        `}
      >
        {/* Sidebar Header */}
        <div className="h-16 border-b border-gray-200 flex items-center justify-between px-4">
          {isSidebarOpen && (
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Workflow className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-gray-900">Codegen</span>
            </div>
          )}
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors hidden lg:block"
          >
            {isSidebarOpen ? (
              <X className="w-5 h-5 text-gray-600" />
            ) : (
              <Menu className="w-5 h-5 text-gray-600" />
            )}
          </button>
        </div>

        {/* Navigation Tabs */}
        <nav className="p-3 space-y-1 overflow-y-auto h-[calc(100vh-4rem)]">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.key;

            return (
              <button
                key={tab.key}
                onClick={() => handleTabChange(tab.key)}
                className={`
                  w-full flex items-center space-x-3 px-4 py-3 rounded-lg
                  transition-all duration-200
                  ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 font-medium shadow-sm'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }
                `}
                title={tab.description}
              >
                <Icon
                  className={`
                    flex-shrink-0 w-5 h-5
                    ${isActive ? 'text-blue-600' : 'text-gray-400'}
                  `}
                />
                {isSidebarOpen && (
                  <div className="flex-1 text-left">
                    <div className="text-sm">{tab.label}</div>
                    {!isActive && (
                      <div className="text-xs text-gray-400 truncate">
                        {tab.description}
                      </div>
                    )}
                  </div>
                )}
                {isSidebarOpen && tab.badge && (
                  <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 rounded-full">
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </aside>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
          <div className="flex items-center space-x-4">
            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="p-2 hover:bg-gray-100 rounded-lg lg:hidden"
            >
              <Menu className="w-6 h-6 text-gray-600" />
            </button>

            {activeTabInfo && (
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  {activeTabInfo.label}
                </h1>
                <p className="text-sm text-gray-500 hidden sm:block">
                  {activeTabInfo.description}
                </p>
              </div>
            )}
          </div>

          {/* Quick Actions */}
          <div className="flex items-center space-x-2">
            <button className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors hidden md:block">
              Export
            </button>
            <button className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors">
              + New
            </button>
          </div>
        </header>

        {/* Content Area with Suspense */}
        <div className="flex-1 overflow-auto bg-gray-50 p-6">
          <Suspense
            fallback={
              <div className="flex items-center justify-center h-64">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">Loading {activeTabInfo?.label}...</p>
                </div>
              </div>
            }
          >
            {activeTab === 'dashboard' && <DashboardView />}
            {activeTab === 'workflows' && <WorkflowCanvas chains={[]} />}
            {activeTab === 'templates' && <TemplateMarketplace />}
            {activeTab === 'analytics' && <ExecutionAnalytics />}
            {activeTab === 'webhooks' && <WebhookConfig />}
            {activeTab === 'tokens' && <TokenManagement />}
            {activeTab === 'profiles' && <ProfileManagement />}
            {activeTab === 'inspector' && <StateInspector />}
          </Suspense>
        </div>
      </main>
    </div>
  );
};

// Dashboard Overview Component
const DashboardView: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl p-8 text-white">
        <h2 className="text-3xl font-bold mb-2">Welcome to Codegen</h2>
        <p className="text-blue-100 text-lg">
          The SWE that Never Sleeps - Your 24/7 AI Coding Agent Platform
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Active Workflows"
          value="12"
          change="+3"
          icon={Workflow}
          color="blue"
        />
        <StatCard
          title="Executions"
          value="1,247"
          change="+156"
          icon={BarChart3}
          color="green"
        />
        <StatCard
          title="Templates"
          value="24"
          change="+2"
          icon={FileText}
          color="purple"
        />
        <StatCard
          title="API Tokens"
          value="8"
          change="0"
          icon={Key}
          color="orange"
        />
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <QuickActionButton
            icon={Workflow}
            title="Create Workflow"
            description="Start a new workflow from scratch"
            onClick={() => {}}
          />
          <QuickActionButton
            icon={FileText}
            title="Browse Templates"
            description="Use pre-built workflow templates"
            onClick={() => {}}
          />
          <QuickActionButton
            icon={BarChart3}
            title="View Analytics"
            description="Check execution metrics"
            onClick={() => {}}
          />
          <QuickActionButton
            icon={Webhook}
            title="Setup Webhook"
            description="Configure event notifications"
            onClick={() => {}}
          />
          <QuickActionButton
            icon={Key}
            title="Generate Token"
            description="Create new API key"
            onClick={() => {}}
          />
          <QuickActionButton
            icon={User}
            title="Manage Profiles"
            description="Configure agent profiles"
            onClick={() => {}}
          />
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Recent Activity</h3>
        <div className="space-y-3">
          <ActivityItem
            type="execution"
            title="Workflow 'Code Review' completed"
            time="2 minutes ago"
            status="success"
          />
          <ActivityItem
            type="webhook"
            title="Webhook event triggered"
            time="5 minutes ago"
            status="info"
          />
          <ActivityItem
            type="template"
            title="Template 'Frontend Dev' created"
            time="1 hour ago"
            status="success"
          />
        </div>
      </div>
    </div>
  );
};

// Stat Card Component
const StatCard: React.FC<{
  title: string;
  value: string;
  change: string;
  icon: React.ComponentType<{ className?: string }>;
  color: 'blue' | 'green' | 'purple' | 'orange';
}> = ({ title, value, change, icon: Icon, color }) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    orange: 'bg-orange-50 text-orange-600'
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
        {change !== '0' && (
          <span
            className={`text-sm font-medium ${
              change.startsWith('+') ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {change}
          </span>
        )}
      </div>
      <h3 className="text-2xl font-bold text-gray-900 mb-1">{value}</h3>
      <p className="text-sm text-gray-600">{title}</p>
    </div>
  );
};

// Quick Action Button
const QuickActionButton: React.FC<{
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  onClick: () => void;
}> = ({ icon: Icon, title, description, onClick }) => {
  return (
    <button
      onClick={onClick}
      className="flex items-start space-x-3 p-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors text-left"
    >
      <div className="p-2 bg-white rounded-lg shadow-sm">
        <Icon className="w-5 h-5 text-blue-600" />
      </div>
      <div className="flex-1">
        <h4 className="font-medium text-gray-900 mb-1">{title}</h4>
        <p className="text-sm text-gray-600">{description}</p>
      </div>
      <ChevronDown className="w-4 h-4 text-gray-400 rotate-[-90deg]" />
    </button>
  );
};

// Activity Item
const ActivityItem: React.FC<{
  type: string;
  title: string;
  time: string;
  status: 'success' | 'info' | 'warning' | 'error';
}> = ({ type, title, time, status }) => {
  const statusColors = {
    success: 'bg-green-100 text-green-700',
    info: 'bg-blue-100 text-blue-700',
    warning: 'bg-yellow-100 text-yellow-700',
    error: 'bg-red-100 text-red-700'
  };

  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
      <div className="flex items-center space-x-3">
        <div className={`w-2 h-2 rounded-full ${statusColors[status].replace('bg-', 'bg-').replace('-100', '-500')}`} />
        <div>
          <p className="text-sm font-medium text-gray-900">{title}</p>
          <p className="text-xs text-gray-500">{time}</p>
        </div>
      </div>
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusColors[status]}`}>
        {status}
      </span>
    </div>
  );
};

export default UnifiedDashboard;

