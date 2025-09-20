import { WebSocket } from 'ws';
import { IncomingMessage } from 'http';
import { ChatInterfaceManager, ChatRequest } from '../../middleware/chat-interface-manager.js';
import { Logger } from '../../utils/logger.js';

export interface WebSocketMessage {
  id: string;
  type: 'request' | 'response' | 'error' | 'ping' | 'pong' | 'subscribe' | 'unsubscribe';
  data?: any;
  timestamp: string;
}

export interface WebSocketClient {
  id: string;
  ws: WebSocket;
  subscriptions: Set<string>;
  lastPing: Date;
  connected: Date;
}

export function createWebSocketHandler(manager: ChatInterfaceManager, logger: Logger) {
  const clients = new Map<string, WebSocketClient>();

  // Cleanup interval for dead connections
  const cleanupInterval = setInterval(() => {
    const now = Date.now();
    for (const [clientId, client] of clients) {
      if (now - client.lastPing.getTime() > 60000) { // 1 minute timeout
        logger.debug(`Cleaning up inactive WebSocket client: ${clientId}`);
        client.ws.terminate();
        clients.delete(clientId);
      }
    }
  }, 30000); // Check every 30 seconds

  // Broadcast to subscribed clients
  const broadcast = (event: string, data: any) => {
    const message: WebSocketMessage = {
      id: generateId(),
      type: 'response',
      data: {
        event,
        ...data
      },
      timestamp: new Date().toISOString()
    };

    for (const client of clients.values()) {
      if (client.subscriptions.has(event) && client.ws.readyState === WebSocket.OPEN) {
        try {
          client.ws.send(JSON.stringify(message));
        } catch (error) {
          logger.error(`Error sending message to client ${client.id}:`, error);
        }
      }
    }
  };

  // Setup manager event listeners for broadcasting
  manager.on('requestProcessed', (request, response) => {
    broadcast('requestProcessed', { request, response });
  });

  manager.on('requestFailed', (request, response, error) => {
    broadcast('requestFailed', { request, response, error: error.message });
  });

  manager.on('configurationUpdated', (name, config) => {
    broadcast('configurationUpdated', { interfaceName: name, config });
  });

  manager.on('configurationRemoved', (name) => {
    broadcast('configurationRemoved', { interfaceName: name });
  });

  return (ws: WebSocket, request: IncomingMessage) => {
    const clientId = generateId();
    const client: WebSocketClient = {
      id: clientId,
      ws,
      subscriptions: new Set(),
      lastPing: new Date(),
      connected: new Date(),
    };

    clients.set(clientId, client);
    logger.info(`WebSocket client connected: ${clientId}`);

    // Send welcome message
    const welcomeMessage: WebSocketMessage = {
      id: generateId(),
      type: 'response',
      data: {
        event: 'connected',
        clientId,
        server: 'Chat Interface Middleware',
        version: '1.0.0',
        availableEvents: [
          'requestProcessed',
          'requestFailed', 
          'configurationUpdated',
          'configurationRemoved'
        ]
      },
      timestamp: new Date().toISOString()
    };

    ws.send(JSON.stringify(welcomeMessage));

    // Handle incoming messages
    ws.on('message', async (data: Buffer) => {
      try {
        client.lastPing = new Date();
        
        const message: WebSocketMessage = JSON.parse(data.toString());
        logger.debug(`WebSocket message from ${clientId}:`, message);

        await handleMessage(client, message);
      } catch (error) {
        logger.error(`Error handling WebSocket message from ${clientId}:`, error);
        
        const errorMessage: WebSocketMessage = {
          id: generateId(),
          type: 'error',
          data: {
            error: 'Invalid message format or processing error',
            details: error.message
          },
          timestamp: new Date().toISOString()
        };

        ws.send(JSON.stringify(errorMessage));
      }
    });

    // Handle WebSocket close
    ws.on('close', (code, reason) => {
      logger.info(`WebSocket client disconnected: ${clientId}`, { code, reason: reason.toString() });
      clients.delete(clientId);
    });

    // Handle WebSocket error
    ws.on('error', (error) => {
      logger.error(`WebSocket error for client ${clientId}:`, error);
      clients.delete(clientId);
    });

    // Ping/pong for connection health
    ws.on('pong', () => {
      client.lastPing = new Date();
    });

    // Send periodic pings
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.ping();
      } else {
        clearInterval(pingInterval);
      }
    }, 30000);
  };

  async function handleMessage(client: WebSocketClient, message: WebSocketMessage) {
    const { ws } = client;

    switch (message.type) {
      case 'ping':
        const pongMessage: WebSocketMessage = {
          id: generateId(),
          type: 'pong',
          data: { originalId: message.id },
          timestamp: new Date().toISOString()
        };
        ws.send(JSON.stringify(pongMessage));
        break;

      case 'subscribe':
        if (message.data?.events) {
          for (const event of message.data.events) {
            client.subscriptions.add(event);
          }
          
          const subscribeResponse: WebSocketMessage = {
            id: generateId(),
            type: 'response',
            data: {
              event: 'subscribed',
              events: message.data.events,
              totalSubscriptions: client.subscriptions.size
            },
            timestamp: new Date().toISOString()
          };
          ws.send(JSON.stringify(subscribeResponse));
        }
        break;

      case 'unsubscribe':
        if (message.data?.events) {
          for (const event of message.data.events) {
            client.subscriptions.delete(event);
          }
          
          const unsubscribeResponse: WebSocketMessage = {
            id: generateId(),
            type: 'response',
            data: {
              event: 'unsubscribed',
              events: message.data.events,
              totalSubscriptions: client.subscriptions.size
            },
            timestamp: new Date().toISOString()
          };
          ws.send(JSON.stringify(unsubscribeResponse));
        }
        break;

      case 'request':
        if (message.data?.interface && message.data?.action) {
          try {
            const chatRequest: ChatRequest = {
              interface: message.data.interface,
              action: message.data.action,
              payload: message.data.payload || {},
              metadata: {
                requestId: message.id,
                timestamp: message.timestamp,
                source: 'websocket',
                clientId: client.id,
                ...message.data.metadata
              }
            };

            const response = await manager.processRequest(chatRequest);
            
            const responseMessage: WebSocketMessage = {
              id: generateId(),
              type: 'response',
              data: {
                event: 'requestResponse',
                originalRequestId: message.id,
                response
              },
              timestamp: new Date().toISOString()
            };

            ws.send(JSON.stringify(responseMessage));
          } catch (error) {
            const errorMessage: WebSocketMessage = {
              id: generateId(),
              type: 'error',
              data: {
                event: 'requestError',
                originalRequestId: message.id,
                error: error.message
              },
              timestamp: new Date().toISOString()
            };

            ws.send(JSON.stringify(errorMessage));
          }
        } else {
          const errorMessage: WebSocketMessage = {
            id: generateId(),
            type: 'error',
            data: {
              error: 'Invalid request format. Required: interface, action',
              originalRequestId: message.id
            },
            timestamp: new Date().toISOString()
          };

          ws.send(JSON.stringify(errorMessage));
        }
        break;

      default:
        const unknownMessage: WebSocketMessage = {
          id: generateId(),
          type: 'error',
          data: {
            error: `Unknown message type: ${message.type}`,
            originalRequestId: message.id
          },
          timestamp: new Date().toISOString()
        };

        ws.send(JSON.stringify(unknownMessage));
    }
  }

  function generateId(): string {
    return `ws_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Cleanup function
  process.on('exit', () => {
    clearInterval(cleanupInterval);
  });
}