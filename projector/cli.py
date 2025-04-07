#!/usr/bin/env python3
"""
Command-line interface for the Projector application.
"""

import os
import sys
import argparse
import subprocess
import streamlit.web.bootstrap

def setup_python_path():
    """
    Set up the Python path to include the src directory for codegen modules.
    """
    # Add the src directory to the Python path for codegen modules
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src'))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

def run_streamlit():
    """
    Run the Streamlit application.
    """
    setup_python_path()
    streamlit_script = os.path.join(os.path.dirname(__file__), 'frontend/streamlit_app.py')
    args = []
    streamlit.web.bootstrap.run(streamlit_script, '', args, flag_options={})

def main():
    """
    Main entry point for the CLI.
    """
    parser = argparse.ArgumentParser(description='Projector - MultiThread Slack GitHub Tool')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    if args.debug:
        print("Debug mode enabled")
        os.environ['PROJECTOR_DEBUG'] = '1'
    
    # Set up the Python path
    setup_python_path()
    
    # Run the Streamlit application
    run_streamlit()

if __name__ == '__main__':
    main()