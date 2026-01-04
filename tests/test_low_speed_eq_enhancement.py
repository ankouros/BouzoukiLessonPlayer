from ui.main_window import LessonPlayerApp


class DummyMediaPlayer:
    def __init__(self):
        self.playback_rate = None

    def setPlaybackRate(self, rate):
        self.playback_rate = rate


class DummyVlcPlayer:
    def __init__(self):
        self.rate = None
        self.pitch_semitones = None
        self.eq_profile = "initial"

    def set_rate(self, rate):
        self.rate = rate

    def set_pitch_semitones(self, semitones):
        self.pitch_semitones = semitones

    def set_eq_profile(self, profile):
        self.eq_profile = profile


class StubApp:
    """Minimal stand-in to exercise low-speed EQ enhancement."""

    def __init__(self):
        self.current_speed = 1.0
        self.transpose_steps = 0
        self.media_player = DummyMediaPlayer()
        self.vlc_player = DummyVlcPlayer()
        self.low_speed_eq_enabled = False

    apply_transposition = LessonPlayerApp.apply_transposition


def test_low_speed_eq_profile_applied_when_enabled_and_speed_low():
    app = StubApp()
    app.current_speed = 0.6
    app.transpose_steps = 0
    app.low_speed_eq_enabled = True

    app.apply_transposition()

    assert app.vlc_player.eq_profile == "low_speed_clarity"


def test_low_speed_eq_profile_cleared_when_disabled_or_speed_high():
    app = StubApp()
    app.current_speed = 1.0
    app.transpose_steps = 0
    app.low_speed_eq_enabled = True

    app.apply_transposition()
    assert app.vlc_player.eq_profile is None

    app.low_speed_eq_enabled = False
    app.current_speed = 0.5
    app.vlc_player.eq_profile = "something"
    app.apply_transposition()
    # Enhancement disabled: profile should be cleared
    assert app.vlc_player.eq_profile is None

