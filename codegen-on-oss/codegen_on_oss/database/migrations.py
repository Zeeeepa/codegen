"""
Database migrations for Codegen-on-OSS

This module provides utilities for database migrations.
"""

import logging
from pathlib import Path
from typing import Optional

import alembic.config
import alembic.command
from alembic.config import Config

from codegen_on_oss.database.session import engine, Base

logger = logging.getLogger(__name__)


def create_alembic_config(alembic_ini_path: Optional[str] = None) -> Config:
    """
    Create an Alembic configuration object.
    
    Args:
        alembic_ini_path: Path to the alembic.ini file.
        
    Returns:
        An Alembic configuration object.
    """
    if alembic_ini_path is None:
        # Use default path relative to this file
        alembic_ini_path = str(Path(__file__).parent.parent.parent / "alembic.ini")
    
    config = Config(alembic_ini_path)
    config.set_main_option("script_location", str(Path(__file__).parent.parent.parent / "alembic"))
    config.set_main_option("sqlalchemy.url", str(engine.url))
    
    return config


def create_initial_migration() -> None:
    """Create the initial migration."""
    config = create_alembic_config()
    alembic.command.revision(
        config,
        message="Initial migration",
        autogenerate=True,
    )


def upgrade_database(revision: str = "head") -> None:
    """
    Upgrade the database to the specified revision.
    
    Args:
        revision: The revision to upgrade to.
    """
    config = create_alembic_config()
    alembic.command.upgrade(config, revision)


def downgrade_database(revision: str) -> None:
    """
    Downgrade the database to the specified revision.
    
    Args:
        revision: The revision to downgrade to.
    """
    config = create_alembic_config()
    alembic.command.downgrade(config, revision)


def init_database() -> None:
    """Initialize the database."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create initial migration
    try:
        create_initial_migration()
        logger.info("Created initial migration")
    except Exception as e:
        logger.error(f"Error creating initial migration: {e}")


if __name__ == "__main__":
    # Initialize the database when this module is run directly
    init_database()

