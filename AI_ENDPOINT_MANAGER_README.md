# AI Endpoint Manager

🚀 **Transform any web chat interface into a scalable API endpoint**

An AI-powered system that converts web chat interfaces (ChatGPT, DeepSeek, Claude, etc.) into REST API endpoints and manages multiple AI services with persistent sessions, fingerprinted browser instances, and intelligent load balancing.

## 🎯 Features

### Core Capabilities
- **Web Chat to API Conversion** - Transform any web chat interface into REST API endpoints
- **Multi-Provider Support** - OpenAI, Gemini, DeepInfra, DeepSeek, Codegen, and custom APIs
- **Dynamic Server Management** - On/off toggleable servers with persistent sessions
- **AI-Assisted Discovery** - Automatically analyze and integrate new web interfaces
- **Sandboxed Execution** - Secure browser automation in isolated containers
- **Session Persistence** - Maintain cookies, fingerprints, and authentication across restarts

### Advanced Features
- **Model Naming System** - `webdeepseek1`, `webdeepseek8` for easy identification
- **Priority Management** - Set provider priorities and load balancing
- **Real-time Monitoring** - Live server status and performance metrics
- **Configuration Management** - Export/import endpoint configurations
- **Proxy Support** - Rotate proxies for different endpoints
- **Interactive Testing** - Built-in chat interface for endpoint validation

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/ai-endpoint-manager.git
cd ai-endpoint-manager

# Install dependencies
pip install -r requirements.txt

# Install browser automation tools
playwright install

# Copy environment configuration
cp .env.example .env
```

### Basic Usage

```bash
# Run the interactive manager
python src/ai_endpoint_manager.py
```

### Menu Options

1. **Create New Web Chat Endpoint** - Add ChatGPT, DeepSeek, Claude, etc.
2. **Create New REST API Endpoint** - Add OpenAI, Gemini, DeepInfra APIs
3. **List Active Endpoints** - View all configured endpoints and their status
4. **Start/Stop Servers** - Toggle individual endpoint servers
5. **Test Endpoints** - Send test messages to validate functionality
6. **AI-Assisted Discovery** - Analyze new web interfaces automatically
7. **Manage Server Priorities** - Configure load balancing and priorities
8. **Export/Import Configuration** - Backup and restore endpoint settings
9. **Run All Features** - Automated mode for production use

## 📋 Configuration

### Web Chat Interface Setup

```python
# Example: Adding DeepSeek web interface
URL: https://chat.deepseek.com
Username: your_username (optional)
Password: your_password (optional)

# CSS Selectors (auto-discovered if left blank)
Text Input: #message-input
Send Button: .send-button
Response Area: .chat-messages
```

### REST API Setup

```python
# Example: Adding OpenAI API
Name: OpenAI GPT-4
URL: https://api.openai.com/v1
API Key: sk-your-api-key-here
```

## 🔧 Advanced Configuration

### Environment Variables

```bash
# Core Features
AUTO_CREATE_ENDPOINTS=TRUE
AUTO_MANAGE_SERVERS=TRUE
AUTO_TEST_ENDPOINTS=TRUE

# API Keys
OPENAI_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here
CODEGEN_API_KEY=your_key_here

# Browser Settings
HEADLESS_BROWSER=TRUE
MAX_CONCURRENT_BROWSERS=5
```

### Proxy Configuration

Create `proxy.txt` with your proxy list:
```
http://proxy1:port
socks5://user:pass@proxy2:port
http://proxy3:port
```

## 🏗️ Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Management UI                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│  │ Endpoint Manager│ │ Server Control  │ │ Test Interface  ││
│  │ (Create/Config) │ │ (Start/Stop)    │ │ (Validation)    ││
│  └─────────────────┘ └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 AI Endpoint Manager Core                    │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│  │ Session Manager │ │ Proxy Manager   │ │ Config Manager  ││
│  │ (Persistence)   │ │ (Rotation)      │ │ (Import/Export) ││
│  └─────────────────┘ └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Web Chat        │ │ REST API        │ │ Custom          │
│ Interceptor     │ │ Proxy           │ │ Endpoints       │
│                 │ │                 │ │                 │
│ • Browser Auto  │ │ • API Clients   │ │ • Plugin System │
│ • Session Mgmt  │ │ • Auth Handling │ │ • Custom Logic  │
│ • Fingerprinting│ │ • Rate Limiting │ │ • Extensibility │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

## 🔍 API Endpoints

Once servers are running, each endpoint provides a standardized API:

### Chat Completion
```bash
POST /v1/chat/completions
Content-Type: application/json

{
  "model": "webdeepseek1",
  "messages": [
    {"role": "user", "content": "Hello, how are you?"}
  ],
  "stream": false
}
```

### List Models
```bash
GET /v1/models

{
  "data": [
    {
      "id": "webdeepseek1",
      "object": "model",
      "created": 1640995200,
      "owned_by": "ai-endpoint-manager"
    }
  ]
}
```

## 📊 Monitoring

### Server Status
- **Online** - Server running and accepting requests
- **Offline** - Server stopped
- **Starting** - Server initializing
- **Stopping** - Server shutting down
- **Error** - Server encountered an error

### Metrics Tracked
- Request count per endpoint
- Response times
- Error rates
- Session persistence status
- Proxy rotation statistics

## 🔒 Security Features

- **Sandboxed Execution** - Browser instances run in isolated containers
- **Session Isolation** - Each endpoint maintains separate sessions
- **Fingerprint Management** - Unique browser fingerprints per session
- **Proxy Rotation** - Automatic proxy switching for anonymity
- **Authentication Handling** - Secure credential storage and management

## 🛠️ Development

### Project Structure
```
src/
├── ai_endpoint_manager.py      # Main application
├── web_interceptor/           # Web chat interface handlers
├── api_proxy/                 # REST API proxy implementations
├── session_manager/           # Session persistence logic
├── browser_automation/        # Playwright/Selenium integration
└── config/                    # Configuration management

tests/
├── unit/                      # Unit tests
├── integration/               # Integration tests
└── e2e/                       # End-to-end tests
```

### Running Tests
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# All tests
pytest
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by cryptocurrency bot patterns for robust session management
- Built on the foundation of modern async Python practices
- Leverages browser automation for seamless web interface integration

## 📞 Support

- 📧 Email: support@ai-endpoint-manager.com
- 💬 Discord: [Join our community](https://discord.gg/ai-endpoint-manager)
- 📖 Documentation: [Full docs](https://docs.ai-endpoint-manager.com)
- 🐛 Issues: [GitHub Issues](https://github.com/your-org/ai-endpoint-manager/issues)

---

**Transform any AI chat interface into a scalable API endpoint with AI Endpoint Manager!** 🚀
