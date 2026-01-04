from pathlib import Path

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


class StubMediaPlayer:
    def __init__(self):
        self.set_media_called = False
        self.play_called = False

    def setMedia(self, media):
        self.set_media_called = True

    def play(self):
        self.play_called = True


class App:
    def __init__(self):
        self.media_player = StubMediaPlayer()


def test_play_selected_video_warns_when_path_missing(monkeypatch):
    _ensure_qapp()

    captured = {}

    def fake_warning(parent, title, text):
        captured["title"] = title
        captured["text"] = text

    monkeypatch.setattr(detail_mod.QMessageBox, "warning", fake_warning)

    app = App()
    item = StubItem(path=None)

    detail_mod.play_selected_video(app, item)

    assert captured["title"] == "Error"
    assert "determine file path" in captured["text"]
    assert app.media_player.set_media_called is False
    assert app.media_player.play_called is False


def test_play_selected_video_warns_when_file_does_not_exist(monkeypatch, tmp_path):
    _ensure_qapp()

    captured = {}

    def fake_warning(parent, title, text):
        captured["title"] = title
        captured["text"] = text

    monkeypatch.setattr(detail_mod.QMessageBox, "warning", fake_warning)

    # Force os.path.exists to return False regardless of path
    monkeypatch.setattr(detail_mod.os.path, "exists", lambda p: False)

    # Ensure we don't try to construct real QMediaContent/QUrl
    monkeypatch.setattr(detail_mod, "QMediaContent", lambda *args, **kwargs: None)

    app = App()
    missing_path = str(tmp_path / "missing.mp3")
    item = StubItem(path=missing_path)

    detail_mod.play_selected_video(app, item)

    assert captured["title"] == "Error"
    assert "not found" in captured["text"]
    assert app.media_player.set_media_called is False
    assert app.media_player.play_called is False

