# Event Bus System

This module provides an event bus system for the codegen-on-oss project. It includes:

- Event publishing and subscription
- Support for both synchronous and asynchronous event handlers
- Event types for various system events

## Architecture

The event bus system follows a publish-subscribe architecture:

```
┌─────────────────────────┐
│ Event Publisher         │
│ (Components)            │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Event Bus               │
│ (Message Broker)        │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Event Subscribers       │
│ (Event Handlers)        │
└─────────────────────────┘
```

## Event Types

The event bus supports the following event types:

- **Analysis Events**:
  - `ANALYSIS_STARTED`: Analysis has started
  - `ANALYSIS_PROGRESS`: Analysis is in progress
  - `ANALYSIS_COMPLETED`: Analysis has completed
  - `ANALYSIS_FAILED`: Analysis has failed

- **Snapshot Events**:
  - `SNAPSHOT_CREATED`: Snapshot has been created
  - `SNAPSHOT_UPDATED`: Snapshot has been updated
  - `SNAPSHOT_DELETED`: Snapshot has been deleted

- **Repository Events**:
  - `REPOSITORY_ADDED`: Repository has been added
  - `REPOSITORY_UPDATED`: Repository has been updated
  - `REPOSITORY_DELETED`: Repository has been deleted

- **Webhook Events**:
  - `WEBHOOK_TRIGGERED`: Webhook has been triggered

- **System Events**:
  - `SYSTEM_ERROR`: System error has occurred
  - `SYSTEM_WARNING`: System warning has occurred
  - `SYSTEM_INFO`: System information event

## Features

- **Asynchronous Processing**: Events are processed asynchronously in a separate thread
- **Event Queue**: Events are queued for processing to avoid blocking the publisher
- **Synchronous and Asynchronous Handlers**: Support for both synchronous and asynchronous event handlers
- **Error Handling**: Errors in event handlers are caught and logged to prevent cascading failures

## Usage

### Initializing the Event Bus

```python
from codegen_on_oss.events.bus import initialize_event_bus

# Initialize with synchronous event handling (default)
event_bus = initialize_event_bus()

# Initialize with asynchronous event handling
event_bus = initialize_event_bus(async_mode=True)
```

### Publishing Events

```python
from codegen_on_oss.events.bus import get_event_bus, EventType, Event

event_bus = get_event_bus()

# Publish an event using the publish_event method
event_bus.publish_event(
    event_type=EventType.ANALYSIS_COMPLETED,
    data={
        "repo_url": "https://github.com/example/repo",
        "snapshot_id": "abc123",
        "branch": "main",
        "commit_sha": "def456"
    }
)

# Or create and publish an event manually
event = Event(
    type=EventType.ANALYSIS_COMPLETED,
    data={
        "repo_url": "https://github.com/example/repo",
        "snapshot_id": "abc123",
        "branch": "main",
        "commit_sha": "def456"
    }
)
event_bus.publish(event)
```

### Subscribing to Events

```python
from codegen_on_oss.events.bus import get_event_bus, EventType, Event

event_bus = get_event_bus()

# Synchronous event handler
def handle_analysis_completed(event: Event):
    print(f"Analysis completed: {event.data}")

# Subscribe to a specific event type
event_bus.subscribe(EventType.ANALYSIS_COMPLETED, handle_analysis_completed)

# Asynchronous event handler
async def handle_analysis_failed(event: Event):
    print(f"Analysis failed: {event.data}")
    await notify_admin(event.data)

# Subscribe to a specific event type with an async handler
event_bus.subscribe(EventType.ANALYSIS_FAILED, handle_analysis_failed)

# Subscribe to all event types
event_bus.subscribe_to_all(handle_all_events)
```

### Unsubscribing from Events

```python
from codegen_on_oss.events.bus import get_event_bus, EventType

event_bus = get_event_bus()

# Unsubscribe from a specific event type
event_bus.unsubscribe(EventType.ANALYSIS_COMPLETED, handle_analysis_completed)
```

## Configuration

The event bus can be configured using environment variables:

- `CODEGEN_EVENT_BUS_ASYNC_MODE`: Whether to use async mode for event handling (default: False)
- `CODEGEN_EVENT_BUS_QUEUE_SIZE`: Maximum size of the event queue (default: unlimited)

