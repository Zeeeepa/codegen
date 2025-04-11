"""
Logger module for the PR Review Bot.
Provides consistent logging functionality across the application.
"""

import os
import logging
import sys
from typing import Optional

def setup_logging(log_file: Optional[str] = None, log_level: int = logging.INFO) -> None:
    """
    Set up logging for the application.
    
    Args:
        log_file: Path to log file (optional)
        log_level: Logging level (default: INFO)
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log file is specified
    if log_file:
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Log setup
    logger.info(f"Logging initialized with level {logging.getLevelName(log_level)}")
    if log_file:
        logger.info(f"Logging to file: {log_file}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
