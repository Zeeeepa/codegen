"""
WebSocket server for real-time updates.

This module provides a WebSocket server for sending real-time updates to clients.
"""

import logging
import asyncio
import json
import time
from typing import Dict, List, Any, Set, Optional
from datetime import datetime

import websockets
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed

from codegen_on_oss.events.bus import EventBus, Event, EventType, get_event_bus

logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    WebSocket manager for handling client connections and sending updates.
    
    This class provides methods for managing WebSocket connections and sending
    real-time updates to connected clients.
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        """
        Initialize the WebSocket manager.
        
        Args:
            event_bus: Event bus instance. If None, uses the global instance.
        """
        self.event_bus = event_bus or get_event_bus()
        self.clients: Dict[str, WebSocketServerProtocol] = {}
        self.subscriptions: Dict[str, Set[EventType]] = {}
        self.server = None
        
        # Subscribe to all events
        self.event_bus.subscribe_to_all(self.handle_event)
    
    async def handle_event(self, event: Event) -> None:
        """
        Handle an event from the event bus.
        
        Args:
            event: Event to handle.
        """
        # Send the event to all subscribed clients
        for client_id, subscribed_events in self.subscriptions.items():
            if event.type in subscribed_events:
                client = self.clients.get(client_id)
                if client:
                    try:
                        await client.send(event.to_json())
                    except ConnectionClosed:
                        # Client disconnected, remove it
                        await self.remove_client(client_id)
                    except Exception as e:
                        logger.error(f"Error sending event to client {client_id}: {e}")
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """
        Handle a WebSocket client connection.
        
        Args:
            websocket: WebSocket connection.
            path: Connection path.
        """
        # Generate a client ID
        client_id = f"client-{time.time()}-{id(websocket)}"
        
        # Add the client to the clients dict
        self.clients[client_id] = websocket
        self.subscriptions[client_id] = set()
        
        logger.info(f"Client {client_id} connected")
        
        try:
            # Send a welcome message
            await websocket.send(json.dumps({
                'type': 'welcome',
                'client_id': client_id,
                'timestamp': datetime.utcnow().isoformat()
            }))
            
            # Handle messages from the client
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(client_id, data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from client {client_id}: {message}")
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': 'Invalid JSON',
                        'timestamp': datetime.utcnow().isoformat()
                    }))
                except Exception as e:
                    logger.error(f"Error handling message from client {client_id}: {e}")
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': str(e),
                        'timestamp': datetime.utcnow().isoformat()
                    }))
        except ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            # Remove the client
            await self.remove_client(client_id)
    
    async def handle_message(self, client_id: str, data: Dict[str, Any]) -> None:
        """
        Handle a message from a client.
        
        Args:
            client_id: Client ID.
            data: Message data.
        """
        message_type = data.get('type')
        
        if message_type == 'subscribe':
            # Subscribe to events
            event_types = data.get('event_types', [])
            for event_type_name in event_types:
                try:
                    event_type = EventType[event_type_name]
                    self.subscriptions[client_id].add(event_type)
                    logger.debug(f"Client {client_id} subscribed to {event_type.name}")
                except KeyError:
                    logger.warning(f"Invalid event type: {event_type_name}")
            
            # Send a confirmation
            client = self.clients.get(client_id)
            if client:
                await client.send(json.dumps({
                    'type': 'subscribed',
                    'event_types': [et.name for et in self.subscriptions[client_id]],
                    'timestamp': datetime.utcnow().isoformat()
                }))
        
        elif message_type == 'unsubscribe':
            # Unsubscribe from events
            event_types = data.get('event_types', [])
            for event_type_name in event_types:
                try:
                    event_type = EventType[event_type_name]
                    self.subscriptions[client_id].discard(event_type)
                    logger.debug(f"Client {client_id} unsubscribed from {event_type.name}")
                except KeyError:
                    logger.warning(f"Invalid event type: {event_type_name}")
            
            # Send a confirmation
            client = self.clients.get(client_id)
            if client:
                await client.send(json.dumps({
                    'type': 'unsubscribed',
                    'event_types': [et.name for et in self.subscriptions[client_id]],
                    'timestamp': datetime.utcnow().isoformat()
                }))
        
        elif message_type == 'ping':
            # Respond with a pong
            client = self.clients.get(client_id)
            if client:
                await client.send(json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.utcnow().isoformat()
                }))
        
        else:
            logger.warning(f"Unknown message type from client {client_id}: {message_type}")
            client = self.clients.get(client_id)
            if client:
                await client.send(json.dumps({
                    'type': 'error',
                    'message': f"Unknown message type: {message_type}",
                    'timestamp': datetime.utcnow().isoformat()
                }))
    
    async def remove_client(self, client_id: str) -> None:
        """
        Remove a client.
        
        Args:
            client_id: Client ID.
        """
        if client_id in self.clients:
            client = self.clients[client_id]
            try:
                await client.close()
            except Exception as e:
                logger.error(f"Error closing client {client_id}: {e}")
            
            del self.clients[client_id]
        
        if client_id in self.subscriptions:
            del self.subscriptions[client_id]
        
        logger.info(f"Client {client_id} removed")
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: Message to broadcast.
        """
        json_message = json.dumps(message)
        
        for client_id, client in list(self.clients.items()):
            try:
                await client.send(json_message)
            except ConnectionClosed:
                # Client disconnected, remove it
                await self.remove_client(client_id)
            except Exception as e:
                logger.error(f"Error broadcasting to client {client_id}: {e}")
    
    async def start_server(self, host: str = 'localhost', port: int = 8765) -> None:
        """
        Start the WebSocket server.
        
        Args:
            host: Server host.
            port: Server port.
        """
        self.server = await websockets.serve(self.handle_client, host, port)
        logger.info(f"WebSocket server started on {host}:{port}")
    
    async def stop_server(self) -> None:
        """Stop the WebSocket server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.server = None
            logger.info("WebSocket server stopped")


# Global WebSocket manager instance
websocket_manager = None

def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance."""
    global websocket_manager
    if websocket_manager is None:
        websocket_manager = WebSocketManager()
    return websocket_manager

async def start_websocket_server(host: str = 'localhost', port: int = 8765) -> WebSocketManager:
    """
    Start the WebSocket server.
    
    Args:
        host: Server host.
        port: Server port.
        
    Returns:
        WebSocketManager instance.
    """
    manager = get_websocket_manager()
    await manager.start_server(host, port)
    return manager

