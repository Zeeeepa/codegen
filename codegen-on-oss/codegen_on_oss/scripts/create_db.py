#!/usr/bin/env python3
"""
Script to create database tables for the application.

This script creates all the necessary database tables using SQLAlchemy.
"""

import logging

from pydantic_settings import SettingsConfigDict

from codegen_on_oss.outputs.sql_output import Base, SQLSettings, get_session_maker

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DotEnvSQLSettings(SQLSettings):
    """Settings class that loads from .env file."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="POSTGRESQL_",
        extra="ignore",
    )


def main():
    """Create database tables."""
    logger.info("Creating database tables...")
    
    settings = DotEnvSQLSettings()
    session_maker = get_session_maker(settings)
    
    with session_maker() as session:
        Base.metadata.create_all(bind=session.bind)
    
    logger.info("Database tables created successfully.")


if __name__ == "__main__":
    main()
