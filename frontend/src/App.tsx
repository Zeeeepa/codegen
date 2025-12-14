import React from 'react';
import { Toaster } from 'react-hot-toast';
import { useAppStore } from './store';
import Settings from './components/Settings';
import UnifiedDashboard from './components/UnifiedDashboard';

const App: React.FC = () => {
  const isSettingsOpen = useAppStore((state) => state.isSettingsOpen);
  const closeSettings = useAppStore((state) => state.closeSettings);

  return (
    <div className="min-h-screen bg-gray-50">
      <Toaster position="top-right" />
      
      {/* Unified Dashboard with all features */}
      <UnifiedDashboard />
      
      {/* Settings Modal */}
      {isSettingsOpen && (
        <Settings onClose={() => closeSettings()} />
      )}
    </div>
  );
};

export default App;

