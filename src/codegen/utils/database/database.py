"""
Database implementation for Codegen.

This module provides database functionality for the Codegen application.
"""

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

from codegen.utils.logger import get_logger

# Logger for the database
logger = get_logger("codegen.database")


class Database:
    """
    SQLite database wrapper for Codegen.
    """

    def __init__(self, db_path: Union[str, Path]):
        """
        Initialize the database.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = Path(db_path)
        self._ensure_directory_exists()
        self.connection = None

    def _ensure_directory_exists(self) -> None:
        """
        Ensure the directory for the database file exists.
        """
        directory = self.db_path.parent
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """
        Context manager for database connections.

        Yields:
            A SQLite connection.
        """
        connection = sqlite3.connect(str(self.db_path))
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    def execute(
        self, query: str, params: Optional[Tuple[Any, ...]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return the results.

        Args:
            query: The SQL query to execute.
            params: Parameters for the query.

        Returns:
            A list of dictionaries representing the query results.
        """
        with self.connect() as conn:
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
                
                # If the query is a SELECT query, return the results
                if query.strip().upper().startswith("SELECT"):
                    return [dict(row) for row in cursor.fetchall()]
                return []
            except sqlite3.Error as e:
                logger.error(f"Database error: {e}")
                conn.rollback()
                raise

    def execute_script(self, script: str) -> None:
        """
        Execute a SQL script.

        Args:
            script: The SQL script to execute.
        """
        with self.connect() as conn:
            try:
                conn.executescript(script)
                conn.commit()
            except sqlite3.Error as e:
                logger.error(f"Database error: {e}")
                conn.rollback()
                raise

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name: The name of the table to check.

        Returns:
            True if the table exists, False otherwise.
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.execute(query, (table_name,))
        return len(result) > 0

    def create_table(self, table_name: str, columns: Dict[str, str]) -> None:
        """
        Create a table in the database.

        Args:
            table_name: The name of the table to create.
            columns: A dictionary mapping column names to their SQL types.
        """
        if self.table_exists(table_name):
            logger.info(f"Table {table_name} already exists")
            return

        column_defs = ", ".join(f"{name} {type_}" for name, type_ in columns.items())
        query = f"CREATE TABLE {table_name} ({column_defs})"
        self.execute(query)
        logger.info(f"Created table {table_name}")

    def insert(self, table_name: str, data: Dict[str, Any]) -> None:
        """
        Insert data into a table.

        Args:
            table_name: The name of the table to insert into.
            data: A dictionary mapping column names to values.
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        self.execute(query, tuple(data.values()))

    def update(
        self, table_name: str, data: Dict[str, Any], condition: str, params: Tuple[Any, ...]
    ) -> None:
        """
        Update data in a table.

        Args:
            table_name: The name of the table to update.
            data: A dictionary mapping column names to new values.
            condition: The WHERE condition for the update.
            params: Parameters for the condition.
        """
        set_clause = ", ".join(f"{key} = ?" for key in data.keys())
        query = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"
        self.execute(query, tuple(data.values()) + params)

    def delete(self, table_name: str, condition: str, params: Tuple[Any, ...]) -> None:
        """
        Delete data from a table.

        Args:
            table_name: The name of the table to delete from.
            condition: The WHERE condition for the delete.
            params: Parameters for the condition.
        """
        query = f"DELETE FROM {table_name} WHERE {condition}"
        self.execute(query, params)

    def select(
        self, table_name: str, columns: List[str] = None, condition: str = None, params: Tuple[Any, ...] = None
    ) -> List[Dict[str, Any]]:
        """
        Select data from a table.

        Args:
            table_name: The name of the table to select from.
            columns: The columns to select (default: all columns).
            condition: The WHERE condition for the select (default: no condition).
            params: Parameters for the condition (default: no parameters).

        Returns:
            A list of dictionaries representing the selected rows.
        """
        columns_str = "*" if not columns else ", ".join(columns)
        query = f"SELECT {columns_str} FROM {table_name}"
        if condition:
            query += f" WHERE {condition}"
        return self.execute(query, params)


class DatabaseManager:
    """
    Manager for multiple databases.
    """

    def __init__(self, base_dir: Union[str, Path] = None):
        """
        Initialize the database manager.

        Args:
            base_dir: Base directory for database files (default: ~/.codegen/db).
        """
        if base_dir is None:
            base_dir = os.path.expanduser("~/.codegen/db")
        self.base_dir = Path(base_dir)
        self.databases: Dict[str, Database] = {}

    def get_database(self, name: str) -> Database:
        """
        Get a database by name.

        Args:
            name: The name of the database.

        Returns:
            The database instance.
        """
        if name not in self.databases:
            db_path = self.base_dir / f"{name}.db"
            self.databases[name] = Database(db_path)
        return self.databases[name]

    def close_all(self) -> None:
        """
        Close all database connections.
        """
        self.databases.clear()


# Global database manager instance
_db_manager = DatabaseManager()


def get_database_manager() -> DatabaseManager:
    """
    Get the global database manager instance.

    Returns:
        The global database manager instance.
    """
    return _db_manager
