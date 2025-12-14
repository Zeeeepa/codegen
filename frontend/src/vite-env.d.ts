/// <reference types="vite/client" />

/**
 * Type definitions for Vite environment variables
 * Fixes TypeScript errors: Property 'env' does not exist on type 'ImportMeta'
 */

interface ImportMetaEnv {
  // API Configuration
  readonly VITE_API_URL?: string;
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_ORGANIZATION_ID?: string;
  readonly VITE_API_TOKEN?: string;
  
  // Database Configuration
  readonly VITE_DATABASE_API_URL?: string;
  readonly VITE_DATABASE_ORG_ID?: string;
  
  // WebSocket Configuration
  readonly VITE_WS_URL?: string;
  readonly VITE_WEBSOCKET_URL?: string;
  
  // Application Configuration
  readonly VITE_APP_NAME?: string;
  readonly VITE_APP_VERSION?: string;
  readonly VITE_APP_ENV?: 'development' | 'staging' | 'production';
  
  // Feature Flags
  readonly VITE_FEATURE_AUTONOMOUS_MODE?: string;
  readonly VITE_FEATURE_TREE_SEARCH?: string;
  readonly VITE_FEATURE_WORKFLOW_CANVAS?: string;
  readonly VITE_FEATURE_ANALYTICS?: string;
  readonly VITE_FEATURE_TELEMETRY?: string;
  
  // Monitoring & Observability
  readonly VITE_SENTRY_DSN?: string;
  readonly VITE_SENTRY_ENVIRONMENT?: string;
  readonly VITE_SENTRY_TRACES_SAMPLE_RATE?: string;
  readonly VITE_LOG_LEVEL?: 'debug' | 'info' | 'warn' | 'error';
  
  // Performance
  readonly VITE_MAX_CONTEXT_SIZE?: string;
  readonly VITE_MAX_STEPS?: string;
  readonly VITE_POLLING_INTERVAL?: string;
  
  // Google Analytics
  readonly VITE_GA_MEASUREMENT_ID?: string;
  
  // Mode
  readonly MODE: string;
  readonly DEV: boolean;
  readonly PROD: boolean;
  readonly SSR: boolean;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

/**
 * Type declarations for static assets
 */
declare module '*.svg' {
  const content: string;
  export default content;
}

declare module '*.png' {
  const content: string;
  export default content;
}

declare module '*.jpg' {
  const content: string;
  export default content;
}

declare module '*.jpeg' {
  const content: string;
  export default content;
}

declare module '*.gif' {
  const content: string;
  export default content;
}

declare module '*.webp' {
  const content: string;
  export default content;
}

declare module '*.ico' {
  const content: string;
  export default content;
}

declare module '*.avif' {
  const content: string;
  export default content;
}

declare module '*.css' {
  const content: Record<string, string>;
  export default content;
}

declare module '*.scss' {
  const content: Record<string, string>;
  export default content;
}

declare module '*.sass' {
  const content: Record<string, string>;
  export default content;
}

declare module '*.less' {
  const content: Record<string, string>;
  export default content;
}

declare module '*.json' {
  const content: any;
  export default content;
}

