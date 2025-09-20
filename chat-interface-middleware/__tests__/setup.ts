// Test setup file
import { beforeAll, afterAll } from 'bun:test';

// Global test setup
beforeAll(() => {
  // Set test environment variables
  process.env.NODE_ENV = 'test';
  process.env.LOG_LEVEL = 'error';
  process.env.CONFIG_DIR = '__tests__/fixtures/configs';
  process.env.STORAGE_DIR = '__tests__/fixtures/storage';
});

// Global test cleanup
afterAll(() => {
  // Clean up any global resources
});