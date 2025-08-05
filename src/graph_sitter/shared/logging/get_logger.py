"""
Graph-Sitter Logger

Simple logging utility for graph-sitter.
"""

import logging
from typing import Optional

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance."""
    logger = logging.getLogger(name or __name__)
    
    if not logger.handlers:
        # Set up basic logging configuration
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger
