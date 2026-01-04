import logging
import sqlite3

import pytest

import main as main_mod


def test_main_logs_exception_on_error(monkeypatch, capsys):
    class FakeQApp:
        def __init__(self, argv):
            pass
        def exec_(self):
            return 0
        @staticmethod
        def setApplicationName(name):
            pass

    class FakeWindow:
        def __init__(self, db_path):
            raise sqlite3.DatabaseError("boom")

    recorded = {}

    def fake_exception(msg):
        recorded["msg"] = msg

    monkeypatch.setattr(main_mod, "QApplication", FakeQApp)
    monkeypatch.setattr(main_mod, "LessonPlayerApp", FakeWindow)
    monkeypatch.setattr(main_mod, "load_theme", lambda app: None)
    monkeypatch.setattr(main_mod.logging, "exception", fake_exception)

    with pytest.raises(SystemExit) as exc:
        main_mod.main()

    assert exc.value.code == 1
    assert recorded["msg"] == "An unexpected error occurred:"
    out = capsys.readouterr().out
    assert "A critical error occurred:" in out
    assert "boom" in out

