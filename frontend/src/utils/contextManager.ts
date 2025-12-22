import { ChainContextSnapshot, ChainStepExecution, AgentRun } from '@/types';

export class ContextManager {
  private static instance: ContextManager;
  private maxTokens: number = 8000;

  private constructor() {}

  static getInstance(): ContextManager {
    if (!ContextManager.instance) {
      ContextManager.instance = new ContextManager();
    }
    return ContextManager.instance;
  }

  setMaxTokens(tokens: number) {
    this.maxTokens = tokens;
  }

  /**
   * Build context for next step based on previous results
   */
  buildContext(
    steps: ChainStepExecution[],
    mode: 'accumulate' | 'selective' | 'minimal' = 'accumulate',
    includeErrors: boolean = true
  ): string {
    if (mode === 'minimal') {
      return this.buildMinimalContext(steps);
    } else if (mode === 'selective') {
      return this.buildSelectiveContext(steps, includeErrors);
    }
    return this.buildAccumulatedContext(steps, includeErrors);
  }

  private buildAccumulatedContext(steps: ChainStepExecution[], includeErrors: boolean): string {
    let context = '=== Accumulated Context ===\n\n';
    
    steps.forEach((step, idx) => {
      context += `Step ${step.stepIndex} (${step.type}):\n`;
      if (step.taskType) {
        context += `  Task Type: ${step.taskType}\n`;
      }
      if (step.result) {
        context += `  Result: ${this.truncateText(step.result, 500)}\n`;
      }
      if (includeErrors && step.error) {
        context += `  Error: ${step.error}\n`;
      }
      if (step.duration) {
        context += `  Duration: ${step.duration}ms\n`;
      }
      context += '\n';
    });

    return this.enforceTokenLimit(context);
  }

  private buildSelectiveContext(steps: ChainStepExecution[], includeErrors: boolean): string {
    let context = '=== Selective Context ===\n\n';
    
    // Only include last successful result and any errors
    const lastSuccess = steps.filter(s => s.status === 'completed').pop();
    const errors = includeErrors ? steps.filter(s => s.status === 'failed') : [];
    
    if (lastSuccess) {
      context += `Last Successful Step ${lastSuccess.stepIndex}:\n`;
      context += `  Result: ${this.truncateText(lastSuccess.result || '', 800)}\n\n`;
    }
    
    if (errors.length > 0) {
      context += 'Recent Errors:\n';
      errors.slice(-3).forEach(err => {
        context += `  Step ${err.stepIndex}: ${err.error}\n`;
      });
    }

    return this.enforceTokenLimit(context);
  }

  private buildMinimalContext(steps: ChainStepExecution[]): string {
    const lastStep = steps[steps.length - 1];
    if (!lastStep) return '';
    
    return `Previous step (${lastStep.stepIndex}): ${this.truncateText(lastStep.result || lastStep.error || 'No output', 200)}`;
  }

  /**
   * Replace template variables in prompt
   */
  replaceTemplateVariables(template: string, context: ChainContextSnapshot): string {
    let result = template;
    
    // Replace step-specific results
    Object.entries(context.stepResults).forEach(([stepIndex, stepResult]) => {
      result = result.replace(new RegExp(`\\{\\{step_${stepIndex}_result\\}\\}`, 'g'), stepResult);
    });
    
    // Replace last result
    const lastResult = Object.values(context.stepResults).pop() || '';
    result = result.replace(/\{\{result\}\}/g, lastResult);
    
    // Replace error information
    const lastError = context.errorHistory[context.errorHistory.length - 1];
    result = result.replace(/\{\{error\}\}/g, lastError?.error || '');
    
    // Replace attempt number
    const attemptCount = context.errorHistory.filter(e => 
      e.step === context.metrics.completedSteps
    ).length + 1;
    result = result.replace(/\{\{attempt\}\}/g, attemptCount.toString());
    
    // Replace metrics
    result = result.replace(/\{\{total_steps\}\}/g, context.metrics.totalSteps.toString());
    result = result.replace(/\{\{completed_steps\}\}/g, context.metrics.completedSteps.toString());
    
    return result;
  }

  /**
   * Build context snapshot for current execution state
   */
  buildContextSnapshot(steps: ChainStepExecution[]): ChainContextSnapshot {
    const stepResults: Record<string, string> = {};
    const errorHistory: Array<{step: number; error: string; timestamp: Date}> = [];
    let totalDuration = 0;
    let completedSteps = 0;
    let failedSteps = 0;

    steps.forEach(step => {
      if (typeof step.stepIndex === 'number') {
        if (step.result) {
          stepResults[step.stepIndex.toString()] = step.result;
        }
        
        if (step.error) {
          errorHistory.push({
            step: step.stepIndex,
            error: step.error,
            timestamp: step.endTime || new Date()
          });
        }
        
        if (step.duration) {
          totalDuration += step.duration;
        }
        
        if (step.status === 'completed') {
          completedSteps++;
        } else if (step.status === 'failed') {
          failedSteps++;
        }
      }
    });

    return {
      stepResults,
      globalState: {},
      errorHistory,
      metrics: {
        totalSteps: steps.length,
        completedSteps,
        failedSteps,
        totalDuration
      }
    };
  }

  /**
   * Merge parallel branch results
   */
  mergeParallelResults(branches: ChainStepExecution[]): string {
    let merged = '=== Parallel Execution Results ===\n\n';
    
    branches.forEach((branch, idx) => {
      merged += `Branch ${idx + 1}:\n`;
      merged += `  Status: ${branch.status}\n`;
      if (branch.result) {
        merged += `  Result: ${this.truncateText(branch.result, 400)}\n`;
      }
      if (branch.error) {
        merged += `  Error: ${branch.error}\n`;
      }
      merged += '\n';
    });

    return merged;
  }

  private truncateText(text: string, maxLength: number): string {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  }

  private enforceTokenLimit(context: string): string {
    // Rough estimation: 1 token ≈ 4 characters
    const maxChars = this.maxTokens * 4;
    if (context.length <= maxChars) return context;
    
    return context.substring(0, maxChars) + '\n\n[Context truncated to fit token limit]';
  }

  /**
   * Extract key information for error analysis
   */
  extractErrorContext(step: ChainStepExecution, previousSteps: ChainStepExecution[]): string {
    let errorContext = `Error in Step ${step.stepIndex} (${step.type}):\n`;
    errorContext += `Error: ${step.error}\n\n`;
    errorContext += `Prompt: ${step.prompt}\n\n`;
    
    if (previousSteps.length > 0) {
      errorContext += 'Previous Step Results:\n';
      previousSteps.slice(-2).forEach(prevStep => {
        errorContext += `  Step ${prevStep.stepIndex}: ${this.truncateText(prevStep.result || 'No output', 200)}\n`;
      });
    }

    return errorContext;
  }
}

export const contextManager = ContextManager.getInstance();

