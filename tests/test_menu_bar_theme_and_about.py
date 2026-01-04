from ui import menu_bar as menu_mod


def test_switch_theme_updates_settings_and_checks_actions(monkeypatch):
    # Fake settings with in-memory storage
    class FakeSettings:
        def __init__(self):
            self.store = {"theme": "light_blue"}

        def value(self, key, default=None):
            return self.store.get(key, default)

        def setValue(self, key, value):
            self.store[key] = value

    settings = FakeSettings()

    recorded = {}

    def fake_load_theme(app, theme):
        recorded["theme"] = theme

    monkeypatch.setattr(menu_mod, "load_theme", fake_load_theme)

    # Build a fake theme_menu with stub actions
    class StubAction:
        def __init__(self, text, checked=False):
            self._text = text
            self._checked = checked

        def text(self):
            return self._text

        def isChecked(self):
            return self._checked

        def setChecked(self, value):
            self._checked = value

    dark_action = StubAction("dark_teal", checked=False)
    light_action = StubAction("light_blue", checked=True)

    class StubMenu:
        def __init__(self, actions):
            self._actions = actions

        def actions(self):
            return self._actions

    theme_menu = StubMenu([dark_action, light_action])

    # Act: switch to dark_teal
    menu_mod.switch_theme(app=None, theme_name="dark_teal", settings=settings, theme_menu=theme_menu)

    # Settings and load_theme should reflect the new theme
    assert settings.store["theme"] == "dark_teal"
    assert recorded["theme"] == "dark_teal"

    # Only dark_teal should now be checked
    assert dark_action.isChecked() is True
    assert light_action.isChecked() is False


def test_show_about_dialog_uses_expected_title_and_text(monkeypatch):
    captured = {}

    def fake_information(parent, title, text):
        captured["title"] = title
        captured["text"] = text

    monkeypatch.setattr(menu_mod.QMessageBox, "information", fake_information)

    menu_mod.show_about_dialog(parent=None)

    assert captured["title"] == "About Lesson Player"
    assert "Bouzouki Lesson Player" in captured["text"]
    assert "Built with" in captured["text"]


def test_open_metronome_from_menu_builds_command_with_tempo(monkeypatch):
    # Fake settings that include a metronome default tempo
    class FakeSettings:
        def __init__(self):
            self.store = {"metronome_default_tempo": "150"}

        def value(self, key, default=None):
            return self.store.get(key, default)

    # Capture the command passed to subprocess.Popen
    captured = {}

    def fake_popen(cmd, *args, **kwargs):
        captured["cmd"] = cmd

    monkeypatch.setattr(menu_mod, "QSettings", lambda *a, **k: FakeSettings())
    monkeypatch.setattr(menu_mod.subprocess, "Popen", fake_popen)

    # Parent object is only used as a QMessageBox parent in error paths
    class DummyApp:
        pass

    menu_mod.open_metronome_from_menu(DummyApp())

    cmd = captured.get("cmd")
    assert cmd is not None
    # Should invoke the metronome module
    assert "-m" in cmd
    assert "metronome.metronome" in cmd
    # Tempo flag forwarded from settings
    assert "--tempo" in cmd
    tempo_index = cmd.index("--tempo")
    assert cmd[tempo_index + 1] == "150"
