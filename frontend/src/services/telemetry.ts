/**
 * IRIS Telemetry Service
 * Tracks AI function performance for optimization
 */

export interface TelemetryEvent {
  functionName: string;
  startTime: number;
  endTime?: number;
  duration?: number;
  success: boolean;
  inputSize?: number;
  outputSize?: number;
  error?: string;
  metadata?: Record<string, any>;
}

export interface TelemetryMetrics {
  totalCalls: number;
  successfulCalls: number;
  failedCalls: number;
  avgDuration: number;
  minDuration: number;
  maxDuration: number;
  avgInputSize: number;
  avgOutputSize: number;
  errorRate: number;
}

class TelemetryService {
  private events: Map<string, TelemetryEvent[]> = new Map();
  private activeEvents: Map<string, TelemetryEvent> = new Map();
  private agentDbPath: string = 'data/telemetry.db';

  /**
   * Start tracking an AI function execution
   */
  startTracking(functionName: string, metadata?: Record<string, any>): string {
    const eventId = `${functionName}-${Date.now()}-${Math.random()}`;
    const event: TelemetryEvent = {
      functionName,
      startTime: performance.now(),
      success: false,
      metadata
    };

    this.activeEvents.set(eventId, event);
    return eventId;
  }

  /**
   * End tracking with success
   */
  endTracking(
    eventId: string,
    result: any,
    metadata?: Record<string, any>
  ): void {
    const event = this.activeEvents.get(eventId);
    if (!event) return;

    event.endTime = performance.now();
    event.duration = event.endTime - event.startTime;
    event.success = true;
    event.outputSize = this.calculateSize(result);
    event.metadata = { ...event.metadata, ...metadata };

    this.storeEvent(event);
    this.activeEvents.delete(eventId);
  }

  /**
   * End tracking with error
   */
  endTrackingWithError(eventId: string, error: Error): void {
    const event = this.activeEvents.get(eventId);
    if (!event) return;

    event.endTime = performance.now();
    event.duration = event.endTime - event.startTime;
    event.success = false;
    event.error = error.message;

    this.storeEvent(event);
    this.activeEvents.delete(eventId);
  }

  /**
   * Store event in memory (and optionally AgentDB)
   */
  private storeEvent(event: TelemetryEvent): void {
    const events = this.events.get(event.functionName) || [];
    events.push(event);
    this.events.set(event.functionName, events);

    // Keep only last 1000 events per function
    if (events.length > 1000) {
      events.shift();
    }

    // Send to AgentDB if available
    this.sendToAgentDB(event);
  }

  /**
   * Send event to IRIS AgentDB
   */
  private async sendToAgentDB(event: TelemetryEvent): Promise<void> {
    try {
      // In production, this would send to AgentDB via API
      // For now, store locally
      if (typeof window !== 'undefined' && window.localStorage) {
        const key = `telemetry_${event.functionName}`;
        const existing = JSON.parse(localStorage.getItem(key) || '[]');
        existing.push(event);
        
        // Keep last 100 events
        const recent = existing.slice(-100);
        localStorage.setItem(key, JSON.stringify(recent));
      }
    } catch (error) {
      console.warn('Failed to send telemetry to AgentDB:', error);
    }
  }

  /**
   * Calculate approximate size of data
   */
  private calculateSize(data: any): number {
    try {
      return JSON.stringify(data).length;
    } catch {
      return 0;
    }
  }

  /**
   * Get metrics for a function
   */
  getMetrics(functionName: string): TelemetryMetrics | null {
    const events = this.events.get(functionName);
    if (!events || events.length === 0) return null;

    const successfulEvents = events.filter(e => e.success);
    const failedEvents = events.filter(e => !e.success);
    const durations = events.filter(e => e.duration).map(e => e.duration!);

    return {
      totalCalls: events.length,
      successfulCalls: successfulEvents.length,
      failedCalls: failedEvents.length,
      avgDuration: durations.reduce((a, b) => a + b, 0) / durations.length || 0,
      minDuration: Math.min(...durations) || 0,
      maxDuration: Math.max(...durations) || 0,
      avgInputSize: events.reduce((sum, e) => sum + (e.inputSize || 0), 0) / events.length,
      avgOutputSize: events.reduce((sum, e) => sum + (e.outputSize || 0), 0) / events.length,
      errorRate: (failedEvents.length / events.length) * 100
    };
  }

  /**
   * Get all metrics
   */
  getAllMetrics(): Map<string, TelemetryMetrics> {
    const metrics = new Map<string, TelemetryMetrics>();
    
    for (const [functionName] of this.events) {
      const funcMetrics = this.getMetrics(functionName);
      if (funcMetrics) {
        metrics.set(functionName, funcMetrics);
      }
    }

    return metrics;
  }

  /**
   * Get recent events for a function
   */
  getRecentEvents(functionName: string, limit: number = 10): TelemetryEvent[] {
    const events = this.events.get(functionName) || [];
    return events.slice(-limit);
  }

  /**
   * Clear all telemetry data
   */
  clear(): void {
    this.events.clear();
    this.activeEvents.clear();
  }

  /**
   * Export telemetry data for IRIS
   */
  exportForIris(): any {
    const data: any = {
      timestamp: new Date().toISOString(),
      functions: {}
    };

    for (const [functionName, events] of this.events) {
      const metrics = this.getMetrics(functionName);
      data.functions[functionName] = {
        metrics,
        recentEvents: events.slice(-50)
      };
    }

    return data;
  }
}

// Singleton instance
export const telemetryService = new TelemetryService();

/**
 * Decorator to automatically track function execution
 */
export function withTelemetry<T extends (...args: any[]) => any>(
  fn: T,
  functionName?: string
): T {
  const trackedName = functionName || fn.name;

  return ((...args: Parameters<T>): ReturnType<T> => {
    const eventId = telemetryService.startTracking(trackedName, {
      args: args.map(arg => typeof arg === 'object' ? '[Object]' : String(arg))
    });

    try {
      const result = fn(...args);

      // Handle async functions
      if (result instanceof Promise) {
        return result
          .then(value => {
            telemetryService.endTracking(eventId, value);
            return value;
          })
          .catch(error => {
            telemetryService.endTrackingWithError(eventId, error);
            throw error;
          }) as ReturnType<T>;
      }

      // Handle sync functions
      telemetryService.endTracking(eventId, result);
      return result;
    } catch (error) {
      telemetryService.endTrackingWithError(eventId, error as Error);
      throw error;
    }
  }) as T;
}

