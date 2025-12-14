/**
 * E2E Tests: Token Management
 * Tests for API token creation, management, and security
 */

import { test, expect } from '@playwright/test';

test.describe('Token Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings/tokens');
  });

  test('should display token management page', async ({ page }) => {
    await expect(page.locator('h2:has-text("API Tokens")')).toBeVisible();
  });

  test('should list existing tokens', async ({ page }) => {
    // Wait for tokens to load
    await page.waitForSelector('[data-testid="token-list"]', { timeout: 5000 });
    
    const tokenCount = await page.locator('[data-testid="token-item"]').count();
    expect(tokenCount).toBeGreaterThanOrEqual(0);
  });

  test('should create new API token', async ({ page }) => {
    // Click create token button
    await page.click('button:has-text("Create Token")');
    
    // Fill in token details
    await page.fill('input[name="name"]', `E2E Test Token ${Date.now()}`);
    
    // Select scopes
    await page.check('input[value="workflows:read"]');
    await page.check('input[value="executions:read"]');
    
    // Create token
    await page.click('button:has-text("Create Token")');
    
    // Verify token created successfully
    await expect(page.locator('text=Token Created Successfully')).toBeVisible({
      timeout: 5000,
    });
    
    // Verify plaintext token is shown
    await expect(page.locator('code:has-text("sk-")')).toBeVisible();
  });

  test('should show token only once on creation', async ({ page }) => {
    // Create token
    await page.click('button:has-text("Create Token")');
    await page.fill('input[name="name"]', `Temp Token ${Date.now()}`);
    await page.check('input[value="workflows:read"]');
    await page.click('button:has-text("Create Token")');
    
    // Copy plaintext token
    const plaintextToken = await page.locator('code:has-text("sk-")').textContent();
    expect(plaintextToken).toContain('sk-');
    
    // Dismiss success message
    await page.click('button:has-text("I\'ve copied my token")');
    
    // Verify plaintext is no longer visible
    await expect(page.locator('code:has-text("sk-")')).not.toBeVisible();
  });

  test('should toggle token visibility', async ({ page }) => {
    // Find first token
    const firstToken = page.locator('[data-testid="token-item"]').first();
    
    // Initially should be masked
    await expect(firstToken.locator('text=/••••/')).toBeVisible();
    
    // Click show button
    await firstToken.locator('button[title="Show"]').click();
    
    // Should show full hash
    await expect(firstToken.locator('code')).toBeVisible();
    
    // Click hide button
    await firstToken.locator('button[title="Hide"]').click();
    
    // Should be masked again
    await expect(firstToken.locator('text=/••••/')).toBeVisible();
  });

  test('should copy token to clipboard', async ({ page }) => {
    const firstToken = page.locator('[data-testid="token-item"]').first();
    
    // Click copy button
    await firstToken.locator('button[title="Copy to clipboard"]').click();
    
    // Verify toast message
    await expect(page.locator('text=Copied to clipboard')).toBeVisible({ timeout: 2000 });
  });

  test('should display expiration warnings', async ({ page }) => {
    // Check for expiring soon badge
    const expiringSoon = page.locator('text=Expiring Soon');
    if (await expiringSoon.count() > 0) {
      await expect(expiringSoon.first()).toBeVisible();
    }
    
    // Check for expired badge
    const expired = page.locator('text=Expired');
    if (await expired.count() > 0) {
      await expect(expired.first()).toBeVisible();
    }
  });

  test('should revoke active token', async ({ page }) => {
    // Find active token
    const activeToken = page.locator('[data-testid="token-item"]')
      .filter({ hasNot: page.locator('text=Revoked') })
      .first();
    
    if (await activeToken.count() === 0) {
      test.skip();
    }
    
    // Click revoke button
    await activeToken.locator('button[title="Revoke token"]').click();
    
    // Confirm revocation
    page.on('dialog', dialog => dialog.accept());
    
    // Verify revoked
    await expect(page.locator('text=Token revoked')).toBeVisible({ timeout: 3000 });
  });

  test('should delete token', async ({ page }) => {
    // Count initial tokens
    const initialCount = await page.locator('[data-testid="token-item"]').count();
    
    if (initialCount === 0) {
      test.skip();
    }
    
    // Delete last token
    const lastToken = page.locator('[data-testid="token-item"]').last();
    await lastToken.locator('button[title="Delete token"]').click();
    
    // Confirm deletion
    page.on('dialog', dialog => dialog.accept());
    
    // Verify deleted
    await expect(page.locator('text=Token deleted')).toBeVisible({ timeout: 3000 });
    
    // Verify count decreased
    const newCount = await page.locator('[data-testid="token-item"]').count();
    expect(newCount).toBe(initialCount - 1);
  });

  test('should validate token creation form', async ({ page }) => {
    // Click create without filling form
    await page.click('button:has-text("Create Token")');
    await page.click('button:has-text("Create Token")');
    
    // Should show validation error
    await expect(page.locator('text=/name and at least one scope/i')).toBeVisible({
      timeout: 2000,
    });
  });

  test('should display token scopes', async ({ page }) => {
    const firstToken = page.locator('[data-testid="token-item"]').first();
    
    // Should show scope badges
    await expect(firstToken.locator('[class*="scope"]')).toHaveCount({ min: 1 });
  });

  test('should show token metadata', async ({ page }) => {
    const firstToken = page.locator('[data-testid="token-item"]').first();
    
    // Should show created date
    await expect(firstToken.locator('text=/Created/')).toBeVisible();
    
    // Should show last used (if available)
    const lastUsed = firstToken.locator('text=/Last used/');
    if (await lastUsed.count() > 0) {
      await expect(lastUsed).toBeVisible();
    }
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route('**/api/api-keys', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Internal server error' }),
      });
    });
    
    await page.reload();
    
    // Should show error message
    await expect(page.locator('text=/failed/i')).toBeVisible({ timeout: 5000 });
  });
});

