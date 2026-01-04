import importlib


def test_metronome_cli_forwards_tempo_and_groove_to_main(monkeypatch):
    mod = importlib.import_module("metronome.metronome")

    called = {}

    def fake_main(tempo=None, groove=None):
        called["tempo"] = tempo
        called["groove"] = groove

    monkeypatch.setattr(mod, "main", fake_main)
    # Simulate CLI invocation with tempo and groove arguments
    monkeypatch.setattr(mod.sys, "argv", ["metronome", "--tempo", "150", "--groove", "4/4"])

    mod.cli()

    assert called["tempo"] == 150
    assert called["groove"] == "4/4"

