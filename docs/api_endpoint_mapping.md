# Codegen API Endpoint Mapping

## Overview
Complete mapping of all Codegen API endpoints, their rate limits, authentication requirements, and corresponding CLI commands.

## Base Configuration
```
BASE_URL: https://api.codegen.com/v1/organizations/{org_id}/
Authentication: Bearer token in Authorization header
Rate Limits: Shared across all endpoints per API token
```

## Core API Endpoints

### 🤖 Agent Operations
| Endpoint | Method | Rate Limit | CLI Command | Description |
|----------|--------|------------|-------------|-------------|
| `/agent/run` | POST | 10 req/min | `codegen agent` | Create new agent run |
| `/agent/run/{agent_id}` | GET | 60 req/30s | `codegen agent status` | Get agent status |
| `/agent/run/resume` | POST | 60 req/30s | `codegen agents resume` | Resume with follow-up |
| `/agent/runs` | GET | 60 req/30s | `codegen agents` | List agent runs (paginated) |
| `/agent/run/{agent_id}/logs` | GET | 5 req/min | `codegen agent logs` | Get execution logs |

### 🧠 Claude Code Integration
| Endpoint | Method | Rate Limit | CLI Command | Description |
|----------|--------|------------|-------------|-------------|
| `/claude_code/session` | POST | 60 req/30s | `codegen claude` | Create Claude session |
| `/claude_code/session/{id}/status` | POST | 60 req/30s | `codegen claude status` | Update session status |
| `/claude_code/session/{id}/log` | POST | 60 req/30s | `codegen claude logs` | Get session logs |

### 🏢 Organization & Projects
| Endpoint | Method | Rate Limit | CLI Command | Description |
|----------|--------|------------|-------------|-------------|
| `/v1/users/me` | GET | 60 req/30s | `codegen profile` | Current user info |
| `/v1/organizations` | GET | 60 req/30s | `codegen org list` | List organizations |
| `/repositories` | GET | 60 req/30s | `codegen repo list` | List repositories |
| `/integrations` | GET | 60 req/30s | `codegen integrations` | List integrations |

### 🛠️ Tools & Execution
| Endpoint | Method | Rate Limit | CLI Command | Description |
|----------|--------|------------|-------------|-------------|
| `/tools` | GET | 60 req/30s | `codegen tools` | List available tools |
| `/tools/execute` | POST | 60 req/30s | MCP Server | Execute tool via API |

### 📊 Setup & Analysis
| Endpoint | Method | Rate Limit | CLI Command | Description |
|----------|--------|------------|-------------|-------------|
| `/setup` | POST | 5 req/min | `codegen init` | Setup commands |
| `/analyze` | POST | 5 req/min | Various | Log analysis |

## CLI Command Structure

### Primary Commands
```bash
codegen agent          # Single agent operations
codegen agents         # Multi-agent management  
codegen claude         # Claude Code integration
codegen config         # Configuration management
codegen init           # Initialize Codegen folder
codegen integrations   # External integrations
codegen login/logout   # Authentication
codegen org            # Organization management
codegen profile        # User profile
codegen repo           # Repository management
codegen tools          # Tool management
codegen tui            # Terminal UI interface
codegen update         # Version updates
```

### Dashboard Commands (To Be Implemented)
```bash
codegen dashboard      # Launch dashboard TUI
codegen star <id>      # Star/unstar agent run
codegen resume <id>    # Resume agent with follow-up
codegen workflows      # Workflow management
codegen projects       # Project management
codegen notifications  # Notification management
```

## Rate Limiting Strategy

### Current Limits
- **Agent Creation**: 10 requests/minute (most restrictive)
- **Standard Operations**: 60 requests/30 seconds
- **Log Analysis**: 5 requests/minute
- **Setup Commands**: 5 requests/minute

### Dashboard Optimization
1. **Intelligent Caching**: Cache agent runs, project lists, tool definitions
2. **Batch Operations**: Group related requests where possible
3. **Smart Polling**: Increase frequency for active agents, decrease for completed
4. **Request Queuing**: Queue requests to respect rate limits
5. **Offline Mode**: Use cached data when rate limits exceeded

## Authentication Flow

### Token Management
```python
# Current token storage pattern
from codegen.cli.auth.token_manager import get_current_token, get_current_org_name

token = get_current_token()
org_name = get_current_org_name()
headers = {"Authorization": f"Bearer {token}"}
```

### Organization Resolution
```python
# Organization ID resolution
from codegen.cli.utils.org import resolve_org_id

org_id = resolve_org_id()  # Uses cached org info from token_manager
```

## API Client Patterns

### Standard Request Pattern
```python
import requests
from codegen.cli.api.endpoints import API_ENDPOINT

url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{org_id}/endpoint"
response = requests.get(url, headers=headers, timeout=10)
response.raise_for_status()
data = response.json()
```

### Error Handling
```python
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
except requests.RequestException as e:
    # Handle API errors, rate limiting, network issues
    logger.error(f"API request failed: {e}")
```

## Dashboard Integration Points

### Real-time Monitoring
- Use `/agent/runs` with pagination for agent list
- Poll `/agent/run/{id}` for status updates
- Respect 60 req/30s limit with smart caching

### Project Management
- Use `/repositories` for project listing
- Implement local starring with persistence
- Monitor PR events via GitHub API integration

### Workflow Orchestration
- Use `/agent/run` for workflow step execution
- Use `/tools/execute` for validation gates
- Implement progress tracking with local state

### Notification System
- Poll for status changes with change detection
- Use local storage for notification history
- Integrate with system notifications

## Implementation Files

### Core API Integration
- `src/codegen/cli/api/endpoints.py` - Endpoint definitions
- `src/codegen/cli/api/client.py` - REST API client
- `src/codegen/cli/api/schemas.py` - Pydantic models

### Authentication
- `src/codegen/cli/auth/token_manager.py` - Token management
- `src/codegen/cli/auth/session.py` - Session handling
- `src/codegen/cli/utils/org.py` - Organization utilities

### Command Implementation
- `src/codegen/cli/commands/agent/main.py` - Agent operations
- `src/codegen/cli/commands/agents/main.py` - Agent management
- `src/codegen/cli/commands/claude/main.py` - Claude integration
- `src/codegen/cli/commands/tools/main.py` - Tool management

### TUI Integration
- `src/codegen/cli/tui/app.py` - Main TUI application
- `src/codegen/cli/tui/agent_detail.py` - Agent detail views

This mapping provides the foundation for implementing all dashboard features while respecting API constraints and leveraging existing patterns.

