import { describe, expect, test } from 'bun:test';
import { validateConfig, ChatInterfaceConfigSchema } from '../src/schemas/config';

describe('Configuration Schema', () => {
  test('should validate a complete valid configuration', () => {
    const validConfig = {
      version: '1.0',
      metadata: {
        name: 'test-interface',
        description: 'Test interface configuration',
      },
      interface: {
        name: 'test_chat',
        url: 'https://example.com',
        selectors: {
          text_input: '.chat-input',
          send_button: '.send-btn',
          response_area: '.messages',
        },
      },
      tools: [
        {
          name: 'sendMessage',
          description: 'Send a message',
          input: {
            type: 'object',
            properties: {
              message: {
                type: 'string',
                description: 'Message to send',
              },
            },
            required: ['message'],
          },
          execute: 'return { success: true };',
        },
      ],
    };

    expect(() => validateConfig(validConfig)).not.toThrow();
  });

  test('should reject configuration with missing required fields', () => {
    const invalidConfig = {
      version: '1.0',
      metadata: {
        name: 'test-interface',
      },
      // Missing interface and tools
    };

    expect(() => validateConfig(invalidConfig)).toThrow();
  });

  test('should reject configuration with invalid URL', () => {
    const invalidConfig = {
      version: '1.0',
      metadata: {
        name: 'test-interface',
      },
      interface: {
        name: 'test_chat',
        url: 'not-a-valid-url',
        selectors: {
          text_input: '.input',
          send_button: '.send',
          response_area: '.messages',
        },
      },
      tools: [],
    };

    expect(() => validateConfig(invalidConfig)).toThrow();
  });

  test('should accept optional authentication configuration', () => {
    const configWithAuth = {
      version: '1.0',
      metadata: {
        name: 'test-interface',
      },
      interface: {
        name: 'test_chat',
        url: 'https://example.com',
        auth: {
          type: 'credentials',
          email: 'test@example.com',
          password: 'password123',
        },
        selectors: {
          text_input: '.input',
          send_button: '.send',
          response_area: '.messages',
        },
      },
      tools: [],
    };

    expect(() => validateConfig(configWithAuth)).not.toThrow();
  });

  test('should validate tool input schemas', () => {
    const configWithComplexTool = {
      version: '1.0',
      metadata: {
        name: 'test-interface',
      },
      interface: {
        name: 'test_chat',
        url: 'https://example.com',
        selectors: {
          text_input: '.input',
          send_button: '.send',
          response_area: '.messages',
        },
      },
      tools: [
        {
          name: 'complexTool',
          description: 'A complex tool',
          input: {
            type: 'object',
            properties: {
              message: {
                type: 'string',
                description: 'Message',
              },
              options: {
                type: 'object',
                properties: {
                  timeout: {
                    type: 'number',
                    description: 'Timeout in ms',
                  },
                  retries: {
                    type: 'number',
                    description: 'Number of retries',
                  },
                },
              },
            },
            required: ['message'],
          },
          execute: 'return { success: true };',
        },
      ],
    };

    expect(() => validateConfig(configWithComplexTool)).not.toThrow();
  });

  test('should accept optional automation configuration', () => {
    const configWithAutomation = {
      version: '1.0',
      metadata: {
        name: 'test-interface',
      },
      interface: {
        name: 'test_chat',
        url: 'https://example.com',
        selectors: {
          text_input: '.input',
          send_button: '.send',
          response_area: '.messages',
        },
      },
      tools: [],
      automation: {
        browser: 'chromium',
        headless: true,
        viewport: {
          width: 1920,
          height: 1080,
        },
        cookies: {
          load_from: 'cookies.json',
          save_to: 'cookies.json',
        },
      },
    };

    expect(() => validateConfig(configWithAutomation)).not.toThrow();
  });

  test('should set default values for optional fields', () => {
    const minimalConfig = {
      metadata: {
        name: 'test-interface',
      },
      interface: {
        name: 'test_chat',
        url: 'https://example.com',
        selectors: {
          text_input: '.input',
          send_button: '.send',
          response_area: '.messages',
        },
      },
      tools: [],
    };

    const validated = validateConfig(minimalConfig);

    expect(validated.version).toBe('1.0');
    expect(validated.interface.states?.initial).toBe('completed');
    expect(validated.interface.states?.pending).toBe('processing');
  });
});