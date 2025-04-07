#!/usr/bin/env python3
"""
Compatibility run script for the PR Review Bot.
This script provides a unified entry point for both old and new code structures.
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

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
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="PR Review Bot")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--use-ngrok", action="store_true", help="Use ngrok to expose the server")
    parser.add_argument("--webhook-url", type=str, help="Webhook URL to use (overrides ngrok)")
    parser.add_argument("--monitor-interval", type=int, default=300, help="Interval in seconds for monitoring repositories")
    parser.add_argument("--monitor-prs", action="store_true", help="Enable PR monitoring")
    parser.add_argument("--monitor-branches", action="store_true", help="Enable branch monitoring")
    parser.add_argument("--legacy", action="store_true", help="Use legacy app.py instead of the new structure")
    return parser.parse_args()

def load_env():
    """Load environment variables from .env file."""
    load_dotenv()
    if not os.environ.get("GITHUB_TOKEN"):
        logger.error("GITHUB_TOKEN environment variable is required")
        print("\n❌ GITHUB_TOKEN environment variable is required")
        print("Please create a .env file with your GitHub token")
        print("Example: GITHUB_TOKEN=ghp_your_token_here")
        return False
    return True

def run_legacy_app(args):
    """Run the legacy app.py."""
    logger.info("Running legacy app.py")
    print("\n🚀 Running legacy app.py")
    
    # Try to import and run the legacy app
    try:
        # Check if we need to use ngrok
        if args.use_ngrok:
            try:
                from ngrok_manager import NgrokManager
                ngrok_auth_token = os.environ.get("NGROK_AUTH_TOKEN")
                ngrok_manager = NgrokManager(args.port, auth_token=ngrok_auth_token)
                public_url = ngrok_manager.start_tunnel()
                
                if public_url:
                    print(f"\n✅ Ngrok tunnel started at {public_url}")
                    
                    # Set up webhooks
                    try:
                        from webhook_manager import WebhookManager
                        from helpers import get_github_client
                        
                        github_token = os.environ.get("GITHUB_TOKEN")
                        github_client = get_github_client(github_token)
                        
                        webhook_manager = WebhookManager(
                            github_client=github_client,
                            webhook_url=public_url + "/webhook"
                        )
                        
                        webhook_manager.setup_webhooks_for_all_repos()
                        print("\n✅ Webhooks set up successfully")
                    except Exception as e:
                        logger.error(f"Error setting up webhooks: {e}")
                        print(f"\n❌ Error setting up webhooks: {e}")
                else:
                    logger.error("Failed to start ngrok tunnel")
                    print("\n❌ Failed to start ngrok tunnel")
            except Exception as e:
                logger.error(f"Error starting ngrok: {e}")
                print(f"\n❌ Error starting ngrok: {e}")
        
        # Run the app
        import uvicorn
        from app_compat import app
        
        print(f"\n🚀 Starting server on port {args.port}...")
        uvicorn.run(app, host="0.0.0.0", port=args.port)
    except Exception as e:
        logger.error(f"Error running legacy app: {e}")
        print(f"\n❌ Error running legacy app: {e}")
        return False
    
    return True

def run_new_app(args):
    """Run the new app structure."""
    logger.info("Running new app structure")
    print("\n🚀 Running new app structure")
    
    try:
        # Import the main module from the new structure
        from pr_review_bot.main import main as bot_main
        
        # Run the bot
        sys.argv = [sys.argv[0]]  # Reset sys.argv
        
        # Add arguments
        if args.port:
            sys.argv.extend(["--port", str(args.port)])
        
        if args.use_ngrok:
            sys.argv.append("--use-ngrok")
        
        if args.webhook_url:
            sys.argv.extend(["--webhook-url", args.webhook_url])
        
        if args.monitor_interval:
            sys.argv.extend(["--monitor-interval", str(args.monitor_interval)])
        
        if args.monitor_prs:
            sys.argv.append("--monitor-prs")
        
        if args.monitor_branches:
            sys.argv.append("--monitor-branches")
        
        # Run the bot
        bot_main()
    except Exception as e:
        logger.error(f"Error running new app structure: {e}")
        print(f"\n❌ Error running new app structure: {e}")
        
        # Fall back to legacy app
        print("\n⚠️ Falling back to legacy app")
        return run_legacy_app(args)
    
    return True

def main():
    """Main entry point."""
    args = parse_args()
    
    # Load environment variables
    if not load_env():
        sys.exit(1)
    
    # Check if we should use the legacy app
    if args.legacy:
        if not run_legacy_app(args):
            sys.exit(1)
    else:
        # Try to run the new app structure first
        try:
            # Check if the new structure is available
            import pr_review_bot.main
            if not run_new_app(args):
                sys.exit(1)
        except ImportError:
            # Fall back to legacy app
            logger.warning("New app structure not found, falling back to legacy app")
            print("\n⚠️ New app structure not found, falling back to legacy app")
            if not run_legacy_app(args):
                sys.exit(1)

if __name__ == "__main__":
    main()
