/**
 * E2E Tests: Database Integration
 * Tests for database API service and workflow persistence
 */

import { test, expect } from '@playwright/test';

test.describe('Database Integration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should connect to database API', async ({ page }) => {
    // Check if database service is available
    const apiHealthCheck = await page.evaluate(async () => {
      try {
        const { databaseApi } = await import('../src/services/databaseApi');
        return { available: true };
      } catch (error) {
        return { available: false, error: error.message };
      }
    });

    expect(apiHealthCheck.available).toBe(true);
  });

  test('should load workflows from database', async ({ page }) => {
    await page.goto('/workflows');
    
    // Wait for workflows to load
    await page.waitForSelector('[data-testid="workflow-list"]', { timeout: 5000 });
    
    // Check if workflows are displayed
    const workflowCount = await page.locator('[data-testid="workflow-item"]').count();
    expect(workflowCount).toBeGreaterThanOrEqual(0);
  });

  test('should create workflow in database', async ({ page }) => {
    await page.goto('/workflows');
    
    // Click create workflow button
    await page.click('button:has-text("Create Workflow")');
    
    // Fill in workflow details
    await page.fill('input[name="name"]', `Test Workflow ${Date.now()}`);
    await page.fill('textarea[name="description"]', 'E2E test workflow');
    
    // Save workflow
    await page.click('button:has-text("Save")');
    
    // Wait for success message
    await expect(page.locator('text=Workflow created')).toBeVisible({ timeout: 5000 });
  });

  test('should sync workflows from database on load', async ({ page }) => {
    // Navigate to workflows page
    await page.goto('/workflows');
    
    // Check if sync occurred (loading indicator should appear then disappear)
    const loadingIndicator = page.locator('[data-testid="loading"]');
    
    // Wait for loading to start
    await loadingIndicator.waitFor({ state: 'visible', timeout: 1000 }).catch(() => {});
    
    // Wait for loading to complete
    await loadingIndicator.waitFor({ state: 'hidden', timeout: 5000 }).catch(() => {});
    
    // Verify workflows are displayed
    const workflowList = page.locator('[data-testid="workflow-list"]');
    await expect(workflowList).toBeVisible();
  });

  test('should migrate localStorage to database', async ({ page }) => {
    // Add test data to localStorage
    await page.evaluate(() => {
      const testWorkflow = {
        id: 'test-123',
        name: 'Migration Test Workflow',
        description: 'Test workflow for migration',
        definition: {
          nodes: [],
          edges: [],
        },
      };
      
      localStorage.setItem(
        'codegen-app-store',
        JSON.stringify({ savedWorkflows: [testWorkflow] })
      );
      
      // Remove migration flag to trigger migration
      localStorage.removeItem('codegen-migrated');
    });
    
    // Reload page to trigger migration
    await page.reload();
    
    // Wait for migration toast
    await expect(page.locator('text=/migrated/i')).toBeVisible({ timeout: 5000 });
  });

  test('should handle database connection errors gracefully', async ({ page }) => {
    // Mock network error
    await page.route('**/api/**', route => {
      route.abort('failed');
    });
    
    await page.goto('/workflows');
    
    // Should show error message
    await expect(page.locator('text=/failed/i')).toBeVisible({ timeout: 5000 });
  });

  test('should persist workflow changes to database', async ({ page }) => {
    await page.goto('/workflows');
    
    // Select first workflow
    await page.click('[data-testid="workflow-item"]:first-child');
    
    // Edit workflow
    await page.click('button:has-text("Edit")');
    await page.fill('input[name="name"]', `Updated ${Date.now()}`);
    
    // Save changes
    await page.click('button:has-text("Save")');
    
    // Verify save success
    await expect(page.locator('text=/saved/i')).toBeVisible({ timeout: 5000 });
  });

  test('should load workflow definitions correctly', async ({ page }) => {
    await page.goto('/workflows');
    
    // Select a workflow
    await page.click('[data-testid="workflow-item"]:first-child');
    
    // Open workflow canvas
    await page.click('button:has-text("Open")');
    
    // Verify workflow is loaded in canvas
    await expect(page.locator('[data-testid="workflow-canvas"]')).toBeVisible();
  });
});

