#!/usr/bin/env python3
"""
Launch script for the Codegen CI/CD Dashboard.

This script initializes and launches the dashboard application.
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from codegen_dashboard import CodegenDashboard
    from codegen_dashboard.utils.logger import setup_logger
except ImportError as e:
    print(f"Failed to import dashboard components: {e}")
    print("Make sure you're running this from the project root directory.")
    sys.exit(1)


def main():
    """Main entry point for the dashboard."""
    # Set up logging
    logger = setup_logger(__name__, level="INFO")
    logger.info("Starting Codegen CI/CD Dashboard")
    
    try:
        # Create the main Tkinter root window
        root = tk.Tk()
        
        # Initialize the dashboard
        dashboard = CodegenDashboard()
        
        # Set up window close handler
        def on_closing():
            """Handle window closing."""
            logger.info("Dashboard closing...")
            dashboard.cleanup()
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Start the main event loop
        logger.info("Dashboard started successfully")
        root.mainloop()
        
    except Exception as e:
        logger.error(f"Failed to start dashboard: {e}")
        
        # Show error dialog if possible
        try:
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            messagebox.showerror(
                "Dashboard Error",
                f"Failed to start the Codegen Dashboard:\n\n{str(e)}\n\n"
                "Please check the logs for more details."
            )
        except:
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()
