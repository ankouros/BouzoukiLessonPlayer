from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

import ui.widgets.detail as detail_mod


def _ensure_qapp():
    return QApplication.instance() or QApplication([])


class StubItem:
    def __init__(self, path):
        self._path = path

    def data(self, role):
        if role == Qt.UserRole:
            return self._path
        return None


class StubDB:
    def __init__(self, row):
        self._row = row

    def get_lesson_metadata(self, file_path):
        return self._row


class DummyLabel:
    def __init__(self):
        self.last = None

    def setText(self, text):
        self.last = text


class App:
    def __init__(self, db):
        self.db = db
        # Label-like object to record metronome status text
        self.practice_status_label = DummyLabel()


def test_open_metronome_for_item_uses_tempo_and_first_tag(monkeypatch):
    _ensure_qapp()

    row = {"lesson_name": "Test", "tempo": 140, "tags": "4/4, slow"}
    db = StubDB(row=row)
    app = App(db=db)
    item = StubItem("/tmp/example.mp3")

    captured = {}

    def fake_popen(cmd, *args, **kwargs):
        captured["cmd"] = cmd

    monkeypatch.setattr(detail_mod.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(detail_mod.QMessageBox, "warning", lambda *a, **k: None)

    detail_mod.open_metronome_for_item(app, item)

    cmd = captured.get("cmd")
    assert cmd is not None
    # Base invocation
    assert "-m" in cmd and "metronome.metronome" in cmd
    # Tempo and groove flags
    assert "--tempo" in cmd
    tempo_index = cmd.index("--tempo")
    assert cmd[tempo_index + 1] == "140"
    assert "--groove" in cmd
    groove_index = cmd.index("--groove")
    assert cmd[groove_index + 1] == "4/4"

    # Status label should reflect metronome state concisely
    label_text = app.practice_status_label.last
    assert "Metronome" in label_text
    assert "140" in label_text
    assert "4/4" in label_text
