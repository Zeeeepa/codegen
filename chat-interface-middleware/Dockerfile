# Multi-stage build for Chat Interface Middleware
FROM oven/bun:1-alpine AS builder

# Install system dependencies for Playwright
RUN apk add --no-cache \
    chromium \
    firefox \
    webkit2gtk \
    ca-certificates \
    fonts-liberation \
    libx11 \
    libxcomposite \
    libxdamage \
    libxext \
    libxfixes \
    libxrandr \
    libxrender \
    libxss \
    libxtst \
    ttf-dejavu \
    ttf-droid \
    ttf-freefont \
    ttf-liberation

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json bun.lock* ./
COPY tsconfig.json ./

# Install dependencies
RUN bun install --frozen-lockfile

# Copy source code
COPY src/ src/
COPY configs/ configs/

# Build the application
RUN bun run build

# Production stage
FROM oven/bun:1-alpine AS production

# Install system dependencies and Playwright browsers
RUN apk add --no-cache \
    chromium \
    firefox \
    webkit2gtk \
    ca-certificates \
    fonts-liberation \
    libx11 \
    libxcomposite \
    libxdamage \
    libxext \
    libxfixes \
    libxrandr \
    libxrender \
    libxss \
    libxtst \
    ttf-dejavu \
    ttf-droid \
    ttf-freefont \
    ttf-liberation \
    dumb-init

# Set Playwright environment variables
ENV PLAYWRIGHT_BROWSERS_PATH=/usr/bin
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Create non-root user
RUN addgroup -g 1001 -S middleware && \
    adduser -S middleware -u 1001

# Set working directory
WORKDIR /app

# Copy built application
COPY --from=builder --chown=middleware:middleware /app/package.json ./
COPY --from=builder --chown=middleware:middleware /app/node_modules ./node_modules
COPY --from=builder --chown=middleware:middleware /app/src ./src
COPY --from=builder --chown=middleware:middleware /app/tsconfig.json ./

# Create required directories
RUN mkdir -p storage logs screenshots traces cookies configs/examples && \
    chown -R middleware:middleware storage logs screenshots traces cookies configs

# Copy example configurations
COPY --chown=middleware:middleware configs/examples/ configs/examples/

# Switch to non-root user
USER middleware

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD bun run -e "fetch('http://localhost:3000/health').then(r => r.ok ? process.exit(0) : process.exit(1)).catch(() => process.exit(1))"

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Start the application
CMD ["bun", "run", "start"]