/**
 * WebSocket Client for Real-time Updates
 * Handles real-time communication with Codegen backend
 */

import { io, Socket } from 'socket.io-client';
import { RealTimeEvent } from '@/types/codegen';

export interface WebSocketConfig {
  url: string;
  token: string;
  organizationId: string;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

export interface WebSocketEventHandlers {
  onConnect?: () => void;
  onDisconnect?: (reason: string) => void;
  onError?: (error: Error) => void;
  onEvent?: (event: RealTimeEvent) => void;
  onAgentRunUpdate?: (data: any) => void;
  onWorkflowUpdate?: (data: any) => void;
  onPRUpdate?: (data: any) => void;
}

class WebSocketClient {
  private socket: Socket | null = null;
  private config: WebSocketConfig | null = null;
  private handlers: WebSocketEventHandlers = {};
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnecting = false;
  private connectionPromise: Promise<void> | null = null;

  constructor() {
    this.handleConnect = this.handleConnect.bind(this);
    this.handleDisconnect = this.handleDisconnect.bind(this);
    this.handleError = this.handleError.bind(this);
    this.handleRealtimeEvent = this.handleRealtimeEvent.bind(this);
  }

  /**
   * Connect to WebSocket server
   */
  async connect(config: WebSocketConfig, handlers: WebSocketEventHandlers = {}): Promise<void> {
    if (this.isConnecting && this.connectionPromise) {
      return this.connectionPromise;
    }

    this.config = config;
    this.handlers = handlers;
    this.maxReconnectAttempts = config.reconnectAttempts || 5;
    this.reconnectDelay = config.reconnectDelay || 1000;

    this.isConnecting = true;
    this.connectionPromise = this.establishConnection();

    try {
      await this.connectionPromise;
    } finally {
      this.isConnecting = false;
      this.connectionPromise = null;
    }
  }

  /**
   * Establish WebSocket connection
   */
  private async establishConnection(): Promise<void> {
    if (!this.config) {
      throw new Error('WebSocket config not provided');
    }

    return new Promise((resolve, reject) => {
      try {
        this.socket = io(this.config!.url, {
          auth: {
            token: this.config!.token,
            organizationId: this.config!.organizationId,
          },
          transports: ['websocket'],
          upgrade: false,
          rememberUpgrade: false,
          timeout: 10000,
          forceNew: true,
        });

        // Set up event listeners
        this.socket.on('connect', () => {
          this.handleConnect();
          resolve();
        });

        this.socket.on('disconnect', this.handleDisconnect);
        this.socket.on('connect_error', (error) => {
          this.handleError(new Error(`Connection failed: ${error.message}`));
          reject(error);
        });

        // Real-time event handlers
        this.socket.on('realtime_event', this.handleRealtimeEvent);
        this.socket.on('agent_run_update', (data) => {
          this.handlers.onAgentRunUpdate?.(data);
          this.handleRealtimeEvent({
            type: 'agent_run_status_change',
            data,
            timestamp: new Date().toISOString(),
            organization_id: this.config!.organizationId,
          });
        });

        this.socket.on('workflow_update', (data) => {
          this.handlers.onWorkflowUpdate?.(data);
          this.handleRealtimeEvent({
            type: 'workflow_update',
            data,
            timestamp: new Date().toISOString(),
            organization_id: this.config!.organizationId,
          });
        });

        this.socket.on('pr_update', (data) => {
          this.handlers.onPRUpdate?.(data);
          this.handleRealtimeEvent({
            type: 'pr_update',
            data,
            timestamp: new Date().toISOString(),
            organization_id: this.config!.organizationId,
          });
        });

        // Set connection timeout
        setTimeout(() => {
          if (!this.socket?.connected) {
            reject(new Error('WebSocket connection timeout'));
          }
        }, 10000);

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.reconnectAttempts = 0;
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  /**
   * Subscribe to specific events for an organization
   */
  subscribe(eventTypes: string[]): void {
    if (!this.socket?.connected) {
      console.warn('WebSocket not connected, cannot subscribe to events');
      return;
    }

    this.socket.emit('subscribe', {
      events: eventTypes,
      organizationId: this.config?.organizationId,
    });
  }

  /**
   * Unsubscribe from specific events
   */
  unsubscribe(eventTypes: string[]): void {
    if (!this.socket?.connected) {
      return;
    }

    this.socket.emit('unsubscribe', {
      events: eventTypes,
      organizationId: this.config?.organizationId,
    });
  }

  /**
   * Send a message to the server
   */
  emit(event: string, data: any): void {
    if (!this.socket?.connected) {
      console.warn('WebSocket not connected, cannot emit event');
      return;
    }

    this.socket.emit(event, data);
  }

  /**
   * Handle successful connection
   */
  private handleConnect(): void {
    console.log('WebSocket connected');
    this.reconnectAttempts = 0;
    this.handlers.onConnect?.();

    // Subscribe to default events
    this.subscribe([
      'agent_run_update',
      'workflow_update',
      'pr_update',
      'system_notification',
    ]);
  }

  /**
   * Handle disconnection
   */
  private handleDisconnect(reason: string): void {
    console.log('WebSocket disconnected:', reason);
    this.handlers.onDisconnect?.(reason);

    // Attempt reconnection if not manually disconnected
    if (reason !== 'io client disconnect' && this.config) {
      this.attemptReconnection();
    }
  }

  /**
   * Handle connection errors
   */
  private handleError(error: Error): void {
    console.error('WebSocket error:', error);
    this.handlers.onError?.(error);
  }

  /**
   * Handle real-time events
   */
  private handleRealtimeEvent(event: RealTimeEvent): void {
    console.log('Real-time event received:', event);
    this.handlers.onEvent?.(event);
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  private async attemptReconnection(): Promise<void> {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);

    setTimeout(async () => {
      try {
        if (this.config) {
          await this.establishConnection();
        }
      } catch (error) {
        console.error('Reconnection failed:', error);
        this.attemptReconnection();
      }
    }, delay);
  }

  /**
   * Get connection status information
   */
  getStatus(): {
    connected: boolean;
    reconnectAttempts: number;
    maxReconnectAttempts: number;
    organizationId?: string;
  } {
    return {
      connected: this.isConnected(),
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.maxReconnectAttempts,
      organizationId: this.config?.organizationId,
    };
  }
}

// Singleton instance
let webSocketClient: WebSocketClient | null = null;

export const getWebSocketClient = (): WebSocketClient => {
  if (!webSocketClient) {
    webSocketClient = new WebSocketClient();
  }
  return webSocketClient;
};

export default WebSocketClient;
