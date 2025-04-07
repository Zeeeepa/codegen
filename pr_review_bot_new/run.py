#!/usr/bin/env python3
"""
Run script for the PR Review Bot.
This script adds the current directory to the Python path and runs the bot.
"""

import os
import sys

def main():
    """Main entry point for the run script."""
    # Add the parent directory to the Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)
    
    # Import the main module from the package
    from pr_review_bot_new.main import main as bot_main
    
    # Run the bot with the command line arguments
    bot_main()

if __name__ == "__main__":
    main()