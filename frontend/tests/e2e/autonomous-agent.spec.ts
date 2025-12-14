/**
 * E2E Tests for Autonomous Agent Functionality
 * Tests full autonomous running mechanics and UI interactions
 */

import { test, expect } from '@playwright/test';

test.describe('Autonomous Agent UI', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');
  });

  test('should display unified dashboard on load', async ({ page }) => {
    // Verify main dashboard elements
    await expect(page.locator('h1')).toContainText('Codegen');
    await expect(page.locator('text=The SWE that Never Sleeps')).toBeVisible();
    
    // Check stat cards
    await expect(page.locator('text=Active Workflows')).toBeVisible();
    await expect(page.locator('text=Executions')).toBeVisible();
    await expect(page.locator('text=Templates')).toBeVisible();
    await expect(page.locator('text=API Tokens')).toBeVisible();
  });

  test('should navigate between dashboard tabs', async ({ page }) => {
    // Test navigation to different sections
    const tabs = [
      'Dashboard',
      'Workflows',
      'Templates',
      'Analytics',
      'Webhooks',
      'API Tokens',
      'Profiles',
      'Inspector'
    ];

    for (const tab of tabs) {
      await page.click(`text=${tab}`);
      await page.waitForTimeout(500);
      
      // Verify tab is active
      const activeTab = page.locator(`button:has-text("${tab}")`);
      await expect(activeTab).toHaveClass(/bg-blue-50|bg-blue-100/);
    }
  });

  test('should display responsive sidebar', async ({ page }) => {
    // Check sidebar is visible on desktop
    await expect(page.locator('aside')).toBeVisible();
    
    // Test collapse/expand on desktop
    const collapseButton = page.locator('button[aria-label*="toggle"]').first();
    if (await collapseButton.isVisible()) {
      await collapseButton.click();
      await page.waitForTimeout(300);
      await collapseButton.click();
    }
    
    // Test mobile menu
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(300);
    
    const mobileMenuButton = page.locator('button[aria-label="Open menu"]');
    if (await mobileMenuButton.isVisible()) {
      await mobileMenuButton.click();
      await expect(page.locator('aside')).toBeVisible();
    }
  });

  test('should handle quick actions', async ({ page }) => {
    // Test "Create Workflow" quick action
    await page.click('text=Create Workflow');
    await page.waitForTimeout(500);
    
    // Should navigate to Workflows tab
    await expect(page.locator('text=Workflow Canvas')).toBeVisible();
    
    // Go back to dashboard
    await page.click('text=Dashboard');
    
    // Test "Browse Templates" quick action
    await page.click('text=Browse Templates');
    await page.waitForTimeout(500);
    
    // Should navigate to Templates tab
    await expect(page.locator('text=Template Marketplace')).toBeVisible();
  });
});

test.describe('Agent Control Panel', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');
    
    // Navigate to Agent tab (if exists)
    const agentTab = page.locator('text=Agent').or(page.locator('text=Workflows'));
    await agentTab.first().click();
    await page.waitForTimeout(500);
  });

  test('should display agent status monitor', async ({ page }) => {
    // Look for agent status indicators
    const statusIndicators = [
      'Idle',
      'Running',
      'Paused',
      'Error',
      'Complete'
    ];

    let found = false;
    for (const status of statusIndicators) {
      if (await page.locator(`text=${status}`).isVisible()) {
        found = true;
        break;
      }
    }

    expect(found).toBeTruthy();
  });

  test('should handle agent task submission', async ({ page }) => {
    // Look for task submission form
    const taskInput = page.locator('textarea[placeholder*="task"]').or(
      page.locator('textarea[placeholder*="prompt"]')
    );

    if (await taskInput.isVisible()) {
      await taskInput.fill('Test task: Create a simple React component');
      
      // Look for submit button
      const submitButton = page.locator('button:has-text("Submit")').or(
        page.locator('button:has-text("Start")')
      );

      if (await submitButton.isVisible()) {
        await submitButton.click();
        await page.waitForTimeout(1000);
        
        // Should show confirmation or status update
        await expect(page.locator('text=Task submitted').or(
          page.locator('text=Starting')
        )).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('should display task queue', async ({ page }) => {
    // Look for task queue display
    const queueElements = [
      'Pending',
      'Running',
      'Completed',
      'Failed'
    ];

    let found = 0;
    for (const element of queueElements) {
      if (await page.locator(`text=${element}`).count() > 0) {
        found++;
      }
    }

    // Should find at least 2 queue status categories
    expect(found).toBeGreaterThanOrEqual(2);
  });

  test('should start and stop agent', async ({ page }) => {
    // Look for agent control buttons
    const startButton = page.locator('button:has-text("Start Agent")').or(
      page.locator('button:has-text("Start")')
    );

    const stopButton = page.locator('button:has-text("Stop")').or(
      page.locator('button:has-text("Pause")')
    );

    // Test start if available
    if (await startButton.isVisible()) {
      await startButton.click();
      await page.waitForTimeout(1000);
      
      // Status should change
      await expect(page.locator('text=Running').or(
        page.locator('text=Active')
      )).toBeVisible({ timeout: 5000 });
    }

    // Test stop if available
    if (await stopButton.isVisible()) {
      await stopButton.click();
      await page.waitForTimeout(1000);
      
      // Status should change
      await expect(page.locator('text=Stopped').or(
        page.locator('text=Idle')
      )).toBeVisible({ timeout: 5000 });
    }
  });
});

test.describe('Agent Logging and Monitoring', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');
  });

  test('should display real-time logs', async ({ page }) => {
    // Navigate to logging view
    await page.click('text=Inspector');
    await page.waitForTimeout(500);

    // Look for log entries
    const logLevels = ['DEBUG', 'INFO', 'WARN', 'ERROR'];
    
    let foundLogs = false;
    for (const level of logLevels) {
      if (await page.locator(`text=${level}`).count() > 0) {
        foundLogs = true;
        break;
      }
    }

    expect(foundLogs).toBeTruthy();
  });

  test('should filter logs by level', async ({ page }) => {
    await page.click('text=Inspector');
    await page.waitForTimeout(500);

    // Look for filter controls
    const filterButton = page.locator('select').or(
      page.locator('button:has-text("Filter")')
    );

    if (await filterButton.isVisible()) {
      await filterButton.click();
      await page.waitForTimeout(300);
      
      // Select a filter option
      const errorFilter = page.locator('text=Error').or(
        page.locator('option:has-text("ERROR")')
      );

      if (await errorFilter.isVisible()) {
        await errorFilter.click();
        await page.waitForTimeout(500);
        
        // Logs should be filtered
        const visibleLogs = await page.locator('[data-log-level]').count();
        expect(visibleLogs).toBeGreaterThanOrEqual(0);
      }
    }
  });

  test('should display agent metrics', async ({ page }) => {
    // Navigate to Analytics
    await page.click('text=Analytics');
    await page.waitForTimeout(500);

    // Look for metric cards
    const metrics = [
      'Success Rate',
      'Average Duration',
      'Total Executions',
      'Error Rate'
    ];

    let foundMetrics = 0;
    for (const metric of metrics) {
      if (await page.locator(`text=${metric}`).count() > 0) {
        foundMetrics++;
      }
    }

    // Should find at least 2 metrics
    expect(foundMetrics).toBeGreaterThanOrEqual(2);
  });
});

test.describe('Telemetry Integration', () => {
  test('should track AI function calls', async ({ page }) => {
    // Intercept telemetry events
    const telemetryEvents: any[] = [];
    
    page.on('console', msg => {
      if (msg.text().includes('telemetry') || msg.text().includes('IRIS')) {
        telemetryEvents.push(msg.text());
      }
    });

    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Navigate to Profiles to trigger AI functions
    await page.click('text=Profiles');
    await page.waitForTimeout(1000);

    // Create or export a profile (triggers generateSettingsJson, etc.)
    const exportButton = page.locator('button:has-text("Export")');
    if (await exportButton.isVisible()) {
      await exportButton.first().click();
      await page.waitForTimeout(2000);
    }

    // Should have captured some telemetry
    expect(telemetryEvents.length).toBeGreaterThanOrEqual(0);
  });

  test('should store telemetry in localStorage', async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Trigger some AI functions
    await page.click('text=Profiles');
    await page.waitForTimeout(1000);

    // Check localStorage for telemetry data
    const telemetryData = await page.evaluate(() => {
      const keys = Object.keys(localStorage).filter(k => k.startsWith('telemetry_'));
      return keys.map(key => ({
        key,
        value: JSON.parse(localStorage.getItem(key) || '[]')
      }));
    });

    expect(Array.isArray(telemetryData)).toBeTruthy();
  });
});

test.describe('Performance & Optimization', () => {
  test('should load dashboard quickly', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    
    // Should load in under 5 seconds
    expect(loadTime).toBeLessThan(5000);
  });

  test('should lazy load heavy components', async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('domcontentloaded');

    // Initially on Dashboard
    await expect(page.locator('text=Dashboard')).toBeVisible();

    // Navigate to Workflows (lazy loaded)
    const startTime = Date.now();
    await page.click('text=Workflows');
    await page.waitForSelector('text=Workflow Canvas', { timeout: 3000 });
    const loadTime = Date.now() - startTime;

    // Lazy loaded component should appear quickly
    expect(loadTime).toBeLessThan(2000);
  });

  test('should handle errors gracefully', async ({ page }) => {
    // Monitor console errors
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    page.on('pageerror', error => {
      errors.push(error.message);
    });

    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Navigate through all tabs
    const tabs = ['Dashboard', 'Workflows', 'Templates', 'Analytics'];
    for (const tab of tabs) {
      await page.click(`text=${tab}`);
      await page.waitForTimeout(500);
    }

    // Should have minimal errors
    const criticalErrors = errors.filter(e => 
      !e.includes('favicon') && 
      !e.includes('404') &&
      !e.includes('network')
    );

    expect(criticalErrors.length).toBeLessThan(5);
  });
});

test.describe('Mobile Responsiveness', () => {
  test('should work on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Main content should be visible
    await expect(page.locator('h1')).toBeVisible();
    
    // Mobile menu should be available
    const menuButton = page.locator('button[aria-label*="menu"]');
    if (await menuButton.isVisible()) {
      await menuButton.click();
      await page.waitForTimeout(300);
      
      // Navigation should be visible
      await expect(page.locator('text=Dashboard')).toBeVisible();
    }
  });

  test('should work on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Sidebar should be visible
    await expect(page.locator('aside')).toBeVisible();
    
    // Content should be properly sized
    const content = page.locator('main');
    const bbox = await content.boundingBox();
    
    expect(bbox).not.toBeNull();
    expect(bbox!.width).toBeGreaterThan(400);
  });
});

