# Codegen-on-OSS Enhanced Architecture

This directory contains the enhanced architecture for the Codegen-on-OSS system, providing a more interconnected analysis, database storage, snapshotting, and frontend data delivery system.

## Architecture Overview

The enhanced architecture is built around several key components:

1. **Unified Data Model**: A comprehensive relational database schema for storing all analysis artifacts with proper ORM models and relationships.

2. **Event-Driven Architecture**: An event bus system that decouples components and allows them to communicate through events.

3. **Enhanced Snapshot System**: An improved snapshot system that integrates with the database and S3 storage for efficient snapshot creation and retrieval.

4. **Real-time Frontend Data Service**: WebSocket support for real-time updates to the frontend with dedicated API endpoints.

5. **Analysis Pipeline Orchestration**: A pipeline orchestrator that manages the analysis workflow, handles task queuing, and provides error handling.

## Directory Structure

- `database/`: Contains the database models, connection management, and repository pattern implementations.
- `events/`: Contains the event bus system and event handlers.
- `snapshot/`: Contains the enhanced snapshot manager.
- `api/`: Contains the API routes, schemas, and WebSocket manager.
- `pipeline/`: Contains the analysis pipeline orchestrator.
- `app.py`: The main FastAPI application that integrates all components.

## Key Components

### Database Models

The database models define the schema for storing analysis artifacts, including repositories, snapshots, analysis results, files, functions, classes, and metrics.

### Event Bus

The event bus provides a publish-subscribe mechanism for components to communicate with each other. Events include analysis completion, snapshot creation, and job status updates.

### Enhanced Snapshot Manager

The enhanced snapshot manager integrates with the database and S3 storage to create, store, and retrieve snapshots of codebases.

### WebSocket Manager

The WebSocket manager provides real-time updates to the frontend, allowing clients to subscribe to topics and receive updates when events occur.

### Analysis Pipeline

The analysis pipeline orchestrates the analysis workflow, managing task queuing, worker threads, and error handling.

## Usage

### Starting the Application

```python
from codegen_on_oss import app, pipeline

# Start the analysis pipeline
pipeline.start()

# Run the FastAPI application
app.run_app(host="0.0.0.0", port=8000)
```

### Creating a Snapshot

```python
from codegen_on_oss import EnhancedSnapshotManager
from codegen_on_oss.database.connection import db_manager

# Create a database session
with db_manager.session_scope() as session:
    # Create a snapshot manager
    snapshot_manager = EnhancedSnapshotManager(session)
    
    # Create a snapshot from a repository
    snapshot = snapshot_manager.snapshot_repo(
        repo_url="https://github.com/example/repo",
        commit_sha="abc123",
        branch="main"
    )
    
    print(f"Created snapshot: {snapshot.snapshot_id}")
```

### Analyzing a Snapshot

```python
from codegen_on_oss import CodeAnalyzer
from codegen_on_oss.database.connection import db_manager
from codegen_on_oss.snapshot.enhanced_snapshot_manager import EnhancedSnapshotManager

# Create a database session
with db_manager.session_scope() as session:
    # Create a snapshot manager
    snapshot_manager = EnhancedSnapshotManager(session)
    
    # Get a snapshot
    snapshot = snapshot_manager.get_snapshot("snapshot_id")
    
    # Load the codebase from the snapshot
    codebase = snapshot_manager.load_codebase_from_snapshot(snapshot)
    
    # Create a code analyzer
    analyzer = CodeAnalyzer(codebase)
    
    # Analyze the codebase
    analysis_result = analyzer.analyze()
    
    print(f"Analysis result: {analysis_result}")
```

## API Endpoints

The API provides endpoints for repository management, snapshot creation, analysis, and real-time updates:

- `/api/repositories`: CRUD operations for repositories
- `/api/snapshots`: CRUD operations for snapshots
- `/api/analysis`: Analysis operations
- `/ws/{client_id}`: WebSocket endpoint for real-time updates

## Event Types

The system defines various event types for communication between components:

- Analysis events: `ANALYSIS_STARTED`, `ANALYSIS_COMPLETED`, `ANALYSIS_FAILED`
- Snapshot events: `SNAPSHOT_CREATED`, `SNAPSHOT_UPDATED`, `SNAPSHOT_DELETED`
- Repository events: `REPOSITORY_ADDED`, `REPOSITORY_UPDATED`, `REPOSITORY_DELETED`
- Job events: `JOB_CREATED`, `JOB_STARTED`, `JOB_COMPLETED`, `JOB_FAILED`
- PR events: `PR_CREATED`, `PR_UPDATED`, `PR_MERGED`, `PR_CLOSED`, `PR_ANALYZED`
- Commit events: `COMMIT_CREATED`, `COMMIT_ANALYZED`
- Webhook events: `WEBHOOK_TRIGGERED`, `WEBHOOK_FAILED`

## Dependencies

- `codegen`: The Codegen SDK for code analysis
- `fastapi`: Web framework for building APIs
- `sqlalchemy`: ORM for database operations
- `pydantic`: Data validation and settings management
- `boto3`: AWS SDK for S3 storage
- `aiohttp`: Asynchronous HTTP client/server
- `websockets`: WebSocket implementation

