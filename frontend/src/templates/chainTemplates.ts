import { ChainTemplate, TaskPromptTemplate } from '@/types';

export const chainTemplates: Record<string, ChainTemplate> = {
  'fix-until-works': {
    id: 'fix-until-works',
    name: 'Fix Until Works',
    description: 'Automatically retry fixes until tests pass with intelligent error analysis',
    category: 'debugging',
    tags: ['debugging', 'testing', 'auto-fix'],
    steps: [
      {
        type: 'initial',
        prompt: '',
        model: 'Sonnet 4.5',
        taskType: 'debugging',
        description: 'Initial fix attempt'
      },
      {
        type: 'conditional',
        maxRetries: 5,
        successCondition: 'test_passed',
        retryPrompt: 'The previous fix did not work. Error: {{error}}. Attempt {{attempt}}/{{maxAttempts}}. Please analyze the issue deeply and provide a different solution.',
        model: 'Sonnet 4.5',
        taskType: 'debugging',
        errorAnalysis: true,
        description: 'Retry with error analysis'
      }
    ],
    contextStrategy: {
      mode: 'selective',
      maxTokens: 6000,
      includeErrors: true,
      includeLogs: true
    },
    errorHandling: {
      autoRetry: true,
      maxGlobalRetries: 3,
      escalateOnFailure: false,
      notifyOnError: true
    }
  },
  
  'implement-test-document': {
    id: 'implement-test-document',
    name: 'Implement → Test → Document',
    description: 'Complete feature workflow from implementation to documentation',
    category: 'workflow',
    tags: ['implementation', 'testing', 'documentation'],
    steps: [
      {
        type: 'initial',
        prompt: '',
        model: 'Sonnet 4.5',
        taskType: 'implementation',
        description: 'Implement the feature'
      },
      {
        type: 'sequential',
        prompt: 'Write comprehensive unit tests for the implementation above. Implementation: {{result}}. Ensure all edge cases are covered.',
        model: 'Sonnet 4.5',
        taskType: 'testing',
        waitForPrevious: true,
        description: 'Create comprehensive tests'
      },
      {
        type: 'sequential',
        prompt: 'Update the documentation to reflect the changes. Implementation: {{step_0_result}}. Tests: {{step_1_result}}. Include usage examples.',
        model: 'Sonnet 4.5',
        taskType: 'documentation',
        waitForPrevious: true,
        description: 'Document the changes'
      }
    ],
    contextStrategy: {
      mode: 'accumulate',
      maxTokens: 8000,
      includeErrors: false
    }
  },

  'review-refactor-optimize': {
    id: 'review-refactor-optimize',
    name: 'Review → Refactor → Optimize',
    description: 'Comprehensive code quality improvement pipeline',
    category: 'quality',
    tags: ['review', 'refactoring', 'optimization', 'quality'],
    steps: [
      {
        type: 'initial',
        prompt: '',
        model: 'Sonnet 4.5',
        taskType: 'review',
        description: 'Initial code implementation'
      },
      {
        type: 'sequential',
        prompt: 'Review the code and identify areas for refactoring. Code: {{result}}. Focus on maintainability, readability, and design patterns.',
        model: 'Sonnet 4.5',
        taskType: 'review',
        waitForPrevious: true,
        description: 'Code review'
      },
      {
        type: 'sequential',
        prompt: 'Apply the refactoring suggestions. Review: {{step_1_result}}. Original code: {{step_0_result}}. Maintain functionality while improving structure.',
        model: 'Sonnet 4.5',
        taskType: 'refactoring',
        waitForPrevious: true,
        description: 'Apply refactoring'
      },
      {
        type: 'sequential',
        prompt: 'Optimize performance. Refactored code: {{step_2_result}}. Identify bottlenecks and apply performance improvements.',
        model: 'Sonnet 4.5',
        taskType: 'refactoring',
        waitForPrevious: true,
        description: 'Performance optimization'
      }
    ],
    contextStrategy: {
      mode: 'accumulate',
      maxTokens: 10000
    }
  },

  'parallel-feature': {
    id: 'parallel-feature',
    name: 'Parallel Feature Development',
    description: 'Develop multiple components simultaneously for faster delivery',
    category: 'workflow',
    tags: ['parallel', 'implementation', 'testing'],
    steps: [
      {
        type: 'initial',
        prompt: '',
        model: 'Sonnet 4.5',
        taskType: 'implementation',
        description: 'Feature specification'
      },
      {
        type: 'parallel',
        branches: [
          {
            prompt: 'Implement the frontend component based on: {{result}}',
            model: 'Sonnet 4.5',
            taskType: 'implementation',
            description: 'Frontend implementation'
          },
          {
            prompt: 'Implement the backend API based on: {{result}}',
            model: 'Sonnet 4.5',
            taskType: 'implementation',
            description: 'Backend implementation'
          },
          {
            prompt: 'Write integration tests based on: {{result}}',
            model: 'Sonnet 4.5',
            taskType: 'testing',
            description: 'Test suite'
          }
        ],
        model: 'Sonnet 4.5',
        mergeStrategy: 'wait-all',
        description: 'Parallel development'
      },
      {
        type: 'sequential',
        prompt: 'Integrate all components. Frontend: {{branch_0_result}}. Backend: {{branch_1_result}}. Tests: {{branch_2_result}}. Ensure they work together.',
        model: 'Sonnet 4.5',
        taskType: 'implementation',
        waitForPrevious: true,
        description: 'Integration step'
      }
    ],
    contextStrategy: {
      mode: 'selective',
      maxTokens: 12000
    }
  },

  'debug-cascade': {
    id: 'debug-cascade',
    name: 'Debug Cascade',
    description: 'Progressive debugging with escalating detail levels',
    category: 'debugging',
    tags: ['debugging', 'logging', 'troubleshooting'],
    steps: [
      {
        type: 'initial',
        prompt: '',
        model: 'Sonnet 4.5',
        taskType: 'debugging',
        description: 'Initial debug attempt'
      },
      {
        type: 'conditional',
        maxRetries: 4,
        successCondition: 'error_resolved',
        retryPrompt: 'Debug attempt {{attempt}} failed. Increase logging verbosity and add more diagnostic information. Previous error: {{error}}',
        model: 'Sonnet 4.5',
        taskType: 'debugging',
        errorAnalysis: true,
        description: 'Escalating debug attempts'
      },
      {
        type: 'sequential',
        prompt: 'Generate detailed diagnostic report. Debug results: {{result}}. Include root cause analysis and prevention recommendations.',
        model: 'Sonnet 4.5',
        taskType: 'documentation',
        waitForPrevious: true,
        description: 'Diagnostic report'
      }
    ],
    contextStrategy: {
      mode: 'accumulate',
      maxTokens: 8000,
      includeErrors: true,
      includeLogs: true
    },
    errorHandling: {
      autoRetry: true,
      maxGlobalRetries: 2,
      escalateOnFailure: true,
      notifyOnError: true
    }
  },

  'deployment-pipeline': {
    id: 'deployment-pipeline',
    name: 'Deployment Pipeline',
    description: 'Automated testing, building, and deployment workflow',
    category: 'deployment',
    tags: ['deployment', 'testing', 'ci-cd'],
    steps: [
      {
        type: 'initial',
        prompt: '',
        model: 'Sonnet 4.5',
        taskType: 'implementation',
        description: 'Code changes'
      },
      {
        type: 'sequential',
        prompt: 'Run all tests. Code: {{result}}. Report any failures.',
        model: 'Sonnet 4.5',
        taskType: 'testing',
        waitForPrevious: true,
        description: 'Test suite execution'
      },
      {
        type: 'conditional',
        maxRetries: 3,
        successCondition: 'build_success',
        retryPrompt: 'Build failed: {{error}}. Attempt {{attempt}}/{{maxAttempts}}. Fix build errors.',
        model: 'Sonnet 4.5',
        taskType: 'deployment',
        description: 'Build with retry'
      },
      {
        type: 'sequential',
        prompt: 'Deploy to staging. Build output: {{step_2_result}}. Verify deployment health.',
        model: 'Sonnet 4.5',
        taskType: 'deployment',
        waitForPrevious: true,
        description: 'Staging deployment'
      }
    ],
    contextStrategy: {
      mode: 'selective',
      maxTokens: 6000
    }
  }
};

export const taskPromptTemplates: Record<string, TaskPromptTemplate> = {
  implementation: {
    id: 'implementation',
    taskType: 'implementation',
    name: 'Feature Implementation',
    template: 'Implement {{feature_name}} with the following requirements:\n{{requirements}}\n\nUse best practices and include error handling.',
    variables: ['feature_name', 'requirements'],
    examples: [
      'Implement user authentication with email/password and OAuth2',
      'Implement data caching layer using Redis',
      'Implement REST API endpoints for user management'
    ]
  },
  
  testing: {
    id: 'testing',
    taskType: 'testing',
    name: 'Test Generation',
    template: 'Write {{test_type}} tests for:\n{{code_snippet}}\n\nInclude edge cases and error scenarios.',
    variables: ['test_type', 'code_snippet'],
    examples: [
      'Write unit tests for the authentication service',
      'Write integration tests for the payment API',
      'Write end-to-end tests for user registration flow'
    ]
  },
  
  debugging: {
    id: 'debugging',
    taskType: 'debugging',
    name: 'Bug Fix',
    template: 'Debug and fix the following issue:\n{{issue_description}}\n\nError: {{error_message}}\n\nProvide a detailed explanation of the root cause.',
    variables: ['issue_description', 'error_message'],
    examples: [
      'Fix memory leak in the data processing pipeline',
      'Resolve race condition in concurrent request handling',
      'Fix null pointer exception in user profile update'
    ]
  },
  
  refactoring: {
    id: 'refactoring',
    taskType: 'refactoring',
    name: 'Code Refactoring',
    template: 'Refactor the following code to improve {{improvement_goal}}:\n{{code_snippet}}\n\nMaintain existing functionality.',
    variables: ['improvement_goal', 'code_snippet'],
    examples: [
      'Refactor to improve code readability and maintainability',
      'Refactor to reduce code duplication',
      'Refactor to improve performance'
    ]
  },
  
  documentation: {
    id: 'documentation',
    taskType: 'documentation',
    name: 'Documentation',
    template: 'Create {{doc_type}} documentation for:\n{{subject}}\n\nInclude examples and best practices.',
    variables: ['doc_type', 'subject'],
    examples: [
      'Create API documentation with usage examples',
      'Create developer guide for the authentication system',
      'Create README with setup instructions'
    ]
  },
  
  review: {
    id: 'review',
    taskType: 'review',
    name: 'Code Review',
    template: 'Review the following code for {{review_focus}}:\n{{code_snippet}}\n\nProvide specific suggestions for improvement.',
    variables: ['review_focus', 'code_snippet'],
    examples: [
      'Review for security vulnerabilities',
      'Review for performance bottlenecks',
      'Review for code quality and best practices'
    ]
  },
  
  deployment: {
    id: 'deployment',
    taskType: 'deployment',
    name: 'Deployment',
    template: 'Prepare deployment for {{environment}}:\n{{deployment_details}}\n\nInclude rollback strategy.',
    variables: ['environment', 'deployment_details'],
    examples: [
      'Deploy to production with zero downtime',
      'Deploy to staging for testing',
      'Deploy hotfix to production'
    ]
  }
};

export function getTaskPrompt(taskType: string, variables: Record<string, string>): string {
  const template = taskPromptTemplates[taskType];
  if (!template) return '';
  
  let prompt = template.template;
  template.variables.forEach(variable => {
    const value = variables[variable] || '';
    prompt = prompt.replace(`{{${variable}}}`, value);
  });
  
  return prompt;
}

