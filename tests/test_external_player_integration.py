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


class FakeSettings:
    def __init__(self, values):
        self.values = values

    def value(self, key, default=None):
        return self.values.get(key, default)


class App:
    pass


def test_open_in_external_player_uses_configured_command(monkeypatch):
    _ensure_qapp()

    captured = {}

    def fake_popen(cmd, *args, **kwargs):
        captured["cmd"] = cmd

    monkeypatch.setattr(detail_mod.subprocess, "Popen", fake_popen)

    fake_settings = FakeSettings({"external_player_command": "fakeplayer --flag"})

    def fake_qsettings(*args, **kwargs):
        return fake_settings

    monkeypatch.setattr(detail_mod, "QSettings", fake_qsettings)
    monkeypatch.setattr(detail_mod.QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(detail_mod.QMessageBox, "warning", lambda *a, **k: None)

    app = App()
    item = StubItem("/tmp/example.mp3")

    detail_mod.open_in_external_player(app, item)

    cmd = captured.get("cmd")
    assert cmd is not None
    assert cmd[0] == "fakeplayer"
    assert cmd[-1] == "/tmp/example.mp3"

