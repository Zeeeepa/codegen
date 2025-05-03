# Enhanced Database and Storage System

This module provides a comprehensive database and storage system for the codegen-on-oss project. It includes:

- SQLAlchemy models for storing analysis results, snapshots, and other data
- Repository pattern implementation for database operations
- Service layer for business logic
- Connection management utilities

## Architecture

The database system follows a layered architecture:

```
┌─────────────────────────┐
│ Service Layer           │
│ (Business Logic)        │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│ Repository Layer        │
│ (CRUD Operations)       │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│ Model Layer             │
│ (SQLAlchemy Models)     │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│ Database Connection     │
│ (Connection Management) │
└─────────────────────────┘
```

## Models

The database schema includes the following models:

- `Repository`: Information about code repositories
- `Snapshot`: Snapshots of codebases at specific points in time
- `File`: Source code files
- `Function`: Functions and methods
- `Class`: Classes and interfaces
- `Import`: Import statements
- `AnalysisResult`: Results of code analysis
- `Issue`: Code issues found during analysis
- `UserPreference`: User preferences
- `WebhookConfig`: Webhook configurations

## Repositories

The repository layer provides CRUD operations for each model:

- `BaseRepository`: Generic repository with common operations
- `RepositoryRepository`: Operations for `Repository` model
- `SnapshotRepository`: Operations for `Snapshot` model
- `FileRepository`: Operations for `File` model
- `FunctionRepository`: Operations for `Function` model
- `ClassRepository`: Operations for `Class` model
- `ImportRepository`: Operations for `Import` model
- `AnalysisResultRepository`: Operations for `AnalysisResult` model
- `IssueRepository`: Operations for `Issue` model
- `UserPreferenceRepository`: Operations for `UserPreference` model
- `WebhookConfigRepository`: Operations for `WebhookConfig` model

## Services

The service layer provides business logic for the application:

- `CodebaseService`: Managing codebase data
- `UserPreferenceService`: Managing user preferences
- `WebhookService`: Managing webhooks

## Usage

### Initializing the Database

```python
from codegen_on_oss.database.connection import initialize_db

# Initialize with default SQLite database
db_manager = initialize_db()

# Initialize with PostgreSQL
db_manager = initialize_db("postgresql://user:password@localhost/codegen")
```

### Using the Service Layer

```python
from codegen import Codebase
from codegen_on_oss.database.service import CodebaseService

# Create a service instance
codebase_service = CodebaseService()

# Create a repository
repository = codebase_service.create_repository(
    url="https://github.com/example/repo",
    name="example-repo",
    description="Example repository",
    default_branch="main"
)

# Create a codebase
codebase = Codebase.from_repo("https://github.com/example/repo")

# Create a snapshot
snapshot = codebase_service.create_snapshot(
    codebase=codebase,
    repository_id=repository.id,
    commit_sha="abc123",
    branch="main"
)

# Store analysis results
codebase_service.store_analysis_result(
    snapshot_id=snapshot.id,
    analysis_type="complexity",
    result={"complexity": 42}
)

# Compare snapshots
differences = codebase_service.compare_snapshots(
    base_snapshot_id="snapshot1",
    compare_snapshot_id="snapshot2"
)
```

## Configuration

The database connection can be configured using environment variables:

- `CODEGEN_DB_URL`: Database connection URL (default: SQLite)
- `CODEGEN_DB_POOL_SIZE`: Connection pool size (default: 5)
- `CODEGEN_DB_MAX_OVERFLOW`: Maximum number of connections to create beyond pool_size (default: 10)
- `CODEGEN_DB_POOL_TIMEOUT`: Seconds to wait before giving up on getting a connection (default: 30)
- `CODEGEN_DB_POOL_RECYCLE`: Seconds after which a connection is automatically recycled (default: 3600)
- `CODEGEN_DB_ECHO`: Whether to log all SQL statements (default: False)

