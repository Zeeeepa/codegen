# Chat Interface Middleware

A powerful middleware system for managing web chat interfaces through YAML configuration, browser automation, and AI-first tooling integration.

## 🚀 Features

- **YAML-Driven Configuration**: Define chat interfaces and automation tools through simple YAML files
- **Browser Automation**: Full Playwright integration with cookie management, snapshots, and state persistence
- **AI-First Architecture**: Built on Better-UI AUI system for seamless AI assistant integration
- **Multi-Interface Support**: Manage multiple chat interfaces (Mistral, OpenAI, Claude, etc.) simultaneously
- **Real-time Communication**: WebSocket support for live updates and streaming
- **Health Monitoring**: Comprehensive health checks and monitoring for all components
- **Hot Reload**: Development-friendly configuration reloading without restarts
- **Containerized Deployment**: Full Docker support with production-ready configurations

## 🏗️ Architecture

This project integrates three main components:

1. **Zeeeepa/API**: Backend API infrastructure with database and testing
2. **Zeeeepa/Auto-Agent**: AI integration layer with modern React frontend
3. **Zeeeepa/Better-UI**: Revolutionary AUI framework for AI-first interfaces

## 📋 Prerequisites

- **Bun** >= 1.0.0 (or Node.js >= 20.0.0)
- **Docker** (optional, for containerized deployment)
- **Git** for cloning repositories

## 🛠️ Installation

### 1. Clone and Setup

```bash
# Clone this middleware project
git clone <this-repo-url> chat-interface-middleware
cd chat-interface-middleware

# Install dependencies
bun install

# Copy environment variables
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` file with your settings:

```env
# Server Configuration
PORT=3000
CONFIG_DIR=./configs
STORAGE_DIR=./storage

# Interface Authentication
MISTRAL_PASSWORD=your-mistral-password
OPENAI_EMAIL=your-email@example.com
OPENAI_PASSWORD=your-openai-password

# Optional: Proxy settings
PROXY_URL=http://your-proxy:8080
```

### 3. Create Interface Configurations

Create YAML configuration files in the `configs/` directory. See `configs/examples/` for templates.

Example `configs/mistral-chat.yaml`:

```yaml
version: "1.0"
metadata:
  name: "mistral-chat-interface"
  description: "Mistral AI chat automation"

interface:
  name: "mistral_chat"
  url: "https://chat.mistral.ai"
  auth:
    type: "credentials"
    email: "your-email@example.com"
    password: "${MISTRAL_PASSWORD}"
  selectors:
    text_input: "textarea[data-testid='chat-input']"
    send_button: "button[data-testid='send-button']"
    response_area: ".message-list"

tools:
  - name: "sendMessage"
    description: "Send message to Mistral"
    input:
      type: "object"
      properties:
        message:
          type: "string"
          description: "Message to send"
      required: ["message"]
    execute: |
      const { page } = await playwright.getInstance(config.interface.name);
      await page.fill(selectors.text_input, input.message);
      await page.click(selectors.send_button);
      return { status: 'sent', message: input.message };
```

## 🚀 Usage

### Development Mode

```bash
# Start development server with hot reload
bun run dev

# The server will be available at http://localhost:3000
```

### Production Mode

```bash
# Build and start
bun run build
bun run start
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f chat-interface-middleware

# Scale services
docker-compose up -d --scale chat-interface-middleware=3
```

## 📡 API Endpoints

### REST API

- **GET `/health`**: System health status
- **GET `/api/interfaces`**: List all available interfaces
- **GET `/api/interfaces/:name`**: Get interface details
- **POST `/api/interfaces/:name/actions/:action`**: Execute action on interface
- **POST `/api/interfaces/:name/test`**: Test interface configuration
- **POST `/api/interfaces/:name/reload`**: Reload interface configuration
- **GET `/api/stats`**: System statistics

### WebSocket API

Connect to `ws://localhost:3000` for real-time communication:

```javascript
const ws = new WebSocket('ws://localhost:3000');

// Subscribe to events
ws.send(JSON.stringify({
  type: 'subscribe',
  data: { events: ['requestProcessed', 'configurationUpdated'] }
}));

// Execute action
ws.send(JSON.stringify({
  type: 'request',
  data: {
    interface: 'mistral_chat',
    action: 'sendMessage',
    payload: { message: 'Hello, world!' }
  }
}));
```

## 🔧 Configuration Reference

### Interface Configuration

```yaml
interface:
  name: "interface_name"
  url: "https://example.com"
  auth:
    type: "credentials" | "oauth" | "token" | "cookie"
    email: "email@example.com"
    password: "${PASSWORD_ENV_VAR}"
  selectors:
    text_input: "css-selector-for-input"
    send_button: "css-selector-for-button"
    response_area: "css-selector-for-responses"
```

### Tool Definition

```yaml
tools:
  - name: "toolName"
    description: "Tool description"
    input:
      type: "object"
      properties:
        param1:
          type: "string"
          description: "Parameter description"
      required: ["param1"]
    execute: |
      // JavaScript code with access to:
      // - input: validated input parameters
      // - playwright: browser automation
      // - storage: file/data storage
      // - selectors: UI selectors
      // - config: full interface config
      // - logger: logging utilities
```

### Automation Settings

```yaml
automation:
  browser: "chromium" | "firefox" | "webkit"
  headless: false
  viewport:
    width: 1280
    height: 720
  cookies:
    load_from: "path/to/cookies.json"
    save_to: "path/to/cookies.json"
```

## 🧪 Testing

### Test Interface Configuration

```bash
# Test a specific interface
curl -X POST http://localhost:3000/api/interfaces/mistral_chat/test \
  -H "Content-Type: application/json" \
  -d '{"action": "sendMessage", "payload": {"message": "Test message"}}'
```

### Run Automated Tests

```bash
# Unit tests
bun test

# Integration tests
bun run test:integration

# Test with coverage
bun run test --coverage
```

## 📊 Monitoring

### Health Checks

- **System Health**: `GET /health`
- **Interface Health**: `GET /health/:interface`
- **Metrics**: `GET /metrics`

### Logging

Logs are written to:
- Console (configurable via `LOG_CONSOLE`)
- File (configurable via `LOG_FILE`)
- Structured JSON format with request IDs

### Performance Monitoring

The system tracks:
- Request response times
- Browser automation performance  
- Memory and CPU usage
- Interface success/failure rates

## 🔐 Security

### Authentication
- Interface credentials stored as environment variables
- Optional encryption for stored data
- Secure cookie handling

### Network Security
- CORS protection
- Helmet.js security headers
- Rate limiting (configurable)
- Proxy support

## 🐛 Troubleshooting

### Common Issues

1. **Browser Launch Fails**
   ```bash
   # Install browser dependencies (Linux)
   apt-get update && apt-get install -y chromium-browser
   
   # Check browser permissions
   chmod +x /usr/bin/chromium
   ```

2. **Configuration Errors**
   ```bash
   # Validate YAML syntax
   bun run validate-config configs/your-config.yaml
   
   # Check logs for detailed errors
   tail -f logs/middleware.log
   ```

3. **Memory Issues**
   ```bash
   # Monitor memory usage
   curl http://localhost:3000/metrics
   
   # Adjust browser limits in .env
   MAX_CONCURRENT_BROWSERS=3
   BROWSER_IDLE_TIMEOUT=180000
   ```

### Debug Mode

Enable debug logging:

```env
LOG_LEVEL=debug
ENABLE_TRACING=true
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Development Setup

```bash
# Install development dependencies
bun install

# Run in development mode
bun run dev

# Run tests
bun test

# Type check
bun run type-check

# Lint code
bun run lint
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Zeeeepa** for the foundational API and auto-agent architecture
- **Better-UI** for the revolutionary AUI framework
- **Playwright** for robust browser automation
- **Bun** for fast JavaScript runtime

## 📞 Support

- Create an [Issue](https://github.com/your-repo/issues) for bugs or feature requests
- Check the [Documentation](docs/) for detailed guides
- Join our [Discord](https://discord.gg/your-discord) community

---

**Built with ❤️ for AI-powered chat interface automation**