# Codegen API Endpoints Mapping & Rate Limits

## Overview
This document provides a comprehensive mapping of all Codegen API endpoints, their rate limits, and corresponding CLI commands.

**Base URL**: `https://{MODAL_PREFIX}--rest-api.modal.run/`
- Configurable via `CODEGEN_API_BASE_URL` environment variable
- Modal prefix determined by environment (production/staging/development)

## Rate Limits Summary

| Category | Rate Limit | Description |
|----------|------------|-------------|
| Standard Endpoints | 60 requests/30 seconds | Most read operations |
| Agent Creation | 10 requests/minute | Agent run creation |
| Setup Commands | 5 requests/minute | Initial setup operations |
| Log Analysis | 5 requests/minute | Log processing operations |

## Core API Endpoints

### 1. Agent Management Endpoints

#### Create Agent Run
- **Endpoint**: `POST /v1/organizations/{org_id}/agent/run`
- **Rate Limit**: 10 requests/minute
- **CLI Command**: `codegen agent create --prompt "..."`
- **Description**: Creates a new agent run with specified prompt
- **Headers**: `Authorization: Bearer {token}`, `x-codegen-client: codegen__claude_code`

#### Get Agent Run Details
- **Endpoint**: `GET /v1/organizations/{org_id}/agent/run/{agent_run_id}`
- **Rate Limit**: 60 requests/30 seconds
- **CLI Command**: `codegen agent get --id {agent_run_id}`
- **Description**: Retrieves detailed information about a specific agent run

#### List Agent Runs
- **Endpoint**: `GET /v1/organizations/{org_id}/agent/runs`
- **Rate Limit**: 60 requests/30 seconds
- **CLI Command**: `codegen agents list`
- **Description**: Lists agent runs with pagination and filtering
- **Query Parameters**: 
  - `source_type`: Filter by source (e.g., "API")
  - `user_id`: Filter by user ID
  - `page`: Page number
  - `page_size`: Items per page

#### Resume Agent Run
- **Endpoint**: `POST /v1/organizations/{org_id}/agent/run/resume`
- **Rate Limit**: 10 requests/minute
- **CLI Command**: Not directly exposed in CLI
- **Description**: Resumes an agent run with follow-up queries

### 2. Claude Code Integration Endpoints

#### Create Claude Session
- **Endpoint**: `POST /v1/organizations/{org_id}/claude_code/session`
- **Rate Limit**: 60 requests/30 seconds
- **CLI Command**: `codegen claude`
- **Description**: Creates a new Claude Code session for tracking

#### Get Session Status
- **Endpoint**: `GET /v1/organizations/{org_id}/claude_code/session/{session_id}/status`
- **Rate Limit**: 60 requests/30 seconds
- **CLI Command**: Internal session tracking
- **Description**: Retrieves current status of a Claude session

#### Get Session Logs
- **Endpoint**: `GET /v1/organizations/{org_id}/claude_code/session/{session_id}/log`
- **Rate Limit**: 5 requests/minute (log analysis)
- **CLI Command**: Internal log watching
- **Description**: Retrieves logs from a Claude session

### 3. User & Organization Management

#### Get Current User
- **Endpoint**: `GET /v1/users/me`
- **Rate Limit**: 60 requests/30 seconds
- **CLI Command**: `codegen profile`
- **Description**: Retrieves current user information

#### List Organizations
- **Endpoint**: `GET /v1/organizations`
- **Rate Limit**: 60 requests/30 seconds
- **CLI Command**: `codegen org list`
- **Description**: Lists organizations accessible to the user

#### List Organization Integrations
- **Endpoint**: `GET /v1/organizations/{org_id}/integrations`
- **Rate Limit**: 60 requests/30 seconds
- **CLI Command**: `codegen integrations list`
- **Description**: Lists available integrations for an organization

#### List Organization Tools
- **Endpoint**: `GET /v1/organizations/{org_id}/tools`
- **Rate Limit**: 60 requests/30 seconds
- **CLI Command**: `codegen tools list`
- **Description**: Lists available tools for an organization

#### Execute Tool
- **Endpoint**: `POST /v1/organizations/{org_id}/tools/execute`
- **Rate Limit**: 60 requests/30 seconds
- **CLI Command**: MCP tool execution
- **Description**: Executes a tool via the API

### 4. Repository Management

#### List Repositories
- **Endpoint**: `GET /v1/organizations/{org_id}/repositories`
- **Rate Limit**: 60 requests/30 seconds
- **CLI Command**: Internal repository resolution
- **Description**: Lists repositories accessible to the organization

## Legacy Modal Endpoints

### Specialized Service Endpoints
These endpoints use the Modal service architecture with different prefixes:

1. **RUN_ENDPOINT**: `https://{MODAL_PREFIX}--cli-run.modal.run`
2. **DOCS_ENDPOINT**: `https://{MODAL_PREFIX}--cli-docs.modal.run`
3. **EXPERT_ENDPOINT**: `https://{MODAL_PREFIX}--cli-ask-expert.modal.run`
4. **IDENTIFY_ENDPOINT**: `https://{MODAL_PREFIX}--cli-identify.modal.run`
5. **CREATE_ENDPOINT**: `https://{MODAL_PREFIX}--cli-create.modal.run`
6. **DEPLOY_ENDPOINT**: `https://{MODAL_PREFIX}--cli-deploy.modal.run`
7. **LOOKUP_ENDPOINT**: `https://{MODAL_PREFIX}--cli-lookup.modal.run`
8. **RUN_ON_PR_ENDPOINT**: `https://{MODAL_PREFIX}--cli-run-on-pull-request.modal.run`
9. **PR_LOOKUP_ENDPOINT**: `https://{MODAL_PREFIX}--cli-pr-lookup.modal.run`
10. **IMPROVE_ENDPOINT**: `https://{MODAL_PREFIX}--cli-improve.modal.run`
11. **MCP_SERVER_ENDPOINT**: `https://{MODAL_PREFIX}--codegen-mcp-server.modal.run/mcp`

## CLI Command to API Endpoint Mapping

| CLI Command | API Endpoint | Rate Limit | Description |
|-------------|--------------|------------|-------------|
| `codegen agent create` | `POST /v1/organizations/{org_id}/agent/run` | 10 req/min | Create agent run |
| `codegen agent get` | `GET /v1/organizations/{org_id}/agent/run/{id}` | 60 req/30s | Get agent details |
| `codegen agents list` | `GET /v1/organizations/{org_id}/agent/runs` | 60 req/30s | List agent runs |
| `codegen claude` | `POST /v1/organizations/{org_id}/claude_code/session` | 60 req/30s | Start Claude session |
| `codegen org list` | `GET /v1/organizations` | 60 req/30s | List organizations |
| `codegen profile` | `GET /v1/users/me` + `GET /v1/organizations` | 60 req/30s | User profile |
| `codegen tools list` | `GET /v1/organizations/{org_id}/tools` | 60 req/30s | List tools |
| `codegen integrations list` | `GET /v1/organizations/{org_id}/integrations` | 60 req/30s | List integrations |

## Authentication

All API endpoints require Bearer token authentication:
```
Authorization: Bearer {token}
```

Tokens are managed by the `TokenManager` class in `src/codegen/cli/auth/token_manager.py`.

## Organization Resolution

Organization ID resolution follows this precedence:
1. Explicit `org_id` parameter
2. `CODEGEN_ORG_ID` environment variable
3. `REPOSITORY_ORG_ID` environment variable
4. Stored org ID from auth data
5. API auto-detection (first organization)

## Error Handling

Standard HTTP status codes:
- `200`: Success
- `401`: Invalid or expired token
- `403`: Access denied
- `404`: Resource not found
- `429`: Rate limit exceeded
- `500`: Server error

## Dashboard Implementation Notes

### WebSocket Requirements
For real-time dashboard updates, consider implementing WebSocket connections for:
- Agent run status changes
- Notification delivery
- Live statistics updates

### Caching Strategy
Implement intelligent caching for:
- Organization lists (cache for 5 minutes)
- User information (cache for 10 minutes)
- Tool lists (cache for 15 minutes)
- Agent run lists (cache for 30 seconds)

### Rate Limit Management
- Implement request queuing for agent creation (10 req/min limit)
- Use exponential backoff for rate limit errors
- Cache frequently accessed data to reduce API calls
- Batch requests where possible

## Next Steps for Dashboard Implementation

1. **Enhanced API Client**: Extend `src/codegen/cli/api/client.py` with caching and rate limiting
2. **WebSocket Layer**: Implement real-time updates on top of polling infrastructure
3. **Database Integration**: Add Supabase for dashboard-specific data persistence
4. **Authentication Adapter**: Create web authentication flow using existing token management
