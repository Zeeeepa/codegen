# 🚀 Codegen Visual Orchestration CI/CD System

## Overview

This project transforms the codegen system into a comprehensive **Visual Orchestration Full CI/CD System** with parallel agent execution, real-time monitoring, and webhook integration capabilities.

## ✨ Key Features

- 🎨 **Visual Pipeline Designer**: Drag-and-drop interface for creating CI/CD pipelines
- ⚡ **Parallel Agent Execution**: Execute multiple codegen agents concurrently
- 📡 **Real-time Monitoring**: WebSocket-based live updates and event streaming
- 🔗 **Webhook Integration**: Completion callbacks with retry logic and security
- 🏗️ **Dependency Management**: Complex stage dependencies and execution ordering
- 🛡️ **Resource Management**: CPU, memory limits, timeouts, and scaling
- 💾 **State Persistence**: Pipeline execution history and recovery
- 🔒 **Enterprise Security**: Authentication, authorization, and audit logging

## 🏗️ Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Visual         │    │  REST API       │    │  Orchestration  │
│  Pipeline       │◄──►│  Layer          │◄──►│  Engine         │
│  Designer       │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                ▲                        ▲
                                │                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  WebSocket      │    │  Webhook        │    │  Parallel       │
│  Real-time      │◄───┤  Integration    │    │  Agent          │
│  Updates        │    │  System         │    │  Executor       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### File Structure

```
src/codegen/orchestration/
├── __init__.py              # Module initialization
├── schemas.py               # Data models and schemas
├── parallel_executor.py     # Parallel agent execution engine
├── webhooks.py             # Webhook integration system
├── engine.py               # Core orchestration engine
├── realtime.py             # Real-time event broadcasting
├── api.py                  # REST API layer
└── test_suite.py           # Comprehensive test suite

web-ui/
├── src/components/
│   └── PipelineDesigner.tsx # React visual designer
├── package.json            # Frontend dependencies
└── ...

requirements-orchestration.txt # Python dependencies
deploy-orchestration.py       # Deployment script
```

## 🚀 Quick Start

### 1. Installation

```bash
# Install Python dependencies
pip install -r requirements-orchestration.txt

# Install frontend dependencies (optional)
cd web-ui
npm install
cd ..
```

### 2. Configuration

Set environment variables:

```bash
export MAX_CONCURRENT_PIPELINES=10
export MAX_CONCURRENT_STAGES=20
export ENABLE_WEBHOOKS=true
export ENABLE_REAL_TIME_UPDATES=true
export DATABASE_URL="sqlite:///orchestration.db"
export REDIS_URL="redis://localhost:6379"
```

### 3. Deployment

```bash
# Run the deployment script
python deploy-orchestration.py

# Or run directly with uvicorn
uvicorn src.codegen.orchestration.api:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Access the System

- **API Documentation**: http://localhost:8000/docs
- **WebSocket Endpoint**: ws://localhost:8000/ws
- **Visual Designer**: http://localhost:3000 (if frontend is running)

## 📊 Usage Examples

### Creating a Pipeline via API

```python
import requests

# Create a pipeline
pipeline_data = {
    "name": "My Visual Pipeline",
    "description": "A pipeline with parallel agent execution",
    "stages": [
        {
            "id": "init",
            "name": "Initialize",
            "stage_type": "agent_task",
            "agent_config": {
                "prompt": "Initialize the pipeline",
                "timeout": 300
            },
            "depends_on": [],
            "can_run_parallel": True
        },
        {
            "id": "parallel_task",
            "name": "Parallel Processing",
            "stage_type": "agent_task", 
            "agent_config": {
                "prompt": "Process data in parallel",
                "timeout": 600
            },
            "depends_on": ["init"],
            "can_run_parallel": True
        }
    ],
    "webhooks": [
        {
            "url": "https://api.example.com/webhook",
            "method": "POST",
            "retry_attempts": 3
        }
    ]
}

response = requests.post("http://localhost:8000/pipelines", json=pipeline_data)
pipeline_id = response.json()["id"]

# Execute the pipeline
execute_response = requests.post(f"http://localhost:8000/pipelines/{pipeline_id}/execute")
execution_id = execute_response.json()["execution_id"]

# Monitor execution status
status_response = requests.get(f"http://localhost:8000/executions/{execution_id}")
print(status_response.json())
```

### WebSocket Real-time Monitoring

```javascript
// Connect to WebSocket for real-time updates
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = function() {
    // Subscribe to pipeline events
    ws.send(JSON.stringify({
        type: 'subscribe_events',
        event_types: ['pipeline_started', 'pipeline_completed', 'stage_completed']
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Real-time update:', data);
    
    if (data.event_type === 'pipeline_completed') {
        console.log('Pipeline completed:', data.data);
    }
};
```

### Using the Visual Designer

1. Open the React application at http://localhost:3000
2. Drag and drop stages from the component palette
3. Connect stages by drawing edges between them
4. Configure each stage with prompts and settings
5. Save and execute the pipeline
6. Monitor real-time execution progress

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_CONCURRENT_PIPELINES` | 10 | Maximum concurrent pipeline executions |
| `MAX_CONCURRENT_STAGES` | 20 | Maximum concurrent stage executions |
| `DEFAULT_STAGE_TIMEOUT` | 3600 | Default stage timeout in seconds |
| `PIPELINE_TIMEOUT` | 14400 | Default pipeline timeout in seconds |
| `ENABLE_WEBHOOKS` | true | Enable webhook integration |
| `ENABLE_REAL_TIME_UPDATES` | true | Enable WebSocket real-time updates |
| `DATABASE_URL` | sqlite:/// | Database connection string |
| `REDIS_URL` | redis://localhost:6379 | Redis connection string |
| `HOST` | 0.0.0.0 | API server host |
| `PORT` | 8000 | API server port |

### Pipeline Configuration

```yaml
# Example pipeline configuration
id: "my-pipeline"
name: "My Visual Pipeline"
description: "A comprehensive CI/CD pipeline"
stages:
  - id: "init"
    name: "Initialize"
    stage_type: "agent_task"
    agent_config:
      prompt: "Initialize the pipeline execution"
      timeout: 300
    depends_on: []
    can_run_parallel: true
    
  - id: "parallel-1"
    name: "Parallel Task 1"
    stage_type: "agent_task"
    agent_config:
      prompt: "Execute first parallel task"
      timeout: 600
    depends_on: ["init"]
    can_run_parallel: true
    
global_variables:
  environment: "production"
  debug_mode: false
  
webhooks:
  - url: "https://api.example.com/webhook"
    method: "POST"
    retry_attempts: 3
    timeout: 30
    
max_parallel_stages: 10
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest src/codegen/orchestration/test_suite.py -v

# Run specific test categories
python -m pytest src/codegen/orchestration/test_suite.py::TestParallelAgentExecution -v
python -m pytest src/codegen/orchestration/test_suite.py::TestWebhookIntegration -v
python -m pytest src/codegen/orchestration/test_suite.py::TestOrchestrationEngine -v

# Run integration tests
python -m pytest src/codegen/orchestration/test_suite.py::TestIntegrationScenarios -v
```

### Manual Testing

1. Start the system: `python deploy-orchestration.py`
2. Open API docs: http://localhost:8000/docs
3. Create a test pipeline using the `/pipelines` endpoint
4. Execute the pipeline using `/pipelines/{id}/execute`
5. Monitor progress via WebSocket connection
6. Check webhook deliveries at `/webhooks/deliveries`

## 📚 API Reference

### Pipeline Management

- `POST /pipelines` - Create a new pipeline
- `GET /pipelines` - List all pipelines
- `GET /pipelines/{id}` - Get pipeline details
- `DELETE /pipelines/{id}` - Delete a pipeline

### Execution Management

- `POST /pipelines/{id}/execute` - Execute a pipeline
- `GET /executions/{id}` - Get execution status
- `GET /executions` - List all executions
- `POST /pipelines/{id}/executions/{execution_id}/cancel` - Cancel execution

### Real-time & Monitoring

- `WS /ws` - WebSocket endpoint for real-time updates
- `GET /events/recent` - Get recent events
- `GET /webhooks/deliveries` - Get webhook delivery status
- `GET /stats` - Get system statistics

## 🔒 Security

### Authentication & Authorization

The system supports multiple authentication methods:

- API Key authentication
- JWT token authentication  
- OAuth2 integration
- Role-based access control (RBAC)

### Webhook Security

- HMAC signature verification
- Request timeout protection
- Retry limit enforcement
- IP whitelisting support

### Network Security

- HTTPS/TLS encryption
- CORS configuration
- Rate limiting
- Input validation and sanitization

## 🚀 Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements-orchestration.txt .
RUN pip install -r requirements-orchestration.txt

COPY src/ ./src/
COPY deploy-orchestration.py .

EXPOSE 8000
CMD ["python", "deploy-orchestration.py"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: codegen-orchestration
spec:
  replicas: 3
  selector:
    matchLabels:
      app: codegen-orchestration
  template:
    metadata:
      labels:
        app: codegen-orchestration
    spec:
      containers:
      - name: orchestration
        image: codegen-orchestration:latest
        ports:
        - containerPort: 8000
        env:
        - name: MAX_CONCURRENT_PIPELINES
          value: "20"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
---
apiVersion: v1
kind: Service
metadata:
  name: codegen-orchestration-service
spec:
  selector:
    app: codegen-orchestration
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/codegen.git
cd codegen

# Install dependencies
pip install -r requirements-orchestration.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
python -m pytest src/codegen/orchestration/test_suite.py

# Start development server
python deploy-orchestration.py
```

## 📝 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙋‍♀️ Support

- **Documentation**: [docs.codegen.com](https://docs.codegen.com)
- **Community**: [community.codegen.com](https://community.codegen.com)
- **Issues**: [GitHub Issues](https://github.com/Zeeeepa/codegen/issues)
- **Discord**: [Join our Discord](https://discord.gg/codegen)

## 🎉 Acknowledgments

- Built on top of the amazing [codegen](https://codegen.com) platform
- Inspired by enterprise CI/CD systems like Jenkins, GitHub Actions, and CircleCI
- Special thanks to the open-source community for the foundational libraries

---

**🚀 Ready to transform your development workflow with AI-powered visual orchestration? Get started today!**