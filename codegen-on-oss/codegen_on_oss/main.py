"""
Main Entry Point for Codegen-on-OSS

This module provides the main entry point for the application.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from codegen_on_oss.api.server import run_server
from codegen_on_oss.database.manager import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def setup_database(db_url=None):
    """Initialize the database schema and create tables."""
    logger.info("Setting up database...")
    
    # Create database manager
    db_manager = DatabaseManager(db_url=db_url)
    
    # Create tables
    db_manager.create_tables()
    
    logger.info("Database setup complete!")

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Codegen-on-OSS Analysis System")
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Run the API server")
    server_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    server_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    server_parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    # Database setup command
    db_parser = subparsers.add_parser("setup-db", help="Set up the database")
    db_parser.add_argument("--db-url", help="Database URL")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle commands
    if args.command == "server":
        # Set up database first
        setup_database()
        
        # Run server
        logger.info(f"Starting server on {args.host}:{args.port}...")
        run_server(host=args.host, port=args.port, debug=args.debug)
    
    elif args.command == "setup-db":
        # Set up database
        setup_database(db_url=args.db_url)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

