#!/usr/bin/env python3
"""
Script to create the database for codegen-on-oss.

This script creates the database tables for codegen-on-oss.
"""

import os
import sys

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from codegen_on_oss.database.connection import get_engine
from codegen_on_oss.database.models import Base


def create_db():
    """Create the database tables."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    create_db()
