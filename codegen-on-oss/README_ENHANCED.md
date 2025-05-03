# Enhanced Codegen-on-OSS Architecture

This document describes the enhanced architecture for the Codegen-on-OSS system, which improves interconnected analysis, database storage, snapshotting, and frontend data transmission.

## Architecture Overview

The enhanced architecture is built around the following key components:

1. **Event-Driven Architecture**: A central event bus connects all components, allowing for decoupled communication and real-time updates.
2. **Comprehensive Database Schema**: An expanded database schema stores all analysis artifacts, including codebases, snapshots, analysis results, symbols, metrics, issues, and relationships.
3. **Enhanced Snapshotting System**: Differential snapshots reduce storage requirements, and improved comparison capabilities make it easier to track code evolution.
4. **Standardized Frontend Data Transmission**: GraphQL and WebSocket support provide flexible and efficient data retrieval for frontend applications.

## Key Components

### Event System

The event system provides a central event bus for communication between components. Events are published by components and consumed by subscribers, allowing for decoupled communication and real-time updates.

Key files:
- `events/event_bus.py`: Implements the event bus and event types
- `events/handlers.py`: Provides base classes for event handlers

### Database Schema

The database schema stores all analysis artifacts, including codebases, snapshots, analysis results, symbols, metrics, issues, and relationships.

```
┌─────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│ CodebaseSnapshot        │      │ AnalysisResult          │      │ CodeMetrics             │
├─────────────────────────┤      ├─────────────────────────┤      ├─────────────────────────┤
│ id                      │      │ id                      │      │ id                      │
│ snapshot_id             │◄─────┤ snapshot_id             │      │ analysis_id             │◄─┐
│ commit_sha              │      │ analyzer_type           │      │ complexity              │  │
│ timestamp               │      │ status                  │      │ maintainability         │  │
│ metadata                │      │ created_at              │      │ halstead_metrics        │  │
│ storage_path            │      │ completed_at            │      │ doi_metrics             │  │
└─────────────────────────┘      │ result_data             │      │ lines_of_code           │  │
                                 └─────────────────────────┘      └─────────────────────────┘  │
                                   ▲                                                           │
                                   │                                                           │
                                   │                                                           │
┌─────────────────────────┐      ┌┴───────────────────────┐                                  │
│ SymbolAnalysis          │      │ DependencyGraph         │                                  │
├─────────────────────────┤      ├─────────────────────────┤                                  │
│ id                      │      │ id                      │                                  │
│ analysis_id             │◄─┐   │ analysis_id             │◄─────────────────────────────────┘
│ symbol_type             │  │   │ graph_data              │
│ symbol_name             │  │   │ node_count              │
│ file_path               │  │   │ edge_count              │
│ line_number             │  │   │ clusters                │
│ complexity              │  │   │ central_nodes           │
│ dependencies            │  │   └─────────────────────────┘
└─────────────────────────┘  │
                             │
                             └───────────────────────────────────────────────────────────────┘
```

Key files:
- `database/models.py`: Defines the database models
- `database/session.py`: Provides utilities for creating and managing database sessions

### Snapshotting System

The enhanced snapshotting system supports differential snapshots, which store only changes between versions to reduce storage requirements. It also provides improved comparison capabilities for tracking code evolution.

Key files:
- `snapshot/enhanced_snapshot_manager.py`: Implements the enhanced snapshot manager

### API Layer

The API layer provides standardized interfaces for frontend applications to access analysis data. It includes a REST API, a GraphQL API, and WebSocket support for real-time updates.

Key files:
- `api/rest.py`: Implements the REST API
- `api/graphql.py`: Implements the GraphQL API
- `api/websocket.py`: Implements WebSocket support

## Event Flow

The event-driven architecture enables a clear flow of data through the system:

1. A user initiates a code analysis through the API
2. The API publishes an `ANALYSIS_STARTED` event
3. The analysis component subscribes to this event and begins analysis
4. As analysis progresses, it publishes events like `ISSUE_DETECTED`
5. When analysis completes, it publishes an `ANALYSIS_COMPLETED` event
6. The snapshot manager subscribes to this event and creates a snapshot
7. The snapshot manager publishes a `SNAPSHOT_CREATED` event
8. The frontend receives these events via WebSocket and updates in real-time

## Getting Started

To run the enhanced Codegen-on-OSS system:

1. Install dependencies:
   ```
   pip install -e ".[dev]"
   ```

2. Initialize the database:
   ```
   python -c "from codegen_on_oss.database import init_db; init_db()"
   ```

3. Run the application:
   ```
   python -m codegen_on_oss.app
   ```

4. Access the API at `http://localhost:8000` and the GraphQL playground at `http://localhost:8000/graphql`

## API Documentation

### REST API

The REST API provides endpoints for accessing analysis results, snapshots, and other data. Key endpoints include:

- `/codebases`: CRUD operations for codebases
- `/snapshots`: CRUD operations for snapshots
- `/analysis-results`: CRUD operations for analysis results
- `/issues`: CRUD operations for issues

### GraphQL API

The GraphQL API provides a flexible way to query analysis data. Example queries:

```graphql
# Get a codebase with its snapshots and analysis results
query {
  codebase(id: 1) {
    id
    name
    repository_url
    snapshots {
      id
      commit_hash
      created_at
    }
    analysis_results {
      id
      analysis_type
      summary
    }
  }
}
```

### WebSocket API

The WebSocket API provides real-time updates for analysis progress and results. Connect to `/ws/{client_id}` and subscribe to events:

```json
{
  "type": "subscribe",
  "event_types": ["ANALYSIS_STARTED", "ANALYSIS_COMPLETED", "ISSUE_DETECTED"]
}
```

## Future Enhancements

Potential future enhancements include:

1. **Distributed Analysis**: Support for distributed analysis across multiple workers
2. **Advanced Visualization**: Enhanced visualization capabilities for analysis results
3. **Machine Learning Integration**: Integration with machine learning models for code quality prediction
4. **Plugin System**: Support for custom analysis plugins

