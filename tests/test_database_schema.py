import sqlite3
from pathlib import Path

from core.database_manager import DatabaseManager


def test_database_manager_creates_expected_tables(tmp_path):
    """DatabaseManager should create lessons and folders tables on first use."""
    db_path = tmp_path / "test_lessons.db"
    db = DatabaseManager(str(db_path))

    try:
        conn = db.conn
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}

        # Core tables that must exist for the app to function
        assert "lessons" in tables
        assert "folders" in tables
    finally:
        db.close()
        if Path(db_path).exists():
            db_path.unlink()
