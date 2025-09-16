# Codegen Workflows Integration

## Overview

The Codegen Workflows Integration provides a comprehensive CI/CD completion validation layer using the [workflows-py](https://github.com/run-llama/workflows) library. This integration enables event-driven, async-first orchestration of complex validation processes for agent runs, code changes, and deployments.

## Key Features

- **Event-Driven Architecture**: Automatic workflow triggering based on database events
- **Async-First Design**: Built on Python's asyncio for high performance
- **Flexible Validation Types**: Multiple workflow types for different scenarios
- **Quality Gate Enforcement**: Policy-based validation with configurable thresholds
- **Real-Time Monitoring**: WebSocket streaming and metrics collection
- **Integration Ready**: Seamless integration with GitHub, Linear, Slack, and other tools

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Database      │    │  Workflow        │    │  Validation     │
│   Events        │───▶│  Manager         │───▶│  Workflows      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Quality       │    │  Workflow        │    │  Event          │
│   Gates         │◀───│  Server          │───▶│  Emitter        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Components

### 1. CodegenValidationWorkflow

The main validation workflow that orchestrates comprehensive CI/CD validation:

```python
from src.codegen.workflows import CodegenValidationWorkflow, ValidationConfig

# Create a custom validation workflow
config = ValidationConfig(
    enable_code_quality=True,
    enable_security_scan=True,
    enable_deployment_validation=True,
    parallel_execution=True,
    timeout_minutes=30,
)

workflow = CodegenValidationWorkflow(config)
```

### 2. CodegenWorkflowServer

HTTP server for serving validation workflows as web services:

```python
from src.codegen.workflows import create_workflow_server

# Create and start workflow server
server = create_workflow_server(
    host="localhost",
    port=8080,
    enable_auto_triggers=True,
)

# Start validation workflow
result = await server.start_validation(
    agent_run_id="agent-run-123",
    organization_id="org-456",
    workflow_type="full-validation",
)
```

### 3. WorkflowManager

High-level manager for policy-based workflow orchestration:

```python
from src.codegen.workflows import create_workflow_manager, WorkflowPolicy

# Create policy
policy = WorkflowPolicy(
    max_concurrent_workflows=10,
    required_validations={"code_quality", "security"},
    blocking_severities={ValidationSeverity.ERROR, ValidationSeverity.CRITICAL},
)

# Create manager
manager = create_workflow_manager(policy=policy)

# Start validation with priority
result = await manager.start_validation_workflow(
    agent_run_id="agent-run-123",
    organization_id="org-456",
    priority=8,
)
```

## Workflow Types

### 1. Default Validation (`validation`)
- **Duration**: ~10-15 minutes
- **Includes**: Agent run validation, code quality, security
- **Use Case**: Standard agent run validation

### 2. Fast Validation (`fast-validation`)
- **Duration**: ~2-5 minutes
- **Includes**: Code quality checks only
- **Use Case**: PR updates and quick checks

### 3. Security Validation (`security-validation`)
- **Duration**: ~5-10 minutes
- **Includes**: Security scanning, secrets detection, vulnerability analysis
- **Use Case**: GitHub check suites and security reviews

### 4. Full Validation (`full-validation`)
- **Duration**: ~15-30 minutes
- **Includes**: All validation types plus deployment checks
- **Use Case**: PR creation and production deployments

## Validation Steps

### 1. Agent Run Validation
- Completion status verification
- Output file validation
- Resource usage analysis
- Token and API call limits

### 2. Code Quality Validation
- Linting and style checks
- Test coverage analysis
- Code complexity metrics
- Documentation completeness

### 3. Security Validation
- Secret scanning (TruffleHog integration)
- Vulnerability scanning
- Dependency security analysis
- Static Application Security Testing (SAST)

### 4. Deployment Validation
- Health check verification
- Configuration validation
- Resource availability
- Rollback capability

## Event Integration

The workflow system automatically triggers on these events:

### Agent Run Events
```python
# Triggered when agent run completes
{
    "event_type": "agentrun.completed",
    "data": {
        "id": "agent-run-123",
        "status": "completed",
        "output_files": ["src/auth.py", "tests/test_auth.py"]
    }
}
```

### Pull Request Events
```python
# Triggered on PR creation/update
{
    "event_type": "pullrequest.created",
    "data": {
        "number": 42,
        "head_sha": "abc123",
        "agent_run_id": "agent-run-123"
    }
}
```

### GitHub Check Suite Events
```python
# Triggered by GitHub check suite requests
{
    "event_type": "github.check_suite.requested",
    "data": {
        "check_suite_id": "12345",
        "head_sha": "abc123",
        "action": "requested"
    }
}
```

## Quality Gates

Quality gates enforce validation policies and prevent deployment of problematic code:

```python
# Configure quality gates
policy = WorkflowPolicy(
    required_validations={"code_quality", "security", "deployment"},
    blocking_severities={ValidationSeverity.ERROR, ValidationSeverity.CRITICAL},
)

# Enforce quality gates
result = await manager.enforce_quality_gates(
    workflow_id="workflow-123",
    validation_results=validation_results
)

if not result["passed"]:
    print(f"Quality gates failed: {result['reason']}")
    # Block deployment or merge
```

## Configuration

### Environment Variables
```bash
# Workflow server configuration
CODEGEN_WORKFLOW_HOST=localhost
CODEGEN_WORKFLOW_PORT=8080
CODEGEN_WORKFLOW_TIMEOUT=1800

# Validation configuration
CODEGEN_ENABLE_CODE_QUALITY=true
CODEGEN_ENABLE_SECURITY_SCAN=true
CODEGEN_ENABLE_DEPLOYMENT_VALIDATION=true

# Quality gates
CODEGEN_REQUIRED_VALIDATIONS=code_quality,security
CODEGEN_BLOCKING_SEVERITIES=error,critical

# Notifications
CODEGEN_NOTIFICATION_CHANNELS=slack,email
CODEGEN_SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

### Policy Configuration
```python
policy = WorkflowPolicy(
    # Trigger conditions
    trigger_on_agent_completion=True,
    trigger_on_pr_creation=True,
    trigger_on_pr_update=True,
    trigger_on_check_suite=True,
    
    # Workflow selection
    default_workflow_type="validation",
    pr_workflow_type="full-validation",
    update_workflow_type="fast-validation",
    check_suite_workflow_type="security-validation",
    
    # Execution limits
    max_concurrent_workflows=10,
    max_retries=3,
    timeout_minutes=30,
    
    # Quality gates
    required_validations={"code_quality", "security"},
    blocking_severities={ValidationSeverity.ERROR, ValidationSeverity.CRITICAL},
    
    # Notifications
    notify_on_failure=True,
    notify_on_success=False,
    notification_channels=["slack", "email"],
)
```

## API Endpoints

The workflow server exposes REST API endpoints:

### Start Validation
```http
POST /workflows/validation/run
Content-Type: application/json

{
    "agent_run_id": "agent-run-123",
    "organization_id": "org-456",
    "workflow_type": "full-validation",
    "pr_number": 42,
    "commit_sha": "abc123"
}
```

### Get Workflow Status
```http
GET /results/{workflow_id}
```

### Stream Events
```http
GET /events/{workflow_id}
Accept: text/event-stream
```

### List Workflows
```http
GET /workflows
```

## Metrics and Monitoring

The system provides comprehensive metrics:

```python
# Get workflow metrics
metrics = manager.get_workflow_metrics()
print(f"Success rate: {metrics['success_rate']}%")
print(f"Average duration: {metrics['average_duration']}s")

# Organization-specific metrics
org_metrics = manager.get_organization_metrics("org-123")
print(f"Active workflows: {org_metrics['active_workflows']}")
```

### Available Metrics
- Total workflows executed
- Success/failure rates
- Average execution duration
- Quality gate failure rate
- Resource utilization
- Queue depth and processing time

## Integration Examples

### GitHub Actions Integration
```yaml
name: Codegen Validation
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Codegen Validation
        run: |
          curl -X POST "$CODEGEN_WORKFLOW_URL/workflows/full-validation/run" \
            -H "Content-Type: application/json" \
            -d '{
              "agent_run_id": "${{ github.event.pull_request.head.sha }}",
              "organization_id": "${{ github.repository_owner }}",
              "pr_number": ${{ github.event.pull_request.number }},
              "commit_sha": "${{ github.event.pull_request.head.sha }}"
            }'
```

### Slack Notifications
```python
# Configure Slack notifications
policy = WorkflowPolicy(
    notification_channels=["slack"],
    notify_on_failure=True,
    notify_on_success=True,
)

# Notifications are sent automatically on workflow completion
```

### Linear Integration
```python
# Automatic Linear issue creation on validation failure
async def handle_validation_failure(event):
    if event.data["status"] == "failed":
        await linear_client.create_issue(
            title=f"Validation failed for {event.data['agent_run_id']}",
            description=f"Workflow failed: {event.data['summary']}",
            team_id="team-123",
        )
```

## Installation

### Prerequisites
```bash
# Install workflows-py
pip install llama-index-workflows

# Install additional dependencies
pip install uvicorn starlette pydantic
```

### Setup
```python
# Initialize workflow system
from src.codegen.workflows import create_workflow_manager

# Create manager with default configuration
manager = create_workflow_manager()

# Start background services
await manager.serve()
```

## Best Practices

### 1. Workflow Design
- Use parallel execution for independent validations
- Implement proper error handling and retries
- Set appropriate timeouts for each validation step
- Use fail-fast for critical validations

### 2. Quality Gates
- Define clear validation requirements
- Set appropriate severity thresholds
- Implement gradual rollout for new validations
- Monitor quality gate effectiveness

### 3. Performance
- Optimize validation steps for speed
- Use caching for repeated validations
- Implement resource limits and throttling
- Monitor and tune execution times

### 4. Monitoring
- Set up comprehensive logging
- Monitor workflow success rates
- Track validation performance metrics
- Implement alerting for failures

## Troubleshooting

### Common Issues

#### Workflow Timeouts
```python
# Increase timeout for long-running validations
config = ValidationConfig(timeout_minutes=45)
```

#### Resource Limits
```python
# Adjust concurrent workflow limits
policy = WorkflowPolicy(max_concurrent_workflows=5)
```

#### Quality Gate Failures
```python
# Review and adjust quality gate policies
policy = WorkflowPolicy(
    blocking_severities={ValidationSeverity.CRITICAL},  # Less strict
)
```

### Debugging
```python
# Enable debug logging
import logging
logging.getLogger("src.codegen.workflows").setLevel(logging.DEBUG)

# Check workflow status
status = manager.get_workflow_status("workflow-123")
print(f"Current step: {status['current_step']}")
print(f"Completed steps: {status['completed_steps']}")
```

## Future Enhancements

- **Custom Validation Steps**: Plugin system for custom validations
- **Advanced Scheduling**: Cron-based and conditional triggers
- **Multi-Environment Support**: Environment-specific validation policies
- **Advanced Analytics**: ML-based failure prediction and optimization
- **Integration Expansion**: Additional tool integrations (Jira, Teams, etc.)

## Contributing

To contribute to the workflows integration:

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add comprehensive tests
5. Update documentation
6. Submit a pull request

## Support

For support and questions:
- GitHub Issues: [Create an issue](https://github.com/Zeeeepa/codegen/issues)
- Documentation: [Workflows Integration Docs](./workflows_integration.md)
- Examples: [Integration Examples](../examples/workflows_integration_example.py)
