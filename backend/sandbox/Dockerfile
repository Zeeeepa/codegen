# Simplified Docker Sandbox for Claude Code Agents
# Based on claude-code-templates architecture
FROM node:22-alpine

# Install development tools
RUN apk --no-cache add \
    git \
    bash \
    python3 \
    py3-pip \
    curl \
    docker-cli

# Install Claude Agent SDK globally
RUN npm install -g @anthropic-ai/claude-agent-sdk

# Create non-root user for security
RUN adduser -u 10001 -D -s /bin/bash sandboxuser

# Set up workspace and output directory
WORKDIR /app
RUN mkdir -p /output && chown sandboxuser:sandboxuser /output

# Copy execution scripts
COPY execute.js /app/execute.js
COPY package.json /app/package.json

# Install dependencies
RUN npm install --production && \
    chown -R sandboxuser:sandboxuser /app

# Run as non-root user
USER sandboxuser

# Environment setup
ENV HOME=/home/sandboxuser
ENV NODE_ENV=production
ENV SANDBOX_MODE=isolated

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node -e "console.log('healthy')" || exit 1

# Default command
CMD ["node", "/app/execute.js"]
