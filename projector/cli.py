#!/usr/bin/env python3
import argparse
import os
import sys
import subprocess

def main():
    """CLI entry point for Projector."""
    parser = argparse.ArgumentParser(description="Projector - Project Management System")
    parser.add_argument("--port", type=int, default=8501, help="Port for the Streamlit app")
    args = parser.parse_args()
    
    # Run the main application
    from projector.main import main as run_app
    run_app()

if __name__ == "__main__":
    main()