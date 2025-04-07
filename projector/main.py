import os
import sys
import argparse
import subprocess
import logging
import multiprocessing
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="MultiThread Slack GitHub Tool"
    )
    
    parser.add_argument(
        "--ui", "-u",
        action="store_true",
        help="Launch the Streamlit UI"
    )
    
    parser.add_argument(
        "--backend", "-b",
        action="store_true",
        help="Run the backend service only"
    )
    
    parser.add_argument(
        "--docs", "-d",
        default="./docs",
        help="Path to markdown documents folder"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--threads",
        type=int,
        default=10,
        help="Maximum number of concurrent threads (1-10)"
    )
    
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Enable automatic Slack thread monitoring"
    )
    
    return parser.parse_args()

def setup_logging(debug=False):
    """Set up logging configuration."""
    log_level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("app.log")
        ]
    )
    
    return logging.getLogger(__name__)

def launch_streamlit():
    """Launch the Streamlit UI."""
    try:
        subprocess.run(["streamlit", "run", "frontend/streamlit_app.py"])
    except Exception as e:
        logging.error(f"Error launching Streamlit: {e}")
        sys.exit(1)

def run_backend(args):
    """Run the backend service."""
    # Load environment variables
    load_dotenv()
    
    # Import backend components
    from agentgen.application.projector.backend.config import (
        SLACK_USER_TOKEN, GITHUB_TOKEN, GITHUB_USERNAME,
        SLACK_DEFAULT_CHANNEL, GITHUB_DEFAULT_REPO
    )
    from agentgen.application.projector.backend.slack_manager import SlackManager
    from agentgen.application.projector.backend.github_manager import GitHubManager
    from agentgen.application.projector.backend.assistant_agent import AssistantAgent
    from agentgen.application.projector.backend.project_database import ProjectDatabase
    from agentgen.application.projector.backend.project_manager import ProjectManager
    from agentgen.application.projector.backend.thread_pool import ThreadPool
    from agentgen.application.projector.backend.utils import validate_config
    
    logger = setup_logging(debug=args.debug)
    
    # Validate configuration
    if not validate_config():
        logger.error("Invalid configuration. Please check your .env file.")
        sys.exit(1)
    
    try:
        # Initialize thread pool
        logger.info(f"Initializing Thread Pool with {args.threads} workers")
        thread_pool = ThreadPool(max_threads=args.threads)
        
        # Initialize database
        logger.info("Initializing Project Database")
        project_database = ProjectDatabase()
        
        # Initialize managers
        logger.info("Initializing Slack Manager")
        slack_manager = SlackManager(SLACK_USER_TOKEN, SLACK_DEFAULT_CHANNEL)
        
        logger.info("Initializing GitHub Manager")
        github_manager = GitHubManager(
            GITHUB_TOKEN,
            GITHUB_USERNAME,
            GITHUB_DEFAULT_REPO
        )
        
        # Initialize project manager
        logger.info("Initializing Project Manager")
        project_manager = ProjectManager(
            github_manager,
            slack_manager,
            thread_pool
        )
        
        # Initialize assistant agent
        logger.info("Initializing Assistant Agent")
        assistant_agent = AssistantAgent(
            slack_manager,
            github_manager,
            args.docs,
            project_database,
            project_manager,
            max_threads=args.threads
        )
        
        # Process existing documents
        logger.info("Processing markdown documents")
        assistant_agent.process_all_documents()
        
        # Start thread monitoring if enabled
        if args.monitor:
            logger.info("Starting Slack thread monitoring")
            monitor_thread = multiprocessing.Process(
                target=monitor_slack_threads,
                args=(assistant_agent,)
            )
            monitor_thread.daemon = True
            monitor_thread.start()
        
        logger.info("Backend service running. Press Ctrl+C to exit.")
        
        # Keep the main thread alive
        try:
            while True:
                # Sleep to prevent CPU hogging
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            if args.monitor and monitor_thread.is_alive():
                monitor_thread.terminate()
            thread_pool.shutdown(wait=True)
            sys.exit(0)
        
    except Exception as e:
        logger.error(f"Error running backend service: {e}")
        sys.exit(1)

def monitor_slack_threads(assistant_agent):
    """Monitor Slack threads for new messages."""
    logger = logging.getLogger("monitor")
    logger.info("Slack thread monitoring started")
    
    try:
        while True:
            assistant_agent.monitor_slack_threads()
            # Sleep for a few seconds before checking again
            import time
            time.sleep(5)
    except Exception as e:
        logger.error(f"Error in monitor thread: {e}")

def main():
    """Main function."""
    args = parse_arguments()
    logger = setup_logging(debug=args.debug)
    
    # Ensure args.threads is within valid range
    args.threads = max(1, min(10, args.threads))
    
    # Create necessary directories
    os.makedirs(args.docs, exist_ok=True)
    os.makedirs("./logs", exist_ok=True)
    
    if args.ui:
        logger.info("Launching Streamlit UI")
        launch_streamlit()
    elif args.backend:
        logger.info("Running backend service")
        run_backend(args)
    else:
        # Default behavior: launch both backend and UI
        logger.info("Launching both backend service and Streamlit UI")
        
        # Launch backend in a separate process
        backend_process = multiprocessing.Process(
            target=run_backend,
            args=(args,)
        )
        backend_process.start()
        
        # Launch Streamlit UI
        try:
            launch_streamlit()
        finally:
            # Terminate backend process when UI exits
            backend_process.terminate()
            backend_process.join()

if __name__ == "__main__":
    main()
