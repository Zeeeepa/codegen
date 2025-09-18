/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  typescript: {
    // Enable strict type checking
    ignoreBuildErrors: false,
  },
  eslint: {
    // Enable ESLint during builds
    ignoreDuringBuilds: false,
  },
  // API routes configuration
  async rewrites() {
    return [
      {
        source: '/api/codegen/:path*',
        destination: process.env.CODEGEN_API_URL + '/:path*',
      },
    ];
  },
  // Environment variables
  env: {
    CODEGEN_API_URL: process.env.CODEGEN_API_URL || 'https://codegen-sh--rest-api.modal.run',
    WEBSOCKET_URL: process.env.WEBSOCKET_URL || 'ws://localhost:3001',
  },
  // Performance optimizations
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
