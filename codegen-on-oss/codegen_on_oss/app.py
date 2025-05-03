"""
Main application module for codegen-on-oss.

This module provides the main application class for running the codegen-on-oss system.
"""

import os
import logging
import asyncio
import argparse
from typing import Dict, Any, Optional

from codegen_on_oss.database.connection import initialize_db
from codegen_on_oss.cache.manager import initialize_cache
from codegen_on_oss.events.bus import initialize_event_bus
from codegen_on_oss.api.websocket import start_websocket_server
from codegen_on_oss.api.rest import run_server as run_rest_server

logger = logging.getLogger(__name__)

class CodegenApp:
    """
    Main application class for codegen-on-oss.
    
    This class provides methods for initializing and running the codegen-on-oss system.
    """
    
    def __init__(
        self,
        db_url: Optional[str] = None,
        cache_backend: str = 'memory',
        cache_config: Optional[Dict[str, Any]] = None,
        rest_host: str = '0.0.0.0',
        rest_port: int = 8000,
        websocket_host: str = '0.0.0.0',
        websocket_port: int = 8765,
        log_level: str = 'INFO'
    ):
        """
        Initialize the application.
        
        Args:
            db_url: Database connection URL. If None, uses the CODEGEN_DB_URL environment variable.
            cache_backend: Cache backend to use ('memory', 'redis', or 'file').
            cache_config: Additional configuration for the cache backend.
            rest_host: Host for the REST API server.
            rest_port: Port for the REST API server.
            websocket_host: Host for the WebSocket server.
            websocket_port: Port for the WebSocket server.
            log_level: Logging level.
        """
        self.db_url = db_url or os.environ.get('CODEGEN_DB_URL')
        self.cache_backend = cache_backend
        self.cache_config = cache_config or {}
        self.rest_host = rest_host
        self.rest_port = rest_port
        self.websocket_host = websocket_host
        self.websocket_port = websocket_port
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def initialize(self):
        """Initialize the application components."""
        logger.info("Initializing database...")
        initialize_db(self.db_url)
        
        logger.info(f"Initializing cache with backend: {self.cache_backend}...")
        initialize_cache(self.cache_backend, **self.cache_config)
        
        logger.info("Initializing event bus...")
        initialize_event_bus(async_mode=True)
        
        logger.info("Application initialized successfully")
    
    async def run_websocket_server(self):
        """Run the WebSocket server."""
        logger.info(f"Starting WebSocket server on {self.websocket_host}:{self.websocket_port}...")
        await start_websocket_server(self.websocket_host, self.websocket_port)
    
    def run_rest_server(self):
        """Run the REST API server."""
        logger.info(f"Starting REST API server on {self.rest_host}:{self.rest_port}...")
        run_rest_server(self.rest_host, self.rest_port)
    
    async def run(self):
        """Run the application."""
        self.initialize()
        
        # Start the WebSocket server
        await self.run_websocket_server()
        
        # Start the REST API server in a separate thread
        import threading
        rest_thread = threading.Thread(target=self.run_rest_server, daemon=True)
        rest_thread.start()
        
        # Keep the main thread alive
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            logger.info("Application stopped")


def main():
    """Run the application from the command line."""
    parser = argparse.ArgumentParser(description='Run the codegen-on-oss application')
    parser.add_argument('--db-url', help='Database connection URL')
    parser.add_argument('--cache-backend', default='memory', choices=['memory', 'redis', 'file'], help='Cache backend to use')
    parser.add_argument('--rest-host', default='0.0.0.0', help='Host for the REST API server')
    parser.add_argument('--rest-port', type=int, default=8000, help='Port for the REST API server')
    parser.add_argument('--websocket-host', default='0.0.0.0', help='Host for the WebSocket server')
    parser.add_argument('--websocket-port', type=int, default=8765, help='Port for the WebSocket server')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Logging level')
    
    args = parser.parse_args()
    
    app = CodegenApp(
        db_url=args.db_url,
        cache_backend=args.cache_backend,
        rest_host=args.rest_host,
        rest_port=args.rest_port,
        websocket_host=args.websocket_host,
        websocket_port=args.websocket_port,
        log_level=args.log_level
    )
    
    asyncio.run(app.run())


if __name__ == '__main__':
    main()

