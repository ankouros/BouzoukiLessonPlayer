from pathlib import Path
import json
import zipfile

import ui.menu_bar as menu_mod


class StubSettings:
    def __init__(self, initial=None):
        self.store = dict(initial or {})

    def allKeys(self):
        return list(self.store.keys())

    def value(self, key):
        return self.store.get(key)

    def setValue(self, key, value):
        self.store[key] = value


class StubApp:
    def __init__(self, db_path):
        self.db_path = str(db_path)
        self.messages = []


def test_build_backup_payload_collects_db_grooves_and_settings(monkeypatch, tmp_path):
    db_path = tmp_path / "lessons.db"
    db_path.write_text("dummy")

    grooves_path = tmp_path / "metronome" / "grooves.json"
    grooves_path.parent.mkdir(parents=True, exist_ok=True)
    grooves_path.write_text('{"foo": "bar"}')

    # Point the helper at our temp paths
    app = StubApp(db_path=db_path)

    # Stub QSettings to avoid real settings
    fake_settings = StubSettings({"theme": "dark_teal", "use_vlc_backend": True})

    def fake_qsettings(*args, **kwargs):
        return fake_settings

    monkeypatch.setattr(menu_mod, "QSettings", fake_qsettings)

    payload = menu_mod._build_backup_payload(app)

    assert Path(payload["db_path"]) == db_path
    assert "settings" in payload
    assert payload["settings"]["theme"] == "dark_teal"


def test_backup_and_restore_roundtrip(monkeypatch, tmp_path):
    db_path = tmp_path / "lessons.db"
    db_path.write_text("db-content")

    grooves_path = tmp_path / "metronome" / "grooves.json"
    grooves_path.parent.mkdir(parents=True, exist_ok=True)
    grooves_path.write_text("groove-content")

    app = StubApp(db_path=db_path)

    # Use temporary QSettings store
    fake_settings = StubSettings({"theme": "dark_teal"})

    def fake_qsettings(*args, **kwargs):
        return fake_settings

    monkeypatch.setattr(menu_mod, "QSettings", fake_qsettings)

    # Capture chosen backup path
    backup_file = tmp_path / "backup.zip"

    def fake_get_save_file_name(*args, **kwargs):
        return str(backup_file), "Backup Files (*.zip)"

    def fake_get_open_file_name(*args, **kwargs):
        return str(backup_file), "Backup Files (*.zip)"

    # Stub QFileDialog methods
    monkeypatch.setattr(menu_mod.QFileDialog, "getSaveFileName", staticmethod(fake_get_save_file_name))
    monkeypatch.setattr(menu_mod.QFileDialog, "getOpenFileName", staticmethod(fake_get_open_file_name))

    # Stub QMessageBox
    monkeypatch.setattr(menu_mod.QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(menu_mod.QMessageBox, "warning", lambda *a, **k: None)
    monkeypatch.setattr(menu_mod.QMessageBox, "question", lambda *a, **k: menu_mod.QMessageBox.Yes)

    # Run backup
    menu_mod.backup_library(app)
    assert backup_file.exists()

    # Overwrite originals to verify restore
    db_path.write_text("overwritten")
    grooves_path.write_text("overwritten-grooves")
    fake_settings.setValue("theme", "light_blue")

    # Run restore
    menu_mod.restore_library(app)

    assert db_path.read_text() == "db-content"
    assert grooves_path.read_text() == "groove-content"
    assert fake_settings.value("theme") == "dark_teal"
