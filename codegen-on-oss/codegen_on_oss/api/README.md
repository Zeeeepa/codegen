# API System

This module provides a comprehensive API system for the codegen-on-oss project. It includes:

- REST API with FastAPI
- GraphQL API for flexible querying
- WebSocket server for real-time updates

## Architecture

The API system follows a layered architecture:

```
┌─────────────────────────┐
│ Client Applications     │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│ API Layer               │
├─────────────────────────┤
│ - REST API (FastAPI)    │
│ - GraphQL API           │
│ - WebSocket Server      │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│ Service Layer           │
│ (Business Logic)        │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│ Data Access Layer       │
│ (Database & Cache)      │
└─────────────────────────┘
```

## REST API

The REST API provides endpoints for:

- Analyzing repositories and commits
- Creating and retrieving snapshots
- Comparing snapshots
- Managing webhooks
- Setting and retrieving user preferences

### Endpoints

- `GET /`: API information
- `POST /analyze_repo`: Analyze a repository
- `POST /create_snapshot`: Create a snapshot of a repository
- `GET /get_snapshot/{snapshot_id}`: Get a snapshot by ID
- `POST /compare_snapshots`: Compare two snapshots
- `POST /graphql`: Execute a GraphQL query
- `POST /register_webhook`: Register a webhook
- `POST /set_preference`: Set a user preference
- `GET /get_preference/{user_id}/{preference_key}`: Get a user preference

## GraphQL API

The GraphQL API provides a flexible query interface for:

- Repositories
- Snapshots
- Files
- Functions
- Classes
- Imports
- Analysis results
- Issues

### Example Queries

```graphql
# Get a repository with its latest snapshot
query {
  repository(url: "https://github.com/example/repo") {
    id
    name
    url
    latest_snapshot {
      id
      commit_sha
      timestamp
    }
  }
}

# Get a snapshot with its files and functions
query {
  snapshot(id: "abc123") {
    id
    commit_sha
    timestamp
    files {
      id
      filepath
      name
      line_count
    }
    functions {
      id
      name
      qualified_name
      cyclomatic_complexity
    }
  }
}

# Get analysis results for a snapshot
query {
  snapshot(id: "abc123") {
    id
    analysis_results {
      id
      analysis_type
      result
    }
  }
}
```

## WebSocket Server

The WebSocket server provides real-time updates for:

- Analysis progress and completion
- Snapshot creation and updates
- Repository changes
- System events

### Message Types

- `welcome`: Sent when a client connects
- `subscribed`: Sent when a client subscribes to events
- `unsubscribed`: Sent when a client unsubscribes from events
- `ping`/`pong`: Heartbeat messages
- `error`: Error messages
- Event messages: Messages for specific events

### Example Usage

```javascript
// Connect to the WebSocket server
const socket = new WebSocket('ws://localhost:8765');

// Handle messages
socket.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'welcome':
      console.log(`Connected with client ID: ${message.client_id}`);
      
      // Subscribe to events
      socket.send(JSON.stringify({
        type: 'subscribe',
        event_types: ['ANALYSIS_COMPLETED', 'ANALYSIS_FAILED']
      }));
      break;
      
    case 'subscribed':
      console.log(`Subscribed to events: ${message.event_types.join(', ')}`);
      break;
      
    case 'ANALYSIS_COMPLETED':
      console.log(`Analysis completed: ${message.data.repo_url}`);
      break;
      
    case 'ANALYSIS_FAILED':
      console.error(`Analysis failed: ${message.data.error}`);
      break;
      
    case 'error':
      console.error(`Error: ${message.message}`);
      break;
  }
};

// Send a ping message
setInterval(() => {
  socket.send(JSON.stringify({ type: 'ping' }));
}, 30000);
```

## Usage

### Starting the API Servers

```python
from codegen_on_oss.app import CodegenApp

# Create and run the application
app = CodegenApp(
    rest_host='0.0.0.0',
    rest_port=8000,
    websocket_host='0.0.0.0',
    websocket_port=8765
)

# Run the application
import asyncio
asyncio.run(app.run())
```

## Configuration

The API servers can be configured using environment variables:

- `CODEGEN_REST_HOST`: Host for the REST API server (default: '0.0.0.0')
- `CODEGEN_REST_PORT`: Port for the REST API server (default: 8000)
- `CODEGEN_WEBSOCKET_HOST`: Host for the WebSocket server (default: '0.0.0.0')
- `CODEGEN_WEBSOCKET_PORT`: Port for the WebSocket server (default: 8765)

