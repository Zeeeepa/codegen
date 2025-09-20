#!/usr/bin/env bun

import { join } from 'path';
import express from 'express';
import { createServer } from 'http';
import { WebSocketServer } from 'ws';
import cors from 'cors';
import helmet from 'helmet';
import { config as loadEnv } from 'dotenv';

import { ChatInterfaceManager, ChatInterfaceManagerOptions } from '../middleware/chat-interface-manager.js';
import { Logger } from '../utils/logger.js';
import { createAPIRouter } from '../api/routes.js';
import { createWebSocketHandler } from '../api/websocket.js';
import { HealthCheckService } from '../monitoring/health-check.js';

// Load environment variables
loadEnv();

export interface ServerConfig {
  port: number;
  host: string;
  configDir: string;
  storageDir: string;
  enableCors: boolean;
  enableSecurity: boolean;
  enableWebSocket: boolean;
  logLevel: 'error' | 'warn' | 'info' | 'debug';
}

export class ChatInterfaceMiddlewareServer {
  private app: express.Application;
  private server: any;
  private wsServer?: WebSocketServer;
  private manager: ChatInterfaceManager;
  private healthCheck: HealthCheckService;
  private logger: Logger;
  private isRunning = false;

  constructor(private config: ServerConfig) {
    this.logger = new Logger('MiddlewareServer', {
      level: config.logLevel,
      file: process.env.LOG_FILE,
      console: true
    });

    this.app = express();
    this.setupMiddleware();
    this.initializeManager();
    this.setupRoutes();
    this.healthCheck = new HealthCheckService(this.manager);
  }

  private setupMiddleware(): void {
    // Security middleware
    if (this.config.enableSecurity) {
      this.app.use(helmet());
    }

    // CORS middleware
    if (this.config.enableCors) {
      this.app.use(cors({
        origin: process.env.CORS_ORIGIN || '*',
        methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allowedHeaders: ['Content-Type', 'Authorization', 'X-Request-ID'],
        credentials: true
      }));
    }

    // Body parsing middleware
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));

    // Request logging middleware
    this.app.use((req, res, next) => {
      const start = Date.now();
      const requestId = req.headers['x-request-id'] || `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      req.requestId = requestId as string;
      
      res.on('finish', () => {
        const duration = Date.now() - start;
        this.logger.request(req.method, req.url, res.statusCode, duration);
      });

      next();
    });
  }

  private initializeManager(): void {
    const managerOptions: ChatInterfaceManagerOptions = {
      configDir: this.config.configDir,
      storage: {
        baseDir: this.config.storageDir,
        enableEncryption: process.env.ENABLE_ENCRYPTION === 'true',
        encryptionKey: process.env.ENCRYPTION_KEY,
        maxFileSize: parseInt(process.env.MAX_FILE_SIZE || '52428800'), // 50MB
      },
      playwright: {
        maxConcurrentBrowsers: parseInt(process.env.MAX_CONCURRENT_BROWSERS || '5'),
        browserIdleTimeout: parseInt(process.env.BROWSER_IDLE_TIMEOUT || '300000'), // 5 minutes
        enableTracing: process.env.ENABLE_TRACING === 'true',
        tracingDir: process.env.TRACING_DIR || './traces',
      },
      enableHotReload: process.env.ENABLE_HOT_RELOAD !== 'false',
    };

    this.manager = new ChatInterfaceManager(managerOptions);

    // Setup manager event handlers
    this.manager.on('initialized', (data) => {
      this.logger.info(`Manager initialized with ${data.configCount} configurations`);
    });

    this.manager.on('requestProcessed', (request, response) => {
      this.logger.performance(`Request ${request.action}`, response.metadata.duration);
    });

    this.manager.on('requestFailed', (request, response, error) => {
      this.logger.error(`Request failed: ${request.action}`, { 
        requestId: response.metadata.requestId,
        error: error.message 
      });
    });
  }

  private setupRoutes(): void {
    // Health check endpoint
    this.app.get('/health', async (req, res) => {
      try {
        const health = await this.healthCheck.getHealthStatus();
        res.status(health.status === 'healthy' ? 200 : 503).json(health);
      } catch (error) {
        res.status(503).json({
          status: 'unhealthy',
          error: error.message,
          timestamp: new Date().toISOString()
        });
      }
    });

    // API routes
    const apiRouter = createAPIRouter(this.manager, this.logger);
    this.app.use('/api', apiRouter);

    // Interface-specific health checks
    this.app.get('/health/:interface', async (req, res) => {
      try {
        const interfaceName = req.params.interface;
        const health = await this.healthCheck.checkInterface(interfaceName);
        res.status(health.healthy ? 200 : 503).json(health);
      } catch (error) {
        res.status(503).json({
          healthy: false,
          error: error.message,
          timestamp: new Date().toISOString()
        });
      }
    });

    // Metrics endpoint
    this.app.get('/metrics', async (req, res) => {
      try {
        const stats = await this.manager.getStats();
        const health = await this.healthCheck.getHealthStatus();
        
        res.json({
          ...stats,
          health: health.status,
          uptime: process.uptime(),
          memory: process.memoryUsage(),
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({
        error: 'Not Found',
        path: req.originalUrl,
        method: req.method,
        timestamp: new Date().toISOString()
      });
    });

    // Error handler
    this.app.use((error: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
      this.logger.error('Unhandled error:', error);
      
      res.status(error.status || 500).json({
        error: error.message || 'Internal Server Error',
        requestId: req.requestId,
        timestamp: new Date().toISOString(),
        ...(process.env.NODE_ENV === 'development' && { stack: error.stack })
      });
    });
  }

  async start(): Promise<void> {
    if (this.isRunning) {
      this.logger.warn('Server is already running');
      return;
    }

    try {
      this.logger.info('Starting Chat Interface Middleware Server');

      // Initialize the manager
      await this.manager.initialize();

      // Create HTTP server
      this.server = createServer(this.app);

      // Setup WebSocket if enabled
      if (this.config.enableWebSocket) {
        this.setupWebSocket();
      }

      // Start listening
      await new Promise<void>((resolve, reject) => {
        this.server.listen(this.config.port, this.config.host, () => {
          resolve();
        });
        
        this.server.on('error', reject);
      });

      this.isRunning = true;

      this.logger.info(`Server started successfully`, {
        host: this.config.host,
        port: this.config.port,
        configDir: this.config.configDir,
        storageDir: this.config.storageDir,
        webSocket: this.config.enableWebSocket
      });

      // Setup graceful shutdown
      this.setupGracefulShutdown();

    } catch (error) {
      this.logger.error('Failed to start server:', error);
      throw error;
    }
  }

  private setupWebSocket(): void {
    this.wsServer = new WebSocketServer({ server: this.server });
    const wsHandler = createWebSocketHandler(this.manager, this.logger);

    this.wsServer.on('connection', (ws, request) => {
      this.logger.info('WebSocket connection established', {
        url: request.url,
        headers: request.headers
      });

      wsHandler(ws, request);
    });

    this.logger.info('WebSocket server enabled');
  }

  private setupGracefulShutdown(): void {
    const shutdown = async (signal: string) => {
      this.logger.info(`Received ${signal}, starting graceful shutdown`);
      
      try {
        await this.stop();
        process.exit(0);
      } catch (error) {
        this.logger.error('Error during shutdown:', error);
        process.exit(1);
      }
    };

    process.on('SIGTERM', () => shutdown('SIGTERM'));
    process.on('SIGINT', () => shutdown('SIGINT'));
    process.on('SIGUSR2', () => shutdown('SIGUSR2')); // For nodemon
  }

  async stop(): Promise<void> {
    if (!this.isRunning) {
      return;
    }

    this.logger.info('Stopping Chat Interface Middleware Server');

    try {
      // Close WebSocket server
      if (this.wsServer) {
        this.wsServer.close();
      }

      // Close HTTP server
      if (this.server) {
        await new Promise<void>((resolve, reject) => {
          this.server.close((error: any) => {
            if (error) reject(error);
            else resolve();
          });
        });
      }

      // Cleanup manager
      await this.manager.cleanup();

      this.isRunning = false;
      this.logger.info('Server stopped successfully');

    } catch (error) {
      this.logger.error('Error stopping server:', error);
      throw error;
    }
  }

  getManager(): ChatInterfaceManager {
    return this.manager;
  }

  isServerRunning(): boolean {
    return this.isRunning;
  }
}

// Main entry point
async function main() {
  const config: ServerConfig = {
    port: parseInt(process.env.PORT || '3000'),
    host: process.env.HOST || '0.0.0.0',
    configDir: process.env.CONFIG_DIR || join(process.cwd(), 'configs'),
    storageDir: process.env.STORAGE_DIR || join(process.cwd(), 'storage'),
    enableCors: process.env.ENABLE_CORS !== 'false',
    enableSecurity: process.env.ENABLE_SECURITY !== 'false',
    enableWebSocket: process.env.ENABLE_WEBSOCKET !== 'false',
    logLevel: (process.env.LOG_LEVEL as any) || 'info',
  };

  const server = new ChatInterfaceMiddlewareServer(config);

  try {
    await server.start();
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Export for programmatic use
export { ChatInterfaceMiddlewareServer };

// Run if this is the main module
if (import.meta.main) {
  main().catch(console.error);
}

// Add request ID to express request type
declare global {
  namespace Express {
    interface Request {
      requestId: string;
    }
  }
}