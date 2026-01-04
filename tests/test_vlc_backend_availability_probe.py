from core import vlc_player as vp


class FakeVlcOK:
    class Instance:
        def __init__(self, *args, **kwargs):
            pass

        def media_player_new(self):
            return FakeVlcOK.FakePlayer()

    class FakePlayer:
        def get_state(self):
            return 3


def test_probe_vlc_backend_returns_false_when_vlc_missing(monkeypatch):
    monkeypatch.setattr(vp, "vlc", None)
    assert vp.probe_vlc_backend() is False


def test_probe_vlc_backend_returns_true_when_basic_calls_succeed(monkeypatch):
    fake = FakeVlcOK()
    monkeypatch.setattr(vp, "vlc", fake)

    assert vp.probe_vlc_backend() is True

