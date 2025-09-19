"""
Real-time Dashboard and WebSocket Integration

This module provides real-time updates for pipeline execution status,
WebSocket connections for live monitoring, and event streaming capabilities.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum

from .schemas import PipelineExecution, TaskExecution, ExecutionStatus


logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types of real-time events."""
    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_FAILED = "pipeline_failed"
    PIPELINE_CANCELLED = "pipeline_cancelled"
    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    STAGE_FAILED = "stage_failed"
    AGENT_TASK_UPDATE = "agent_task_update"
    RESOURCE_UPDATE = "resource_update"
    LOG_MESSAGE = "log_message"
    HEARTBEAT = "heartbeat"


@dataclass
class RealtimeEvent:
    """Real-time event data structure."""
    event_type: EventType
    timestamp: datetime
    pipeline_id: Optional[str] = None
    execution_id: Optional[str] = None
    stage_id: Optional[str] = None
    task_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "pipeline_id": self.pipeline_id,
            "execution_id": self.execution_id,
            "stage_id": self.stage_id,
            "task_id": self.task_id,
            "data": self.data
        }


@dataclass
class WebSocketConnection:
    """Represents a WebSocket connection."""
    connection_id: str
    websocket: Any  # WebSocket connection object
    connected_at: datetime
    last_heartbeat: datetime
    subscribed_pipelines: Set[str] = field(default_factory=set)
    subscribed_events: Set[EventType] = field(default_factory=lambda: set(EventType))
    metadata: Dict[str, Any] = field(default_factory=dict)


class RealtimeEventBroadcaster:
    """
    Manages real-time event broadcasting to WebSocket connections
    with filtering and subscription management.
    """
    
    def __init__(self, heartbeat_interval: int = 30):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.event_history: List[RealtimeEvent] = []
        self.max_history_size: int = 1000
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_task: Optional[asyncio.Task] = None
        self._shutdown = False
        
    async def start(self):
        """Start the event broadcaster."""
        self.heartbeat_task = asyncio.create_task(self._heartbeat_worker())
        logger.info("Real-time event broadcaster started")
        
    async def stop(self):
        """Stop the event broadcaster."""
        self._shutdown = True
        
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
                
        # Close all connections
        for connection in list(self.connections.values()):
            await self.disconnect_client(connection.connection_id)
            
        logger.info("Real-time event broadcaster stopped")
        
    async def connect_client(
        self, 
        websocket: Any, 
        connection_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection object
            connection_id: Optional custom connection ID
            metadata: Optional connection metadata
            
        Returns:
            Connection ID
        """
        connection_id = connection_id or str(uuid.uuid4())
        metadata = metadata or {}
        
        connection = WebSocketConnection(
            connection_id=connection_id,
            websocket=websocket,
            connected_at=datetime.now(),
            last_heartbeat=datetime.now(),
            metadata=metadata
        )
        
        self.connections[connection_id] = connection
        
        logger.info(f"WebSocket client connected: {connection_id}")
        
        # Send connection acknowledgment
        await self._send_to_connection(connection, RealtimeEvent(
            event_type=EventType.HEARTBEAT,
            timestamp=datetime.now(),
            data={
                "type": "connection_ack",
                "connection_id": connection_id,
                "server_time": datetime.now().isoformat()
            }
        ))
        
        return connection_id
        
    async def disconnect_client(self, connection_id: str):
        """Disconnect a WebSocket client."""
        connection = self.connections.pop(connection_id, None)
        if connection:
            try:
                await connection.websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket {connection_id}: {e}")
                
            logger.info(f"WebSocket client disconnected: {connection_id}")
            
    async def subscribe_to_pipeline(self, connection_id: str, pipeline_id: str):
        """Subscribe a connection to pipeline events."""
        connection = self.connections.get(connection_id)
        if connection:
            connection.subscribed_pipelines.add(pipeline_id)
            logger.info(f"Connection {connection_id} subscribed to pipeline {pipeline_id}")
            
    async def unsubscribe_from_pipeline(self, connection_id: str, pipeline_id: str):
        """Unsubscribe a connection from pipeline events."""
        connection = self.connections.get(connection_id)
        if connection:
            connection.subscribed_pipelines.discard(pipeline_id)
            logger.info(f"Connection {connection_id} unsubscribed from pipeline {pipeline_id}")
            
    async def subscribe_to_events(self, connection_id: str, event_types: List[EventType]):
        """Subscribe a connection to specific event types."""
        connection = self.connections.get(connection_id)
        if connection:
            connection.subscribed_events.update(event_types)
            logger.info(f"Connection {connection_id} subscribed to events: {event_types}")
            
    async def broadcast_event(self, event: RealtimeEvent):
        """Broadcast an event to all subscribed connections."""
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history_size:
            self.event_history.pop(0)
            
        # Send to matching connections
        for connection in list(self.connections.values()):
            if self._should_send_event(connection, event):
                await self._send_to_connection(connection, event)
                
    def _should_send_event(self, connection: WebSocketConnection, event: RealtimeEvent) -> bool:
        """Check if an event should be sent to a connection."""
        # Check event type subscription
        if event.event_type not in connection.subscribed_events:
            return False
            
        # Check pipeline subscription (if event has pipeline_id)
        if event.pipeline_id:
            if (
                connection.subscribed_pipelines and 
                event.pipeline_id not in connection.subscribed_pipelines
            ):
                return False
                
        return True
        
    async def _send_to_connection(self, connection: WebSocketConnection, event: RealtimeEvent):
        """Send an event to a specific connection."""
        try:
            message = json.dumps(event.to_dict())
            await connection.websocket.send(message)
            connection.last_heartbeat = datetime.now()
            
        except Exception as e:
            logger.warning(f"Failed to send event to {connection.connection_id}: {e}")
            # Disconnect on send failure
            await self.disconnect_client(connection.connection_id)
            
    async def _heartbeat_worker(self):
        """Background task to send heartbeats and clean up stale connections."""
        while not self._shutdown:
            try:
                current_time = datetime.now()
                stale_connections = []
                
                # Check for stale connections and send heartbeats
                for connection in list(self.connections.values()):
                    time_since_heartbeat = (current_time - connection.last_heartbeat).total_seconds()
                    
                    if time_since_heartbeat > self.heartbeat_interval * 3:
                        # Connection is stale
                        stale_connections.append(connection.connection_id)
                    elif time_since_heartbeat > self.heartbeat_interval:
                        # Send heartbeat
                        heartbeat_event = RealtimeEvent(
                            event_type=EventType.HEARTBEAT,
                            timestamp=current_time,
                            data={"server_time": current_time.isoformat()}
                        )
                        await self._send_to_connection(connection, heartbeat_event)
                        
                # Clean up stale connections
                for connection_id in stale_connections:
                    logger.warning(f"Disconnecting stale connection: {connection_id}")
                    await self.disconnect_client(connection_id)
                    
                await asyncio.sleep(self.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat worker error: {e}")
                await asyncio.sleep(self.heartbeat_interval)
                
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        current_time = datetime.now()
        
        connection_stats = []
        for connection in self.connections.values():
            connection_stats.append({
                "connection_id": connection.connection_id,
                "connected_at": connection.connected_at.isoformat(),
                "duration_seconds": (current_time - connection.connected_at).total_seconds(),
                "last_heartbeat": connection.last_heartbeat.isoformat(),
                "subscribed_pipelines": list(connection.subscribed_pipelines),
                "subscribed_events": [e.value for e in connection.subscribed_events],
                "metadata": connection.metadata
            })
            
        return {
            "total_connections": len(self.connections),
            "connections": connection_stats,
            "event_history_size": len(self.event_history)
        }
        
    def get_recent_events(
        self, 
        limit: int = 100,
        pipeline_id: Optional[str] = None,
        event_types: Optional[List[EventType]] = None
    ) -> List[Dict[str, Any]]:
        """Get recent events with optional filtering."""
        filtered_events = []
        
        for event in reversed(self.event_history[-limit:]):
            # Filter by pipeline_id if specified
            if pipeline_id and event.pipeline_id != pipeline_id:
                continue
                
            # Filter by event types if specified
            if event_types and event.event_type not in event_types:
                continue
                
            filtered_events.append(event.to_dict())
            
        return filtered_events


class RealtimeIntegration:
    """
    Integration layer that connects the orchestration engine with real-time updates.
    """
    
    def __init__(self, broadcaster: RealtimeEventBroadcaster):
        self.broadcaster = broadcaster
        
    async def on_pipeline_started(self, execution: PipelineExecution):
        """Handle pipeline start event."""
        event = RealtimeEvent(
            event_type=EventType.PIPELINE_STARTED,
            timestamp=datetime.now(),
            pipeline_id=execution.pipeline_id,
            execution_id=execution.id,
            data={
                "pipeline_name": execution.pipeline_definition.name,
                "total_stages": execution.total_stages,
                "triggered_by": execution.triggered_by
            }
        )
        await self.broadcaster.broadcast_event(event)
        
    async def on_pipeline_completed(self, execution: PipelineExecution):
        """Handle pipeline completion event."""
        event_type = EventType.PIPELINE_COMPLETED
        if execution.status == ExecutionStatus.FAILED:
            event_type = EventType.PIPELINE_FAILED
        elif execution.status == ExecutionStatus.CANCELLED:
            event_type = EventType.PIPELINE_CANCELLED
            
        event = RealtimeEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            pipeline_id=execution.pipeline_id,
            execution_id=execution.id,
            data={
                "pipeline_name": execution.pipeline_definition.name,
                "status": execution.status,
                "duration_seconds": execution.duration_seconds,
                "completed_stages": execution.completed_stages,
                "failed_stages": execution.failed_stages,
                "skipped_stages": execution.skipped_stages
            }
        )
        await self.broadcaster.broadcast_event(event)
        
    async def on_stage_started(self, task_execution: TaskExecution):
        """Handle stage start event."""
        event = RealtimeEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime.now(),
            pipeline_id=task_execution.pipeline_id,
            stage_id=task_execution.stage_id,
            task_id=task_execution.id,
            data={
                "status": task_execution.status,
                "agent_run_id": task_execution.agent_run_id
            }
        )
        await self.broadcaster.broadcast_event(event)
        
    async def on_stage_completed(self, task_execution: TaskExecution):
        """Handle stage completion event."""
        event_type = EventType.STAGE_COMPLETED
        if task_execution.status == ExecutionStatus.FAILED:
            event_type = EventType.STAGE_FAILED
            
        event = RealtimeEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            pipeline_id=task_execution.pipeline_id,
            stage_id=task_execution.stage_id,
            task_id=task_execution.id,
            data={
                "status": task_execution.status,
                "duration_seconds": task_execution.duration_seconds,
                "agent_run_id": task_execution.agent_run_id,
                "agent_web_url": task_execution.agent_web_url,
                "error_message": task_execution.error_message
            }
        )
        await self.broadcaster.broadcast_event(event)
        
    async def on_agent_task_update(
        self, 
        task_execution: TaskExecution, 
        update_data: Dict[str, Any]
    ):
        """Handle agent task progress update."""
        event = RealtimeEvent(
            event_type=EventType.AGENT_TASK_UPDATE,
            timestamp=datetime.now(),
            pipeline_id=task_execution.pipeline_id,
            stage_id=task_execution.stage_id,
            task_id=task_execution.id,
            data={
                "status": task_execution.status,
                "agent_run_id": task_execution.agent_run_id,
                "update": update_data
            }
        )
        await self.broadcaster.broadcast_event(event)
        
    async def on_resource_update(self, resource_data: Dict[str, Any]):
        """Handle resource usage update."""
        event = RealtimeEvent(
            event_type=EventType.RESOURCE_UPDATE,
            timestamp=datetime.now(),
            data=resource_data
        )
        await self.broadcaster.broadcast_event(event)
        
    async def on_log_message(
        self,
        level: str,
        message: str,
        pipeline_id: Optional[str] = None,
        stage_id: Optional[str] = None,
        task_id: Optional[str] = None
    ):
        """Handle log message event."""
        event = RealtimeEvent(
            event_type=EventType.LOG_MESSAGE,
            timestamp=datetime.now(),
            pipeline_id=pipeline_id,
            stage_id=stage_id,
            task_id=task_id,
            data={
                "level": level,
                "message": message
            }
        )
        await self.broadcaster.broadcast_event(event)


# Example WebSocket handler for frameworks like FastAPI or aiohttp
class WebSocketHandler:
    """
    Example WebSocket handler implementation.
    This would be adapted for specific web frameworks.
    """
    
    def __init__(self, broadcaster: RealtimeEventBroadcaster):
        self.broadcaster = broadcaster
        
    async def handle_websocket(self, websocket):
        """Handle WebSocket connection."""
        connection_id = None
        
        try:
            # Accept connection
            await websocket.accept()
            
            # Register connection
            connection_id = await self.broadcaster.connect_client(websocket)
            
            # Handle messages
            while True:
                try:
                    message = await websocket.receive_text()
                    await self.handle_message(connection_id, json.loads(message))
                except Exception as e:
                    logger.error(f"WebSocket message handling error: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
        finally:
            if connection_id:
                await self.broadcaster.disconnect_client(connection_id)
                
    async def handle_message(self, connection_id: str, message: Dict[str, Any]):
        """Handle incoming WebSocket message."""
        message_type = message.get("type")
        
        if message_type == "subscribe_pipeline":
            pipeline_id = message.get("pipeline_id")
            if pipeline_id:
                await self.broadcaster.subscribe_to_pipeline(connection_id, pipeline_id)
                
        elif message_type == "unsubscribe_pipeline":
            pipeline_id = message.get("pipeline_id")
            if pipeline_id:
                await self.broadcaster.unsubscribe_from_pipeline(connection_id, pipeline_id)
                
        elif message_type == "subscribe_events":
            event_types = message.get("event_types", [])
            if event_types:
                event_enum_types = [EventType(et) for et in event_types if et in EventType.__members__.values()]
                await self.broadcaster.subscribe_to_events(connection_id, event_enum_types)
                
        elif message_type == "get_recent_events":
            limit = message.get("limit", 100)
            pipeline_id = message.get("pipeline_id")
            event_types_str = message.get("event_types", [])
            event_types = [EventType(et) for et in event_types_str if et in EventType.__members__.values()] if event_types_str else None
            
            recent_events = self.broadcaster.get_recent_events(
                limit=limit,
                pipeline_id=pipeline_id,
                event_types=event_types
            )
            
            # Send response
            connection = self.broadcaster.connections.get(connection_id)
            if connection:
                response_event = RealtimeEvent(
                    event_type=EventType.HEARTBEAT,
                    timestamp=datetime.now(),
                    data={
                        "type": "recent_events_response",
                        "events": recent_events
                    }
                )
                await self.broadcaster._send_to_connection(connection, response_event)