#!/usr/bin/env python3
"""
Run script for the PR Review Bot.
This script adds the current directory to the Python path and runs the bot.
"""

import os
import sys

def main():
    """Main entry point for the run script."""
    # Import the main module
    from pr_review_bot.main import main as bot_main
    
    # Run the bot with the command line arguments
    # Pass all command-line arguments directly to main.py
    bot_main()

if __name__ == "__main__":
    main()