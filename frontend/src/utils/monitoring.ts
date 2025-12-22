/**
 * Monitoring & Observability Setup
 * Integrates Sentry for error tracking and performance monitoring
 */

// Note: Install with: npm install @sentry/react @sentry/tracing

interface MonitoringConfig {
  dsn: string;
  environment: string;
  tracesSampleRate: number;
  enabled: boolean;
}

/**
 * Initialize monitoring (Sentry)
 */
export function initializeMonitoring(): void {
  const config: MonitoringConfig = {
    dsn: import.meta.env.VITE_SENTRY_DSN || '',
    environment: import.meta.env.VITE_APP_ENV || 'development',
    tracesSampleRate: parseFloat(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || '0.1'),
    enabled: import.meta.env.VITE_APP_ENV === 'production' || import.meta.env.VITE_APP_ENV === 'staging',
  };

  if (!config.enabled || !config.dsn) {
    console.log('📊 Monitoring disabled (development mode or no DSN)');
    return;
  }

  try {
    // Dynamic import to avoid bundling Sentry in development
    import('@sentry/react').then((Sentry) => {
      Sentry.init({
        dsn: config.dsn,
        environment: config.environment,
        tracesSampleRate: config.tracesSampleRate,
        
        integrations: [
          // Use browserTracingIntegration() for Sentry v8+
          ...(Sentry.browserTracingIntegration ? [
            Sentry.browserTracingIntegration({
              tracePropagationTargets: [
                'localhost',
                /^https:\/\/.*\.codegen\.com/,
              ],
            })
          ] : []),
          // Use replayIntegration() for Sentry v8+
          ...(Sentry.replayIntegration ? [
            Sentry.replayIntegration({
              maskAllText: true,
              blockAllMedia: true,
            })
          ] : []),
        ],

        // Performance Monitoring
        beforeSend(event) {
          // Filter out development errors
          if (event.environment === 'development') {
            return null;
          }
          return event;
        },

        // Release tracking
        release: `codegen-frontend@${import.meta.env.VITE_APP_VERSION}`,
      });

      console.log('✅ Monitoring initialized (Sentry)');
    });
  } catch (error) {
    console.error('❌ Failed to initialize monitoring:', error);
  }
}

/**
 * Log custom event
 */
export function logEvent(name: string, data?: Record<string, any>): void {
  if (import.meta.env.VITE_ENABLE_TELEMETRY === 'true') {
    console.log(`📊 Event: ${name}`, data);
    
    // Send to analytics if available
    if (window.gtag) {
      window.gtag('event', name, data);
    }
  }
}

/**
 * Log error
 */
export function logError(error: Error, context?: Record<string, any>): void {
  console.error('❌ Error:', error, context);
  
  if (import.meta.env.VITE_APP_ENV !== 'development') {
    import('@sentry/react').then((Sentry) => {
      Sentry.captureException(error, {
        extra: context,
      });
    });
  }
}

/**
 * Log performance metric
 */
export function logPerformance(metric: string, value: number, unit: string = 'ms'): void {
  if (import.meta.env.VITE_ENABLE_TELEMETRY === 'true') {
    console.log(`⚡ Performance: ${metric} = ${value}${unit}`);
    
    import('@sentry/react').then((Sentry) => {
      Sentry.metrics.gauge(metric, value);
    });
  }
}

// Extend Window interface for gtag
declare global {
  interface Window {
    gtag?: (...args: any[]) => void;
  }
}
