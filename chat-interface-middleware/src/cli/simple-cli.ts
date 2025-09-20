#!/usr/bin/env node

import { readFileSync } from 'fs';
import { parse as parseYAML } from 'yaml';

// Simple CLI without external dependencies
const args = process.argv.slice(2);
const command = args[0];

console.log('🔧 Chat Interface Middleware CLI\n');

switch (command) {
  case 'validate':
    await validateCommand();
    break;
  case 'list':
    await listCommand();
    break;
  case 'help':
  case '--help':
  case undefined:
    showHelp();
    break;
  default:
    console.log(`❌ Unknown command: ${command}`);
    console.log('Run "cli help" for available commands');
    process.exit(1);
}

async function validateCommand() {
  const configFile = getArgValue('--config', '-c') || './configs/examples/mistral-chat.yaml';
  
  console.log(`🔍 Validating configuration: ${configFile}`);
  
  try {
    const content = readFileSync(configFile, 'utf8');
    const config = parseYAML(content);
    
    // Basic validation
    const errors = [];
    
    if (!config.interface) {
      errors.push('Missing "interface" section');
    } else {
      if (!config.interface.name) errors.push('Missing interface.name');
      if (!config.interface.url) errors.push('Missing interface.url');
      if (!config.interface.selectors) errors.push('Missing interface.selectors');
    }
    
    if (!config.tools || !Array.isArray(config.tools)) {
      errors.push('Missing "tools" array');
    } else if (config.tools.length === 0) {
      errors.push('Tools array is empty');
    }
    
    if (errors.length === 0) {
      console.log('✅ Configuration is valid!');
      console.log(`   Interface: ${config.interface.name}`);
      console.log(`   URL: ${config.interface.url}`);
      console.log(`   Tools: ${config.tools.length}`);
    } else {
      console.log('❌ Configuration errors found:');
      errors.forEach(error => console.log(`   - ${error}`));
      process.exit(1);
    }
  } catch (error) {
    console.log(`❌ Validation failed: ${error.message}`);
    process.exit(1);
  }
}

async function listCommand() {
  console.log('📋 Available Configurations:\n');
  
  try {
    import('fs').then(fs => {
      const configs = fs.readdirSync('./configs/examples');
      const yamlFiles = configs.filter(f => f.endsWith('.yaml') || f.endsWith('.yml'));
      
      if (yamlFiles.length === 0) {
        console.log('No configuration files found in ./configs/examples');
        return;
      }
      
      yamlFiles.forEach(file => {
        try {
          const content = readFileSync(`./configs/examples/${file}`, 'utf8');
          const config = parseYAML(content);
          
          console.log(`📡 ${file}`);
          console.log(`   Name: ${config.interface?.name || 'Unknown'}`);
          console.log(`   URL: ${config.interface?.url || 'Unknown'}`);
          console.log(`   Tools: ${config.tools?.length || 0}`);
          console.log('');
        } catch (error) {
          console.log(`📡 ${file} (❌ Parse error)`);
          console.log('');
        }
      });
    });
  } catch (error) {
    console.log(`❌ Failed to list configurations: ${error.message}`);
  }
}

function showHelp() {
  console.log('Available Commands:');
  console.log('');
  console.log('  validate [--config <file>]  Validate a configuration file');
  console.log('  list                        List available configurations');
  console.log('  help                        Show this help message');
  console.log('');
  console.log('Examples:');
  console.log('  npm run cli validate');
  console.log('  npm run cli validate --config configs/my-config.yaml');
  console.log('  npm run cli list');
  console.log('');
  console.log('Options:');
  console.log('  --config, -c <file>         Configuration file path');
  console.log('  --help                      Show help');
}

function getArgValue(longFlag: string, shortFlag?: string): string | undefined {
  const index = args.findIndex(arg => arg === longFlag || (shortFlag && arg === shortFlag));
  return index !== -1 && index + 1 < args.length ? args[index + 1] : undefined;
}