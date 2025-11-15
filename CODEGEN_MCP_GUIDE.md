# Codegen MCP Server - Complete Guide

## Overview

The Codegen MCP (Model Context Protocol) server enables AI chat interfaces to interact with Codegen's autonomous AI development agents. This allows AI assistants to create agent runs, monitor their progress, and manage development workflows programmatically.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Configuration](#configuration)
3. [Core Features](#core-features)
4. [API Endpoints](#api-endpoints)
5. [Testing Examples](#testing-examples)
6. [Status States](#status-states)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

- Python 3.10+
- Codegen SDK installed: `pip install codegen`
- Valid Codegen API token
- Organization ID

### Installation

```bash
# Install via pip
pip install codegen

# Or via uv (recommended)
uvx --from codegen codegen-mcp-server
```

### Basic Configuration

Add to your MCP client configuration (e.g., Claude Desktop, Cline, Cursor):

```json
{
  "mcpServers": {
    "codegen": {
      "command": "uvx",
      "args": [
        "--from",
        "codegen",
        "codegen-mcp-server"
      ],
      "env": {
        "CODEGEN_API_KEY": "your-api-key-here",
        "CODEGEN_ORG_ID": "your-org-id-here"
      }
    }
  }
}
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CODEGEN_API_KEY` | Yes | - | Your Codegen API authentication token |
| `CODEGEN_ORG_ID` | Yes | - | Organization ID for agent runs |
| `CODEGEN_API_BASE_URL` | No | `https://dev--rest-api.modal.run` | API endpoint URL |

### Authentication

The MCP server uses Bearer token authentication:

```
Authorization: Bearer sk-xxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

Your token is automatically included in all API requests when set via `CODEGEN_API_KEY`.

---

## Core Features

### 1. Create Agent Run

Launch an autonomous AI agent to execute a development task.

**Tool Name:** `create_agent_run`

**Parameters:**
- `org_id` (integer, required): Organization ID (default: 323)
- `prompt` (string, required): Task description for the agent
- `repo_name` (string, optional): Target repository
- `branch_name` (string, optional): Target branch

**Example:**
```python
{
  "org_id": 323,
  "prompt": "Fix the login authentication bug in auth.py and add unit tests",
  "repo_name": "myapp",
  "branch_name": "main"
}
```

**Response:**
```json
{
  "id": 12345,
  "status": "PENDING",
  "created_at": "2025-01-15T10:30:00Z",
  "prompt": "Fix the login authentication bug in auth.py and add unit tests",
  "repo_name": "myapp",
  "branch_name": "main",
  "web_url": "https://codegen.com/traces/12345"
}
```

### 2. Get Agent Run Status

Check the status and retrieve results of a specific agent run.

**Tool Name:** `get_agent_run`

**Parameters:**
- `org_id` (integer, required): Organization ID
- `agent_run_id` (integer, required): Agent run ID to query

**Example:**
```python
{
  "org_id": 323,
  "agent_run_id": 12345
}
```

**Response:**
```json
{
  "id": 12345,
  "status": "COMPLETE",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:45:00Z",
  "prompt": "Fix the login authentication bug in auth.py and add unit tests",
  "result": {
    "summary": "Fixed authentication issue and added 5 unit tests",
    "files_modified": ["auth.py", "test_auth.py"],
    "pull_request_url": "https://github.com/org/repo/pull/123",
    "commits": ["abc123", "def456"]
  },
  "repo_name": "myapp",
  "branch_name": "main",
  "web_url": "https://codegen.com/traces/12345"
}
```

### 3. List Agent Runs

Retrieve a paginated list of agent runs with optional filtering.

**Tool Name:** `list_agent_runs`

**Parameters:**
- `org_id` (integer, required): Organization ID
- `status` (string, optional): Filter by status (see [Status States](#status-states))
- `page` (integer, optional): Page number (default: 1)
- `page_size` (integer, optional): Results per page (default: 10, max: 100)

**Example:**
```python
{
  "org_id": 323,
  "status": "ACTIVE",
  "page": 1,
  "page_size": 10
}
```

### 4. Resume Agent Run

To resume or continue an agent run, simply create a new agent run with reference to the previous one:

```python
{
  "org_id": 323,
  "prompt": "Continue the previous task from agent run #12345 - add integration tests",
  "repo_name": "myapp",
  "branch_name": "main"
}
```

---

## API Endpoints

### Base URL
```
https://dev--rest-api.modal.run
```

### Endpoints Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/organizations/{org_id}/agent/run` | Create agent run |
| `GET` | `/v1/organizations/{org_id}/agent/run/{agent_run_id}` | Get agent run details |
| `GET` | `/v1/organizations/{org_id}/agent/runs` | List agent runs |
| `GET` | `/v1/users/me` | Get current user |
| `GET` | `/v1/organizations` | List organizations |
| `GET` | `/v1/organizations/{org_id}/users` | List users |
| `GET` | `/v1/organizations/{org_id}/users/{user_id}` | Get user details |

### Authentication Header
```
Authorization: Bearer {your-api-token}
```

---

## Testing Examples

### Example 1: Create and Monitor Agent Run

```python
from codegen import Agent
import time

# Initialize agent
agent = Agent(
    org_id=323,
    token="sk-92083737-4e5b-4a48-a2a1-f870a3a096a6"
)

# Create agent run
task = agent.run("Generate comprehensive API documentation for the user service")

print(f"Created agent run: {task.id}")
print(f"Initial status: {task.status}")
print(f"View in dashboard: {task.web_url}")

# Poll for completion
while task.status in ["PENDING", "ACTIVE", "RUNNING"]:
    time.sleep(10)  # Wait 10 seconds
    task.refresh()
    print(f"Status: {task.status}")

# Check final result
if task.status == "COMPLETE":
    print("✅ Agent completed successfully!")
    print(f"Result: {task.result}")
else:
    print(f"❌ Agent ended with status: {task.status}")
```

### Example 2: List Active Agents

```python
from codegen import Agent
import requests

token = "sk-92083737-4e5b-4a48-a2a1-f870a3a096a6"
org_id = 323

headers = {"Authorization": f"Bearer {token}"}
params = {
    "status": "ACTIVE",
    "page": 1,
    "page_size": 20
}

response = requests.get(
    f"https://dev--rest-api.modal.run/v1/organizations/{org_id}/agent/runs",
    headers=headers,
    params=params
)

data = response.json()
print(f"Found {data['total']} active agents")

for run in data['items']:
    print(f"- Agent #{run['id']}: {run['prompt'][:50]}... ({run['status']})")
```

### Example 3: MCP Tool Call via Claude Desktop

```typescript
// In Claude Desktop or compatible MCP client
await use_mcp_tool("codegen", "create_agent_run", {
  org_id: 323,
  prompt: "Add error handling to the payment processing module",
  repo_name: "ecommerce-backend",
  branch_name: "main"
});

// Poll for completion
const runId = response.id;
let status = "PENDING";

while (["PENDING", "ACTIVE", "RUNNING"].includes(status)) {
  await sleep(15000); // Wait 15 seconds
  
  const result = await use_mcp_tool("codegen", "get_agent_run", {
    org_id: 323,
    agent_run_id: runId
  });
  
  status = result.status;
  console.log(`Agent status: ${status}`);
}

console.log("Agent completed!", result);
```

### Example 4: Batch Agent Creation

```python
from codegen import Agent

agent = Agent(org_id=323, token="sk-92083737-4e5b-4a48-a2a1-f870a3a096a6")

tasks = [
    "Add input validation to all API endpoints",
    "Write unit tests for the authentication module",
    "Update README with deployment instructions",
    "Refactor database queries for better performance",
    "Add logging to error handlers"
]

runs = []
for task_prompt in tasks:
    task = agent.run(task_prompt)
    runs.append({
        "id": task.id,
        "prompt": task_prompt,
        "status": task.status
    })
    print(f"✅ Created agent run #{task.id}")

print(f"\n📊 Created {len(runs)} agent runs")
for run in runs:
    print(f"  - #{run['id']}: {run['prompt'][:40]}...")
```

### Example 5: Error Handling

```python
from codegen import Agent
import time

agent = Agent(org_id=323, token="sk-92083737-4e5b-4a48-a2a1-f870a3a096a6")

try:
    task = agent.run("Implement user authentication with OAuth2")
    
    # Monitor with timeout
    max_wait = 600  # 10 minutes
    elapsed = 0
    
    while task.status in ["PENDING", "ACTIVE", "RUNNING"] and elapsed < max_wait:
        time.sleep(30)
        elapsed += 30
        task.refresh()
        print(f"[{elapsed}s] Status: {task.status}")
    
    if task.status == "COMPLETE":
        print("✅ Success!")
        print(f"Results: {task.result}")
    elif task.status in ["ERROR", "FAILED"]:
        print(f"❌ Agent failed with status: {task.status}")
        print(f"Check dashboard: {task.web_url}")
    elif elapsed >= max_wait:
        print("⏱️ Timeout reached, agent still running")
        print(f"Monitor at: {task.web_url}")
    
except Exception as e:
    print(f"❌ Error: {e}")
```

---

## Status States

Agent runs progress through several states:

| Status | Description | Terminal | Next States |
|--------|-------------|----------|-------------|
| `PENDING` | Agent run queued, waiting to start | No | `ACTIVE`, `CANCELLED` |
| `ACTIVE` | Agent is being initialized | No | `RUNNING`, `ERROR` |
| `RUNNING` | Agent is actively executing task | No | `COMPLETE`, `ERROR`, `FAILED`, `STOPPED` |
| `COMPLETE` | Agent successfully completed task | Yes | - |
| `ERROR` | Agent encountered an error | Yes | - |
| `FAILED` | Agent failed to complete task | Yes | - |
| `CANCELLED` | Agent run was cancelled by user | Yes | - |
| `STOPPED` | Agent was stopped mid-execution | Yes | - |

### Polling Best Practices

1. **Initial delay**: Wait 5-10 seconds before first status check
2. **Poll interval**: Check every 10-30 seconds while `RUNNING`
3. **Timeout**: Set reasonable timeout (5-15 minutes depending on task)
4. **Exponential backoff**: Increase wait time if agent runs long
5. **Terminal states**: Stop polling when status is terminal

### Example Polling Loop

```python
import time

def wait_for_completion(task, timeout=600):
    """Wait for agent run to complete with timeout."""
    elapsed = 0
    interval = 10  # Start with 10 second intervals
    
    while elapsed < timeout:
        task.refresh()
        
        # Check if terminal state
        if task.status in ["COMPLETE", "ERROR", "FAILED", "CANCELLED", "STOPPED"]:
            return task.status
        
        # Wait before next check
        time.sleep(interval)
        elapsed += interval
        
        # Increase interval gradually
        interval = min(interval + 5, 30)
    
    return "TIMEOUT"

status = wait_for_completion(task)
print(f"Final status: {status}")
```

---

## Troubleshooting

### Common Issues

#### 1. Authentication Failed

**Error:** `401 Unauthorized`

**Solution:**
- Verify `CODEGEN_API_KEY` is set correctly
- Check token hasn't expired
- Ensure token has proper Bearer format

```bash
# Test authentication
curl -H "Authorization: Bearer sk-your-token" \
     https://dev--rest-api.modal.run/v1/users/me
```

#### 2. Organization Not Found

**Error:** `404 Not Found` or `403 Forbidden`

**Solution:**
- Verify `CODEGEN_ORG_ID` is correct
- Ensure you have access to the organization
- Check organization exists

```python
from codegen import Agent

agent = Agent(org_id=323, token="your-token")
# This will validate access on first API call
```

#### 3. Agent Stuck in PENDING

**Symptoms:** Agent status stays `PENDING` for extended period

**Solution:**
- Check Codegen service status
- Verify organization has capacity for new agents
- Review any rate limits or quotas
- Contact support if issue persists

#### 4. MCP Server Not Starting

**Error:** Server fails to start or tools not available

**Solution:**
- Verify Python environment has `codegen` package installed
- Check `CODEGEN_API_KEY` environment variable is set
- Review MCP client logs for detailed errors
- Ensure `uvx` or `python` command is available

```bash
# Test MCP server locally
python -m codegen.cli.mcp.server

# Or with uvx
uvx --from codegen codegen-mcp-server
```

#### 5. Rate Limiting

**Error:** `429 Too Many Requests`

**Solution:**
- Implement exponential backoff
- Reduce request frequency
- Contact support for rate limit increase

```python
import time
import requests

def retry_with_backoff(func, max_retries=3):
    for i in range(max_retries):
        try:
            return func()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                wait = (2 ** i) * 5  # Exponential backoff
                print(f"Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise Exception("Max retries exceeded")
```

### Debug Mode

Enable detailed logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("codegen")
logger.setLevel(logging.DEBUG)
```

### Getting Help

- **Documentation**: https://docs.codegen.com
- **GitHub Issues**: https://github.com/codegen-sh/codegen/issues
- **Support**: support@codegen.com
- **Dashboard**: https://codegen.com/traces

---

## Advanced Usage

### Custom API Base URL

For self-hosted or enterprise deployments:

```json
{
  "mcpServers": {
    "codegen": {
      "env": {
        "CODEGEN_API_BASE_URL": "https://your-custom-domain.com/api"
      }
    }
  }
}
```

### Multiple Organizations

Configure separate MCP servers for different organizations:

```json
{
  "mcpServers": {
    "codegen-org-dev": {
      "command": "uvx",
      "args": ["--from", "codegen", "codegen-mcp-server"],
      "env": {
        "CODEGEN_API_KEY": "sk-dev-token",
        "CODEGEN_ORG_ID": "123"
      }
    },
    "codegen-org-prod": {
      "command": "uvx",
      "args": ["--from", "codegen", "codegen-mcp-server"],
      "env": {
        "CODEGEN_API_KEY": "sk-prod-token",
        "CODEGEN_ORG_ID": "456"
      }
    }
  }
}
```

### Webhook Integration

For real-time notifications when agent runs complete:

```python
# Configure webhook URL in Codegen dashboard
# Receive POST requests when agent status changes

from flask import Flask, request

app = Flask(__name__)

@app.route("/webhook/codegen", methods=["POST"])
def handle_webhook():
    data = request.json
    agent_run_id = data["agent_run_id"]
    status = data["status"]
    
    print(f"Agent #{agent_run_id} status: {status}")
    
    if status == "COMPLETE":
        # Handle completion
        result = data["result"]
        notify_team(f"Agent completed: {result['summary']}")
    
    return {"status": "ok"}
```

---

## SDK Reference

### Agent Class

```python
from codegen import Agent

class Agent:
    def __init__(
        self,
        token: str,
        org_id: int = None,
        base_url: str = None
    ):
        """
        Initialize Codegen Agent.
        
        Args:
            token: API authentication token
            org_id: Organization ID (optional)
            base_url: Custom API base URL (optional)
        """
        pass
    
    def run(self, prompt: str) -> AgentTask:
        """
        Create and run an agent task.
        
        Args:
            prompt: Task description for the agent
            
        Returns:
            AgentTask: Task object with status and results
        """
        pass
    
    def get_status(self) -> dict:
        """
        Get status of the current task.
        
        Returns:
            dict: Status information including id, status, result
        """
        pass
```

### AgentTask Class

```python
class AgentTask:
    id: int                    # Unique task ID
    org_id: int               # Organization ID
    status: str               # Current status
    result: dict | None       # Task results (when complete)
    web_url: str              # Dashboard URL
    
    def refresh(self) -> None:
        """Refresh task status from API."""
        pass
```

---

## Best Practices

1. **Always poll for completion** - Don't assume immediate completion
2. **Handle all status states** - Account for errors and failures
3. **Set reasonable timeouts** - Different tasks take different times
4. **Use exponential backoff** - Be kind to API rate limits
5. **Log agent run IDs** - For debugging and monitoring
6. **Monitor dashboard** - Use web_url for detailed insights
7. **Test in development** - Validate prompts before production
8. **Batch similar tasks** - More efficient than sequential runs
9. **Handle errors gracefully** - Implement retry logic
10. **Keep prompts clear** - Better prompts = better results

---

## Version History

- **v1.0.0** (2025-01-15): Initial MCP server release
  - Core CRUD operations for agent runs
  - Organization and user management
  - Status monitoring and result retrieval
  - Full MCP protocol compliance

---

## License

Codegen SDK is released under the MIT License. See LICENSE file for details.

---

## Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.

**Maintained by:** Codegen Team (https://codegen.com)
**Last Updated:** January 15, 2025

