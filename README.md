# Codegen API Server

A FastAPI server that provides a streaming interface to the Codegen SDK.

## Features

- Run Codegen agents with real-time status updates
- Server-Sent Events (SSE) for live task progress
- Step-by-step progress tracking
- Configurable timeouts (default 30 minutes)
- Heartbeat events to maintain connections

## Installation

```bash
pip install -r requirements.txt
```

## Environment Variables

- `CODEGEN_ORG_ID`: Your Codegen organization ID
- `CODEGEN_TOKEN`: Your Codegen API token
- `SERVER_PORT`: Port to run the server on (default: 8000)

## Usage

Start the server:

```bash
python backend/api.py
```

### API Endpoints

#### Run an Agent

```http
POST /run
Content-Type: application/json

{
    "prompt": "Your prompt here",
    "thread_id": "optional_thread_id"
}
```

Response:
```json
{
    "task_id": "task_123",
    "thread_id": "thread_456"
}
```

#### Get Task Status

```http
GET /status/{task_id}
```

Response:
```json
{
    "status": "in_progress",
    "result": null,
    "error": null
}
```

#### Stream Task Events

```http
GET /events/{task_id}
```

Response (Server-Sent Events):
```
data: {"status": "in_progress", "task_id": "123", "current_step": "Analyzing code", "step_number": 1}

data: {"status": "completed", "task_id": "123", "result": "Success"}

data: [DONE]
```

## Development

Run tests:

```bash
pytest tests/
```

## Event Format

Events are sent in Server-Sent Events (SSE) format with the following structure:

```json
{
    "status": "in_progress",
    "task_id": "123",
    "timestamp": "2025-06-12T14:58:40Z",
    "current_step": "Analyzing repository structure",
    "step_number": 1
}
```

Status values:
- `queued`: Task is queued
- `in_progress`: Task is running
- `completed`: Task completed successfully
- `failed`: Task failed with error
- `error`: Internal server error

## Timeouts and Heartbeats

- Tasks timeout after 30 minutes (configurable via `max_retries`)
- Heartbeat events sent every 5 seconds to keep connections alive
- Failed tasks automatically cleaned up

