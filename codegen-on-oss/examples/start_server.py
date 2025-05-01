#!/usr/bin/env python
"""
Example script demonstrating how to start the Code Context Retrieval Server.

This script starts the FastAPI server that provides endpoints for analysis,
context management, and agent execution.
"""

import argparse
import os

from loguru import logger

from codegen_on_oss.context_server import start_server


def main():
    """Start the Code Context Retrieval Server."""
    parser = argparse.ArgumentParser(description="Start the Code Context Retrieval Server")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the server to",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to",
    )
    parser.add_argument(
        "--s3-bucket",
        type=str,
        help="Optional S3 bucket name for snapshot storage",
    )
    parser.add_argument(
        "--s3-endpoint",
        type=str,
        default="https://s3.amazonaws.com",
        help="S3 endpoint URL",
    )
    args = parser.parse_args()

    # Set environment variables for S3 integration if provided
    if args.s3_bucket:
        os.environ["S3_BUCKET"] = args.s3_bucket
        os.environ["S3_ENDPOINT"] = args.s3_endpoint
        logger.info(f"Configured S3 integration with bucket: {args.s3_bucket}")

    # Start the server
    logger.info(f"Starting Code Context Retrieval Server on {args.host}:{args.port}")
    start_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()

