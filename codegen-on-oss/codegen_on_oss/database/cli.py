"""
Command-line interface for database operations.

This module provides a CLI for managing the database.
"""

import os
import sys
import logging
import argparse
from typing import Optional

from codegen_on_oss.database.connection import initialize_db, get_db_manager

logger = logging.getLogger(__name__)

def init_db(db_url: Optional[str] = None, drop_existing: bool = False) -> None:
    """
    Initialize the database.
    
    Args:
        db_url: Database connection URL. If None, uses the CODEGEN_DB_URL environment variable.
        drop_existing: If True, drop existing tables before creating new ones.
    """
    db_manager = initialize_db(db_url)
    
    if drop_existing:
        logger.info("Dropping existing tables...")
        db_manager.drop_tables()
    
    logger.info("Creating database tables...")
    db_manager.create_tables()
    logger.info("Database initialized successfully")

def main() -> None:
    """Run the CLI."""
    parser = argparse.ArgumentParser(description='Manage the codegen-on-oss database')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # init command
    init_parser = subparsers.add_parser('init', help='Initialize the database')
    init_parser.add_argument('--db-url', help='Database connection URL')
    init_parser.add_argument('--drop-existing', action='store_true', help='Drop existing tables')
    
    # check command
    check_parser = subparsers.add_parser('check', help='Check database connection')
    check_parser.add_argument('--db-url', help='Database connection URL')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if args.command == 'init':
        init_db(args.db_url, args.drop_existing)
    elif args.command == 'check':
        db_manager = initialize_db(args.db_url)
        if db_manager.health_check():
            logger.info("Database connection is healthy")
            sys.exit(0)
        else:
            logger.error("Database connection is not healthy")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()

