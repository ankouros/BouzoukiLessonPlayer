from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox

from core.database_manager import DatabaseManager
import ui.widgets.detail as detail_mod


def _ensure_qapp():
    return QApplication.instance() or QApplication([])


def test_practice_presets_roundtrip_in_database(tmp_path):
    db_path = tmp_path / "test_lessons.db"
    db = DatabaseManager(str(db_path))
    try:
        file_path = "/tmp/example.mp3"
        db.insert_lesson((1, "Test", "example.mp3", file_path, 10.0, 128000))

        db.save_practice_preset(
            file_path=file_path,
            tempo=120,
            transpose_steps=2,
            loop_start_ms=1000,
            loop_end_ms=4000,
            groove="4/4",
        )

        row = db.get_practice_preset(file_path)
        assert row is not None
        assert row["tempo"] == 120
        assert row["transpose_steps"] == 2
        assert row["loop_start_ms"] == 1000
        assert row["loop_end_ms"] == 4000
        assert row["metronome_groove"] == "4/4"
    finally:
        db.close()


class StubItem:
    def __init__(self, path):
        self._path = path

    def data(self, role):
        if role == Qt.UserRole:
            return self._path
        return None


class StubDB:
    def __init__(self, preset_row=None, meta_row=None):
        self.preset_row = preset_row
        self.meta_row = meta_row
        self.saved = None

    def get_practice_preset(self, file_path):
        return self.preset_row

    def get_lesson_metadata(self, file_path):
        return self.meta_row

    def save_practice_preset(
        self,
        file_path,
        tempo,
        transpose_steps,
        loop_start_ms,
        loop_end_ms,
        groove,
    ):
        self.saved = (file_path, tempo, transpose_steps, loop_start_ms, loop_end_ms, groove)

    def update_lesson_metadata(self, file_path, lesson_name, tempo, tags):
        self.meta_row = {"lesson_name": "Test", "tempo": tempo, "tags": tags}


class DummyLabel:
    def __init__(self):
        self.last = None

    def setText(self, text):
        self.last = text


class StubApp:
    def __init__(self, db, transpose_steps=0, loop_start=None, loop_end=None):
        self.db = db
        self.transpose_steps = transpose_steps
        self.loop_start_ms = loop_start
        self.loop_end_ms = loop_end
        self.practice_status_label = DummyLabel()
        self.status_messages = []

    def _set_status_message(self, text: str):
        self.status_messages.append(text)

    def apply_transposition(self):
        pass


def test_save_practice_preset_uses_current_state(monkeypatch):
    _ensure_qapp()
    db = StubDB(meta_row={"lesson_name": "Test", "tempo": 110, "tags": "3/4"})
    app = StubApp(db, transpose_steps=3, loop_start=500, loop_end=2500)
    item = StubItem("/tmp/example.mp3")

    monkeypatch.setattr(detail_mod.QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(detail_mod.QMessageBox, "warning", lambda *a, **k: None)

    detail_mod.save_practice_preset(app, item)

    saved = db.saved
    assert saved is not None
    file_path, tempo, transpose_steps, loop_start_ms, loop_end_ms, groove = saved
    assert file_path == "/tmp/example.mp3"
    assert tempo == 110
    assert transpose_steps == 3
    assert loop_start_ms == 500
    assert loop_end_ms == 2500
    assert groove == "3/4"
    # Status label should indicate an active preset
    assert app.practice_status_label.last == "Preset on"
    # Status bar helper should also receive the message
    assert "Preset on" in app.status_messages


def test_apply_practice_preset_updates_app_state_and_tags(monkeypatch):
    _ensure_qapp()
    preset_row = {
        "tempo": 130,
        "transpose_steps": 2,
        "loop_start_ms": 1000,
        "loop_end_ms": 3000,
        "metronome_groove": "4/4",
    }
    db = StubDB(preset_row=preset_row, meta_row={"lesson_name": "Test", "tempo": 110, "tags": "3/4"})
    app = StubApp(db, transpose_steps=0, loop_start=None, loop_end=None)
    item = StubItem("/tmp/example.mp3")

    monkeypatch.setattr(detail_mod.QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(detail_mod.QMessageBox, "warning", lambda *a, **k: None)

    # apply_practice_preset will call update_lesson_metadata to rewrite tags
    detail_mod.apply_practice_preset(app, item)

    assert app.transpose_steps == 2
    assert app.loop_start_ms == 1000
    assert app.loop_end_ms == 3000
    # Groove should be first tag
    assert db.meta_row["tags"].startswith("4/4")
    # Status label should indicate an active preset
    assert app.practice_status_label.last == "Preset on"
    assert "Preset on" in app.status_messages


def test_reset_practice_preset_clears_row_and_label(tmp_path, monkeypatch):
    _ensure_qapp()
    db_path = tmp_path / "test_lessons.db"
    db = DatabaseManager(str(db_path))
    try:
        file_path = "/tmp/example_reset.mp3"
        db.insert_lesson((1, "Test", "example_reset.mp3", file_path, 10.0, 128000))
        db.save_practice_preset(
            file_path=file_path,
            tempo=100,
            transpose_steps=1,
            loop_start_ms=500,
            loop_end_ms=1500,
            groove="2/4",
        )

        app = StubApp(db, transpose_steps=0, loop_start=None, loop_end=None)
        item = StubItem(file_path)

        monkeypatch.setattr(detail_mod.QMessageBox, "information", lambda *a, **k: None)
        monkeypatch.setattr(detail_mod.QMessageBox, "warning", lambda *a, **k: None)

        detail_mod.reset_practice_preset(app, item)

        assert db.get_practice_preset(file_path) is None
        assert app.practice_status_label.last == ""
        # No explicit status bar message here; apply_practice_preset handles the cleared case.
    finally:
        db.close()
