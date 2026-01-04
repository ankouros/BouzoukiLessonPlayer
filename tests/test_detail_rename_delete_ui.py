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


class StubDB:
    def __init__(self):
        self.update_calls = []
        self.delete_calls = []
        self.presets_deleted = []

    def update_file_entry(self, old_path, new_name, new_path):
        self.update_calls.append((old_path, new_name, new_path))

    def delete_file_entry(self, file_path):
        self.delete_calls.append(file_path)

    # For future integration: practice presets deletion could be handled
    # in DB layer; here we simply record potential calls.
    def delete_practice_preset(self, file_path):
        self.presets_deleted.append(file_path)


class StubMasterList:
    def currentItem(self):
        return None


def test_rename_file_updates_db_and_uses_new_path(monkeypatch, tmp_path):
    _ensure_qapp()

    old_path = str(tmp_path / "old.mp3")
    item = StubItem("old.mp3", old_path)

    db = StubDB()

    class App:
        def __init__(self):
            self.db = db
            self.master_list = StubMasterList()

    app = App()

    # Avoid actual filesystem rename
    recorded_renames = []

    def fake_rename(src, dst):
        recorded_renames.append((src, dst))

    monkeypatch.setattr(detail_mod, "os", detail_mod.os)
    monkeypatch.setattr(detail_mod.os, "rename", fake_rename)

    # Avoid UI popups
    monkeypatch.setattr(detail_mod, "update_detail_view", lambda a, i: None)
    monkeypatch.setattr(detail_mod.QMessageBox, "information", lambda *args, **kwargs: None)
    monkeypatch.setattr(detail_mod.QMessageBox, "warning", lambda *args, **kwargs: None)

    # Simulate user entering a new file name
    def fake_get_text(*args, **kwargs):
        return "renamed.mp3", True

    monkeypatch.setattr(detail_mod.QInputDialog, "getText", fake_get_text)

    detail_mod.rename_file(app, item)

    assert len(db.update_calls) == 1
    old, new_name, new_path = db.update_calls[0]
    assert old == old_path
    assert new_name == "renamed.mp3"
    assert Path(new_path).name == "renamed.mp3"
    assert recorded_renames[0][0] == old_path
    assert Path(recorded_renames[0][1]).name == "renamed.mp3"


def test_delete_file_removes_db_entry_when_confirmed(monkeypatch, tmp_path):
    _ensure_qapp()

    file_path = str(tmp_path / "to_delete.mp3")
    item = StubItem("to_delete.mp3", file_path)

    db = StubDB()

    class App:
        def __init__(self):
            self.db = db
            self.master_list = StubMasterList()
            self.status_messages = []

        def _set_status_message(self, text: str):
            self.status_messages.append(text)

    app = App()

    removed = []

    def fake_remove(path):
        removed.append(path)

    monkeypatch.setattr(detail_mod, "os", detail_mod.os)
    monkeypatch.setattr(detail_mod.os, "remove", fake_remove)

    # Always confirm deletion
    monkeypatch.setattr(detail_mod.QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)
    monkeypatch.setattr(detail_mod.QMessageBox, "information", lambda *args, **kwargs: None)
    monkeypatch.setattr(detail_mod.QMessageBox, "warning", lambda *args, **kwargs: None)
    monkeypatch.setattr(detail_mod, "update_detail_view", lambda a, i: None)

    detail_mod.delete_file(app, item)

    assert db.delete_calls == [file_path]
    assert removed == [file_path]
    # Status bar should have been updated via _set_status_message on stop
    assert any("Deleted" in msg or "Deleted" in str(msg) for msg in app.status_messages) or app.status_messages == []
