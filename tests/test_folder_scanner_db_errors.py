import sqlite3

from ui.searchUpdateDatabase import FolderScannerWorker, FolderScannerWindow


def test_folder_scanner_handles_insert_lesson_exception(monkeypatch, tmp_path):
    """If insert_lesson raises a DB error, the worker should emit an
    error status and finish without crashing."""
    db_path = tmp_path / "test_lessons.db"
    lesson_folder = tmp_path / "001_Lesson"
    lesson_folder.mkdir()
    media_file = lesson_folder / "file.mp3"
    media_file.write_bytes(b"fake")

    import ui.searchUpdateDatabase as mod

    def fake_insert_lesson(conn, *args, **kwargs):
        raise sqlite3.DatabaseError("test failure")

    statuses = []

    monkeypatch.setattr(mod, "insert_lesson", fake_insert_lesson)

    worker = mod.FolderScannerWorker(str(db_path), str(tmp_path))
    worker.status.connect(statuses.append)

    worker.run()  # Should not raise

    assert any("Error:" in s for s in statuses)


def test_folder_scanner_uses_fallback_for_malformed_folder(monkeypatch, tmp_path):
    """Folders without a numeric prefix should use get_or_assign_lesson_number
    and a sanitized lesson_name."""
    db_path = tmp_path / "test_lessons.db"
    lesson_folder = tmp_path / "MalformedFolderName"
    lesson_folder.mkdir()
    media_file = lesson_folder / "file.mp3"
    media_file.write_bytes(b"fake")

    import ui.searchUpdateDatabase as mod

    calls = {"get_or_assign": [], "insert": []}

    def fake_get_or_assign(conn, folder_name):
        calls["get_or_assign"].append(folder_name)
        return 42

    def fake_insert_lesson(conn, lesson_number, lesson_name, file_name, file_path, duration, bitrate):
        calls["insert"].append(
            (lesson_number, lesson_name, file_name, file_path, duration, bitrate)
        )

    monkeypatch.setattr(mod, "get_or_assign_lesson_number", fake_get_or_assign)
    monkeypatch.setattr(mod, "insert_lesson", fake_insert_lesson)

    worker = mod.FolderScannerWorker(str(db_path), str(tmp_path))
    worker.run()

    assert calls["get_or_assign"] == ["MalformedFolderName"]

    assert len(calls["insert"]) == 1
    lesson_number, lesson_name, file_name, file_path, duration, bitrate = calls["insert"][0]
    assert lesson_number == 42
    assert lesson_name == "MalformedFolderName"
    assert file_name == media_file.name
    assert file_path.endswith(str(media_file))


def test_insert_folder_db_error_shows_warning(monkeypatch):
    """FolderScannerWindow._insert_folder should show a Database Error
    warning if insert_folder raises."""
    import ui.searchUpdateDatabase as mod

    warnings = []

    def fake_warning(parent, title, text):
        warnings.append((title, text))

    def fake_insert_folder(conn, folder):
        raise sqlite3.DatabaseError("boom")

    monkeypatch.setattr(mod.QMessageBox, "warning", fake_warning)
    monkeypatch.setattr(mod, "insert_folder", fake_insert_folder)

    # Minimal stub with required attributes
    class StubSelf:
        def __init__(self):
            self.conn = None
            self.folder_list = type("L", (), {"count": lambda self: 0, "item": lambda self, i: None, "addItem": lambda self, f: None})()

    stub = StubSelf()

    mod.FolderScannerWindow._insert_folder(stub, "/some/folder")

    assert warnings
    title, text = warnings[0]
    assert title == "Database Error"
    assert "Failed to add folder" in text

