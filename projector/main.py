import os
import sys
import argparse
import subprocess
import logging
import multiprocessing
from dotenv import load_dotenv

# Add the project root to the Python path
# This ensures that the 'projector' module can be imported
project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

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
    
    parser.add_argument(
        "--max_concurrent_projects",
        type=int,
        default=3,
        help="Maximum number of concurrent projects to implement (1-5)"
    )
    
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Setup configuration files (.env and .streamlit/secrets.toml)"
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
        # Check if the streamlit_app.py file exists
        streamlit_app_path = "projector/frontend/streamlit_app.py"
        if not os.path.exists(streamlit_app_path):
            logging.error(f"Streamlit app file not found: {streamlit_app_path}")
            sys.exit(1)
            
        subprocess.run(["streamlit", "run", streamlit_app_path])
    except Exception as e:
        logging.error(f"Error launching Streamlit: {e}")
        sys.exit(1)

def setup_config_files():
    """Set up configuration files from examples if they don't exist."""
    logger = logging.getLogger("setup")
    
    # Setup .env file
    env_example_path = ".env.example"
    env_path = ".env"
    
    if not os.path.exists(env_path) and os.path.exists(env_example_path):
        logger.info("Creating .env file from example...")
        with open(env_example_path, 'r') as example_file:
            example_content = example_file.read()
        
        with open(env_path, 'w') as env_file:
            env_file.write(example_content)
        
        logger.info(f".env file created at {os.path.abspath(env_path)}")
        logger.info("Please edit this file with your actual configuration values.")
    
    # Setup Streamlit secrets
    streamlit_dir = ".streamlit"
    secrets_path = os.path.join(streamlit_dir, "secrets.toml")
    
    if not os.path.exists(streamlit_dir):
        os.makedirs(streamlit_dir)
        logger.info(f"Created directory: {streamlit_dir}")
    
    if not os.path.exists(secrets_path):
        logger.info("Creating Streamlit secrets.toml file...")
        
        # Convert .env format to TOML format
        if os.path.exists(env_path):
            with open(env_path, 'r') as env_file:
                env_content = env_file.readlines()
            
            toml_content = []
            for line in env_content:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    toml_content.append(f'{key} = "{value}"')
            
            with open(secrets_path, 'w') as secrets_file:
                secrets_file.write("\n".join(toml_content))
            
            logger.info(f"Streamlit secrets.toml file created at {os.path.abspath(secrets_path)}")
        else:
            logger.warning("No .env file found to create secrets.toml from.")
    
    logger.info("Configuration setup complete. Please edit the files with your actual values.")
    logger.info("Then run the application again without the --setup flag.")

def run_backend(args):
    """Run the backend service."""
    # Load environment variables
    load_dotenv()
    
    try:
        # Import backend components
        from projector.backend.config import (
            SLACK_USER_TOKEN, GITHUB_TOKEN, GITHUB_USERNAME,
            SLACK_DEFAULT_CHANNEL, GITHUB_DEFAULT_REPO
        )
        from projector.backend.slack_manager import SlackManager
        from projector.backend.github_manager import GitHubManager
        from projector.backend.assistant_agent import AssistantAgent
        from projector.backend.project_database import ProjectDatabase
        from projector.backend.project_manager import ProjectManager
        from projector.backend.thread_pool import ThreadPool
        from projector.backend.utils import validate_config
        
        logger = setup_logging(debug=args.debug)
        
        # Validate configuration
        if not validate_config():
            logger.error("Invalid configuration. Please check your .env file or .streamlit/secrets.toml file.")
            logger.info("You can run 'python main.py --setup' to create template configuration files.")
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
    except ImportError as e:
        logger = setup_logging(debug=args.debug)
        logger.error(f"Error importing required modules: {e}")
        logger.info("This may be due to missing configuration. Run 'python main.py --setup' to create configuration files.")
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
    
    # Handle setup flag
    if args.setup:
        logger.info("Setting up configuration files...")
        setup_config_files()
        return
    
    # Ensure args.threads is within valid range
    args.threads = max(1, min(10, args.threads))
    
    # Ensure max_concurrent_projects is within valid range
    args.max_concurrent_projects = max(1, min(5, args.max_concurrent_projects))
    
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
