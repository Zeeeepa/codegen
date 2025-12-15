/**
 * PRD to Implementation Component
 * 
 * User Flow:
 * 1. Select repository
 * 2. Create/edit PRD
 * 3. Press "Implement" button
 * 4. Watch agent chain execute
 * 5. View results
 */

import React, { useState } from 'react';
import { Play, CheckCircle, XCircle, Clock, Loader2 } from 'lucide-react';
import { AgentChainExecutor, createFeatureImplementationChain, type ChainExecutionState } from '@/orchestration/agentChain';
import { useAppStore } from '@/store';

export const PRDToImplementation: React.FC = () => {
  // Use REAL credentials from .env
  const apiToken = import.meta.env.VITE_CODEGEN_API_TOKEN || 'sk-92083737-4e5b-4a48-a2a1-f870a3a096a6';
  const organizationId = import.meta.env.VITE_CODEGEN_ORG_ID || '323';
  
  const [repositories, setRepositories] = useState<Array<{id: string; name: string; fullName: string}>>([]);
  const [repository, setRepository] = useState('');
  const [prd, setPrd] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionState, setExecutionState] = useState<ChainExecutionState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoadingRepos, setIsLoadingRepos] = useState(false);

  // Load repositories on mount
  useEffect(() => {
    loadRepositories();
  }, []);

  const loadRepositories = async () => {
    setIsLoadingRepos(true);
    try {
      const { listRepositories } = await import('@/services/codegenApi');
      const repos = await listRepositories(organizationId, apiToken);
      setRepositories(repos);
      if (repos.length > 0 && !repository) {
        setRepository(repos[0].id);
      }
    } catch (err: any) {
      console.error('Failed to load repositories:', err);
      setError(`Failed to load repositories: ${err.message}`);
    } finally {
      setIsLoadingRepos(false);
    }
  };

  /**
   * Handle "Implement" button click
   * 
   * This is where the magic happens:
   * 1. Creates agent chain configuration
   * 2. Starts execution
   * 3. Watches state changes in real-time
   */
  const handleImplement = async () => {
    if (!prd.trim()) {
      setError('Please provide a PRD');
      return;
    }

    if (!repository.trim()) {
      setError('Please select a repository');
      return;
    }

    setError(null);
    setIsExecuting(true);

    try {
      // Create chain configuration
      const chainConfig = createFeatureImplementationChain(prd, repository);

      // Create executor with real-time state updates
      const executor = new AgentChainExecutor(
        organizationId,
        apiToken,
        `chain-${Date.now()}`,
        (state) => {
          console.log('[PRDToImplementation] State update:', state);
          setExecutionState(state);
        }
      );

      // Execute chain
      const finalState = await executor.executeChain(chainConfig, {
        prd,
        metadata: {
          repository,
          startTime: Date.now(),
        },
      });

      console.log('[PRDToImplementation] Chain completed:', finalState);

    } catch (err: any) {
      console.error('[PRDToImplementation] Chain failed:', err);
      setError(err.message);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">PRD to Implementation</h1>

      {/* Repository Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">
          Repository {isLoadingRepos && <span className="text-gray-500">(Loading...)</span>}
        </label>
        <select
          value={repository}
          onChange={(e) => setRepository(e.target.value)}
          className="w-full px-4 py-2 border rounded-lg"
          disabled={isExecuting || isLoadingRepos}
        >
          <option value="">Select a repository...</option>
          {repositories.map((repo) => (
            <option key={repo.id} value={repo.id}>
              {repo.fullName}
            </option>
          ))}
        </select>
      </div>

      {/* PRD Editor */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">
          Product Requirements Document (PRD)
        </label>
        <textarea
          value={prd}
          onChange={(e) => setPrd(e.target.value)}
          placeholder="Describe the feature you want to implement..."
          className="w-full h-64 px-4 py-2 border rounded-lg font-mono text-sm"
          disabled={isExecuting}
        />
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start gap-2">
            <XCircle className="text-red-500 mt-0.5" size={20} />
            <div>
              <p className="font-semibold text-red-900">Error</p>
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Implement Button */}
      <div className="mb-6">
        <button
          onClick={handleImplement}
          disabled={isExecuting || !prd.trim() || !repository.trim()}
          className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {isExecuting ? (
            <>
              <Loader2 size={20} className="animate-spin" />
              Executing...
            </>
          ) : (
            <>
              <Play size={20} />
              Implement
            </>
          )}
        </button>
      </div>

      {/* Execution Progress */}
      {executionState && (
        <div className="bg-white border rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Execution Progress</h2>

          {/* Overall Status */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Status</p>
                <p className="text-lg font-semibold capitalize">{executionState.status}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Current Task</p>
                <p className="text-lg font-semibold">
                  {executionState.currentTaskIndex + 1} of {executionState.results.length + 1}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Agent Run ID</p>
                <p className="text-sm font-mono">{executionState.currentAgentRunId}</p>
              </div>
            </div>
          </div>

          {/* Task Results */}
          <div className="space-y-3">
            {executionState.results.map((result, index) => (
              <div
                key={index}
                className="p-4 border rounded-lg bg-green-50 border-green-200"
              >
                <div className="flex items-start gap-3">
                  <CheckCircle className="text-green-500 mt-0.5" size={20} />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <p className="font-semibold capitalize">{result.agentType} Agent</p>
                      <span className="text-sm text-gray-600">
                        {(result.duration / 1000).toFixed(1)}s
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 mt-1">{result.result}</p>
                    <p className="text-xs text-gray-500 mt-1 font-mono">
                      Run ID: {result.agentRunId}
                    </p>
                  </div>
                </div>
              </div>
            ))}

            {/* Current Task (in progress) */}
            {executionState.status === 'running' && (
              <div className="p-4 border rounded-lg bg-blue-50 border-blue-200">
                <div className="flex items-start gap-3">
                  <Loader2 className="text-blue-500 mt-0.5 animate-spin" size={20} />
                  <div className="flex-1">
                    <p className="font-semibold">
                      Task {executionState.currentTaskIndex + 1} in progress...
                    </p>
                    <p className="text-sm text-gray-600 mt-1">
                      Waiting for agent to complete
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Final Status */}
          {executionState.status === 'completed' && (
            <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-start gap-2">
                <CheckCircle className="text-green-500 mt-0.5" size={20} />
                <div>
                  <p className="font-semibold text-green-900">Feature Implemented Successfully!</p>
                  <p className="text-green-700 text-sm mt-1">
                    All agents completed their tasks. Check your repository for the changes.
                  </p>
                </div>
              </div>
            </div>
          )}

          {executionState.status === 'failed' && executionState.error && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start gap-2">
                <XCircle className="text-red-500 mt-0.5" size={20} />
                <div>
                  <p className="font-semibold text-red-900">Execution Failed</p>
                  <p className="text-red-700 text-sm mt-1">{executionState.error}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Info Box */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="font-semibold text-blue-900 mb-2">How it works</h3>
        <div className="text-sm text-blue-800 space-y-1">
          <p>1. <strong>Developer Agent</strong> implements the feature</p>
          <p>2. <strong>Visual Testing Agent</strong> validates UI/UX</p>
          <p>3. <strong>Validator Agent</strong> tests with real-life scenarios</p>
          <p>4. <strong>Debugging Agent</strong> fixes any errors (if needed)</p>
          <p>5. <strong>PR Agent</strong> creates pull request</p>
          <p>6. <strong>Commit Agent</strong> commits changes</p>
          <p>7. <strong>Reflection Agent</strong> performs self-review</p>
          <p>8. <strong>Validation Agent</strong> gives final approval</p>
        </div>
      </div>
    </div>
  );
};
