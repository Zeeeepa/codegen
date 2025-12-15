## 🎯 Controller Dashboard - Comprehensive Guide

### Overview

The **Controller Dashboard** is a powerful workflow management and sandbox execution system for Codegen, providing:

- 🔄 **Workflow Management** - Create, configure, and toggle workflows on/off with state persistence
- 🔬 **Sandboxed Execution** - Isolated, parallel execution environments with resource management
- 📈 **Real-Time Monitoring** - Live tracking of execution status, metrics, and logs
- 📊 **Projects & PRDs** - Manage projects and Product Requirements Documents
- 🎨 **Interactive TUI** - Terminal-based user interface with tab navigation

---

## 🚀 Quick Start

### Installation

```bash
# Install Codegen CLI
pip install codegen

# Authenticate
codegen login

# Launch Controller Dashboard
codegen tui
```

### Navigate to Controller Tabs

Once in the TUI, use **Tab** or **Shift+Tab** to navigate between views:

- **Workflows** - Manage and execute workflows
- **Sandboxes** - Monitor active execution environments
- **Monitoring** - Real-time metrics and resource usage
- **Projects** - Project management
- **PRDs** - Product Requirements Documents

---

## 📋 Features

### 1. Workflow Management

#### Create Workflows

```python
from codegen.cli.tui.controller_dashboard import WorkflowConfig, WorkflowStatus
from datetime import datetime

workflow = WorkflowConfig(
    id="my-workflow",
    name="Automated Code Review",
    description="AI-powered code quality analysis",
    status=WorkflowStatus.ENABLED,
    created_at=datetime.now(),
    updated_at=datetime.now(),
    enabled=True,
    parallel_execution=True,
    max_instances=3,
    schedule="0 */4 * * *",  # Every 4 hours
    tags=["code-quality", "automated"],
    retry_policy={
        "max_retries": 3,
        "backoff_multiplier": 2
    }
)
```

#### Toggle Workflows

```python
# Enable/disable workflow
controller.toggle_workflow("my-workflow")

# Via TUI: Press [Space] on selected workflow
```

#### Execute Workflows

```python
# Execute workflow with parameters
run_id = controller.execute_workflow_in_sandbox(
    workflow_id="my-workflow",
    params={
        "target": "src/",
        "analysis_type": "full"
    }
)
```

---

### 2. Sandbox Execution

#### Create Isolated Sandboxes

```python
# Create sandbox for workflow
sandbox_id = controller.create_sandbox("my-workflow")

# Sandboxes provide:
# - Complete execution isolation
# - Independent resource allocation
# - Automatic cleanup after completion
# - Real-time status tracking
```

#### Parallel Execution

```python
# Configure workflow for parallel execution
workflow.parallel_execution = True
workflow.max_instances = 5

# Launch multiple executions simultaneously
for module in ["module_a", "module_b", "module_c"]:
    controller.execute_workflow_in_sandbox(
        "my-workflow",
        params={"module": module}
    )

# All executions run in isolated sandboxes
active_sandboxes = controller.get_parallel_executions("my-workflow")
print(f"Active: {len(active_sandboxes)}")
```

#### Monitor Sandbox Status

```python
# Get real-time sandbox status
status = controller.monitor_sandbox(sandbox_id)

print(f"Status: {status['status']}")
print(f"Metrics: {status['metrics']}")
print(f"Resource Usage: {status['resource_usage']}")
print(f"Logs: {status['logs']}")
```

#### Terminate Sandbox

```python
# Gracefully terminate execution
controller.terminate_sandbox(sandbox_id)

# Via TUI: Press [t] on selected sandbox
```

---

### 3. Real-Time Monitoring

#### Start Monitoring

```python
# Enable real-time monitoring
controller.start_monitoring()

# Monitoring automatically:
# - Polls active sandboxes every 5 seconds
# - Collects metrics and resource usage
# - Stores historical data
# - Detects completion and errors
```

#### View Metrics History

```python
# Access collected metrics
for sandbox_id, history in controller.metrics_history.items():
    print(f"\nSandbox: {sandbox_id}")
    for entry in history:
        print(f"  {entry['timestamp']}: {entry['metrics']}")
```

#### Stop Monitoring

```python
# Disable monitoring
controller.stop_monitoring()
```

---

### 4. Workflow Configuration

#### Scheduling

```python
# Cron-based scheduling
workflow.schedule = "0 2 * * *"  # Daily at 2 AM
workflow.schedule = "0 */6 * * *"  # Every 6 hours
workflow.schedule = "0 0 * * 0"  # Weekly on Sunday
```

#### Retry Policies

```python
workflow.retry_policy = {
    "max_retries": 3,
    "backoff_multiplier": 2,
    "initial_delay_seconds": 1,
    "max_delay_seconds": 60
}
```

#### Dependencies

```python
workflow.dependencies = [
    "database-migration",
    "environment-setup"
]
```

---

## 🎨 TUI Interface

### Workflows Tab

```
╔════════════════════════════════════════════════════════════════════════════╗
║                    🎯 WORKFLOW CONTROLLER DASHBOARD                         ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 SUMMARY
────────────────────────────────────────────────────────────────────────────
Total Workflows: 5 | Enabled: 4 | Disabled: 1 | Running: 2
Active Sandboxes: 3 | Total Sandboxes: 8

📋 WORKFLOWS
────────────────────────────────────────────────────────────────────────────
1. 🟢 Automated Code Review
   ✓ ENABLED | Status: running
   AI-powered code quality analysis
   ⏰ Schedule: 0 */4 * * *
   🔄 Active Executions: 2

2. 🟢 PR Generator
   ✓ ENABLED | Status: enabled
   Generate PRs from task descriptions with tests

Commands: [Space] Toggle | [Enter] Details | [r] Run | [m] Monitor | [q] Quit
```

### Sandboxes Tab

```
╔════════════════════════════════════════════════════════════════════════════╗
║                    🔬 SANDBOX EXECUTION MONITOR                             ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 SANDBOX STATUS
────────────────────────────────────────────────────────────────────────────
Active: 3 | Idle: 5 | Error: 0

🔍 ACTIVE SANDBOXES
────────────────────────────────────────────────────────────────────────────
● sandbox-wf-code-review-1734234567
  Workflow: wf-code-review
  Status: running
  Started: 14:25:30
  Metrics: token_usage=1250, execution_time=12.5s

Commands: [r] Refresh | [t] Terminate Selected | [Enter] Details | [q] Quit
```

### Monitoring Tab

```
╔════════════════════════════════════════════════════════════════════════════╗
║                    📈 REAL-TIME MONITORING DASHBOARD                        ║
╚════════════════════════════════════════════════════════════════════════════╝

Monitoring Status: 🟢 ACTIVE

📊 METRICS HISTORY
────────────────────────────────────────────────────────────────────────────

sandbox-wf-code-review-1734234567:
  Latest Update: 2025-12-15T02:25:45Z
  Metrics: {token_usage: 1250, api_calls: 5, success_rate: 100%}
  Resources: {cpu: 45%, memory: 512MB, network: 2.5Mbps}

Commands: [s] Stop Monitoring | [r] Refresh | [q] Quit
```

---

## 🔧 API Endpoints

### Workflow Endpoints

```http
GET    /workflows                    # List all workflows
GET    /workflows/{workflow_id}      # Get workflow details
POST   /workflows                    # Create workflow
PATCH  /workflows/{workflow_id}      # Update workflow
POST   /workflows/{workflow_id}/toggle      # Toggle enabled/disabled
POST   /workflows/{workflow_id}/execute     # Execute workflow
GET    /workflows/{workflow_id}/metrics     # Get metrics
```

### Sandbox Endpoints

```http
GET    /sandboxes                    # List sandboxes
GET    /sandboxes/{sandbox_id}/status       # Get status
POST   /sandboxes/{sandbox_id}/terminate    # Terminate sandbox
```

### Project Endpoints

```http
GET    /projects                     # List projects
POST   /projects                     # Create project
GET    /projects/{project_id}        # Get project details
```

### PRD Endpoints

```http
GET    /prds                         # List PRDs
POST   /prds                         # Create PRD
GET    /prds/{prd_id}                # Get PRD details
```

---

## 💻 Practical Examples

### Example 1: Simple Workflow Execution

```python
from codegen.cli.workflows.execution_examples import WorkflowExecutionExamples
import asyncio

async def simple_example():
    examples = WorkflowExecutionExamples()
    await examples.example_1_simple_workflow_execution()

asyncio.run(simple_example())
```

### Example 2: Parallel Execution

```python
async def parallel_example():
    examples = WorkflowExecutionExamples()
    await examples.example_2_parallel_execution()

asyncio.run(parallel_example())
```

### Example 3: Real-Time Monitoring

```python
async def monitoring_example():
    examples = WorkflowExecutionExamples()
    await examples.example_3_workflow_with_monitoring()

asyncio.run(monitoring_example())
```

### Run All Examples

```python
from codegen.cli.workflows.execution_examples import main

# Run all practical examples
asyncio.run(main())
```

---

## 🏗️ Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Controller Dashboard                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐ │
│  │   Workflow     │  │    Sandbox     │  │   Monitoring   │ │
│  │   Manager      │  │    Manager     │  │    System      │ │
│  └────────────────┘  └────────────────┘  └───────────────┘ │
│           │                  │                    │           │
│           └──────────────────┴────────────────────┘           │
│                             │                                │
│                   ┌─────────▼────────────┐                   │
│                   │   Controller API     │                   │
│                   └──────────────────────┘                   │
│                             │                                │
│                   ┌─────────▼────────────┐                   │
│                   │    Modal Backend     │                   │
│                   └──────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Action → TUI → Controller → API → Modal → Sandbox
                                               │
                                               ▼
                                          Execution
                                               │
                                               ▼
                                          Monitoring ← Metrics Collection
                                               │
                                               ▼
                                          Results → Storage
```

---

## 🛡️ Security & Isolation

### Sandbox Isolation

- **Process Isolation**: Each sandbox runs in separate Modal container
- **Resource Limits**: Configurable CPU, memory, and network quotas
- **Org Isolation**: Multi-tenant separation via `org_id` filtering
- **No Cross-Contamination**: Completely independent execution contexts

### Authentication

```python
# All API calls require authentication
headers = {
    "Authorization": f"Bearer {token}"
}

# Organization-scoped operations
params = {
    "org_id": org_id
}
```

---

## 📊 Metrics & Observability

### Tracked Metrics

- **Execution Metrics**
  - Start/end timestamps
  - Duration
  - Success/failure rate
  - Retry attempts

- **Resource Metrics**
  - CPU usage
  - Memory consumption
  - Network bandwidth
  - Token usage

- **Cost Metrics**
  - API call counts
  - Token consumption
  - Resource hours
  - Estimated cost

### OpenTelemetry Integration

```python
# Automatic tracing and metrics collection
logger.info("Workflow executed", extra={
    "workflow_id": workflow_id,
    "sandbox_id": sandbox_id,
    "run_id": run_id,
    "duration": duration,
    "status": "success"
})
```

---

## 🔗 Integration with Existing Systems

### GitHub Integration

```python
# Workflows can trigger GitHub actions
workflow_config = {
    "github_integration": {
        "auto_create_pr": True,
        "auto_comment": True,
        "status_checks": True
    }
}
```

### Linear Integration

```python
# Workflows can update Linear issues
workflow_config = {
    "linear_integration": {
        "update_on_completion": True,
        "auto_close_on_success": True
    }
}
```

---

## 🎓 Best Practices

### Workflow Design

1. **Keep workflows focused** - One responsibility per workflow
2. **Use meaningful names** - Clear, descriptive workflow names
3. **Configure retry policies** - Handle transient failures
4. **Set resource limits** - Prevent runaway executions
5. **Tag workflows** - Organize with consistent tagging

### Sandbox Management

1. **Monitor active sandboxes** - Prevent resource exhaustion
2. **Clean up completed sandboxes** - Automatic or manual cleanup
3. **Set timeout limits** - Prevent infinite runs
4. **Use parallel execution wisely** - Balance speed vs. resources

### Monitoring

1. **Enable monitoring for production** - Always monitor critical workflows
2. **Set up alerts** - Notify on failures or anomalies
3. **Review metrics regularly** - Optimize based on data
4. **Store historical data** - Track trends over time

---

## 📚 Additional Resources

- [API Documentation](./api-documentation.md)
- [Workflow Examples](../src/codegen/cli/workflows/execution_examples.py)
- [TUI Integration Guide](./tui-integration.md)
- [Security Best Practices](./security.md)

---

## 🆘 Troubleshooting

### Common Issues

**Workflow won't execute**
- Check if workflow is enabled
- Verify authentication token
- Check max instances limit

**Sandbox stuck in initializing**
- Check Modal backend status
- Verify resource availability
- Review sandbox logs

**Monitoring not collecting data**
- Ensure monitoring is started
- Check if sandboxes are active
- Verify API connectivity

---

## 🚧 Roadmap

### Coming Soon

- [ ] Workflow templates marketplace
- [ ] Advanced scheduling (dependencies, triggers)
- [ ] Cost optimization recommendations
- [ ] Multi-region sandbox deployment
- [ ] Enhanced visualization dashboards
- [ ] Workflow versioning and rollback
- [ ] Integration with CI/CD pipelines
- [ ] Custom metrics and alerts

---

**Controller Dashboard - Bringing enterprise-grade workflow management to Codegen! 🎯**

