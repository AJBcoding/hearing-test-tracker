"""Tests for database utilities."""
import sqlite3
from pathlib import Path
import pytest
from backend.database.db_utils import init_database, get_connection


def test_init_database_creates_tables(tmp_path):
    """Test that init_database creates required tables."""
    db_path = tmp_path / "test.db"
    init_database(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check hearing_test table exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='hearing_test'
    """)
    assert cursor.fetchone() is not None

    # Check audiogram_measurement table exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='audiogram_measurement'
    """)
    assert cursor.fetchone() is not None

    conn.close()


def test_get_connection_returns_valid_connection(tmp_path):
    """Test that get_connection returns a working connection."""
    db_path = tmp_path / "test.db"
    init_database(db_path)

    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()

    assert result[0] == 1
    conn.close()
