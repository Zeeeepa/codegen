/**
 * Production-Ready Workflow Templates for Codegen Controller Dashboard
 * 
 * These templates integrate with the real Codegen API and demonstrate:
 * - Chain orchestration with context passing
 * - Error handling and retry logic
 * - Parallel execution capabilities
 * - Template parameter configuration
 * - Real-world use cases
 */

import { ChainTemplate } from '@/types';

export const productionTemplates: Record<string, ChainTemplate> = {
  /**
   * Template 1: Code Review & Refactoring Pipeline
   * 
   * Multi-stage workflow that:
   * 1. Reviews code for issues
   * 2. Suggests improvements
   * 3. Refactors based on feedback
   * 4. Validates changes with tests
   */
  'code-review-pipeline': {
    id: 'code-review-pipeline',
    name: 'Code Review & Refactoring Pipeline',
    description: 'Comprehensive code review workflow with automated refactoring and validation',
    category: 'code-quality',
    tags: ['code-review', 'refactoring', 'testing', 'quality'],
    steps: [
      {
        type: 'initial',
        prompt: `Review the codebase and identify:
1. Code smells and anti-patterns
2. Performance bottlenecks
3. Security vulnerabilities
4. Missing error handling
5. Opportunities for refactoring

Provide a detailed analysis with specific file locations and recommendations.`,
        model: 'Sonnet 4.5',
        taskType: 'code-review',
        description: 'Analyze code for issues and improvements'
      },
      {
        type: 'sequential',
        prompt: `Based on the code review results: {{result}}

Refactor the identified issues following these priorities:
1. Security vulnerabilities (highest priority)
2. Critical bugs
3. Performance improvements
4. Code maintainability

Make changes and explain each modification.`,
        model: 'Sonnet 4.5',
        taskType: 'refactoring',
        waitForPrevious: true,
        description: 'Apply refactoring based on review'
      },
      {
        type: 'sequential',
        prompt: `Validate the refactored code: {{step_1_result}}

1. Run existing tests to ensure no regressions
2. Add new tests for refactored code
3. Verify performance improvements
4. Check code coverage

Report validation results with metrics.`,
        model: 'Sonnet 4.5',
        taskType: 'testing',
        waitForPrevious: true,
        description: 'Validate refactored code with tests'
      },
      {
        type: 'conditional',
        maxRetries: 3,
        successCondition: 'tests_passed',
        retryPrompt: `Tests failed: {{error}}

Review failure in step {{failed_step}}:
{{step_1_result}}

Fix the issues and try again. Attempt {{attempt}}/{{maxAttempts}}`,
        model: 'Sonnet 4.5',
        taskType: 'debugging',
        errorAnalysis: true,
        description: 'Fix any test failures'
      }
    ],
    contextStrategy: {
      mode: 'selective', // Use selective mode to keep relevant context
      maxTokens: 10000,
      includeErrors: true,
      includeLogs: true
    },
    errorHandling: {
      autoRetry: true,
      maxGlobalRetries: 3,
      escalateOnFailure: true,
      notifyOnError: true
    }
  },

  /**
   * Template 2: API Integration Builder
   * 
   * Builds complete API integrations with:
   * 1. API client generation
   * 2. Type definitions
   * 3. Error handling
   * 4. Integration tests
   */
  'api-integration-builder': {
    id: 'api-integration-builder',
    name: 'API Integration Builder',
    description: 'Generate complete API integrations with types, error handling, and tests',
    category: 'integration',
    tags: ['api', 'integration', 'types', 'testing'],
    steps: [
      {
        type: 'initial',
        prompt: `Generate a complete API integration for the specified endpoint.

Create:
1. TypeScript interfaces for request/response types
2. API client class with methods for each endpoint
3. Error handling with retry logic
4. Rate limiting support
5. Request/response logging

Use axios or fetch, include proper error types and status code handling.`,
        model: 'Sonnet 4.5',
        taskType: 'implementation',
        description: 'Generate API client with types'
      },
      {
        type: 'parallel',
        model: 'Sonnet 4.5',
        branches: [
          {
            prompt: `Write integration tests for the API client: {{result}}

Include tests for:
1. Successful requests
2. Error handling (4xx, 5xx)
3. Retry logic
4. Rate limiting
5. Timeout handling

Use jest or vitest with proper mocking.`,
            model: 'Sonnet 4.5',
            taskType: 'testing',
            description: 'Create integration tests'
          },
          {
            prompt: `Create comprehensive documentation for the API client: {{result}}

Include:
1. Installation instructions
2. Authentication setup
3. Usage examples for each method
4. Error handling guide
5. Best practices

Format as markdown with code examples.`,
            model: 'Sonnet 4.5',
            taskType: 'documentation',
            description: 'Write API documentation'
          }
        ],
        mergeStrategy: 'wait-all',
        description: 'Generate tests and docs in parallel'
      },
      {
        type: 'sequential',
        prompt: `Review the complete API integration:

Implementation: {{step_0_result}}
Tests: {{step_1_branch_0_result}}
Documentation: {{step_1_branch_1_result}}

Validate:
1. All endpoints are covered
2. Error handling is comprehensive
3. Tests achieve >80% coverage
4. Documentation is complete

Provide a quality assessment and any improvements needed.`,
        model: 'Sonnet 4.5',
        taskType: 'code-review',
        waitForPrevious: true,
        description: 'Review and validate integration'
      }
    ],
    contextStrategy: {
      mode: 'accumulate', // Need full context for integration work
      maxTokens: 12000,
      includeErrors: true
    },
    errorHandling: {
      autoRetry: true,
      maxGlobalRetries: 2,
      escalateOnFailure: true,
      notifyOnError: true
    }
  },

  /**
   * Template 3: Bug Investigation & Fix
   * 
   * Comprehensive debugging workflow:
   * 1. Reproduce bug
   * 2. Root cause analysis
   * 3. Fix implementation
   * 4. Regression test
   */
  'bug-investigation-fix': {
    id: 'bug-investigation-fix',
    name: 'Bug Investigation & Fix',
    description: 'Systematic bug investigation with root cause analysis and comprehensive fix',
    category: 'debugging',
    tags: ['debugging', 'bug-fix', 'investigation', 'testing'],
    steps: [
      {
        type: 'initial',
        prompt: `Investigate the reported bug systematically:

1. Reproduce the issue
2. Identify affected components
3. Trace the execution flow
4. Find the root cause
5. Assess impact and severity

Provide detailed findings with:
- Steps to reproduce
- Expected vs actual behavior
- Root cause analysis
- Affected code locations
- Recommended fix approach`,
        model: 'Sonnet 4.5',
        taskType: 'debugging',
        description: 'Investigate and identify root cause'
      },
      {
        type: 'sequential',
        prompt: `Implement fix for bug: {{result}}

Requirements:
1. Fix the root cause (not just symptoms)
2. Handle edge cases
3. Add defensive programming
4. Include error logging
5. Update documentation if needed

Explain the fix strategy and implementation.`,
        model: 'Sonnet 4.5',
        taskType: 'implementation',
        waitForPrevious: true,
        description: 'Implement comprehensive fix'
      },
      {
        type: 'sequential',
        prompt: `Create regression test for bug fix: {{step_1_result}}

Test must:
1. Reproduce the original bug scenario
2. Verify the fix works correctly
3. Test edge cases
4. Ensure no side effects
5. Add to CI/CD pipeline

Use appropriate testing framework with clear assertions.`,
        model: 'Sonnet 4.5',
        taskType: 'testing',
        waitForPrevious: true,
        description: 'Create regression test'
      },
      {
        type: 'conditional',
        maxRetries: 5,
        successCondition: 'test_passed',
        retryPrompt: `Fix validation failed: {{error}}

Investigation: {{step_0_result}}
Fix attempt: {{step_1_result}}
Test: {{step_2_result}}

Error indicates the fix is incomplete. Attempt {{attempt}}/{{maxAttempts}}.

Re-analyze and provide an improved fix addressing: {{error}}`,
        model: 'Sonnet 4.5',
        taskType: 'debugging',
        errorAnalysis: true,
        description: 'Validate fix with retry logic'
      }
    ],
    contextStrategy: {
      mode: 'selective',
      maxTokens: 8000,
      includeErrors: true,
      includeLogs: true
    },
    errorHandling: {
      autoRetry: true,
      maxGlobalRetries: 3,
      escalateOnFailure: true,
      notifyOnError: true
    }
  },

  /**
   * Template 4: Feature Implementation Sprint
   * 
   * Complete feature development workflow:
   * 1. Design & planning
   * 2. Implementation
   * 3. Testing
   * 4. Documentation
   */
  'feature-implementation-sprint': {
    id: 'feature-implementation-sprint',
    name: 'Feature Implementation Sprint',
    description: 'Complete feature development from design to deployment with testing and docs',
    category: 'implementation',
    tags: ['feature', 'implementation', 'testing', 'documentation'],
    steps: [
      {
        type: 'initial',
        prompt: `Design the feature implementation:

Create:
1. Technical design document
2. Component architecture
3. API interface definitions
4. Database schema (if needed)
5. State management approach

Include diagrams and code structure outline.`,
        model: 'Sonnet 4.5',
        taskType: 'design',
        description: 'Design feature architecture'
      },
      {
        type: 'parallel',
        model: 'Sonnet 4.5',
        branches: [
          {
            prompt: `Implement the backend/API layer for: {{result}}

Create:
1. API endpoints
2. Business logic
3. Data access layer
4. Input validation
5. Error handling

Follow REST best practices and include proper status codes.`,
            model: 'Sonnet 4.5',
            taskType: 'implementation',
            description: 'Implement backend/API'
          },
          {
            prompt: `Implement the frontend/UI layer for: {{result}}

Create:
1. React components
2. State management (Redux/Context)
3. API integration
4. Form validation
5. Error handling UI

Follow design system and accessibility guidelines.`,
            model: 'Sonnet 4.5',
            taskType: 'implementation',
            description: 'Implement frontend/UI'
          }
        ],
        mergeStrategy: 'wait-all',
        description: 'Implement frontend and backend in parallel'
      },
      {
        type: 'parallel',
        model: 'Sonnet 4.5',
        branches: [
          {
            prompt: `Write unit tests for backend: {{step_1_branch_0_result}}

Test coverage:
1. API endpoint tests
2. Business logic tests
3. Error handling tests
4. Edge cases
5. Integration tests

Achieve >80% code coverage.`,
            model: 'Sonnet 4.5',
            taskType: 'testing',
            description: 'Create backend tests'
          },
          {
            prompt: `Write tests for frontend: {{step_1_branch_1_result}}

Test coverage:
1. Component tests (React Testing Library)
2. Integration tests
3. User interaction tests
4. Error state tests
5. Accessibility tests

Achieve >80% code coverage.`,
            model: 'Sonnet 4.5',
            taskType: 'testing',
            description: 'Create frontend tests'
          },
          {
            prompt: `Create comprehensive documentation:

Design: {{step_0_result}}
Backend: {{step_1_branch_0_result}}
Frontend: {{step_1_branch_1_result}}

Document:
1. Feature overview
2. API documentation
3. Usage guide
4. Configuration
5. Deployment instructions

Include code examples and screenshots.`,
            model: 'Sonnet 4.5',
            taskType: 'documentation',
            description: 'Create documentation'
          }
        ],
        mergeStrategy: 'wait-all',
        description: 'Create tests and docs in parallel'
      },
      {
        type: 'sequential',
        prompt: `Final review and integration:

Design: {{step_0_result}}
Backend: {{step_1_branch_0_result}}
Frontend: {{step_1_branch_1_result}}
Backend Tests: {{step_2_branch_0_result}}
Frontend Tests: {{step_2_branch_1_result}}
Documentation: {{step_2_branch_2_result}}

Verify:
1. All requirements met
2. Tests pass
3. Code quality standards met
4. Documentation complete
5. Ready for deployment

Provide deployment checklist.`,
        model: 'Sonnet 4.5',
        taskType: 'code-review',
        waitForPrevious: true,
        description: 'Final review and validation'
      }
    ],
    contextStrategy: {
      mode: 'accumulate',
      maxTokens: 15000,
      includeErrors: true
    },
    errorHandling: {
      autoRetry: true,
      maxGlobalRetries: 2,
      escalateOnFailure: true,
      notifyOnError: true
    }
  },

  /**
   * Template 5: Security Audit & Remediation
   * 
   * Comprehensive security workflow:
   * 1. Security scan
   * 2. Vulnerability assessment
   * 3. Remediation
   * 4. Verification
   */
  'security-audit-remediation': {
    id: 'security-audit-remediation',
    name: 'Security Audit & Remediation',
    description: 'Comprehensive security audit with vulnerability detection and fixes',
    category: 'security',
    tags: ['security', 'audit', 'vulnerability', 'compliance'],
    steps: [
      {
        type: 'initial',
        prompt: `Perform comprehensive security audit:

Scan for:
1. SQL injection vulnerabilities
2. XSS (Cross-Site Scripting)
3. CSRF issues
4. Authentication/authorization flaws
5. Insecure dependencies
6. Sensitive data exposure
7. Security misconfigurations
8. Insufficient logging

Provide detailed findings with CVSS scores and remediation priorities.`,
        model: 'Sonnet 4.5',
        taskType: 'security-audit',
        description: 'Scan for security vulnerabilities'
      },
      {
        type: 'sequential',
        prompt: `Assess vulnerability impact: {{result}}

For each vulnerability:
1. Severity rating (Critical/High/Medium/Low)
2. Exploitability assessment
3. Business impact
4. Affected components
5. Recommended remediation approach

Prioritize by risk score.`,
        model: 'Sonnet 4.5',
        taskType: 'security-audit',
        waitForPrevious: true,
        description: 'Assess vulnerability impact'
      },
      {
        type: 'sequential',
        prompt: `Implement security fixes: {{step_1_result}}

Fix all Critical and High vulnerabilities:
1. Input validation and sanitization
2. Authentication improvements
3. Authorization checks
4. Dependency updates
5. Configuration hardening
6. Logging enhancements

Include security best practices and explain each fix.`,
        model: 'Sonnet 4.5',
        taskType: 'implementation',
        waitForPrevious: true,
        description: 'Implement security fixes'
      },
      {
        type: 'parallel',
        model: 'Sonnet 4.5',
        branches: [
          {
            prompt: `Create security tests: {{step_2_result}}

Test:
1. Input validation
2. Authentication flows
3. Authorization checks
4. XSS prevention
5. SQL injection prevention
6. CSRF protection

Use security testing frameworks.`,
            model: 'Sonnet 4.5',
            taskType: 'testing',
            description: 'Create security tests'
          },
          {
            prompt: `Document security improvements: {{step_2_result}}

Document:
1. Vulnerabilities found and fixed
2. Security enhancements made
3. Updated security guidelines
4. Secure coding practices
5. Compliance status

Format as security report.`,
            model: 'Sonnet 4.5',
            taskType: 'documentation',
            description: 'Document security improvements'
          }
        ],
        mergeStrategy: 'wait-all',
        description: 'Create tests and docs in parallel'
      },
      {
        type: 'sequential',
        prompt: `Final security verification:

Audit: {{step_0_result}}
Assessment: {{step_1_result}}
Fixes: {{step_2_result}}
Tests: {{step_3_branch_0_result}}
Documentation: {{step_3_branch_1_result}}

Verify:
1. All critical vulnerabilities fixed
2. Security tests pass
3. No new vulnerabilities introduced
4. Compliance requirements met

Provide security certification report.`,
        model: 'Sonnet 4.5',
        taskType: 'security-audit',
        waitForPrevious: true,
        description: 'Final security verification'
      }
    ],
    contextStrategy: {
      mode: 'selective',
      maxTokens: 12000,
      includeErrors: true,
      includeLogs: true
    },
    errorHandling: {
      autoRetry: true,
      maxGlobalRetries: 2,
      escalateOnFailure: true,
      notifyOnError: true
    }
  }
};

/**
 * Get template by ID
 */
export function getProductionTemplate(id: string): ChainTemplate | undefined {
  return productionTemplates[id];
}

/**
 * Get all production templates
 */
export function getAllProductionTemplates(): ChainTemplate[] {
  return Object.values(productionTemplates);
}

/**
 * Get templates by category
 */
export function getProductionTemplatesByCategory(category: string): ChainTemplate[] {
  return Object.values(productionTemplates).filter(t => t.category === category);
}

/**
 * Get template categories
 */
export function getProductionTemplateCategories(): string[] {
  const categories = new Set(Object.values(productionTemplates).map(t => t.category));
  return Array.from(categories);
}
