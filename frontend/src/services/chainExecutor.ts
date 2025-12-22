import { 
  ChainConfig, 
  ChainExecution, 
  ChainStep, 
  ChainStepExecution, 
  ConditionalStep,
  ParallelStep,
  RunStatus,
  AgentRun,
  ErrorAnalysisResult 
} from '@/types';
import { contextManager } from '@/utils/contextManager';
import { codegenApi } from './api';

export class ChainExecutor {
  private static instance: ChainExecutor;
  private executions: Map<number, ChainExecution> = new Map();
  private nextExecutionId: number = 1;

  private constructor() {}

  static getInstance(): ChainExecutor {
    if (!ChainExecutor.instance) {
      ChainExecutor.instance = new ChainExecutor();
    }
    return ChainExecutor.instance;
  }

  /**
   * Execute a chain configuration
   */
  async executeChain(
    chain: ChainConfig,
    orgId: string,
    apiKey: string,
    onUpdate?: (execution: ChainExecution) => void
  ): Promise<ChainExecution> {
    const executionId = this.nextExecutionId++;
    const execution: ChainExecution = {
      id: executionId,
      chainConfig: chain,
      status: 'running',
      currentStep: 0,
      steps: [],
      startTime: new Date(),
      logs: [],
      context: contextManager.buildContextSnapshot([])
    };

    this.executions.set(executionId, execution);
    onUpdate?.(execution);

    try {
      this.addLog(execution, 'info', `Starting chain: ${chain.name}`);
      
      // Execute initial step
      await this.executeStep(
        chain.steps[0],
        0,
        execution,
        orgId,
        apiKey,
        onUpdate
      );

      // Execute subsequent steps
      for (let i = 1; i < chain.steps.length; i++) {
        execution.currentStep = i;
        await this.executeStep(
          chain.steps[i],
          i,
          execution,
          orgId,
          apiKey,
          onUpdate
        );
      }

      execution.status = 'completed';
      execution.endTime = new Date();
      this.addLog(execution, 'info', 'Chain completed successfully');

    } catch (error) {
      execution.status = 'failed';
      execution.endTime = new Date();
      const errorMessage = error instanceof Error ? error.message : String(error);
      this.addLog(execution, 'error', `Chain failed: ${errorMessage}`);
      
      // Perform error analysis
      if (chain.errorHandling?.autoRetry) {
        await this.attemptErrorRecovery(execution, orgId, apiKey, onUpdate);
      }
    }

    onUpdate?.(execution);
    return execution;
  }

  /**
   * Execute a single step
   */
  private async executeStep(
    step: ChainStep,
    stepIndex: number,
    execution: ChainExecution,
    orgId: string,
    apiKey: string,
    onUpdate?: (execution: ChainExecution) => void
  ): Promise<void> {
    this.addLog(execution, 'info', `Executing step ${stepIndex}: ${step.type}`);

    if (step.type === 'sequential' || step.type === 'initial') {
      await this.executeSequentialStep(step, stepIndex, execution, orgId, apiKey, onUpdate);
    } else if (step.type === 'conditional') {
      await this.executeConditionalStep(step as ConditionalStep, stepIndex, execution, orgId, apiKey, onUpdate);
    } else if (step.type === 'parallel') {
      await this.executeParallelStep(step as ParallelStep, stepIndex, execution, orgId, apiKey, onUpdate);
    }
  }

  /**
   * Execute sequential/initial step
   */
  private async executeSequentialStep(
    step: ChainStep & { prompt: string },
    stepIndex: number,
    execution: ChainExecution,
    orgId: string,
    apiKey: string,
    onUpdate?: (execution: ChainExecution) => void
  ): Promise<void> {
    // Build context from previous steps
    const context = contextManager.buildContext(
      execution.steps,
      execution.chainConfig.contextStrategy?.mode || 'accumulate',
      execution.chainConfig.contextStrategy?.includeErrors ?? true
    );

    // Replace template variables
    execution.context = contextManager.buildContextSnapshot(execution.steps);
    let prompt = contextManager.replaceTemplateVariables(step.prompt, execution.context);
    
    // Add context if not initial step
    if (stepIndex > 0 && context) {
      prompt = `${context}\n\n${prompt}`;
    }

    this.addLog(execution, 'debug', `Step ${stepIndex} prompt: ${prompt.substring(0, 200)}...`);

    // Create agent run
    const run = await codegenApi.createRun(
      orgId,
      apiKey,
      prompt,
      step.model,
      execution.chainConfig.repoId
    );

    const stepExecution: ChainStepExecution = {
      stepIndex,
      runId: run.id,
      status: 'running',
      type: step.type,
      taskType: step.taskType,
      prompt,
      startTime: new Date()
    };

    execution.steps.push(stepExecution);
    onUpdate?.(execution);

    // Wait for completion
    const result = await this.waitForRunCompletion(
      run.id,
      orgId,
      apiKey,
      (status) => {
        stepExecution.status = status;
        onUpdate?.(execution);
      }
    );

    // Update step with result
    stepExecution.status = result.status as RunStatus;
    stepExecution.result = result.result || result.summary;
    stepExecution.error = result.error;
    stepExecution.endTime = new Date();
    stepExecution.duration = stepExecution.endTime.getTime() - stepExecution.startTime!.getTime();

    this.addLog(
      execution,
      result.status === 'completed' ? 'info' : 'error',
      `Step ${stepIndex} ${result.status}: ${result.status === 'completed' ? 'Success' : result.error}`
    );

    if (result.status === 'failed') {
      throw new Error(`Step ${stepIndex} failed: ${result.error}`);
    }

    onUpdate?.(execution);
  }

  /**
   * Execute conditional step with retry logic
   */
  private async executeConditionalStep(
    step: ConditionalStep,
    stepIndex: number,
    execution: ChainExecution,
    orgId: string,
    apiKey: string,
    onUpdate?: (execution: ChainExecution) => void
  ): Promise<void> {
    let attempt = 0;
    let success = false;
    let lastError: string | undefined;

    while (attempt < step.maxRetries && !success) {
      attempt++;
      this.addLog(execution, 'info', `Step ${stepIndex} attempt ${attempt}/${step.maxRetries}`);

      try {
        execution.context = contextManager.buildContextSnapshot(execution.steps);
        let prompt = contextManager.replaceTemplateVariables(step.retryPrompt, execution.context);

        // Add error context if this is a retry
        if (attempt > 1 && lastError) {
          prompt = `Previous attempt failed with error: ${lastError}\n\n${prompt}`;
          
          // Perform error analysis if enabled
          if (step.errorAnalysis) {
            const analysis = await this.analyzeError(lastError, prompt, execution);
            prompt = `Error Analysis: ${analysis.analysis}\nSuggested Fix: ${analysis.suggestedFix}\n\n${prompt}`;
          }
        }

        const run = await codegenApi.createRun(
          orgId,
          apiKey,
          prompt,
          step.model,
          execution.chainConfig.repoId
        );

        const stepExecution: ChainStepExecution = {
          stepIndex,
          runId: run.id,
          status: 'running',
          type: 'conditional',
          taskType: step.taskType,
          attempt,
          maxAttempts: step.maxRetries,
          prompt,
          startTime: new Date()
        };

        execution.steps.push(stepExecution);
        onUpdate?.(execution);

        const result = await this.waitForRunCompletion(
          run.id,
          orgId,
          apiKey,
          (status) => {
            stepExecution.status = status;
            onUpdate?.(execution);
          }
        );

        stepExecution.status = result.status as RunStatus;
        stepExecution.result = result.result || result.summary;
        stepExecution.error = result.error;
        stepExecution.endTime = new Date();
        stepExecution.duration = stepExecution.endTime.getTime() - stepExecution.startTime!.getTime();

        // Check success condition
        if (result.status === 'completed' && this.checkSuccessCondition(result, step.successCondition)) {
          success = true;
          this.addLog(execution, 'info', `Step ${stepIndex} succeeded on attempt ${attempt}`);
        } else {
          lastError = result.error || 'Success condition not met';
          this.addLog(execution, 'warn', `Step ${stepIndex} attempt ${attempt} failed: ${lastError}`);
        }

        onUpdate?.(execution);

      } catch (error) {
        lastError = error instanceof Error ? error.message : String(error);
        this.addLog(execution, 'error', `Step ${stepIndex} attempt ${attempt} error: ${lastError}`);
      }
    }

    if (!success) {
      throw new Error(`Step ${stepIndex} failed after ${step.maxRetries} attempts. Last error: ${lastError}`);
    }
  }

  /**
   * Execute parallel branches
   */
  private async executeParallelStep(
    step: ParallelStep,
    stepIndex: number,
    execution: ChainExecution,
    orgId: string,
    apiKey: string,
    onUpdate?: (execution: ChainExecution) => void
  ): Promise<void> {
    this.addLog(execution, 'info', `Executing ${step.branches.length} parallel branches`);

    // Build current context
    execution.context = contextManager.buildContextSnapshot(execution.steps);
    const previousContext = contextManager.buildContext(
      execution.steps,
      execution.chainConfig.contextStrategy?.mode || 'selective'
    );

    // Start all branches
    const branchPromises = step.branches.map(async (branch, branchIndex) => {
      const prompt = contextManager.replaceTemplateVariables(
        `${previousContext}\n\n${branch.prompt}`,
        execution.context
      );

      const run = await codegenApi.createRun(
        orgId,
        apiKey,
        prompt,
        branch.model,
        execution.chainConfig.repoId
      );

      const branchExecution: ChainStepExecution = {
        stepIndex: `${stepIndex}_${branchIndex}`,
        runId: run.id,
        status: 'running',
        type: 'parallel',
        taskType: branch.taskType,
        branchIndex,
        prompt,
        startTime: new Date()
      };

      execution.steps.push(branchExecution);
      onUpdate?.(execution);

      const result = await this.waitForRunCompletion(
        run.id,
        orgId,
        apiKey,
        (status) => {
          branchExecution.status = status;
          onUpdate?.(execution);
        }
      );

      branchExecution.status = result.status as RunStatus;
      branchExecution.result = result.result || result.summary;
      branchExecution.error = result.error;
      branchExecution.endTime = new Date();
      branchExecution.duration = branchExecution.endTime.getTime() - branchExecution.startTime!.getTime();

      onUpdate?.(execution);

      return branchExecution;
    });

    // Wait based on merge strategy
    const mergeStrategy = step.mergeStrategy || 'wait-all';
    let completedBranches: ChainStepExecution[];

    if (mergeStrategy === 'wait-all') {
      completedBranches = await Promise.all(branchPromises);
    } else if (mergeStrategy === 'wait-any') {
      completedBranches = [await Promise.race(branchPromises)];
    } else {
      // race mode - same as wait-any for now
      completedBranches = [await Promise.race(branchPromises)];
    }

    // Check if any branch failed
    const failedBranches = completedBranches.filter(b => b.status === 'failed');
    if (failedBranches.length > 0 && mergeStrategy === 'wait-all') {
      const errors = failedBranches.map(b => `Branch ${b.branchIndex}: ${b.error}`).join(', ');
      throw new Error(`Parallel execution failed: ${errors}`);
    }

    this.addLog(execution, 'info', `Parallel execution completed: ${completedBranches.length} branches`);
  }

  /**
   * Wait for run completion with polling
   */
  private async waitForRunCompletion(
    runId: string,
    orgId: string,
    apiKey: string,
    onStatusUpdate?: (status: RunStatus) => void
  ): Promise<AgentRun> {
    const pollInterval = 3000; // 3 seconds
    const maxWaitTime = 600000; // 10 minutes
    const startTime = Date.now();

    while (Date.now() - startTime < maxWaitTime) {
      const run = await codegenApi.getRunDetails(orgId, apiKey, runId);
      
      onStatusUpdate?.(run.status as RunStatus);

      if (run.status === 'completed' || run.status === 'failed') {
        return run;
      }

      await this.sleep(pollInterval);
    }

    throw new Error(`Run ${runId} timed out after ${maxWaitTime}ms`);
  }

  /**
   * Check if success condition is met
   */
  private checkSuccessCondition(result: AgentRun, condition: string): boolean {
    const resultText = (result.result || result.summary || '').toLowerCase();
    
    // Support various success indicators
    const successKeywords = ['success', 'passed', 'completed', 'fixed', 'resolved'];
    const hasSuccess = successKeywords.some(keyword => resultText.includes(keyword));
    
    const errorKeywords = ['error', 'failed', 'exception', 'crash'];
    const hasError = errorKeywords.some(keyword => resultText.includes(keyword));
    
    // If condition is specified, check for it
    if (condition && condition !== 'default') {
      return resultText.includes(condition.toLowerCase());
    }
    
    // Default: success if completed without errors
    return hasSuccess || (!hasError && result.status === 'completed');
  }

  /**
   * Analyze error and provide suggestions
   */
  private async analyzeError(
    error: string,
    context: string,
    execution: ChainExecution
  ): Promise<ErrorAnalysisResult> {
    // Simple rule-based error analysis
    // In production, this could call an LLM for deeper analysis
    
    const analysis: ErrorAnalysisResult = {
      stepIndex: execution.currentStep,
      error,
      analysis: '',
      suggestedFix: '',
      confidence: 0.7
    };

    // Common error patterns
    if (error.includes('timeout')) {
      analysis.analysis = 'Operation timed out. The task may be too complex or the service is slow.';
      analysis.suggestedFix = 'Break down the task into smaller steps or increase timeout duration.';
    } else if (error.includes('syntax error') || error.includes('parse error')) {
      analysis.analysis = 'Code syntax error detected.';
      analysis.suggestedFix = 'Review the generated code for syntax issues and ensure proper formatting.';
    } else if (error.includes('not found') || error.includes('undefined')) {
      analysis.analysis = 'Missing dependency or undefined reference.';
      analysis.suggestedFix = 'Check that all required dependencies are imported and variables are defined.';
    } else {
      analysis.analysis = 'General error occurred.';
      analysis.suggestedFix = 'Review the error message and previous step results for clues.';
    }

    if (!execution.errorAnalysis) {
      execution.errorAnalysis = [];
    }
    execution.errorAnalysis.push(analysis);

    return analysis;
  }

  /**
   * Attempt to recover from chain failure
   */
  private async attemptErrorRecovery(
    execution: ChainExecution,
    orgId: string,
    apiKey: string,
    onUpdate?: (execution: ChainExecution) => void
  ): Promise<void> {
    const maxRetries = execution.chainConfig.errorHandling?.maxGlobalRetries || 1;
    this.addLog(execution, 'warn', 'Attempting error recovery...');

    // Implementation for recovery logic
    // This is a placeholder for sophisticated recovery strategies
  }

  /**
   * Add log entry
   */
  private addLog(
    execution: ChainExecution,
    level: 'info' | 'warn' | 'error' | 'debug',
    message: string,
    metadata?: Record<string, any>
  ): void {
    execution.logs.push({
      timestamp: new Date(),
      level,
      message,
      metadata
    });
  }

  /**
   * Utility to sleep
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Get execution by ID
   */
  getExecution(id: number): ChainExecution | undefined {
    return this.executions.get(id);
  }

  /**
   * Get all executions
   */
  getAllExecutions(): ChainExecution[] {
    return Array.from(this.executions.values());
  }
}

export const chainExecutor = ChainExecutor.getInstance();

