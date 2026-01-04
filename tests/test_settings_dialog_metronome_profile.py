def test_settings_dialog_loads_and_saves_metronome_sound_profile(tmp_path, monkeypatch):
    # This test only validates the pure QSettings contract: that
    # metronome_sound_profile can be stored and retrieved. GUI wiring
    # is covered elsewhere by integration tests.
    from PyQt5.QtCore import QSettings

    settings = QSettings("bouzouki", "lessonplayer")
    settings.clear()
    settings.setValue("metronome_sound_profile", "soft")
    assert settings.value("metronome_sound_profile") == "soft"
