# Codegen Platform - Complete Features & Functions Documentation

## Table of Contents
1. [Overview](#overview)
2. [Core Capabilities](#core-capabilities)
3. [Python SDK](#python-sdk)
4. [Command-Line Interface (CLI)](#command-line-interface-cli)
5. [Integrations](#integrations)
6. [Sandbox Environment](#sandbox-environment)
7. [Configuration & Settings](#configuration--settings)
8. [Analytics & Monitoring](#analytics--monitoring)
9. [Security & Compliance](#security--compliance)

---

## Overview

**Codegen** is an enterprise-grade platform for running frontier code agents at scale. It provides the necessary building blocks (sandboxes, integrations, telemetry) for successful enterprise code agent deployments.

### Key Value Propositions
- **AI Co-worker**: Acts as an autonomous software engineer that understands coding challenges
- **Instant Codebase Access**: Quickly analyzes and navigates your codebase
- **Tool Integration**: Directly interacts with your development tools
- **SOC 2 Certified**: Type I & II certified with regular pen tests
- **Scalable**: Used by thousands of teams in production

---

## Core Capabilities

### 1. Code Understanding & Implementation
- **Feature Implementation**: Analyze requirements and implement new features
- **Bug Fixing**: Identify and fix bugs automatically
- **Code Refactoring**: Improve code quality and structure
- **Test Writing**: Generate comprehensive test suites
- **Documentation**: Create and improve technical documentation
- **Code Review**: Analyze code changes and provide feedback

### 2. Pull Request Management
- **PR Creation**: Automatically create well-documented PRs
- **PR Review**: Leave detailed code reviews with specific feedback
- **PR Comments**: Respond to review comments with code changes
- **Auto-fix Failed Checks**: Monitor CI/CD and automatically fix failures
- **Branch Management**: Create and manage feature branches
- **Commit Management**: Create properly formatted commits with co-author attribution

### 3. Task & Ticket Management
Supports multiple project management platforms:
- **Linear**: Update statuses, add comments, link PRs, create tasks
- **Jira**: Manage issues, add comments, update statuses
- **ClickUp**: Handle task assignments and comments
- **Monday.com**: Manage items and updates
- **GitHub Issues**: Comment on issues and manage assignments

### 4. Communication & Collaboration
- **Slack Integration**: Send notifications, ask for clarification, report progress
- **Direct Messages**: Interact via DM in Slack
- **Channel Mentions**: Tag @codegen in any Slack channel
- **Thread Responses**: Maintain context in conversation threads
- **Follow-up Questions**: Respond to clarification requests

### 5. Code Execution & Testing
- **Safe Code Execution**: Run code in isolated sandbox environments
- **Dependency Management**: Install and manage dependencies
- **Test Execution**: Run test suites and validate changes
- **Build Validation**: Ensure builds succeed before committing
- **Security Scanning**: Integrated TruffleHog for secret detection

### 6. Continuous Integration
- **CI/CD Monitoring**: Watch for build failures in real-time
- **Auto-fix System**: Automatically fix failed checks (up to 3 attempts)
- **Test Failure Analysis**: Analyze and fix failing tests
- **Linting Fixes**: Auto-correct linting issues
- **Build Error Resolution**: Diagnose and fix build errors

---

## Python SDK

### Installation
```python
pip install codegen  # Using pip
pipx install codegen  # Using pipx
uv tool install codegen  # Using uv
```

### Core SDK Features

#### Agent Class
Primary interface for programmatic interaction with Codegen agents.

**Initialization:**
```python
from codegen import Agent

agent = Agent(
    org_id="YOUR_ORG_ID",      # Organization ID
    token="YOUR_API_TOKEN",     # API authentication token
    base_url="..."              # Optional: custom API endpoint
)
```

#### Agent.run() Method
Execute agent tasks with custom prompts.

**Features:**
- **Asynchronous Execution**: Tasks run in background
- **Status Tracking**: Monitor task progress
- **Result Retrieval**: Access completed task outputs
- **Error Handling**: Graceful failure management

**Usage:**
```python
task = agent.run(prompt="Implement a new feature")
print(task.status)  # Check status
task.refresh()      # Update status
if task.status == "completed":
    print(task.result)
```

#### AgentTask Class
Represents a running or completed agent task.

**Attributes:**
- `status`: Current task status (pending, running, completed, failed)
- `result`: Task output (code, summaries, links)
- `task_id`: Unique task identifier
- `created_at`: Task creation timestamp

**Methods:**
- `refresh()`: Update task status from server
- `wait()`: Block until task completes
- `cancel()`: Stop a running task

### API Client Features
- **REST API Wrapper**: Pythonic interface to Codegen API
- **Authentication Management**: Token-based auth
- **Error Handling**: Comprehensive exception handling
- **Rate Limiting**: Built-in rate limit management
- **Retry Logic**: Automatic retry on transient failures

---

## Command-Line Interface (CLI)

### Installation & Setup
```bash
uv tool install codegen
codegen login  # Authenticate
```

### Core CLI Commands

#### `codegen`
Launch interactive terminal UI (TUI)
- **Browse Agents**: List and filter agent runs
- **View Runs**: See detailed execution logs
- **Manage Workflow**: Terminal-based workflow management
- **Real-time Updates**: Live status monitoring

#### `codegen login`
Authentication and token management
```bash
codegen login              # Interactive login
codegen login --token ...  # Direct token input
```

**Features:**
- Secure token storage
- Multi-organization support
- Session management

#### `codegen update`
Self-update system
```bash
codegen update              # Update to latest
codegen update --check      # Check for updates
codegen update --version X  # Specific version
codegen update --dry-run    # Preview changes
```

**Features:**
- Automatic daily update checks
- Notification system
- Version management
- Change preview

#### Additional CLI Capabilities
- **View Agent Logs**: Detailed execution traces
- **Pull Agent Work**: Download branches and changes locally
- **Create New Agents**: Trigger runs from command line
- **Run Claude Code**: Execute with OpenTelemetry monitoring
- **Manage Organizations**: Switch between orgs
- **Configure Repositories**: Manage repo settings

### Claude Code Integration
Run local Claude Code with cloud telemetry:
- **Full Logging**: Comprehensive execution traces
- **Remote Telemetry**: Surface traces in web UI
- **MCP Injection**: Access Codegen integrations via MCP
- **Analytics**: Performance monitoring and insights

---

## Integrations

### Communication Platforms

#### Slack
**Trigger Methods:**
- Tag @codegen in any channel
- Send direct messages
- Mention in threads

**Capabilities:**
- Send notifications
- Report progress updates
- Ask for clarification
- Provide status updates
- Share PR links
- Thread-based conversations

#### GitHub
**Capabilities:**
- Create and manage repositories
- Create pull requests
- Review PRs with inline comments
- Comment on issues
- Create branches
- Commit code changes
- Manage repository settings
- Monitor CI/CD checks

### Project Management

#### Linear
**Features:**
- Issue assignment triggers
- Comment mentions
- Status updates
- PR linking
- Task creation
- Progress tracking

#### Jira
**Features:**
- Issue assignment
- Comment integration
- Status management
- Workflow automation
- Custom field updates

#### ClickUp
**Features:**
- Task assignment triggers
- Comment mentions
- Status updates
- Task creation
- Priority management

#### Monday.com
**Features:**
- Item assignment
- Update creation
- Status changes
- Integration with boards

### Development Tools

#### CircleCI
**Capabilities:**
- CI/CD monitoring
- Build failure detection
- Pipeline integration
- Status tracking

#### Sentry
**Features:**
- Error monitoring integration
- Issue linking
- Error analysis
- Automated error fixes

#### Figma
**Capabilities:**
- Design file access
- Component inspection
- Design token extraction
- Collaboration on design implementations

#### PostgreSQL
**Features:**
- Database query execution
- Schema inspection
- Data analysis
- Database migrations

### Extensibility

#### Model Context Protocol (MCP)
**MCP Server Support:**
- Custom tool integration
- Protocol-based extensibility
- Third-party tool connections
- Organization-wide MCP server provisioning

**MCP Capabilities:**
- Define custom agent tools
- Extend agent functionality
- Connect external services
- Share tools across organization

#### Web Search
**Features:**
- Real-time web searches
- Context-aware queries
- Result summarization
- Information retrieval

#### Notion
**Capabilities:**
- Document access
- Page creation
- Content updates
- Knowledge base integration

---

## Sandbox Environment

### Secure Execution
Codegen agents work in **isolated sandbox environments** that provide:

#### Security Features
- **Process Isolation**: Complete separation from host systems
- **Network Restrictions**: Controlled outbound access
- **File System Isolation**: Sandboxed file operations
- **Resource Limits**: CPU and memory constraints
- **No Host Access**: Cannot affect production systems

#### Sandbox Capabilities
- **Code Execution**: Run arbitrary code safely
- **Dependency Installation**: Install packages and libraries
- **Test Execution**: Run comprehensive test suites
- **Build Operations**: Compile and build projects
- **Git Operations**: Clone, commit, push changes
- **Environment Variables**: Secure secret management

#### Configuration Options
- **Custom Docker Images**: Bring your own environment
- **Setup Scripts**: Run initialization commands
- **Pre-installed Tools**: Common dev tools included
- **Persistent Storage**: Optional data persistence
- **Resource Tiers**: Choose CPU/memory levels

### Sandbox Lifecycle
1. **Provisioning**: Create isolated environment
2. **Code Checkout**: Clone repository
3. **Setup**: Run initialization scripts
4. **Execution**: Perform agent tasks
5. **Validation**: Run tests and checks
6. **Cleanup**: Destroy environment

---

## Configuration & Settings

### Model Configuration
**Supported LLM Providers:**
- Claude (Anthropic)
- GPT-4 (OpenAI)
- Custom models via API
- Configurable per organization

**Configuration Options:**
- API key management
- Model selection
- Performance tuning
- Cost optimization
- Rate limit configuration

### Agent Behavior Settings

#### Plan Proposals
- **Automatic Planning**: Generate execution plans before changes
- **Plan Approval**: Require human approval for plans
- **Plan Format**: Structured step-by-step approach
- **Confidence Levels**: Risk assessment per step

#### Interaction Patterns
- **GitHub Mention Requirements**: Control when @mentions are needed
- **Response Timing**: Configure acknowledgment speed
- **Follow-up Handling**: Manage conversation threads
- **Escalation Rules**: When to request human input

### Agent Permissions

#### Repository Access
- **Read Permissions**: Code inspection and analysis
- **Write Permissions**: Code modifications and commits
- **PR Creation**: Control PR generation
- **Branch Management**: Branch creation and deletion
- **Secret Access**: Environment variable permissions

#### Action Controls
- **PR Creation**: Enable/disable PR generation
- **Auto-fix**: Control automatic fix attempts
- **External Integrations**: Manage integration access
- **Resource Limits**: Execution time and resource caps

### Security Settings

#### Signed Commits
- **GPG Signing**: Enforce commit signing
- **Verification**: Validate signed commits
- **Key Management**: Secure key storage
- **Co-author Attribution**: Proper commit attribution

#### TruffleHog Integration
- **Secret Detection**: Pre-commit secret scanning
- **Automatic Blocking**: Prevent secret commits
- **False Positive Management**: Handle detection errors
- **Scan Configuration**: Customize detection rules

### Team & Organization

#### Team Roles
- **Admin**: Full organization control
- **Developer**: Standard development access
- **Read-only**: View-only permissions
- **Custom Roles**: Configurable permission sets

#### Repository Rules
- **Per-repo Settings**: Repository-specific configurations
- **Branch Protection**: Enforce branch rules
- **Review Requirements**: Code review policies
- **CI/CD Requirements**: Required status checks

#### Organization Rules
- **Global Policies**: Organization-wide settings
- **Default Behaviors**: Baseline agent behavior
- **Integration Defaults**: Standard integration configs
- **Compliance Settings**: Security and compliance rules

### On-Premises Deployment
For enterprise customers:
- **Self-hosted Option**: Deploy on your infrastructure
- **Private Cloud**: Dedicated cloud instances
- **Hybrid Deployment**: Mix of cloud and on-prem
- **Custom Security**: Your security controls
- **Data Residency**: Keep data in your region

---

## Analytics & Monitoring

### Performance Metrics
- **Task Completion Rate**: Success vs. failure ratio
- **Average Task Duration**: Time to complete tasks
- **Error Rates**: Frequency of failures
- **Retry Statistics**: Auto-fix success rates
- **Resource Utilization**: Sandbox resource usage

### Usage Analytics
- **Agent Activity**: Task execution frequency
- **User Engagement**: Team member interactions
- **Integration Usage**: Platform-specific metrics
- **Repository Activity**: Per-repo statistics
- **Cost Tracking**: Resource consumption

### Monitoring Features
- **Real-time Dashboards**: Live performance monitoring
- **Historical Trends**: Time-series analysis
- **Alerting**: Notification on anomalies
- **Custom Reports**: Configurable reporting
- **Export Capabilities**: Data export for analysis

### OpenTelemetry Integration
When running Claude Code via CLI:
- **Distributed Tracing**: Full execution traces
- **Log Aggregation**: Centralized logging
- **Metrics Collection**: Performance metrics
- **Custom Instrumentation**: Add your own traces
- **Cloud Surfacing**: View traces in web UI

### Logging Features
- **Structured Logs**: Machine-readable format
- **Log Levels**: Configurable verbosity
- **Context Preservation**: Full execution context
- **Search & Filter**: Query historical logs
- **Real-time Streaming**: Live log viewing

---

## Security & Compliance

### Certifications
- **SOC 2 Type I**: Security controls certification
- **SOC 2 Type II**: Operational effectiveness over time
- **Regular Pen Tests**: Third-party security testing
- **Compliance Monitoring**: Ongoing compliance verification

### Security Features

#### Data Protection
- **Encryption at Rest**: Stored data encryption
- **Encryption in Transit**: TLS/SSL for all communications
- **Key Management**: Secure key storage and rotation
- **Data Isolation**: Tenant data separation
- **Backup & Recovery**: Regular backups with encryption

#### Access Controls
- **Multi-factor Authentication**: Optional MFA
- **Role-based Access**: Granular permissions
- **IP Allowlisting**: Network-level restrictions
- **Audit Logs**: Complete action history
- **Session Management**: Secure session handling

#### Code Security
- **Secret Scanning**: TruffleHog integration
- **Dependency Scanning**: Vulnerability detection
- **Code Isolation**: Sandboxed execution
- **Signed Commits**: GPG commit signing
- **Branch Protection**: Enforce security policies

### Privacy
- **Data Minimization**: Collect only necessary data
- **Data Retention**: Configurable retention policies
- **Right to Delete**: Data deletion requests
- **Privacy Controls**: User privacy settings
- **GDPR Compliance**: European privacy regulations

### Trust & Transparency
- **Trust Center**: Public security documentation
- **Security Portal**: https://codegen.com/security
- **SOC 2 Reports**: Available to customers
- **Pen Test Results**: Shared with enterprise clients
- **Incident Response**: Published response procedures

---

## Additional Features

### API Features
- **RESTful API**: Standard HTTP REST interface
- **Authentication**: Token-based auth
- **Rate Limiting**: Fair usage policies
- **Webhooks**: Event notifications
- **API Versioning**: Stable API versions
- **Comprehensive Docs**: Full API documentation

### GitHub Actions Integration
- **Workflow Automation**: Integrate with CI/CD
- **Custom Actions**: Codegen-specific actions
- **Event Triggers**: React to GitHub events
- **Automated Reviews**: Trigger reviews on PR
- **Status Checks**: Add agent as status check

### Interrupts System
Handle real-time user input during agent execution:
- **Mid-execution Updates**: Receive new instructions
- **Priority Changes**: Adjust task priority
- **Direction Changes**: Modify approach mid-flight
- **Question Answering**: Respond to clarifications
- **Context Updates**: Add new information

### Use Cases
- **Feature Development**: Build new features from specifications
- **Bug Fixes**: Diagnose and repair issues
- **Code Reviews**: Automated PR reviews
- **Test Generation**: Create comprehensive tests
- **Documentation**: Generate and update docs
- **Refactoring**: Improve code quality
- **Migration**: Upgrade dependencies or frameworks
- **Boilerplate Generation**: Create project scaffolding

---

## Getting Started

### Quick Start Steps
1. **Create Account**: Sign up at codegen.com
2. **Install GitHub App**: One-click GitHub installation
3. **Connect Integrations**: Link Slack, Linear, etc.
4. **Configure Settings**: Set up agent behavior
5. **Trigger First Agent**: @mention in Slack or assign issue
6. **Review Results**: Check PR and provide feedback

### Resources
- **Documentation**: https://docs.codegen.com
- **Community Slack**: Join active community
- **GitHub Repository**: Star and contribute
- **API Reference**: Complete API docs
- **Support**: Contact via email or Slack
- **Request Demo**: Enterprise demos available

---

## Summary

Codegen provides a comprehensive platform for autonomous software engineering with:
- **15+ Integrations** across communication, project management, and dev tools
- **Secure Sandboxes** for safe code execution
- **Python SDK & CLI** for programmatic and terminal access
- **Auto-fix System** for CI/CD failures
- **SOC 2 Certified** security and compliance
- **Extensive Configuration** options for customization
- **Real-time Analytics** and monitoring
- **MCP Extensibility** for custom tools
- **Enterprise Features** including on-prem deployment

The platform is designed for scale, security, and seamless integration into existing development workflows.

# Codegen API - Comprehensive Developer Reference

## Table of Contents
1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Base URL & Environment](#base-url--environment)
4. [Rate Limits](#rate-limits)
5. [Error Handling](#error-handling)
6. [Agent Endpoints](#agent-endpoints)
7. [Organization Endpoints](#organization-endpoints)
8. [User Endpoints](#user-endpoints)
9. [Repository Endpoints](#repository-endpoints)
10. [JavaScript/TypeScript Examples](#javascripttypescript-examples)
11. [Complete SDK Examples](#complete-sdk-examples)

---

## API Overview

The Codegen API provides programmatic access to create and manage AI coding agents. The API follows RESTful principles and returns JSON responses.

**Key Capabilities:**
- Create and manage AI agent runs
- Access organization data
- Retrieve detailed agent execution logs
- Manage repositories and integrations
- Control sandbox environments

**API Server:**
- **Production**: `https://api.codegen.com`
- **Modal (Alternative)**: `https://codegen-sh--rest-api.modal.run/`

---

## Authentication

### Overview
All API endpoints require Bearer token authentication. You need both an **API Token** and **Organization ID**.

### Getting Credentials
1. Visit [https://codegen.com/token](https://codegen.com/token)
2. Generate your API token
3. Note your Organization ID

### Authentication Methods

#### 1. Bearer Token (Recommended)
Include your API token in the `Authorization` header:

```http
Authorization: Bearer YOUR_API_TOKEN
```

#### 2. Environment Variable
Set the environment variable for automated access:
```bash
export CODEGEN_API_TOKEN="your_api_token_here"
export CODEGEN_ORG_ID="your_org_id_here"
```

### JavaScript Authentication Examples

```javascript
// Method 1: Using fetch with headers
const API_TOKEN = 'your_api_token';
const ORG_ID = 'your_org_id';

const headers = {
  'Authorization': `Bearer ${API_TOKEN}`,
  'Content-Type': 'application/json'
};

// Method 2: Using axios
const axios = require('axios');

const apiClient = axios.create({
  baseURL: 'https://api.codegen.com',
  headers: {
    'Authorization': `Bearer ${API_TOKEN}`,
    'Content-Type': 'application/json'
  }
});

// Method 3: Using a reusable function
function createAuthenticatedRequest(endpoint, options = {}) {
  return fetch(`https://api.codegen.com${endpoint}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${API_TOKEN}`,
      'Content-Type': 'application/json',
      ...options.headers
    }
  });
}
```

---

## Base URL & Environment

### Production Environment
```
Base URL: https://api.codegen.com
API Version: v1
Full Endpoint Format: https://api.codegen.com/v1/{resource}
```

### Environment Configuration

```javascript
// config.js
const CONFIG = {
  production: {
    baseUrl: 'https://api.codegen.com',
    version: 'v1'
  },
  development: {
    baseUrl: 'https://codegen-sh--rest-api.modal.run',
    version: 'v1'
  }
};

const ENV = process.env.NODE_ENV || 'production';
const API_BASE = CONFIG[ENV].baseUrl;
const API_VERSION = CONFIG[ENV].version;

// Helper function
function buildUrl(path) {
  return `${API_BASE}/${API_VERSION}${path}`;
}

// Usage
const endpoint = buildUrl('/organizations/123/agent/run');
// Returns: https://api.codegen.com/v1/organizations/123/agent/run
```

---

## Rate Limits

The API implements rate limiting to ensure fair usage across all users.

### Rate Limit Tiers

| Endpoint Category | Limit | Window |
|------------------|-------|--------|
| Standard endpoints | 60 requests | 30 seconds |
| Agent creation | 10 requests | 1 minute |
| Setup commands | 5 requests | 1 minute |
| Log analysis | 5 requests | 1 minute |

### Rate Limit Headers

The API returns rate limit information in response headers:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640000000
```

### JavaScript Rate Limit Handling

```javascript
async function makeRequestWithRateLimit(url, options) {
  try {
    const response = await fetch(url, options);
    
    // Check rate limit headers
    const limit = response.headers.get('X-RateLimit-Limit');
    const remaining = response.headers.get('X-RateLimit-Remaining');
    const reset = response.headers.get('X-RateLimit-Reset');
    
    console.log(`Rate Limit: ${remaining}/${limit} remaining`);
    
    if (response.status === 429) {
      // Rate limit exceeded
      const resetTime = new Date(reset * 1000);
      const waitTime = resetTime - new Date();
      
      console.log(`Rate limited. Waiting ${waitTime}ms...`);
      await new Promise(resolve => setTimeout(resolve, waitTime));
      
      // Retry the request
      return makeRequestWithRateLimit(url, options);
    }
    
    return response;
  } catch (error) {
    console.error('Request failed:', error);
    throw error;
  }
}

// Usage
const response = await makeRequestWithRateLimit(
  'https://api.codegen.com/v1/organizations/123/agent/run',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ prompt: 'Fix the bug' })
  }
);
```

### Rate Limit Best Practices

```javascript
class CodegenAPIClient {
  constructor(apiToken, orgId) {
    this.apiToken = apiToken;
    this.orgId = orgId;
    this.requestQueue = [];
    this.processing = false;
  }
  
  async queueRequest(endpoint, options) {
    return new Promise((resolve, reject) => {
      this.requestQueue.push({ endpoint, options, resolve, reject });
      this.processQueue();
    });
  }
  
  async processQueue() {
    if (this.processing || this.requestQueue.length === 0) return;
    
    this.processing = true;
    const { endpoint, options, resolve, reject } = this.requestQueue.shift();
    
    try {
      const response = await fetch(endpoint, {
        ...options,
        headers: {
          'Authorization': `Bearer ${this.apiToken}`,
          'Content-Type': 'application/json',
          ...options.headers
        }
      });
      
      if (response.status === 429) {
        // Re-queue the request
        this.requestQueue.unshift({ endpoint, options, resolve, reject });
        const retryAfter = response.headers.get('Retry-After') || 30;
        await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
      } else {
        resolve(response);
      }
    } catch (error) {
      reject(error);
    } finally {
      this.processing = false;
      // Process next request after a small delay
      setTimeout(() => this.processQueue(), 100);
    }
  }
}
```

---

## Error Handling

### Error Response Format

All error responses follow this structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

### HTTP Status Codes

| Status Code | Meaning | Description |
|-------------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Validation Error | Request validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Common Error Types

#### 1. Authentication Errors (401)
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or missing API token"
  }
}
```

#### 2. Permission Errors (403)
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "User does not have permission to access this resource"
  }
}
```

#### 3. Validation Errors (422)
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "field": "prompt",
      "issue": "Field is required"
    }
  }
}
```

#### 4. Rate Limit Errors (429)
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "details": {
      "retry_after": 30,
      "limit": 60,
      "window": "30 seconds"
    }
  }
}
```

# Codegen REST API - Complete Technical Reference

> **Version:** 1.0.0  
> **Base URL:** `https://api.codegen.com`  
> **Documentation:** https://docs.codegen.com

---

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Authentication & Security](#authentication--security)
4. [Request Format](#request-format)
5. [Response Format](#response-format)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Pagination](#pagination)
9. [Endpoints by Category](#endpoints-by-category)
10. [Complete Endpoint Reference](#complete-endpoint-reference)
11. [Data Models & Schemas](#data-models--schemas)
12. [JavaScript SDK](#javascript-sdk)
13. [Code Examples](#code-examples)
14. [Webhooks](#webhooks)
15. [Best Practices](#best-practices)

---

## Introduction

The Codegen REST API enables programmatic access to AI-powered code generation and management capabilities. Build integrations, automate workflows, and create custom tooling on top of Codegen's agent platform.

### API Characteristics

- **Protocol:** HTTPS/REST
- **Data Format:** JSON
- **Authentication:** Bearer Token
- **Versioning:** URL-based (`/v1/`)
- **Rate Limited:** Yes
- **Idempotent:** Where applicable

### Key Features

✅ **Agent Management** - Create, monitor, and control AI coding agents  
✅ **Organization Access** - Manage users, repos, and integrations  
✅ **Real-time Status** - Poll agent execution status  
✅ **Log Retrieval** - Access detailed execution traces  
✅ **Repository Control** - Configure and manage repositories  
✅ **Pull Request Management** - Edit and manage PRs  
✅ **Sandbox Operations** - Analyze sandbox logs  
✅ **OAuth Integration** - Manage third-party connections

---

## Quick Start

### 1. Get Your Credentials

Visit [https://codegen.com/token](https://codegen.com/token) to obtain:
- **API Token** - Your authentication token
- **Organization ID** - Your org identifier

### 2. Make Your First Request

```bash
curl -X POST "https://api.codegen.com/v1/organizations/YOUR_ORG_ID/agent/run" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Add error handling to the authentication module",
    "repo_id": 123
  }'
```

### 3. Check Agent Status

```bash
curl "https://api.codegen.com/v1/organizations/YOUR_ORG_ID/agent/run/AGENT_RUN_ID" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

---

## Authentication & Security

### Authentication Method

All API requests require Bearer token authentication via the `Authorization` header.

**Header Format:**
```
Authorization: Bearer YOUR_API_TOKEN
```

### Token Management

**Obtaining Tokens:**
1. Log in to [codegen.com](https://codegen.com)
2. Navigate to [codegen.com/token](https://codegen.com/token)
3. Generate new API token
4. Store securely (tokens are shown once)

**Token Security:**
- ⚠️ Never commit tokens to version control
- 🔒 Store in environment variables or secret managers
- 🔄 Rotate tokens periodically
- 🚫 Don't share tokens across applications

### Security Headers

**Recommended Headers:**
```http
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json
User-Agent: YourApp/1.0.0
X-Request-ID: unique-request-id
```

### IP Whitelisting

Enterprise customers can restrict API access to specific IP ranges. Contact support@codegen.com for configuration.

---

## Request Format

### HTTP Methods

| Method | Usage |
|--------|-------|
| GET | Retrieve resources |
| POST | Create resources |
| PATCH | Update resources partially |
| PUT | Update resources completely |
| DELETE | Remove resources |

### Headers

**Required:**
```http
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json
```

**Optional:**
```http
Accept: application/json
User-Agent: YourApp/1.0.0
X-Request-ID: unique-correlation-id
```

### URL Structure

```
https://api.codegen.com/v1/{resource}/{identifier}?param=value
│                        │  │    │         │        │
└─ Base URL              │  │    │         │        └─ Query parameters
                         │  │    │         └─ Resource identifier
                         │  │    └─ Resource type
                         │  └─ API version
                         └─ Path separator
```

### Request Body

**JSON Format (application/json):**
```json
{
  "field_name": "value",
  "nested": {
    "field": "value"
  },
  "array": [1, 2, 3]
}
```

**Field Naming:**
- Use `snake_case` for field names
- Boolean fields: `is_active`, `has_permission`
- Timestamps: ISO 8601 format

---

## Response Format

### Success Response

**Structure:**
```json
{
  "id": 12345,
  "status": "completed",
  "data": { },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.0.0"
  }
}
```

### Response Headers

```http
HTTP/1.1 200 OK
Content-Type: application/json
X-Request-ID: abc-123-def-456
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640000000
```

### Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 202 | Accepted | Request accepted, processing |
| 204 | No Content | Success, no response body |
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Invalid/missing auth |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 502 | Bad Gateway | Upstream error |
| 503 | Service Unavailable | Temporary unavailable |

---

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description",
    "details": {
      "field": "field_name",
      "reason": "Specific validation failure"
    },
    "request_id": "abc-123-def-456",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Error Codes

#### Authentication Errors (401)

**INVALID_TOKEN**
```json
{
  "error": {
    "code": "INVALID_TOKEN",
    "message": "The provided API token is invalid or expired"
  }
}
```

**MISSING_TOKEN**
```json
{
  "error": {
    "code": "MISSING_TOKEN",
    "message": "Authorization header is required"
  }
}
```

#### Permission Errors (403)

**INSUFFICIENT_PERMISSIONS**
```json
{
  "error": {
    "code": "INSUFFICIENT_PERMISSIONS",
    "message": "User does not have permission to perform this action",
    "details": {
      "required_permission": "agent:create",
      "user_role": "viewer"
    }
  }
}
```

**ORGANIZATION_ACCESS_DENIED**
```json
{
  "error": {
    "code": "ORGANIZATION_ACCESS_DENIED",
    "message": "User is not a member of this organization"
  }
}
```

#### Validation Errors (422)

**VALIDATION_ERROR**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "errors": [
        {
          "field": "prompt",
          "message": "Field is required",
          "code": "REQUIRED_FIELD"
        },
        {
          "field": "repo_id",
          "message": "Must be a positive integer",
          "code": "INVALID_TYPE"
        }
      ]
    }
  }
}
```

#### Resource Errors (404)

**RESOURCE_NOT_FOUND**
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested resource was not found",
    "details": {
      "resource_type": "agent_run",
      "resource_id": 12345
    }
  }
}
```

#### Rate Limit Errors (429)

**RATE_LIMIT_EXCEEDED**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded for this endpoint",
    "details": {
      "limit": 10,
      "window": "60 seconds",
      "retry_after": 45
    }
  }
}
```

### Error Handling Best Practices

```javascript
async function makeAPIRequest(endpoint, options) {
  try {
    const response = await fetch(endpoint, options);
    
    // Check if response is ok
    if (!response.ok) {
      const errorData = await response.json();
      
      // Handle specific error codes
      switch (errorData.error.code) {
        case 'RATE_LIMIT_EXCEEDED':
          const retryAfter = errorData.error.details.retry_after;
          console.log(`Rate limited. Retry after ${retryAfter}s`);
          await new Promise(r => setTimeout(r, retryAfter * 1000));
          return makeAPIRequest(endpoint, options); // Retry
          
        case 'INVALID_TOKEN':
          console.error('Token is invalid. Please refresh authentication.');
          throw new Error('Authentication failed');
          
        case 'VALIDATION_ERROR':
          console.error('Validation errors:', errorData.error.details.errors);
          throw new Error('Request validation failed');
          
        default:
          console.error('API Error:', errorData.error);
          throw new Error(errorData.error.message);
      }
    }
    
    return await response.json();
  } catch (error) {
    console.error('Request failed:', error);
    throw error;
  }
}
```

---

## Rate Limiting

### Rate Limit Tiers

| Endpoint Category | Requests | Time Window | Per |
|------------------|----------|-------------|-----|
| Standard GET endpoints | 60 | 30 seconds | Token |
| Agent creation (POST) | 10 | 60 seconds | Token |
| Setup commands | 5 | 60 seconds | Token |
| Log analysis | 5 | 60 seconds | Token |
| Sandbox operations | 5 | 60 seconds | Token |

### Rate Limit Headers

Every API response includes rate limit information:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705318800
X-RateLimit-Window: 30
```

**Header Descriptions:**
- `X-RateLimit-Limit` - Maximum requests allowed in window
- `X-RateLimit-Remaining` - Requests remaining in current window
- `X-RateLimit-Reset` - Unix timestamp when limit resets
- `X-RateLimit-Window` - Window duration in seconds

### Handling Rate Limits

**JavaScript Example:**
```javascript
class RateLimitedAPIClient {
  constructor(apiToken, orgId) {
    this.apiToken = apiToken;
    this.orgId = orgId;
    this.baseUrl = 'https://api.codegen.com/v1';
  }
  
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.apiToken}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    
    // Store rate limit info
    this.rateLimit = {
      limit: parseInt(response.headers.get('X-RateLimit-Limit')),
      remaining: parseInt(response.headers.get('X-RateLimit-Remaining')),
      reset: parseInt(response.headers.get('X-RateLimit-Reset')),
      window: parseInt(response.headers.get('X-RateLimit-Window'))
    };
    
    // Handle rate limit
    if (response.status === 429) {
      const resetTime = this.rateLimit.reset * 1000;
      const waitTime = resetTime - Date.now();
      
      console.log(`Rate limited. Waiting ${waitTime}ms until reset...`);
      await new Promise(resolve => setTimeout(resolve, waitTime));
      
      // Retry the request
      return this.request(endpoint, options);
    }
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return response.json();
  }
  
  getRateLimitStatus() {
    if (!this.rateLimit) return null;
    
    const now = Date.now() / 1000;
    const timeUntilReset = this.rateLimit.reset - now;
    
    return {
      ...this.rateLimit,
      timeUntilReset: Math.max(0, timeUntilReset),
      percentUsed: ((this.rateLimit.limit - this.rateLimit.remaining) / this.rateLimit.limit) * 100
    };
  }
}
```

---

## Pagination

### Pagination Parameters

List endpoints support pagination via query parameters:

**Parameters:**
- `skip` (integer) - Number of items to skip (default: 0, min: 0)
- `limit` (integer) - Number of items to return (default: 100, min: 1, max: 100)

**Example:**
```
GET /v1/organizations/123/agent/runs?skip=20&limit=10
```

### Pagination Response

```json
{
  "items": [
    { "id": 1, "...": "..." },
    { "id": 2, "...": "..." }
  ],
  "total": 150,
  "skip": 20,
  "limit": 10,
  "has_more": true
}
```

### Pagination Helper

```javascript
async function* paginateResults(endpoint, options = {}) {
  let skip = 0;
  const limit = options.limit || 100;
  
  while (true) {
    const url = `${endpoint}?skip=${skip}&limit=${limit}`;
    const response = await makeAPIRequest(url, options);
    
    // Yield current page items
    for (const item of response.items) {
      yield item;
    }
    
    // Check if more pages exist
    if (!response.has_more || response.items.length === 0) {
      break;
    }
    
    skip += limit;
  }
}

// Usage
for await (const agentRun of paginateResults('/v1/organizations/123/agent/runs')) {
  console.log('Agent Run:', agentRun);
}
```

