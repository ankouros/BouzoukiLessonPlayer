from pathlib import Path

from core.database_manager import DatabaseManager


def _get_all_lessons(conn):
    cur = conn.cursor()
    cur.execute("SELECT lesson_number, lesson_name, file_name, file_path FROM lessons")
    return cur.fetchall()


def test_update_file_entry_updates_name_and_path(tmp_path):
    db_path = tmp_path / "test_lessons.db"
    db = DatabaseManager(str(db_path))
    try:
        lesson_data = (1, "Test Lesson", "old.mp4", "/tmp/old.mp4", 10.0, 128000)
        db.insert_lesson(lesson_data)

        db.update_file_entry("/tmp/old.mp4", "new.mp4", "/tmp/new.mp4")

        rows = _get_all_lessons(db.conn)
        assert len(rows) == 1
        row = rows[0]
        assert row[2] == "new.mp4"
        assert row[3] == "/tmp/new.mp4"
    finally:
        db.close()
        if Path(db_path).exists():
            db_path.unlink()


def test_delete_file_entry_removes_row(tmp_path):
    db_path = tmp_path / "test_lessons.db"
    db = DatabaseManager(str(db_path))
    try:
        lesson_data = (1, "Test Lesson", "to_delete.mp4", "/tmp/to_delete.mp4", 10.0, 128000)
        db.insert_lesson(lesson_data)

        db.delete_file_entry("/tmp/to_delete.mp4")

        rows = _get_all_lessons(db.conn)
        assert rows == []
    finally:
        db.close()
        if Path(db_path).exists():
            db_path.unlink()


def test_update_file_entry_only_affects_matching_path_with_duplicate_names(tmp_path):
    """If two lessons share the same file_name but different paths, updating
    one path should not affect the other row."""
    db_path = tmp_path / "test_lessons.db"
    db = DatabaseManager(str(db_path))
    try:
        db.insert_lesson((1, "Lesson A", "same.mp4", "/tmp/a/same.mp4", 10.0, 128000))
        db.insert_lesson((2, "Lesson B", "same.mp4", "/tmp/b/same.mp4", 20.0, 192000))

        db.update_file_entry("/tmp/a/same.mp4", "renamed.mp4", "/tmp/a/renamed.mp4")

        rows = sorted(_get_all_lessons(db.conn), key=lambda r: r[0])
        assert rows[0][2:] == ("renamed.mp4", "/tmp/a/renamed.mp4")
        assert rows[1][2:] == ("same.mp4", "/tmp/b/same.mp4")
    finally:
        db.close()
        if Path(db_path).exists():
            db_path.unlink()


def test_delete_file_entry_only_removes_matching_path_with_duplicate_names(tmp_path):
    db_path = tmp_path / "test_lessons.db"
    db = DatabaseManager(str(db_path))
    try:
        db.insert_lesson((1, "Lesson A", "same.mp4", "/tmp/a/same.mp4", 10.0, 128000))
        db.insert_lesson((2, "Lesson B", "same.mp4", "/tmp/b/same.mp4", 20.0, 192000))

        db.delete_file_entry("/tmp/a/same.mp4")

        rows = _get_all_lessons(db.conn)
        assert len(rows) == 1
        row = rows[0]
        assert row[0] == 2
        assert row[2] == "same.mp4"
        assert row[3] == "/tmp/b/same.mp4"
    finally:
        db.close()
        if Path(db_path).exists():
            db_path.unlink()

