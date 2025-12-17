/**
 * Template Execution Service
 * 
 * Handles execution of production templates with:
 * - Real Codegen API integration
 * - Context passing between steps
 * - Error handling and retry logic
 * - Progress tracking
 * - Result aggregation
 */

import { ChainTemplate } from '@/types';
import { createAgentRun, getAgentRunStatus, AgentRunStatusResponse } from './codegenApi';

// ============================================================================
// Types
// ============================================================================

export interface TemplateExecutionContext {
  templateId: string;
  parameters: Record<string, any>;
  orgId: string;
  token: string;
  repository?: string;
}

export interface StepExecutionResult {
  stepIndex: number;
  stepType: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  agentRunId?: string;
  result?: string;
  error?: string;
  startTime: number;
  endTime?: number;
  duration?: number;
}

export interface TemplateExecutionResult {
  executionId: string;
  templateId: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'partial';
  steps: StepExecutionResult[];
  overallProgress: number;
  startTime: number;
  endTime?: number;
  totalDuration?: number;
  contextSnapshot: Record<string, any>;
  errors: string[];
}

// ============================================================================
// Template Execution Engine
// ============================================================================

export class TemplateExecutionService {
  private executionResults: Map<string, TemplateExecutionResult> = new Map();
  private pollingIntervals: Map<string, NodeJS.Timeout> = new Map();

  /**
   * Execute a template workflow
   */
  async executeTemplate(
    template: ChainTemplate,
    context: TemplateExecutionContext
  ): Promise<TemplateExecutionResult> {
    const executionId = this.generateExecutionId();
    const startTime = Date.now();

    console.log('[TemplateExecution] Starting execution:', {
      executionId,
      templateId: template.id,
      stepsCount: template.steps.length
    });

    // Initialize execution result
    const execution: TemplateExecutionResult = {
      executionId,
      templateId: template.id,
      status: 'running',
      steps: template.steps.map((step, index) => ({
        stepIndex: index,
        stepType: step.type,
        status: 'pending',
        startTime: Date.now()
      })),
      overallProgress: 0,
      startTime,
      contextSnapshot: { ...context.parameters },
      errors: []
    };

    this.executionResults.set(executionId, execution);

    // Execute template asynchronously
    this.executeTemplateSteps(template, context, execution).catch(error => {
      console.error('[TemplateExecution] Fatal error:', error);
      execution.status = 'failed';
      execution.errors.push(error.message);
      execution.endTime = Date.now();
      execution.totalDuration = execution.endTime - execution.startTime;
    });

    return execution;
  }

  /**
   * Execute template steps sequentially/parallel based on type
   */
  private async executeTemplateSteps(
    template: ChainTemplate,
    context: TemplateExecutionContext,
    execution: TemplateExecutionResult
  ): Promise<void> {
    const contextData: Record<string, any> = { ...context.parameters };

    for (let i = 0; i < template.steps.length; i++) {
      const step = template.steps[i];
      const stepResult = execution.steps[i];

      try {
        console.log(`[TemplateExecution] Executing step ${i}:`, step.type);
        stepResult.status = 'running';
        stepResult.startTime = Date.now();

        // Replace template variables in prompt
        // Get prompt based on step type
        let promptText = '';
        if ('prompt' in step) {
          promptText = step.prompt || '';
        } else if ('retryPrompt' in step) {
          promptText = step.retryPrompt || '';
        }
        
        const prompt = this.replaceTemplateVariables(
          promptText,
          contextData,
          i
        );

        // Handle different step types
        if (step.type === 'parallel' && 'branches' in step && step.branches) {
          // Execute parallel branches
          await this.executeParallelBranches(
            step.branches,
            context,
            contextData,
            stepResult,
            i
          );
        } else {
          // Execute single step
          await this.executeSingleStep(
            prompt,
            context,
            stepResult
          );
        }

        // Update context with result
        if (stepResult.result) {
          contextData[`step_${i}_result`] = stepResult.result;
          contextData.result = stepResult.result; // Latest result
        }

        // Update progress
        execution.overallProgress = Math.round(((i + 1) / template.steps.length) * 100);

        console.log(`[TemplateExecution] Step ${i} completed:`, {
          status: stepResult.status,
          duration: stepResult.duration
        });

      } catch (error: any) {
        console.error(`[TemplateExecution] Step ${i} failed:`, error);
        stepResult.status = 'failed';
        stepResult.error = error.message;
        stepResult.endTime = Date.now();
        stepResult.duration = stepResult.endTime - stepResult.startTime;

        execution.errors.push(`Step ${i} failed: ${error.message}`);

        // Handle conditional retry logic
        if (step.type === 'conditional' && 'maxRetries' in step && step.maxRetries) {
          const retrySuccess = await this.handleConditionalRetry(
            step,
            context,
            contextData,
            stepResult,
            i
          );
          
          if (!retrySuccess) {
            execution.status = 'failed';
            break;
          }
        } else {
          // Non-retry step failed, stop execution
          execution.status = 'failed';
          break;
        }
      }
    }

    // Mark execution as complete
    if (execution.status !== 'failed') {
      execution.status = 'completed';
    }
    execution.endTime = Date.now();
    execution.totalDuration = execution.endTime - execution.startTime;

    console.log('[TemplateExecution] Execution completed:', {
      executionId: execution.executionId,
      status: execution.status,
      duration: execution.totalDuration,
      errors: execution.errors.length
    });
  }

  /**
   * Execute a single step
   */
  private async executeSingleStep(
    prompt: string,
    context: TemplateExecutionContext,
    stepResult: StepExecutionResult
  ): Promise<void> {
    // Create agent run
    const response = await createAgentRun(
      context.orgId,
      context.token,
      {
        task: prompt,
        context: context.parameters,
        metadata: {
          repository: context.repository,
          templateId: context.templateId,
          stepIndex: stepResult.stepIndex
        }
      }
    );

    stepResult.agentRunId = response.agentRunId;

    // Poll for completion
    const result = await this.pollAgentRunStatus(
      response.agentRunId,
      context.orgId,
      context.token
    );

    stepResult.status = result.status === 'completed' ? 'completed' : 'failed';
    stepResult.result = result.result;
    stepResult.error = result.error;
    stepResult.endTime = Date.now();
    stepResult.duration = stepResult.endTime - stepResult.startTime;
  }

  /**
   * Execute parallel branches
   */
  private async executeParallelBranches(
    branches: any[],
    context: TemplateExecutionContext,
    contextData: Record<string, any>,
    stepResult: StepExecutionResult,
    stepIndex: number
  ): Promise<void> {
    const branchPromises = branches.map(async (branch, branchIndex) => {
      const branchPrompt = this.replaceTemplateVariables(
        branch.prompt,
        contextData,
        stepIndex
      );

      const response = await createAgentRun(
        context.orgId,
        context.token,
        {
          task: branchPrompt,
          context: contextData,
          metadata: {
            repository: context.repository,
            templateId: context.templateId,
            stepIndex,
            branchIndex
          }
        }
      );

      const result = await this.pollAgentRunStatus(
        response.agentRunId,
        context.orgId,
        context.token
      );

      return {
        branchIndex,
        agentRunId: response.agentRunId,
        result: result.result,
        status: result.status
      };
    });

    const branchResults = await Promise.all(branchPromises);

    // Merge branch results
    const allSuccessful = branchResults.every(r => r.status === 'completed');
    stepResult.status = allSuccessful ? 'completed' : 'failed';
    
    // Store branch results in context
    branchResults.forEach(br => {
      contextData[`step_${stepIndex}_branch_${br.branchIndex}_result`] = br.result;
    });

    // Combine results
    stepResult.result = branchResults.map(br => br.result).join('\n\n---\n\n');
    stepResult.endTime = Date.now();
    stepResult.duration = stepResult.endTime - stepResult.startTime;
  }

  /**
   * Handle conditional retry logic
   */
  private async handleConditionalRetry(
    step: any,
    context: TemplateExecutionContext,
    contextData: Record<string, any>,
    stepResult: StepExecutionResult,
    stepIndex: number
  ): Promise<boolean> {
    const maxRetries = step.maxRetries || 3;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      console.log(`[TemplateExecution] Retry attempt ${attempt}/${maxRetries} for step ${stepIndex}`);

      // Build retry prompt with error context
      const retryPrompt = this.replaceTemplateVariables(
        step.retryPrompt || 'Previous attempt failed. Please try again.',
        {
          ...contextData,
          error: stepResult.error,
          attempt,
          maxAttempts: maxRetries,
          failed_step: stepIndex
        },
        stepIndex
      );

      try {
        await this.executeSingleStep(retryPrompt, context, stepResult);
        
        if (stepResult.status === 'completed') {
          console.log(`[TemplateExecution] Retry successful on attempt ${attempt}`);
          return true;
        }
      } catch (error: any) {
        console.error(`[TemplateExecution] Retry attempt ${attempt} failed:`, error);
        stepResult.error = error.message;
      }
    }

    console.error(`[TemplateExecution] All ${maxRetries} retry attempts failed`);
    return false;
  }

  /**
   * Poll agent run status until completion
   */
  private async pollAgentRunStatus(
    agentRunId: string,
    orgId: string,
    token: string,
    maxAttempts: number = 60,
    intervalMs: number = 2000
  ): Promise<AgentRunStatusResponse> {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const status = await getAgentRunStatus(orgId, agentRunId, token);

      if (status.status === 'completed' || status.status === 'failed') {
        return status;
      }

      // Wait before next poll
      await new Promise(resolve => setTimeout(resolve, intervalMs));
    }

    throw new Error(`Agent run ${agentRunId} timed out after ${maxAttempts * intervalMs}ms`);
  }

  /**
   * Replace template variables in prompt
   */
  private replaceTemplateVariables(
    prompt: string,
    context: Record<string, any>,
    currentStep: number
  ): string {
    let result = prompt;

    // Replace step results
    for (let i = 0; i < currentStep; i++) {
      const stepKey = `step_${i}_result`;
      if (context[stepKey]) {
        result = result.replace(
          new RegExp(`{{${stepKey}}}`, 'g'),
          context[stepKey]
        );
      }
    }

    // Replace other context variables
    Object.keys(context).forEach(key => {
      result = result.replace(
        new RegExp(`{{${key}}}`, 'g'),
        String(context[key])
      );
    });

    return result;
  }

  /**
   * Get execution result
   */
  getExecutionResult(executionId: string): TemplateExecutionResult | undefined {
    return this.executionResults.get(executionId);
  }

  /**
   * Get all execution results
   */
  getAllExecutionResults(): TemplateExecutionResult[] {
    return Array.from(this.executionResults.values());
  }

  /**
   * Cancel execution
   */
  cancelExecution(executionId: string): void {
    const interval = this.pollingIntervals.get(executionId);
    if (interval) {
      clearInterval(interval);
      this.pollingIntervals.delete(executionId);
    }

    const execution = this.executionResults.get(executionId);
    if (execution && execution.status === 'running') {
      execution.status = 'failed';
      execution.errors.push('Execution cancelled by user');
      execution.endTime = Date.now();
      execution.totalDuration = execution.endTime - execution.startTime;
    }
  }

  /**
   * Generate unique execution ID
   */
  private generateExecutionId(): string {
    return `exec_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Singleton instance
export const templateExecutionService = new TemplateExecutionService();
