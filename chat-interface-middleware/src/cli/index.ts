#!/usr/bin/env bun

import { Command } from 'commander';
import { join } from 'path';
import chalk from 'chalk';
import ora from 'ora';
import inquirer from 'inquirer';

import { ConfigLoader } from '../../config/loader.js';
import { validateConfig } from '../../schemas/config.js';
import { ChatInterfaceManager } from '../../middleware/chat-interface-manager.js';

const program = new Command();

program
  .name('chat-interface-cli')
  .description('CLI for Chat Interface Middleware')
  .version('1.0.0');

// Validate configuration command
program
  .command('validate')
  .description('Validate configuration files')
  .option('-c, --config <path>', 'Configuration file path')
  .option('-d, --dir <path>', 'Configuration directory path', './configs')
  .action(async (options) => {
    const spinner = ora('Validating configurations...').start();

    try {
      if (options.config) {
        // Validate single file
        const configLoader = new ConfigLoader({ configDir: process.cwd() });
        const result = await configLoader.validateConfigFile(options.config);
        
        if (result.valid) {
          spinner.succeed(chalk.green(`✓ Configuration is valid: ${options.config}`));
        } else {
          spinner.fail(chalk.red(`✗ Configuration is invalid: ${options.config}`));
          console.error(chalk.red('Errors:'));
          result.errors?.forEach(error => {
            console.error(chalk.red(`  - ${error.message}`));
          });
          process.exit(1);
        }
      } else {
        // Validate all files in directory
        const configLoader = new ConfigLoader({ configDir: options.dir });
        const configs = await configLoader.loadConfigsFromDirectory();
        
        let validCount = 0;
        let invalidCount = 0;
        
        for (const [name, config] of configs) {
          try {
            validateConfig(config);
            validCount++;
            console.log(chalk.green(`✓ ${name}`));
          } catch (error) {
            invalidCount++;
            console.log(chalk.red(`✗ ${name}: ${error.message}`));
          }
        }
        
        if (invalidCount === 0) {
          spinner.succeed(chalk.green(`All ${validCount} configurations are valid`));
        } else {
          spinner.fail(chalk.red(`${invalidCount} configurations are invalid, ${validCount} are valid`));
          process.exit(1);
        }
      }
    } catch (error) {
      spinner.fail(chalk.red(`Error: ${error.message}`));
      process.exit(1);
    }
  });

// Test interface command
program
  .command('test')
  .description('Test interface configuration')
  .requiredOption('-i, --interface <name>', 'Interface name to test')
  .option('-c, --config-dir <path>', 'Configuration directory', './configs')
  .option('-a, --action <action>', 'Test action')
  .option('-p, --payload <json>', 'Test payload as JSON string')
  .action(async (options) => {
    const spinner = ora('Testing interface...').start();

    try {
      const manager = new ChatInterfaceManager({
        configDir: options.configDir,
        storage: {
          baseDir: join(process.cwd(), 'storage')
        }
      });

      await manager.initialize();

      const payload = options.payload ? JSON.parse(options.payload) : {};
      const result = await manager.testInterface(options.interface, options.action, payload);

      if (result.success) {
        spinner.succeed(chalk.green('Interface test passed'));
        
        console.log(chalk.blue('\\nTest Results:'));
        result.results.forEach(test => {
          const status = test.success ? chalk.green('✓') : chalk.red('✗');
          const duration = test.duration ? chalk.gray(`(${test.duration}ms)`) : '';
          console.log(`  ${status} ${test.test} ${duration}`);
          if (test.error) {
            console.log(chalk.red(`    Error: ${test.error}`));
          }
        });
      } else {
        spinner.fail(chalk.red('Interface test failed'));
        
        console.log(chalk.blue('\\nTest Results:'));
        result.results.forEach(test => {
          const status = test.success ? chalk.green('✓') : chalk.red('✗');
          console.log(`  ${status} ${test.test}`);
          if (test.error) {
            console.log(chalk.red(`    Error: ${test.error}`));
          }
        });
        process.exit(1);
      }

      await manager.cleanup();
    } catch (error) {
      spinner.fail(chalk.red(`Error: ${error.message}`));
      process.exit(1);
    }
  });

// List interfaces command
program
  .command('list')
  .description('List available interfaces')
  .option('-c, --config-dir <path>', 'Configuration directory', './configs')
  .action(async (options) => {
    const spinner = ora('Loading interfaces...').start();

    try {
      const configLoader = new ConfigLoader({ configDir: options.configDir });
      const configs = await configLoader.loadConfigsFromDirectory();

      spinner.stop();

      if (configs.size === 0) {
        console.log(chalk.yellow('No interfaces found'));
        return;
      }

      console.log(chalk.blue(`\\nFound ${configs.size} interface(s):\\n`));

      for (const [name, config] of configs) {
        console.log(chalk.green(`📡 ${config.interface.name}`));
        console.log(`   Name: ${name}`);
        console.log(`   URL: ${config.interface.url}`);
        console.log(`   Tools: ${config.tools.length}`);
        console.log(`   Description: ${config.metadata.description || 'No description'}`);
        console.log('');
      }
    } catch (error) {
      spinner.fail(chalk.red(`Error: ${error.message}`));
      process.exit(1);
    }
  });

// Interactive setup command
program
  .command('setup')
  .description('Interactive setup wizard')
  .action(async () => {
    console.log(chalk.blue('🚀 Chat Interface Middleware Setup Wizard\\n'));

    const answers = await inquirer.prompt([
      {
        type: 'input',
        name: 'interfaceName',
        message: 'Interface name:',
        default: 'my_chat_interface'
      },
      {
        type: 'input', 
        name: 'url',
        message: 'Interface URL:',
        validate: (input) => {
          try {
            new URL(input);
            return true;
          } catch {
            return 'Please enter a valid URL';
          }
        }
      },
      {
        type: 'list',
        name: 'authType',
        message: 'Authentication method:',
        choices: [
          { name: 'No authentication', value: 'none' },
          { name: 'Email + Password', value: 'credentials' },
          { name: 'OAuth', value: 'oauth' },
          { name: 'Token', value: 'token' },
          { name: 'Cookies', value: 'cookie' }
        ]
      },
      {
        type: 'input',
        name: 'textInputSelector',
        message: 'CSS selector for text input:',
        default: 'textarea, input[type="text"]'
      },
      {
        type: 'input',
        name: 'sendButtonSelector',
        message: 'CSS selector for send button:',
        default: 'button[type="submit"], .send-button'
      },
      {
        type: 'confirm',
        name: 'createConfig',
        message: 'Create configuration file?',
        default: true
      }
    ]);

    if (answers.createConfig) {
      const configTemplate = `version: "1.0"
metadata:
  name: "${answers.interfaceName}-interface"
  description: "Auto-generated configuration for ${answers.interfaceName}"

interface:
  name: "${answers.interfaceName}"
  url: "${answers.url}"
  ${answers.authType !== 'none' ? `auth:\n    type: "${answers.authType}"` : ''}
  selectors:
    text_input: "${answers.textInputSelector}"
    send_button: "${answers.sendButtonSelector}"
    response_area: ".messages, .chat-messages"

tools:
  - name: "sendMessage"
    description: "Send message to ${answers.interfaceName}"
    input:
      type: "object"
      properties:
        message:
          type: "string"
          description: "Message to send"
      required: ["message"]
    execute: |
      const { page } = await playwright.getInstance(config.interface.name);
      await page.fill(selectors.text_input, input.message);
      await page.click(selectors.send_button);
      return { status: 'sent', message: input.message };

automation:
  browser: "chromium"
  headless: false
  viewport:
    width: 1280
    height: 720
`;

      const fs = await import('fs/promises');
      const configPath = join(process.cwd(), 'configs', `${answers.interfaceName}.yaml`);
      
      await fs.mkdir(join(process.cwd(), 'configs'), { recursive: true });
      await fs.writeFile(configPath, configTemplate);

      console.log(chalk.green(`\\n✅ Configuration created: ${configPath}`));
      console.log(chalk.blue('\\n🔧 Next steps:'));
      console.log(`1. Edit the configuration file to customize selectors`);
      console.log(`2. Test the configuration: ${chalk.cyan(`bun run cli test -i ${answers.interfaceName}`)}`);
      console.log(`3. Start the middleware server: ${chalk.cyan('bun run dev')}`);
    }
  });

// Server command
program
  .command('server')
  .description('Start the middleware server')
  .option('-p, --port <port>', 'Port number', '3000')
  .option('-c, --config-dir <path>', 'Configuration directory', './configs')
  .action(async (options) => {
    const { ChatInterfaceMiddlewareServer } = await import('@/index.js');
    
    const config = {
      port: parseInt(options.port),
      host: '0.0.0.0',
      configDir: options.configDir,
      storageDir: join(process.cwd(), 'storage'),
      enableCors: true,
      enableSecurity: true,
      enableWebSocket: true,
      logLevel: 'info' as const,
    };

    const server = new ChatInterfaceMiddlewareServer(config);
    
    console.log(chalk.blue('🚀 Starting Chat Interface Middleware Server...\\n'));
    
    try {
      await server.start();
    } catch (error) {
      console.error(chalk.red('Failed to start server:', error.message));
      process.exit(1);
    }
  });

// Parse command line arguments
program.parse();

export { program };