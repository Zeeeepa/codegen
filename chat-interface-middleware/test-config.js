#!/usr/bin/env node

// Simple test for configuration validation
import { readFileSync } from 'fs';
import { parse as parseYAML } from 'yaml';
import { ChatInterfaceConfigSchema } from './src/schemas/config.js';

async function testConfigValidation() {
  console.log('🧪 Testing configuration validation...');

  try {
    // Test 1: Load example config
    const configPath = './configs/examples/mistral-chat.yaml';
    console.log(`📄 Loading config: ${configPath}`);
    
    const yamlContent = readFileSync(configPath, 'utf8');
    const config = parseYAML(yamlContent);
    
    console.log(`✅ YAML parsed successfully`);
    
    // Test 2: Validate with schema
    const validationResult = ChatInterfaceConfigSchema.safeParse(config);
    
    if (validationResult.success) {
      console.log(`✅ Configuration validation passed`);
      console.log(`🔧 Interface: ${validationResult.data.interface.name}`);
      console.log(`🛠️  Tools: ${validationResult.data.tools.length}`);
      console.log(`📝 Description: ${validationResult.data.metadata.description}`);
    } else {
      console.log(`❌ Configuration validation failed:`);
      validationResult.error.errors.forEach(error => {
        console.log(`   - ${error.path.join('.')}: ${error.message}`);
      });
      return false;
    }

    // Test 3: Validate required fields
    const requiredFields = ['interface', 'tools'];
    for (const field of requiredFields) {
      if (!validationResult.data[field]) {
        console.log(`❌ Missing required field: ${field}`);
        return false;
      }
    }
    console.log(`✅ Required fields present`);

    return true;
  } catch (error) {
    console.error(`❌ Test failed:`, error.message);
    return false;
  }
}

// Run the test
testConfigValidation()
  .then(success => {
    if (success) {
      console.log(`\n🎉 Configuration validation test passed!`);
      process.exit(0);
    } else {
      console.log(`\n💥 Configuration validation test failed!`);
      process.exit(1);
    }
  })
  .catch(error => {
    console.error('💥 Unexpected error:', error);
    process.exit(1);
  });