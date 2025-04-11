"""
Main application module for the PR Review Bot.
This module provides the entry point for the PR Review Bot.
"""

import os
import sys
import logging
import argparse
from typing import Dict, Any, Optional
import uvicorn
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pr_review_bot.log")
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="PR Review Bot")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    return parser.parse_args()

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
    """
    import yaml
    
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        
        # Override config with environment variables
        if "github" in config:
            config["github"]["token"] = os.environ.get("GITHUB_TOKEN", config["github"].get("token", ""))
            config["github"]["webhook_secret"] = os.environ.get("GITHUB_WEBHOOK_SECRET", config["github"].get("webhook_secret", ""))
        
        if "ai" in config:
            config["ai"]["api_key"] = os.environ.get(f"{config['ai']['provider'].upper()}_API_KEY", config["ai"].get("api_key", ""))
        
        if "notification" in config and "slack" in config["notification"]:
            config["notification"]["slack"]["token"] = os.environ.get("SLACK_BOT_TOKEN", config["notification"]["slack"].get("token", ""))
            config["notification"]["slack"]["channel"] = os.environ.get("SLACK_CHANNEL", config["notification"]["slack"].get("channel", ""))
        
        return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise

def main():
    """Main entry point for the PR Review Bot."""
    args = parse_args()
    
    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        sys.exit(1)
    
    # Import FastAPI app
    try:
        from .api.app import app
        logger.info("Successfully imported FastAPI app")
    except ImportError as e:
        logger.error(f"Error importing FastAPI app: {e}")
        sys.exit(1)
    
    # Start the server
    logger.info(f"Starting PR Review Bot on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
