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
from .utils.slack_notifier import SlackNotifier
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
    parser.add_argument("--threads", type=int, default=10, help="Number of threads to use for parallel processing")
    parser.add_argument("--show-merges", action="store_true", help="Show recent merges on startup")
    parser.add_argument("--show-projects", action="store_true", help="Show project implementation stats on startup")
    parser.add_argument("--slack-channel", type=str, help="Slack channel to send notifications to")
    parser.add_argument("--skip-empty-branches", action="store_true", help="Skip branches with no commits")
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

def run_monitors(github_client, pr_reviewer, monitor_interval, threads=10, monitor_prs=True, monitor_branches=True, show_merges=False, show_projects=False, skip_empty_branches=False):
    """
    Run PR and branch monitors.
    
    Args:
        github_client: GitHub client
        pr_reviewer: PR reviewer
        monitor_interval: Interval in seconds between checks
        threads: Number of threads to use for parallel processing
        monitor_prs: Whether to monitor PRs
        monitor_branches: Whether to monitor branches
        show_merges: Whether to show recent merges on startup
        show_projects: Whether to show project implementation stats on startup
        skip_empty_branches: Whether to skip branches with no commits
    """
    pr_monitor = None
    branch_monitor = None
    
    if monitor_branches:
        logger.info("Starting branch monitor")
        print("\n🔄 Starting branch monitor...")
        
        branch_monitor = BranchMonitor(github_client, pr_reviewer)
        branch_monitor.max_workers = threads
        branch_monitor.skip_empty_branches = skip_empty_branches
        
        if skip_empty_branches:
            logger.info("Branch monitor will skip branches with no commits")
            print("\n⚙️ Branch monitor will skip branches with no commits")
        
        branch_monitor_thread = threading.Thread(
            target=branch_monitor.run_monitor,
            args=(monitor_interval,),
            daemon=True
        )
        branch_monitor_thread.start()
        
        # Show recent merges if requested
        if show_merges:
            print("\n📊 Getting recent merges...")
            merges = branch_monitor.get_recent_merges()
            print(f"\nFound {len(merges)} recent merges")
            for i, merge in enumerate(merges[:10], 1):
                print(f"{i}. {merge['pr_title']} - {merge['repo_name']} - {merge['merged_at'].strftime('%Y-%m-%d')}")
        
        # Show project implementation stats if requested
        if show_projects:
            print("\n📊 Getting project implementation stats...")
            stats = branch_monitor.get_project_implementation_stats()
            print("\nProject implementation counts:")
            for project, count in list(stats.items())[:10]:
                print(f"- {project}: {count} implementations")
    
    if monitor_prs:
        logger.info("Starting PR monitor")
        print("\n🔄 Starting PR monitor...")
        
        pr_monitor = PRMonitor(github_client, pr_reviewer)
        pr_monitor.max_workers = threads
        pr_monitor_thread = threading.Thread(
            target=pr_monitor.run_monitor,
            args=(monitor_interval,),
            daemon=True
        )
        pr_monitor_thread.start()
    
    return pr_monitor, branch_monitor

def main():
    """
    Main entry point for the PR Review Bot.
    """
    args = parse_args()
    if not load_env():
        sys.exit(1)
    
    # Get GitHub token
    github_token = os.environ.get("GITHUB_TOKEN")
    
    # Get Slack channel
    slack_channel = args.slack_channel or os.environ.get("SLACK_NOTIFICATION_CHANNEL")
    if slack_channel:
        logger.info(f"Slack notifications will be sent to channel: {slack_channel}")
        print(f"\n📣 Slack notifications will be sent to channel: {slack_channel}")
    else:
        logger.info("No Slack channel specified, notifications will be disabled")
        print("\n⚠️ No Slack channel specified, notifications will be disabled")
    
    # Create GitHub client
    github_client = GitHubClient(github_token)
    
    # Create PR reviewer
    pr_reviewer = PRReviewer(github_token, slack_channel=slack_channel)
    
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
    pr_monitor, branch_monitor = run_monitors(
        github_client=github_client,
        pr_reviewer=pr_reviewer,
        monitor_interval=args.monitor_interval,
        threads=args.threads,
        monitor_prs=args.monitor_prs,
        monitor_branches=args.monitor_branches,
        show_merges=args.show_merges,
        show_projects=args.show_projects,
        skip_empty_branches=args.skip_empty_branches
    )
    
    # Start the server
    print(f"\n🚀 Starting server on port {args.port}...")
    try:
        # Add routes for the new functionality
        @app.get("/api/merges")
        async def get_recent_merges():
            if branch_monitor:
                merges = branch_monitor.get_recent_merges()
                return {"merges": merges}
            return {"error": "Branch monitor not enabled"}
        
        @app.get("/api/projects")
        async def get_project_stats():
            if branch_monitor:
                stats = branch_monitor.get_project_implementation_stats()
                return {"projects": stats}
            return {"error": "Branch monitor not enabled"}
        
        @app.get("/api/status")
        async def get_status_report():
            if branch_monitor:
                report = branch_monitor.generate_status_report()
                return {"report": report}
            return {"error": "Branch monitor not enabled"}
        
        uvicorn.run(app, host="0.0.0.0", port=args.port)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
