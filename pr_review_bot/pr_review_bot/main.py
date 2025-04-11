"""
Main entry point for the PR Review Bot.
"""

import os
import sys
import logging
import argparse
import threading
import time
import signal
import traceback
from typing import Dict, Any, Optional, List, Tuple

# Import core components
from .core.github_client import GitHubClient
from .core.pr_reviewer import PRReviewer
from .core.pr_review_controller import PRReviewController

# Import monitors
from .monitors.pr_monitor import PRMonitor
from .monitors.branch_monitor import BranchMonitor

# Import utilities
from .utils.logger import setup_logging
from .utils.ngrok_manager import NgrokManager
from .utils.webhook_manager import WebhookManager

# Import API
from .api.app import PRReviewBotApp

logger = logging.getLogger(__name__)

def parse_args():
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="PR Review Bot")
    
    # Server settings
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")
    
    # GitHub settings
    parser.add_argument("--github-token", type=str, help="GitHub API token")
    parser.add_argument("--webhook-secret", type=str, help="GitHub webhook secret")
    
    # Slack settings
    parser.add_argument("--slack-channel", type=str, help="Slack channel to send notifications to")
    
    # Monitor settings
    parser.add_argument("--monitor-interval", type=int, default=300, help="Interval in seconds between checks")
    parser.add_argument("--threads", type=int, default=10, help="Number of threads to use for parallel processing")
    parser.add_argument("--monitor-prs", action="store_true", help="Monitor PRs")
    parser.add_argument("--monitor-branches", action="store_true", help="Monitor branches")
    parser.add_argument("--show-merges", action="store_true", help="Show recent merges on startup")
    parser.add_argument("--show-projects", action="store_true", help="Show project implementation stats on startup")
    parser.add_argument("--skip-empty-branches", action="store_true", help="Skip branches with no commits")
    
    # Ngrok settings
    parser.add_argument("--ngrok", action="store_true", help="Use ngrok to expose the server")
    parser.add_argument("--ngrok-auth-token", type=str, help="Ngrok auth token")
    
    # Webhook settings
    parser.add_argument("--setup-webhooks", action="store_true", help="Set up webhooks for repositories")
    parser.add_argument("--webhook-url", type=str, help="Webhook URL")
    
    # Logging settings
    parser.add_argument("--log-file", type=str, help="Log file")
    parser.add_argument("--log-level", type=str, default="INFO", help="Log level")
    
    return parser.parse_args()

def monitor_ip_changes(webhook_manager, ngrok_manager, interval=300):
    """
    Monitor IP changes and update webhooks if needed.
    
    Args:
        webhook_manager: Webhook manager
        ngrok_manager: Ngrok manager
        interval: Interval in seconds between checks
    """
    logger.info(f"Starting IP change monitor with interval {interval} seconds")
    
    # Get initial URL
    last_url = ngrok_manager.get_public_url()
    
    while True:
        time.sleep(interval)
        
        # Get current URL
        current_url = ngrok_manager.get_public_url()
        
        # Check if URL has changed
        if current_url != last_url:
            logger.info(f"Public URL changed from {last_url} to {current_url}")
            
            # Update webhook URL
            webhook_manager.webhook_url = current_url
            webhook_manager.setup_webhooks_for_all_repos()
            
            # Update last URL
            last_url = current_url

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
        
    Returns:
        Tuple of (pr_monitor, branch_monitor)
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
    # Parse command line arguments
    args = parse_args()
    
    # Set up logging
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    setup_logging(args.log_file, log_level)
    
    # Get GitHub token
    github_token = args.github_token or os.environ.get("GITHUB_TOKEN")
    if not github_token:
        logger.error("GitHub token is required")
        print("Error: GitHub token is required")
        print("Set it with --github-token or GITHUB_TOKEN environment variable")
        sys.exit(1)
    
    # Get webhook secret
    webhook_secret = args.webhook_secret or os.environ.get("GITHUB_WEBHOOK_SECRET")
    
    # Get Slack channel
    slack_channel = args.slack_channel or os.environ.get("SLACK_CHANNEL")
    
    # Create GitHub client
    github_client = GitHubClient(github_token)
    
    # Create PR reviewer
    pr_reviewer = PRReviewer(github_token, slack_channel=slack_channel)
    
    # Get PR Review Controller from PR Reviewer
    pr_review_controller = pr_reviewer.pr_review_controller
    
    # Set up ngrok if requested
    ngrok_manager = None
    webhook_url = args.webhook_url
    
    if args.ngrok:
        logger.info("Setting up ngrok")
        print("\n🌐 Setting up ngrok...")
        
        ngrok_auth_token = args.ngrok_auth_token or os.environ.get("NGROK_AUTH_TOKEN")
        ngrok_manager = NgrokManager(args.port, auth_token=ngrok_auth_token)
        webhook_url = ngrok_manager.start_tunnel()
        
        if webhook_url:
            logger.info(f"Ngrok tunnel established at {webhook_url}")
            print(f"\n✅ Ngrok tunnel established at {webhook_url}")
        else:
            logger.error("Failed to establish ngrok tunnel")
            print("\n❌ Failed to establish ngrok tunnel")
            sys.exit(1)
    
    # Set up webhooks if requested
    webhook_manager = None
    
    if args.setup_webhooks:
        if not webhook_url:
            logger.error("Webhook URL is required for setting up webhooks")
            print("\n❌ Webhook URL is required for setting up webhooks")
            print("Set it with --webhook-url or use --ngrok")
            sys.exit(1)
        
        logger.info(f"Setting up webhooks with URL {webhook_url}")
        print(f"\n🔗 Setting up webhooks with URL {webhook_url}")
        
        webhook_manager = WebhookManager(
            github_client=github_client,
            webhook_url=webhook_url,
            webhook_secret=webhook_secret
        )
        
        webhook_manager.setup_webhooks_for_all_repos()
    
    # Start IP change monitor if using ngrok and webhooks
    if ngrok_manager and webhook_manager:
        logger.info("Starting IP change monitor")
        print("\n🔄 Starting IP change monitor...")
        
        ip_monitor_thread = threading.Thread(
            target=monitor_ip_changes,
            args=(webhook_manager, ngrok_manager),
            daemon=True
        )
        ip_monitor_thread.start()
    
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
    
    # Create FastAPI app
    app = PRReviewBotApp(
        github_token=github_token,
        webhook_secret=webhook_secret,
        slack_channel=slack_channel
    ).get_app()
    
    # Start the server
    logger.info(f"Starting server on {args.host}:{args.port}")
    print(f"\n🚀 Starting server on {args.host}:{args.port}")
    
    # Import uvicorn here to avoid circular imports
    import uvicorn
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutting down...")
        print("\n👋 Shutting down...")
        
        # Stop ngrok tunnel if running
        if ngrok_manager:
            ngrok_manager.stop_tunnel()
        
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the server
    uvicorn.run(app, host=args.host, port=args.port, workers=args.workers)

if __name__ == "__main__":
    main()
