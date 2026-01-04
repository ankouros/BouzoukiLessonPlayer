import sqlite3

import pytest

from core.database_manager import DatabaseManager
from core.database import connect_to_db


def test_database_manager_raises_on_corrupted_db(tmp_path):
    """A physically corrupted SQLite file should cause DatabaseManager
    to raise a DatabaseError, which higher-level code (e.g. main.main)
    can then handle gracefully."""
    db_path = tmp_path / "lessons.db"
    # Write non-SQLite garbage to the file
    db_path.write_bytes(b"not a sqlite database")

    with pytest.raises(sqlite3.DatabaseError):
        DatabaseManager(str(db_path))


def test_connect_to_db_raises_on_corrupted_db(tmp_path):
    """connect_to_db should also surface errors for corrupted files so
    callers can handle them."""
    db_path = tmp_path / "lessons.db"
    db_path.write_bytes(b"corrupt content")

    with pytest.raises(sqlite3.DatabaseError):
        connect_to_db(str(db_path))

