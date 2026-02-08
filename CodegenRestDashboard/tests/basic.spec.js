const { test, expect } = require('@playwright/test');

test.describe('Basic Dashboard Tests', () => {
  test('should load dashboard successfully', async ({ page }) => {
    // Mock API calls to avoid using real credentials
    await page.route('**/api/agent-runs', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [],
          total: 0,
          page: 1,
          size: 0,
          pages: 0
        })
      });
    });

    await page.route('**/api/health', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'ok', timestamp: new Date().toISOString() })
      });
    });

    // Navigate to the dashboard
    await page.goto('http://localhost:3001');

    // Wait for the app to load
    await page.waitForSelector('text=Codegen Dashboard', { timeout: 10000 });

    // Verify basic elements are present
    await expect(page.locator('text=Codegen Dashboard')).toBeVisible();
    await expect(page.locator('button').filter({ hasText: 'Active Runs' })).toBeVisible();
    await expect(page.locator('button').filter({ hasText: 'Past Runs' })).toBeVisible();
    await expect(page.locator('button').filter({ hasText: 'Templates' })).toBeVisible();
  });

  test('should show new run button', async ({ page }) => {
    await page.route('**/api/agent-runs', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [],
          total: 0,
          page: 1,
          size: 0,
          pages: 0
        })
      });
    });

    await page.goto('http://localhost:3001');
    await page.waitForSelector('text=Codegen Dashboard', { timeout: 10000 });

    // Check if New Run button exists
    const newRunButton = page.locator('button').filter({ hasText: 'New Run' });
    await expect(newRunButton).toBeVisible();
  });
});
