# 🔍 **COMPREHENSIVE CODEGEN API & CLI ENDPOINT MAPPING**

## 📊 **API Rate Limits**
```
Standard endpoints: 60 requests per 30 seconds
Agent creation: 10 requests per minute  
Setup commands: 5 requests per minute
Log analysis: 5 requests per minute
```

## 🌐 **Base API Endpoints**
```
Production: https://codegen-sh--rest-api.modal.run/
Staging: https://codegen-sh-staging--rest-api.modal.run/
Development: https://codegen-sh-develop--rest-api.modal.run/
```

## 🔗 **REST API Endpoints (v1)**

### **Agent Management**
| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| `POST` | `/v1/organizations/{org_id}/agent/run` | Create new agent run | 10/min |
| `GET` | `/v1/organizations/{org_id}/agent/run/{agent_run_id}` | Get agent run status | 60/30s |
| `GET` | `/v1/organizations/{org_id}/agent/run/{agent_run_id}/logs` | Get agent run logs | 5/min |
| `POST` | `/v1/organizations/{org_id}/agent/run/resume` | Resume agent run | 10/min |

### **Organization Management**
| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| `GET` | `/v1/organizations` | List user organizations | 60/30s |
| `GET` | `/v1/organizations/{org_id}/users` | List organization users | 60/30s |
| `GET` | `/v1/organizations/{org_id}/users/{user_id}` | Get specific user | 60/30s |

### **Project Management**
| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| `GET` | `/v1/organizations/{org_id}/projects` | List projects (paginated) | 60/30s |
| `GET` | `/v1/organizations/{org_id}/projects/{id}/prs` | List project PRs | 60/30s |

## 🖥️ **CLI Commands Mapping**

### **Core Commands**
| CLI Command | Function | API Endpoint Used | File Location |
|-------------|----------|-------------------|---------------|
| `codegen agent` | Create agent run | `POST /v1/organizations/{org_id}/agent/run` | `src/codegen/cli/commands/agent/main.py` |
| `codegen agents` | List agent runs | `GET /v1/organizations/{org_id}/agent/run` | `src/codegen/cli/commands/agents/main.py` |
| `codegen claude` | Run Claude Code | Claude session API | `src/codegen/cli/commands/claude/main.py` |
| `codegen login` | Authenticate user | Token validation | `src/codegen/cli/commands/login/main.py` |
| `codegen logout` | Clear auth token | Local token removal | `src/codegen/cli/commands/logout/main.py` |
| `codegen org` | Manage organizations | `GET /v1/organizations` | `src/codegen/cli/commands/org/main.py` |
| `codegen repo` | Manage repositories | Repository API | `src/codegen/cli/commands/repo/main.py` |
| `codegen tools` | List available tools | MCP tools API | `src/codegen/cli/commands/tools/main.py` |
| `codegen tui` | Launch TUI interface | Local TUI app | `src/codegen/cli/commands/tui/main.py` |

### **Configuration Commands**
| CLI Command | Function | API Endpoint Used | File Location |
|-------------|----------|-------------------|---------------|
| `codegen config` | Manage configuration | Local config management | `src/codegen/cli/commands/config/main.py` |
| `codegen init` | Initialize Codegen folder | Local initialization | `src/codegen/cli/commands/init/main.py` |
| `codegen profile` | Manage user profile | User profile API | `src/codegen/cli/commands/profile/main.py` |
| `codegen integrations` | Manage integrations | Integration API | `src/codegen/cli/commands/integrations/main.py` |
| `codegen update` | Update Codegen version | Version check API | `src/codegen/cli/commands/update/main.py` |
| `codegen style-debug` | Debug CLI styling | Local styling test | `src/codegen/cli/commands/style_debug/main.py` |

## 🔧 **MCP (Model Context Protocol) Tools**

### **Dynamic Tools** (`src/codegen/cli/mcp/tools/dynamic.py`)
- Auto-registers all available tools from API
- Supports parameter validation and type conversion
- Handles tool execution via API calls

### **Static Tools** (`src/codegen/cli/mcp/tools/static.py`)
- Pre-defined tool definitions
- Core functionality tools
- System integration tools

### **Tool Executor** (`src/codegen/cli/mcp/tools/executor.py`)
- Executes tools via API
- Handles authentication and error handling
- Provides tool result processing

## 🎯 **TUI (Terminal User Interface)**

### **Main TUI App** (`src/codegen/cli/tui/app.py`)
- Interactive terminal interface
- Real-time agent monitoring
- Command execution interface

### **Agent Detail View** (`src/codegen/cli/tui/agent_detail.py`)
- Detailed agent run information
- Log viewing and analysis
- Status monitoring

## 📊 **Telemetry & Monitoring**

### **OpenTelemetry Setup** (`src/codegen/cli/telemetry/otel_setup.py`)
- Distributed tracing
- Performance monitoring
- Error tracking

### **Exception Logger** (`src/codegen/cli/telemetry/exception_logger.py`)
- Global exception handling
- Error reporting
- Debug information collection

### **Telemetry Viewer** (`src/codegen/cli/telemetry/viewer.py`)
- Telemetry data visualization
- Performance analysis
- Monitoring dashboards

## 🔐 **Authentication & Authorization**

### **Token Manager** (`src/codegen/cli/auth/token_manager.py`)
- Token storage and retrieval
- Organization caching
- User context management

### **API Client** (`src/codegen/cli/api/client.py`)
- REST API communication
- Authentication handling
- Error management

## 🛠️ **Utility Functions**

### **Organization Utils** (`src/codegen/cli/utils/org.py`)
- Organization ID resolution
- Organization switching
- Context management

### **Repository Utils** (`src/codegen/cli/utils/repo.py`)
- Repository ID resolution
- Repository configuration
- Environment variable management

### **Function Finder** (`src/codegen/cli/utils/function_finder.py`)
- Code analysis utilities
- Function detection
- Symbol resolution

## 📋 **Data Models & Schemas**

### **API Client Models** (`src/codegen_api_client/models/`)
- `AgentRunResponse`: Agent run data structure
- `CreateAgentRunInput`: Agent creation parameters
- `PageOrganizationResponse`: Paginated organization data
- `UserResponse`: User information structure

### **CLI Schemas** (`src/codegen/cli/api/schemas.py`)
- `RunCodemodInput`: Codemod execution parameters
- `AskExpertInput`: Expert query structure
- `DocsResponse`: Documentation data
- `IdentifyResponse`: User identification data

## 🔄 **Integration Points for Dashboard**

### **Real-time Monitoring**
- **Claude Log Watcher**: `src/codegen/cli/commands/claude/claude_log_watcher.py`
- **Session API**: `src/codegen/cli/commands/claude/claude_session_api.py`
- **Telemetry System**: `src/codegen/cli/telemetry/`

### **Agent Management**
- **Agent Creation**: `src/codegen/cli/commands/agent/main.py`
- **Agent Listing**: `src/codegen/cli/commands/agents/main.py`
- **Agent API**: `src/codegen/agents/agent.py`

### **Authentication Flow**
- **Token Management**: `src/codegen/cli/auth/token_manager.py`
- **Organization Resolution**: `src/codegen/cli/utils/org.py`
- **API Client**: `src/codegen/cli/api/client.py`

### **UI Framework**
- **TUI Components**: `src/codegen/cli/tui/`
- **Styling**: `src/codegen/cli/tui/codegen_theme.tcss`
- **Event Handling**: TUI app event system

## 🚀 **External Integration Opportunities**

### **Z.AI Client** (web-ui-python-sdk)
- **Description**: Unofficial Python SDK for Z.AI API
- **Features**: GLM-4.5V and 360B models, streaming responses
- **Integration Point**: Agentic observability overlay
- **Use Case**: Intelligent code context analysis

### **GrainChain** (Langchain for sandboxes)
- **Description**: Python-based Langchain implementation
- **Features**: WSL2 deployment support
- **Integration Point**: Deployment snapshots
- **Use Case**: Environment state management

### **RepoMaster** (AI GitHub agent)
- **Description**: Open-source AI agent for GitHub mastery
- **Features**: Code repository analysis, autonomous task-solving
- **Integration Point**: Code context detection
- **Use Case**: Intelligent repository understanding

## 📈 **Dashboard Implementation Strategy**

### **Service Layer Architecture**
1. **Agent Service**: Wraps existing agent CLI commands
2. **Auth Service**: Leverages token manager and org utils
3. **Monitoring Service**: Uses Claude log watcher and telemetry
4. **Project Service**: Integrates with organization and repository APIs
5. **AI Service**: Integrates Z.AI client for observability

### **Real-time Updates**
1. **Polling Strategy**: Respect rate limits (60/30s for status checks)
2. **Event System**: Use existing telemetry infrastructure
3. **WebSocket Alternative**: Long-polling for real-time updates
4. **Caching Layer**: Local storage for offline capabilities

### **UI Framework Options**
1. **Tkinter**: Native Python GUI with existing theme integration
2. **Web-based**: Local Flask/FastAPI server with web UI
3. **TUI Extension**: Enhance existing Textual framework
4. **Hybrid**: Desktop app with web components

This comprehensive mapping provides the foundation for implementing a full-featured CI/CD Dashboard that leverages ALL existing Codegen functionality while adding advanced features through external integrations.

## 🔄 **Implementation Status**

✅ **Step 1 Complete**: API Endpoint Analysis & Rate Limit Mapping  
🚧 **In Progress**: Dashboard Core Architecture Setup  

**Next Steps**: 
- Dashboard Core Architecture Setup
- Authentication Service Integration  
- Agent Management Service Implementation
