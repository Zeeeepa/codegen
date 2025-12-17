/**
 * AgentRunDialog Component
 * Dialog for creating new agent runs with repository selection
 */

import { useState, useEffect } from 'react';
import { X, Loader2, AlertCircle, Rocket } from 'lucide-react';
import { listRepositories, createAgentRun, type Repository } from '@/services/codegenApi';
import toast from 'react-hot-toast';

interface AgentRunDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (agentRunId: string) => void;
}

// Cache configuration
const REPOS_CACHE_KEY = 'agent_run_repos_cache';
const REPOS_CACHE_TTL = 5 * 60 * 1000; // 5 minutes
const RECENT_REPOS_KEY = 'agent_run_recent_repos';
const MAX_RECENT_REPOS = 5;

interface CachedRepos {
  data: Repository[];
  timestamp: number;
}

const AgentRunDialog: React.FC<AgentRunDialogProps> = ({ isOpen, onClose, onSuccess }) => {
  const [task, setTask] = useState('');
  const [selectedRepoId, setSelectedRepoId] = useState<number | undefined>();
  const [model, setModel] = useState('Sonnet 4.5');
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [isLoadingRepos, setIsLoadingRepos] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);
  const [recentRepos, setRecentRepos] = useState<number[]>([]);

  // Load recent repositories from localStorage
  useEffect(() => {
    if (isOpen) {
      loadRepositories();
      loadRecentRepos();
      // Reset form
      setTask('');
      setSelectedRepoId(undefined);
      setModel('Sonnet 4.5');
      setError(null);
      setSearchTerm('');
      setValidationError(null);
    }
  }, [isOpen]);

  // Helper: Load recent repos from localStorage
  const loadRecentRepos = () => {
    try {
      const stored = localStorage.getItem(RECENT_REPOS_KEY);
      if (stored) {
        const recent = JSON.parse(stored) as number[];
        setRecentRepos(recent.slice(0, MAX_RECENT_REPOS));
      }
    } catch (err) {
      console.error('[AgentRunDialog] Failed to load recent repos:', err);
    }
  };

  // Helper: Save recent repo to localStorage
  const saveRecentRepo = (repoId: number) => {
    try {
      const stored = localStorage.getItem(RECENT_REPOS_KEY);
      let recent: number[] = stored ? JSON.parse(stored) : [];
      
      // Remove if already exists
      recent = recent.filter(id => id !== repoId);
      
      // Add to front
      recent.unshift(repoId);
      
      // Keep only MAX_RECENT_REPOS
      recent = recent.slice(0, MAX_RECENT_REPOS);
      
      localStorage.setItem(RECENT_REPOS_KEY, JSON.stringify(recent));
      setRecentRepos(recent);
    } catch (err) {
      console.error('[AgentRunDialog] Failed to save recent repo:', err);
    }
  };

  // Helper: Get cached repositories
  const getCachedRepos = (): Repository[] | null => {
    try {
      const stored = localStorage.getItem(REPOS_CACHE_KEY);
      if (!stored) return null;

      const cached = JSON.parse(stored) as CachedRepos;
      const now = Date.now();

      // Check if cache is still valid
      if (now - cached.timestamp < REPOS_CACHE_TTL) {
        console.log('[AgentRunDialog] Using cached repositories');
        return cached.data;
      }

      // Cache expired, remove it
      localStorage.removeItem(REPOS_CACHE_KEY);
      return null;
    } catch (err) {
      console.error('[AgentRunDialog] Failed to load cache:', err);
      return null;
    }
  };

  // Helper: Save repositories to cache
  const setCachedRepos = (repos: Repository[]) => {
    try {
      const cache: CachedRepos = {
        data: repos,
        timestamp: Date.now(),
      };
      localStorage.setItem(REPOS_CACHE_KEY, JSON.stringify(cache));
      console.log('[AgentRunDialog] Cached repositories');
    } catch (err) {
      console.error('[AgentRunDialog] Failed to cache repos:', err);
    }
  };

  // Filter repositories based on search term
  const filteredRepositories = repositories.filter(repo =>
    repo.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    repo.full_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Validate task input
  const validateTask = (taskValue: string): string | null => {
    if (!taskValue.trim()) {
      return 'Task description is required';
    }
    if (taskValue.trim().length < 10) {
      return 'Task description is too short (minimum 10 characters)';
    }
    if (taskValue.length > 5000) {
      return 'Task description is too long (maximum 5000 characters)';
    }
    if (!/[a-zA-Z]/.test(taskValue)) {
      return 'Task description must contain at least one letter';
    }
    return null;
  };

  // Handle task change with validation
  const handleTaskChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newTask = e.target.value;
    setTask(newTask);
    
    // Clear validation error when user starts typing
    if (validationError) {
      setValidationError(null);
    }
  };

  // Get detailed error message based on error response
  const getErrorMessage = (err: any): string => {
    if (err?.response?.status) {
      switch (err.response.status) {
        case 403:
          return "You don't have access to this repository. Please check your permissions.";
        case 404:
          return 'Repository not found. It may have been deleted or renamed.';
        case 429:
          return 'Rate limit exceeded. Please try again in a few minutes.';
        case 500:
          return 'Server error. Please try again later.';
        default:
          return err.message || 'An unexpected error occurred';
      }
    }
    return err instanceof Error ? err.message : 'An unexpected error occurred';
  };

  const loadRepositories = async () => {
    // Try to load from cache first
    const cached = getCachedRepos();
    if (cached) {
      setRepositories(cached);
      console.log('[AgentRunDialog] Loaded repositories from cache:', cached.length);
      return;
    }

    // Cache miss - fetch from API
    setIsLoadingRepos(true);
    setError(null);
    try {
      const response = await listRepositories();
      const repos = response.items || [];
      setRepositories(repos);
      
      // Save to cache
      setCachedRepos(repos);
      
      console.log('[AgentRunDialog] Loaded repositories from API:', repos.length);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load repositories';
      setError(errorMsg);
      console.error('[AgentRunDialog] Failed to load repos:', err);
      toast.error(errorMsg);
    } finally {
      setIsLoadingRepos(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate task
    const validationErr = validateTask(task);
    if (validationErr) {
      setValidationError(validationErr);
      toast.error(validationErr);
      return;
    }

    setIsCreating(true);
    setError(null);
    setValidationError(null);

    try {
      console.log('[AgentRunDialog] Creating agent run:', {
        task: task.substring(0, 100),
        repo_id: selectedRepoId,
        model
      });

      const response = await createAgentRun(undefined, undefined, {
        task: task.trim(),
        repo_id: selectedRepoId,
        model
      });

      console.log('[AgentRunDialog] Agent run created:', response.agentRunId);
      toast.success('🎉 Agent run created successfully!');
      
      // Save to recent repositories if a repo was selected
      if (selectedRepoId) {
        saveRecentRepo(selectedRepoId);
      }
      
      onSuccess?.(response.agentRunId);
      
      // Small delay to show success message before closing
      setTimeout(() => {
        onClose();
      }, 500);
    } catch (err) {
      const errorMsg = getErrorMessage(err);
      setError(errorMsg);
      console.error('[AgentRunDialog] Failed to create run:', err);
      toast.error(errorMsg);
    } finally {
      setIsCreating(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Dialog */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-xl shadow-2xl max-w-2xl w-full p-6 transform transition-all">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Rocket className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Create Agent Run</h2>
                <p className="text-sm text-gray-500 mt-1">Configure and launch a new AI coding agent</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              disabled={isCreating}
              aria-label="Close dialog"
              aria-disabled={isCreating}
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-800">Error</p>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Task Description */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label htmlFor="task" className="block text-sm font-medium text-gray-700">
                  Task Description <span className="text-red-500">*</span>
                </label>
                <span className={`text-xs font-medium ${
                  task.length > 5000 
                    ? 'text-red-600' 
                    : task.length > 4500 
                    ? 'text-orange-600' 
                    : 'text-gray-500'
                }`}>
                  {task.length} / 5000 characters
                </span>
              </div>
              <textarea
                id="task"
                value={task}
                onChange={handleTaskChange}
                placeholder="Describe what you want the agent to do (e.g., 'Add error handling to the authentication module')"
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none ${
                  validationError ? 'border-red-300 bg-red-50' : 'border-gray-300'
                }`}
                rows={4}
                disabled={isCreating}
                required
                aria-label="Task description"
                aria-invalid={!!validationError}
                aria-describedby={validationError ? "task-error" : "task-hint"}
              />
              {validationError && (
                <p id="task-error" className="mt-2 text-sm text-red-600 flex items-center" role="alert">
                  <AlertCircle className="w-4 h-4 mr-1" />
                  {validationError}
                </p>
              )}
              <p id="task-hint" className="mt-2 text-xs text-gray-500">
                Be specific about the task (10-5000 characters). The agent will analyze your codebase and implement the requested changes.
              </p>
            </div>

            {/* Repository Selection */}
            <div>
              <label htmlFor="repository" className="block text-sm font-medium text-gray-700 mb-2">
                Repository (Optional)
              </label>
              {isLoadingRepos ? (
                <div className="flex items-center justify-center py-4 text-gray-500">
                  <Loader2 className="w-5 h-5 animate-spin mr-2" />
                  <span className="text-sm">Loading repositories...</span>
                </div>
              ) : repositories.length === 0 ? (
                <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg text-center">
                  <p className="text-sm text-gray-600">No repositories available</p>
                  <button
                    type="button"
                    onClick={loadRepositories}
                    className="mt-2 text-sm text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Retry
                  </button>
                </div>
              ) : (
                <>
                  {/* Search Box */}
                  {repositories.length > 10 && (
                    <input
                      type="text"
                      placeholder="🔍 Search repositories..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full px-4 py-2 mb-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      disabled={isCreating}
                      aria-label="Search repositories"
                      aria-describedby="repo-search-results"
                    />
                  )}
                  
                  <select
                    id="repository"
                    value={selectedRepoId || ''}
                    onChange={(e) => setSelectedRepoId(e.target.value ? Number(e.target.value) : undefined)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                    disabled={isCreating}
                    aria-label="Select repository"
                  >
                    <option value="">No specific repository</option>
                    {filteredRepositories.map((repo) => (
                      <option key={repo.id} value={repo.id}>
                        {repo.name} {repo.archived && '(Archived)'}
                      </option>
                    ))}
                  </select>
                  
                  {searchTerm && filteredRepositories.length === 0 && (
                    <p className="mt-2 text-sm text-orange-600">
                      No repositories match "{searchTerm}"
                    </p>
                  )}
                  
                  {searchTerm && filteredRepositories.length > 0 && (
                    <p id="repo-search-results" className="mt-2 text-xs text-gray-500" aria-live="polite">
                      Showing {filteredRepositories.length} of {repositories.length} repositories
                    </p>
                  )}
                </>
              )}
              <p className="mt-2 text-xs text-gray-500">
                Select a repository to scope the agent's work. Leave blank for organization-wide access.
              </p>
            </div>

            {/* Model Selection */}
            <div>
              <label htmlFor="model" className="block text-sm font-medium text-gray-700 mb-2">
                AI Model
              </label>
              <select
                id="model"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                disabled={isCreating}
                aria-label="Select AI model"
              >
                <option value="Sonnet 4.5">Claude Sonnet 4.5 (Recommended)</option>
                <option value="Sonnet 3.5">Claude Sonnet 3.5</option>
                <option value="GPT-4">GPT-4</option>
                <option value="GPT-4 Turbo">GPT-4 Turbo</option>
              </select>
              <p className="mt-2 text-xs text-gray-500">
                Choose the AI model for this task. Sonnet 4.5 offers the best balance of speed and capability.
              </p>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                className="px-5 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                disabled={isCreating}
                aria-label="Cancel"
                aria-disabled={isCreating}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isCreating || !task.trim()}
                className="px-5 py-2.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                aria-label={isCreating ? "Creating agent run" : "Create agent run"}
                aria-disabled={isCreating || !task.trim()}
              >
                {isCreating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Creating...</span>
                  </>
                ) : (
                  <>
                    <Rocket className="w-4 h-4" />
                    <span>Create Agent Run</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AgentRunDialog;
