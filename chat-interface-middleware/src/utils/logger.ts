import winston from 'winston';
import { join } from 'path';

export interface LoggerConfig {
  level?: 'error' | 'warn' | 'info' | 'debug';
  file?: string;
  console?: boolean;
  format?: 'simple' | 'json' | 'detailed';
  maxFiles?: number;
  maxSize?: string;
}

export class Logger {
  private winston: winston.Logger;
  private context: string;

  constructor(context: string = 'App', config: LoggerConfig = {}) {
    this.context = context;
    this.winston = this.createLogger(config);
  }

  private createLogger(config: LoggerConfig): winston.Logger {
    const formats = [];

    // Add timestamp
    formats.push(winston.format.timestamp());

    // Add context and formatting based on config
    switch (config.format || 'detailed') {
      case 'simple':
        formats.push(winston.format.simple());
        break;
      case 'json':
        formats.push(winston.format.json());
        break;
      case 'detailed':
      default:
        formats.push(
          winston.format.printf(({ timestamp, level, message, context, ...meta }) => {
            let log = `${timestamp} [${level.toUpperCase()}] [${context || this.context}]: ${message}`;
            if (Object.keys(meta).length > 0) {
              log += `\\n${JSON.stringify(meta, null, 2)}`;
            }
            return log;
          })
        );
    }

    const transports: winston.transport[] = [];

    // Console transport
    if (config.console !== false) {
      transports.push(
        new winston.transports.Console({
          format: winston.format.combine(
            winston.format.colorize(),
            ...formats
          )
        })
      );
    }

    // File transport
    if (config.file) {
      transports.push(
        new winston.transports.File({
          filename: config.file,
          format: winston.format.combine(...formats),
          maxFiles: config.maxFiles || 5,
          maxsize: config.maxSize ? this.parseSize(config.maxSize) : 10 * 1024 * 1024, // 10MB
          tailable: true
        })
      );
    }

    return winston.createLogger({
      level: config.level || 'info',
      transports,
      handleExceptions: true,
      exitOnError: false
    });
  }

  private parseSize(size: string): number {
    const units = {
      'B': 1,
      'KB': 1024,
      'MB': 1024 * 1024,
      'GB': 1024 * 1024 * 1024
    };

    const match = size.match(/^(\\d+)([A-Z]{1,2})$/i);
    if (!match) return 10 * 1024 * 1024; // Default 10MB

    const [, num, unit] = match;
    return parseInt(num) * (units[unit.toUpperCase() as keyof typeof units] || 1);
  }

  // Logging methods
  error(message: string, ...meta: any[]): void {
    this.winston.error(message, { context: this.context, ...this.processMeta(meta) });
  }

  warn(message: string, ...meta: any[]): void {
    this.winston.warn(message, { context: this.context, ...this.processMeta(meta) });
  }

  info(message: string, ...meta: any[]): void {
    this.winston.info(message, { context: this.context, ...this.processMeta(meta) });
  }

  debug(message: string, ...meta: any[]): void {
    this.winston.debug(message, { context: this.context, ...this.processMeta(meta) });
  }

  // Specialized logging methods
  request(method: string, url: string, statusCode?: number, responseTime?: number): void {
    this.info(`${method} ${url}`, {
      type: 'request',
      method,
      url,
      statusCode,
      responseTime: responseTime ? `${responseTime}ms` : undefined
    });
  }

  performance(operation: string, duration: number, ...meta: any[]): void {
    this.info(`Performance: ${operation} completed in ${duration}ms`, {
      type: 'performance',
      operation,
      duration,
      ...this.processMeta(meta)
    });
  }

  security(event: string, details: any = {}): void {
    this.warn(`Security event: ${event}`, {
      type: 'security',
      event,
      ...details
    });
  }

  automation(action: string, interfaceName: string, success: boolean, ...meta: any[]): void {
    const level = success ? 'info' : 'error';
    this[level](`Automation ${action} on ${interfaceName}: ${success ? 'SUCCESS' : 'FAILED'}`, {
      type: 'automation',
      action,
      interface: interfaceName,
      success,
      ...this.processMeta(meta)
    });
  }

  config(message: string, configName?: string, ...meta: any[]): void {
    this.info(`Config: ${message}`, {
      type: 'config',
      configName,
      ...this.processMeta(meta)
    });
  }

  // Utility methods
  private processMeta(meta: any[]): any {
    if (meta.length === 0) return {};
    if (meta.length === 1 && typeof meta[0] === 'object') {
      return meta[0];
    }
    return { meta };
  }

  // Create child logger with additional context
  child(context: string, additionalConfig?: Partial<LoggerConfig>): Logger {
    const fullContext = `${this.context}:${context}`;
    return new Logger(fullContext, additionalConfig);
  }

  // Get underlying Winston instance for advanced usage
  getWinstonLogger(): winston.Logger {
    return this.winston;
  }

  // Update logger configuration
  updateConfig(config: Partial<LoggerConfig>): void {
    if (config.level) {
      this.winston.level = config.level;
    }
    // Note: For more complex config updates, might need to recreate logger
  }
}

// Global logger instance
export const logger = new Logger('ChatInterfaceMiddleware', {
  level: (process.env.LOG_LEVEL as any) || 'info',
  file: process.env.LOG_FILE ? join(process.cwd(), process.env.LOG_FILE) : undefined,
  console: process.env.LOG_CONSOLE !== 'false'
});

// Export logger creation utility
export const createLogger = (context: string, config?: LoggerConfig): Logger => {
  return new Logger(context, config);
};