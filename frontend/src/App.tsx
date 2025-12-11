import React, { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import { 
  RefreshCw, Play, Settings, Zap, Loader, 
  Link, Plus, X, AlertCircle, CheckCircle, XCircle, Clock 
} from 'lucide-react';
import { codegenApi } from './services/api';
import { chainExecutor } from './services/chainExecutor';
import { chainTemplates } from './templates/chainTemplates';
import type { 
  Repository, AgentRun, ChainConfig, ChainExecution, 
  RunStatus, ChainStep 
} from './types';

const App: React.FC = () => {
  const [orgId, setOrgId] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [repos, setRepos] = useState<Repository[]>([]);
  const [allRuns, setAllRuns] = useState<AgentRun[]>([]);
  const [activeRuns, setActiveRuns] = useState<AgentRun[]>([]);
  const [chains, setChains] = useState<ChainConfig[]>([]);
  const [activeChains, setActiveChains] = useState<ChainExecution[]>([]);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState('chains');
  const [error, setError] = useState('');
  const [showChainDialog, setShowChainDialog] = useState(false);
  const [editingChain, setEditingChain] = useState<ChainConfig | null>(null);

  useEffect(() => {
    if (orgId && apiKey) {
      fetchRepos();
      fetchAllRuns();
      const interval = setInterval(fetchAllRuns, 5000);
      return () => clearInterval(interval);
    }
  }, [orgId, apiKey]);

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
    try {
      const data = await codegenApi.fetchRepos(orgId, apiKey);
      setRepos(data);
    } catch (err) {
      setError(`Failed to fetch repos: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  const fetchAllRuns = async () => {
    try {
      setLoading(true);
      const data = await codegenApi.fetchAllRuns(orgId, apiKey);
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
    try {
      await chainExecutor.executeChain(
        chain,
        orgId,
        apiKey,
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

  if (!orgId || !apiKey) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
        <div className="bg-gray-900 rounded-lg shadow-2xl border border-gray-800 p-8 w-full max-w-md">
          <h1 className="text-2xl font-bold mb-6 text-green-400">CodeGen Chain Dashboard</h1>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Organization ID
              </label>
              <input
                type="text"
                value={orgId}
                onChange={(e) => setOrgId(e.target.value)}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:ring-2 focus:ring-green-500 focus:border-transparent"
                placeholder="Enter org ID"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                API Key
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 focus:ring-2 focus:ring-green-500 focus:border-transparent"
                placeholder="Enter API key"
              />
            </div>
            <button
              onClick={() => {
                if (orgId && apiKey) {
                  fetchRepos();
                  fetchAllRuns();
                }
              }}
              className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors"
            >
              Connect
            </button>
          </div>
        </div>
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
              <h1 className="text-2xl font-bold text-green-400">CodeGen Chain Dashboard</h1>
              <p className="text-sm text-gray-400 mt-1">Org: {orgId}</p>
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
              >
                <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
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
                                <Settings className="w-4 h-4" />
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
    </div>
  );
};

export default App;

