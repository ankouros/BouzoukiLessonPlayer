import importlib

import pytest


def test_metronome_missing_dependencies_prints_message_and_exits(monkeypatch, capsys):
    # Import the module normally
    mod = importlib.import_module("metronome.metronome")

    # Simulate a dependency-related ImportError when running the CLI
    def fake_main(*args, **kwargs):
        raise ImportError("No module named numpy")

    monkeypatch.setattr(mod, "main", fake_main)

    with pytest.raises(SystemExit) as exc:
        mod.cli()

    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "Metronome dependencies are missing" in out
    assert "numpy, simpleaudio, PyQt5" in out
