#!/usr/bin/env python3
"""
Run script for the PR Review Bot.
This script adds the current directory to the Python path and runs the bot.
"""

import os
import sys
import argparse

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    """Main entry point for the run script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="PR Review Bot")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--use-ngrok", action="store_true", help="Use ngrok to expose the server")
    parser.add_argument("--webhook-url", type=str, help="Webhook URL to use (overrides ngrok)")
    parser.add_argument("--monitor-interval", type=int, default=300, help="Interval in seconds for monitoring repositories")
    parser.add_argument("--monitor-prs", action="store_true", help="Enable PR monitoring")
    parser.add_argument("--monitor-branches", action="store_true", help="Enable branch monitoring")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Import the main module
    from pr_review_bot.main import main as bot_main
    
    # Run the bot
    sys.exit(bot_main())

if __name__ == "__main__":
    main()
