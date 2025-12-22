import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3001,
    host: true,
    strictPort: false,
    proxy: {
      '/api/v1': {
        target: 'https://api.codegen.com',
        changeOrigin: true,
        secure: true,
        rewrite: (path) => path
      }
    }
  },
  preview: {
    port: 3001,
    host: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      onwarn(warning, warn) {
        // Suppress "use client" warnings and other non-critical warnings
        if (warning.code === 'MODULE_LEVEL_DIRECTIVE') return;
        warn(warning);
      }
    }
  },
  esbuild: {
    // Don't fail build on TypeScript errors - report them but continue
    logOverride: { 'this-is-undefined-in-esm': 'silent' }
  },
});
