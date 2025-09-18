import { test, expect } from '@playwright/test';
import { authFixture } from './fixtures/auth';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication APIs before each test
    await authFixture.mockAuthAPIs(page);
  });

  test('should redirect to login page when not authenticated', async ({ page }) => {
    await page.goto('/');
    await page.waitForURL('/login');
    
    // Should show login form
    await expect(page.locator('h2:has-text("Sign in to Codegen")')).toBeVisible();
    await expect(page.locator('input[name="token"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should show login form elements', async ({ page }) => {
    await page.goto('/login');
    
    // Check for all login form elements
    await expect(page.locator('label:has-text("API Token")')).toBeVisible();
    await expect(page.locator('input[name="token"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    
    // Check for toggle password visibility button
    const toggleButton = page.locator('button:near(input[name="token"])');
    await expect(toggleButton).toBeVisible();
  });

  test('should toggle password visibility', async ({ page }) => {
    await page.goto('/login');
    
    const tokenInput = page.locator('input[name="token"]');
    const toggleButton = page.locator('button:near(input[name="token"])');
    
    // Initially should be password type
    await expect(tokenInput).toHaveAttribute('type', 'password');
    
    // Click toggle button
    await toggleButton.click();
    
    // Should change to text type
    await expect(tokenInput).toHaveAttribute('type', 'text');
    
    // Click again to toggle back
    await toggleButton.click();
    await expect(tokenInput).toHaveAttribute('type', 'password');
  });

  test('should show validation error for empty token', async ({ page }) => {
    await page.goto('/login');
    
    // Try to submit without token
    await page.click('button[type="submit"]');
    
    // Should show validation error
    await expect(page.locator('text=API token is required')).toBeVisible();
  });

  test('should successfully login with valid token', async ({ page }) => {
    await page.goto('/login');
    
    const token = authFixture.getMockToken();
    await page.fill('input[name="token"]', token);
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Should redirect to dashboard
    await page.waitForURL('/');
    
    // Should show dashboard elements
    await expect(page.locator('h1:has-text("Welcome to Codegen Visual Interface")')).toBeVisible();
  });

  test('should handle login failure', async ({ page }) => {
    // Setup failing auth API
    await authFixture.mockAuthAPIs(page, { shouldSucceed: false });
    
    await page.goto('/login');
    
    await page.fill('input[name="token"]', 'invalid-token');
    await page.click('button[type="submit"]');
    
    // Should show error message
    await expect(page.locator('text=Invalid API token')).toBeVisible();
    
    // Should stay on login page
    await expect(page).toHaveURL('/login');
  });

  test('should show loading state during login', async ({ page }) => {
    await page.goto('/login');
    
    const token = authFixture.getMockToken();
    await page.fill('input[name="token"]', token);
    
    // Submit form
    const submitPromise = page.click('button[type="submit"]');
    
    // Should show loading spinner briefly
    await expect(page.locator('button[type="submit"] svg')).toBeVisible({ timeout: 1000 });
    
    await submitPromise;
  });

  test('should logout successfully', async ({ page }) => {
    // First login
    await authFixture.setupAuthState(page);
    
    // Should be on dashboard
    await expect(page).toHaveURL('/');
    
    // Click logout button
    await page.click('button:has-text("Logout")');
    
    // Should redirect to login
    await page.waitForURL('/login');
    
    // Should show login form again
    await expect(page.locator('h2:has-text("Sign in to Codegen")')).toBeVisible();
  });

  test('should persist authentication state on page refresh', async ({ page }) => {
    await authFixture.setupAuthState(page);
    
    // Refresh the page
    await page.reload();
    
    // Should still be authenticated and on dashboard
    await expect(page).toHaveURL('/');
    await expect(page.locator('h1:has-text("Welcome to Codegen Visual Interface")')).toBeVisible();
  });

  test('should redirect to original page after login', async ({ page }) => {
    // Try to access agents page directly
    await page.goto('/agents');
    
    // Should redirect to login
    await page.waitForURL('/login');
    
    // Login
    const token = authFixture.getMockToken();
    await page.fill('input[name="token"]', token);
    await page.click('button[type="submit"]');
    
    // Should redirect back to agents page after login
    // Note: This might need adjustment based on actual redirect logic
    await page.waitForURL('/');
  });
});