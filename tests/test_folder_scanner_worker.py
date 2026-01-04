from pathlib import Path

from ui.searchUpdateDatabase import FolderScannerWorker, FolderScannerWindow
from core.database import connect_to_db
from PyQt5.QtWidgets import QApplication


def test_folder_scanner_worker_handles_empty_folder(tmp_path):
    """Running the worker on an empty folder should not crash and
    should not insert any lessons."""
    db_path = tmp_path / "test_lessons.db"
    empty_folder = tmp_path / "empty"
    empty_folder.mkdir()

    worker = FolderScannerWorker(str(db_path), str(empty_folder))
    worker.run()  # should not raise

    conn = connect_to_db(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM lessons")
        (count,) = cur.fetchone()
        assert count == 0
    finally:
        conn.close()


def test_folder_scanner_worker_ignores_downloads_folder(tmp_path):
    """Files under any Downloads directory should be ignored."""
    db_path = tmp_path / "test_lessons.db"

    # Root with nested Downloads containing media
    root = tmp_path / "root"
    downloads = root / "Downloads" / "001_Test"
    downloads.mkdir(parents=True)
    media_file = downloads / "example.mp3"
    media_file.write_bytes(b"fake-audio")

    worker = FolderScannerWorker(str(db_path), str(root))
    worker.run()

    conn = connect_to_db(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM lessons")
        (count,) = cur.fetchone()
        assert count == 0
    finally:
        conn.close()


def test_folder_scanner_window_uses_default_scan_folder_for_dialog(monkeypatch, tmp_path):
    """Folder selection should start at the configured default scan folder when available."""
    app = QApplication.instance() or QApplication([])

    captured = {}

    class FakeSettings:
        def __init__(self):
            self.store = {"default_scan_folder": str(tmp_path / "start_here")}

        def value(self, key, default=None):
            return self.store.get(key, default)

    def fake_qsettings(*args, **kwargs):
        return FakeSettings()

    monkeypatch.setattr("ui.searchUpdateDatabase.QSettings", fake_qsettings)

    def fake_get_existing_directory(parent, title, start_dir=""):
        captured["start_dir"] = start_dir
        return ""  # simulate cancel

    monkeypatch.setattr("ui.searchUpdateDatabase.QFileDialog.getExistingDirectory", fake_get_existing_directory)

    window = FolderScannerWindow(str(tmp_path / "db.sqlite"))
    window.select_folder()

    assert captured.get("start_dir") == str(tmp_path / "start_here")
