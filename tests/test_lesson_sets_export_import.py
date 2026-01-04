from pathlib import Path

from core.database_manager import DatabaseManager
from core.lesson_sets import export_all_lessons, import_lessons


def _all_lessons(conn):
    cur = conn.cursor()
    cur.execute(
        "SELECT lesson_number, lesson_name, file_name, file_path, tempo, tags FROM lessons ORDER BY lesson_number, file_name"
    )
    return [tuple(row) for row in cur.fetchall()]


def _all_presets(conn):
    cur = conn.cursor()
    cur.execute(
        "SELECT file_path, tempo, transpose_steps, loop_start_ms, loop_end_ms, metronome_groove FROM practice_presets ORDER BY file_path"
    )
    return [tuple(row) for row in cur.fetchall()]


def test_export_and_import_all_lessons_roundtrip(tmp_path):
    # Source DB
    src_db_path = tmp_path / "src.db"
    src_db = DatabaseManager(str(src_db_path))
    try:
        # Seed a couple of lessons and a practice preset
        src_db.insert_lesson(
            (1, "Lesson One", "one.mp3", "/media/one.mp3", 10.0, 128000, 110, "4/4")
        )
        src_db.insert_lesson(
            (2, "Lesson Two", "two.mp3", "/media/two.mp3", 12.0, 192000, None, None)
        )
        src_db.save_practice_preset(
            file_path="/media/one.mp3",
            tempo=110,
            transpose_steps=2,
            loop_start_ms=1000,
            loop_end_ms=3000,
            groove="4/4",
        )

        export_path = tmp_path / "lessons_export.json"
        export_all_lessons(src_db, str(export_path))
    finally:
        src_db.close()

    # Target DB
    dest_db_path = tmp_path / "dest.db"
    dest_db = DatabaseManager(str(dest_db_path))
    try:
        import_lessons(dest_db, str(export_path))

        lessons = _all_lessons(dest_db.conn)
        presets = _all_presets(dest_db.conn)

        assert len(lessons) == 2
        assert lessons[0][0:3] == (1, "Lesson One", "one.mp3")
        assert lessons[1][0:3] == (2, "Lesson Two", "two.mp3")

        assert len(presets) == 1
        preset = presets[0]
        assert preset[0] == "/media/one.mp3"
        assert preset[1] == 110
        assert preset[2] == 2
        assert preset[5] == "4/4"
    finally:
        dest_db.close()

