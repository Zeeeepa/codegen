#!/usr/bin/env python3
"""
Script to run the WSL server.
"""

import argparse
import logging
import os

from codegen_on_oss.wsl import WSLServer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Run the WSL server."""
    parser = argparse.ArgumentParser(description="Run the WSL server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--api-key", help="API key for authentication")
    
    args = parser.parse_args()
    
    # Get API key from environment if not provided
    api_key = args.api_key or os.environ.get("WSL_API_KEY")
    
    logger.info(f"Starting WSL server on {args.host}:{args.port}")
    
    server = WSLServer(host=args.host, port=args.port, api_key=api_key)
    server.run()


if __name__ == "__main__":
    main()

