import json
from pathlib import Path

from metronome.metronome import load_custom_presets


def test_load_custom_presets_invalid_json_returns_empty(monkeypatch, tmp_path, capsys):
    bad_file = tmp_path / "bad_grooves.json"
    bad_file.write_text("{ this is not valid json")

    presets = load_custom_presets(str(bad_file))

    assert presets == {}
    out = capsys.readouterr().out
    assert "Failed to load custom grooves" in out


def test_load_custom_presets_filters_out_entries_without_required_keys(tmp_path):
    groove_file = tmp_path / "grooves.json"
    data = {
        "valid": {"pulses": 4, "accents": [0, 2]},
        "missing_accents": {"pulses": 3},
        "missing_pulses": {"accents": [0]},
    }
    groove_file.write_text(json.dumps(data))

    presets = load_custom_presets(str(groove_file))

    assert "valid" in presets
    assert presets["valid"] == {"pulses": 4, "accents": [0, 2]}
    assert "missing_accents" not in presets
    assert "missing_pulses" not in presets

