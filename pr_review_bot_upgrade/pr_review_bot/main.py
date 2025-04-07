"""
Main module for the PR Review Bot.
Provides the entry point for running the bot.
"""

import os
import sys
import time
import logging
import argparse
import threading
import schedule
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import uvicorn

from .core.github_client import GitHubClient
from .core.pr_reviewer import PRReviewer
from .utils.webhook_manager import WebhookManager
from .utils.ngrok_manager import NgrokManager
from .monitors.pr_monitor import PRMonitor
from .monitors.branch_monitor import BranchMonitor
from .api.app import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pr_review_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("pr_review_bot")

def parse_args():
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="PR Review Bot")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--use-ngrok", action="store_true", help="Use ngrok to expose the server")
    parser.add_argument("--webhook-url", type=str, help="Webhook URL to use (overrides ngrok)")
    parser.add_argument("--monitor-interval", type=int, default=300, help="Interval in seconds for monitoring repositories")
    parser.add_argument("--monitor-prs", action="store_true", help="Enable PR monitoring")
    parser.add_argument("--monitor-branches", action="store_true", help="Enable branch monitoring")
    return parser.parse_args()

def load_env():
    """
    Load environment variables from .env file.
    
    Returns:
        True if successful, False otherwise
    """
    load_dotenv()
    if not os.environ.get("GITHUB_TOKEN"):
        logger.error("GITHUB_TOKEN environment variable is required")
        print("\n❌ GITHUB_TOKEN environment variable is required")
        print("Please create a .env file with your GitHub token")
        print("Example: GITHUB_TOKEN=ghp_your_token_here")
        return False
    return True

def monitor_ip_changes(webhook_manager, ngrok_manager, interval=300):
    """
    Monitor ngrok IP changes and update webhooks accordingly.
    
    Args:
        webhook_manager: Webhook manager
        ngrok_manager: Ngrok manager
        interval: Interval in seconds between checks
    """
    logger.info("Starting IP change monitor")
    print("\n🔄 Starting IP change monitor...")
    
    last_url = ngrok_manager.get_public_url()
    
    while True:
        try:
            time.sleep(interval)
            current_url = ngrok_manager.get_public_url()
            
            if current_url != last_url:
                logger.info(f"IP changed from {last_url} to {current_url}")
                print(f"\n🔄 IP changed from {last_url} to {current_url}")
                
                webhook_manager.webhook_url = current_url
                webhook_manager.setup_webhooks_for_all_repos()
                last_url = current_url
        except Exception as e:
            logger.error(f"Error in IP monitor: {e}")
            print(f"\n❌ Error in IP monitor: {e}")

def run_monitors(github_client, pr_reviewer, monitor_interval, monitor_prs=True, monitor_branches=True):
    """
    Run PR and branch monitors.
    
    Args:
        github_client: GitHub client
        pr_reviewer: PR reviewer
        monitor_interval: Interval in seconds between checks
        monitor_prs: Whether to monitor PRs
        monitor_branches: Whether to monitor branches
    """
    if monitor_prs:
        logger.info("Starting PR monitor")
        print("\n🔄 Starting PR monitor...")
        
        pr_monitor = PRMonitor(github_client, pr_reviewer)
        pr_monitor_thread = threading.Thread(
            target=pr_monitor.run_monitor,
            args=(monitor_interval,),
            daemon=True
        )
        pr_monitor_thread.start()
    
    if monitor_branches:
        logger.info("Starting branch monitor")
        print("\n🔄 Starting branch monitor...")
        
        branch_monitor = BranchMonitor(github_client, pr_reviewer)
        branch_monitor_thread = threading.Thread(
            target=branch_monitor.run_monitor,
            args=(monitor_interval,),
            daemon=True
        )
        branch_monitor_thread.start()

def main():
    """
    Main entry point for the PR Review Bot.
    """
    args = parse_args()
    if not load_env():
        sys.exit(1)
    
    # Get GitHub token
    github_token = os.environ.get("GITHUB_TOKEN")
    
    # Create GitHub client
    github_client = GitHubClient(github_token)
    
    # Create PR reviewer
    pr_reviewer = PRReviewer(github_token)
    
    # Set up webhook URL
    webhook_url = args.webhook_url
    ngrok_manager = None
    
    if args.use_ngrok and not webhook_url:
        print("\n🔄 Starting ngrok tunnel...")
        try:
            ngrok_auth_token = os.environ.get("NGROK_AUTH_TOKEN")
            ngrok_manager = NgrokManager(args.port, auth_token=ngrok_auth_token)
            webhook_url = ngrok_manager.start_tunnel()
            
            if not webhook_url:
                logger.error("Failed to start ngrok tunnel")
                print("\n❌ Failed to start ngrok tunnel")
                sys.exit(1)
                
            print(f"\n✅ Ngrok tunnel started at {webhook_url}")
        except Exception as e:
            logger.error(f"Error starting ngrok: {e}")
            print(f"\n❌ Error starting ngrok: {e}")
            sys.exit(1)
    
    # Create webhook manager
    webhook_manager = WebhookManager(
        github_client=github_client,
        webhook_url=webhook_url or f"http://localhost:{args.port}/webhook"
    )
    
    # Set up webhooks for all repositories
    print("\n🔄 Setting up webhooks for all repositories...")
    try:
        webhook_manager.setup_webhooks_for_all_repos()
        print("\n✅ Webhooks set up successfully")
    except Exception as e:
        logger.error(f"Error setting up webhooks: {e}")
        print(f"\n❌ Error setting up webhooks: {e}")
    
    # Start IP change monitor if using ngrok
    if ngrok_manager:
        monitor_thread = threading.Thread(
            target=monitor_ip_changes,
            args=(webhook_manager, ngrok_manager),
            daemon=True
        )
        monitor_thread.start()
    
    # Start PR and branch monitors
    run_monitors(
        github_client=github_client,
        pr_reviewer=pr_reviewer,
        monitor_interval=args.monitor_interval,
        monitor_prs=args.monitor_prs,
        monitor_branches=args.monitor_branches
    )
    
    # Start the server
    print(f"\n🚀 Starting server on port {args.port}...")
    try:
        uvicorn.run(app, host="0.0.0.0", port=args.port)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
