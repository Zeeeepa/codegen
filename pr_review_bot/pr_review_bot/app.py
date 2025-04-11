#!/usr/bin/env python3
"""
PR Review Agent - Main Application
This is the main entry point for the PR Review Agent, which provides a locally hostable
backend for reviewing PRs and new branches, validating them against the codebase and documentation.
"""
import os
import sys
import logging
import argparse
import uvicorn
from dotenv import load_dotenv
from api.app import create_app
from core.config_manager import ConfigManager
from utils.logger import setup_logging
def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="PR Review Agent")
    parser.add_argument("--config", type=str, default="config/default.yaml", 
                        help="Path to configuration file")
    parser.add_argument("--port", type=int, default=8000, 
                        help="Port to run the server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", 
                        help="Host to run the server on")
    parser.add_argument("--log-level", type=str, default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Logging level")
    parser.add_argument("--log-file", type=str, default="pr_review_agent.log",
                        help="Path to log file")
    parser.add_argument("--env-file", type=str, default=".env",
                        help="Path to .env file")
    return parser.parse_args()
def main():
    """Main entry point for the PR Review Agent."""
    # Parse command line arguments
    args = parse_args()
    
    # Set up logging
    setup_logging(log_file=args.log_file, log_level=args.log_level)
    logger = logging.getLogger(__name__)
    
    # Load environment variables
    load_dotenv(args.env_file)
    
    # Load configuration
    config_manager = ConfigManager(args.config)
    config = config_manager.get_config()
    
    # Create FastAPI app
    app = create_app(config)
    
    # Run the server
    logger.info(f"Starting PR Review Agent on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)
if __name__ == "__main__":
    main()