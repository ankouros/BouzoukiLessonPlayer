import json

from metronome import tap as tap_mod


class StubTap:
    def __init__(self, timestamps, clicks):
        self.timestamps = timestamps
        self.clicks = clicks


def test_tap_groove_not_enough_taps_does_not_write_file(monkeypatch, tmp_path, capsys):
    groove_path = tmp_path / "grooves.json"
    monkeypatch.setattr(tap_mod, "GROOVE_FILE", str(groove_path))

    stub = StubTap(timestamps=[1.0], clicks=[False])

    tap_mod.TapGroove._save_groove(stub)

    out = capsys.readouterr().out
    assert "Not enough taps" in out
    assert not groove_path.exists()
    assert stub.timestamps == [1.0]
    assert stub.clicks == [False]


def test_tap_groove_saves_valid_groove_and_preserves_existing(monkeypatch, tmp_path, capsys):
    groove_path = tmp_path / "grooves.json"
    monkeypatch.setattr(tap_mod, "GROOVE_FILE", str(groove_path))

    # Existing groove in the file
    existing = {"existing": {"pulses": 4, "accents": [0, 2], "swing": False}}
    groove_path.write_text(json.dumps(existing))

    # Three taps, second accented
    stub = StubTap(timestamps=[1.0, 1.5, 2.0], clicks=[False, True, False])

    tap_mod.TapGroove._save_groove(stub)

    assert groove_path.exists()
    data = json.loads(groove_path.read_text())

    # Existing entry preserved, plus one new groove
    assert "existing" in data
    assert data["existing"] == existing["existing"]
    assert len(data) == 2

    # Internal state cleared after saving
    assert stub.timestamps == []
    assert stub.clicks == []

