# Enhanced Codegen-on-OSS System

This is an enhanced version of the codegen-on-oss system with improved database storage, caching, event handling, and API capabilities.

## Architecture Overview

The enhanced system follows a modular, layered architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│ Client Applications                                             │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ API Layer                                                       │
├─────────────────────┬─────────────────────┬─────────────────────┤
│ REST API (FastAPI)  │ GraphQL API         │ WebSocket Server    │
└─────────────────────┴─────────────────────┴─────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ Service Layer                                                   │
├─────────────────────┬─────────────────────┬─────────────────────┤
│ Codebase Service    │ User Preference     │ Webhook Service     │
│                     │ Service             │                     │
└─────────────────────┴─────────────────────┴─────────────────────┘
                                │
                 ┌──────────────┴──────────────┐
                 │                             │
┌────────────────▼─────────────┐  ┌────────────▼─────────────────┐
│ Repository Layer             │  │ Event Bus                    │
├────────────────┬─────────────┤  ├────────────────┬─────────────┤
│ CRUD           │ Query       │  │ Publishers     │ Subscribers │
│ Operations     │ Operations  │  │                │             │
└────────────────┴─────────────┘  └────────────────┴─────────────┘
                 │                             │
                 └──────────────┬──────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ Data Layer                                                      │
├─────────────────────┬─────────────────────┬─────────────────────┤
│ Database            │ Cache               │ File Storage        │
│ (SQLAlchemy)        │ (Memory/Redis/File) │ (S3/Local)          │
└─────────────────────┴─────────────────────┴─────────────────────┘
```

## Key Components

### Database System

The database system provides a comprehensive solution for storing and retrieving analysis data:

- **SQLAlchemy Models**: Well-defined models for repositories, snapshots, files, functions, classes, etc.
- **Repository Pattern**: Clean separation of data access logic
- **Service Layer**: Business logic for managing codebase data
- **Multiple Database Support**: Works with SQLite, PostgreSQL, and other SQLAlchemy-supported databases

[Learn more about the database system](database/README.md)

### Caching System

The caching system improves performance by storing frequently accessed data:

- **Multiple Backends**: Support for in-memory, Redis, and file-based caching
- **TTL Support**: Automatic expiration of cached items
- **Function Decorator**: Easy caching of function results
- **Serialization**: Customizable serialization for different data types

[Learn more about the caching system](cache/README.md)

### Event Bus

The event bus enables loose coupling between components:

- **Publish-Subscribe Pattern**: Components can publish and subscribe to events
- **Asynchronous Processing**: Events are processed asynchronously
- **Event Types**: Well-defined event types for different system events
- **Error Handling**: Robust error handling to prevent cascading failures

[Learn more about the event bus](events/README.md)

### API System

The API system provides multiple interfaces for interacting with the system:

- **REST API**: FastAPI-based REST API for standard operations
- **GraphQL API**: Flexible querying of complex code relationships
- **WebSocket Server**: Real-time updates for analysis progress and results

[Learn more about the API system](api/README.md)

## Getting Started

### Installation

```bash
# Install the package
pip install codegen-on-oss

# Or install from source
git clone https://github.com/codegen-sh/codegen.git
cd codegen/codegen-on-oss
pip install -e .
```

### Running the Application

```bash
# Run with default settings
codegen-on-oss

# Run with custom settings
codegen-on-oss --db-url postgresql://user:password@localhost/codegen --cache-backend redis
```

### Configuration

The application can be configured using environment variables or command-line arguments:

```bash
# Database configuration
export CODEGEN_DB_URL="postgresql://user:password@localhost/codegen"

# Cache configuration
export CODEGEN_CACHE_BACKEND="redis"
export CODEGEN_CACHE_REDIS_HOST="localhost"
export CODEGEN_CACHE_REDIS_PORT="6379"

# API configuration
export CODEGEN_REST_PORT="8000"
export CODEGEN_WEBSOCKET_PORT="8765"
```

## Development

### Setting Up a Development Environment

```bash
# Clone the repository
git clone https://github.com/codegen-sh/codegen.git
cd codegen/codegen-on-oss

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=codegen_on_oss
```

### Code Style

```bash
# Format code
black codegen_on_oss

# Sort imports
isort codegen_on_oss

# Lint code
ruff codegen_on_oss

# Type checking
mypy codegen_on_oss
```

