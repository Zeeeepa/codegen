#!/usr/bin/env python3
"""
Wrapper script to run the projector streamlit app with the correct Python path.
This script adds the src directory to the Python path so that the codegen.agents
module can be imported correctly.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir.absolute()))

# Run the streamlit app
if __name__ == "__main__":
    # Import and run the streamlit app module
    import projector.frontend.streamlit_app
    projector.frontend.streamlit_app.main()
