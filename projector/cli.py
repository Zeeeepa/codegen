#!/usr/bin/env python3
"""
Command-line interface for the Projector system.
This is a simplified version that just runs the Streamlit app.
"""
import os
import sys
import argparse
import subprocess

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Projector - Project Management System")
    parser.add_argument("--port", type=int, default=8501, help="Port for the Streamlit app")
    args = parser.parse_args()
    
    # Get the path to the streamlit_app.py file
    streamlit_app_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "frontend",
        "streamlit_app.py"
    )
    
    # Check if the file exists
    if not os.path.exists(streamlit_app_path):
        print(f"Error: Streamlit app file not found: {streamlit_app_path}")
        sys.exit(1)
    
    # Run the Streamlit app
    try:
        subprocess.run(
            ["streamlit", "run", streamlit_app_path, "--server.port", str(args.port)],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit app: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()