# Codegen Utilities

This directory contains utility modules for the Codegen application.

## Overview

The utilities are organized into the following modules:

- **Logger**: Standardized logging functionality
- **Tracer**: Tracing and performance monitoring
- **Database**: SQLite database operations

## Logger

The logger module provides a standardized way to log messages in the Codegen application.

```python
from codegen.utils import setup_logger, get_logger

# Set up a logger with custom configuration
logger = setup_logger(
    name="my_module",
    level=logging.DEBUG,
    log_file="/path/to/log/file.log"
)

# Or get an existing logger
logger = get_logger("my_module")

# Use the logger
logger.info("This is an info message")
logger.error("This is an error message")
```

## Tracer

The tracer module provides functionality to trace function calls and measure performance.

```python
from codegen.utils import trace, CodegenTracer

# Use the trace decorator to trace function calls
@trace
def my_function(arg1, arg2):
    # Function implementation
    return result

# Or with additional metadata
@trace(operation="data_processing", component="parser")
def process_data(data):
    # Function implementation
    return processed_data

# Get the global tracer instance
from codegen.utils.tracer import get_tracer
tracer = get_tracer()

# Export trace events
events_json = tracer.export_events(format_type="json")
```

## Database

The database module provides a simple interface for SQLite database operations.

```python
from codegen.utils import Database, DatabaseManager

# Get the global database manager
from codegen.utils.database import get_database_manager
db_manager = get_database_manager()

# Get a database instance
db = db_manager.get_database("my_database")

# Create a table
db.create_table(
    "users",
    {
        "id": "INTEGER PRIMARY KEY",
        "name": "TEXT NOT NULL",
        "email": "TEXT UNIQUE",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }
)

# Insert data
db.insert(
    "users",
    {
        "name": "John Doe",
        "email": "john@example.com"
    }
)

# Query data
users = db.select(
    "users",
    columns=["id", "name", "email"],
    condition="name LIKE ?",
    params=("%John%",)
)

# Update data
db.update(
    "users",
    {"name": "Jane Doe"},
    condition="id = ?",
    params=(1,)
)

# Delete data
db.delete(
    "users",
    condition="id = ?",
    params=(1,)
)
```
