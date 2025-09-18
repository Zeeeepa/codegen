'use client';

import React, { ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import useAppStore from '@/store/app-store';
import { 
  Home, 
  Settings, 
  Users, 
  GitBranch, 
  MessageSquare, 
  FolderOpen, 
  Activity, 
  Bell,
  Search,
  Menu,
  X,
  ChevronDown
} from 'lucide-react';
import { clsx } from 'clsx';

interface DashboardLayoutProps {
  children: ReactNode;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const router = useRouter();
  const { auth, ui, toggleSidebar, setActiveView, logout } = useAppStore();

  const navigationItems = [
    { name: 'Dashboard', href: '/', icon: Home, view: 'dashboard' as const },
    { name: 'Agent Runs', href: '/agents', icon: Activity, view: 'agents' as const },
    { name: 'Projects', href: '/projects', icon: FolderOpen, view: 'projects' as const },
    { name: 'Workflows', href: '/workflows', icon: GitBranch, view: 'workflows' as const },
    { name: 'Chat', href: '/chat', icon: MessageSquare, view: 'dashboard' as const },
  ];

  const handleNavigation = (href: string, view: string) => {
    setActiveView(view as any);
    router.push(href);
  };

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className={clsx(
        'fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-200 ease-in-out',
        ui.sidebarOpen ? 'translate-x-0' : '-translate-x-full',
        'lg:translate-x-0 lg:static lg:inset-0'
      )}>
        <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold">C</span>
            </div>
            <span className="ml-2 text-lg font-semibold text-gray-900">Codegen</span>
          </div>
          <button
            onClick={toggleSidebar}
            className="lg:hidden p-1 rounded-md hover:bg-gray-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <nav className="mt-5 px-2">
          <div className="space-y-1">
            {navigationItems.map((item) => (
              <button
                key={item.name}
                onClick={() => handleNavigation(item.href, item.view)}
                className={clsx(
                  'group flex items-center px-2 py-2 text-sm font-medium rounded-md w-full text-left',
                  ui.activeView === item.view
                    ? 'bg-blue-100 text-blue-900'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                )}
              >
                <item.icon className="mr-3 flex-shrink-0 h-5 w-5" />
                {item.name}
              </button>
            ))}
          </div>
          
          <div className="mt-8 pt-8 border-t border-gray-200">
            <button
              onClick={() => router.push('/settings')}
              className="group flex items-center px-2 py-2 text-sm font-medium rounded-md w-full text-left text-gray-600 hover:bg-gray-50 hover:text-gray-900"
            >
              <Settings className="mr-3 flex-shrink-0 h-5 w-5" />
              Settings
            </button>
          </div>
        </nav>
      </div>

      {/* Main content */}
      <div className={clsx('lg:pl-64 flex flex-col flex-1')}>
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center">
                <button
                  onClick={toggleSidebar}
                  className="lg:hidden p-1 rounded-md hover:bg-gray-100"
                >
                  <Menu className="w-5 h-5" />
                </button>
                
                <div className="ml-4 lg:ml-0 flex-1">
                  <div className="max-w-lg w-full lg:max-w-xs">
                    <label htmlFor="search" className="sr-only">Search</label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Search className="h-5 w-5 text-gray-400" />
                      </div>
                      <input
                        id="search"
                        name="search"
                        className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        placeholder="Search..."
                        type="search"
                      />
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                {/* Notifications */}
                <button className="p-1 rounded-full text-gray-400 hover:text-gray-500">
                  <Bell className="h-5 w-5" />
                </button>
                
                {/* User menu */}
                <div className="relative">
                  <button className="bg-white flex items-center text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                    <img
                      className="h-8 w-8 rounded-full"
                      src={auth.user?.avatar_url || `https://ui-avatars.com/api/?name=${auth.user?.name || 'User'}&background=3b82f6&color=fff`}
                      alt={auth.user?.name || 'User'}
                    />
                    <span className="ml-2 text-gray-700">{auth.user?.name || 'User'}</span>
                    <ChevronDown className="ml-1 h-4 w-4 text-gray-400" />
                  </button>
                  
                  {/* User dropdown menu would go here */}
                </div>
                
                {/* Organization info */}
                {auth.organization && (
                  <div className="hidden md:flex items-center space-x-2 text-sm text-gray-600">
                    <span>{auth.organization.name}</span>
                  </div>
                )}
                
                {/* Logout button */}
                <button
                  onClick={handleLogout}
                  className="text-sm text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md hover:bg-gray-100"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1">
          {children}
        </main>
      </div>
      
      {/* Mobile sidebar overlay */}
      {ui.sidebarOpen && (
        <div 
          className="fixed inset-0 bg-gray-600 bg-opacity-50 z-40 lg:hidden"
          onClick={toggleSidebar}
        />
      )}
    </div>
  );
};

export default DashboardLayout;