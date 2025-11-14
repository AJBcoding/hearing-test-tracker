"""Database utilities for SQLite operations."""
import sqlite3
import uuid
from pathlib import Path
from typing import Optional


def generate_uuid() -> str:
    """Generate a UUID string for primary keys."""
    return str(uuid.uuid4())


def init_database(db_path: Path) -> None:
    """
    Initialize database with schema.

    Args:
        db_path: Path to SQLite database file
    """
    schema_path = Path(__file__).parent / "schema.sql"

    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.executescript(schema_sql)
    conn.commit()
    conn.close()


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Get database connection with row factory.

    Args:
        db_path: Path to database file, defaults to config.DB_PATH

    Returns:
        SQLite connection with row factory enabled
    """
    if db_path is None:
        from backend.config import DB_PATH
        db_path = DB_PATH

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
