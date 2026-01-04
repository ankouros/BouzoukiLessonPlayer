import sqlite3

import pytest

import main as main_mod


def test_main_handles_db_error_gracefully(monkeypatch, capsys):
    class FakeQApp:
        def __init__(self, argv):
            pass
        def exec_(self):
            return 0
        @staticmethod
        def setApplicationName(name):
            # No-op for tests
            pass

    class FakeWindow:
        def __init__(self, db_path):
            raise sqlite3.DatabaseError("malformed database")

    monkeypatch.setattr(main_mod, "QApplication", FakeQApp)
    monkeypatch.setattr(main_mod, "LessonPlayerApp", FakeWindow)
    monkeypatch.setattr(main_mod, "load_theme", lambda app: None)

    with pytest.raises(SystemExit) as exc:
        main_mod.main()

    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "A critical error occurred:" in out
    assert "malformed database" in out

