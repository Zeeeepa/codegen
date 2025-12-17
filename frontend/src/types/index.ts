export type RunStatus = 'pending' | 'running' | 'completed' | 'failed';

export type ChainStepType = 'initial' | 'sequential' | 'conditional' | 'parallel';

export type TaskType = 
  | 'implementation'
  | 'testing'
  | 'debugging'
  | 'refactoring'
  | 'documentation'
  | 'review'
  | 'deployment'
  | 'custom'
  | 'code-review'
  | 'design'
  | 'security-audit';

export interface Repository {
  id: number;
  name: string;
  full_name: string;
  description?: string;
}

export interface AgentRun {
  id: string;
  status: RunStatus;
  prompt: string;
  model?: string;
  result?: string;
  summary?: string;
  error?: string;
  created_at?: string;
  updated_at?: string;
  pr_urls?: string[];
}

export interface ChainStepBase {
  type: ChainStepType;
  model: string;
  taskType?: TaskType;
  description?: string;
}

export interface InitialStep extends ChainStepBase {
  type: 'initial';
  prompt: string;
}

export interface SequentialStep extends ChainStepBase {
  type: 'sequential';
  prompt: string;
  waitForPrevious: boolean;
}

export interface ConditionalStep extends ChainStepBase {
  type: 'conditional';
  maxRetries: number;
  successCondition: string;
  retryPrompt: string;
  errorAnalysis?: boolean;
}

export interface ParallelBranch {
  prompt: string;
  model: string;
  taskType?: TaskType;
  description?: string;
}

export interface ParallelStep extends ChainStepBase {
  type: 'parallel';
  branches: ParallelBranch[];
  mergeStrategy?: 'wait-all' | 'wait-any' | 'race';
}

export type ChainStep = InitialStep | SequentialStep | ConditionalStep | ParallelStep;

export interface ChainConfig {
  id?: number;
  name: string;
  description: string;
  repoId?: string;
  steps: ChainStep[];
  contextStrategy?: ContextStrategy;
  errorHandling?: ErrorHandlingConfig;
}

export interface ContextStrategy {
  mode: 'accumulate' | 'selective' | 'minimal';
  maxTokens?: number;
  includeErrors?: boolean;
  includeLogs?: boolean;
}

export interface ErrorHandlingConfig {
  autoRetry: boolean;
  maxGlobalRetries: number;
  escalateOnFailure: boolean;
  notifyOnError: boolean;
}

export interface ChainStepExecution {
  stepIndex: number | string;
  runId: string;
  status: RunStatus;
  type: ChainStepType;
  taskType?: TaskType;
  attempt?: number;
  maxAttempts?: number;
  prompt?: string;
  result?: string;
  error?: string;
  startTime?: Date;
  endTime?: Date;
  duration?: number;
  branchIndex?: number;
  contextSnapshot?: ChainContextSnapshot;
}

export interface ChainContextSnapshot {
  stepResults: Record<string, string>;
  globalState: Record<string, any>;
  errorHistory: Array<{step: number; error: string; timestamp: Date}>;
  metrics: {
    totalSteps: number;
    completedSteps: number;
    failedSteps: number;
    totalDuration: number;
  };
}

export interface ChainExecution {
  id: number;
  chainConfig: ChainConfig;
  status: RunStatus;
  currentStep: number;
  steps: ChainStepExecution[];
  startTime: Date;
  endTime?: Date;
  logs: ChainLog[];
  context: ChainContextSnapshot;
  errorAnalysis?: ErrorAnalysisResult[];
}

export interface ChainLog {
  timestamp: Date;
  level: 'info' | 'warn' | 'error' | 'debug';
  message: string;
  metadata?: Record<string, any>;
}

export interface ErrorAnalysisResult {
  stepIndex: number;
  error: string;
  analysis: string;
  suggestedFix: string;
  confidence: number;
}

export interface ChainTemplate {
  id: string;
  name: string;
  description: string;
  category: 'workflow' | 'quality' | 'deployment' | 'debugging' | 'custom' | 'code-quality' | 'integration' | 'implementation' | 'security';
  steps: ChainStep[];
  tags: string[];
  popularity?: number;
  contextStrategy?: ContextStrategy;
  errorHandling?: ErrorHandlingConfig;
}

export interface TaskPromptTemplate {
  id: string;
  taskType: TaskType;
  name: string;
  template: string;
  variables: string[];
  examples: string[];
}
