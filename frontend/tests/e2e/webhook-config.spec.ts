/**
 * E2E Tests: Webhook Configuration
 * Tests for webhook creation, management, and real-time events
 */

import { test, expect } from '@playwright/test';

test.describe('Webhook Configuration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings/webhooks');
  });

  test('should display webhook configuration page', async ({ page }) => {
    await expect(page.locator('h2:has-text("Webhooks")')).toBeVisible();
  });

  test('should list existing webhooks', async ({ page }) => {
    await page.waitForSelector('[data-testid="webhook-list"]', { timeout: 5000 });
    const webhookCount = await page.locator('[data-testid="webhook-item"]').count();
    expect(webhookCount).toBeGreaterThanOrEqual(0);
  });

  test('should create new webhook', async ({ page }) => {
    // Click create webhook
    await page.click('button:has-text("Create Webhook")');
    
    // Fill webhook URL
    await page.fill('input[name="url"]', 'https://example.com/webhook');
    
    // Select events
    await page.check('input[value="workflow:created"]');
    await page.check('input[value="execution:completed"]');
    
    // Create webhook
    await page.click('button:has-text("Create Webhook")');
    
    // Verify success
    await expect(page.locator('text=Webhook created')).toBeVisible({ timeout: 5000 });
  });

  test('should validate webhook URL', async ({ page }) => {
    await page.click('button:has-text("Create Webhook")');
    
    // Try invalid URL
    await page.fill('input[name="url"]', 'not-a-valid-url');
    await page.check('input[value="workflow:created"]');
    await page.click('button:has-text("Create Webhook")');
    
    // Should show validation error
    await expect(page.locator('text=/valid URL/i')).toBeVisible({ timeout: 2000 });
  });

  test('should require at least one event', async ({ page }) => {
    await page.click('button:has-text("Create Webhook")');
    await page.fill('input[name="url"]', 'https://example.com/webhook');
    
    // Try to create without selecting events
    await page.click('button:has-text("Create Webhook")');
    
    // Should show validation error
    await expect(page.locator('text=/at least one event/i')).toBeVisible({
      timeout: 2000,
    });
  });

  test('should add custom headers', async ({ page }) => {
    await page.click('button:has-text("Create Webhook")');
    
    // Add custom header
    await page.fill('input[placeholder*="Header name"]', 'Authorization');
    await page.fill('input[placeholder*="Header value"]', 'Bearer token123');
    await page.click('button:has-text("Add")');
    
    // Verify header added
    await expect(page.locator('text=Authorization: Bearer token123')).toBeVisible();
  });

  test('should remove custom headers', async ({ page }) => {
    await page.click('button:has-text("Create Webhook")');
    
    // Add header
    await page.fill('input[placeholder*="Header name"]', 'X-Custom');
    await page.fill('input[placeholder*="Header value"]', 'value');
    await page.click('button:has-text("Add")');
    
    // Remove header
    await page.click('button[title*="Remove"]:near(:text("X-Custom"))');
    
    // Verify removed
    await expect(page.locator('text=X-Custom')).not.toBeVisible();
  });

  test('should toggle webhook status', async ({ page }) => {
    const firstWebhook = page.locator('[data-testid="webhook-item"]').first();
    
    if (await firstWebhook.count() === 0) {
      test.skip();
    }
    
    // Toggle webhook
    await firstWebhook.locator('button[title*="Disable"], button[title*="Enable"]').click();
    
    // Verify toggle message
    await expect(page.locator('text=/enabled|disabled/i')).toBeVisible({
      timeout: 3000,
    });
  });

  test('should test webhook endpoint', async ({ page }) => {
    const firstWebhook = page.locator('[data-testid="webhook-item"]').first();
    
    if (await firstWebhook.count() === 0) {
      test.skip();
    }
    
    // Test webhook
    await firstWebhook.locator('button[title="Test webhook"]').click();
    
    // Wait for test result (may succeed or fail depending on endpoint)
    await expect(
      page.locator('text=/test successful|test failed/i')
    ).toBeVisible({ timeout: 5000 });
  });

  test('should delete webhook', async ({ page }) => {
    const initialCount = await page.locator('[data-testid="webhook-item"]').count();
    
    if (initialCount === 0) {
      test.skip();
    }
    
    // Delete webhook
    const lastWebhook = page.locator('[data-testid="webhook-item"]').last();
    await lastWebhook.locator('button[title="Delete webhook"]').click();
    
    // Confirm deletion
    page.on('dialog', dialog => dialog.accept());
    
    // Verify deleted
    await expect(page.locator('text=Webhook deleted')).toBeVisible({ timeout: 3000 });
  });

  test('should display webhook events', async ({ page }) => {
    const firstWebhook = page.locator('[data-testid="webhook-item"]').first();
    
    if (await firstWebhook.count() === 0) {
      test.skip();
    }
    
    // Should show event badges
    await expect(firstWebhook.locator('[class*="event"]')).toHaveCount({ min: 1 });
  });

  test('should show webhook metadata', async ({ page }) => {
    const firstWebhook = page.locator('[data-testid="webhook-item"]').first();
    
    if (await firstWebhook.count() === 0) {
      test.skip();
    }
    
    // Should show created date
    await expect(firstWebhook.locator('text=/Created/')).toBeVisible();
    
    // Should show URL
    await expect(firstWebhook.locator('code')).toBeVisible();
  });

  test('should display payload format info', async ({ page }) => {
    // Should show info box with payload format
    await expect(page.locator('text=Webhook Payload Format')).toBeVisible();
    await expect(page.locator('pre')).toBeVisible();
  });

  test('should handle webhook creation errors', async ({ page }) => {
    // Mock API error
    await page.route('**/api/webhooks', route => {
      if (route.request().method() === 'POST') {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ error: 'Failed to create webhook' }),
        });
      } else {
        route.continue();
      }
    });
    
    // Try to create webhook
    await page.click('button:has-text("Create Webhook")');
    await page.fill('input[name="url"]', 'https://example.com/webhook');
    await page.check('input[value="workflow:created"]');
    await page.click('button:has-text("Create Webhook")');
    
    // Should show error
    await expect(page.locator('text=/failed/i')).toBeVisible({ timeout: 5000 });
  });

  test('should cancel webhook creation', async ({ page }) => {
    await page.click('button:has-text("Create Webhook")');
    await page.fill('input[name="url"]', 'https://example.com/webhook');
    
    // Cancel
    await page.click('button:has-text("Cancel")');
    
    // Form should be hidden
    await expect(page.locator('input[name="url"]')).not.toBeVisible();
  });
});

