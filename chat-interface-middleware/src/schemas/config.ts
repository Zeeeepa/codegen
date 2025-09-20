import { z } from 'zod';

// Authentication schema
const AuthConfigSchema = z.object({
  type: z.enum(['credentials', 'oauth', 'token', 'cookie']),
  email: z.string().email().optional(),
  password: z.string().optional(),
  token: z.string().optional(),
  oauth_url: z.string().url().optional(),
  cookie_file: z.string().optional(),
});

// Network configuration schema
const NetworkConfigSchema = z.object({
  proxy: z.string().optional(),
  timeout: z.number().default(30000),
  user_agent: z.string().optional(),
  headers: z.record(z.string()).optional(),
});

// UI selectors schema
const SelectorsSchema = z.object({
  text_input: z.string(),
  send_button: z.string(),
  response_area: z.string(),
  new_chat_button: z.string().optional(),
  loading_indicator: z.string().optional(),
  error_message: z.string().optional(),
});

// Interface states schema
const StatesSchema = z.object({
  initial: z.string().default('completed'),
  pending: z.string().default('processing'),
  error: z.string().default('failed'),
  success: z.string().default('completed'),
});

// Tool input schema (flexible for different tools)
const ToolInputSchema = z.object({
  type: z.literal('object'),
  properties: z.record(z.any()),
  required: z.array(z.string()).optional(),
});

// Tool definition schema
const ToolSchema = z.object({
  name: z.string(),
  description: z.string(),
  input: ToolInputSchema,
  execute: z.string(), // JavaScript code as string
  client_execute: z.string().optional(), // Optional client-side execution
  render: z.string().optional(), // Optional rendering function
});

// Interface configuration schema
const InterfaceConfigSchema = z.object({
  name: z.string(),
  url: z.string().url(),
  auth: AuthConfigSchema.optional(),
  network: NetworkConfigSchema.optional(),
  selectors: SelectorsSchema,
  states: StatesSchema.optional(),
});

// Browser automation configuration
const AutomationConfigSchema = z.object({
  browser: z.enum(['chromium', 'firefox', 'webkit']).default('chromium'),
  headless: z.boolean().default(false),
  viewport: z.object({
    width: z.number().default(1280),
    height: z.number().default(720),
  }),
  cookies: z.object({
    load_from: z.string().optional(),
    save_to: z.string().optional(),
    auto_save: z.boolean().default(true),
  }),
  screenshots: z.object({
    auto_capture: z.boolean().default(true),
    path: z.string().default('screenshots/'),
    format: z.enum(['png', 'jpeg']).default('png'),
  }),
});

// Integration configurations
const IntegrationsConfigSchema = z.object({
  better_ui: z.object({
    enabled: z.boolean().default(true),
    theme: z.enum(['light', 'dark', 'auto']).default('dark'),
    components: z.array(z.string()).default([]),
  }),
  mcp_playwright: z.object({
    enabled: z.boolean().default(true),
    port: z.number().default(3001),
    timeout: z.number().default(30000),
    max_contexts: z.number().default(10),
  }),
  zeeeepa_api: z.object({
    enabled: z.boolean().default(true),
    base_url: z.string().url().optional(),
    api_key: z.string().optional(),
  }),
});

// Monitoring configuration
const MonitoringConfigSchema = z.object({
  health_check: z.object({
    enabled: z.boolean().default(true),
    interval: z.number().default(30000),
    endpoint: z.string().default('/health'),
  }),
  logging: z.object({
    level: z.enum(['error', 'warn', 'info', 'debug']).default('info'),
    file: z.string().optional(),
    console: z.boolean().default(true),
  }),
  metrics: z.object({
    enabled: z.boolean().default(true),
    endpoint: z.string().default('/metrics'),
    collection_interval: z.number().default(10000),
  }),
});

// Testing configuration
const TestingConfigSchema = z.object({
  auto_test: z.boolean().default(false),
  test_message: z.string().default('Hello, this is a test'),
  expected_response_time: z.number().default(5000),
  test_interval: z.number().optional(),
  health_checks: z.boolean().default(true),
});

// Main configuration schema
export const ChatInterfaceConfigSchema = z.object({
  version: z.string().default('1.0'),
  metadata: z.object({
    name: z.string(),
    description: z.string().optional(),
    version: z.string().optional(),
    created_at: z.string().optional(),
    updated_at: z.string().optional(),
  }),
  interface: InterfaceConfigSchema,
  tools: z.array(ToolSchema),
  automation: AutomationConfigSchema.optional(),
  integrations: IntegrationsConfigSchema.optional(),
  monitoring: MonitoringConfigSchema.optional(),
  testing: TestingConfigSchema.optional(),
});

// Type exports
export type AuthConfig = z.infer<typeof AuthConfigSchema>;
export type NetworkConfig = z.infer<typeof NetworkConfigSchema>;
export type Selectors = z.infer<typeof SelectorsSchema>;
export type States = z.infer<typeof StatesSchema>;
export type ToolInput = z.infer<typeof ToolInputSchema>;
export type Tool = z.infer<typeof ToolSchema>;
export type InterfaceConfig = z.infer<typeof InterfaceConfigSchema>;
export type AutomationConfig = z.infer<typeof AutomationConfigSchema>;
export type IntegrationsConfig = z.infer<typeof IntegrationsConfigSchema>;
export type MonitoringConfig = z.infer<typeof MonitoringConfigSchema>;
export type TestingConfig = z.infer<typeof TestingConfigSchema>;
export type ChatInterfaceConfig = z.infer<typeof ChatInterfaceConfigSchema>;

// Validation functions
export const validateConfig = (config: unknown): ChatInterfaceConfig => {
  return ChatInterfaceConfigSchema.parse(config);
};

export const validatePartialConfig = (config: unknown): Partial<ChatInterfaceConfig> => {
  return ChatInterfaceConfigSchema.partial().parse(config);
};

// Schema validation helpers
export const isValidConfig = (config: unknown): config is ChatInterfaceConfig => {
  try {
    ChatInterfaceConfigSchema.parse(config);
    return true;
  } catch {
    return false;
  }
};

export const getConfigErrors = (config: unknown): z.ZodError | null => {
  try {
    ChatInterfaceConfigSchema.parse(config);
    return null;
  } catch (error) {
    if (error instanceof z.ZodError) {
      return error;
    }
    return null;
  }
};