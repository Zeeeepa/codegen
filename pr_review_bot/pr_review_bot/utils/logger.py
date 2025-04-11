"""
Logger utility for the PR Review Bot.
"""

import os
import sys
import logging
from typing import Optional

def setup_logging(log_file: Optional[str] = None, log_level: int = logging.INFO):
    """
    Set up logging for the PR Review Bot.
    
    Args:
        log_file: Path to the log file
        log_level: Logging level
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
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
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Set log level for specific loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("github").setLevel(logging.WARNING)
    logging.getLogger("pyngrok").setLevel(logging.WARNING)
    
    return logger

def get_logger(name: str, log_level: int = logging.INFO):
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
        log_level: Logging level
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    return logger
