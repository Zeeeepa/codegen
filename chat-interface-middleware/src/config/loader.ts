import { promises as fs } from 'fs';
import { join, dirname } from 'path';
import { parse as parseYAML } from 'yaml';
import { watch } from 'chokidar';
import { EventEmitter } from 'events';
import { 
  ChatInterfaceConfig, 
  validateConfig, 
  getConfigErrors 
} from '../schemas/config.js';
import { Logger } from '../utils/logger.js';

export interface ConfigLoaderOptions {
  configDir: string;
  enableHotReload?: boolean;
  watchPatterns?: string[];
  encoding?: BufferEncoding;
}

export class ConfigurationError extends Error {
  constructor(
    message: string,
    public configPath?: string,
    public validationErrors?: any[]
  ) {
    super(message);
    this.name = 'ConfigurationError';
  }
}

export class ConfigLoader extends EventEmitter {
  private configs: Map<string, ChatInterfaceConfig> = new Map();
  private watchers: Map<string, any> = new Map();
  private logger: Logger;

  constructor(private options: ConfigLoaderOptions) {
    super();
    this.logger = new Logger('ConfigLoader');
    
    if (this.options.enableHotReload) {
      this.setupHotReload();
    }
  }

  /**
   * Load a single configuration file
   */
  async loadConfig(configPath: string): Promise<ChatInterfaceConfig> {
    try {
      const fullPath = this.resolveConfigPath(configPath);
      this.logger.info(`Loading configuration from ${fullPath}`);

      const content = await fs.readFile(fullPath, this.options.encoding || 'utf8');
      const rawConfig = parseYAML(content);

      // Validate configuration
      const errors = getConfigErrors(rawConfig);
      if (errors) {
        throw new ConfigurationError(
          `Configuration validation failed: ${errors.message}`,
          fullPath,
          errors.errors
        );
      }

      const config = validateConfig(rawConfig);
      
      // Store configuration
      const configName = this.getConfigName(configPath);
      this.configs.set(configName, config);

      this.logger.info(`Successfully loaded configuration: ${configName}`);
      this.emit('configLoaded', configName, config);

      return config;
    } catch (error) {
      if (error instanceof ConfigurationError) {
        throw error;
      }
      
      throw new ConfigurationError(
        `Failed to load configuration: ${error.message}`,
        configPath
      );
    }
  }

  /**
   * Load multiple configuration files from directory
   */
  async loadConfigsFromDirectory(directory?: string): Promise<Map<string, ChatInterfaceConfig>> {
    const configDir = directory || this.options.configDir;
    const configs = new Map<string, ChatInterfaceConfig>();

    try {
      const files = await fs.readdir(configDir);
      const yamlFiles = files.filter(file => 
        file.endsWith('.yaml') || file.endsWith('.yml')
      );

      this.logger.info(`Found ${yamlFiles.length} configuration files in ${configDir}`);

      for (const file of yamlFiles) {
        try {
          const configPath = join(configDir, file);
          const config = await this.loadConfig(configPath);
          const configName = this.getConfigName(file);
          configs.set(configName, config);
        } catch (error) {
          this.logger.error(`Failed to load config ${file}:`, error);
          // Continue loading other configs
        }
      }

      this.configs = configs;
      return configs;
    } catch (error) {
      throw new ConfigurationError(
        `Failed to load configurations from directory: ${error.message}`,
        configDir
      );
    }
  }

  /**
   * Get a specific configuration by name
   */
  getConfig(name: string): ChatInterfaceConfig | undefined {
    return this.configs.get(name);
  }

  /**
   * Get all loaded configurations
   */
  getAllConfigs(): Map<string, ChatInterfaceConfig> {
    return new Map(this.configs);
  }

  /**
   * Reload a specific configuration
   */
  async reloadConfig(configName: string): Promise<ChatInterfaceConfig> {
    const configPath = join(this.options.configDir, `${configName}.yaml`);
    return await this.loadConfig(configPath);
  }

  /**
   * Validate a configuration without loading it
   */
  async validateConfigFile(configPath: string): Promise<{
    valid: boolean;
    errors?: any[];
    config?: ChatInterfaceConfig;
  }> {
    try {
      const fullPath = this.resolveConfigPath(configPath);
      const content = await fs.readFile(fullPath, 'utf8');
      const rawConfig = parseYAML(content);

      const errors = getConfigErrors(rawConfig);
      if (errors) {
        return {
          valid: false,
          errors: errors.errors
        };
      }

      const config = validateConfig(rawConfig);
      return {
        valid: true,
        config
      };
    } catch (error) {
      return {
        valid: false,
        errors: [{ message: error.message }]
      };
    }
  }

  /**
   * Setup hot reload functionality
   */
  private setupHotReload(): void {
    const patterns = this.options.watchPatterns || [
      join(this.options.configDir, '**/*.yaml'),
      join(this.options.configDir, '**/*.yml')
    ];

    this.logger.info('Setting up hot reload for configuration files');

    const watcher = watch(patterns, {
      ignored: /node_modules/,
      persistent: true,
      ignoreInitial: true
    });

    watcher
      .on('change', async (filePath) => {
        this.logger.info(`Configuration file changed: ${filePath}`);
        await this.handleFileChange(filePath);
      })
      .on('add', async (filePath) => {
        this.logger.info(`New configuration file added: ${filePath}`);
        await this.handleFileChange(filePath);
      })
      .on('unlink', (filePath) => {
        this.logger.info(`Configuration file removed: ${filePath}`);
        this.handleFileRemoval(filePath);
      })
      .on('error', (error) => {
        this.logger.error('Configuration watcher error:', error);
        this.emit('watchError', error);
      });

    this.watchers.set('main', watcher);
  }

  /**
   * Handle configuration file changes
   */
  private async handleFileChange(filePath: string): Promise<void> {
    try {
      const config = await this.loadConfig(filePath);
      const configName = this.getConfigName(filePath);
      
      this.emit('configChanged', configName, config);
      this.logger.info(`Configuration reloaded: ${configName}`);
    } catch (error) {
      this.logger.error(`Failed to reload configuration ${filePath}:`, error);
      this.emit('configError', filePath, error);
    }
  }

  /**
   * Handle configuration file removal
   */
  private handleFileRemoval(filePath: string): void {
    const configName = this.getConfigName(filePath);
    this.configs.delete(configName);
    this.emit('configRemoved', configName);
    this.logger.info(`Configuration removed: ${configName}`);
  }

  /**
   * Resolve configuration path
   */
  private resolveConfigPath(configPath: string): string {
    if (configPath.startsWith('/')) {
      return configPath;
    }
    return join(this.options.configDir, configPath);
  }

  /**
   * Extract configuration name from path
   */
  private getConfigName(configPath: string): string {
    const basename = configPath.split('/').pop() || configPath;
    return basename.replace(/\.(yaml|yml)$/, '');
  }

  /**
   * Clean up watchers and resources
   */
  async cleanup(): Promise<void> {
    this.logger.info('Cleaning up configuration loader');
    
    for (const [name, watcher] of this.watchers) {
      await watcher.close();
      this.logger.debug(`Closed watcher: ${name}`);
    }
    
    this.watchers.clear();
    this.configs.clear();
    this.removeAllListeners();
  }

  /**
   * Create a new configuration file
   */
  async createConfig(
    configName: string, 
    config: ChatInterfaceConfig
  ): Promise<string> {
    const configPath = join(this.options.configDir, `${configName}.yaml`);
    
    // Ensure directory exists
    await fs.mkdir(dirname(configPath), { recursive: true });
    
    // Convert config to YAML
    const yamlContent = this.configToYAML(config);
    
    // Write file
    await fs.writeFile(configPath, yamlContent, 'utf8');
    
    this.logger.info(`Created configuration: ${configPath}`);
    return configPath;
  }

  /**
   * Update an existing configuration file
   */
  async updateConfig(
    configName: string, 
    updates: Partial<ChatInterfaceConfig>
  ): Promise<ChatInterfaceConfig> {
    const existingConfig = this.getConfig(configName);
    if (!existingConfig) {
      throw new ConfigurationError(`Configuration not found: ${configName}`);
    }

    const updatedConfig = { ...existingConfig, ...updates };
    const configPath = join(this.options.configDir, `${configName}.yaml`);
    const yamlContent = this.configToYAML(updatedConfig);
    
    await fs.writeFile(configPath, yamlContent, 'utf8');
    
    this.configs.set(configName, updatedConfig);
    this.emit('configUpdated', configName, updatedConfig);
    
    return updatedConfig;
  }

  /**
   * Convert configuration object to YAML string
   */
  private configToYAML(config: ChatInterfaceConfig): string {
    // Note: This would need a proper YAML stringifier
    // Using JSON.stringify for now, but should use yaml.stringify
    return JSON.stringify(config, null, 2);
  }
}