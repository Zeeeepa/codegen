"""
Event emission and webhook system for Codegen.

Provides real-time event emission, webhook delivery, and state synchronization.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from uuid import uuid4
import hashlib
import hmac

import httpx
from sqlalchemy.orm import Session

from .connection import db_session_scope

logger = logging.getLogger(__name__)


class Event:
    """Represents a system event."""
    
    def __init__(
        self,
        event_type: str,
        data: Dict[str, Any],
        event_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        source: Optional[str] = None,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None
    ):
        self.event_id = event_id or str(uuid4())
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp or datetime.utcnow()
        self.source = source or 'codegen-system'
        self.user_id = user_id
        self.organization_id = organization_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'data': self.data,
            'timestamp': self.timestamp.isoformat() + 'Z',
            'source': self.source,
            'user_id': self.user_id,
            'organization_id': self.organization_id,
        }
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class EventEmitter:
    """
    Event emitter for system-wide events.
    
    Provides:
    - Event emission and handling
    - Webhook delivery
    - Real-time notifications
    - Event persistence
    """
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._webhook_manager: Optional[WebhookManager] = None
        self._websocket_manager: Optional[WebSocketManager] = None
    
    def set_webhook_manager(self, webhook_manager: "WebhookManager") -> None:
        """Set the webhook manager."""
        self._webhook_manager = webhook_manager
    
    def set_websocket_manager(self, websocket_manager: "WebSocketManager") -> None:
        """Set the WebSocket manager."""
        self._websocket_manager = websocket_manager
    
    def on(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Register an event handler."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def off(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Unregister an event handler."""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    def emit(
        self,
        event_type: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        source: Optional[str] = None
    ) -> Event:
        """Emit an event."""
        event = Event(
            event_type=event_type,
            data=data,
            user_id=user_id,
            organization_id=organization_id,
            source=source
        )
        
        # Store event in database
        self._persist_event(event)
        
        # Call registered handlers
        self._call_handlers(event)
        
        # Send webhooks
        if self._webhook_manager:
            asyncio.create_task(self._webhook_manager.deliver_event(event))
        
        # Send WebSocket notifications
        if self._websocket_manager:
            asyncio.create_task(self._websocket_manager.broadcast_event(event))
        
        logger.debug(f"Emitted event: {event_type} with ID: {event.event_id}")
        return event
    
    def _call_handlers(self, event: Event) -> None:
        """Call all registered handlers for an event."""
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event.event_type}: {e}")
    
    def _persist_event(self, event: Event) -> None:
        """Persist event to database."""
        try:
            with db_session_scope() as session:
                from .models.events import SystemEvent
                
                system_event = SystemEvent(
                    event_id=event.event_id,
                    event_type=event.event_type,
                    event_data=event.data,
                    timestamp=event.timestamp.isoformat() + 'Z',
                    source=event.source,
                    user_id=event.user_id,
                    organization_id=event.organization_id
                )
                session.add(system_event)
                
        except Exception as e:
            logger.error(f"Failed to persist event {event.event_id}: {e}")


class WebhookManager:
    """
    Webhook delivery manager.
    
    Provides:
    - Webhook endpoint management
    - Event delivery with retries
    - Signature verification
    - Delivery tracking
    """
    
    def __init__(self, max_retries: int = 3, timeout: int = 30):
        self.max_retries = max_retries
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
    
    async def deliver_event(self, event: Event) -> None:
        """Deliver event to all registered webhooks."""
        try:
            with db_session_scope() as session:
                from .models.webhooks import WebhookEndpoint
                
                # Get active webhook endpoints
                endpoints = session.query(WebhookEndpoint).filter(
                    WebhookEndpoint.is_active == True
                ).all()
                
                # Filter endpoints by organization if applicable
                if event.organization_id:
                    endpoints = [
                        ep for ep in endpoints 
                        if ep.organization_id == event.organization_id
                    ]
                
                # Deliver to each endpoint
                for endpoint in endpoints:
                    if self._should_deliver_event(endpoint, event):
                        await self._deliver_to_endpoint(endpoint, event)
                        
        except Exception as e:
            logger.error(f"Failed to deliver event {event.event_id}: {e}")
    
    def _should_deliver_event(self, endpoint, event: Event) -> bool:
        """Check if event should be delivered to endpoint."""
        # Check event type filters
        if endpoint.event_types and event.event_type not in endpoint.event_types:
            return False
        
        # Check other filters (can be extended)
        return True
    
    async def _deliver_to_endpoint(self, endpoint, event: Event) -> None:
        """Deliver event to a specific webhook endpoint."""
        delivery_id = str(uuid4())
        
        try:
            # Prepare payload
            payload = event.to_dict()
            payload_json = json.dumps(payload, default=str)
            
            # Generate signature
            signature = self._generate_signature(payload_json, endpoint.secret)
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'X-Codegen-Event': event.event_type,
                'X-Codegen-Event-ID': event.event_id,
                'X-Codegen-Delivery': delivery_id,
                'X-Codegen-Signature': signature,
                'User-Agent': 'Codegen-Webhooks/1.0'
            }
            
            # Add custom headers
            if endpoint.headers:
                headers.update(endpoint.headers)
            
            # Attempt delivery with retries
            success = False
            last_error = None
            
            for attempt in range(self.max_retries + 1):
                try:
                    response = await self._client.post(
                        endpoint.url,
                        content=payload_json,
                        headers=headers
                    )
                    
                    if 200 <= response.status_code < 300:
                        success = True
                        break
                    else:
                        last_error = f"HTTP {response.status_code}: {response.text}"
                        
                except Exception as e:
                    last_error = str(e)
                
                # Wait before retry (exponential backoff)
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)
            
            # Record delivery
            await self._record_delivery(
                endpoint, event, delivery_id, success, last_error
            )
            
            if success:
                logger.info(f"Webhook delivered: {event.event_type} to {endpoint.url}")
            else:
                logger.error(f"Webhook delivery failed: {event.event_type} to {endpoint.url} - {last_error}")
                
        except Exception as e:
            logger.error(f"Webhook delivery error: {e}")
            await self._record_delivery(
                endpoint, event, delivery_id, False, str(e)
            )
    
    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook payload."""
        if not secret:
            return ''
        
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    async def _record_delivery(
        self, 
        endpoint, 
        event: Event, 
        delivery_id: str, 
        success: bool, 
        error: Optional[str]
    ) -> None:
        """Record webhook delivery attempt."""
        try:
            with db_session_scope() as session:
                from .models.webhooks import WebhookDelivery
                
                delivery = WebhookDelivery(
                    delivery_id=delivery_id,
                    webhook_endpoint_id=endpoint.id,
                    event_id=event.event_id,
                    event_type=event.event_type,
                    success=success,
                    status_code=200 if success else 500,
                    error_message=error,
                    delivered_at=datetime.utcnow().isoformat() + 'Z'
                )
                session.add(delivery)
                
        except Exception as e:
            logger.error(f"Failed to record webhook delivery: {e}")


class WebSocketManager:
    """
    WebSocket connection manager for real-time updates.
    
    Provides:
    - Connection management
    - Event broadcasting
    - User-specific notifications
    - Connection authentication
    """
    
    def __init__(self):
        self._connections: Dict[str, List[Any]] = {}  # user_id -> [connections]
        self._organization_connections: Dict[str, List[Any]] = {}  # org_id -> [connections]
    
    def add_connection(
        self, 
        connection: Any, 
        user_id: str, 
        organization_id: Optional[str] = None
    ) -> None:
        """Add a WebSocket connection."""
        # Add to user connections
        if user_id not in self._connections:
            self._connections[user_id] = []
        self._connections[user_id].append(connection)
        
        # Add to organization connections
        if organization_id:
            if organization_id not in self._organization_connections:
                self._organization_connections[organization_id] = []
            self._organization_connections[organization_id].append(connection)
        
        logger.info(f"WebSocket connection added for user {user_id}")
    
    def remove_connection(
        self, 
        connection: Any, 
        user_id: str, 
        organization_id: Optional[str] = None
    ) -> None:
        """Remove a WebSocket connection."""
        # Remove from user connections
        if user_id in self._connections:
            try:
                self._connections[user_id].remove(connection)
                if not self._connections[user_id]:
                    del self._connections[user_id]
            except ValueError:
                pass
        
        # Remove from organization connections
        if organization_id and organization_id in self._organization_connections:
            try:
                self._organization_connections[organization_id].remove(connection)
                if not self._organization_connections[organization_id]:
                    del self._organization_connections[organization_id]
            except ValueError:
                pass
        
        logger.info(f"WebSocket connection removed for user {user_id}")
    
    async def broadcast_event(self, event: Event) -> None:
        """Broadcast event to relevant WebSocket connections."""
        message = {
            'type': 'event',
            'event': event.to_dict()
        }
        message_json = json.dumps(message, default=str)
        
        # Send to specific user
        if event.user_id and event.user_id in self._connections:
            await self._send_to_connections(
                self._connections[event.user_id], 
                message_json
            )
        
        # Send to organization members
        if event.organization_id and event.organization_id in self._organization_connections:
            await self._send_to_connections(
                self._organization_connections[event.organization_id], 
                message_json
            )
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> None:
        """Send message to a specific user."""
        if user_id in self._connections:
            message_json = json.dumps(message, default=str)
            await self._send_to_connections(
                self._connections[user_id], 
                message_json
            )
    
    async def _send_to_connections(self, connections: List[Any], message: str) -> None:
        """Send message to a list of connections."""
        if not connections:
            return
        
        # Remove closed connections
        active_connections = []
        for connection in connections:
            try:
                await connection.send_text(message)
                active_connections.append(connection)
            except Exception as e:
                logger.debug(f"Removing closed WebSocket connection: {e}")
        
        # Update connections list
        connections[:] = active_connections


# Global instances
_event_emitter: Optional[EventEmitter] = None
_webhook_manager: Optional[WebhookManager] = None
_websocket_manager: Optional[WebSocketManager] = None


def get_event_emitter() -> EventEmitter:
    """Get the global event emitter instance."""
    global _event_emitter, _webhook_manager, _websocket_manager
    
    if _event_emitter is None:
        _event_emitter = EventEmitter()
        
        # Initialize managers
        _webhook_manager = WebhookManager()
        _websocket_manager = WebSocketManager()
        
        # Connect managers
        _event_emitter.set_webhook_manager(_webhook_manager)
        _event_emitter.set_websocket_manager(_websocket_manager)
    
    return _event_emitter


def get_webhook_manager() -> WebhookManager:
    """Get the global webhook manager instance."""
    get_event_emitter()  # Ensure initialization
    return _webhook_manager


def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance."""
    get_event_emitter()  # Ensure initialization
    return _websocket_manager
