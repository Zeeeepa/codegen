# Web2API - OpenAI-Compatible API for Web Services

Transform any web service into an OpenAI-compatible API using browser automation.

## What is Web2API?

Web2API allows you to access web services through a standardized OpenAI-compatible API. Simply register a service with its URL and login credentials, and Web2API handles:

- **Automatic Login** - Detects login forms and authenticates automatically
- **Session Management** - Maintains authenticated sessions with cookie persistence
- **Feature Discovery** - AI-powered detection of service capabilities
- **OpenAI Compatibility** - Use standard OpenAI API format to interact with services

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/Zeeeepa/TOWER.git
cd TOWER/backend/web2api/autoqa-ai-testing

# Install dependencies
pip install -e .
```

### 2. Setup Environment

```bash
# Generate encryption key
python -c "from autoqa.auth.credential_store import CredentialStore; print(CredentialStore.generate_key())"

# Set environment variables
export CREDENTIAL_ENCRYPTION_KEY="<generated-key>"
export DATABASE_URL="postgresql+asyncpg://web2api:web2api@localhost:5432/web2api"
export OWL_BROWSER_URL="http://localhost:8080"
export OWL_BROWSER_TOKEN="your-token"

# Initialize database
python -m autoqa.cli init-db
```

### 3. Start Server

```bash
# Start API server
python -m autoqa.api.server
```

Server runs on `http://localhost:8000`

### 4. Register a Service

```bash
curl -X POST http://localhost:8000/api/services \
  -H "Content-Type: application/json" \
  -d '{
    "name": "k2think",
    "url": "https://k2think.ai",
    "credentials": {
      "email": "user@example.com",
      "password": "your-password"
    }
  }'
```

### 5. Use OpenAI API

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "k2think",
    "messages": [
      {"role": "user", "content": "Write a haiku about programming"}
    ]
  }'
```

## API Endpoints

### Service Management

#### Register Service
```http
POST /api/services
Content-Type: application/json

{
  "name": "service-name",
  "url": "https://example.com",
  "description": "My AI Service",
  "credentials": {
    "email": "user@example.com",
    "password": "password123"
  }
}
```

#### List Services
```http
GET /api/services
```

#### Get Service
```http
GET /api/services/{service_id}
```

#### Trigger Discovery
```http
POST /api/services/{service_id}/discover
```

### OpenAI-Compatible Endpoints

#### Chat Completions
```http
POST /v1/chat/completions
Content-Type: application/json

{
  "model": "service-name",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 1.0,
  "max_tokens": 1000
}
```

**Response:**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1699999999,
  "model": "service-name",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 10,
    "total_tokens": 30
  }
}
```

#### List Models
```http
GET /v1/models
```

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "k2think",
      "object": "model",
      "created": 1699999999,
      "owned_by": "web2api"
    }
  ]
}
```

## Architecture

```
┌─────────────┐
│   Client    │
│  (OpenAI)   │
└──────┬──────┘
       │ HTTP Request
       ▼
┌─────────────────────────────────────┐
│         Web2API Server              │
│  ┌────────────────────────────────┐ │
│  │   API Layer (FastAPI)          │ │
│  │  - Service CRUD                │ │
│  │  - OpenAI Compatibility        │ │
│  │  - WebSocket Events            │ │
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │   Service Manager              │ │
│  │  - Lifecycle Management        │ │
│  │  - Discovery Orchestrator      │ │
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │   Session Manager              │ │
│  │  - Auth Flow Execution         │ │
│  │  - Cookie Persistence          │ │
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │   Execution Engine             │ │
│  │  - Queue Manager               │ │
│  │  - SSE Streaming               │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│      Owl-Browser Adapter           │
│  - 157+ Browser Commands           │
│  - AI-Powered Features             │
│  - CAPTCHA Solving                 │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│     Web Service (k2think.ai)        │
│  - Login Form                      │
│  - Chat Interface                  │
│  - Response                        │
└─────────────────────────────────────┘
```

## Components

### 1. Owl-Browser Adapter
- Wraps all 157 Owl-Browser commands
- Retry logic with exponential backoff
- Telemetry logging

### 2. Auth Detector
- Automatic login form detection
- CAPTCHA identification
- Success indicator detection

### 3. Session Manager
- Cookie-based session persistence
- Automatic session refresh
- Multi-tab support

### 4. Discovery System
- AI-powered feature mapping
- Operation definition generation
- Capability configuration

### 5. Execution Engine
- Request queueing with priorities
- SSE streaming support
- Live viewport streaming

## Testing

### Run End-to-End Tests

```bash
# Set test credentials
export K2THINK_EMAIL="your-email@example.com"
export K2THINK_PASSWORD="your-password"

# Run tests
cd backend/web2api/autoqa-ai-testing
python tests/test_web2api_e2e.py
```

### Test Coverage

- ✅ Health check
- ✅ Service registration
- ✅ Service listing
- ✅ Discovery trigger
- ✅ Chat completions
- ✅ Model listing

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CREDENTIAL_ENCRYPTION_KEY` | Fernet encryption key for credentials | - |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `OWL_BROWSER_URL` | Owl-Browser server URL | `http://localhost:8080` |
| `OWL_BROWSER_TOKEN` | Owl-Browser auth token | - |
| `WEB2API_PORT` | API server port | `8000` |

### Database Setup

```bash
# Create database
createdb web2api

# Run migrations
python -m autoqa.cli init-db
```

## Development

### Project Structure

```
backend/web2api/autoqa-ai-testing/src/autoqa/
├── adapters/          # Owl-Browser SDK adapter
├── api/               # REST API server
├── auth/              # Credential store & session manager
├── discovery/         # Auto-discovery system
├── execution/         # Operation execution engine
├── storage/           # Database models & repositories
└── exceptions.py      # Custom exceptions
```

### Adding New Features

1. **New Operation Type**
   - Add to `discovery/operation_builder.py`
   - Register in `ServiceManager`
   - Add OpenAI format mapping

2. **New Auth Method**
   - Extend `discovery/auth_detector.py`
   - Add flow to `auth/session_manager.py`

3. **New Streaming Format**
   - Add to `execution/streaming.py`
   - Update WebSocket events

## Troubleshooting

### Service Discovery Fails

**Problem:** Discovery status stuck on "discovering"

**Solutions:**
- Check Owl-Browser connection: `curl http://localhost:8080/health`
- Verify credentials are correct
- Check service is accessible
- Review logs: `tail -f logs/web2api.log`

### Login Fails

**Problem:** Service status shows "error"

**Solutions:**
- Verify email/password are correct
- Check if CAPTCHA is present (may need manual solving)
- Try manual login to service first

### Chat Completion Returns Error

**Problem:** 500 error from `/v1/chat/completions`

**Solutions:**
- Ensure service is "active" status
- Check session exists and is valid
- Verify service URL is correct
- Test with simple message first

## Security

- **Credentials Storage:** Encrypted at rest with Fernet
- **Session Isolation:** Separate browser contexts per service
- **API Authentication:** Add API key middleware (TODO)
- **Rate Limiting:** Per-service rate limits (TODO)

## Performance

- **Session Pooling:** Reuse authenticated sessions
- **Concurrent Requests:** Queue manager with workers
- **Caching:** Cookie persistence reduces login overhead
- **Streaming:** SSE for real-time responses

## Roadmap

- [ ] Frontend UI for service management
- [ ] Live viewport streaming
- [ ] Video recording of operations
- [ ] Multi-service routing
- [ ] Streaming responses (SSE)
- [ ] WebSocket real-time events
- [ ] Advanced CAPTCHA solving
- [ ] OAuth flow support
- [ ] Custom operation definitions
- [ ] Metrics and monitoring dashboard

## Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.

## License

MIT License - see LICENSE file for details.

## Support

- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions
- **Email:** support@web2api.dev

## Acknowledgments

Built with:
- [Owl-Browser](https://owlbrowser.net) - AI-first browser automation
- [AutoQA](https://github.com/Olib-AI/owl-projects) - Test automation framework
- [FastAPI](https://fastapi.tiangolo.com) - Modern Python web framework
