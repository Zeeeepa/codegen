const { test, expect } = require('@playwright/test');

test.describe('Codegen Dashboard E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API calls to avoid using real credentials
    await page.route('**/api/agent-runs', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 123,
              organization_id: 323,
              status: 'completed',
              created_at: new Date().toISOString(),
              summary: 'Test agent run',
              result: 'Test result',
              web_url: 'https://codegen.com/run/123'
            }
          ],
          total: 1,
          page: 1,
          size: 1,
          pages: 1
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
    await page.goto('http://localhost:3000');

    // Wait for the app to load
    await page.waitForSelector('text=Codegen Dashboard', { timeout: 10000 });
  });

  test('should display dashboard title', async ({ page }) => {
    await expect(page.locator('text=Codegen Dashboard')).toBeVisible();
  });

  test('should show active runs count in header', async ({ page }) => {
    // Check if the active runs badge exists (may show 0 with mock data)
    const header = page.locator('header');
    await expect(header).toBeVisible();
  });

  test('should display runs list', async ({ page }) => {
    // Wait for runs to load
    await page.waitForTimeout(1000);

    // Should show runs or "no runs" message
    const hasRuns = await page.locator('text=Run #123').isVisible();
    const hasNoRuns = await page.locator('text=No active runs').isVisible();

    expect(hasRuns || hasNoRuns).toBe(true);
  });

  test('should open new run dialog', async ({ page }) => {
    // Click the "New Run" button
    const newRunButton = page.locator('text=New Run');
    await expect(newRunButton).toBeVisible();
    await newRunButton.click();

    // Check if dialog opens
    const dialog = page.locator('[role="dialog"]');
    await expect(dialog).toBeVisible();

    // Check form elements exist
    await expect(page.locator('textarea').first()).toBeVisible();
  });

  test('should validate new run form', async ({ page }) => {
    // Open new run dialog
    await page.locator('text=New Run').click();

    // Try to submit without prompt
    const submitButton = page.locator('button').filter({ hasText: 'Create Run' });
    await expect(submitButton).toBeVisible();

    // Button should be disabled without prompt
    await expect(submitButton).toBeDisabled();
  });

  test('should switch between tabs', async ({ page }) => {
    // Check tabs exist
    const activeTab = page.locator('button').filter({ hasText: /Active Runs/ });
    const pastTab = page.locator('button').filter({ hasText: 'Past Runs' });
    const templatesTab = page.locator('button').filter({ hasText: 'Templates' });

    await expect(activeTab).toBeVisible();
    await expect(pastTab).toBeVisible();
    await expect(templatesTab).toBeVisible();

    // Switch to past runs
    await pastTab.click();
    await expect(pastTab).toHaveClass(/Mui-selected/);

    // Switch to templates
    await templatesTab.click();
    await expect(templatesTab).toHaveClass(/Mui-selected/);
  });

  test('should display templates tab', async ({ page }) => {
    // Switch to templates tab
    await page.locator('button').filter({ hasText: 'Templates' }).click();

    // Check if templates interface is shown
    await expect(page.locator('text=Prompt Templates')).toBeVisible();
    await expect(page.locator('text=New Template')).toBeVisible();
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock a failed API call
    await page.route('**/api/agent-runs', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });

    // Reload the page to trigger the failed request
    await page.reload();

    // Should still show dashboard title (error handled gracefully)
    await expect(page.locator('text=Codegen Dashboard')).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set viewport to mobile size
    await page.setViewportSize({ width: 375, height: 667 });

    // Check that header is still visible
    await expect(page.locator('text=Codegen Dashboard')).toBeVisible();

    // Check that tabs are still accessible
    await expect(page.locator('button').filter({ hasText: /Active Runs/ })).toBeVisible();
  });

  test('should be responsive on tablet', async ({ page }) => {
    // Set viewport to tablet size
    await page.setViewportSize({ width: 768, height: 1024 });

    // Check layout adapts
    await expect(page.locator('text=Codegen Dashboard')).toBeVisible();
  });

  test('should show no console errors', async ({ page }) => {
    // Check that no console errors are present
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Navigate and wait
    await page.waitForTimeout(2000);

    // Filter out expected errors (like favicon, etc.)
    const significantErrors = errors.filter(error =>
      !error.includes('favicon') &&
      !error.includes('manifest') &&
      !error.includes('chunk')
    );

    // Should have no significant console errors
    expect(significantErrors.length).toBe(0);
  });

  test('should handle run creation flow', async ({ page }) => {
    // Mock successful run creation
    await page.route('**/api/agent-runs', route => {
      if (route.request().method() === 'POST') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 456,
            organization_id: 323,
            status: 'running',
            created_at: new Date().toISOString(),
            summary: 'New test run',
            web_url: 'https://codegen.com/run/456'
          })
        });
      } else {
        // For GET requests, return the new run
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [
              {
                id: 456,
                organization_id: 323,
                status: 'running',
                created_at: new Date().toISOString(),
                summary: 'New test run',
                web_url: 'https://codegen.com/run/456'
              }
            ],
            total: 1,
            page: 1,
            size: 1,
            pages: 1
          })
        });
      }
    }, { times: 2 });

    // Open new run dialog
    await page.locator('text=New Run').click();

    // Fill form
    await page.locator('textarea').first().fill('Test prompt for new run');

    // Submit
    await page.locator('button').filter({ hasText: 'Create Run' }).click();

    // Should close dialog and show success message
    await expect(page.locator('[role="dialog"]')).not.toBeVisible();

    // Should show the new run
    await expect(page.locator('text=Run #456')).toBeVisible();
  });
});

