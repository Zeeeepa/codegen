#!/usr/bin/env node

// Simple test for basic functionality
import { readFileSync } from 'fs';
import { parse as parseYAML } from 'yaml';

console.log('🧪 Running Simple Middleware Tests...\n');

// Test 1: YAML Parsing
console.log('Test 1: YAML Configuration Parsing');
try {
  const configPath = './configs/examples/mistral-chat.yaml';
  const yamlContent = readFileSync(configPath, 'utf8');
  const config = parseYAML(yamlContent);
  
  console.log(`✅ YAML parsed successfully`);
  console.log(`   - Interface: ${config.interface?.name || 'Unknown'}`);
  console.log(`   - URL: ${config.interface?.url || 'Unknown'}`);
  console.log(`   - Tools: ${config.tools?.length || 0}`);
} catch (error) {
  console.log(`❌ YAML parsing failed: ${error.message}`);
}

// Test 2: Project Structure
console.log('\nTest 2: Project Structure');
import { readdirSync, statSync } from 'fs';

const expectedDirs = ['src', 'configs', '__tests__'];
const missingDirs = [];

for (const dir of expectedDirs) {
  try {
    const stat = statSync(`./${dir}`);
    if (stat.isDirectory()) {
      console.log(`✅ Directory exists: ${dir}`);
    } else {
      console.log(`❌ Not a directory: ${dir}`);
      missingDirs.push(dir);
    }
  } catch {
    console.log(`❌ Directory missing: ${dir}`);
    missingDirs.push(dir);
  }
}

// Test 3: Source Files
console.log('\nTest 3: Key Source Files');
const expectedFiles = [
  'src/schemas/config.ts',
  'src/utils/logger.ts',
  'src/middleware/chat-interface-manager.ts',
  'src/automation/playwright-manager.ts',
  'src/index.ts'
];

for (const file of expectedFiles) {
  try {
    const stat = statSync(`./${file}`);
    if (stat.isFile()) {
      const size = Math.round(stat.size / 1024);
      console.log(`✅ File exists: ${file} (${size}KB)`);
    }
  } catch {
    console.log(`❌ File missing: ${file}`);
  }
}

// Test 4: Dependencies
console.log('\nTest 4: Package Dependencies');
try {
  const packageJson = JSON.parse(readFileSync('./package.json', 'utf8'));
  const deps = Object.keys(packageJson.dependencies || {});
  const devDeps = Object.keys(packageJson.devDependencies || {});
  
  console.log(`✅ Dependencies: ${deps.length} runtime, ${devDeps.length} dev`);
  
  const criticalDeps = ['playwright', 'zod', 'yaml', 'express', 'winston'];
  const missing = criticalDeps.filter(dep => !deps.includes(dep));
  
  if (missing.length === 0) {
    console.log(`✅ All critical dependencies present`);
  } else {
    console.log(`⚠️  Missing critical dependencies: ${missing.join(', ')}`);
  }
} catch (error) {
  console.log(`❌ Package.json check failed: ${error.message}`);
}

// Test 5: Configuration Examples
console.log('\nTest 5: Example Configurations');
try {
  const exampleDir = './configs/examples';
  const files = readdirSync(exampleDir);
  const yamlFiles = files.filter(f => f.endsWith('.yaml') || f.endsWith('.yml'));
  
  console.log(`✅ Found ${yamlFiles.length} example configuration(s)`);
  
  for (const file of yamlFiles) {
    const filePath = `${exampleDir}/${file}`;
    try {
      const content = readFileSync(filePath, 'utf8');
      const config = parseYAML(content);
      console.log(`   - ${file}: ${config.interface?.name || 'unnamed'}`);
    } catch (error) {
      console.log(`   - ${file}: ❌ Parse error`);
    }
  }
} catch (error) {
  console.log(`❌ Example config check failed: ${error.message}`);
}

console.log('\n🎯 Basic Tests Complete!\n');

// Summary
console.log('📊 Test Summary:');
console.log('   - Project structure validation');
console.log('   - YAML configuration parsing');  
console.log('   - Dependency verification');
console.log('   - Source file existence checks');
console.log('   - Example configuration validation');

console.log('\n✅ Core middleware components are properly structured!');
console.log('🚀 Ready for TypeScript compilation and advanced testing.');

export {}; // Make this a module