import { Page } from '@playwright/test';
import { AgentRun } from '../../../src/types/codegen';

/**
 * Agent runs test fixture
 * Provides helper methods for testing agent functionality
 */
export const agentFixture = {
  /**
   * Create a new agent run via the UI
   */
  createAgentRun: async (page: Page, prompt: string, model?: string) => {
    await page.goto('/agents/create');
    await page.fill('textarea[name="prompt"]', prompt);
    
    if (model) {
      await page.selectOption('select[name="model"]', model);
    }
    
    await page.click('button[type="submit"]');
    
    // Wait for the agent run to be created and redirected
    await page.waitForURL(/\/agents\/\d+/);
    
    // Extract the agent run ID from the URL
    const url = page.url();
    const matches = url.match(/\/agents\/(\d+)/);
    return matches ? matches[1] : null;
  },

  /**
   * Navigate to the agents list page
   */
  goToAgentsList: async (page: Page) => {
    await page.goto('/agents');
    await page.waitForSelector('[data-testid="agents-list"]', { 
      timeout: 10000 
    });
  },

  /**
   * Search for agent runs
   */
  searchAgentRuns: async (page: Page, searchTerm: string) => {
    await page.fill('input[placeholder*="Search agent runs"]', searchTerm);
    await page.waitForTimeout(500); // Wait for debounced search
  },

  /**
   * Filter agent runs by status
   */
  filterByStatus: async (page: Page, status: string) => {
    await page.selectOption('select:near(text="All Status")', status);
    await page.waitForTimeout(500);
  },

  /**
   * Get agent run cards from the list
   */
  getAgentRunCards: async (page: Page) => {
    await page.waitForSelector('[data-testid="agent-run-card"]');
    return await page.locator('[data-testid="agent-run-card"]').all();
  },

  /**
   * Click on an agent run card
   */
  clickAgentRun: async (page: Page, index: number = 0) => {
    const cards = await agentFixture.getAgentRunCards(page);
    if (cards[index]) {
      await cards[index].click();
    }
  },

  /**
   * Mock agent runs API endpoints
   */
  mockAgentAPIs: async (page: Page, mockData: {
    runs?: AgentRun[];
    createResponse?: AgentRun;
    shouldFailCreate?: boolean;
  } = {}) => {
    const { runs = [], createResponse, shouldFailCreate = false } = mockData;

    // Mock the list agent runs endpoint
    await page.route('**/api/v1/organizations/*/agent/runs*', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: runs.length > 0 ? runs : agentFixture.getMockAgentRuns(),
            total: runs.length || 3,
            page: 1,
            per_page: 10,
          }),
        });
      }
    });

    // Mock the create agent run endpoint
    await page.route('**/api/v1/organizations/*/agent/run', async (route) => {
      if (route.request().method() === 'POST') {
        if (shouldFailCreate) {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'Failed to create agent run' }),
          });
        } else {
          const response = createResponse || agentFixture.getMockAgentRun();
          await route.fulfill({
            status: 201,
            contentType: 'application/json',
            body: JSON.stringify(response),
          });
        }
      }
    });

    // Mock individual agent run endpoint
    await page.route('**/api/v1/organizations/*/agent/run/*', async (route) => {
      if (route.request().method() === 'GET') {
        const url = route.request().url();
        const runId = url.split('/').pop();
        
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            ...agentFixture.getMockAgentRun(),
            id: runId,
          }),
        });
      }
    });
  },

  /**
   * Generate mock agent run data
   */
  getMockAgentRun: (overrides: Partial<AgentRun> = {}): AgentRun => {
    const baseRun: AgentRun = {
      id: 'test-run-' + Date.now(),
      organization_id: 'test-org-1',
      user_id: 'test-user-1',
      status: 'RUNNING',
      source_type: 'API',
      prompt: 'Fix the authentication bug in the user login flow',
      summary: 'Analyzing authentication flow and implementing fixes',
      model: 'claude-3-5-sonnet-20241022',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      progress_percentage: 45,
    };

    return { ...baseRun, ...overrides };
  },

  /**
   * Generate multiple mock agent runs
   */
  getMockAgentRuns: (count: number = 3): AgentRun[] => {
    const statuses: AgentRun['status'][] = ['RUNNING', 'COMPLETE', 'FAILED'];
    const prompts = [
      'Fix the authentication bug in the user login flow',
      'Refactor the database connection logic to use connection pooling',
      'Add comprehensive unit tests for the API endpoints',
    ];

    return Array.from({ length: count }, (_, i) => 
      agentFixture.getMockAgentRun({
        id: `test-run-${i + 1}`,
        status: statuses[i % statuses.length],
        prompt: prompts[i % prompts.length],
        progress_percentage: [100, 0, 75][i % 3],
        completed_at: i === 1 ? new Date().toISOString() : undefined,
      })
    );
  },

  /**
   * Verify agent run creation flow
   */
  verifyAgentCreationFlow: async (page: Page, prompt: string) => {
    // Go to create page
    await page.goto('/agents/create');
    
    // Fill form
    await page.fill('textarea[name="prompt"]', prompt);
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Should redirect to agent run detail page
    await page.waitForURL(/\/agents\/\d+/);
    
    // Should show success notification
    await page.waitForSelector('.notification-success', { timeout: 5000 });
  },

  /**
   * Verify agent run status updates
   */
  verifyStatusUpdates: async (page: Page, runId: string, expectedStatus: string) => {
    await page.goto(`/agents/${runId}`);
    
    // Wait for status to be displayed
    const statusElement = page.locator('[data-testid="agent-status"]');
    await statusElement.waitFor();
    
    // Check if status matches expected
    const currentStatus = await statusElement.textContent();
    return currentStatus?.toLowerCase().includes(expectedStatus.toLowerCase()) || false;
  },
};