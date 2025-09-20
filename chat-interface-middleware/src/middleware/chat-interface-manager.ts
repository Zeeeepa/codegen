import { EventEmitter } from 'events';
import { ConfigLoader, ConfigLoaderOptions } from '../../config/loader.js';
import { BetterUIIntegration } from '../../integrations/better-ui.js';
import { PlaywrightManager, PlaywrightManagerOptions } from '../../automation/playwright-manager.js';
import { StorageManager, StorageOptions } from '../../storage/storage-manager.js';
import { Logger } from '../../utils/logger.js';
import { 
  ChatInterfaceConfig,
  validateConfig 
} from '../../schemas/config.js';

export interface ChatInterfaceManagerOptions {
  configDir: string;
  storage: StorageOptions;
  playwright?: PlaywrightManagerOptions;
  enableHotReload?: boolean;
}

export interface ChatRequest {
  interface: string;
  action: string;
  payload: any;
  metadata?: {
    requestId?: string;
    timestamp?: string;
    source?: string;
  };
}

export interface ChatResponse {
  success: boolean;
  data?: any;
  error?: {
    message: string;
    code: string;
    details?: any;
  };
  metadata: {
    requestId: string;
    timestamp: string;
    interface: string;
    action: string;
    duration: number;
  };
}

export class ChatInterfaceManagerError extends Error {
  constructor(
    message: string,
    public code: string = 'UNKNOWN_ERROR',
    public details?: any
  ) {
    super(message);
    this.name = 'ChatInterfaceManagerError';
  }
}

export class ChatInterfaceManager extends EventEmitter {
  private configLoader: ConfigLoader;
  private playwrightManager: PlaywrightManager;
  private storageManager: StorageManager;
  private betterUIIntegrations: Map<string, BetterUIIntegration> = new Map();
  private logger: Logger;
  private isInitialized = false;

  constructor(private options: ChatInterfaceManagerOptions) {
    super();
    this.logger = new Logger('ChatInterfaceManager');
    
    // Initialize components
    this.configLoader = new ConfigLoader({
      configDir: options.configDir,
      enableHotReload: options.enableHotReload ?? true,
    });

    this.playwrightManager = new PlaywrightManager(options.playwright);
    this.storageManager = new StorageManager(options.storage);

    this.setupEventHandlers();
  }

  /**
   * Initialize the manager and load configurations
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) {
      this.logger.warn('Manager already initialized');
      return;
    }

    try {
      this.logger.info('Initializing Chat Interface Manager');

      // Load all configurations
      const configs = await this.configLoader.loadConfigsFromDirectory();
      this.logger.info(`Loaded ${configs.size} interface configurations`);

      // Initialize Better-UI integrations for each config
      for (const [name, config] of configs) {
        await this.initializeBetterUIIntegration(name, config);
      }

      this.isInitialized = true;
      this.logger.info('Chat Interface Manager initialized successfully');
      this.emit('initialized', { configCount: configs.size });

    } catch (error) {
      this.logger.error('Failed to initialize Chat Interface Manager:', error);
      throw new ChatInterfaceManagerError(
        'Initialization failed',
        'INITIALIZATION_ERROR',
        error
      );
    }
  }

  /**
   * Process a chat request
   */
  async processRequest(request: ChatRequest): Promise<ChatResponse> {
    const startTime = Date.now();
    const requestId = request.metadata?.requestId || this.generateRequestId();

    try {
      this.logger.info(`Processing request: ${requestId}`, {
        interface: request.interface,
        action: request.action
      });

      // Validate request
      this.validateRequest(request);

      // Get configuration for the interface
      const config = this.configLoader.getConfig(request.interface);
      if (!config) {
        throw new ChatInterfaceManagerError(
          `Interface configuration not found: ${request.interface}`,
          'CONFIG_NOT_FOUND'
        );
      }

      // Get Better-UI integration
      const betterUI = this.betterUIIntegrations.get(request.interface);
      if (!betterUI) {
        throw new ChatInterfaceManagerError(
          `Better-UI integration not found for interface: ${request.interface}`,
          'INTEGRATION_NOT_FOUND'
        );
      }

      // Execute the action
      const result = await this.executeAction(config, betterUI, request);

      const duration = Date.now() - startTime;

      const response: ChatResponse = {
        success: true,
        data: result,
        metadata: {
          requestId,
          timestamp: new Date().toISOString(),
          interface: request.interface,
          action: request.action,
          duration,
        },
      };

      this.logger.info(`Request processed successfully: ${requestId}`, {
        duration: `${duration}ms`
      });

      this.emit('requestProcessed', request, response);
      return response;

    } catch (error) {
      const duration = Date.now() - startTime;
      
      this.logger.error(`Request failed: ${requestId}`, error);

      const response: ChatResponse = {
        success: false,
        error: {
          message: error.message,
          code: error.code || 'UNKNOWN_ERROR',
          details: error.details,
        },
        metadata: {
          requestId,
          timestamp: new Date().toISOString(),
          interface: request.interface,
          action: request.action,
          duration,
        },
      };

      this.emit('requestFailed', request, response, error);
      return response;
    }
  }

  /**
   * Execute a specific action using Better-UI integration
   */
  private async executeAction(
    config: ChatInterfaceConfig,
    betterUI: BetterUIIntegration,
    request: ChatRequest
  ): Promise<any> {
    // Find the tool for this action
    const tool = betterUI.getTool(request.action);
    if (!tool) {
      throw new ChatInterfaceManagerError(
        `Tool not found for action: ${request.action}`,
        'TOOL_NOT_FOUND'
      );
    }

    // Validate input against tool schema
    const validationResult = tool.input.safeParse(request.payload);
    if (!validationResult.success) {
      throw new ChatInterfaceManagerError(
        `Invalid input for action ${request.action}: ${validationResult.error.message}`,
        'INVALID_INPUT',
        validationResult.error.errors
      );
    }

    // Create execution context
    const context = {
      input: validationResult.data,
      playwright: this.playwrightManager,
      storage: this.storageManager,
      selectors: config.interface.selectors,
      config,
      logger: this.logger.child(`Action:${request.action}`),
    };

    // Execute the tool
    return await tool.execute(context);
  }

  /**
   * Get available interfaces
   */
  getAvailableInterfaces(): string[] {
    const configs = this.configLoader.getAllConfigs();
    return Array.from(configs.keys());
  }

  /**
   * Get interface configuration
   */
  getInterfaceConfig(interfaceName: string): ChatInterfaceConfig | undefined {
    return this.configLoader.getConfig(interfaceName);
  }

  /**
   * Get available actions for an interface
   */
  getAvailableActions(interfaceName: string): string[] {
    const betterUI = this.betterUIIntegrations.get(interfaceName);
    if (!betterUI) return [];

    return Array.from(betterUI.getTools().keys());
  }

  /**
   * Test an interface configuration
   */
  async testInterface(
    interfaceName: string,
    testAction?: string,
    testPayload?: any
  ): Promise<{
    success: boolean;
    results: Array<{
      test: string;
      success: boolean;
      error?: string;
      duration?: number;
    }>;
  }> {
    const config = this.configLoader.getConfig(interfaceName);
    if (!config) {
      return {
        success: false,
        results: [{
          test: 'config_load',
          success: false,
          error: `Configuration not found: ${interfaceName}`
        }]
      };
    }

    const results = [];

    // Test 1: Configuration validation
    try {
      validateConfig(config);
      results.push({ test: 'config_validation', success: true });
    } catch (error) {
      results.push({ 
        test: 'config_validation', 
        success: false, 
        error: error.message 
      });
    }

    // Test 2: Browser instance creation
    const browserTestStart = Date.now();
    try {
      const instance = await this.playwrightManager.createInstance(
        config.interface,
        config.automation
      );
      await this.playwrightManager.closeInstance(instance.id);
      
      results.push({ 
        test: 'browser_creation', 
        success: true,
        duration: Date.now() - browserTestStart
      });
    } catch (error) {
      results.push({ 
        test: 'browser_creation', 
        success: false, 
        error: error.message,
        duration: Date.now() - browserTestStart
      });
    }

    // Test 3: Tool execution (if specified)
    if (testAction && testPayload) {
      const toolTestStart = Date.now();
      try {
        const response = await this.processRequest({
          interface: interfaceName,
          action: testAction,
          payload: testPayload,
          metadata: { requestId: `test_${Date.now()}` }
        });

        results.push({
          test: 'tool_execution',
          success: response.success,
          error: response.error?.message,
          duration: Date.now() - toolTestStart
        });
      } catch (error) {
        results.push({
          test: 'tool_execution',
          success: false,
          error: error.message,
          duration: Date.now() - toolTestStart
        });
      }
    }

    const success = results.every(result => result.success);
    return { success, results };
  }

  /**
   * Reload interface configuration
   */
  async reloadInterface(interfaceName: string): Promise<void> {
    try {
      this.logger.info(`Reloading interface: ${interfaceName}`);

      // Reload configuration
      const config = await this.configLoader.reloadConfig(interfaceName);

      // Reinitialize Better-UI integration
      await this.initializeBetterUIIntegration(interfaceName, config);

      this.logger.info(`Interface reloaded successfully: ${interfaceName}`);
      this.emit('interfaceReloaded', interfaceName, config);

    } catch (error) {
      this.logger.error(`Failed to reload interface ${interfaceName}:`, error);
      throw new ChatInterfaceManagerError(
        `Failed to reload interface: ${interfaceName}`,
        'RELOAD_ERROR',
        error
      );
    }
  }

  /**
   * Get manager statistics
   */
  async getStats(): Promise<{
    interfaces: number;
    activeInstances: number;
    totalRequests?: number;
    storage: any;
  }> {
    const configs = this.configLoader.getAllConfigs();
    const activeInstances = this.playwrightManager.getActiveInstances();
    const storageStats = await this.storageManager.getStats();

    return {
      interfaces: configs.size,
      activeInstances: activeInstances.length,
      storage: storageStats,
    };
  }

  /**
   * Cleanup resources
   */
  async cleanup(): Promise<void> {
    this.logger.info('Cleaning up Chat Interface Manager');

    try {
      await this.configLoader.cleanup();
      await this.playwrightManager.cleanup();
      
      this.betterUIIntegrations.clear();
      this.removeAllListeners();
      
      this.isInitialized = false;
      this.logger.info('Cleanup completed successfully');
    } catch (error) {
      this.logger.error('Error during cleanup:', error);
    }
  }

  // Private helper methods

  private async initializeBetterUIIntegration(
    name: string, 
    config: ChatInterfaceConfig
  ): Promise<void> {
    try {
      this.logger.debug(`Initializing Better-UI integration for: ${name}`);

      const betterUI = new BetterUIIntegration(
        config.integrations?.better_ui || { enabled: true, theme: 'dark', components: [] },
        this.playwrightManager,
        this.storageManager
      );

      // Create tools from configuration
      await betterUI.createToolsFromConfig(config);

      this.betterUIIntegrations.set(name, betterUI);
      this.logger.debug(`Better-UI integration initialized: ${name}`);

    } catch (error) {
      this.logger.error(`Failed to initialize Better-UI integration for ${name}:`, error);
      throw error;
    }
  }

  private setupEventHandlers(): void {
    // Configuration loader events
    this.configLoader.on('configChanged', async (name, config) => {
      this.logger.info(`Configuration changed: ${name}`);
      try {
        await this.initializeBetterUIIntegration(name, config);
        this.emit('configurationUpdated', name, config);
      } catch (error) {
        this.logger.error(`Failed to update integration for changed config ${name}:`, error);
      }
    });

    this.configLoader.on('configRemoved', (name) => {
      this.logger.info(`Configuration removed: ${name}`);
      this.betterUIIntegrations.delete(name);
      this.emit('configurationRemoved', name);
    });

    // Playwright manager events
    this.playwrightManager.on('instanceCreated', (instance) => {
      this.logger.debug(`Browser instance created: ${instance.id}`);
    });

    this.playwrightManager.on('instanceClosed', (instanceId) => {
      this.logger.debug(`Browser instance closed: ${instanceId}`);
    });
  }

  private validateRequest(request: ChatRequest): void {
    if (!request.interface) {
      throw new ChatInterfaceManagerError(
        'Interface name is required',
        'INVALID_REQUEST'
      );
    }

    if (!request.action) {
      throw new ChatInterfaceManagerError(
        'Action is required',
        'INVALID_REQUEST'
      );
    }

    if (request.payload === undefined) {
      throw new ChatInterfaceManagerError(
        'Payload is required',
        'INVALID_REQUEST'
      );
    }
  }

  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}