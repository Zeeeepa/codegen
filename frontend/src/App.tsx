import React, { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import { 
  RefreshCw, Play, Settings as SettingsIcon, Zap, Loader, 
  Link, Plus, X, AlertCircle, CheckCircle, XCircle, Clock, Users 
} from 'lucide-react';
import { codegenApi } from './services/api';
import { chainExecutor } from './services/chainExecutor';
import { chainTemplates } from './templates/chainTemplates';
import { useAppStore, selectHasValidCredentials } from './store';
import Settings from './components/Settings';
import WorkflowCanvas from './components/WorkflowCanvas';
import { ProfileManagement } from './components/ProfileManagement';
import type { 
  Repository, AgentRun, ChainConfig, ChainExecution, 
  RunStatus, ChainStep 
} from './types';

const App: React.FC = () => {
  // Get credentials from Zustand store
  const apiToken = useAppStore((state) => state.apiToken);
  const organizationId = useAppStore((state) => state.organizationId);
  const hasCredentials = useAppStore(selectHasValidCredentials);
  const isSettingsOpen = useAppStore((state) => state.isSettingsOpen);
  const openSettings = useAppStore((state) => state.openSettings);
  const closeSettings = useAppStore((state) => state.closeSettings);
  
  const [repos, setRepos] = useState<Repository[]>([]);
  const [allRuns, setAllRuns] = useState<AgentRun[]>([]);
  const [activeRuns, setActiveRuns] = useState<AgentRun[]>([]);
  const [chains, setChains] = useState<ChainConfig[]>([]);
  const [activeChains, setActiveChains] = useState<ChainExecution[]>([]);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState('visual'); // Start with visual editor
  const [error, setError] = useState('');
  const [showChainDialog, setShowChainDialog] = useState(false);
  const [editingChain, setEditingChain] = useState<ChainConfig | null>(null);

  useEffect(() => {
    if (hasCredentials) {
      fetchRepos();
      fetchAllRuns();
      const interval = setInterval(fetchAllRuns, 5000);
      return () => clearInterval(interval);
    }
  }, [hasCredentials]);

  useEffect(() => {
    const savedChains = localStorage.getItem('codegen-chains');
    if (savedChains) {
      setChains(JSON.parse(savedChains));
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('codegen-chains', JSON.stringify(chains));
  }, [chains]);

  const fetchRepos = async () => {
    if (!organizationId || !apiToken) return;
    try {
      const data = await codegenApi.fetchRepos(organizationId, apiToken);
      setRepos(data);
    } catch (err) {
      setError(`Failed to fetch repos: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  const fetchAllRuns = async () => {
    if (!organizationId || !apiToken) return;
    try {
      setLoading(true);
      const data = await codegenApi.fetchAllRuns(organizationId, apiToken);
      setAllRuns(data);
      setActiveRuns(data.filter(r => r.status === 'running' || r.status === 'pending'));
      setError('');
    } catch (err) {
      setError(`Failed to fetch runs: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoading(false);
    }
  };

  const executeChain = async (chain: ChainConfig) => {
    if (!organizationId || !apiToken) {
      setError('Please configure API credentials in Settings');
      return;
    }
    try {
      await chainExecutor.executeChain(
        chain,
        organizationId,
        apiToken,
        (execution) => {
          setActiveChains(prev => {
            const idx = prev.findIndex(e => e.id === execution.id);
            if (idx >= 0) {
              const updated = [...prev];
              updated[idx] = execution;
              return updated;
            }
            return [...prev, execution];
          });
        }
      );
    } catch (err) {
      setError(`Chain execution failed: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  const saveChain = (chain: ChainConfig) => {
    if (editingChain && editingChain.id) {
      setChains(prev => prev.map(c => c.id === editingChain.id ? { ...chain, id: editingChain.id } : c));
    } else {
      setChains(prev => [...prev, { ...chain, id: Date.now() }]);
    }
    setShowChainDialog(false);
    setEditingChain(null);
  };

  const deleteChain = (chainId?: number) => {
    if (!chainId) return;
    setChains(prev => prev.filter(c => c.id !== chainId));
  };

  const getStatusColor = (status: RunStatus) => {
    const colors = {
      running: 'text-emerald-400 bg-emerald-950',
      pending: 'text-yellow-400 bg-yellow-950',
      completed: 'text-green-400 bg-green-950',
      failed: 'text-red-400 bg-red-950',
    };
    return colors[status] || 'text-gray-400 bg-gray-800';
  };

  const getStatusIcon = (status: RunStatus) => {
    switch(status) {
      case 'running': return <Loader className="w-4 h-4 animate-spin" />;
      case 'completed': return <CheckCircle className="w-4 h-4" />;
      case 'failed': return <XCircle className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  // Show setup prompt if no credentials
  if (!hasCredentials) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
        <Toaster position="top-right" />
        <div className="bg-gray-900 rounded-lg shadow-2xl border border-gray-800 p-8 w-full max-w-md text-center">
          <h1 className="text-2xl font-bold mb-4 text-green-400">Welcome to CodeGen Visual Orchestration</h1>
          <p className="text-gray-300 mb-6">
            Get started by configuring your API credentials
          </p>
          <button
            onClick={() => openSettings()}
            className="w-full bg-purple-600 text-white py-3 px-4 rounded-lg hover:bg-purple-700 transition-colors flex items-center justify-center gap-2"
          >
            <SettingsIcon className="w-5 h-5" />
            Configure Settings
          </button>
        </div>
        
        {/* Settings Modal */}
        {isSettingsOpen && (
          <Settings onClose={() => closeSettings()} />
        )}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950">
      <Toaster position="top-right" />
      
      <header className="bg-gray-900 shadow-lg border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-green-400">CodeGen Visual Orchestration Platform</h1>
              <p className="text-sm text-gray-400 mt-1">
                {organizationId ? `Org: ${organizationId}` : 'No organization configured'}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-4 py-2 bg-purple-950 border border-purple-900 rounded-lg">
                <Zap className="w-5 h-5 text-purple-400" />
                <div>
                  <div className="text-2xl font-bold text-purple-400">
                    {activeChains.filter(c => c.status === 'running').length}
                  </div>
                  <div className="text-xs text-gray-400">Active Chains</div>
                </div>
              </div>
              <div className="flex items-center gap-2 px-4 py-2 bg-green-950 border border-green-900 rounded-lg">
                <Loader className="w-5 h-5 text-green-400 animate-spin" />
                <div>
                  <div className="text-2xl font-bold text-green-400">{activeRuns.length}</div>
                  <div className="text-xs text-gray-400">Active Runs</div>
                </div>
              </div>
              <button
                onClick={fetchAllRuns}
                disabled={loading}
                className="p-2 text-gray-400 hover:text-green-400 hover:bg-gray-800 rounded-lg transition-colors"
                aria-label="Refresh runs"
              >
                <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
              </button>
              <button
                onClick={() => openSettings()}
                className="p-2 text-gray-400 hover:text-purple-400 hover:bg-gray-800 rounded-lg transition-colors"
                aria-label="Open settings"
              >
                <SettingsIcon className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        {error && (
          <div className="mb-4 p-4 bg-red-950 border border-red-900 rounded-lg text-red-400 flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => setError('')} className="text-red-400 hover:text-red-300">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        <div className="bg-gray-900 border border-gray-800 rounded-lg shadow-lg mb-6">
          <div className="border-b border-gray-800">
            <nav className="flex gap-4 px-6">
              <button
                onClick={() => setView('visual')}
                className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors flex items-center gap-2 ${
                  view === 'visual'
                    ? 'border-purple-500 text-purple-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300'
                }`}
              >
                <Zap className="w-4 h-4" />
                Visual Workflow Editor
              </button>
              <button
                onClick={() => setView('chains')}
                className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors flex items-center gap-2 ${
                  view === 'chains'
                    ? 'border-purple-500 text-purple-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300'
                }`}
              >
                <Link className="w-4 h-4" />
                Chains ({chains.length})
              </button>
              <button
                onClick={() => setView('active-chains')}
                className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors flex items-center gap-2 ${
                  view === 'active-chains'
                    ? 'border-purple-500 text-purple-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300'
                }`}
              >
                <Zap className="w-4 h-4" />
                Active Chains ({activeChains.length})
              </button>
              <button
                onClick={() => setView('profiles')}
                className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors flex items-center gap-2 ${
                  view === 'profiles'
                    ? 'border-purple-500 text-purple-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300'
                }`}
                data-testid="profiles-tab"
              >
                <Users className="w-4 h-4" />
                Profiles
              </button>
              <button
                onClick={() => setView('runs')}
                className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
                  view === 'runs'
                    ? 'border-green-500 text-green-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300'
                }`}
              >
                All Runs ({allRuns.length})
              </button>
            </nav>
          </div>

          <div className="p-6">
            {view === 'visual' && (
              <div className="h-[calc(100vh-280px)]">
                <WorkflowCanvas />
              </div>
            )}
            
            {view === 'chains' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-purple-400">Chain Configurations</h2>
                  <button
                    onClick={() => {
                      setEditingChain(null);
                      setShowChainDialog(true);
                    }}
                    className="bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    Create Chain
                  </button>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-gray-400 mb-3">Quick Start Templates</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {Object.values(chainTemplates).map((template) => (
                      <div key={template.id} className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h4 className="font-semibold text-gray-100">{template.name}</h4>
                            <p className="text-xs text-gray-400 mt-1">{template.description}</p>
                            <p className="text-xs text-purple-400 mt-2">{template.steps.length} steps</p>
                          </div>
                          <button
                            onClick={() => {
                              const chainFromTemplate: ChainConfig = {
                                name: template.name,
                                description: template.description,
                                steps: template.steps,
                                contextStrategy: template.contextStrategy,
                                errorHandling: template.errorHandling
                              };
                              setEditingChain(chainFromTemplate);
                              setShowChainDialog(true);
                            }}
                            className="text-purple-400 hover:text-purple-300 text-sm"
                          >
                            Use →
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-gray-400 mb-3">Saved Chains</h3>
                  {chains.length === 0 ? (
                    <div className="text-center py-8 text-gray-400">
                      No chains configured yet. Create one from a template or start from scratch!
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {chains.map((chain) => (
                        <div key={chain.id} className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                          <div className="flex items-start justify-between mb-3">
                            <div>
                              <h4 className="font-semibold text-gray-100">{chain.name}</h4>
                              <p className="text-xs text-gray-400 mt-1">{chain.description}</p>
                              <p className="text-xs text-purple-400 mt-2">{chain.steps?.length || 0} steps</p>
                            </div>
                            <div className="flex gap-2">
                              <button
                                onClick={() => {
                                  setEditingChain(chain);
                                  setShowChainDialog(true);
                                }}
                                className="text-gray-400 hover:text-gray-300"
                              >
                                <SettingsIcon className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => deleteChain(chain.id)}
                                className="text-red-400 hover:text-red-300"
                              >
                                <X className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                          <button
                            onClick={() => executeChain(chain)}
                            className="w-full bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 transition-colors flex items-center justify-center gap-2"
                          >
                            <Play className="w-4 h-4" />
                            Execute Chain
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {view === 'active-chains' && (
              <div className="space-y-4">
                {activeChains.length === 0 ? (
                  <div className="text-center py-8 text-gray-400">
                    No active chains. Execute a chain to see it here!
                  </div>
                ) : (
                  activeChains.map((chain) => (
                    <div key={chain.id} className="bg-gray-800 border border-purple-700 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h3 className="font-semibold text-gray-100 flex items-center gap-2">
                            {chain.chainConfig.name}
                            <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(chain.status)} flex items-center gap-1`}>
                              {getStatusIcon(chain.status)}
                              {chain.status}
                            </span>
                          </h3>
                          <p className="text-xs text-gray-400 mt-1">
                            Started: {chain.startTime.toLocaleString()}
                          </p>
                        </div>
                      </div>

                      <div className="space-y-2">
                        {chain.steps.map((step, idx) => (
                          <div key={idx} className="bg-gray-900 border border-gray-700 rounded p-3">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-medium text-gray-300">
                                  Step {step.stepIndex} - {step.type}
                                </span>
                                {step.attempt && (
                                  <span className="text-xs text-yellow-400">
                                    Attempt {step.attempt}/{step.maxAttempts}
                                  </span>
                                )}
                              </div>
                              <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(step.status)}`}>
                                {step.status}
                              </span>
                            </div>
                            <p className="text-xs text-gray-400 mb-1">Run ID: {step.runId}</p>
                            {step.prompt && (
                              <p className="text-xs text-gray-500 truncate">{step.prompt}</p>
                            )}
                            {step.result && (
                              <details className="mt-2">
                                <summary className="text-xs text-purple-400 cursor-pointer">View result</summary>
                                <p className="text-xs text-gray-400 mt-2 p-2 bg-gray-950 rounded">{step.result}</p>
                              </details>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {view === 'profiles' && (
              <ProfileManagement />
            )}

            {view === 'runs' && (
              <div className="space-y-3">
                {allRuns.length === 0 ? (
                  <p className="text-gray-400 text-center py-8">No runs found.</p>
                ) : (
                  allRuns.map((run) => (
                    <div
                      key={run.id}
                      className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-green-700 transition-all"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-semibold text-gray-100">Run #{run.id}</span>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(run.status as RunStatus)} flex items-center gap-1`}>
                              {getStatusIcon(run.status as RunStatus)}
                              {run.status}
                            </span>
                          </div>
                          <p className="text-sm text-gray-300 mb-2">{run.prompt}</p>
                          <p className="text-xs text-gray-500">
                            {run.created_at && new Date(run.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Settings Modal */}
      {isSettingsOpen && (
        <Settings onClose={() => closeSettings()} />
      )}
    </div>
  );
};

export default App;
