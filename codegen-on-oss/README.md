# Codegen OSS - Enhanced Architecture

This repository contains an enhanced version of the Codegen OSS system with improved interconnected analysis, database storage, snapshotting, and frontend data integration.

## Architecture Overview

The enhanced Codegen OSS system is built around the following key components:

1. **Unified Database Schema**
   - Relational database connecting repositories, snapshots, analyses, and code entities
   - Support for tracking relationships between code elements
   - Temporal tracking of changes across snapshots

2. **Event-Driven Analysis Pipeline**
   - Event bus for publishing and subscribing to system events
   - Decoupled services communicating through events
   - Automatic triggering of analysis on code changes

3. **Enhanced Snapshot System**
   - Incremental snapshots to save storage space
   - Rich comparison tools for analyzing differences between snapshots
   - Enhanced metadata capture for better analysis
   - Visualization export for frontend integration

4. **Frontend Data Integration**
   - GraphQL API for flexible data querying
   - WebSocket support for real-time updates
   - REST API endpoints for basic operations
   - Comprehensive data models for frontend visualization

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL database
- Git

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/Zeeeepa/codegen.git
   cd codegen/codegen-on-oss
   ```

2. Install dependencies:
   ```
   pip install -e .
   ```

3. Initialize the database:
   ```
   python -m codegen_on_oss.cli init-db --db-name codegen_oss
   ```

### Usage

#### Creating a Snapshot

```
python -m codegen_on_oss.cli snapshot https://github.com/username/repo --enhanced
```

#### Analyzing a Repository

```
python -m codegen_on_oss.cli analyze https://github.com/username/repo --analysis-type all
```

#### Comparing Snapshots

```
python -m codegen_on_oss.cli compare snapshot1.json snapshot2.json --detail-level detailed
```

#### Running the API Server

```
python -m codegen_on_oss.cli serve --port 8000
```

## API Documentation

### GraphQL API

The GraphQL API is available at `/graphql` and provides access to all system data with flexible querying capabilities.

Example query:
```graphql
query {
  repositories {
    id
    name
    url
    snapshots {
      id
      commitSha
      timestamp
    }
  }
}
```

### WebSocket API

The WebSocket API is available at `/ws` and provides real-time updates for system events.

To subscribe to events:
```json
{
  "action": "subscribe",
  "event_type": "SNAPSHOT_CREATED"
}
```

### REST API

Basic REST API endpoints are available for common operations:

- `GET /api/repositories` - Get all repositories
- `GET /api/repositories/{id}` - Get a repository by ID
- `GET /api/snapshots` - Get all snapshots
- `GET /api/snapshots/{id}` - Get a snapshot by ID
- `GET /api/analyses` - Get all analyses
- `GET /api/analyses/{id}` - Get an analysis by ID
- `GET /api/compare?snapshot_id_1={id1}&snapshot_id_2={id2}` - Compare two snapshots
- `GET /api/visualization?snapshot_id={id}&format=json` - Get visualization data for a snapshot

## Architecture Details

### Database Schema

The database schema includes the following main entities:

- **Repository**: Represents a code repository
- **Snapshot**: Represents a point-in-time capture of a codebase
- **CodeEntity**: Base class for code entities (files, functions, classes)
- **Analysis**: Represents an analysis of a snapshot
- **EventLog**: Records system events

### Event System

The event system uses an event bus to publish and subscribe to events. Key event types include:

- Repository events (added, updated, removed)
- Snapshot events (created, updated, deleted)
- Analysis events (requested, started, completed, failed)
- Code entity events (created, updated, deleted)
- System events (error, warning, info)

### Enhanced Snapshot System

The enhanced snapshot system extends the basic snapshot functionality with:

- Incremental snapshots that only store changes
- Enhanced metadata capture (security metrics, test coverage, etc.)
- Comprehensive comparison capabilities
- Visualization export for frontend integration

### Frontend Integration

The frontend integration layer provides:

- GraphQL API for flexible data querying
- WebSocket support for real-time updates
- REST API endpoints for basic operations
- Data models optimized for visualization

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

