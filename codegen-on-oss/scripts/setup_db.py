#!/usr/bin/env python
"""
Database Setup Script for Codegen-on-OSS

This script initializes the database schema and creates necessary tables.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from codegen_on_oss.database.manager import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Initialize the database schema and create tables."""
    logger.info("Setting up database...")
    
    # Get database URL from environment or use default
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///codegen_oss.db')
    
    # Create database manager
    db_manager = DatabaseManager(db_url=db_url)
    
    # Create tables
    db_manager.create_tables()
    
    logger.info("Database setup complete!")

if __name__ == "__main__":
    setup_database()

