import os
from pathlib import Path

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

    def data(self, role):
        if role == Qt.UserRole:
            return self._path
        return None

    def setText(self, text):
        self._text = text

    def setData(self, role, value):
        if role == Qt.UserRole:
            self._path = value


class StubDB:
    def __init__(self):
        self.update_calls = []

    def update_file_entry(self, old_path, new_name, new_path):
        self.update_calls.append((old_path, new_name, new_path))


class App:
    def __init__(self, db):
        self.db = db


def test_relink_file_updates_db_and_item(monkeypatch, tmp_path):
    _ensure_qapp()

    original_path = str(tmp_path / "original.mp3")
    replacement_path = str(tmp_path / "replacement.mp3")

    Path(replacement_path).touch()

    item = StubItem("original.mp3", original_path)
    db = StubDB()
    app = App(db)

    # Pretend original does not exist, replacement does.
    def fake_exists(path):
        return path == replacement_path

    monkeypatch.setattr(detail_mod.os.path, "exists", fake_exists)

    # Avoid user interaction: always return a replacement path.
    monkeypatch.setattr(
        detail_mod.QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (replacement_path, ""),
    )

    # Suppress dialogs.
    monkeypatch.setattr(detail_mod.QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(detail_mod.QMessageBox, "warning", lambda *a, **k: None)

    detail_mod.relink_file(app, item)

    assert len(db.update_calls) == 1
    old_path, new_name, new_path = db.update_calls[0]
    assert old_path == original_path
    assert new_name == "replacement.mp3"
    assert new_path == replacement_path
    assert item.text() == "replacement.mp3"
    assert item.data(Qt.UserRole) == replacement_path

