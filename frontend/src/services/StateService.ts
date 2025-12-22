/**
 * StateService - Manages application state with reactive updates
 * Provides centralized state management with subscriber pattern
 * Supports state history, action tracking, and real-time updates
 */

export interface AppState {
  // Profile Management
  profiles: any[];
  activeProfile: any | null;
  profileStates: Record<string, string>;
  
  // CI/CD Pipeline States
  pipelines: any[];
  activePipeline: any | null;
  pipelineExecutions: Record<string, any>;
  
  // System Health
  systemHealth: {
    status: 'healthy' | 'degraded' | 'down';
    uptime: number;
    lastCheck: number;
    services: Record<string, boolean>;
  };
  
  // Observability
  metrics: {
    profileExecutions: number;
    successRate: number;
    avgExecutionTime: number;
    errors: number;
  };
  
  // UI State
  isLoading: boolean;
  error: string | null;
  lastUpdate: number | null;
  
  // Real-time Updates
  wsConnected: boolean;
  lastWsMessage: number | null;
}

export interface StateHistoryEntry {
  state: AppState;
  action: string;
  timestamp: number;
}

export type StateSubscriber = (
  state: AppState,
  action: string,
  changedState: Partial<AppState>
) => void;

export class StateService {
  private state: AppState;
  private subscribers: Set<StateSubscriber>;
  private stateHistory: StateHistoryEntry[];
  private maxHistorySize: number;

  constructor() {
    this.state = this.getInitialState();
    this.subscribers = new Set();
    this.stateHistory = [];
    this.maxHistorySize = 50;
  }

  /**
   * Get initial state
   */
  private getInitialState(): AppState {
    return {
      profiles: [],
      activeProfile: null,
      profileStates: {},
      pipelines: [],
      activePipeline: null,
      pipelineExecutions: {},
      systemHealth: {
        status: 'healthy',
        uptime: 0,
        lastCheck: Date.now(),
        services: {}
      },
      metrics: {
        profileExecutions: 0,
        successRate: 0,
        avgExecutionTime: 0,
        errors: 0
      },
      isLoading: false,
      error: null,
      lastUpdate: null,
      wsConnected: false,
      lastWsMessage: null
    };
  }

  /**
   * Subscribe to state changes
   */
  subscribe(callback: StateSubscriber): () => void {
    this.subscribers.add(callback);
    
    // Return unsubscribe function
    return () => {
      this.subscribers.delete(callback);
    };
  }

  /**
   * Get current state (immutable copy)
   */
  getState(): AppState {
    return { ...this.state };
  }

  /**
   * Get specific state property
   */
  getStateProperty<K extends keyof AppState>(key: K): AppState[K] {
    return this.state[key];
  }

  /**
   * Update state and notify subscribers
   */
  setState(newState: Partial<AppState>, action: string = 'setState'): void {
    // Save current state to history
    this.saveStateToHistory(action);

    // Update state
    this.state = {
      ...this.state,
      ...newState,
      lastUpdate: Date.now()
    };

    // Notify all subscribers
    this.notifySubscribers(action, newState);
  }

  /**
   * Update specific state property
   */
  setStateProperty<K extends keyof AppState>(
    key: K,
    value: AppState[K],
    action: string = `set_${String(key)}`
  ): void {
    this.setState({ [key]: value } as Partial<AppState>, action);
  }

  /**
   * Save current state to history
   */
  private saveStateToHistory(action: string): void {
    this.stateHistory.push({
      state: { ...this.state },
      action,
      timestamp: Date.now()
    });

    // Keep history size manageable
    if (this.stateHistory.length > this.maxHistorySize) {
      this.stateHistory.shift();
    }
  }

  /**
   * Notify all subscribers of state changes
   */
  private notifySubscribers(action: string, changedState: Partial<AppState>): void {
    this.subscribers.forEach(callback => {
      try {
        callback(this.state, action, changedState);
      } catch (error) {
        console.error('Error in StateService subscriber:', error);
      }
    });
  }

  /**
   * Notify listeners with specific action and data (for real-time events)
   */
  notifyListeners(action: string, data: any): void {
    this.notifySubscribers(action, data);
  }

  // ===== Profile Management Actions =====

  updateProfiles(profiles: any[]): void {
    this.setState({ profiles }, 'update_profiles');
  }

  setActiveProfile(profile: any): void {
    this.setState({ activeProfile: profile }, 'set_active_profile');
  }

  updateProfileState(profileId: string, state: string): void {
    const profileStates = { ...this.state.profileStates, [profileId]: state };
    this.setState({ profileStates }, 'update_profile_state');
  }

  // ===== CI/CD Pipeline Actions =====

  updatePipelines(pipelines: any[]): void {
    this.setState({ pipelines }, 'update_pipelines');
  }

  setActivePipeline(pipeline: any): void {
    this.setState({ activePipeline: pipeline }, 'set_active_pipeline');
  }

  updatePipelineExecution(pipelineId: string, execution: any): void {
    const pipelineExecutions = {
      ...this.state.pipelineExecutions,
      [pipelineId]: execution
    };
    this.setState({ pipelineExecutions }, 'update_pipeline_execution');
  }

  // ===== System Health Actions =====

  updateSystemHealth(health: Partial<AppState['systemHealth']>): void {
    const systemHealth = { ...this.state.systemHealth, ...health };
    this.setState({ systemHealth }, 'update_system_health');
  }

  // ===== Metrics Actions =====

  updateMetrics(metrics: Partial<AppState['metrics']>): void {
    const newMetrics = { ...this.state.metrics, ...metrics };
    this.setState({ metrics: newMetrics }, 'update_metrics');
  }

  incrementProfileExecutions(): void {
    const metrics = {
      ...this.state.metrics,
      profileExecutions: this.state.metrics.profileExecutions + 1
    };
    this.setState({ metrics }, 'increment_profile_executions');
  }

  recordError(): void {
    const metrics = {
      ...this.state.metrics,
      errors: this.state.metrics.errors + 1
    };
    this.setState({ metrics }, 'record_error');
  }

  // ===== UI State Actions =====

  setLoading(isLoading: boolean): void {
    this.setState({ isLoading }, 'set_loading');
  }

  setError(error: string | null): void {
    this.setState({ error }, 'set_error');
    if (error) {
      this.recordError();
    }
  }

  clearError(): void {
    this.setState({ error: null }, 'clear_error');
  }

  // ===== WebSocket Actions =====

  setWsConnected(connected: boolean): void {
    this.setState({ wsConnected: connected }, 'set_ws_connected');
  }

  updateWsMessage(): void {
    this.setState({ lastWsMessage: Date.now() }, 'update_ws_message');
  }

  // ===== Query Methods =====

  getProfileById(profileId: string): any | null {
    return this.state.profiles.find(p => p.id === profileId) || null;
  }

  getProfilesByStatus(status: string): any[] {
    return this.state.profiles.filter(p => this.state.profileStates[p.id] === status);
  }

  getPipelineById(pipelineId: string): any | null {
    return this.state.pipelines.find(p => p.id === pipelineId) || null;
  }

  // ===== History & Stats =====

  getStateHistory(): StateHistoryEntry[] {
    return [...this.stateHistory];
  }

  clearStateHistory(): void {
    this.stateHistory = [];
  }

  resetState(): void {
    this.setState(this.getInitialState(), 'reset_state');
  }

  getStateStats(): {
    subscribers: number;
    historySize: number;
    profilesCount: number;
    pipelinesCount: number;
    lastUpdate: number | null;
    hasError: boolean;
    isLoading: boolean;
    wsConnected: boolean;
  } {
    return {
      subscribers: this.subscribers.size,
      historySize: this.stateHistory.length,
      profilesCount: this.state.profiles.length,
      pipelinesCount: this.state.pipelines.length,
      lastUpdate: this.state.lastUpdate,
      hasError: !!this.state.error,
      isLoading: this.state.isLoading,
      wsConnected: this.state.wsConnected
    };
  }
}

// Export singleton instance
export const stateService = new StateService();

