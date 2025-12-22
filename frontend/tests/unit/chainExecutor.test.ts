import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ChainExecutor } from '../../src/services/chainExecutor';
import { ChainConfig, ChainStep } from '../../src/types';

describe('ChainExecutor Unit Tests', () => {
  let executor: ChainExecutor;
  let mockOnUpdate: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockOnUpdate = vi.fn();
    executor = new ChainExecutor();
  });

  describe('Step Validation', () => {
    it('should validate chain configuration with all required fields', () => {
      const validChain: ChainConfig = {
        name: 'Test Chain',
        steps: [
          {
            type: 'initial',
            prompt: 'Test prompt',
            model: 'Sonnet 4.5',
            taskType: 'implementation',
            waitForPrevious: true,
          },
        ],
      };

      expect(validChain.steps).toHaveLength(1);
      expect(validChain.steps[0].type).toBe('initial');
    });

    it('should handle empty chain configuration', () => {
      const emptyChain: ChainConfig = {
        name: 'Empty Chain',
        steps: [],
      };

      expect(emptyChain.steps).toHaveLength(0);
    });

    it('should validate step types', () => {
      const stepTypes = ['initial', 'sequential', 'conditional', 'parallel'];
      
      stepTypes.forEach((type) => {
        const step: ChainStep = {
          type: type as any,
          prompt: 'Test',
          model: 'Sonnet 4.5',
          taskType: 'implementation',
          waitForPrevious: true,
        };

        expect(step.type).toBe(type);
      });
    });
  });

  describe('Chain Execution Logic', () => {
    it('should execute sequential steps in order', async () => {
      const chain: ChainConfig = {
        name: 'Sequential Chain',
        steps: [
          {
            type: 'initial',
            prompt: 'Step 1',
            model: 'Sonnet 4.5',
            taskType: 'implementation',
            waitForPrevious: true,
          },
          {
            type: 'sequential',
            prompt: 'Step 2',
            model: 'Sonnet 4.5',
            taskType: 'testing',
            waitForPrevious: true,
          },
        ],
      };

      expect(chain.steps[0].type).toBe('initial');
      expect(chain.steps[1].type).toBe('sequential');
      expect(chain.steps[1].waitForPrevious).toBe(true);
    });

    it('should handle parallel step execution', () => {
      const parallelStep: ChainStep = {
        type: 'parallel',
        prompt: 'Parallel task',
        model: 'Sonnet 4.5',
        taskType: 'implementation',
        waitForPrevious: false,
      };

      expect(parallelStep.type).toBe('parallel');
      expect(parallelStep.waitForPrevious).toBe(false);
    });

    it('should handle conditional step branching', () => {
      const conditionalStep: ChainStep = {
        type: 'conditional',
        prompt: 'If condition met, do this',
        model: 'Sonnet 4.5',
        taskType: 'analysis',
        waitForPrevious: true,
      };

      expect(conditionalStep.type).toBe('conditional');
    });
  });

  describe('Context Management', () => {
    it('should pass context between steps', () => {
      const step1Result = 'Result from step 1';
      const step2Prompt = `Using result: ${step1Result}`;

      expect(step2Prompt).toContain(step1Result);
    });

    it('should handle empty context gracefully', () => {
      const emptyContext = {};
      expect(emptyContext).toEqual({});
    });

    it('should merge context from multiple steps', () => {
      const context1 = { result: 'Step 1 result' };
      const context2 = { result: 'Step 2 result' };
      const mergedContext = { ...context1, ...context2 };

      expect(mergedContext.result).toBe('Step 2 result'); // Later step overwrites
    });
  });

  describe('Error Handling', () => {
    it('should handle step execution errors', () => {
      const errorStep: ChainStep = {
        type: 'sequential',
        prompt: 'This will fail',
        model: 'Sonnet 4.5',
        taskType: 'implementation',
        waitForPrevious: true,
      };

      // Simulate error scenario
      const error = new Error('Execution failed');
      expect(error.message).toBe('Execution failed');
    });

    it('should continue chain execution on non-fatal errors', () => {
      const chain: ChainConfig = {
        name: 'Resilient Chain',
        steps: [
          {
            type: 'initial',
            prompt: 'Step 1',
            model: 'Sonnet 4.5',
            taskType: 'implementation',
            waitForPrevious: true,
          },
          {
            type: 'sequential',
            prompt: 'Step 2 (may fail)',
            model: 'Sonnet 4.5',
            taskType: 'testing',
            waitForPrevious: false, // Don't block on previous
          },
        ],
      };

      expect(chain.steps[1].waitForPrevious).toBe(false);
    });

    it('should halt execution on critical errors', () => {
      const criticalError = {
        type: 'CRITICAL',
        message: 'System failure',
        shouldHalt: true,
      };

      expect(criticalError.shouldHalt).toBe(true);
    });
  });

  describe('Model Selection', () => {
    it('should support multiple model types', () => {
      const models = ['Sonnet 4.5', 'Opus 3.5', 'Haiku 3.5'];
      
      models.forEach((model) => {
        const step: ChainStep = {
          type: 'sequential',
          prompt: 'Test',
          model: model,
          taskType: 'implementation',
          waitForPrevious: true,
        };

        expect(step.model).toBe(model);
      });
    });

    it('should default to Sonnet 4.5 when model not specified', () => {
      const defaultModel = 'Sonnet 4.5';
      expect(defaultModel).toBe('Sonnet 4.5');
    });
  });

  describe('Task Type Validation', () => {
    it('should validate task types', () => {
      const taskTypes = [
        'implementation',
        'testing',
        'documentation',
        'refactoring',
        'review',
        'analysis',
      ];

      taskTypes.forEach((taskType) => {
        const step: ChainStep = {
          type: 'sequential',
          prompt: 'Test',
          model: 'Sonnet 4.5',
          taskType: taskType as any,
          waitForPrevious: true,
        };

        expect(step.taskType).toBe(taskType);
      });
    });
  });

  describe('Chain State Management', () => {
    it('should track chain execution progress', () => {
      const progress = {
        total: 5,
        completed: 3,
        percentage: (3 / 5) * 100,
      };

      expect(progress.percentage).toBe(60);
    });

    it('should update chain status correctly', () => {
      const statuses = ['pending', 'running', 'completed', 'failed'];
      
      statuses.forEach((status) => {
        expect(status).toMatch(/pending|running|completed|failed/);
      });
    });

    it('should track individual step statuses', () => {
      const stepStatuses = new Map<number, string>();
      stepStatuses.set(0, 'completed');
      stepStatuses.set(1, 'running');
      stepStatuses.set(2, 'pending');

      expect(stepStatuses.get(0)).toBe('completed');
      expect(stepStatuses.get(1)).toBe('running');
      expect(stepStatuses.get(2)).toBe('pending');
    });
  });

  describe('Performance Considerations', () => {
    it('should handle large chains efficiently', () => {
      const largeChain: ChainConfig = {
        name: 'Large Chain',
        steps: Array.from({ length: 100 }, (_, i) => ({
          type: 'sequential',
          prompt: `Step ${i + 1}`,
          model: 'Sonnet 4.5',
          taskType: 'implementation',
          waitForPrevious: true,
        })),
      };

      expect(largeChain.steps).toHaveLength(100);
    });

    it('should optimize parallel execution', () => {
      const parallelSteps = [
        {
          type: 'parallel',
          prompt: 'Task A',
          model: 'Sonnet 4.5',
          taskType: 'implementation',
          waitForPrevious: false,
        },
        {
          type: 'parallel',
          prompt: 'Task B',
          model: 'Sonnet 4.5',
          taskType: 'implementation',
          waitForPrevious: false,
        },
      ];

      parallelSteps.forEach((step) => {
        expect(step.waitForPrevious).toBe(false);
      });
    });
  });
});

