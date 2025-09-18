import { chromium, FullConfig } from '@playwright/test';
import path from 'path';

/**
 * Global setup for Playwright tests
 * Runs once before all tests
 */
async function globalSetup(config: FullConfig) {
  console.log('🚀 Setting up Playwright tests...');
  
  // Create a browser instance for setup
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // Wait for the server to be ready
    const baseURL = config.projects[0].use?.baseURL || 'http://localhost:3000';
    
    console.log(`📡 Waiting for server at ${baseURL}...`);
    
    // Try to connect to the server with retries
    let retries = 30;
    let serverReady = false;
    
    while (retries > 0 && !serverReady) {
      try {
        const response = await page.goto(baseURL, { 
          waitUntil: 'networkidle', 
          timeout: 5000 
        });
        
        if (response && response.status() < 400) {
          serverReady = true;
          console.log('✅ Server is ready!');
        } else {
          throw new Error(`Server returned status: ${response?.status()}`);
        }
      } catch (error) {
        retries--;
        console.log(`⏱️  Waiting for server... (${retries} retries left)`);
        await page.waitForTimeout(2000);
      }
    }
    
    if (!serverReady) {
      throw new Error('❌ Server failed to start within the timeout period');
    }
    
    // Pre-populate test data or perform global setup actions here
    console.log('📝 Setting up test data...');
    
    // You could add mock data setup, database seeding, etc. here
    
    // Store authentication state for reuse in tests
    // This would be where you'd login with a test account and save the session
    
    console.log('✅ Global setup completed successfully!');
    
  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  } finally {
    await context.close();
    await browser.close();
  }
}

export default globalSetup;