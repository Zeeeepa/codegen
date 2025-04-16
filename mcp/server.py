"""
MCP server implementation.

This module provides the HTTP server implementation for the MCP server.
"""

import argparse
import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Optional, Tuple, Union

from .protocol.router import Router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MCPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the MCP server."""

    def __init__(self, *args, router: Router = None, **kwargs):
        """Initialize the request handler.

        Args:
            router (Router, optional): Router to handle requests. Defaults to None.
        """
        self.router = router
        super().__init__(*args, **kwargs)

    def _set_headers(self, status_code: int = 200, content_type: str = "application/json"):
        """Set the response headers.

        Args:
            status_code (int, optional): HTTP status code. Defaults to 200.
            content_type (str, optional): Content type. Defaults to "application/json".
        """
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        """Handle OPTIONS requests."""
        self._set_headers()

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/health":
            self._set_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

    def do_POST(self):
        """Handle POST requests."""
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)

        try:
            request = json.loads(post_data.decode("utf-8"))
            operation = request.get("operation")
            params = request.get("params", {})

            if not operation:
                self._set_headers(400)
                self.wfile.write(
                    json.dumps({"error": "Missing required field: operation"}).encode()
                )
                return

            if not self.router:
                self._set_headers(500)
                self.wfile.write(
                    json.dumps({"error": "Server not properly initialized"}).encode()
                )
                return

            response = self.router.handle_request(operation, params)
            self._set_headers(200 if response.get("success", False) else 400)
            self.wfile.write(json.dumps(response).encode())

        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
        except Exception as e:
            logger.exception("Error handling request")
            self._set_headers(500)
            self.wfile.write(
                json.dumps({"error": f"Internal server error: {str(e)}"}).encode()
            )


class MCPServer:
    """MCP server."""

    def __init__(self, host: str = "localhost", port: int = 8000, codebase=None):
        """Initialize the MCP server.

        Args:
            host (str, optional): Host to bind to. Defaults to "localhost".
            port (int, optional): Port to bind to. Defaults to 8000.
            codebase: The codebase to operate on. Defaults to None.
        """
        self.host = host
        self.port = port
        self.codebase = codebase
        self.router = Router(codebase)
        self.server = None

    def start(self):
        """Start the server."""
        handler = lambda *args, **kwargs: MCPRequestHandler(
            *args, router=self.router, **kwargs
        )
        self.server = HTTPServer((self.host, self.port), handler)
        logger.info(f"Starting MCP server on {self.host}:{self.port}")
        self.server.serve_forever()

    def stop(self):
        """Stop the server."""
        if self.server:
            self.server.shutdown()
            logger.info("MCP server stopped")


def main():
    """Run the MCP server."""
    parser = argparse.ArgumentParser(description="MCP Server")
    parser.add_argument(
        "--host", type=str, default="localhost", help="Host to bind to"
    )
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--repo", type=str, help="Path to the repository")
    args = parser.parse_args()

    # This would be implemented to load the actual codebase
    # For now, just pass None as a placeholder
    codebase = None
    if args.repo:
        logger.info(f"Loading codebase from {args.repo}")
        # codebase = load_codebase(args.repo)

    server = MCPServer(host=args.host, port=args.port, codebase=codebase)
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping server")
        server.stop()


if __name__ == "__main__":
    main()
