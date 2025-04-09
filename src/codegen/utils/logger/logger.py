"""
Logger implementation for Codegen.

This module provides a standardized logging setup for the Codegen application.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Dict, Optional

# Default log format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Global dictionary to store loggers
_loggers: Dict[str, logging.Logger] = {}


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_format: str = DEFAULT_LOG_FORMAT,
    log_file: Optional[str] = None,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    propagate: bool = False,
) -> logging.Logger:
    """
    Set up a logger with the specified configuration.

    Args:
        name: The name of the logger.
        level: The logging level (default: INFO).
        log_format: The log format string (default: DEFAULT_LOG_FORMAT).
        log_file: The path to the log file (default: None, logs to console only).
        max_bytes: Maximum size of log file before rotation (default: 10MB).
        backup_count: Number of backup log files to keep (default: 5).
        propagate: Whether to propagate logs to parent loggers (default: False).

    Returns:
        The configured logger.
    """
    # Check if logger already exists
    if name in _loggers:
        return _loggers[name]

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = propagate

    # Remove existing handlers if any
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create file handler if log_file is specified
    if log_file:
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # Create rotating file handler
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Store logger in global dictionary
    _loggers[name] = logger

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger by name. If the logger doesn't exist, create it with default settings.

    Args:
        name: The name of the logger.

    Returns:
        The requested logger.
    """
    if name not in _loggers:
        return setup_logger(name)
    return _loggers[name]
