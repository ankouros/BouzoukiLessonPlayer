from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox

import ui.widgets.detail as detail_mod


def _ensure_qapp():
    return QApplication.instance() or QApplication([])


class StubItem:
    def __init__(self, text, path):
        self._text = text
        self._path = path

    def text(self):
        return self._text

    def setText(self, text):
        self._text = text

    def data(self, role):
        if role == Qt.UserRole:
            return self._path
        return None


class StubDB:
    def __init__(self, initial_row=None):
        self.initial_row = initial_row
        self.update_calls = []

    def get_lesson_metadata(self, file_path):
        return self.initial_row

    def update_lesson_metadata(self, file_path, lesson_name, tempo, tags):
        self.update_calls.append((file_path, lesson_name, tempo, tags))


class App:
    def __init__(self, db):
        self.db = db


def test_edit_metadata_updates_db_and_item(monkeypatch):
    _ensure_qapp()

    row = {"lesson_name": "Old Title", "tempo": 90, "tags": "old"}
    db = StubDB(initial_row=row)
    app = App(db)
    item = StubItem("Old Title", "/tmp/example.mp3")

    # Simulate three sequential QInputDialog.getText calls
    responses = [
        ("New Title", True),   # title
        ("120", True),         # tempo
        ("tag1, tag2", True),  # tags
    ]

    def fake_get_text(*args, **kwargs):
        return responses.pop(0)

    monkeypatch.setattr(detail_mod.QInputDialog, "getText", fake_get_text)
    monkeypatch.setattr(detail_mod.QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(detail_mod.QMessageBox, "warning", lambda *a, **k: None)

    detail_mod.edit_metadata(app, item)

    assert len(db.update_calls) == 1
    file_path, title, tempo, tags = db.update_calls[0]
    assert file_path == "/tmp/example.mp3"
    assert title == "New Title"
    assert tempo == 120
    assert tags == "tag1, tag2"
    assert item.text() == "New Title"


def test_edit_metadata_rejects_invalid_tempo(monkeypatch):
    _ensure_qapp()

    db = StubDB(initial_row={"lesson_name": "Title", "tempo": None, "tags": None})
    app = App(db)
    item = StubItem("Title", "/tmp/example.mp3")

    responses = [
        ("Title", True),  # title unchanged
        ("not-a-number", True),  # invalid tempo
    ]

    def fake_get_text(*args, **kwargs):
        return responses.pop(0)

    warnings = []

    monkeypatch.setattr(detail_mod.QInputDialog, "getText", fake_get_text)
    monkeypatch.setattr(
        detail_mod.QMessageBox,
        "warning",
        lambda *a, **k: warnings.append("warn"),
    )
    monkeypatch.setattr(detail_mod.QMessageBox, "information", lambda *a, **k: None)

    detail_mod.edit_metadata(app, item)

    # No DB update should occur on invalid tempo
    assert db.update_calls == []
    assert warnings, "Expected a warning on invalid tempo"

