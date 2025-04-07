import os
import sys
import argparse
import logging
import threading
import time
import subprocess
import signal
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Global flag to control the main loop
running = True

def signal_handler(sig, frame):
    """Handle termination signals."""
    global running
    logging.info("Received termination signal. Shutting down...")
    running = False

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def start_streamlit(port=8501):
    """Start the Streamlit app."""
    streamlit_app_path = "projector/frontend/streamlit_app.py"
    
    # Check if the Streamlit app file exists
    if not os.path.exists(streamlit_app_path):
        logging.error(f"Streamlit app file not found: {streamlit_app_path}")
        return None
    
    # Start Streamlit process
    try:
        process = subprocess.Popen(
            ["streamlit", "run", streamlit_app_path, "--server.port", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logging.info(f"Started Streamlit app on port {port}")
        return process
    except Exception as e:
        logging.error(f"Failed to start Streamlit app: {e}")
        return None

def monitor_streamlit(process):
    """Monitor the Streamlit process and restart if needed."""
    while running:
        # Check if the process is still running
        if process.poll() is not None:
            logging.warning("Streamlit process has terminated. Restarting...")
            process = start_streamlit()
            if process is None:
                logging.error("Failed to restart Streamlit. Exiting monitor.")
                break
        
        # Sleep for a while before checking again
        time.sleep(5)

def run_backend_service():
    """Run the backend service."""
    global running
    
    logging.info("Starting backend service...")
    
    # Import backend components
    from projector.backend.config import (
        SLACK_USER_TOKEN, GITHUB_TOKEN, GITHUB_USERNAME,
        SLACK_DEFAULT_CHANNEL, GITHUB_DEFAULT_REPO
    )
    from projector.backend.slack_manager import SlackManager
    from projector.backend.github_manager import GitHubManager
    from projector.backend.assistant_agent import AssistantAgent
    from projector.backend.ai_user_agent import AIUserAgent
    from projector.backend.project_database import ProjectDatabase
    from projector.backend.project_manager import ProjectManager
    from projector.backend.thread_pool import ThreadPool
    from projector.backend.merge_manager import MergeManager
    from projector.backend.utils import validate_config
    
    # Validate configuration
    if not validate_config():
        logging.error("Invalid configuration. Please check your environment variables.")
        return
    
    # Initialize components
    try:
        # Initialize GitHub manager
        github_manager = GitHubManager(
            github_token=GITHUB_TOKEN,
            github_username=GITHUB_USERNAME,
            default_repo=GITHUB_DEFAULT_REPO
        )
        
        # Initialize Slack manager
        slack_manager = SlackManager(
            slack_token=SLACK_USER_TOKEN,
            default_channel=SLACK_DEFAULT_CHANNEL
        )
        
        # Initialize thread pool
        thread_pool = ThreadPool(max_threads=10)
        
        # Initialize project database
        project_database = ProjectDatabase()
        
        # Initialize project manager
        project_manager = ProjectManager(
            github_manager=github_manager,
            slack_manager=slack_manager,
            thread_pool=thread_pool
        )
        
        # Initialize merge manager
        merge_manager = MergeManager(
            github_manager=github_manager,
            project_manager=project_manager
        )
        
        # Initialize AI User Agent
        ai_user_agent = AIUserAgent(
            slack_manager=slack_manager,
            github_manager=github_manager,
            project_database=project_database,
            project_manager=project_manager,
            thread_pool=thread_pool,
            docs_path="docs"
        )
        
        # Initialize assistant agent
        assistant_agent = AssistantAgent(
            github_manager=github_manager,
            slack_manager=slack_manager,
            docs_path="docs",
            project_database=project_database,
            project_manager=project_manager
        )
        
        logging.info("Backend components initialized successfully.")
        
        # Main service loop
        while running:
            # Process any pending tasks
            thread_pool.process_pending_tasks()
            
            # Sleep for a while before the next iteration
            time.sleep(1)
        
        # Cleanup
        thread_pool.shutdown()
        logging.info("Backend service stopped.")
        
    except Exception as e:
        logging.error(f"Error in backend service: {e}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MultiThread Slack GitHub Tool")
    parser.add_argument("--port", type=int, default=8501, help="Port for the Streamlit app")
    parser.add_argument("--backend-only", action="store_true", help="Run only the backend service")
    parser.add_argument("--frontend-only", action="store_true", help="Run only the frontend (Streamlit)")
    args = parser.parse_args()
    
    try:
        # Start components based on arguments
        if args.backend_only:
            # Run only the backend service
            run_backend_service()
        elif args.frontend_only:
            # Run only the Streamlit app
            process = start_streamlit(port=args.port)
            if process:
                # Wait for the process to complete
                process.wait()
        else:
            # Run both backend and frontend
            # Start Streamlit in a separate process
            streamlit_process = start_streamlit(port=args.port)
            if streamlit_process:
                # Start a thread to monitor the Streamlit process
                monitor_thread = threading.Thread(target=monitor_streamlit, args=(streamlit_process,))
                monitor_thread.daemon = True
                monitor_thread.start()
                
                # Run the backend service in the main thread
                run_backend_service()
                
                # Cleanup
                if streamlit_process.poll() is None:
                    logging.info("Terminating Streamlit process...")
                    streamlit_process.terminate()
                    streamlit_process.wait(timeout=5)
    
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt. Shutting down...")
    except Exception as e:
        logging.error(f"Error in main function: {e}")
    finally:
        logging.info("Application shutdown complete.")

if __name__ == "__main__":
    main()
