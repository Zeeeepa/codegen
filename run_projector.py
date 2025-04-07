#!/usr/bin/env python3
"""
Wrapper script to run the projector streamlit app with the correct Python path.
This script adds the src directory to the Python path so that the codegen.agents
module can be imported correctly.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """
    Main function to run the projector application.
    """
    # Get the absolute path to the repository root
    repo_root = Path(__file__).parent.absolute()
    
    # Add the repository root to the Python path
    sys.path.insert(0, str(repo_root))
    
    # Add the src directory to the Python path
    src_dir = repo_root / "src"
    sys.path.insert(0, str(src_dir))
    
    # Set environment variables for the subprocess
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{str(src_dir)}:{env.get('PYTHONPATH', '')}"
    
    # Run the streamlit app
    streamlit_app_path = repo_root / "projector" / "frontend" / "streamlit_app.py"
    
    try:
        # Try to run using streamlit command
        subprocess.run(["streamlit", "run", str(streamlit_app_path)], env=env, check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        # If streamlit command fails, import and run the module directly
        print("Streamlit command failed, running module directly...")
        
        # Import the streamlit app module
        import projector.frontend.streamlit_app
        
        # Run the main function
        projector.frontend.streamlit_app.main()

if __name__ == "__main__":
    main()
