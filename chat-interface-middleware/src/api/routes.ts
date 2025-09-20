import { Router } from 'express';
import { ChatInterfaceManager, ChatRequest } from '../../middleware/chat-interface-manager.js';
import { Logger } from '../../utils/logger.js';

export function createAPIRouter(manager: ChatInterfaceManager, logger: Logger): Router {
  const router = Router();

  // Get all available interfaces
  router.get('/interfaces', async (req, res) => {
    try {
      const interfaces = manager.getAvailableInterfaces();
      const interfaceDetails = interfaces.map(name => {
        const config = manager.getInterfaceConfig(name);
        const actions = manager.getAvailableActions(name);
        
        return {
          name,
          url: config?.interface.url,
          description: config?.metadata.description,
          actions: actions.length,
          available_actions: actions,
        };
      });

      res.json({
        success: true,
        data: {
          count: interfaces.length,
          interfaces: interfaceDetails
        }
      });
    } catch (error) {
      logger.error('Error getting interfaces:', error);
      res.status(500).json({
        success: false,
        error: error.message
      });
    }
  });

  // Get specific interface details
  router.get('/interfaces/:name', async (req, res) => {
    try {
      const { name } = req.params;
      const config = manager.getInterfaceConfig(name);
      
      if (!config) {
        return res.status(404).json({
          success: false,
          error: `Interface not found: ${name}`
        });
      }

      const actions = manager.getAvailableActions(name);

      res.json({
        success: true,
        data: {
          name,
          config: {
            metadata: config.metadata,
            interface: {
              name: config.interface.name,
              url: config.interface.url,
              selectors: config.interface.selectors,
            },
            tools: config.tools.map(tool => ({
              name: tool.name,
              description: tool.description,
              input: tool.input,
            })),
            automation: config.automation,
          },
          available_actions: actions,
        }
      });
    } catch (error) {
      logger.error(`Error getting interface ${req.params.name}:`, error);
      res.status(500).json({
        success: false,
        error: error.message
      });
    }
  });

  // Execute action on an interface
  router.post('/interfaces/:name/actions/:action', async (req, res) => {
    try {
      const { name: interfaceName, action } = req.params;
      const { payload = {}, metadata = {} } = req.body;

      const request: ChatRequest = {
        interface: interfaceName,
        action,
        payload,
        metadata: {
          requestId: req.requestId,
          timestamp: new Date().toISOString(),
          source: 'api',
          ...metadata
        }
      };

      const response = await manager.processRequest(request);
      
      res.status(response.success ? 200 : 400).json(response);
    } catch (error) {
      logger.error(`Error executing action ${req.params.action} on ${req.params.name}:`, error);
      res.status(500).json({
        success: false,
        error: error.message,
        metadata: {
          requestId: req.requestId,
          timestamp: new Date().toISOString(),
          interface: req.params.name,
          action: req.params.action,
          duration: 0,
        }
      });
    }
  });

  // Test an interface
  router.post('/interfaces/:name/test', async (req, res) => {
    try {
      const { name } = req.params;
      const { action, payload } = req.body;

      const testResult = await manager.testInterface(name, action, payload);
      
      res.status(testResult.success ? 200 : 503).json({
        success: testResult.success,
        data: testResult
      });
    } catch (error) {
      logger.error(`Error testing interface ${req.params.name}:`, error);
      res.status(500).json({
        success: false,
        error: error.message
      });
    }
  });

  // Reload interface configuration
  router.post('/interfaces/:name/reload', async (req, res) => {
    try {
      const { name } = req.params;
      
      await manager.reloadInterface(name);
      
      res.json({
        success: true,
        message: `Interface ${name} reloaded successfully`
      });
    } catch (error) {
      logger.error(`Error reloading interface ${req.params.name}:`, error);
      res.status(500).json({
        success: false,
        error: error.message
      });
    }
  });

  // Get manager statistics
  router.get('/stats', async (req, res) => {
    try {
      const stats = await manager.getStats();
      
      res.json({
        success: true,
        data: {
          ...stats,
          uptime: process.uptime(),
          memory: process.memoryUsage(),
          timestamp: new Date().toISOString(),
        }
      });
    } catch (error) {
      logger.error('Error getting stats:', error);
      res.status(500).json({
        success: false,
        error: error.message
      });
    }
  });

  // Bulk operation: Execute same action on multiple interfaces
  router.post('/bulk/execute', async (req, res) => {
    try {
      const { interfaces, action, payload, metadata = {} } = req.body;

      if (!Array.isArray(interfaces)) {
        return res.status(400).json({
          success: false,
          error: 'interfaces must be an array'
        });
      }

      const results = await Promise.allSettled(
        interfaces.map(async (interfaceName: string) => {
          const request: ChatRequest = {
            interface: interfaceName,
            action,
            payload,
            metadata: {
              requestId: `${req.requestId}_${interfaceName}`,
              timestamp: new Date().toISOString(),
              source: 'bulk_api',
              ...metadata
            }
          };

          return {
            interface: interfaceName,
            result: await manager.processRequest(request)
          };
        })
      );

      const responses = results.map((result, index) => {
        if (result.status === 'fulfilled') {
          return result.value;
        } else {
          return {
            interface: interfaces[index],
            result: {
              success: false,
              error: {
                message: result.reason.message,
                code: 'BULK_OPERATION_ERROR'
              },
              metadata: {
                requestId: `${req.requestId}_${interfaces[index]}`,
                timestamp: new Date().toISOString(),
                interface: interfaces[index],
                action,
                duration: 0
              }
            }
          };
        }
      });

      const successCount = responses.filter(r => r.result.success).length;

      res.json({
        success: successCount > 0,
        data: {
          total: interfaces.length,
          successful: successCount,
          failed: interfaces.length - successCount,
          results: responses
        }
      });
    } catch (error) {
      logger.error('Error executing bulk operation:', error);
      res.status(500).json({
        success: false,
        error: error.message
      });
    }
  });

  return router;
}