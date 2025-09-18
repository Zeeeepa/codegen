"""
Event-Driven Architecture Core
=============================

Core event system for the Codegen Visual Flow interface, providing real-time
communication and coordination between all system components.

Features:
- Event publishing and subscription with type safety
- Real-time event streaming via WebSocket
- Event persistence and replay capabilities
- Distributed event coordination across services
- Integration with existing Codegen telemetry system
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Union
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as redis
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Event types for the visual flow system."""
    
    # Workflow events
    WORKFLOW_CREATED = "workflow.created"
    WORKFLOW_UPDATED = "workflow.updated"
    WORKFLOW_DELETED = "workflow.deleted"
    WORKFLOW_EXECUTED = "workflow.executed"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    
    # Agent events
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    AGENT_TRACE_UPDATED = "agent.trace_updated"
    
    # System events
    SYSTEM_HEALTH_CHECK = "system.health_check"
    SYSTEM_PERFORMANCE_UPDATE = "system.performance_update"
    
    # User events
    USER_CONNECTED = "user.connected"
    USER_DISCONNECTED = "user.disconnected"
    USER_ACTION = "user.action"
    
    # Integration events
    INTEGRATION_CONNECTED = "integration.connected"
    INTEGRATION_DISCONNECTED = "integration.disconnected"
    INTEGRATION_ERROR = "integration.error"


@dataclass
class Event:
    """Base event class for all system events."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType
    source: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "correlation_id": self.correlation_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        return cls(
            id=data["id"],
            type=EventType(data["type"]),
            source=data["source"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            data=data.get("data", {}),
            user_id=data.get("user_id"),
            organization_id=data.get("organization_id"),
            correlation_id=data.get("correlation_id"),
        )


class EventHandler:
    """Base class for event handlers."""
    
    def __init__(self, event_types: List[EventType]):
        self.event_types = event_types
    
    async def handle(self, event: Event) -> None:
        """Handle an event. Override in subclasses."""
        raise NotImplementedError


class EventSystem:
    """
    Core event system for real-time communication and coordination.
    
    Provides:
    - Event publishing and subscription
    - Real-time event streaming
    - Event persistence and replay
    - Distributed coordination
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.subscribers: Dict[EventType, Set[EventHandler]] = {}
        self.running = False
        self.tasks: List[asyncio.Task] = []
        
    async def initialize(self) -> None:
        """Initialize the event system."""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Event system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize event system: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the event system."""
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Event system shutdown complete")
    
    def subscribe(self, handler: EventHandler) -> None:
        """Subscribe an event handler to specific event types."""
        for event_type in handler.event_types:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = set()
            self.subscribers[event_type].add(handler)
        
        logger.info(f"Subscribed handler to events: {handler.event_types}")
    
    def unsubscribe(self, handler: EventHandler) -> None:
        """Unsubscribe an event handler."""
        for event_type in handler.event_types:
            if event_type in self.subscribers:
                self.subscribers[event_type].discard(handler)
        
        logger.info(f"Unsubscribed handler from events: {handler.event_types}")
    
    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        try:
            # Store event in Redis for persistence
            if self.redis_client:
                await self.redis_client.lpush(
                    f"events:{event.type.value}",
                    json.dumps(event.to_dict())
                )
                
                # Publish to Redis pub/sub for real-time distribution
                await self.redis_client.publish(
                    f"events:{event.type.value}",
                    json.dumps(event.to_dict())
                )
            
            # Handle locally subscribed handlers
            if event.type in self.subscribers:
                handlers = list(self.subscribers[event.type])
                await asyncio.gather(
                    *[handler.handle(event) for handler in handlers],
                    return_exceptions=True
                )
            
            logger.debug(f"Published event: {event.type.value} from {event.source}")
            
        except Exception as e:
            logger.error(f"Failed to publish event {event.type.value}: {e}")
            raise
    
    async def get_events(
        self,
        event_type: EventType,
        limit: int = 100,
        offset: int = 0
    ) -> List[Event]:
        """Get historical events of a specific type."""
        if not self.redis_client:
            return []
        
        try:
            event_data = await self.redis_client.lrange(
                f"events:{event_type.value}",
                offset,
                offset + limit - 1
            )
            
            events = []
            for data in event_data:
                try:
                    event_dict = json.loads(data)
                    events.append(Event.from_dict(event_dict))
                except Exception as e:
                    logger.warning(f"Failed to parse event data: {e}")
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get events for {event_type.value}: {e}")
            return []
    
    async def start_listening(self) -> None:
        """Start listening for Redis pub/sub events."""
        if not self.redis_client:
            logger.error("Redis client not initialized")
            return
        
        self.running = True
        
        # Create pub/sub listener task
        task = asyncio.create_task(self._redis_listener())
        self.tasks.append(task)
        
        logger.info("Started event system listener")
    
    async def _redis_listener(self) -> None:
        """Listen for Redis pub/sub events."""
        try:
            pubsub = self.redis_client.pubsub()
            
            # Subscribe to all event channels
            for event_type in EventType:
                await pubsub.subscribe(f"events:{event_type.value}")
            
            while self.running:
                try:
                    message = await pubsub.get_message(timeout=1.0)
                    if message and message["type"] == "message":
                        await self._handle_redis_message(message)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Error processing Redis message: {e}")
            
            await pubsub.unsubscribe()
            await pubsub.close()
            
        except Exception as e:
            logger.error(f"Redis listener error: {e}")
    
    async def _handle_redis_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming Redis pub/sub message."""
        try:
            event_data = json.loads(message["data"])
            event = Event.from_dict(event_data)
            
            # Handle locally subscribed handlers
            if event.type in self.subscribers:
                handlers = list(self.subscribers[event.type])
                await asyncio.gather(
                    *[handler.handle(event) for handler in handlers],
                    return_exceptions=True
                )
            
        except Exception as e:
            logger.error(f"Failed to handle Redis message: {e}")


# Specialized event handlers for common use cases

class WorkflowEventHandler(EventHandler):
    """Handler for workflow-related events."""
    
    def __init__(self):
        super().__init__([
            EventType.WORKFLOW_CREATED,
            EventType.WORKFLOW_UPDATED,
            EventType.WORKFLOW_DELETED,
            EventType.WORKFLOW_EXECUTED,
            EventType.WORKFLOW_COMPLETED,
            EventType.WORKFLOW_FAILED,
        ])
    
    async def handle(self, event: Event) -> None:
        """Handle workflow events."""
        logger.info(f"Handling workflow event: {event.type.value}")
        
        # Implement workflow-specific logic here
        if event.type == EventType.WORKFLOW_EXECUTED:
            await self._handle_workflow_execution(event)
        elif event.type == EventType.WORKFLOW_FAILED:
            await self._handle_workflow_failure(event)
    
    async def _handle_workflow_execution(self, event: Event) -> None:
        """Handle workflow execution event."""
        workflow_id = event.data.get("workflow_id")
        logger.info(f"Workflow {workflow_id} started execution")
    
    async def _handle_workflow_failure(self, event: Event) -> None:
        """Handle workflow failure event."""
        workflow_id = event.data.get("workflow_id")
        error = event.data.get("error")
        logger.error(f"Workflow {workflow_id} failed: {error}")


class AgentEventHandler(EventHandler):
    """Handler for agent-related events."""
    
    def __init__(self):
        super().__init__([
            EventType.AGENT_STARTED,
            EventType.AGENT_COMPLETED,
            EventType.AGENT_FAILED,
            EventType.AGENT_TRACE_UPDATED,
        ])
    
    async def handle(self, event: Event) -> None:
        """Handle agent events."""
        logger.info(f"Handling agent event: {event.type.value}")
        
        # Implement agent-specific logic here
        if event.type == EventType.AGENT_TRACE_UPDATED:
            await self._handle_trace_update(event)
    
    async def _handle_trace_update(self, event: Event) -> None:
        """Handle agent trace update."""
        agent_run_id = event.data.get("agent_run_id")
        trace_data = event.data.get("trace_data")
        logger.info(f"Agent {agent_run_id} trace updated with {len(trace_data)} entries")


# Global event system instance
event_system = EventSystem()
