import { z } from 'zod';
import { Tool, ChatInterfaceConfig } from '../../schemas/config.js';
import { Logger } from '../../utils/logger.js';
import { PlaywrightManager } from '../../automation/playwright-manager.js';
import { StorageManager } from '../../storage/storage-manager.js';

// Better-UI integration types
export interface AUITool {
  name: string;
  description: string;
  input: z.ZodSchema<any>;
  execute: (context: ExecutionContext) => Promise<any>;
  clientExecute?: (context: ClientExecutionContext) => Promise<any>;
  render?: (data: { data: any; error?: Error }) => React.ReactNode;
}

export interface ExecutionContext {
  input: any;
  playwright: PlaywrightManager;
  storage: StorageManager;
  selectors: any;
  config: ChatInterfaceConfig;
  logger: Logger;
}

export interface ClientExecutionContext extends ExecutionContext {
  fetch: typeof fetch;
  cache: Map<string, any>;
}

export interface BetterUIIntegrationConfig {
  enabled: boolean;
  theme: 'light' | 'dark' | 'auto';
  components: string[];
}

export class BetterUIIntegration {
  private logger: Logger;
  private tools: Map<string, AUITool> = new Map();

  constructor(
    private config: BetterUIIntegrationConfig,
    private playwrightManager: PlaywrightManager,
    private storageManager: StorageManager
  ) {
    this.logger = new Logger('BetterUIIntegration');
  }

  /**
   * Convert YAML tool definition to Better-UI AUI tool
   */
  createAUITool(toolDef: Tool, interfaceConfig: ChatInterfaceConfig): AUITool {
    this.logger.debug(`Creating AUI tool: ${toolDef.name}`);

    // Create Zod schema from tool input definition
    const inputSchema = this.createZodSchema(toolDef.input);

    // Create execution function
    const executeFunction = this.createExecuteFunction(
      toolDef.execute,
      interfaceConfig
    );

    // Create client execution function if defined
    const clientExecuteFunction = toolDef.client_execute
      ? this.createClientExecuteFunction(toolDef.client_execute, interfaceConfig)
      : undefined;

    // Create render function if defined
    const renderFunction = toolDef.render
      ? this.createRenderFunction(toolDef.render)
      : undefined;

    const auiTool: AUITool = {
      name: toolDef.name,
      description: toolDef.description,
      input: inputSchema,
      execute: executeFunction,
      clientExecute: clientExecuteFunction,
      render: renderFunction,
    };

    this.tools.set(toolDef.name, auiTool);
    this.logger.info(`Created AUI tool: ${toolDef.name}`);

    return auiTool;
  }

  /**
   * Create Zod schema from tool input definition
   */
  private createZodSchema(inputDef: any): z.ZodSchema<any> {
    if (inputDef.type === 'object') {
      const shape: any = {};
      
      for (const [key, propDef] of Object.entries(inputDef.properties)) {
        shape[key] = this.createZodFieldSchema(propDef as any);
      }

      let schema = z.object(shape);

      // Handle required fields
      if (inputDef.required && inputDef.required.length > 0) {
        const optional = Object.keys(inputDef.properties).filter(
          key => !inputDef.required.includes(key)
        );
        
        for (const field of optional) {
          schema = schema.extend({
            [field]: schema.shape[field].optional()
          });
        }
      }

      return schema;
    }

    return z.any(); // Fallback for unknown types
  }

  /**
   * Create individual Zod field schema
   */
  private createZodFieldSchema(propDef: any): z.ZodSchema<any> {
    switch (propDef.type) {
      case 'string':
        let stringSchema = z.string();
        if (propDef.format === 'email') stringSchema = stringSchema.email();
        if (propDef.format === 'url') stringSchema = stringSchema.url();
        if (propDef.minLength) stringSchema = stringSchema.min(propDef.minLength);
        if (propDef.maxLength) stringSchema = stringSchema.max(propDef.maxLength);
        if (propDef.enum) stringSchema = z.enum(propDef.enum);
        return stringSchema;

      case 'number':
        let numberSchema = z.number();
        if (propDef.minimum) numberSchema = numberSchema.min(propDef.minimum);
        if (propDef.maximum) numberSchema = numberSchema.max(propDef.maximum);
        return numberSchema;

      case 'integer':
        let intSchema = z.number().int();
        if (propDef.minimum) intSchema = intSchema.min(propDef.minimum);
        if (propDef.maximum) intSchema = intSchema.max(propDef.maximum);
        return intSchema;

      case 'boolean':
        return z.boolean();

      case 'array':
        const itemSchema = propDef.items 
          ? this.createZodFieldSchema(propDef.items)
          : z.any();
        return z.array(itemSchema);

      case 'object':
        return this.createZodSchema(propDef);

      default:
        return z.any();
    }
  }

  /**
   * Create execution function from JavaScript code string
   */
  private createExecuteFunction(
    executeCode: string,
    interfaceConfig: ChatInterfaceConfig
  ): (context: ExecutionContext) => Promise<any> {
    return async (context: ExecutionContext) => {
      try {
        this.logger.debug(`Executing tool with context for interface: ${interfaceConfig.interface.name}`);

        // Create safe execution environment
        const safeContext = {
          ...context,
          // Add additional helper functions
          wait: (ms: number) => new Promise(resolve => setTimeout(resolve, ms)),
          log: this.logger.debug.bind(this.logger),
        };

        // Execute the code safely
        const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
        const executeFunc = new AsyncFunction('context', `
          const { input, playwright, storage, selectors, config, logger, wait, log } = context;
          ${executeCode}
        `);

        const result = await executeFunc(safeContext);
        
        this.logger.debug('Tool execution completed successfully');
        return result;
      } catch (error) {
        this.logger.error('Tool execution failed:', error);
        throw error;
      }
    };
  }

  /**
   * Create client execution function
   */
  private createClientExecuteFunction(
    clientExecuteCode: string,
    interfaceConfig: ChatInterfaceConfig
  ): (context: ClientExecutionContext) => Promise<any> {
    return async (context: ClientExecutionContext) => {
      try {
        this.logger.debug(`Executing client-side tool for interface: ${interfaceConfig.interface.name}`);

        const safeContext = {
          ...context,
          log: this.logger.debug.bind(this.logger),
        };

        const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
        const executeFunc = new AsyncFunction('context', `
          const { input, playwright, storage, selectors, config, logger, fetch, cache } = context;
          ${clientExecuteCode}
        `);

        const result = await executeFunc(safeContext);
        
        this.logger.debug('Client-side tool execution completed successfully');
        return result;
      } catch (error) {
        this.logger.error('Client-side tool execution failed:', error);
        throw error;
      }
    };
  }

  /**
   * Create render function for UI display
   */
  private createRenderFunction(renderCode: string): (data: { data: any; error?: Error }) => any {
    return (data) => {
      try {
        // Note: This would need proper React JSX compilation
        // For now, return a simple representation
        const renderFunc = new Function('data', `
          const { data: result, error } = data;
          ${renderCode}
        `);

        return renderFunc(data);
      } catch (error) {
        this.logger.error('Render function execution failed:', error);
        return `Error rendering: ${error.message}`;
      }
    };
  }

  /**
   * Convert tools to AI SDK format for integration
   */
  toAISDKTools(tools: AUITool[]): Record<string, any> {
    const aiSDKTools: Record<string, any> = {};

    for (const tool of tools) {
      aiSDKTools[tool.name] = {
        description: tool.description,
        parameters: this.zodSchemaToParameters(tool.input),
        execute: tool.execute,
      };
    }

    return aiSDKTools;
  }

  /**
   * Convert Zod schema to AI SDK parameters format
   */
  private zodSchemaToParameters(schema: z.ZodSchema<any>): any {
    // This is a simplified conversion - would need more robust implementation
    if (schema instanceof z.ZodObject) {
      const properties: any = {};
      const required: string[] = [];

      for (const [key, fieldSchema] of Object.entries(schema.shape)) {
        properties[key] = this.zodFieldToParameter(fieldSchema as z.ZodSchema<any>);
        
        if (!(fieldSchema as any).isOptional()) {
          required.push(key);
        }
      }

      return {
        type: 'object',
        properties,
        required,
      };
    }

    return { type: 'any' };
  }

  /**
   * Convert individual Zod field to parameter definition
   */
  private zodFieldToParameter(schema: z.ZodSchema<any>): any {
    if (schema instanceof z.ZodString) {
      return { type: 'string' };
    } else if (schema instanceof z.ZodNumber) {
      return { type: 'number' };
    } else if (schema instanceof z.ZodBoolean) {
      return { type: 'boolean' };
    } else if (schema instanceof z.ZodArray) {
      return { 
        type: 'array',
        items: this.zodFieldToParameter(schema.element)
      };
    }

    return { type: 'any' };
  }

  /**
   * Get all registered tools
   */
  getTools(): Map<string, AUITool> {
    return new Map(this.tools);
  }

  /**
   * Get specific tool by name
   */
  getTool(name: string): AUITool | undefined {
    return this.tools.get(name);
  }

  /**
   * Create tools from interface configuration
   */
  async createToolsFromConfig(config: ChatInterfaceConfig): Promise<AUITool[]> {
    const tools: AUITool[] = [];

    for (const toolDef of config.tools) {
      try {
        const auiTool = this.createAUITool(toolDef, config);
        tools.push(auiTool);
      } catch (error) {
        this.logger.error(`Failed to create tool ${toolDef.name}:`, error);
      }
    }

    this.logger.info(`Created ${tools.length} AUI tools from configuration`);
    return tools;
  }

  /**
   * Test tool execution
   */
  async testTool(
    toolName: string, 
    input: any, 
    config: ChatInterfaceConfig
  ): Promise<{ success: boolean; result?: any; error?: Error }> {
    const tool = this.getTool(toolName);
    if (!tool) {
      return { 
        success: false, 
        error: new Error(`Tool not found: ${toolName}`) 
      };
    }

    try {
      const context: ExecutionContext = {
        input,
        playwright: this.playwrightManager,
        storage: this.storageManager,
        selectors: config.interface.selectors,
        config,
        logger: this.logger.child('ToolExecution'),
      };

      const result = await tool.execute(context);
      return { success: true, result };
    } catch (error) {
      return { 
        success: false, 
        error: error as Error 
      };
    }
  }
}