from core import vlc_player as vp


class FakeVlcMedia:
    def __init__(self):
        self.path = None


class FakeVlcPlayer:
    def __init__(self):
        self.media = None
        self.rate = None
        self.volume = None
        self.play_called = False
        self.pause_called = False
        self.stop_called = False
        self.equalizer = "initial"
        self.time_ms = 0

    def set_media(self, media):
        self.media = media

    def play(self):
        self.play_called = True

    def pause(self):
        self.pause_called = True

    def stop(self):
        self.stop_called = True

    def set_rate(self, rate):
        self.rate = rate

    def audio_set_volume(self, volume):
        self.volume = volume

    def audio_set_equalizer(self, eq):
        self.equalizer = eq

    def get_state(self):
        return 3  # mimic State_Playing

    def set_time(self, t):
        self.time_ms = t


class FakeVlcInstance:
    def __init__(self, args):
        self.args = args

    def media_player_new(self):
        return FakeVlcPlayer()

    def media_new(self, path):
        m = FakeVlcMedia()
        m.path = path
        return m


class FakeVlcModule:
    def __init__(self):
        self.Instance = FakeVlcInstance
        self.State_Playing = 3

    def audio_output_equalizer_new(self):
        return "EQ_OBJECT"


def test_vlc_media_player_wraps_vlc_media_and_controls(monkeypatch):
    fake_vlc = FakeVlcModule()
    monkeypatch.setattr(vp, "vlc", fake_vlc)

    player = vp.VlcMediaPlayer()

    player.set_media("/tmp/example.mp3")
    player.set_rate(0.5)
    player.set_volume(80)
    player.play()
    player.pause()
    player.stop()

    # Access the underlying fake player through the wrapper internals
    underlying = player._player

    assert isinstance(underlying, FakeVlcPlayer)
    assert underlying.media.path == "/tmp/example.mp3"
    assert underlying.rate == 0.5
    assert underlying.volume == 80
    assert underlying.play_called is True
    assert underlying.pause_called is True
    assert underlying.stop_called is True
    assert player.is_playing() is True

    # Seeking should delegate to set_time on the underlying player
    player.set_position_ms(1234)
    assert underlying.time_ms == 1234


def test_vlc_media_player_raises_if_unavailable(monkeypatch):
    monkeypatch.setattr(vp, "vlc", None)

    try:
        vp.VlcMediaPlayer()
    except vp.VlcUnavailableError:
        pass
    else:  # pragma: no cover - should not happen
        assert False, "Expected VlcUnavailableError when vlc is None"


def test_vlc_media_player_sets_eq_profile_if_supported(monkeypatch):
    fake_vlc = FakeVlcModule()
    monkeypatch.setattr(vp, "vlc", fake_vlc)

    player = vp.VlcMediaPlayer()
    underlying = player._player

    # Apply a low-speed clarity profile
    player.set_eq_profile("low_speed_clarity")
    assert underlying.equalizer == "EQ_OBJECT"

    # Clearing the profile should reset the equalizer
    player.set_eq_profile(None)
    assert underlying.equalizer is None
