/**
 * WebSocketService - Handles real-time communication with server
 * Supports auto-reconnect, heartbeat, message queuing, and subscriptions
 * Enables real-time CI/CD pipeline updates and profile execution monitoring
 */

export interface WebSocketMessage {
  type: string;
  data: any;
  messageId?: string;
  timestamp: number;
}

export interface WebSocketOptions {
  url?: string;
  autoReconnect?: boolean;
  maxReconnectAttempts?: number;
  reconnectDelay?: number;
  heartbeatInterval?: number;
}

export type WebSocketEventHandler = (data: any) => void;

export class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string | null = null;
  private isConnected: boolean = false;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 1000;
  private maxReconnectDelay: number = 30000;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private heartbeatTimeout: NodeJS.Timeout | null = null;
  
  private eventListeners: Map<string, Set<WebSocketEventHandler>> = new Map();
  private subscriptions: Set<string> = new Set();
  private messageQueue: WebSocketMessage[] = [];
  private autoReconnect: boolean = true;
  
  // Message ID tracking for responses
  private messageId: number = 0;
  private pendingMessages: Map<string, {
    resolve: (value: any) => void;
    reject: (reason: any) => void;
    timeout: NodeJS.Timeout;
  }> = new Map();

  constructor(options: WebSocketOptions = {}) {
    this.maxReconnectAttempts = options.maxReconnectAttempts ?? 5;
    this.reconnectDelay = options.reconnectDelay ?? 1000;
    this.autoReconnect = options.autoReconnect ?? true;
    
    if (options.url) {
      this.url = options.url;
    }
  }

  /**
   * Connect to WebSocket server
   */
  async connect(url?: string): Promise<void> {
    if (this.isConnected) {
      console.log('🔌 WebSocket already connected');
      return Promise.resolve();
    }

    // Auto-detect WebSocket URL if not provided
    if (!url && !this.url) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      this.url = `${protocol}//${host}/ws`;
    } else if (url) {
      this.url = url;
    }

    return new Promise((resolve, reject) => {
      try {
        console.log(`🔌 Connecting to WebSocket: ${this.url}`);
        this.ws = new WebSocket(this.url!);
        
        this.ws.onopen = (event) => {
          this.handleOpen(event);
          resolve();
        };
        
        this.ws.onmessage = (event) => {
          this.handleMessage(event);
        };
        
        this.ws.onclose = (event) => {
          this.handleClose(event);
        };
        
        this.ws.onerror = (event) => {
          this.handleError(event);
          if (!this.isConnected) {
            reject(new Error(`WebSocket connection failed to ${this.url}`));
          }
        };
        
      } catch (error) {
        console.error('❌ Failed to create WebSocket connection:', error);
        reject(error);
      }
    });
  }

  /**
   * Handle WebSocket connection open
   */
  private handleOpen(event: Event): void {
    console.log('✅ WebSocket connected');
    this.isConnected = true;
    this.reconnectAttempts = 0;
    
    // Start heartbeat
    this.startHeartbeat();
    
    // Process queued messages
    this.processMessageQueue();
    
    // Re-subscribe to channels
    this.resubscribeToChannels();
    
    // Emit connection event
    this.emit('connected', { event });
  }

  /**
   * Handle WebSocket message
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const data: WebSocketMessage = JSON.parse(event.data);
      console.log('📨 WebSocket message received:', data.type);
      
      // Handle different message types
      switch (data.type) {
        case 'connection':
          this.handleConnectionMessage(data);
          break;
        case 'pong':
          this.handlePong(data);
          break;
        case 'profile_execution_start':
        case 'profile_execution_end':
        case 'profile_execution_error':
          this.handleProfileExecution(data);
          break;
        case 'pipeline_start':
        case 'pipeline_progress':
        case 'pipeline_complete':
        case 'pipeline_error':
          this.handlePipelineEvent(data);
          break;
        case 'system_health':
          this.handleSystemHealth(data);
          break;
        case 'metrics_update':
          this.handleMetricsUpdate(data);
          break;
        case 'subscription_confirmed':
        case 'unsubscription_confirmed':
          this.handleSubscriptionConfirmation(data);
          break;
        default:
          // Check if it's a response to a pending message
          if (data.messageId && this.pendingMessages.has(data.messageId)) {
            this.handleMessageResponse(data);
          } else {
            this.emit('message', data);
          }
      }
      
    } catch (error) {
      console.error('❌ Error parsing WebSocket message:', error);
    }
  }

  /**
   * Handle WebSocket close
   */
  private handleClose(event: CloseEvent): void {
    console.log('🔌 WebSocket disconnected:', event.code, event.reason);
    this.isConnected = false;
    
    // Stop heartbeat
    this.stopHeartbeat();
    
    // Emit disconnect event
    this.emit('disconnected', { event });
    
    // Attempt reconnection if enabled
    if (this.autoReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.attemptReconnect();
    }
  }

  /**
   * Handle WebSocket error
   */
  private handleError(event: Event): void {
    console.error('❌ WebSocket error:', event);
    this.emit('error', { event });
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  private attemptReconnect(): void {
    this.reconnectAttempts++;
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay
    );
    
    console.log(`🔄 Attempting reconnect ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);
    
    setTimeout(() => {
      this.connect(this.url || undefined).catch(error => {
        console.error('Reconnect failed:', error);
      });
    }, delay);
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected) {
        this.send({ type: 'ping', timestamp: Date.now() });
        
        // Set timeout for pong response
        this.heartbeatTimeout = setTimeout(() => {
          console.warn('⚠️ No pong received, connection may be dead');
          this.ws?.close();
        }, 5000);
      }
    }, 30000); // Send ping every 30 seconds
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    if (this.heartbeatTimeout) {
      clearTimeout(this.heartbeatTimeout);
      this.heartbeatTimeout = null;
    }
  }

  /**
   * Handle pong response
   */
  private handlePong(data: WebSocketMessage): void {
    if (this.heartbeatTimeout) {
      clearTimeout(this.heartbeatTimeout);
      this.heartbeatTimeout = null;
    }
    console.log('💓 Pong received');
  }

  /**
   * Handle connection confirmation message
   */
  private handleConnectionMessage(data: WebSocketMessage): void {
    console.log('🔗 Connection confirmed:', data.data);
    this.emit('connection_confirmed', data.data);
  }

  /**
   * Handle profile execution events
   */
  private handleProfileExecution(data: WebSocketMessage): void {
    this.emit(data.type, data.data);
    this.emit('profile_execution', data);
  }

  /**
   * Handle pipeline events
   */
  private handlePipelineEvent(data: WebSocketMessage): void {
    this.emit(data.type, data.data);
    this.emit('pipeline_event', data);
  }

  /**
   * Handle system health updates
   */
  private handleSystemHealth(data: WebSocketMessage): void {
    this.emit('system_health', data.data);
  }

  /**
   * Handle metrics updates
   */
  private handleMetricsUpdate(data: WebSocketMessage): void {
    this.emit('metrics_update', data.data);
  }

  /**
   * Handle subscription confirmation
   */
  private handleSubscriptionConfirmation(data: WebSocketMessage): void {
    console.log('✅ Subscription confirmed:', data.type);
    this.emit(data.type, data.data);
  }

  /**
   * Handle message response
   */
  private handleMessageResponse(data: WebSocketMessage): void {
    const pending = this.pendingMessages.get(data.messageId!);
    if (pending) {
      clearTimeout(pending.timeout);
      pending.resolve(data.data);
      this.pendingMessages.delete(data.messageId!);
    }
  }

  /**
   * Send message to server
   */
  send(message: any): void {
    if (this.isConnected && this.ws) {
      try {
        this.ws.send(JSON.stringify(message));
      } catch (error) {
        console.error('❌ Failed to send WebSocket message:', error);
        // Queue message for retry
        this.messageQueue.push(message);
      }
    } else {
      // Queue message for when connection is established
      this.messageQueue.push(message);
    }
  }

  /**
   * Send message and wait for response
   */
  async sendWithResponse(message: any, timeout: number = 5000): Promise<any> {
    const messageId = `msg_${++this.messageId}`;
    const messageWithId = { ...message, messageId };

    return new Promise((resolve, reject) => {
      const timeoutHandle = setTimeout(() => {
        this.pendingMessages.delete(messageId);
        reject(new Error(`Message timeout: ${message.type}`));
      }, timeout);

      this.pendingMessages.set(messageId, {
        resolve,
        reject,
        timeout: timeoutHandle
      });

      this.send(messageWithId);
    });
  }

  /**
   * Process queued messages
   */
  private processMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.isConnected) {
      const message = this.messageQueue.shift();
      if (message) {
        this.send(message);
      }
    }
  }

  /**
   * Subscribe to a channel
   */
  subscribe(channel: string): void {
    this.subscriptions.add(channel);
    this.send({ type: 'subscribe', channel });
  }

  /**
   * Unsubscribe from a channel
   */
  unsubscribe(channel: string): void {
    this.subscriptions.delete(channel);
    this.send({ type: 'unsubscribe', channel });
  }

  /**
   * Re-subscribe to all channels after reconnect
   */
  private resubscribeToChannels(): void {
    this.subscriptions.forEach(channel => {
      this.send({ type: 'subscribe', channel });
    });
  }

  /**
   * Add event listener
   */
  on(event: string, handler: WebSocketEventHandler): () => void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, new Set());
    }
    this.eventListeners.get(event)!.add(handler);
    
    // Return unsubscribe function
    return () => {
      this.off(event, handler);
    };
  }

  /**
   * Remove event listener
   */
  off(event: string, handler: WebSocketEventHandler): void {
    const handlers = this.eventListeners.get(event);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  /**
   * Emit event to all listeners
   */
  private emit(event: string, data: any): void {
    const handlers = this.eventListeners.get(event);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`Error in WebSocket event handler for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    this.autoReconnect = false;
    this.stopHeartbeat();
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.isConnected = false;
    this.subscriptions.clear();
    this.messageQueue = [];
  }

  /**
   * Get connection status
   */
  getStatus(): {
    isConnected: boolean;
    reconnectAttempts: number;
    subscriptions: string[];
    queuedMessages: number;
  } {
    return {
      isConnected: this.isConnected,
      reconnectAttempts: this.reconnectAttempts,
      subscriptions: Array.from(this.subscriptions),
      queuedMessages: this.messageQueue.length
    };
  }

  /**
   * Subscribe to webhook events
   * These events come from the backend webhook system
   */
  subscribeToWebhookEvents(): void {
    // Workflow events
    this.on('workflow:created', (data) => {
      console.log('📝 Workflow created:', data);
      this.emit('data_refresh', { type: 'workflows', payload: data });
    });

    this.on('workflow:updated', (data) => {
      console.log('✏️ Workflow updated:', data);
      this.emit('data_refresh', { type: 'workflows', payload: data });
    });

    this.on('workflow:deleted', (data) => {
      console.log('🗑️ Workflow deleted:', data);
      this.emit('data_refresh', { type: 'workflows', payload: data });
    });

    // Execution events
    this.on('execution:started', (data) => {
      console.log('▶️ Execution started:', data);
      this.emit('execution_update', { type: 'started', payload: data });
    });

    this.on('execution:completed', (data) => {
      console.log('✅ Execution completed:', data);
      this.emit('execution_update', { type: 'completed', payload: data });
    });

    this.on('execution:failed', (data) => {
      console.log('❌ Execution failed:', data);
      this.emit('execution_update', { type: 'failed', payload: data });
    });

    this.on('execution:updated', (data) => {
      console.log('🔄 Execution updated:', data);
      this.emit('execution_update', { type: 'updated', payload: data });
    });
  }

  /**
   * Enable real-time updates for workflows and executions
   */
  enableRealTimeUpdates(): void {
    if (!this.isConnected) {
      console.warn('⚠️ Cannot enable real-time updates: not connected');
      return;
    }

    this.subscribeToWebhookEvents();
    
    // Subscribe to relevant channels
    this.subscribe('workflows');
    this.subscribe('executions');
    
    console.log('🔔 Real-time updates enabled');
  }

  /**
   * Disable real-time updates
   */
  disableRealTimeUpdates(): void {
    this.unsubscribe('workflows');
    this.unsubscribe('executions');
    
    console.log('🔕 Real-time updates disabled');
  }
}

// Export singleton instance
export const webSocketService = new WebSocketService();
