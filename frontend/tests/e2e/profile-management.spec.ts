/**
 * E2E Tests for Profile Management - Feature 1
 * 
 * Test Scenarios:
 * 1. Create profile with valid data
 * 2. Verify profile appears in list
 * 3. Edit profile and verify changes
 * 4. Set profile as active
 * 5. Delete profile
 * 6. Verify localStorage persistence across reload
 * 7. Error handling (empty name, validation)
 */

import { test, expect, Page } from '@playwright/test';

const BASE_URL = 'http://localhost:4173';

// Helper to clear localStorage and set up mock credentials
async function clearStorage(page: Page) {
  await page.evaluate(() => {
    localStorage.clear();
    
    // Set mock credentials to bypass the welcome screen
    const mockStore = {
      state: {
        isValidated: true,
        apiToken: 'test-api-token',
        organizationId: 'test-org-id',
        profiles: [],
        activeProfileId: null,
      },
      version: 0,
    };
    
    localStorage.setItem('codegen-app-store', JSON.stringify(mockStore));
  });
}

// Helper to wait for app to be ready
async function waitForApp(page: Page) {
  await page.waitForSelector('[data-testid="profiles-tab"]', { timeout: 10000 });
}

test.describe('Profile Management - Feature 1 E2E', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
    await clearStorage(page);
    await page.reload();
    await waitForApp(page);
  });

  test('1. Navigate to Profiles tab', async ({ page }) => {
    // Click Profiles tab
    await page.click('[data-testid="profiles-tab"]');
    
    // Verify we're on the profiles page
    await expect(page.locator('text=Agent Profiles')).toBeVisible();
    await expect(page.locator('text=No profiles yet')).toBeVisible();
  });

  test('2. Create profile with valid data', async ({ page }) => {
    // Navigate to Profiles
    await page.click('[data-testid="profiles-tab"]');
    
    // Click create button
    await page.click('[data-testid="create-profile-button"]');
    
    // Verify form is visible
    await expect(page.locator('[data-testid="profile-form"]')).toBeVisible();
    await expect(page.locator('text=Create New Profile')).toBeVisible();
    
    // Fill in profile data
    await page.fill('[data-testid="profile-name-input"]', 'Test Researcher');
    await page.fill('[data-testid="profile-description-input"]', 'A test profile for research tasks');
    await page.selectOption('[data-testid="profile-role-select"]', 'researcher');
    
    // Submit
    await page.click('[data-testid="save-profile-button"]');
    
    // Verify profile appears in list
    await expect(page.locator('text=Test Researcher')).toBeVisible();
    await expect(page.locator('text=A test profile for research tasks')).toBeVisible();
    await expect(page.locator('text=Research Specialist')).toBeVisible();
    
    // Verify form is closed
    await expect(page.locator('[data-testid="profile-form"]')).not.toBeVisible();
  });

  test('3. Create profile with custom role', async ({ page }) => {
    await page.click('[data-testid="profiles-tab"]');
    await page.click('[data-testid="create-profile-button"]');
    
    await page.fill('[data-testid="profile-name-input"]', 'Product Manager');
    await page.fill('[data-testid="profile-description-input"]', 'Manages product roadmap');
    await page.selectOption('[data-testid="profile-role-select"]', 'custom');
    
    // Wait for custom role input to appear
    await expect(page.locator('[data-testid="profile-custom-role-input"]')).toBeVisible();
    await page.fill('[data-testid="profile-custom-role-input"]', 'Product Manager');
    
    await page.click('[data-testid="save-profile-button"]');
    
    // Verify profile name appears (use more specific selector to avoid matching role text)
    await expect(page.locator('[data-testid^="profile-name-"]:has-text("Product Manager")')).toBeVisible();
    await expect(page.locator('text=Custom Role - Product Manager')).toBeVisible();
  });

  test('4. Edit existing profile', async ({ page }) => {
    // Create a profile first
    await page.click('[data-testid="profiles-tab"]');
    await page.click('[data-testid="create-profile-button"]');
    await page.fill('[data-testid="profile-name-input"]', 'Original Name');
    await page.fill('[data-testid="profile-description-input"]', 'Original description');
    await page.click('[data-testid="save-profile-button"]');
    
    // Get the profile ID from the DOM
    const profileItem = page.locator('[data-testid^="profile-item-"]').first();
    const profileId = await profileItem.getAttribute('data-testid');
    const id = profileId?.replace('profile-item-', '');
    
    // Click edit button
    await page.click(`[data-testid="edit-profile-${id}"]`);
    
    // Verify form shows with existing data
    await expect(page.locator('[data-testid="profile-form"]')).toBeVisible();
    await expect(page.locator('text=Edit Profile')).toBeVisible();
    await expect(page.locator('[data-testid="profile-name-input"]')).toHaveValue('Original Name');
    
    // Update the profile
    await page.fill('[data-testid="profile-name-input"]', 'Updated Name');
    await page.fill('[data-testid="profile-description-input"]', 'Updated description');
    await page.selectOption('[data-testid="profile-role-select"]', 'developer');
    
    await page.click('[data-testid="save-profile-button"]');
    
    // Verify changes
    await expect(page.locator('text=Updated Name')).toBeVisible();
    await expect(page.locator('text=Updated description')).toBeVisible();
    await expect(page.locator('text=Software Developer')).toBeVisible();
    await expect(page.locator('text=Original Name')).not.toBeVisible();
  });

  test('5. Set profile as active', async ({ page }) => {
    // Create a profile
    await page.click('[data-testid="profiles-tab"]');
    await page.click('[data-testid="create-profile-button"]');
    await page.fill('[data-testid="profile-name-input"]', 'API Manager');
    await page.click('[data-testid="save-profile-button"]');
    
    // Get profile ID
    const profileItem = page.locator('[data-testid^="profile-item-"]').first();
    const profileId = await profileItem.getAttribute('data-testid');
    const id = profileId?.replace('profile-item-', '');
    
    // Activate the profile
    await page.click(`[data-testid="activate-profile-${id}"]`);
    
    // Verify "Active" badge appears within the profile item (use specific selector)
    const activeProfileItem = page.locator(`[data-testid="profile-item-${id}"]`);
    await expect(activeProfileItem.locator('text=Active')).toBeVisible();
    
    // Verify activate button is gone (profile is already active)
    await expect(page.locator(`[data-testid="activate-profile-${id}"]`)).not.toBeVisible();
  });

  test('6. Delete profile', async ({ page }) => {
    // Create a profile
    await page.click('[data-testid="profiles-tab"]');
    await page.click('[data-testid="create-profile-button"]');
    await page.fill('[data-testid="profile-name-input"]', 'To Be Deleted');
    await page.click('[data-testid="save-profile-button"]');
    
    await expect(page.locator('text=To Be Deleted')).toBeVisible();
    
    // Get profile ID
    const profileItem = page.locator('[data-testid^="profile-item-"]').first();
    const profileId = await profileItem?.getAttribute('data-testid');
    const id = profileId?.replace('profile-item-', '');
    
    // Handle confirmation dialog
    page.on('dialog', dialog => dialog.accept());
    
    // Delete the profile
    await page.click(`[data-testid="delete-profile-${id}"]`);
    
    // Verify profile is gone
    await expect(page.locator('text=To Be Deleted')).not.toBeVisible();
    await expect(page.locator('text=No profiles yet')).toBeVisible();
  });

  test('7. Validate empty name error', async ({ page }) => {
    await page.click('[data-testid="profiles-tab"]');
    await page.click('[data-testid="create-profile-button"]');
    
    // Try to submit with empty name
    await page.fill('[data-testid="profile-name-input"]', '');
    await page.click('[data-testid="save-profile-button"]');
    
    // Verify error message
    await expect(page.locator('[data-testid="form-error"]')).toBeVisible();
    await expect(page.locator('text=Name is required')).toBeVisible();
    
    // Verify form is still open
    await expect(page.locator('[data-testid="profile-form"]')).toBeVisible();
  });

  test('8. Cancel form closes without saving', async ({ page }) => {
    await page.click('[data-testid="profiles-tab"]');
    await page.click('[data-testid="create-profile-button"]');
    
    await page.fill('[data-testid="profile-name-input"]', 'Will Not Save');
    await page.fill('[data-testid="profile-description-input"]', 'This should not persist');
    
    // Click cancel
    await page.click('[data-testid="cancel-profile-button"]');
    
    // Verify form is closed
    await expect(page.locator('[data-testid="profile-form"]')).not.toBeVisible();
    
    // Verify profile was not created
    await expect(page.locator('text=Will Not Save')).not.toBeVisible();
    await expect(page.locator('text=No profiles yet')).toBeVisible();
  });

  test('9. localStorage persistence across reload', async ({ page }) => {
    // Create two profiles
    await page.click('[data-testid="profiles-tab"]');
    
    // Profile 1
    await page.click('[data-testid="create-profile-button"]');
    await page.fill('[data-testid="profile-name-input"]', 'Persistent Profile 1');
    await page.fill('[data-testid="profile-description-input"]', 'First test profile');
    await page.selectOption('[data-testid="profile-role-select"]', 'researcher');
    await page.click('[data-testid="save-profile-button"]');
    
    // Profile 2
    await page.click('[data-testid="create-profile-button"]');
    await page.fill('[data-testid="profile-name-input"]', 'Persistent Profile 2');
    await page.fill('[data-testid="profile-description-input"]', 'Second test profile');
    await page.selectOption('[data-testid="profile-role-select"]', 'developer');
    await page.click('[data-testid="save-profile-button"]');
    
    // Set Profile 2 as active
    const profileItems = page.locator('[data-testid^="profile-item-"]');
    const secondProfile = profileItems.nth(1);
    const secondProfileId = (await secondProfile.getAttribute('data-testid'))?.replace('profile-item-', '');
    await page.click(`[data-testid="activate-profile-${secondProfileId}"]`);
    
    // Verify both profiles visible and Profile 2 is active
    await expect(page.locator('text=Persistent Profile 1')).toBeVisible();
    await expect(page.locator('text=Persistent Profile 2')).toBeVisible();
    // Check for Active badge within profiles list only (not in nav bar)
    const activeBadges = page.locator('[data-testid="profiles-list"]').locator('text=Active');
    await expect(activeBadges).toHaveCount(1);
    
    // Reload page
    await page.reload();
    await waitForApp(page);
    await page.click('[data-testid="profiles-tab"]');
    
    // Verify profiles still exist
    await expect(page.locator('text=Persistent Profile 1')).toBeVisible();
    await expect(page.locator('text=Persistent Profile 2')).toBeVisible();
    await expect(page.locator('text=Research Specialist')).toBeVisible();
    await expect(page.locator('text=Software Developer')).toBeVisible();
    
    // Verify Profile 2 is still active (use specific selector within profiles list)
    const profilesList = page.locator('[data-testid="profiles-list"]');
    await expect(profilesList.locator('text=Active')).toBeVisible();
    const activeProfile = page.locator('[data-testid^="profile-item-"]:has-text("Active")');
    await expect(activeProfile.locator('[data-testid^="profile-name-"]')).toHaveText('Persistent Profile 2');
  });

  test('10. Multiple profiles management', async ({ page }) => {
    await page.click('[data-testid="profiles-tab"]');
    
    // Create 5 different profiles
    const profiles = [
      { name: 'Researcher', role: 'researcher', description: 'Research tasks' },
      { name: 'Developer', role: 'developer', description: 'Development tasks' },
      { name: 'QA Engineer', role: 'qa-engineer', description: 'Testing tasks' },
      { name: 'DevOps', role: 'devops', description: 'Infrastructure tasks' },
      { name: 'Security', role: 'security', description: 'Security tasks' }
    ];
    
    for (const profile of profiles) {
      await page.click('[data-testid="create-profile-button"]');
      await page.fill('[data-testid="profile-name-input"]', profile.name);
      await page.fill('[data-testid="profile-description-input"]', profile.description);
      await page.selectOption('[data-testid="profile-role-select"]', profile.role);
      await page.click('[data-testid="save-profile-button"]');
    }
    
    // Verify all 5 profiles visible (use specific selectors to avoid matching role descriptions)
    await expect(page.locator('[data-testid^="profile-name-"]:has-text("Researcher")')).toBeVisible();
    await expect(page.locator('[data-testid^="profile-name-"]:has-text("Developer")')).toBeVisible();
    await expect(page.locator('[data-testid^="profile-name-"]:has-text("QA Engineer")')).toBeVisible();
    await expect(page.locator('[data-testid^="profile-name-"]:has-text("DevOps")')).toBeVisible();
    await expect(page.locator('[data-testid^="profile-name-"]:has-text("Security")')).toBeVisible();
    
    // Verify no empty state
    await expect(page.locator('text=No profiles yet')).not.toBeVisible();
    
    // Count profile items
    const profileCount = await page.locator('[data-testid^="profile-item-"]').count();
    expect(profileCount).toBe(5);
  });
  
  test('11. Creation timestamp is displayed', async ({ page }) => {
    await page.click('[data-testid="profiles-tab"]');
    await page.click('[data-testid="create-profile-button"]');
    await page.fill('[data-testid="profile-name-input"]', 'Timestamped Profile');
    await page.click('[data-testid="save-profile-button"]');
    
    // Verify timestamp is shown
    await expect(page.locator('text=Created:')).toBeVisible();
    
    // Verify it's a valid date format (contains numbers and slashes or dashes)
    const timestampText = await page.locator('text=Created:').textContent();
    expect(timestampText).toMatch(/Created:.*\d/);
  });

  test('12. Long names and descriptions are handled', async ({ page }) => {
    await page.click('[data-testid="profiles-tab"]');
    await page.click('[data-testid="create-profile-button"]');
    
    const longName = 'A'.repeat(50); // Max length
    const longDescription = 'B'.repeat(500); // Max length
    
    await page.fill('[data-testid="profile-name-input"]', longName);
    await page.fill('[data-testid="profile-description-input"]', longDescription);
    await page.click('[data-testid="save-profile-button"]');
    
    // Verify profile created successfully
    await expect(page.locator(`text=${longName.substring(0, 20)}`)).toBeVisible();
  });
});
