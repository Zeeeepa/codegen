import { Page } from '@playwright/test';

export interface AuthFixture {
  loginWithToken: (token: string) => Promise<void>;
  logout: () => Promise<void>;
  isLoggedIn: () => Promise<boolean>;
  getMockToken: () => string;
}

/**
 * Authentication test fixture
 * Provides helper methods for login/logout in tests
 */
export const authFixture = {
  loginWithToken: async (page: Page, token: string) => {
    await page.goto('/login');
    await page.fill('input[name="token"]', token);
    await page.click('button[type="submit"]');
    
    // Wait for successful login and redirect
    await page.waitForURL('/');
    await page.waitForSelector('[data-testid="dashboard-header"]', { 
      timeout: 10000 
    });
  },

  logout: async (page: Page) => {
    // Click the logout button if it exists
    const logoutButton = page.locator('button:has-text("Logout")');
    if (await logoutButton.count() > 0) {
      await logoutButton.click();
    }
    
    // Wait for redirect to login page
    await page.waitForURL('/login');
  },

  isLoggedIn: async (page: Page): Promise<boolean> => {
    try {
      // Check if we're on a protected page and have authentication indicators
      await page.waitForSelector('[data-testid="dashboard-header"]', { 
        timeout: 2000 
      });
      return true;
    } catch {
      return false;
    }
  },

  getMockToken: (): string => {
    // Return a mock token for testing
    // In real tests, this might come from environment variables or test config
    return 'test_token_' + Date.now();
  },

  /**
   * Setup authentication state for tests that need it
   */
  setupAuthState: async (page: Page) => {
    const token = authFixture.getMockToken();
    await authFixture.loginWithToken(page, token);
    return token;
  },

  /**
   * Mock the authentication API endpoints
   */
  mockAuthAPIs: async (page: Page, options: {
    shouldSucceed?: boolean;
    userData?: any;
    orgData?: any;
  } = {}) => {
    const { shouldSucceed = true, userData, orgData } = options;

    // Mock the authentication endpoint
    await page.route('**/api/v1/users/me', async (route) => {
      if (shouldSucceed) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(userData || {
            id: 'test-user-1',
            email: 'test@example.com',
            name: 'Test User',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }),
        });
      } else {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Invalid token' }),
        });
      }
    });

    // Mock the organizations endpoint
    await page.route('**/api/v1/organizations', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([orgData || {
          id: 'test-org-1',
          name: 'Test Organization',
          slug: 'test-org',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }]),
      });
    });
  },
};