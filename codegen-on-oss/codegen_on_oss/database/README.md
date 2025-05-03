# Enhanced Database Architecture for Codegen-on-OSS

This directory contains the enhanced database architecture for Codegen-on-OSS, which provides a comprehensive data model for storing and retrieving code analysis data.

## Overview

The enhanced database architecture provides:

1. **Unified Data Model**: A comprehensive data model that connects all aspects of code analysis, including repositories, commits, files, symbols, snapshots, and analysis results.

2. **Efficient Storage**: Properly designed database schema for efficient querying and storage of code analysis data.

3. **Repository Pattern**: A clean repository pattern for database operations, making it easy to interact with the database.

4. **Connection Management**: Efficient connection management with connection pooling and transaction support.

## Components

### Models

The `models.py` file defines the SQLAlchemy ORM models for the unified data model:

- **Repository**: Represents a code repository.
- **Commit**: Represents a specific commit in a repository.
- **File**: Represents a source code file in a commit.
- **Symbol**: Represents a code symbol (function, class, etc.) in a file.
- **Snapshot**: Represents a point-in-time capture of a codebase.
- **AnalysisResult**: Represents the outcome of a code analysis.
- **Metric**: Represents a code quality metric.
- **Issue**: Represents a code quality issue.

### Manager

The `manager.py` file provides a database manager for handling database operations:

- **DatabaseManager**: Manages database connections, sessions, and transactions.
- **DatabaseSettings**: Configuration settings for the database connection.
- **get_db_manager**: Get the singleton instance of DatabaseManager.
- **get_db_session**: Get a database session from the singleton DatabaseManager.

### Repository

The `repository.py` file provides repository classes for database operations:

- **BaseRepository**: Base repository for database operations.
- **RepositoryRepository**: Repository for Repository entities.
- **CommitRepository**: Repository for Commit entities.
- **FileRepository**: Repository for File entities.
- **SymbolRepository**: Repository for Symbol entities.
- **SnapshotRepository**: Repository for Snapshot entities.
- **AnalysisResultRepository**: Repository for AnalysisResult entities.
- **MetricRepository**: Repository for Metric entities.
- **IssueRepository**: Repository for Issue entities.

## Usage

### Initializing the Database

```python
from codegen_on_oss.database import get_db_manager

# Initialize the database
db_manager = get_db_manager()
db_manager.create_tables()
```

### Working with Repositories

```python
from codegen_on_oss.database import get_db_session, RepositoryRepository

# Create a repository
with get_db_session() as session:
    repo_repo = RepositoryRepository()
    repo = repo_repo.create(
        session,
        name="example-repo",
        url="https://github.com/example/example-repo",
        default_branch="main"
    )
    session.commit()

# Get a repository by name
with get_db_session() as session:
    repo_repo = RepositoryRepository()
    repo = repo_repo.get_by_name(session, "example-repo")
```

### Working with Commits

```python
from codegen_on_oss.database import get_db_session, CommitRepository

# Create a commit
with get_db_session() as session:
    commit_repo = CommitRepository()
    commit = commit_repo.create(
        session,
        repository_id=repo.id,
        sha="abc123",
        author="John Doe <john@example.com>",
        message="Initial commit",
        timestamp=datetime.utcnow()
    )
    session.commit()

# Get a commit by SHA
with get_db_session() as session:
    commit_repo = CommitRepository()
    commit = commit_repo.get_by_sha(session, repo.id, "abc123")
```

### Working with Snapshots

```python
from codegen_on_oss.database import get_db_session, SnapshotRepository

# Create a snapshot
with get_db_session() as session:
    snapshot_repo = SnapshotRepository()
    snapshot = snapshot_repo.create(
        session,
        repository_id=repo.id,
        commit_sha="abc123",
        snapshot_hash="def456",
        description="Initial snapshot",
        data={"files": {...}, "symbols": {...}}
    )
    session.commit()

# Get the latest snapshots for a repository
with get_db_session() as session:
    snapshot_repo = SnapshotRepository()
    snapshots = snapshot_repo.get_latest_snapshots(session, repo.id, limit=5)
```

## Database Schema

The database schema is defined using SQLAlchemy ORM models. The schema includes:

- Tables for repositories, commits, files, symbols, snapshots, analysis results, metrics, and issues.
- Foreign key relationships between tables.
- Indexes for efficient querying.
- Unique constraints to prevent duplicate data.

## Differential Snapshots

The enhanced architecture supports differential snapshots to reduce storage requirements. When creating a snapshot, the system checks if a file has changed since the previous snapshot. If not, the file is referenced from the previous snapshot instead of being stored again.

## Metrics and Issues

The architecture provides comprehensive support for storing and retrieving code quality metrics and issues. Metrics and issues can be associated with repositories, files, and symbols, allowing for detailed analysis of code quality.

## API Integration

The database architecture is integrated with the API server, providing endpoints for:

- Analyzing repositories and commits.
- Creating and comparing snapshots.
- Retrieving metrics and issues.
- Searching for symbols and files.

## Future Enhancements

Future enhancements to the database architecture may include:

- Support for more database backends (e.g., MySQL, SQLite).
- Improved caching for frequently accessed data.
- Support for distributed databases for large-scale deployments.
- Integration with more code analysis tools and metrics.

