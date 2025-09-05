"""
WebSocket Service for real-time updates during PRD implementation
"""

import json
import asyncio
from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class WebSocketMessage:
    event_type: str
    payload: Dict[str, Any]
    timestamp: str
    id: str


class WebSocketService:
    """
    Service for managing real-time WebSocket communications
    """
    
    def __init__(self):
        self.connections: Dict[str, Any] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.message_history: List[WebSocketMessage] = []
        self.max_history_size = 1000
    
    def send(self, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Send a message to all connected clients
        
        Args:
            event_type: Type of event (e.g., 'prd_generated', 'task_completed')
            payload: Event data
        """
        
        message = WebSocketMessage(
            event_type=event_type,
            payload=payload,
            timestamp=datetime.now().isoformat(),
            id=f"{event_type}-{int(datetime.now().timestamp() * 1000)}"
        )
        
        # Store in history
        self._add_to_history(message)
        
        # Send to all connections
        self._broadcast_message(message)
        
        # Trigger event handlers
        self._trigger_event_handlers(event_type, payload)
    
    def on(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register an event handler
        
        Args:
            event_type: Type of event to listen for
            handler: Function to call when event occurs
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
    
    def off(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        Unregister an event handler
        
        Args:
            event_type: Type of event
            handler: Handler function to remove
        """
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    def add_connection(self, connection_id: str, connection: Any) -> None:
        """
        Add a WebSocket connection
        
        Args:
            connection_id: Unique identifier for the connection
            connection: WebSocket connection object
        """
        self.connections[connection_id] = connection
        
        # Send recent history to new connection
        self._send_history_to_connection(connection_id)
    
    def remove_connection(self, connection_id: str) -> None:
        """
        Remove a WebSocket connection
        
        Args:
            connection_id: Connection identifier to remove
        """
        if connection_id in self.connections:
            del self.connections[connection_id]
    
    def get_message_history(self, limit: int = 100) -> List[WebSocketMessage]:
        """
        Get recent message history
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of recent messages
        """
        return self.message_history[-limit:]
    
    def _add_to_history(self, message: WebSocketMessage) -> None:
        """Add message to history with size limit"""
        self.message_history.append(message)
        
        # Trim history if too large
        if len(self.message_history) > self.max_history_size:
            self.message_history = self.message_history[-self.max_history_size:]
    
    def _broadcast_message(self, message: WebSocketMessage) -> None:
        """Broadcast message to all connections"""
        message_json = json.dumps({
            'event_type': message.event_type,
            'payload': message.payload,
            'timestamp': message.timestamp,
            'id': message.id
        })
        
        # Remove dead connections
        dead_connections = []
        
        for connection_id, connection in self.connections.items():
            try:
                # In a real implementation, this would send via WebSocket
                # For now, we'll just print for debugging
                print(f"WebSocket [{connection_id}]: {message_json}")
                
                # Simulate sending to connection
                # connection.send(message_json)
                
            except Exception as e:
                print(f"Failed to send to connection {connection_id}: {e}")
                dead_connections.append(connection_id)
        
        # Clean up dead connections
        for connection_id in dead_connections:
            self.remove_connection(connection_id)
    
    def _trigger_event_handlers(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Trigger registered event handlers"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(payload)
                except Exception as e:
                    print(f"Error in event handler for {event_type}: {e}")
    
    def _send_history_to_connection(self, connection_id: str) -> None:
        """Send recent message history to a specific connection"""
        if connection_id not in self.connections:
            return
        
        # Send last 10 messages to new connection
        recent_messages = self.get_message_history(10)
        
        for message in recent_messages:
            try:
                message_json = json.dumps({
                    'event_type': message.event_type,
                    'payload': message.payload,
                    'timestamp': message.timestamp,
                    'id': message.id
                })
                
                # In a real implementation, this would send via WebSocket
                print(f"WebSocket History [{connection_id}]: {message_json}")
                
            except Exception as e:
                print(f"Failed to send history to connection {connection_id}: {e}")
    
    # Convenience methods for common events
    def send_prd_generation_started(self, prd_id: str, config: Dict[str, Any]) -> None:
        """Send PRD generation started event"""
        self.send('prd_generation_started', {
            'prd_id': prd_id,
            'config': config
        })
    
    def send_prd_generation_progress(self, prd_id: str, progress: Dict[str, Any]) -> None:
        """Send PRD generation progress event"""
        self.send('prd_generation_progress', {
            'prd_id': prd_id,
            'progress': progress
        })
    
    def send_prd_generated(self, prd_id: str, prd_data: Dict[str, Any]) -> None:
        """Send PRD generated event"""
        self.send('prd_generated', {
            'prd_id': prd_id,
            'prd': prd_data
        })
    
    def send_implementation_started(self, prd_id: str, task_count: int) -> None:
        """Send implementation started event"""
        self.send('implementation_started', {
            'prd_id': prd_id,
            'total_tasks': task_count
        })
    
    def send_task_progress(self, prd_id: str, task_id: str, status: str, progress: float) -> None:
        """Send task progress event"""
        self.send('task_progress', {
            'prd_id': prd_id,
            'task_id': task_id,
            'status': status,
            'progress': progress
        })
    
    def send_implementation_completed(self, prd_id: str, results: Dict[str, Any]) -> None:
        """Send implementation completed event"""
        self.send('implementation_completed', {
            'prd_id': prd_id,
            'results': results
        })
    
    def send_validation_started(self, prd_id: str, validation_types: List[str]) -> None:
        """Send validation started event"""
        self.send('validation_started', {
            'prd_id': prd_id,
            'validation_types': validation_types
        })
    
    def send_validation_progress(self, prd_id: str, validation_type: str, progress: Dict[str, Any]) -> None:
        """Send validation progress event"""
        self.send('validation_progress', {
            'prd_id': prd_id,
            'validation_type': validation_type,
            'progress': progress
        })
    
    def send_validation_completed(self, prd_id: str, results: Dict[str, Any]) -> None:
        """Send validation completed event"""
        self.send('validation_completed', {
            'prd_id': prd_id,
            'results': results
        })
    
    def send_deployment_started(self, prd_id: str, config: Dict[str, Any]) -> None:
        """Send deployment started event"""
        self.send('deployment_started', {
            'prd_id': prd_id,
            'config': config
        })
    
    def send_deployment_progress(self, prd_id: str, stage: str, progress: Dict[str, Any]) -> None:
        """Send deployment progress event"""
        self.send('deployment_progress', {
            'prd_id': prd_id,
            'stage': stage,
            'progress': progress
        })
    
    def send_deployment_completed(self, prd_id: str, results: Dict[str, Any]) -> None:
        """Send deployment completed event"""
        self.send('deployment_completed', {
            'prd_id': prd_id,
            'results': results
        })
    
    def send_error(self, error_type: str, error_data: Dict[str, Any]) -> None:
        """Send error event"""
        self.send('error', {
            'error_type': error_type,
            'error_data': error_data
        })
    
    def send_system_status(self, status: Dict[str, Any]) -> None:
        """Send system status event"""
        self.send('system_status', status)
    
    # Statistics and monitoring
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.connections)
    
    def get_event_stats(self) -> Dict[str, Any]:
        """Get event statistics"""
        event_counts = {}
        for message in self.message_history:
            event_type = message.event_type
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            'total_messages': len(self.message_history),
            'active_connections': self.get_connection_count(),
            'event_counts': event_counts,
            'registered_handlers': {
                event_type: len(handlers) 
                for event_type, handlers in self.event_handlers.items()
            }
        }

