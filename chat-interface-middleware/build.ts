#!/usr/bin/env bun

import { $ } from 'bun';
import { existsSync } from 'fs';

console.log('🏗️  Building Chat Interface Middleware...');

try {
  // Type check
  console.log('🔍 Type checking...');
  await $`bun run type-check`;
  console.log('✅ Type check passed');

  // Run tests
  console.log('🧪 Running tests...');
  if (existsSync('__tests__')) {
    await $`bun test`;
    console.log('✅ Tests passed');
  } else {
    console.log('⚠️  No tests found, skipping...');
  }

  // Create directories
  console.log('📁 Creating directories...');
  await $`mkdir -p dist storage logs screenshots traces cookies`;

  // Copy static files
  console.log('📋 Copying files...');
  await $`cp -r configs dist/ || echo "No configs directory found"`;
  await $`cp package.json dist/`;
  await $`cp README.md dist/ || echo "No README found"`;

  console.log('🎉 Build completed successfully!');
  console.log('');
  console.log('📦 Built files are in: dist/');
  console.log('🚀 To start: bun run start');

} catch (error) {
  console.error('❌ Build failed:', error.message);
  process.exit(1);
}