import os
import sys
import argparse
import logging
import subprocess
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("projector/app.log"),
        logging.StreamHandler()
    ]
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
    streamlit_app_path = "projector/streamlit_app.py"
    
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

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Projector - Project Management System")
    parser.add_argument("--port", type=int, default=8501, help="Port for the Streamlit app")
    args = parser.parse_args()
    
    try:
        # Start the Streamlit app
        process = start_streamlit(port=args.port)
        if process:
            # Wait for the process to complete
            process.wait()
    
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt. Shutting down...")
    except Exception as e:
        logging.error(f"Error in main function: {e}")
    finally:
        logging.info("Application shutdown complete.")

if __name__ == "__main__":
    main()
