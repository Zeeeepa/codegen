import { FullConfig } from '@playwright/test';

/**
 * Global teardown for Playwright tests
 * Runs once after all tests complete
 */
async function globalTeardown(config: FullConfig) {
  console.log('🧹 Cleaning up after Playwright tests...');
  
  try {
    // Cleanup test data, reset databases, etc.
    console.log('📝 Cleaning up test data...');
    
    // You could add cleanup logic here:
    // - Reset test database
    // - Clear test files
    // - Reset external services
    
    console.log('✅ Global teardown completed successfully!');
    
  } catch (error) {
    console.error('❌ Global teardown failed:', error);
    // Don't throw here as it would fail the test run
  }
}

export default globalTeardown;