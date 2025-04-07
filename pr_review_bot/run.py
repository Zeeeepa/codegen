#!/usr/bin/env python3
"""
Run script for the PR Review Bot.
This script adds the current directory to the Python path and runs the bot.
"""

import os
import sys
import argparse

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    """Main entry point for the run script."""
    # Import the main module
    from pr_review_bot.main import main as bot_main
    
    # Run the bot with the command line arguments
    # This will let main.py handle the argument parsing
    sys.exit(bot_main())

if __name__ == "__main__":
    main()
