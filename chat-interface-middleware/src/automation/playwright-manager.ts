import { 
  Browser, 
  BrowserContext, 
  Page, 
  chromium, 
  firefox, 
  webkit,
  BrowserType,
  Cookie
} from 'playwright';
import { EventEmitter } from 'events';
import { Logger } from '../../utils/logger.js';
import { 
  AutomationConfig, 
  InterfaceConfig, 
  AuthConfig 
} from '../../schemas/config.js';

export interface BrowserInstance {
  id: string;
  browser: Browser;
  context: BrowserContext;
  page: Page;
  interfaceConfig: InterfaceConfig;
  createdAt: Date;
  lastUsed: Date;
}

export interface PlaywrightManagerOptions {
  maxConcurrentBrowsers?: number;
  browserIdleTimeout?: number;
  defaultBrowserType?: 'chromium' | 'firefox' | 'webkit';
  enableTracing?: boolean;
  tracingDir?: string;
}

export class PlaywrightManagerError extends Error {
  constructor(message: string, public cause?: Error) {
    super(message);
    this.name = 'PlaywrightManagerError';
  }
}

export class PlaywrightManager extends EventEmitter {
  private instances: Map<string, BrowserInstance> = new Map();
  private logger: Logger;
  private cleanupInterval: NodeJS.Timeout | null = null;

  constructor(private options: PlaywrightManagerOptions = {}) {
    super();
    this.logger = new Logger('PlaywrightManager');
    this.setupCleanup();
  }

  /**
   * Create a new browser instance for an interface
   */
  async createInstance(
    interfaceConfig: InterfaceConfig,
    automationConfig?: AutomationConfig
  ): Promise<BrowserInstance> {
    const instanceId = this.generateInstanceId(interfaceConfig.name);
    
    try {
      this.logger.info(`Creating browser instance for interface: ${interfaceConfig.name}`);

      // Check concurrent browser limit
      if (this.instances.size >= (this.options.maxConcurrentBrowsers || 10)) {
        await this.cleanupIdleInstances();
        
        if (this.instances.size >= (this.options.maxConcurrentBrowsers || 10)) {
          throw new PlaywrightManagerError(
            'Maximum concurrent browser limit reached'
          );
        }
      }

      // Get browser type
      const browserType = this.getBrowserType(
        automationConfig?.browser || this.options.defaultBrowserType || 'chromium'
      );

      // Launch browser
      const browser = await browserType.launch({
        headless: automationConfig?.headless ?? false,
        args: this.getBrowserArgs(automationConfig),
      });

      // Create context with configuration
      const contextOptions: any = {
        viewport: automationConfig?.viewport || { width: 1280, height: 720 },
        userAgent: this.getUserAgent(),
      };

      // Add proxy if configured
      if (interfaceConfig.network?.proxy) {
        contextOptions.proxy = {
          server: interfaceConfig.network.proxy
        };
      }

      const context = await browser.newContext(contextOptions);

      // Enable tracing if configured
      if (this.options.enableTracing) {
        await context.tracing.start({ 
          screenshots: true, 
          snapshots: true,
          sources: true
        });
      }

      // Load cookies if specified
      if (automationConfig?.cookies?.load_from) {
        await this.loadCookies(context, automationConfig.cookies.load_from);
      }

      // Create page
      const page = await context.newPage();

      // Navigate to interface URL
      await page.goto(interfaceConfig.url, { 
        waitUntil: 'networkidle',
        timeout: interfaceConfig.network?.timeout || 30000
      });

      // Perform authentication if required
      if (interfaceConfig.auth) {
        await this.authenticate(page, interfaceConfig.auth);
      }

      // Create instance record
      const instance: BrowserInstance = {
        id: instanceId,
        browser,
        context,
        page,
        interfaceConfig,
        createdAt: new Date(),
        lastUsed: new Date(),
      };

      this.instances.set(instanceId, instance);

      this.logger.info(`Browser instance created successfully: ${instanceId}`);
      this.emit('instanceCreated', instance);

      return instance;
    } catch (error) {
      this.logger.error(`Failed to create browser instance: ${error.message}`);
      throw new PlaywrightManagerError(
        `Failed to create browser instance for ${interfaceConfig.name}`,
        error as Error
      );
    }
  }

  /**
   * Get an existing instance or create a new one
   */
  async getInstance(
    interfaceConfigName: string,
    interfaceConfig?: InterfaceConfig,
    automationConfig?: AutomationConfig
  ): Promise<BrowserInstance> {
    // Look for existing instance
    const existingInstance = Array.from(this.instances.values())
      .find(instance => instance.interfaceConfig.name === interfaceConfigName);

    if (existingInstance) {
      existingInstance.lastUsed = new Date();
      this.logger.debug(`Reusing existing instance: ${existingInstance.id}`);
      return existingInstance;
    }

    // Create new instance if interface config provided
    if (!interfaceConfig) {
      throw new PlaywrightManagerError(
        `No existing instance found and no interface config provided for: ${interfaceConfigName}`
      );
    }

    return await this.createInstance(interfaceConfig, automationConfig);
  }

  /**
   * Execute automation action on an interface
   */
  async executeAction(
    instanceId: string,
    action: AutomationAction
  ): Promise<AutomationResult> {
    const instance = this.instances.get(instanceId);
    if (!instance) {
      throw new PlaywrightManagerError(`Instance not found: ${instanceId}`);
    }

    instance.lastUsed = new Date();

    try {
      this.logger.debug(`Executing action ${action.type} on instance ${instanceId}`);

      const result = await this.performAction(instance, action);
      
      this.logger.debug(`Action ${action.type} completed successfully`);
      this.emit('actionExecuted', instanceId, action, result);

      return result;
    } catch (error) {
      this.logger.error(`Action ${action.type} failed:`, error);
      this.emit('actionFailed', instanceId, action, error);
      throw error;
    }
  }

  /**
   * Perform specific automation action
   */
  private async performAction(
    instance: BrowserInstance,
    action: AutomationAction
  ): Promise<AutomationResult> {
    const { page } = instance;

    switch (action.type) {
      case 'sendMessage':
        return await this.sendMessage(page, action);

      case 'click':
        await page.click(action.selector, action.options);
        return { success: true, action: action.type };

      case 'fill':
        await page.fill(action.selector, action.value, action.options);
        return { success: true, action: action.type };

      case 'screenshot':
        const screenshot = await page.screenshot(action.options);
        return { 
          success: true, 
          action: action.type, 
          data: { screenshot: screenshot.toString('base64') }
        };

      case 'waitForSelector':
        await page.waitForSelector(action.selector, action.options);
        return { success: true, action: action.type };

      case 'waitForResponse':
        const response = await page.waitForResponse(action.urlPattern, action.options);
        return { 
          success: true, 
          action: action.type, 
          data: { status: response.status(), url: response.url() }
        };

      case 'evaluate':
        const result = await page.evaluate(action.script);
        return { 
          success: true, 
          action: action.type, 
          data: { result }
        };

      case 'saveCookies':
        const cookies = await instance.context.cookies();
        return { 
          success: true, 
          action: action.type, 
          data: { cookies }
        };

      default:
        throw new Error(`Unknown action type: ${(action as any).type}`);
    }
  }

  /**
   * Send message to chat interface
   */
  private async sendMessage(page: Page, action: SendMessageAction): Promise<AutomationResult> {
    const { message, selectors, waitForResponse = true } = action;

    // Fill message input
    await page.fill(selectors.text_input, message);
    
    // Click send button
    await page.click(selectors.send_button);

    // Wait for response if requested
    if (waitForResponse && selectors.response_area) {
      await page.waitForSelector(`${selectors.response_area} .new-message`, {
        timeout: 30000
      });
    }

    return {
      success: true,
      action: 'sendMessage',
      data: { message, sent: true }
    };
  }

  /**
   * Authenticate with the interface
   */
  private async authenticate(page: Page, authConfig: AuthConfig): Promise<void> {
    this.logger.info(`Authenticating with method: ${authConfig.type}`);

    switch (authConfig.type) {
      case 'credentials':
        if (authConfig.email && authConfig.password) {
          // Look for common login selectors
          const emailSelectors = ['input[type="email"]', 'input[name="email"]', '#email'];
          const passwordSelectors = ['input[type="password"]', 'input[name="password"]', '#password'];
          const submitSelectors = ['button[type="submit"]', 'input[type="submit"]', '.login-button'];

          for (const selector of emailSelectors) {
            try {
              await page.fill(selector, authConfig.email);
              break;
            } catch (e) {
              continue;
            }
          }

          for (const selector of passwordSelectors) {
            try {
              await page.fill(selector, authConfig.password);
              break;
            } catch (e) {
              continue;
            }
          }

          for (const selector of submitSelectors) {
            try {
              await page.click(selector);
              break;
            } catch (e) {
              continue;
            }
          }

          // Wait for navigation or specific element indicating successful login
          try {
            await page.waitForNavigation({ timeout: 10000 });
          } catch (e) {
            // Navigation might not occur, that's okay
          }
        }
        break;

      case 'oauth':
        if (authConfig.oauth_url) {
          await page.goto(authConfig.oauth_url);
          // OAuth flow would need to be handled manually or with specific selectors
        }
        break;

      case 'token':
        if (authConfig.token) {
          // Add token to local storage or headers
          await page.addInitScript(`
            localStorage.setItem('authToken', '${authConfig.token}');
          `);
        }
        break;

      case 'cookie':
        // Cookies should be loaded via loadCookies method
        break;
    }
  }

  /**
   * Load cookies from file
   */
  private async loadCookies(context: BrowserContext, cookieFile: string): Promise<void> {
    try {
      this.logger.debug(`Loading cookies from: ${cookieFile}`);
      
      // In a real implementation, you'd read from the file system
      // For now, this is a placeholder
      const fs = await import('fs/promises');
      const cookieData = await fs.readFile(cookieFile, 'utf8');
      const cookies: Cookie[] = JSON.parse(cookieData);
      
      await context.addCookies(cookies);
      
      this.logger.debug(`Loaded ${cookies.length} cookies`);
    } catch (error) {
      this.logger.warn(`Failed to load cookies from ${cookieFile}:`, error);
    }
  }

  /**
   * Save cookies to file
   */
  async saveCookies(instanceId: string, cookieFile: string): Promise<void> {
    const instance = this.instances.get(instanceId);
    if (!instance) {
      throw new PlaywrightManagerError(`Instance not found: ${instanceId}`);
    }

    try {
      const cookies = await instance.context.cookies();
      const fs = await import('fs/promises');
      await fs.writeFile(cookieFile, JSON.stringify(cookies, null, 2));
      
      this.logger.info(`Saved ${cookies.length} cookies to: ${cookieFile}`);
    } catch (error) {
      throw new PlaywrightManagerError(`Failed to save cookies: ${error.message}`, error as Error);
    }
  }

  /**
   * Close specific instance
   */
  async closeInstance(instanceId: string): Promise<void> {
    const instance = this.instances.get(instanceId);
    if (!instance) {
      this.logger.warn(`Instance not found for closing: ${instanceId}`);
      return;
    }

    try {
      // Stop tracing if enabled
      if (this.options.enableTracing) {
        await instance.context.tracing.stop({
          path: `${this.options.tracingDir || './traces'}/${instanceId}.zip`
        });
      }

      await instance.context.close();
      await instance.browser.close();
      
      this.instances.delete(instanceId);
      
      this.logger.info(`Closed browser instance: ${instanceId}`);
      this.emit('instanceClosed', instanceId);
    } catch (error) {
      this.logger.error(`Error closing instance ${instanceId}:`, error);
    }
  }

  /**
   * Close all instances
   */
  async closeAllInstances(): Promise<void> {
    this.logger.info(`Closing ${this.instances.size} browser instances`);
    
    const closePromises = Array.from(this.instances.keys()).map(
      instanceId => this.closeInstance(instanceId)
    );
    
    await Promise.allSettled(closePromises);
  }

  /**
   * Clean up idle instances
   */
  private async cleanupIdleInstances(): Promise<void> {
    const idleTimeout = this.options.browserIdleTimeout || 300000; // 5 minutes
    const now = Date.now();
    
    const idleInstances = Array.from(this.instances.entries()).filter(
      ([, instance]) => now - instance.lastUsed.getTime() > idleTimeout
    );
    
    for (const [instanceId] of idleInstances) {
      this.logger.debug(`Cleaning up idle instance: ${instanceId}`);
      await this.closeInstance(instanceId);
    }
  }

  /**
   * Setup periodic cleanup
   */
  private setupCleanup(): void {
    this.cleanupInterval = setInterval(() => {
      this.cleanupIdleInstances().catch(error => {
        this.logger.error('Error during cleanup:', error);
      });
    }, 60000); // Check every minute
  }

  /**
   * Generate unique instance ID
   */
  private generateInstanceId(interfaceName: string): string {
    return `${interfaceName}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get browser type instance
   */
  private getBrowserType(browserName: string): BrowserType {
    switch (browserName) {
      case 'firefox':
        return firefox;
      case 'webkit':
        return webkit;
      case 'chromium':
      default:
        return chromium;
    }
  }

  /**
   * Get browser launch arguments
   */
  private getBrowserArgs(config?: AutomationConfig): string[] {
    const args: string[] = [];
    
    // Add common args for stability
    args.push(
      '--no-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--disable-background-timer-throttling',
      '--disable-backgrounding-occluded-windows',
      '--disable-renderer-backgrounding'
    );

    return args;
  }

  /**
   * Get user agent string
   */
  private getUserAgent(): string {
    return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36';
  }

  /**
   * Get all active instances
   */
  getActiveInstances(): BrowserInstance[] {
    return Array.from(this.instances.values());
  }

  /**
   * Get instance by ID
   */
  getInstanceById(instanceId: string): BrowserInstance | undefined {
    return this.instances.get(instanceId);
  }

  /**
   * Cleanup resources
   */
  async cleanup(): Promise<void> {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
    
    await this.closeAllInstances();
    this.removeAllListeners();
  }
}

// Action types
export interface AutomationAction {
  type: string;
  [key: string]: any;
}

export interface SendMessageAction extends AutomationAction {
  type: 'sendMessage';
  message: string;
  selectors: {
    text_input: string;
    send_button: string;
    response_area?: string;
  };
  waitForResponse?: boolean;
}

export interface AutomationResult {
  success: boolean;
  action: string;
  data?: any;
  error?: Error;
}