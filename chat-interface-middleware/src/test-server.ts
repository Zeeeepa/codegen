#!/usr/bin/env node

// Simple test server without complex dependencies
import express from 'express';
import { readFileSync, readdirSync } from 'fs';
import { parse as parseYAML } from 'yaml';

const app = express();
const port = process.env.PORT || 3333;

// Middleware
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    service: 'Chat Interface Middleware',
    version: '1.0.0'
  });
});

// List interfaces endpoint
app.get('/api/interfaces', (req, res) => {
  try {
    const configFiles = readdirSync('./configs/examples').filter(f => 
      f.endsWith('.yaml') || f.endsWith('.yml')
    );

    const interfaces = configFiles.map(file => {
      try {
        const content = readFileSync(`./configs/examples/${file}`, 'utf8');
        const config = parseYAML(content);
        
        return {
          name: config.interface?.name || 'unknown',
          file: file,
          url: config.interface?.url,
          description: config.metadata?.description,
          tools: config.tools?.length || 0,
          available_actions: config.tools?.map((tool: any) => tool.name) || []
        };
      } catch (error) {
        return {
          name: file.replace(/\.(yaml|yml)$/, ''),
          file: file,
          error: 'Parse error',
          tools: 0
        };
      }
    });

    res.json({
      success: true,
      data: {
        count: interfaces.length,
        interfaces
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Get specific interface
app.get('/api/interfaces/:name', (req, res) => {
  try {
    const { name } = req.params;
    const configFiles = readdirSync('./configs/examples');
    
    // Find config file by interface name
    let configFile = null;
    let config = null;
    
    for (const file of configFiles) {
      if (file.endsWith('.yaml') || file.endsWith('.yml')) {
        try {
          const content = readFileSync(`./configs/examples/${file}`, 'utf8');
          const parsed = parseYAML(content);
          if (parsed.interface?.name === name) {
            configFile = file;
            config = parsed;
            break;
          }
        } catch (error) {
          continue;
        }
      }
    }
    
    if (!config) {
      return res.status(404).json({
        success: false,
        error: `Interface not found: ${name}`
      });
    }

    res.json({
      success: true,
      data: {
        name,
        file: configFile,
        config: {
          metadata: config.metadata,
          interface: {
            name: config.interface.name,
            url: config.interface.url,
            selectors: config.interface.selectors,
            auth: config.interface.auth ? {
              type: config.interface.auth.type
            } : undefined
          },
          tools: config.tools.map((tool: any) => ({
            name: tool.name,
            description: tool.description,
            input: tool.input,
          })),
          automation: config.automation,
        },
        available_actions: config.tools?.map((tool: any) => tool.name) || [],
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Mock action execution endpoint
app.post('/api/interfaces/:name/actions/:action', (req, res) => {
  const { name: interfaceName, action } = req.params;
  const { payload = {} } = req.body;
  const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  console.log(`🎯 Mock execution: ${action} on ${interfaceName}`);
  console.log(`   Payload:`, payload);

  // Mock successful response
  res.json({
    success: true,
    data: {
      action,
      interface: interfaceName,
      payload,
      result: {
        status: 'mock_success',
        message: `Mock execution of ${action} completed`,
        timestamp: new Date().toISOString(),
        mock: true
      }
    },
    metadata: {
      requestId,
      timestamp: new Date().toISOString(),
      interface: interfaceName,
      action,
      duration: Math.floor(Math.random() * 1000) + 100, // Random duration 100-1100ms
    }
  });
});

// Stats endpoint
app.get('/api/stats', (req, res) => {
  try {
    const configFiles = readdirSync('./configs/examples').filter(f => 
      f.endsWith('.yaml') || f.endsWith('.yml')
    );

    res.json({
      success: true,
      data: {
        interfaces: configFiles.length,
        activeInstances: 0, // Mock
        storage: {
          totalItems: 0,
          totalSize: 0
        },
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        timestamp: new Date().toISOString(),
        mode: 'test'
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Not Found',
    path: req.originalUrl,
    method: req.method,
    timestamp: new Date().toISOString(),
    available_endpoints: [
      'GET /health',
      'GET /api/interfaces', 
      'GET /api/interfaces/:name',
      'POST /api/interfaces/:name/actions/:action',
      'GET /api/stats'
    ]
  });
});

// Error handler
app.use((error: any, req: any, res: any, next: any) => {
  console.error('Server error:', error);
  res.status(error.status || 500).json({
    error: error.message || 'Internal Server Error',
    timestamp: new Date().toISOString(),
  });
});

// Start server
const server = app.listen(port, () => {
  console.log('🚀 Chat Interface Middleware Test Server');
  console.log(`📍 Server running at: http://localhost:${port}`);
  console.log('📋 Available endpoints:');
  console.log('   GET  /health');
  console.log('   GET  /api/interfaces');
  console.log('   GET  /api/interfaces/:name');
  console.log('   POST /api/interfaces/:name/actions/:action');
  console.log('   GET  /api/stats');
  console.log('');
  console.log('🧪 Test the API:');
  console.log(`   curl http://localhost:${port}/health`);
  console.log(`   curl http://localhost:${port}/api/interfaces`);
  console.log('');
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('🛑 Received SIGTERM, shutting down gracefully');
  server.close(() => {
    console.log('✅ Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('\n🛑 Received SIGINT (Ctrl+C), shutting down gracefully');
  server.close(() => {
    console.log('✅ Server closed');
    process.exit(0);
  });
});

export default app;